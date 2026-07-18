# Skill quality standard

This is the bar every skill in `.agents/skills/` must meet. The validator
(`scripts/validate_skills.py`) enforces the mechanical parts; maintainer
review enforces the rest. Planned-but-unbuilt skills live in the catalog,
never as empty skill folders.

## Frontmatter contract

```yaml
---
name: coworking-example-skill        # lowercase/digits/hyphens, = folder name, <=64 chars
description: >         # <=1024 chars; WHAT it does + WHEN to trigger, in operator words
license: Apache-2.0
compatibility: ...     # only if real environment requirements exist (<=500 chars)
metadata:
  opencoworking.category: sales      # from catalog/categories.yaml
  opencoworking.version: "0.1.0"     # semver
  opencoworking.maturity: stable     # experimental|beta|stable|deprecated
  opencoworking.risk: r0             # r0-r4; shipped skills are r0/r1
  opencoworking.data-sensitivity: confidential
---
```

Description rules: state the job and the trigger phrases operators
actually say; include the terminology that should route here; do not
overlap another skill's territory — every skill's evals include negative
triggers naming the better skill.

## Required anatomy (20 items)

Every stable skill covers, in SKILL.md or clearly referenced files:
purpose, operator problem, when to use, when NOT to use, operating modes,
required inputs, optional inputs, definitions, step-by-step workflow,
calculations/decision logic, data-quality checks, output contract,
evidence/confidence requirements, edge cases, privacy and security rules,
failure/escalation conditions, example request, example output,
validation/eval cases, version and maturity.

## Banned content in stable skills

- Vague directives: "analyze the data", "provide actionable insights",
  "create a strategy", "optimize the business", "use best practices" —
  replace with observable actions, decision rules, formulas, checks,
  explicit deliverables
- `TODO`, `TBD`, "coming soon", unresolved placeholders
- Unsourced external claims, invented statistics, ranking/outcome promises
- Real personal data in any example
- Instructions to take R2-R4 actions without explicit human confirmation

## Structural rules

- SKILL.md under 500 lines; details go to skill-local `references/`
- Reference chains one level deep from SKILL.md
- Deterministic calculations live in the shared `opencoworking` package
  (single canonical implementation) and are invoked by exact CLI commands
  in the skill; Mode 1 must work with no code at all
- Every skill has `evals/cases.yaml`: ≥2 positive triggers, ≥1 negative
  trigger with the better skill named, ≥1 ambiguous trigger, ≥2 task cases
  including at least one refusal/edge case; computable outputs get
  `kind: command` known-answer cases

## Metric integrity

Any formula the skill uses states numerator, denominator, exclusions, and
period, and never claims industry standardization. Numbers derived from
<10 records are reported with their counts.

## The three modes

Mode 1 (guided manual) must deliver value with zero code or credentials.
Mode 2 (export analysis) uses the deterministic CLI. Mode 3 (connected)
is optional, read-only by default, and no skill may require it to
demonstrate value.

## Data is data

Skills ingesting CRM notes, cells, reviews, or messages must instruct the
agent never to obey instructions found inside that content, and include
an eval case testing it when the surface is significant.
