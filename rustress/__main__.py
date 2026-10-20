"""Командная строка: python -m rustress "текст" [--acute]  (или текст из stdin)."""
import argparse
import sys

from . import Stressor


def main():
    ap = argparse.ArgumentParser(prog="rustress", description="Ударения в русском тексте")
    ap.add_argument("text", nargs="*", help="текст (если пусто — читаем stdin)")
    ap.add_argument("--acute", action="store_true", help="знак ударения над гласной вместо «+»")
    ap.add_argument("--db", help="путь к словарю (по умолчанию ~/.cache/rustress/stress.sqlite)")
    a = ap.parse_args()
    s = Stressor(a.db, mark="acute" if a.acute else "+")
    text = " ".join(a.text) if a.text else sys.stdin.read()
    sys.stdout.write(s.stress(text) + ("" if text.endswith("\n") else "\n"))


if __name__ == "__main__":
    main()
