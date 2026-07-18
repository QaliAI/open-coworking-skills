# Analyze your first export

Goal: go from "a CSV my software gave me" to a trustworthy analysis.

## 1. Export

From your WMS or CRM, export the list you care about (leads, memberships,
invoices...) as CSV. XLSX works too (install the xlsx extra). Don't clean
it by hand first — the tooling wants to see the problems.

## 2. Identify

```bash
python -m opencoworking.cli inspect "path/to/your export.csv"
```

The inspector guesses the entity from **column names only** (filenames
lie) and reports structural problems. If confidence is low, it lists
candidates — you confirm, it never assumes.

## 3. Quality-check

```bash
python -m opencoworking.cli quality "path/to/your export.csv" --date-columns created_at --key-columns email --required source
```

Adjust the columns to your file. You get findings with row numbers:
duplicates, blanks, unparseable or mixed date formats (slash dates are
read month-first — the report says so; tell it if your locale is
day-first). Exit code 2 means error-grade problems: fix or acknowledge
before analyzing.

## 4. Map (if your columns aren't canonical)

If headers don't match the [generic CSV format](../../adapters/generic-csv/README.md),
use the `coworking-data-dictionary` skill with your assistant, or rename
columns per your system's guide in [adapters/](../../adapters/README.md).
The traps that matter: monthly vs term-total money columns, people vs
paying companies, cancellation vs end dates. Never guess these.

## 5. Analyze

Now run the analysis matching your question — `occupancy`, `pipeline`,
`speed-to-lead`, `sources`, `funnel`, `leakage`, `vo-reconcile` — or ask
your assistant, which will route to the right skill. Every output shows
its formulas and its data caveats; read those lines first.

## Practice run

The whole flow works on the synthetic demo files in
`examples/synthetic-space/data/` — same commands, planted problems,
[documented expected findings](../../examples/synthetic-space/README.md).
