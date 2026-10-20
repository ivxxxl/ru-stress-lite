"""Piper с правильными ударениями: pip install piper-tts numpy ru-stress-lite
python examples/piper_demo.py ru_RU-irina-medium.onnx "Замок стоит на холме." out.wav"""
import sys
import wave

import numpy as np

from piper import PiperVoice
from rustress import Stressor
from rustress.piper import phonemes

model, text, out = sys.argv[1], sys.argv[2], sys.argv[3]
voice = PiperVoice.load(model)
ids = voice.phonemes_to_ids(phonemes(voice, text, Stressor()))
audio = voice.phoneme_ids_to_audio(ids)
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(voice.config.sample_rate)
    a = np.asarray(audio)
    if a.dtype != np.int16:                       # Piper 1.3+ отдаёт float в [-1, 1]
        a = (np.clip(a, -1, 1) * 32767).astype(np.int16)
    w.writeframes(a.tobytes())
print("готово:", out)
