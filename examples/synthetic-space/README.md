# Northstar Coworking Demo (synthetic workspace)

A complete fictional two-location coworking operator for demos, testing,
and learning. **Every record is invented**: `.example` email domains,
reserved 555-01xx phone numbers, fictional names and companies — enforced
by an integration test. Regenerate byte-identically with:

```bash
python scripts/generate_synthetic_data.py --force
```

## The business

- **LOC-NOR — Northstar Downtown**: 5 offices, 1 suite, 8 dedicated
  desks, a 12-seat hot-desk pool, 2 meeting rooms, an event loft.
- **LOC-RIV — Northstar Riverside**: 3 offices, 4 desks, 1 meeting room
  (opened 2025).
- Products: offices, suite, desks, community memberships, virtual office
  (direct and via the fictional partner "MailNation Demo"), meeting-room
  and event bookings.

## Planted problems (find them with the skills)

The dataset intentionally contains, as of **2026-07-01**:

- 1 duplicate contact (same person, differently-cased email)
- 3 blank lead sources + inconsistent labels (four spellings of Google Ads)
- 3 leads never contacted (two arrived after hours)
- 2 completed tours with no next action; 2 no-shows
- 1 unassigned + stale + duplicated deal (D-2002/D-2012 vs D-2001)
- 1 won deal with no membership (C-GHOSTWON)
- 1 membership marked active past its end date and unbilled (M-011)
- 1 direct virtual-office client never invoiced (C-DIRECTVO)
- 1 partner-billed client with no service record (C-PARTB) and 1 possible
  double bill (C-PARTC)
- 1 comped desk (DD-08), 1 office discounted 28.6% (OF-105), 1 office
  out of service (OF-104), 2 units without list prices
- 1 failed and 1 overdue invoice; a cancellation notice on the largest
  suite (M-005); 1 canceled member with continuity signals (C-EXIT)
- 1 review containing prompt-injection text (REV-04) — for testing that
  assistants treat review text as data, never instructions

Full hand-computed expected analysis results:
[tests/fixtures/synthetic_expected.json](../../tests/fixtures/synthetic_expected.json)
(verified by `tests/integration/test_synthetic_demo.py`).

## Try it

```bash
python -m opencoworking.cli occupancy --inventory examples/synthetic-space/data/inventory.csv --memberships examples/synthetic-space/data/memberships.csv --as-of 2026-07-01
python -m opencoworking.cli leakage --as-of 2026-07-01 --leads examples/synthetic-space/data/leads.csv --deals examples/synthetic-space/data/deals.csv --tours examples/synthetic-space/data/tours.csv --memberships examples/synthetic-space/data/memberships.csv --invoices examples/synthetic-space/data/invoices.csv --inventory examples/synthetic-space/data/inventory.csv
```

Sample request/output pairs: [../sample-requests/](../sample-requests/)
and [../sample-outputs/](../sample-outputs/).
