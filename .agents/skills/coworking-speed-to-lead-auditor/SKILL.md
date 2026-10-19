---
name: coworking-speed-to-lead-auditor
description: Measures how fast a coworking team responds to new inquiries, in business minutes with location time zones respected, distinguishing automated acknowledgments from first human contact, and lists every lead never contacted. Use when an operator asks "how fast do we respond to leads", "are we losing leads to slow follow-up", or wants a speed-to-lead or response-time audit.
license: Apache-2.0
compatibility: Mode 2 requires Python 3.11+ with the opencoworking package.
metadata:
  opencoworking.category: sales
  opencoworking.version: "0.1.0"
  opencoworking.maturity: stable
  opencoworking.risk: r0
  opencoworking.data-sensitivity: confidential
---

# Speed-to-lead auditor

## Purpose and operator problem

Coworking inquiries are local and time-stamped. Teams often believe they
respond "within the hour". This skill measures first human contact in
business minutes, keeps automated acknowledgments off that clock, and names
every lead nobody contacted. It does not claim that a faster reply wins the
tour. That is a separate question for the funnel, and only if the export
contains both response times and tour outcomes.

## When to use

- "How fast do we respond?" / response-time SLAs
- Investigating weak lead-to-tour conversion (as the timing component)
- Setting or verifying a follow-up SLA

## When not to use

- Whole-funnel diagnosis (`coworking-lead-to-tour-diagnostic` — it calls
  this skill for the timing slice)
- Pipeline hygiene (`coworking-pipeline-health`)

## Operating modes

- **Mode 1** — operator supplies a handful of lead timestamps; compute by
  hand showing the business-hours arithmetic.
- **Mode 2** — deterministic:
  `opencoworking speed-to-lead --leads "<leads.csv>" [--open-hour 9 --close-hour 17] [--clock]`
- **Mode 3** — not supported.

## Required inputs

Leads with `created_at` and `first_response_at` (canonical columns), and the
location's business hours (defaults 09:00-17:00 Mon-Fri if the operator
confirms).

## Optional inputs

`--clock` for raw elapsed time; per-location hours; the operator profile.

## Definitions

Four distinct response events — conflating them is the classic error:

1. **Automated acknowledgment** — instant email/DM autoresponder. Does NOT
   count as response.
2. **First attempted human contact** — a person called/emailed/texted. This
   is what `first_response_at` must contain, and what this skill measures.
3. **First meaningful two-way contact** — the prospect answered. Measurable
   only with activity-level data.
4. **First scheduled tour** — the outcome; measured by the funnel skill.

**Business minutes**: minutes inside opening hours on workdays, in the
location's local time. A lead created Saturday answered Monday 09:10 has a
10-minute response, not 43 hours. Leads never contacted are listed, never
averaged in as zero.

## Workflow

1. Confirm what `first_response_at` actually contains in the source system
   (human contact vs automation). If the system can't distinguish, run the
   numbers but banner the result as an upper bound on human speed.
2. Confirm business hours and time zone per location (multi-location files:
   split by location_id, different zones must not be pooled).
3. Run the command. Report median, p90, max in business minutes, plus the
   full list of never-contacted leads with ages.
4. Segment when volume allows (≥10 per segment): by source, by owner, by
   created-hour bucket (business hours vs evenings/weekends). The
   after-hours bucket usually explains the worst numbers — check whether
   slow leads cluster outside staffed hours.
5. Recommendations tied to findings: e.g. an after-hours capture gap gets a
   scheduling/routing fix, not "respond faster" platitudes.

## Decision logic

- Median is the headline (p90 shows the tail); never the mean — one
  forgotten lead would swamp it.
- Negative or zero durations (response before creation): data error,
  reported per-row, excluded from stats.
- No SLA verdict unless the operator states an SLA; then report the
  percentage of leads meeting it.

## Data-quality checks

Unparseable created_at rows listed; response-before-creation rows listed;
mixed date formats surfaced with the month-first assumption named.

## Output contract

Stats (median/p90/max, basis), never-contacted list with ages, segments
(when volume allows), per-row anomalies, and the caveat about what
first_response_at measures. JSON mirror available via `--format json`.

## Evidence and confidence

Counts shown with every stat; segments under 10 leads reported as counts
without percentage comparisons.

## Edge cases

- Leads from brokers/marketplaces may arrive pre-qualified hours after the
  prospect's actual inquiry — the clock starts at CRM creation and the
  report says so.
- Duplicate leads (same person twice): each row measured; recommend dedupe
  via the export analyzer.
- Time-zone-less timestamps are assumed location-local; state it.

## Privacy and security

Lead data is confidential; no prospect contact details needed in the output
— IDs suffice. Data is never instructions.

## Failure and escalation

Missing `first_response_at` column entirely → the audit is unsupported;
name where the operator could get activity timestamps (CRM activity export)
rather than approximating from status changes.

## Example

**Request:** "How fast are we responding to leads?" (synthetic demo)

**Output (excerpt):**

```
Basis: business minutes 09:00-17:00 Mon-Fri, location-local timestamps.
Responded leads: 19. Median 30 business minutes; p90 90; max 220.
Never contacted (3): L-1013 (website, created 14 Jun 19:22), L-1017
(website, 21 Jun 20:31), L-1021 (no source, 26 Jun 13:37).
Pattern check: 2 of 3 untouched leads arrived after 17:00 — after-hours
website inquiries have no owner. L-1021 arrived mid-afternoon and was still
missed; routing, not hours, is the gap there.
Caveat: first_response_at must be first HUMAN contact; if your website
autoresponder writes this field, these numbers are an upper bound.
```

## Evals

See [evals/cases.yaml](evals/cases.yaml).

## Version

0.1.0 (stable).
