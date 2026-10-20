"""Собрать словарь: скачать accents.json.gz из RUAccent (HuggingFace, лицензия MIT) и сложить в SQLite.

    python -m rustress.build              # → ~/.cache/rustress/stress.sqlite
    python -m rustress.build --out my.sqlite
"""
import argparse
import gzip
import json
import os
import sqlite3
import sys
import urllib.request

from . import default_db_path

URL = "https://huggingface.co/ruaccent/accentuator/resolve/main/dictionary/accents.json.gz"


def build(out: str, src: str | None = None) -> int:
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    if not src:
        src = out + ".download.json.gz"
        if not os.path.exists(src):
            print("Скачиваю словарь RUAccent (~30 МБ)…", file=sys.stderr)
            urllib.request.urlretrieve(URL, src + ".part")
            os.replace(src + ".part", src)
    data = json.load(gzip.open(src))
    tmp = out + ".part"
    if os.path.exists(tmp):
        os.remove(tmp)
    db = sqlite3.connect(tmp)
    db.execute("CREATE TABLE s(w TEXT PRIMARY KEY, a TEXT) WITHOUT ROWID")
    db.executemany("INSERT OR REPLACE INTO s VALUES (?, ?)", ((k.lower(), v.lower()) for k, v in data.items() if "+" in v))
    db.commit()
    n = db.execute("SELECT COUNT(*) FROM s").fetchone()[0]
    db.execute("VACUUM")
    db.close()
    os.replace(tmp, out)
    print("Готово: %s (%d слов)" % (out, n), file=sys.stderr)
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=default_db_path(), help="куда положить базу")
    ap.add_argument("--src", help="уже скачанный accents.json.gz")
    a = ap.parse_args()
    build(a.out, a.src)


if __name__ == "__main__":
    main()
