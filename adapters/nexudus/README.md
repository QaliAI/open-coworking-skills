# Nexudus adapter (mapping-documented)

Status: **mapping-documented**. No API connector exists or is claimed.
Nexudus exposes extensive CSV exports from most admin list views; column
names vary by module and configuration, so **verify against your export**.

## Concept mappings

| Nexudus concept | Canonical entity | Watch for |
|---|---|---|
| Business/Space | `locations.csv` | Multi-space accounts export per-space or combined; keep `location_id` consistent. |
| Desks / Offices / Resources | `inventory.csv` | Nexudus distinguishes desks, offices, and bookable resources; meeting rooms come from the resources module. |
| Coworker | `contacts.csv` + `members.csv` | "Coworker" is Nexudus's person record — it covers prospects AND active members; use status/contract presence to split. |
| Team | `companies.csv` | Individuals without a team are their own paying entity. |
| Contract / Coworker contract | `memberships.csv` | Contract price = `contracted_rate`; tariff/plan price = `list_rate`; the desk/office allocation gives `unit_id`. Cancellation date vs contract end date differ — map both. |
| Opportunities / enquiries (CRM module) | `leads.csv`, `deals.csv` | If the CRM module is unused, leads may only exist in a website-form mailbox — then Mode 1 (paste) is the honest path. |
| Invoices | `invoices.csv` | Nexudus invoice states are richer than the canonical enum; map explicitly and keep a note of the collapse rules. |
| Bookings | `room-bookings.csv` | |

## Known traps

- The coworker/member/team distinction is the most common mapping error:
  counting coworkers counts people, not paying memberships.
- Tariffs renamed over time keep old names on old contracts; normalize
  product names before grouping.
- Credits (booking credit bundles) are not revenue at usage time; they were
  revenue at purchase time.

Future connector work must start from current Nexudus developer docs
(https://developers.nexudus.com/) and record findings in
`docs/research/SOURCES.yaml`.
