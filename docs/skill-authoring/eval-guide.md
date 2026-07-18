# Eval guide

Every production skill needs eval coverage across triggering, task
performance, and safety. Cases live in each skill's `evals/cases.yaml`;
`python scripts/run_evals.py` validates structure and executes the
deterministic cases.

## Case kinds

### `kind: command` — deterministic (the floor)

The command runs from the repo root; stdout+stderr must contain every
`expect_contains` string. Use for every computable output: metric values
against the synthetic demo's hand-computed fixtures, finding IDs, refusal
messages from the CLI. `{tmp}` in arguments becomes a fresh temp dir.
These run in CI on every PR — an analysis regression fails the build.

### `kind: checklist` — graded

A prompt plus observable expected outcomes. Graded by a human reviewer or
by an agent instructed to check each expectation literally. Write
expectations as observations ("OF-104 not offered as an option"), not
qualities ("output is good"). **An LLM grader is never the only gate**:
each skill must also have command cases or a deterministic structural
check for its core claims where computable; purely behavioral skills
(drafting, coaching) compensate with more precise checklist expectations.

## What to cover per skill

- **Triggering**: ≥2 positive prompts in operator language; ≥1 negative
  prompt naming the skill that SHOULD trigger; ≥1 ambiguous prompt with a
  note on acceptable routing. Negative triggers are how the collection
  avoids overlap wars.
- **Happy path**: a realistic task with observable outcomes.
- **Missing data**: the skill degrades honestly (drops sections, names
  blockers) instead of inventing.
- **Conflicting data**: contradictions surfaced, not resolved silently.
- **Privacy/safety**: at least one refusal case — false urgency, consent
  violation, legal-advice request, credential storage, or prompt
  injection via imported data (the demo's `reviews.csv` REV-04 exists
  for this).
- **Known answers**: every formula the skill relies on has a command case
  hitting the synthetic demo, whose expected values were computed BY HAND
  from the literal rows (see `tests/fixtures/synthetic_expected.json` —
  never regenerate those numbers by running the code under test).
- **Output format**: JSON outputs asserted via `expect_contains` on keys.

## Grading dimensions (for checklist reviews)

Outcome (required artifact produced?), process (intended sequence and
checks used?), triggering (activated when it should, stayed quiet when a
sibling skill was better?), accuracy (formulas correct?), evidence
(facts/calculations/assumptions/hypotheses separated?), safety (no PII
exposure, no unauthorized actions?), efficiency (no sprawling output or
unnecessary files?).

## Regression rule

Bug fixes add a case reproducing the bug. Formula changes update the
hand-computed fixtures FIRST (by hand, with the arithmetic in the PR
description), then the code, then verify.
