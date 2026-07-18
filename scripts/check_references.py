#!/usr/bin/env python3
"""Check relative Markdown links across the repository for broken targets.

Exit codes: 0 clean, 1 broken links.
Usage: python scripts/check_references.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".research"}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    broken: list[str] = []
    checked = 0
    for md in REPO.rglob("*.md"):
        if any(part in SKIP_DIRS for part in md.parts):
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        # Skip fenced code blocks - links there are illustrative templates.
        text = re.sub(r"^(`{3,}|~{3,}).*?^\1\s*$", "", text, flags=re.S | re.M)
        for raw in LINK_RE.findall(text):
            link = raw.split("#")[0]
            if not link or link.startswith(("http://", "https://", "mailto:", "{")):
                continue
            checked += 1
            target = (md.parent / link).resolve()
            if not target.exists():
                broken.append(f"{md.relative_to(REPO)}: '{raw}'")
    print(f"Checked {checked} relative links.")
    if broken:
        print(f"\n{len(broken)} broken link(s):")
        for b in broken:
            print(f"  - {b}")
        return 1
    print("No broken relative links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
