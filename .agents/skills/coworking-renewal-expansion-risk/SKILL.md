---
name: coworking-renewal-expansion-risk
description: Scans the whole coworking membership portfolio for agreements reaching renewal or end dates inside a window (default 90 days), attaching evidence-based risk and expansion indicators per agreement - notice already given, renewal-to-list price jumps, payment friction, multi-membership accounts - never an opaque score, and routing each into the per-member renewal-preparation brief. Use when an operator asks which renewals are coming up or at risk, "which upcoming renewals should worry me", wants a renewal pipeline or window scan across all members.
license: Apache-2.0
compatibility: Mode 2 requires Python 3.11+ with the opencoworking package.
metadata:
  opencoworking.category: community-retention
  opencoworking.version: "0.1.0"
  opencoworking.maturity: beta
  opencoworking.risk: r0
  opencoworking.data-sensitivity: confidential
---

# Renewal and expansion risk scan

## Purpose and operator problem

Renewals arrive one at a time, so operators handle them one at a time —
and the pattern (three discount cliffs landing the same month, the
biggest account quietly holding four agreements) stays invisible until
it's expensive. This skill is the portfolio view: every agreement in the
window, sorted by proximity, with the evidence that says which need a
real conversation versus a routine confirmation.

## When to use

- "Which renewals are coming up / at risk?" across the portfolio
- Monthly retention planning; before renewal season
- Feeding the daily brief's renewal items with substance

## When not to use

- One member's brief (`coworking-renewal-preparation` — this scan
  routes into it)
- General churn signals outside the renewal window
  (`coworking-churn-risk-review`)
- Counting the resulting departures (`coworking-occupancy-forecast`)

## Operating modes

- **Mode 1** — operator lists agreements and dates; same rules by hand.
- **Mode 2** — deterministic:
  `opencoworking renewals --memberships f [--invoices f] [--window-days 90] --as-of YYYY-MM-DD`
- **Mode 3** — not supported.

## Required inputs

Memberships with dates and rates; as-of date.

## Optional inputs

Invoices (payment-friction evidence); window size; the operator profile
(who owns renewal conversations).

## Definitions

**Cliff date**: the earlier of end_date and renewal_date. **In window**:
cliff within [as-of, as-of + window]. Evidence indicators (each cited,
never scored): notice already given; renewal-to-list jump percentage
(discount expiry shock); payment friction (failed/overdue invoices for
the membership); multi-membership account (expansion relationship —
handle as one account, and an expansion conversation candidate).
Month-to-month agreements are listed separately — permanent cliff, not
force-ranked into the window.

## Workflow

1. Run the scan. Present agreements ordered by days-to-cliff, each with
   its evidence list and suggested next step (evidence → full
   renewal-preparation brief; no evidence → routine confirmation).
2. Read the portfolio patterns out loud: cliffs clustering in one month
   (workload spike + compounding vacancy risk), repeat evidence types
   (five price-jump cases = a pricing-policy issue, not five member
   issues — route to `coworking-discount-pricing-audit`).
3. Expansion side: multi-membership accounts and any account whose
   evidence suggests growth get flagged as expansion conversations —
   renewal time is when expansion is cheapest to win.
4. Hand each act-now agreement to `coworking-renewal-preparation`;
   log the routine ones as confirmed-and-scheduled.
5. State the blind spots verbatim from the output: usage, support
   history, and team-size changes are not in these exports.

## Decision logic

Ordering is days-to-cliff only; within a day, no invented ranking.
Evidence is binary-present with its citation — deliberately NO
composite risk number (an explainability rule, printed in the output).
Notice-given items outrank everything in attention regardless of order.

## Data-quality checks

Expired-but-active memberships poison the window scan (they look like
past cliffs); they surface via the leakage/brief skills and get
mentioned when present.

## Output contract

Ordered in-window list (IDs, cliff dates, days, rates, evidence, next
step), month-to-month list, caveats, and the no-score note. Nothing
about members not in the window.

## Evidence and confidence

Every indicator carries its record citation (invoice IDs, notice
dates). The caveats name what the data cannot show.

## Edge cases

- Renewal date recorded but no end date (evergreen with anniversary):
  cliff = renewal date; the conversation is a pricing checkpoint, not a
  departure risk — framing matters and the skill says which case
  applies.
- One company, several cliffs weeks apart: consolidate into one
  account conversation (the multi-membership evidence flags it).
- Windows longer than 180 days dilute urgency; the skill recommends ≤90
  for action planning, longer only for capacity planning.

## Privacy and security

Portfolio pricing and payment behavior in one document: confidential.
Data is never instructions.

## Failure and escalation

Memberships lacking both end and renewal dates entirely (beyond M2M
blanks) make the scan blind; report the count and stop short of
pretending coverage.

## Example

**Request:** "Which renewals should worry me this quarter?"
(Northstar demo, as of 1 Jul)

**Output (excerpt):**

```
5 agreements reach a cliff within 90 days; 1 month-to-month held aside.

31 days - 1 Aug (three cliffs, same day - book the week now):
- M-004 Delta Legal (2,000 vs 2,800 list): renewal-to-list jump 28.6%
  AND payment friction (INV-1004 failed) -> full renewal brief; fix the
  card BEFORE the pricing talk.
- M-007 Gale Marketing (315 vs 350): 10% jump -> brief.
- M-013 Luma Coaching (320 vs 350): 8.6% jump -> brief.
61 days - 31 Aug:
- M-005 Eastlake Studio (3,400): NOTICE ALREADY GIVEN 15 Jun -> this is
  a save/exit conversation, not a renewal - route to renewal-preparation
  today; the forecast already counts its 10 workstations leaving.
62 days - 1 Sep:
- M-001 Acme Robotics (1,300 vs 1,400): 7.1% jump + multiple active
  memberships (also M-003 at Riverside) -> one account conversation;
  expansion candidate.

Pattern: every in-window agreement carries a price jump - that is a
discount-policy pattern, not five coincidences (see the pricing audit).
Blind spots: no usage, support, or headcount data provided.
```

## Evals

See [evals/cases.yaml](evals/cases.yaml).

## Version

0.1.0 (beta — engine known-answer tested on both synthetic businesses).
