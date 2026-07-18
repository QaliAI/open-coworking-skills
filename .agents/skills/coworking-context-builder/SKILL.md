---
name: coworking-context-builder
description: Builds a reusable operator profile for a coworking or flex-workspace business by interviewing the operator about locations, products, inventory, pricing, team, sales stages, systems, KPIs, and terminology, and saving it as a structured file other coworking skills reuse. Use when an operator says "set up my space", "remember my locations/pricing", "build my operator profile", or before running other coworking analyses for the first time.
license: Apache-2.0
metadata:
  opencoworking.category: foundation
  opencoworking.version: "0.1.0"
  opencoworking.maturity: stable
  opencoworking.risk: r1
  opencoworking.data-sensitivity: internal
---

# Coworking context builder

## Purpose and operator problem

Every coworking analysis depends on operator-specific facts: what products
exist, which occupancy definition the owner uses, who owns sales follow-up,
which systems hold the data. Without a saved profile, each skill re-asks the
same questions and risks silently assuming wrong defaults. This skill builds
`operator-profile.md` once and keeps facts separated from assumptions.

## When to use

- First engagement with a new operator, before analytical skills run
- The operator wants stored context updated (new location, price change)
- Another coworking skill reports missing profile fields

## When not to use

- Analyzing data exports (use `coworking-wms-export-analyzer`)
- Mapping export columns (use `coworking-data-dictionary`)
- One-off questions that need no persistent context

## Operating modes

- **Mode 1 (guided manual)** — interview the operator section by section. Fully
  supported; no code needed.
- **Mode 2 (export analysis)** — if the operator provides inventory or
  membership exports, pre-fill inventory/product sections from them and ask
  only for confirmation. Run `opencoworking inspect <file>` first.
- **Mode 3 (connected)** — not supported; this skill never reads live systems.

## Required inputs

Operator answers (or documents) covering at minimum: location list, product
list, sellable inventory summary, currency, and which systems hold CRM,
workspace management, and accounting data.

## Optional inputs

Pricing sheets, org chart/roles, marketing channel list, existing KPI
definitions, brand terminology, approval rules ("who may approve discounts").

## Definitions

Use the shared vocabulary in this skill's [references/profile-template.md](references/profile-template.md)
and keep the operator's own words in a `terminology` section when they differ
(e.g. they say "studios" for private offices).

## Workflow

1. Explain what will be produced and where it will be saved (default:
   `operator-profile.md` in the working directory; ask before writing anywhere
   else). Never store credentials in the profile.
2. Work through the template sections in order: identity, locations, products,
   inventory, pricing, target customers, team and roles, sales process and
   stage definitions, membership lifecycle, systems, marketing channels, KPI
   definitions, approval requirements, terminology.
3. For each answer, record it under **Facts** only if the operator stated it or
   a provided document shows it. Anything inferred goes under **Assumptions**
   with the reasoning. Unanswered fields are listed under **Missing** — never
   silently defaulted.
4. For KPI definitions, ask the two highest-impact questions explicitly:
   which occupancy definition they manage to (unit-count, workstation, or
   financial — show the one-line difference), and what counts as a "lead".
5. Write the file, show a summary of Facts vs Assumptions vs Missing counts,
   and list the top 3 missing fields that would most improve later analyses.

## Decision logic

- A field is a **Fact** only with an explicit operator statement or document.
- Conflicting statements: keep both, mark `CONFLICT`, ask once; if
  unresolved, leave under Missing with the conflict noted.
- Numbers that don't reconcile (e.g. stated 60 workstations but inventory
  sums to 54) are recorded with both values and flagged — this skill never
  picks a winner.

## Data-quality checks

Before saving: every location has a timezone; every product maps to a
canonical product type (or is listed under terminology); sellable inventory
numbers reconcile with any provided export within stated tolerance.

## Output contract

`operator-profile.md` following the template in references, with `Facts`,
`Assumptions`, and `Missing` clearly separated, a `last_updated` date, and no
credentials, API keys, or member personal data.

## Evidence and confidence

The profile records the source of each section (interview date, document
name). Sections built from documents cite the document; sections from memory
of a conversation say so.

## Edge cases

- Multi-location operators with different definitions per location: store
  per-location overrides rather than forcing one definition.
- Franchise/branded operators: record brand rules under approval requirements;
  do not reproduce franchise manual content into the profile.
- Operators mid-migration between systems: record both systems with dates.

## Privacy and security

Profile is `internal` sensitivity: business structure, pricing, and staff
roles, but no member personal data, no credentials, no contracts. If the
operator pastes member data during the interview, use it for the answer but
do not store it in the profile.

## Failure and escalation

If the operator cannot answer the minimum required inputs, save a partial
profile with an explicit `INCOMPLETE` banner listing blockers — do not guess.

## Example

**Request:** "Set up my context: we're Harbor Works, one location in Portland,
32 offices, 40 desks, we use Nexudus and HubSpot."

**Output (excerpt):**

```markdown
# Operator profile — Harbor Works
last_updated: 2026-07-17

## Facts
- Locations: Portland (1). Timezone: MISSING (asked, pending)
- Inventory: 32 private offices, 40 dedicated desks (operator statement,
  not yet reconciled against a Nexudus export)
- Systems: WMS = Nexudus, CRM = HubSpot, Accounting: MISSING

## Assumptions
- Currency USD (US location; confirm)

## Missing (top priority first)
1. Occupancy definition the owner manages to
2. Lead definition and sales stages in HubSpot
3. Portland timezone confirmation (assumed America/Los_Angeles? NOT stored
   as fact)
```

## Evals

See [evals/cases.yaml](evals/cases.yaml).

## Version

0.1.0 (stable). Changes require updating evals and the catalog entry.
