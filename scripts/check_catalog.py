#!/usr/bin/env python3
"""Verify catalog/skills.yaml agrees with .agents/skills/ and categories.yaml.

Exit codes: 0 consistent, 1 mismatches.
Usage: python scripts/check_catalog.py
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("\n---", 1)[0][3:]) or {}


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    problems: list[str] = []

    catalog = yaml.safe_load((REPO / "catalog" / "skills.yaml").read_text(encoding="utf-8"))
    categories = yaml.safe_load((REPO / "catalog" / "categories.yaml").read_text(encoding="utf-8"))
    valid_categories = set((categories.get("categories") or {}).keys())
    skills_dir = REPO / ".agents" / "skills"
    dirs = {p.name for p in skills_dir.iterdir() if p.is_dir()}

    entries = catalog.get("skills") or []
    seen: set[str] = set()
    stable_in_catalog: set[str] = set()

    for e in entries:
        name = e.get("name", "?")
        if name in seen:
            problems.append(f"catalog: duplicate entry '{name}'")
        seen.add(name)
        if e.get("category") not in valid_categories:
            problems.append(f"catalog: '{name}' has unknown category '{e.get('category')}'")
        status = e.get("status")
        if status not in {"stable", "beta", "experimental", "planned", "deprecated"}:
            problems.append(f"catalog: '{name}' has invalid status '{status}'")
        if status in {"stable", "beta", "experimental"}:
            stable_in_catalog.add(name)
            if name not in dirs:
                problems.append(f"catalog: '{name}' is {status} but has no skill directory")
            else:
                fm = frontmatter(skills_dir / name / "SKILL.md")
                meta = fm.get("metadata") or {}
                if meta.get("opencoworking.maturity") != status:
                    problems.append(
                        f"catalog: '{name}' status {status} != frontmatter maturity "
                        f"{meta.get('opencoworking.maturity')}")
                if str(meta.get("opencoworking.version")) != str(e.get("version")):
                    problems.append(f"catalog: '{name}' version mismatch")
                if meta.get("opencoworking.risk") != e.get("risk"):
                    problems.append(f"catalog: '{name}' risk mismatch")
                if meta.get("opencoworking.category") != e.get("category"):
                    problems.append(f"catalog: '{name}' category mismatch")
        elif status == "planned":
            if name in dirs:
                problems.append(f"catalog: '{name}' is planned but a skill directory exists")
            for field in ("problem", "evidence_needed", "planned_evals", "priority"):
                if not e.get(field):
                    problems.append(f"catalog: planned '{name}' missing '{field}'")
            if e.get("priority") not in {"p1", "p2", "p3"}:
                problems.append(f"catalog: planned '{name}' invalid priority")

        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", str(name)):
            problems.append(f"catalog: '{name}' violates naming rules")

    for d in dirs - stable_in_catalog:
        problems.append(f"catalog: skill directory '{d}' has no stable catalog entry")

    stable_count = sum(1 for e in entries if e.get("status") == "stable")
    planned_count = sum(1 for e in entries if e.get("status") == "planned")
    print(f"Catalog: {stable_count} stable, {planned_count} planned, "
          f"{len(dirs)} skill directories.")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("Catalog and skills agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
