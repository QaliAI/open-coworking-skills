# Audit your sales pipeline

Run this monthly; it takes fifteen minutes and usually pays for itself in
the first run.

## 1. Hygiene first

```bash
python -m opencoworking.cli pipeline --deals deals.csv --as-of 2026-07-01
```

You get row-level findings in action order: overdue next actions →
missing next actions → unassigned deals → stale deals → duplicate open
deals → invalid stages. Work the list top down — an unassigned, stale,
duplicated deal (the demo's D-2002) is a deal that's silently dead.

Conversion analysis on a dirty pipeline is fiction; fix hygiene findings
(or at least acknowledge them) before reading rates.

## 2. Funnel and speed

```bash
python -m opencoworking.cli funnel --leads leads.csv --tours tours.csv --deals deals.csv
python -m opencoworking.cli speed-to-lead --leads leads.csv
python -m opencoworking.cli sources --leads leads.csv
```

Definitions are printed with each rate. Watch for: leads nobody ever
touched (listed by ID), the tour show rate, and source labels that need
normalizing before any channel judgment.

If conversion is weak and you don't know where, the
`coworking-lead-to-tour-diagnostic` skill walks the nine checkpoints in
causal order — resist the reflex that every conversion problem is a
marketing-volume problem.

## 3. Leakage

<a name="leakage"></a>

```bash
python -m opencoworking.cli leakage --as-of 2026-07-01 --leads leads.csv --deals deals.csv --tours tours.csv --memberships memberships.csv --invoices invoices.csv --inventory inventory.csv
```

Findings come in three never-summed classes: **billing gaps** (likely
real money — unbilled active memberships, failed/overdue invoices),
**process gaps** (pipeline value at risk — untouched leads, ghosted
tours, won deals never converted to agreements), **inventory** (idle
list value). Checks that couldn't run for lack of files are listed —
absence of a finding is not absence of a problem.

Two findings deserve same-day action whenever they appear: a won deal
with no membership (someone said yes and nothing happened), and an
active membership with no recent invoice.

## 4. Close the loop

Assign every finding to a person with a date. Next month, run it again —
the diff is your process improvement, measured.
