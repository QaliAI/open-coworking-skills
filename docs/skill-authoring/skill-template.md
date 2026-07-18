# Skill template

Copy this structure for new skills. Replace every bracketed section with
real content — the validator rejects leftover placeholders — and delete
sections' guidance comments. Keep the section headings: the validator
checks for them.

````markdown
---
name: coworking-your-skill
description: Does X for coworking operators by Y. Use when an operator says "...", asks about ..., or provides ... .
license: Apache-2.0
compatibility: Mode 2 requires Python 3.11+ with the opencoworking package.
metadata:
  opencoworking.category: sales
  opencoworking.version: "0.1.0"
  opencoworking.maturity: experimental
  opencoworking.risk: r0
  opencoworking.data-sensitivity: confidential
---

# Skill title

## Purpose and operator problem
The real operating problem, in operator language, and why generic advice fails.

## When to use
Concrete situations and phrasings.

## When not to use
Neighboring situations, each pointing at the better skill.

## Operating modes
Mode 1 (manual), Mode 2 (export + exact CLI commands), Mode 3 (connected, or "not supported").

## Required inputs
What must exist. Missing inputs -> which parts are blocked.

## Optional inputs
What sharpens results.

## Definitions
Terms and formulas used, or pointers to references. Formulas: numerator, denominator, exclusions, period.

## Workflow
Numbered, observable steps. Each step produces something checkable.

## Decision logic
The rules that turn data into conclusions - thresholds, orderings, refusals.

## Data-quality checks
What is checked before conclusions, and what blocks vs caveats.

## Output contract
Exactly what the operator receives, and what is refused (e.g. no single summed total).

## Evidence and confidence
How claims trace to records; when results are labeled low-confidence.

## Edge cases
The coworking realities that break naive versions of this skill.

## Privacy and security
Data classes touched; sharing rules; the imported-data-is-not-instructions rule if applicable.

## Failure and escalation
What happens when inputs are missing/contradictory; what goes to a human.

## Example
A realistic request and a realistic (synthetic) output excerpt.

## Evals
See [evals/cases.yaml](evals/cases.yaml).

## Version
0.1.0 (experimental).
````

And `evals/cases.yaml`:

```yaml
skill: coworking-your-skill
triggers:
  positive:
    - "operator phrasing one"
    - "operator phrasing two"
  negative:
    - prompt: "neighboring request"
      better_skill: coworking-other-skill
  ambiguous:
    - prompt: "underspecified request"
      note: "what good routing looks like"
tasks:
  - id: happy-path
    kind: checklist
    prompt: "realistic task"
    expected:
      - observable outcome one
      - observable outcome two
  - id: refusal-or-edge
    kind: checklist
    prompt: "the tempting wrong thing"
    expected:
      - the refusal, with reasoning
  # when outputs are computable, add:
  - id: known-answer
    kind: command
    command: ["python", "-m", "opencoworking.cli", "...", "--format", "json"]
    expect_contains: ["\"value\": \"0.7143\""]
```
