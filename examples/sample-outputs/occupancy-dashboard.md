# Occupancy and revenue dashboard

As of: 2026-07-01

## office_occupancy: 71.4%

- Formula: occupied sellable in-service offices / sellable in-service offices
- Numerator: 5  |  Denominator: 7
- Excludes: out-of-service units; non-sellable units

## workstation_occupancy: 57.6%

- Formula: workstation capacity of occupied sellable in-service units / total sellable in-service workstation capacity
- Numerator: 38  |  Denominator: 66
- Excludes: out-of-service units; non-sellable units

## financial_occupancy: 63.7%

- Formula: contracted recurring revenue of occupied priced units / list-price total of all priced sellable in-service units
- Numerator: 11785  |  Denominator: 18500
- Excludes: out-of-service units; non-sellable units; units without a list price (both sides)
- ⚠ 2 sellable unit(s) have no list price and are excluded from financial occupancy on both sides.

## Flags

- **out_of_service_units** (1): OF-104
  Excluded from occupancy denominators; each is capacity producing no revenue.
- **complimentary_occupancy** (1): DD-08
  Counted as occupied but contribute zero revenue; they inflate count-based occupancy relative to financial occupancy.
- **missing_list_price** (2): DD-07, HD-POOL
  Excluded from financial occupancy on both sides.
- **discount_over_25pct** (1): {'unit_id': 'OF-105', 'discount_pct': '28.6'}
  Occupied but materially below list; physical occupancy hides the revenue gap.

## Data issues

- {"type": "active_memberships_without_unit", "count": 6, "membership_ids": ["M-009", "M-010", "M-015", "M-016", "M-017", "M-020"], "note": "Not an error for floating/community memberships, but they are excluded from unit occupancy and shown separately."}
