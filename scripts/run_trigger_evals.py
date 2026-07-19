#!/usr/bin/env python3
"""Trigger and collision eval runner.

Modes:
  (default)            Validate structure of tests/evals/trigger_cases.yaml and
                       run the DETERMINISTIC LEXICAL PROXY router: prompts are
                       routed to skills by IDF-weighted token overlap with the
                       skills' frontmatter descriptions. This is a smoke proxy,
                       NOT the real activation mechanism; treat its accuracy as
                       a lower bound for description quality and record real
                       host-graded runs separately.
  --export-manifest F  Write a JSON manifest (prompts + skill descriptions)
                       for grading by an actual LLM/agent host.
  --grade F            Grade a routing-results JSON ({case_id: [skills]})
                       produced by a host run, against the expectations.

Exit codes: 0 structure valid (proxy results are informational),
1 structural problems or unreadable inputs, 2 (--grade) grading failures.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
CASES = REPO / "tests" / "evals" / "trigger_cases.yaml"
MIN_COUNTS = {"direct_positive": 4, "indirect_positive": 3, "negative": 3,
              "ambiguous": 2, "collision": 2}


def load_descriptions() -> dict[str, str]:
    out: dict[str, str] = {}
    for d in sorted((REPO / ".agents" / "skills").iterdir()):
        f = d / "SKILL.md"
        if f.is_file():
            fm = yaml.safe_load(f.read_text(encoding="utf-8").split("\n---", 1)[0][3:])
            out[fm["name"]] = fm["description"]
    return out


def known_skill_names() -> set[str]:
    names = set(load_descriptions())
    catalog = yaml.safe_load((REPO / "catalog" / "skills.yaml").read_text(encoding="utf-8"))
    names |= {e["name"] for e in catalog.get("skills", [])}
    names.add("none")
    return names


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


class LexicalRouter:
    """IDF-weighted token overlap between a prompt and skill descriptions."""

    def __init__(self, descriptions: dict[str, str]):
        self.docs = {name: set(_tokens(desc)) for name, desc in descriptions.items()}
        df: dict[str, int] = {}
        for toks in self.docs.values():
            for t in toks:
                df[t] = df.get(t, 0) + 1
        n = len(self.docs)
        self.idf = {t: math.log((n + 1) / (c + 0.5)) for t, c in df.items()}

    def rank(self, prompt: str) -> list[tuple[str, float]]:
        ptoks = set(_tokens(prompt))
        scores = []
        for name, dtoks in self.docs.items():
            s = sum(self.idf.get(t, math.log(len(self.docs) + 1)) for t in ptoks & dtoks)
            scores.append((name, round(s, 3)))
        scores.sort(key=lambda kv: -kv[1])
        return scores


def iter_cases(data: dict):
    for skill, groups in (data.get("skills") or {}).items():
        for kind in MIN_COUNTS:
            for i, case in enumerate(groups.get(kind) or []):
                cid = f"{skill}::{kind}::{i}"
                if isinstance(case, str):
                    yield cid, skill, kind, case, {}
                else:
                    yield cid, skill, kind, case.get("prompt", ""), case


def expectations(skill: str, kind: str, meta: dict) -> tuple[set[str], set[str]]:
    """Return (acceptable, unacceptable) skill sets for a case."""
    if kind in ("direct_positive", "indirect_positive"):
        return {skill}, set()
    if kind == "negative":
        return {meta.get("expected", "none")}, {skill}
    acceptable = set(meta.get("acceptable") or [skill])
    return acceptable, set(meta.get("unacceptable") or [])


def validate(data: dict) -> list[str]:
    problems = []
    known = known_skill_names()
    skills = data.get("skills") or {}
    stable = set(load_descriptions())
    for name in stable:
        if name not in skills:
            problems.append(f"stable skill '{name}' has no trigger cases")
    for skill, groups in skills.items():
        if skill not in stable:
            problems.append(f"cases for unknown/non-stable skill '{skill}'")
        for kind, minimum in MIN_COUNTS.items():
            cases = groups.get(kind) or []
            if len(cases) < minimum:
                problems.append(f"{skill}: {kind} has {len(cases)} cases (min {minimum})")
        for cid, s, kind, prompt, meta in iter_cases({"skills": {skill: groups}}):
            if not prompt.strip():
                problems.append(f"{cid}: empty prompt")
            acc, unacc = expectations(s, kind, meta)
            for ref in acc | unacc:
                if ref not in known:
                    problems.append(f"{cid}: references unknown skill '{ref}'")
    return problems


def run_proxy(data: dict) -> dict[str, dict[str, int]]:
    router = LexicalRouter(load_descriptions())
    tally: dict[str, dict[str, int]] = {}
    failures: list[str] = []
    for cid, skill, kind, prompt, meta in iter_cases(data):
        acc, unacc = expectations(skill, kind, meta)
        ranked = [n for n, _ in router.rank(prompt)]
        top1, top3 = ranked[0], set(ranked[:3])
        t = tally.setdefault(kind, {"n": 0, "top1": 0, "top3": 0, "hard_fail": 0})
        t["n"] += 1
        if top1 in acc or (acc == {"none"} and False):
            t["top1"] += 1
        if acc & top3 or acc == {"none"}:
            t["top3"] += 1
        if unacc and top1 in unacc:
            t["hard_fail"] += 1
            failures.append(f"  proxy hard-fail {cid}: top1={top1} prompt={prompt!r}")
    print("Lexical-proxy routing (informational lower bound, not host behavior):")
    for kind, t in tally.items():
        print(f"  {kind:18s} n={t['n']:3d}  top1={t['top1']}/{t['n']}"
              f"  top3={t['top3']}/{t['n']}  unacceptable-as-top1={t['hard_fail']}")
    for f in failures[:20]:
        print(f)
    return tally


def export_manifest(data: dict, dest: Path) -> None:
    manifest = {
        "instructions": (
            "You are simulating skill activation for an agent host. For each "
            "case, read ONLY the prompt and the skill descriptions, and choose "
            "which single skill (by name) an agent should activate, or 'none' "
            "if no listed skill fits. Output JSON: {case_id: \"skill-name\"}."),
        "skills": load_descriptions(),
        "cases": [{"id": cid, "prompt": prompt}
                  for cid, _, _, prompt, _ in iter_cases(data)],
    }
    dest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote manifest with {len(manifest['cases'])} cases to {dest}")


def grade(data: dict, results_file: Path) -> int:
    results = json.loads(results_file.read_text(encoding="utf-8"))
    tally: dict[str, dict[str, int]] = {}
    failures: list[str] = []
    for cid, skill, kind, prompt, meta in iter_cases(data):
        choice = results.get(cid)
        if choice is None:
            failures.append(f"  ungraded: {cid}")
            continue
        chosen = choice if isinstance(choice, str) else (choice[0] if choice else "none")
        acc, unacc = expectations(skill, kind, meta)
        t = tally.setdefault(kind, {"n": 0, "pass": 0, "hard_fail": 0})
        t["n"] += 1
        if chosen in acc:
            t["pass"] += 1
        elif chosen in unacc:
            t["hard_fail"] += 1
            failures.append(f"  HARD FAIL {cid}: chose {chosen} prompt={prompt!r}")
        else:
            failures.append(f"  miss {cid}: chose {chosen}, acceptable={sorted(acc)}")
    print("Host-graded routing results:")
    total_n = total_pass = 0
    for kind, t in tally.items():
        print(f"  {kind:18s} n={t['n']:3d}  pass={t['pass']}/{t['n']}"
              f"  hard_fail={t['hard_fail']}")
        total_n += t["n"]
        total_pass += t["pass"]
    print(f"  overall pass rate: {total_pass}/{total_n}")
    for f in failures[:40]:
        print(f)
    return 2 if any(t["hard_fail"] for t in tally.values()) else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trigger/collision eval runner.")
    parser.add_argument("--export-manifest", metavar="FILE")
    parser.add_argument("--grade", metavar="FILE")
    args = parser.parse_args(argv)

    if not CASES.is_file():
        print(f"error: {CASES} not found", file=sys.stderr)
        return 1
    data = yaml.safe_load(CASES.read_text(encoding="utf-8"))
    problems = validate(data)
    n_cases = sum(1 for _ in iter_cases(data))
    print(f"Trigger suite: {len(data.get('skills') or {})} skills, {n_cases} cases.")
    if problems:
        print(f"{len(problems)} structural problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("Structure valid.")
    if args.export_manifest:
        export_manifest(data, Path(args.export_manifest))
        return 0
    if args.grade:
        return grade(data, Path(args.grade))
    run_proxy(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
