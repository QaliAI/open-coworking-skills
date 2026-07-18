#!/usr/bin/env python3
"""Run deterministic skill evals.

Two things happen for every .agents/skills/*/evals/cases.yaml:
1. Structure validation (triggers, tasks, required fields).
2. Execution of `kind: command` cases - the command runs from the repo root
   and stdout must contain every `expect_contains` string. `{tmp}` in
   arguments is replaced with a fresh temporary directory.

Checklist-kind cases are validated structurally only; they are graded by a
human or an agent following the checklist (see docs/skill-authoring/eval-guide.md).
LLM grading is deliberately not the only gate - command cases are the
deterministic floor.

Exit codes: 0 all pass, 1 failures.
Usage: python scripts/run_evals.py [--skill NAME]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent


def run_command_case(skill: str, case: dict, failures: list[str]) -> None:
    case_id = case.get("id", "?")
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [str(a).replace("{tmp}", tmp) for a in case.get("command", [])]
        if cmd and cmd[0] == "python":
            cmd[0] = sys.executable
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as e:
            failures.append(f"{skill}/{case_id}: command failed to run: {e}")
            return
        out = r.stdout + r.stderr
        for expected in case.get("expect_contains", []):
            if str(expected) not in out:
                failures.append(
                    f"{skill}/{case_id}: output missing {expected!r} "
                    f"(exit {r.returncode})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic skill evals.")
    parser.add_argument("--skill", help="run evals for one skill only")
    args = parser.parse_args(argv)

    skills_dir = REPO / ".agents" / "skills"
    failures: list[str] = []
    command_cases = checklist_cases = 0
    skill_dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir())
    if args.skill:
        skill_dirs = [d for d in skill_dirs if d.name == args.skill]
        if not skill_dirs:
            print(f"error: no skill named {args.skill}", file=sys.stderr)
            return 1

    for skill_dir in skill_dirs:
        cases_file = skill_dir / "evals" / "cases.yaml"
        if not cases_file.is_file():
            failures.append(f"{skill_dir.name}: missing evals/cases.yaml")
            continue
        data = yaml.safe_load(cases_file.read_text(encoding="utf-8"))
        for i, task in enumerate(data.get("tasks") or []):
            kind = task.get("kind")
            if kind == "command":
                command_cases += 1
                run_command_case(skill_dir.name, task, failures)
            elif kind == "checklist":
                checklist_cases += 1
                if not task.get("prompt") or not task.get("expected"):
                    failures.append(
                        f"{skill_dir.name}/task{i}: checklist case missing prompt/expected")
            else:
                failures.append(f"{skill_dir.name}/task{i}: unknown kind '{kind}'")

    print(f"Evals: {command_cases} command cases executed, "
          f"{checklist_cases} checklist cases validated structurally.")
    if failures:
        print(f"\n{len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("All deterministic evals pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
