# Governance

## Model

OpenCoworking Skills uses maintainer governance with public process:
decisions happen in issues and PRs, and this document defines who decides
what. As the contributor base grows, this model is expected to evolve
toward a small technical steering group; changes to governance itself are
proposed by PR to this file.

## Roles

- **Maintainers** — merge rights; accountable for the quality standard,
  releases, and security response. Initial maintainer: the repository
  owner. New maintainers are invited by existing maintainers after a
  record of high-quality contributions.
- **Skill owners** — each stable skill lists an owner (default: the
  maintainers collectively; recorded per-skill in `catalog/skills.yaml`
  when individual ownership exists). Owners review changes to their skill
  and its evals.
- **Contributors** — anyone submitting PRs under the DCO.

## Decision rules

- Routine changes: one maintainer approval.
- New stable skills, breaking schema changes, licensing or governance
  changes: all maintainers (while few) or majority (when >3).
- Security issues: maintainers may act first and document after.

## Maturity promotion process

Maturity levels: `experimental` → `beta` → `stable` → (`deprecated`).

A skill may be promoted to **stable** only when ALL of the following hold
(verified in the promoting PR):

1. Complete documentation per the skill anatomy in
   [docs/skill-authoring/quality-standard.md](docs/skill-authoring/quality-standard.md)
2. Trigger evals (positive, negative, ambiguous) present
3. Output/task evals present, with deterministic command cases wherever
   the skill has computable outputs
4. Privacy review recorded in the PR (data classes touched, injection
   surface considered)
5. At least one realistic worked example
6. `python scripts/validate_skills.py` and `scripts/run_evals.py` pass
7. A named owner or explicit maintainer-collective ownership

**Deprecation**: a stable skill that misleads operators or can't be
maintained is marked `deprecated` in frontmatter and catalog with a
pointer to its replacement, kept for two minor releases, then moved out of
`.agents/skills/`.

## Releases

Maintainers cut releases per the versioning policy in
[docs/skill-authoring/versioning-policy.md](docs/skill-authoring/versioning-policy.md).
No release ships with failing validators, tests, or evals.
