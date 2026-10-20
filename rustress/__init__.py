"""ru-stress-lite — ударения в русском тексте по словарю на 3,2 млн словоформ.

Быстро и легко: словарь лежит в SQLite и читается с диска по одному слову, поэтому
библиотека занимает десятки мегабайт памяти вместо гигабайтов у нейросетевых решений.
Омографы (за́мок / замо́к) без контекста не различить — для частых из них есть
список «самого вероятного» варианта (OMOGRAPHS), его можно дополнить своим.
"""
from __future__ import annotations

import os
import re
import sqlite3
import threading

__all__ = ["Stressor", "stress", "OMOGRAPHS", "default_db_path"]
__version__ = "0.1.0"

VOWELS = "аеёиоуыэюя"
ACUTE = "́"

# частые омографы: вариант, который чаще нужен в учебных и разговорных текстах
OMOGRAPHS = {
    "органов": "+органов", "органы": "+органы", "орган": "+орган", "потом": "пот+ом", "белки": "б+елки",
    "белков": "белк+ов", "крови": "кр+ови", "воды": "вод+ы", "руки": "р+уки", "ноги": "н+оги", "дома": "д+ома",
    "мука": "м+ука", "кружки": "кр+ужки", "среды": "ср+еды", "атлас": "+атлас", "уже": "уж+е",
    "больше": "б+ольше", "замок": "з+амок", "горе": "г+оре", "голов": "гол+ов", "сорок": "с+орок", "плачу": "пл+ачу",
    "писать": "пис+ать", "хлопок": "хл+опок", "веками": "век+ами", "часы": "час+ы", "окон": "+окон", "слова": "слов+а",
    "среда": "сред+а", "клетки": "кл+етки", "ткани": "тк+ани", "кожи": "к+ожи", "мышцы": "м+ышцы", "ряда": "р+яда",
}

_WORD = re.compile(r"[А-Яа-яЁё]+")


def default_db_path() -> str:
    """Где искать словарь: $RUSTRESS_DB или ~/.cache/rustress/stress.sqlite."""
    return os.environ.get("RUSTRESS_DB") or os.path.join(os.path.expanduser("~"), ".cache", "rustress", "stress.sqlite")


class Stressor:
    """Расставляет ударения. Потокобезопасен; одно соединение SQLite на объект.

    >>> s = Stressor()                       # doctest: +SKIP
    >>> s.stress("Мой дядя самых честных правил")  # doctest: +SKIP
    'М+ой д+ядя с+амых ч+естных пр+авил'
    """

    def __init__(self, db_path: str | None = None, omographs: dict | None = None, mark: str = "+"):
        path = db_path or default_db_path()
        if not os.path.exists(path):
            raise FileNotFoundError("Нет словаря %s — соберите его: python -m rustress.build" % path)
        self._db = sqlite3.connect("file:%s?mode=ro" % path, uri=True, check_same_thread=False)
        self._lock = threading.Lock()
        self.omographs = dict(OMOGRAPHS)
        if omographs:
            self.omographs.update({k.lower(): v for k, v in omographs.items()})
        if mark not in ("+", "acute"):
            raise ValueError("mark: '+' (перед гласной) или 'acute' (знак над гласной)")
        self.mark = mark

    def lookup(self, word: str) -> str | None:
        """Слово (любой регистр) → «пр+авил» (в нижнем регистре) или None, если слова нет в словаре."""
        w = word.lower()
        if w in self.omographs:
            return self.omographs[w]
        with self._lock:
            r = self._db.execute("SELECT a FROM s WHERE w=?", (w,)).fetchone()
        return r[0] if r else None

    def _apply(self, word: str, marked: str) -> str:
        out, k = [], 0                                   # переносим ударение на слово с исходным регистром
        for ch in marked:
            if ch == "+":
                out.append("+")
            else:
                out.append(word[k] if k < len(word) else ch)
                k += 1
        s = "".join(out)
        if self.mark == "acute":
            s = re.sub(r"\+(.)", lambda m: m.group(1) + ACUTE, s)
        return s

    def stress(self, text: str) -> str:
        """Текст → тот же текст с ударениями. Односложные и неизвестные слова не трогаем."""
        def one(m):
            w = m.group(0)
            if sum(1 for c in w.lower() if c in VOWELS) < 2 or "ё" in w.lower():
                return w                                 # одна гласная или «ё» — ударение и так ясно
            a = self.lookup(w)
            return self._apply(w, a) if a else w
        return _WORD.sub(one, text)

    def close(self):
        self._db.close()


_default = None


def stress(text: str, mark: str = "+") -> str:
    """Быстрый вызов с общим словарём по умолчанию."""
    global _default
    if _default is None or _default.mark != mark:
        _default = Stressor(mark=mark)
    return _default.stress(text)
