#!/usr/bin/env python3
"""Generate the README skills table from catalog/skills.yaml.

The table is written between the markers:
<!-- catalog:start --> and <!-- catalog:end -->

Usage:
  python scripts/generate_readme_catalog.py          # rewrite README section
  python scripts/generate_readme_catalog.py --check  # verify up to date (CI)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
START, END = "<!-- catalog:start -->", "<!-- catalog:end -->"


def build_table() -> str:
    catalog = yaml.safe_load((REPO / "catalog" / "skills.yaml").read_text(encoding="utf-8"))
    categories = yaml.safe_load((REPO / "catalog" / "categories.yaml").read_text(encoding="utf-8"))
    cat_titles = {k: v["title"] for k, v in (categories.get("categories") or {}).items()}
    shipped = [e for e in catalog.get("skills", [])
               if e.get("status") in {"stable", "beta"}]
    planned = [e for e in catalog.get("skills", []) if e.get("status") == "planned"]

    lines = [
        "| Skill | Category | What it does | Modes | Risk | Maturity |",
        "|---|---|---|---|---|---|",
    ]
    for e in shipped:
        modes = "+".join(e.get("modes", []))
        lines.append(
            f"| [`{e['name']}`](.agents/skills/{e['name']}/SKILL.md) "
            f"| {cat_titles.get(e['category'], e['category'])} "
            f"| {e['problem']} "
            f"| {modes} | {e['risk'].upper()} | {e['status']} |")
    lines.append("")
    lines.append(f"Plus **{len(planned)} planned skills** tracked in "
                 f"[`catalog/skills.yaml`](catalog/skills.yaml) and [ROADMAP.md](ROADMAP.md). "
                 "Beta means complete and tested, not yet proven with an outside operator.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify instead of write")
    args = parser.parse_args(argv)

    readme = REPO / "README.md"
    if not readme.is_file():
        print("error: README.md not found", file=sys.stderr)
        return 1
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print(f"error: markers {START} / {END} missing from README", file=sys.stderr)
        return 1
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{START}\n{build_table()}\n{END}{tail}"
    if args.check:
        if new != text:
            print("README catalog table is out of date. "
                  "Run: python scripts/generate_readme_catalog.py")
            return 1
        print("README catalog table is up to date.")
        return 0
    readme.write_text(new, encoding="utf-8")
    print("README catalog table regenerated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
