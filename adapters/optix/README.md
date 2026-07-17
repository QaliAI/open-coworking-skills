# Optix adapter (mapping-documented)

Status: **mapping-documented**. No API connector exists or is claimed. Optix
is mobile-first and organizes around users, plans, and bookings; admin
exports/reports supply the data. Column names vary by report and plan —
**verify against your own export**.

## Concept mappings

| Optix concept | Canonical entity | Watch for |
|---|---|---|
| Venue/location | `locations.csv` | |
| Resources (offices, desks, rooms) | `inventory.csv` | Assignable resources vs bookable resources map to units vs meeting rooms. |
| User | `contacts.csv` + `members.csv` | Optix is user-centric; the paying organization (team) may need separate handling to become `companies.csv`. |
| Plan subscription | `memberships.csv` | Plan price = `contracted_rate`; an assigned resource gives `unit_id`; plans without resources are floating memberships (blank `unit_id`). |
| Invoices / transactions | `invoices.csv`, `payments.csv` | Separate recurring plan charges from one-time booking charges before MRR math. |
| Bookings | `room-bookings.csv` | |
| Inquiries/requests | `leads.csv` | If sales runs in an external CRM, export leads from there instead and keep IDs linkable. |

## Known traps

- User-centric counting inflates membership counts when several users share
  one plan; count subscriptions, not users, for ARPM.
- Day-pass style products can appear as plans or as one-off charges depending
  on configuration; classify by billing behavior, not name.

Future connector work must start from current Optix developer docs
(https://developer.optixapp.com/) and record findings in
`docs/research/SOURCES.yaml`.
