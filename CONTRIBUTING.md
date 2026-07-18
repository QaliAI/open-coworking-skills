# Contributing

Thanks for helping coworking operators get trustworthy AI tooling. This
project values a small number of rigorous skills over a large number of
shallow ones — contributions are reviewed against that standard.

## Ground rules

1. Read [AGENTS.md](AGENTS.md) — it governs all work here, human or agent.
2. Every factual external claim needs a recorded source
   ([docs/research/SOURCES.yaml](docs/research/SOURCES.yaml)).
3. No real member/client data anywhere, including tests and examples.
4. Nothing copied from sources with unclear or incompatible licenses.
5. New skills follow
   [docs/skill-authoring/quality-standard.md](docs/skill-authoring/quality-standard.md)
   and start at `experimental` or `beta` maturity — `stable` is earned
   (see GOVERNANCE.md for promotion).

## Developer Certificate of Origin

By contributing, you certify the [Developer Certificate of Origin 1.1](https://developercertificate.org/):
that you have the right to submit the work under Apache-2.0. Sign off each
commit (`git commit -s`), which adds a `Signed-off-by` line. Contributions
without sign-off can't be merged.

## Getting set up

```bash
git clone <your-fork>
cd open-coworking-skills
python -m pip install -e ".[dev]"
python -m pytest                      # everything should pass before you start
```

## Before opening a PR

Run the full local gate:

```bash
python -m pytest
python scripts/validate_skills.py
python scripts/check_catalog.py
python scripts/check_references.py
python scripts/run_evals.py
python scripts/generate_readme_catalog.py --check
```

## What to contribute

- **Adapters** — the highest-value contribution. Follow the
  `coworking-system-adapter-builder` skill; honest support labels are
  mandatory.
- **Skills** — propose via the skill-proposal issue template first;
  catalog `planned` entries list what each needs.
- **Fixtures and evals** — more known-answer cases for existing skills.
- **Operator review** — running skills on your own (redacted!) data and
  reporting where they mislead is enormously valuable.

## Pull-request checklist

The PR template includes it; the short version: local gate passes, new
skills have evals + example + catalog entry, sources recorded, no PII, no
secrets, no unsourced claims, DCO sign-off present.

## Code style

Python 3.11+, ruff + mypy clean, stdlib-first (new runtime dependencies
need a strong argument), every script has `--help` and never overwrites
inputs by default. Documentation: direct, specific, honest about limits,
readable by nontechnical operators.
