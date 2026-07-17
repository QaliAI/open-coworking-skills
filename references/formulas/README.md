# Metric formulas

Canonical formulas used by every analytical skill in this repository. Coworking
terminology is **not standardized across the industry**; these are this
project's documented definitions, implemented and unit-tested in
`src/opencoworking/metrics.py`. When an operator uses a different definition,
skills must apply the operator's definition and say which one was used.

Every metric statement must name: numerator, denominator, exclusions, and
reporting period, and must distinguish count-based from revenue-based measures.

## Occupancy family

| Metric | Numerator | Denominator | Excludes |
|---|---|---|---|
| Office occupancy (count) | occupied sellable in-service offices | sellable in-service offices | out-of-service, non-sellable |
| Workstation occupancy | capacity of occupied sellable in-service units | capacity of all sellable in-service units | same |
| Contracted occupancy | same as workstation occupancy measured on signed agreements as of the date | same | same |
| Physical utilization | people actually present (check-ins/access events) | workstation capacity | needs access data; NOT the same as occupancy |
| Financial occupancy | contracted recurring revenue of occupied priced units | list-price total of priced sellable in-service units | units without list price (both sides), comped revenue counts as 0 |

Distortions the dashboard must flag: complimentary/internal-use inventory
(occupies units, earns nothing), discounts (physical occupancy hides revenue
gaps), out-of-service units (shrink the denominator — verify they're real),
missing list prices (silently bias financial occupancy if only one side).

## Funnel family

All funnel rates are per-period; the period must be stated. Definitions:

- **Lead-to-contact**: leads with any status beyond `new` / all leads created in period.
- **Contact-to-qualified**: qualified+later / contacted+later.
- **Lead-to-tour**: distinct leads with ≥1 tour record / leads created in period.
- **Tour show rate**: completed tours / (completed + no-show). Still-scheduled tours excluded.
- **Tour-to-deal**: deals reaching proposal+later / completed tours.
- **Lead-to-deal (win) rate**: won deals / leads. Beware period misalignment:
  deals won this month usually come from prior months' leads. Cohort-based
  measurement (by lead creation month) is correct; blended same-period rates
  must be labeled as approximations.
- **Speed to lead**: business minutes from lead creation to first attempted
  human contact. Automated acknowledgments do not count. Use location-local
  business hours; report leads never contacted separately (never average as 0).
- **Sales-cycle length**: days from lead creation to deal won, median not mean.

## Retention family

- **Logo churn**: memberships canceled in period / active memberships at period
  start. Members who join and cancel within the period aren't in the
  denominator; disclose this.
- **Revenue churn (gross)**: MRR lost to cancellations + downgrades / MRR at
  period start. Expansion reported separately, never netted silently.
- **Retention** = 1 − logo churn (same period, same denominator).
- **Renewal rate**: agreements renewed / agreements reaching their renewal or
  end date in the period (not all agreements).
- **Expansion revenue**: MRR added by existing customers (upgrades, added
  units, added services) in period.

## Revenue family

- **ARPM (average revenue per active membership)**: monthly recurring
  membership revenue / active memberships. Excludes one-time revenue.
- **Revenue per sellable workstation (RevPAW)**: monthly recurring revenue /
  sellable in-service workstation capacity. State whether booking/day-pass
  revenue is included; default here: excluded.
- **Meeting-room utilization**: booked hours / bookable hours in the period.
  Bookable hours require declared opening hours; without them, report booked
  hours only.
- **Discount dependence**: share of active memberships with contracted rate
  below list rate, and MRR-weighted average discount.
- **Revenue leakage**: itemized, evidence-based only — see the
  `coworking-revenue-leakage-audit` skill. Never extrapolate.
- **CAC**: marketing + sales spend in period / new customers won in period.
  Requires spend data; without it, skills must not estimate it.
- **LTV**: ARPM × gross margin % × average customer lifetime (months). Every
  input must be sourced; if lifetime comes from churn (1/churn), say so and
  flag low-volume instability.

## Rounding and precision

Report ratios to at most one decimal percentage point. Never present a metric
computed from fewer than 10 underlying records without stating the count —
"2 of 3 tours converted (67%)" not "67% tour conversion".
