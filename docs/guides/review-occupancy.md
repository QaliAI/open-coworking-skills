# Review occupancy properly

"How full are we?" has three correct answers, and confusing them is how
full-looking spaces go broke.

## The three numbers

```bash
python -m opencoworking.cli occupancy --inventory inventory.csv --memberships memberships.csv --as-of 2026-07-01
```

- **Office occupancy (count)** — occupied sellable in-service offices ÷
  the same pool. The "feels full" number.
- **Workstation occupancy** — capacity-weighted. A 6-person office counts
  6 whether 1 or 6 people use it; this measures contracted consumption,
  not attendance.
- **Financial occupancy** — contracted revenue ÷ list-price potential.
  The "bank account" number.

The dashboard prints each with numerator, denominator, and exclusions.
Never quote one without saying which it is.

## Read the flags before the percentages

The output flags the distortions:

- **Out-of-service units** — excluded from denominators, so they IMPROVE
  your percentages while earning nothing. Check each is genuinely
  unusable and has a return date.
- **Complimentary occupancy** — comped desks count as occupied but
  contribute zero revenue; they widen the count-vs-financial gap.
- **Missing list prices** — excluded from financial occupancy entirely;
  set the prices or the number is blind to those units.
- **Deep discounts** — units above the threshold (default 25%) are where
  physical occupancy hides revenue gaps.
- **Referential issues** — active memberships with no unit (floating —
  fine, but excluded from unit occupancy), memberships past their end
  date still marked active (data rot that corrupts everything).

## Interpret the spread

- Financial ≪ workstation → discounts and comps are the story.
- Workstation ≪ office-count → your big offices are empty (or only small
  ones are full) — a unit-mix problem, not a marketing problem.
- Both high, revenue still low → billing gaps; run the
  [leakage audit](audit-your-sales-pipeline.md#leakage) next.

## What this can't tell you

Physical attendance ("how many humans showed up") needs access/check-in
data — a different measure (utilization) this dashboard doesn't fake.
Mid-month proration is ignored by the as-of snapshot; monthly revenue
totals come from invoices, not from this view.
