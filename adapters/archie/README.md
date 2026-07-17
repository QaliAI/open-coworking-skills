# Archie adapter (mapping-documented)

Status: **mapping-documented**. No API connector exists or is claimed. Archie
covers coworking and flex-office management with members, plans, invoicing,
and bookings; admin exports supply the data. Column names vary by version and
configuration — **verify against your own export**.

## Concept mappings

| Archie concept | Canonical entity | Watch for |
|---|---|---|
| Location | `locations.csv` | |
| Spaces/desks/rooms | `inventory.csv` | Confirm which records are sellable membership inventory vs bookable rooms. |
| Members / companies | `contacts.csv`, `members.csv`, `companies.csv` | Distinguish the person from the paying entity. |
| Memberships/plans | `memberships.csv` | Assigned space gives `unit_id`; plan price vs charged price map to `list_rate` vs `contracted_rate`. |
| Invoices/payments | `invoices.csv`, `payments.csv` | Map status vocabulary explicitly. |
| Bookings | `room-bookings.csv` | |
| Leads (if CRM features used) | `leads.csv` | Otherwise export from the external CRM in use. |

## Known traps

- As with all WMS exports: separate one-time charges from recurring before
  revenue metrics; confirm whether "active" filters include future starts;
  confirm date-format locale before parsing slash dates.

Future connector work must start from current Archie documentation
(https://archieapp.co/) and record findings in `docs/research/SOURCES.yaml`.
