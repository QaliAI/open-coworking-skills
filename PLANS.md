# PLANS.md — OpenCoworking Skills execution plan

This file is the durable execution plan for building and maintaining this repository.
It is written to survive context resets: any agent or contributor should be able to
resume work from this file plus `AGENTS.md` and `BUILD_REPORT.md`.

## Mission

Build the most useful, trusted, portable, and rigorously tested collection of AI agent
skills for coworking and flexible-workspace operators. Quality outranks skill count.
Every stable skill must solve a real operating problem, define inputs/outputs, handle
edge cases, and prove usefulness through tests or realistic examples.

## Canonical decisions (do not re-litigate without new evidence)

| Decision | Choice | Evidence |
|---|---|---|
| Skill format | Agent Skills open spec (agentskills.io/specification, accessed 2026-07-17) | Spec fetched; name ≤64 chars lowercase/hyphen, description ≤1024 chars, optional `license`/`compatibility`/`metadata` |
| Canonical skill directory | `.agents/skills/` | Codex reads `.agents/skills` at repo root; `gh skill install` targets `.agents/skills/` project scope |
| License | Apache-2.0 | Permissive, patent grant, standard for skill repos (Anthropic skills, OpenAI examples use MIT/Apache-style permissive) |
| Language/runtime | Python 3.11+ floor, stdlib-first, `openpyxl` optional extra for XLSX | Installed interpreter is 3.13; stdlib CSV keeps zero-install Mode 2 |
| Contribution certification | DCO (Developer Certificate of Origin) sign-off | Lighter than CLA, standard for Apache-2.0 community projects |
| Repo owner placeholder | `QaliAI` (authenticated `gh` user at build time) | `gh api user` on 2026-07-17 |
| Metric definitions | Never claim universal standards; every formula states numerator/denominator/exclusions/period | Coworking terminology is inconsistent across vendors |
| Risk model | R0–R4 tiers; public skills default R0/R1; no silent R2–R4 | Defined in `docs/security/data-handling.md` |

## Build phases and status

- [x] Phase 0 — Environment: git init (branch `main`), tool inventory (git 2.49, Python 3.13.3, gh 2.92 authed as QaliAI, node 24; Codex CLI not installed locally)
- [x] Phase 1 — Research: Agent Skills spec, Codex skills docs, Claude Code skills docs, `gh skill` manual, client showcase. Recorded in `docs/research/`.
- [x] Phase 2 — Governance scaffold: PLANS, AGENTS, LICENSE, NOTICE, THIRD_PARTY_NOTICES, .gitignore
- [x] Phase 3 — Shared tooling: `src/opencoworking` package + unit tests
- [x] Phase 4 — Domain model: `schemas/`, `references/`, `adapters/generic-csv/`
- [x] Phase 5 — Synthetic demo workspace (`examples/synthetic-space/`) + expected-answer fixtures
- [x] Phase 6 — 24 production skills under `.agents/skills/` with evals
- [x] Phase 7 — Catalog (`catalog/`), validators (`scripts/`), README generation
- [x] Phase 8 — Docs: installation, guides, security, skill authoring
- [x] Phase 9 — CI (`.github/`), templates, dependabot
- [x] Phase 10 — Final verification, BUILD_REPORT.md, scoped commits

## Working rules for resumption

1. Read `AGENTS.md` first; it governs all future work.
2. Run `python scripts/validate_skills.py` and `python -m pytest` before and after changes.
3. Never add a skill to `.agents/skills/` unless it meets the stable bar in
   `docs/skill-authoring/quality-standard.md`; incomplete skills go in `ROADMAP.md`.
4. Never fabricate outputs, metrics, integrations, badges, or industry statistics.
5. Do not publish or create a public remote without explicit maintainer authorization.
6. Record every outside source in `docs/research/SOURCES.yaml` before adapting anything.

## Next development wave (post-initial-build)

See `ROADMAP.md` and the "Recommended next development wave" section of `BUILD_REPORT.md`.
