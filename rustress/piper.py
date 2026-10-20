"""Ударения для Piper TTS.

espeak (через него Piper превращает текст в звуки) сам угадывает ударение и знаки ударения в тексте
игнорирует — отсюда «з[а]мок» и «орг[а]нов». Здесь мы ставим ударение прямо в звуках: ударной гласной —
полное звучание по букве, бывшей ударной — редукцию, как в живой речи.

    from piper import PiperVoice
    from rustress import Stressor
    from rustress.piper import phonemes

    voice = PiperVoice.load("ru_RU-irina-medium.onnx")
    ids = voice.phonemes_to_ids(phonemes(voice, "Замок стоит на холме.", Stressor()))
"""
import re

VL = "аеёиоуыэюя"
VP = set("aɑeiɨouʌəɐɪʊɛæɵ")
FULL = {"а": "a", "я": "a", "о": "o", "ё": "o", "е": "e", "э": "e", "и": "i", "ы": "ɨ", "у": "u", "ю": "u"}
_PUNCT = re.compile(r"[.,!?;:—–-]")


def fix_word(word_plus, ph):
    """Звуки одного слова (как их дал espeak) + слово с «+» → звуки с ударением на нужной гласной."""
    word = word_plus.replace("+", "")
    letters = [c for c in word.lower() if c in VL]
    si, k = None, 0
    for c in word_plus.lower():
        if c == "+":
            si = k
        elif c in VL:
            k += 1
    vidx = [i for i, p in enumerate(ph) if p in VP]
    if si is None or len(letters) < 2 or len(vidx) != len(letters):
        return list(ph)                                  # не сошлось число гласных (числа, сокращения) — как у espeak
    old = [j for j, i in enumerate(vidx) if i > 0 and ph[i - 1] == "ˈ"]
    out = list(ph)
    for j, i in enumerate(vidx):
        L = letters[j]
        if j == si:
            out[i] = FULL[L]
        elif j in old:                                   # бывшая ударная — редуцируем
            out[i] = ("ʌ" if j == si - 1 else "ə") if L in "ао" else ("i" if L in "еяэ" else out[i])
    res = []
    for i, p in enumerate(out):
        if p == "ˈ":
            continue
        if i in vidx and vidx.index(i) == si:
            res.append("ˈ")
        res.append(p)
    return res


def phonemes(voice, sentence, stressor):
    """Предложение → список звуков Piper с исправленными ударениями (для voice.phonemes_to_ids)."""
    acc = stressor.stress(sentence) if stressor.mark == "+" else sentence
    toks = re.findall(r"[А-Яа-яЁё+]+(?:-[А-Яа-яЁё+]+)*|[A-Za-z0-9]+|[.,!?;:—–-]", acc)
    words = [t for t in toks if not _PUNCT.fullmatch(t)]
    # фраза целиком — предлоги и частицы безударные, как в речи; дальше правим ударение внутри слов
    whole = [p for s in voice.phonemize(" ".join(t.replace("+", "") for t in words)) for p in s]
    groups, cur = [], []
    for p in whole:
        if p == " ":
            if cur:
                groups.append(cur)
                cur = []
        elif p not in ".,!?;:":
            cur.append(p)
    if cur:
        groups.append(cur)
    aligned = len(groups) == len(words)
    wi, out = 0, []
    for t in toks:
        if _PUNCT.fullmatch(t):
            if out and out[-1] == " ":
                out.pop()
            out += [{"—": ",", "–": ",", "-": ","}.get(t, t), " "]
            continue
        ph = groups[wi] if aligned else [p for s in voice.phonemize(t.replace("+", "")) for p in s]
        out += (fix_word(t, ph) if re.search(r"[А-Яа-яЁё]", t) else ph) + [" "]
        wi += 1
    while out and out[-1] == " ":
        out.pop()
    if out and out[-1] not in ".!?":
        out.append(".")
    return out
