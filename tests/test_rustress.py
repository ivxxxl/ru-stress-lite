import os
import sqlite3
import tempfile

import pytest

from rustress import Stressor
from rustress.piper import fix_word


@pytest.fixture(scope="module")
def stressor():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "s.sqlite")
    db = sqlite3.connect(p)
    db.execute("CREATE TABLE s(w TEXT PRIMARY KEY, a TEXT) WITHOUT ROWID")
    db.executemany("INSERT INTO s VALUES (?,?)", [("дядя", "д+ядя"), ("самых", "с+амых"), ("честных", "ч+естных"),
                                                 ("правил", "пр+авил"), ("молоко", "молок+о")])
    db.commit()
    db.close()
    return Stressor(p)


def test_sentence(stressor):
    assert stressor.stress("Мой дядя самых честных правил") == "Мой д+ядя с+амых ч+естных пр+авил"


def test_case_and_punct(stressor):
    assert stressor.stress("МОЛОКО, молоко!") == "МОЛОК+О, молок+о!"


def test_unknown_and_short(stressor):
    assert stressor.stress("кот и абвгдеж") == "кот и абвгдеж"


def test_omograph(stressor):
    assert stressor.stress("замок") == "з+амок"


def test_acute(stressor):
    s = Stressor.__new__(Stressor)
    s.__dict__.update(stressor.__dict__)
    s.mark = "acute"
    assert s.stress("молоко") == "молоко́"


def test_fix_word_moves_stress():
    # espeak: замок → zˈamək (ударение на «а»); словарь: зам+ок
    assert fix_word("зам+ок", ["z", "ˈ", "a", "m", "ə", "k"]) == ["z", "ʌ", "m", "ˈ", "o", "k"]
