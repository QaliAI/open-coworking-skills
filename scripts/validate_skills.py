#!/usr/bin/env python3
"""Validate every skill in .agents/skills/ against the repo quality standard.

Checks frontmatter (Agent Skills spec), naming, descriptions, required
sections, references, placeholders, secrets, and eval presence.
Exit codes: 0 clean, 1 violations found.

Usage: python scripts/validate_skills.py [--skills-dir DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("error: pyyaml required (pip install -e '.[dev]')", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parent.parent

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
VALID_MATURITY = {"experimental", "beta", "stable", "deprecated"}
VALID_RISK = {"r0", "r1", "r2", "r3", "r4"}
VALID_SENSITIVITY = {"public", "internal", "confidential", "restricted"}
PLACEHOLDER_RE = re.compile(
    r"\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b|coming soon|lorem ipsum|<placeholder>|\[insert",
    re.I,
)
SECRET_RES = [
    re.compile(r"sk_live_[0-9a-zA-Z]{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[0-9A-Za-z]{20,}"),
    re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|password|secret)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"),
]
# Absolute paths that would break on other machines.
ABS_PATH_RE = re.compile(r"[A-Za-z]:\\Users\\|/home/\w+|/Users/\w+")

REQUIRED_SECTION_PATTERNS = {
    "purpose/problem": r"##.*(Purpose|problem)",
    "when to use": r"##\s*When to use",
    "when not to use": r"##\s*When not to use",
    "modes": r"##\s*(Operating modes|.*modes)",
    "inputs": r"##\s*Required inputs",
    "workflow": r"##\s*Workflow",
    "output contract": r"##\s*Output contract",
    "edge cases": r"##\s*Edge cases",
    "privacy": r"##\s*Privacy",
    "failure": r"##\s*Failure",
    "example": r"##\s*Example",
    "evals": r"##\s*Evals",
    "version": r"##\s*Version",
}

VAGUE_PHRASES = [
    "analyze the data.",
    "provide actionable insights",
    "create a strategy.",
    "optimize the business",
    "use best practices",
]


def split_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    if not text.startswith("---"):
        return None, text, "missing frontmatter"
    parts = text.split("\n---", 2)
    if len(parts) < 2:
        return None, text, "unterminated frontmatter"
    try:
        fm = yaml.safe_load(parts[0][3:])
    except yaml.YAMLError as e:
        return None, text, f"invalid YAML frontmatter: {e}"
    body = parts[1] if len(parts) == 2 else parts[1] + "\n---" + parts[2]
    return fm, body, None


def validate_skill(skill_dir: Path, problems: list[str], descriptions: dict[str, str],
                   names: set[str]) -> None:
    rel = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        problems.append(f"{rel}: missing SKILL.md")
        return
    text = skill_md.read_text(encoding="utf-8")
    fm, body, err = split_frontmatter(text)
    if err or not isinstance(fm, dict):
        problems.append(f"{rel}: {err or 'frontmatter is not a mapping'}")
        return

    name = str(fm.get("name", ""))
    desc = str(fm.get("description", ""))
    if not name:
        problems.append(f"{rel}: missing required field 'name'")
    else:
        if not NAME_RE.match(name) or len(name) > 64:
            problems.append(f"{rel}: name '{name}' violates naming constraints")
        if name != skill_dir.name:
            problems.append(f"{rel}: name '{name}' does not match folder name")
        if name in names:
            problems.append(f"{rel}: duplicate skill name '{name}'")
        names.add(name)
    if not desc:
        problems.append(f"{rel}: missing required field 'description'")
    else:
        if len(desc) > 1024:
            problems.append(f"{rel}: description exceeds 1024 chars ({len(desc)})")
        if len(desc) < 80:
            problems.append(f"{rel}: description too short to be a useful trigger ({len(desc)} chars)")
        if not re.search(r"\bUse when\b|\bUse (this |it )?(before|right after|for)\b", desc, re.I):
            problems.append(f"{rel}: description lacks an explicit 'Use when...' trigger clause")
        low = desc.lower().strip()
        for other, otherdesc in descriptions.items():
            if low == otherdesc:
                problems.append(f"{rel}: description duplicates {other}")
        descriptions[name] = low
    comp = fm.get("compatibility")
    if comp is not None and len(str(comp)) > 500:
        problems.append(f"{rel}: compatibility exceeds 500 chars")
    if str(fm.get("license", "")) != "Apache-2.0":
        problems.append(f"{rel}: license metadata missing or not Apache-2.0")
    meta = fm.get("metadata") or {}
    if not isinstance(meta, dict):
        problems.append(f"{rel}: metadata must be a mapping")
        meta = {}
    if meta.get("opencoworking.maturity") not in VALID_MATURITY:
        problems.append(f"{rel}: metadata opencoworking.maturity invalid/missing")
    if meta.get("opencoworking.risk") not in VALID_RISK:
        problems.append(f"{rel}: metadata opencoworking.risk invalid/missing")
    if meta.get("opencoworking.data-sensitivity") not in VALID_SENSITIVITY:
        problems.append(f"{rel}: metadata opencoworking.data-sensitivity invalid/missing")
    if not re.match(r"^\d+\.\d+\.\d+$", str(meta.get("opencoworking.version", ""))):
        problems.append(f"{rel}: metadata opencoworking.version not semver")
    if not meta.get("opencoworking.category"):
        problems.append(f"{rel}: metadata opencoworking.category missing")

    lines = text.splitlines()
    if len(lines) > 500:
        problems.append(f"{rel}: SKILL.md is {len(lines)} lines (max 500)")

    for label, pattern in REQUIRED_SECTION_PATTERNS.items():
        if not re.search(pattern, body, re.I):
            problems.append(f"{rel}: missing required section '{label}'")

    for phrase in VAGUE_PHRASES:
        if phrase in body.lower():
            problems.append(f"{rel}: vague phrase '{phrase}' in stable skill")

    if PLACEHOLDER_RE.search(body):
        m = PLACEHOLDER_RE.search(body)
        problems.append(f"{rel}: unresolved placeholder '{m.group(0)}'")

    if ABS_PATH_RE.search(text):
        problems.append(f"{rel}: absolute local path in SKILL.md")

    # Relative reference targets must exist (skill-local or repo-relative).
    for link in re.findall(r"\]\(([^)#\s]+)\)", body):
        if link.startswith(("http://", "https://", "mailto:")):
            continue
        target = (skill_dir / link).resolve()
        target_repo = (REPO / link).resolve()
        if not target.exists() and not target_repo.exists():
            problems.append(f"{rel}: broken relative reference '{link}'")
    for script in re.findall(r"(?:scripts/[\w./-]+\.(?:py|sh))", body):
        if not (skill_dir / script).exists() and not (REPO / script).exists():
            problems.append(f"{rel}: referenced script '{script}' not found")

    evals = skill_dir / "evals" / "cases.yaml"
    if not evals.is_file():
        problems.append(f"{rel}: missing evals/cases.yaml")
    else:
        try:
            cases = yaml.safe_load(evals.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            problems.append(f"{rel}: evals/cases.yaml invalid YAML: {e}")
            cases = None
        if isinstance(cases, dict):
            if cases.get("skill") != skill_dir.name:
                problems.append(f"{rel}: evals skill field mismatch")
            trig = cases.get("triggers") or {}
            if len(trig.get("positive") or []) < 2:
                problems.append(f"{rel}: evals need >=2 positive triggers")
            if len(trig.get("negative") or []) < 1:
                problems.append(f"{rel}: evals need >=1 negative trigger")
            if len(cases.get("tasks") or []) < 2:
                problems.append(f"{rel}: evals need >=2 task cases")

    # Secrets scan over the entire skill dir.
    for f in skill_dir.rglob("*"):
        if f.is_file() and f.suffix in {".md", ".yaml", ".yml", ".py", ".json", ".txt", ".csv"}:
            content = f.read_text(encoding="utf-8", errors="replace")
            for sre in SECRET_RES:
                if sre.search(content):
                    problems.append(f"{rel}: possible secret in {f.name} ({sre.pattern[:25]}...)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skills against the quality standard.")
    parser.add_argument("--skills-dir", default=str(REPO / ".agents" / "skills"))
    args = parser.parse_args(argv)

    skills_dir = Path(args.skills_dir)
    if not skills_dir.is_dir():
        print(f"error: {skills_dir} not found", file=sys.stderr)
        return 1
    problems: list[str] = []
    descriptions: dict[str, str] = {}
    names: set[str] = set()
    dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir())
    for skill_dir in dirs:
        validate_skill(skill_dir, problems, descriptions, names)

    print(f"Validated {len(dirs)} skills.")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("All skills pass validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
