# Pull request

## What and why

<!-- What does this change, and what operator problem or repo need drives it? -->

## Checklist

- [ ] `python -m pytest` passes
- [ ] `python scripts/validate_skills.py` passes
- [ ] `python scripts/check_catalog.py` passes
- [ ] `python scripts/check_references.py` passes
- [ ] `python scripts/run_evals.py` passes
- [ ] `python scripts/generate_readme_catalog.py --check` passes (regenerate if catalog changed)
- [ ] No real member/client data, no credentials, no secrets anywhere (including fixtures)
- [ ] Every new external factual claim has a source recorded in `docs/research/SOURCES.yaml`
- [ ] Any copied/adapted outside material is license-checked and recorded in `THIRD_PARTY_NOTICES.md`
- [ ] Commits are signed off (DCO, `git commit -s`)

## If this adds or changes a skill

- [ ] Follows `docs/skill-authoring/quality-standard.md` (all 20 anatomy items)
- [ ] `evals/cases.yaml` updated (triggers + tasks; command known-answers where computable)
- [ ] Catalog entry added/updated; maturity honest (new skills start experimental/beta)
- [ ] Formula changes: hand-computed fixture updates included with arithmetic shown below
- [ ] Privacy review: data classes touched and injection surface considered (describe below)

## Privacy / formula notes

<!-- Required when the boxes above apply; otherwise "n/a" -->
