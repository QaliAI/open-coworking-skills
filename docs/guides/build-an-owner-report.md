# Build an owner report

The monthly report is an assembly of analyses you can already run — plus
discipline about what gets claimed.

## Gather

Exports for the month: inventory, memberships, leads, deals, tours,
invoices; room-bookings and events if you track them. Missing files
shrink the report honestly — sections get dropped with a note, never
invented.

## Run the pieces

```bash
python -m opencoworking.cli quality memberships.csv --date-columns start_date,end_date --key-columns membership_id
python -m opencoworking.cli occupancy --inventory inventory.csv --memberships memberships.csv --as-of 2026-06-30
python -m opencoworking.cli funnel --leads leads.csv --tours tours.csv --deals deals.csv
python -m opencoworking.cli speed-to-lead --leads leads.csv
python -m opencoworking.cli leakage --as-of 2026-06-30 --leads leads.csv --deals deals.csv --tours tours.csv --memberships memberships.csv --invoices invoices.csv --inventory inventory.csv
```

Or ask your assistant for "the monthly owner report" — the
`coworking-monthly-owner-report` skill runs this sequence and assembles
the 12 sections: executive summary, KPI scorecard, funnel, occupancy,
revenue, churn/renewals, collections, rooms & events, data-quality
warnings, risks, prioritized actions, methodology appendix.

## The rules that keep it honest

- **Facts, calculations, hypotheses — visually separated.** "Occupancy
  fell 4 points" is a calculation; "because of the road works" is a
  hypothesis and gets labeled as one with a proposed test.
- **Deltas only with prior-period data actually in hand.**
- **No external claims without a source.** No "industry average" filler.
- **Counts with small numbers.** "2 of 3 tours converted (67%)", never
  a bare "67%".
- **Partial months say so** and never annualize.
- **One customer over 25% of MRR** → key metrics shown with and without
  them.
- **Actions ≤7, each with an owner role and its evidence reference.**

Before sending, run the draft through the `coworking-source-verifier`
skill — it flags unsourced claims, unlabeled causal language, and
numbers that don't recompute.

## Template shortcut

The skill's [SKILL.md](../../.agents/skills/coworking-monthly-owner-report/SKILL.md)
contains a worked example against the synthetic demo — copy its shape for
your first report.
