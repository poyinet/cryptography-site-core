#!/usr/bin/env python3
"""One-click hotfix for the already-built play output.

The clean fix is `build_games.py`; this helper exists for a release repo where
rebuilding is not desirable and only the 119 raw-game canonical lines need to
change. It is idempotent and prints a count.

Usage:
    python cryptography-site-core/scripts/fix_play_canonicals.py
"""
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
PLAY = PROJECT / "cryptography-site-play"
OLD = "https://poyi.net/games/"
NEW = "https://play.poyi.net/games/"


def main():
    changed = 0
    for p in (PLAY / "games").glob("*/index.html"):
        text = p.read_text(encoding="utf-8")
        if OLD in text:
            p.write_text(text.replace(OLD, NEW), encoding="utf-8")
            changed += 1
    print("raw game canonical fixed: %d" % changed)
    return 0 if changed <= 119 else 1


if __name__ == "__main__":
    raise SystemExit(main())
