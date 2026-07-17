# OfficeRnD adapter (mapping-documented)

Status: **mapping-documented**. No API connector exists or is claimed. This
guide covers mapping OfficeRnD data exports into the canonical model.
OfficeRnD's export column names vary by product version (Flex vs Workplace),
plan, and configured custom properties — **verify each mapping against your
own export**; the value of this guide is knowing which concepts to look for.

## What to export

From the OfficeRnD admin: members/companies lists, memberships, offices/
resources (inventory), invoices/billing, and opportunities if you use the
built-in CRM. Each is exportable as a spreadsheet from its list view.

## Concept mappings

| OfficeRnD concept | Canonical entity | Watch for |
|---|---|---|
| Location | `locations.csv` | |
| Office / Resource (desk, office, meeting room) | `inventory.csv` | Capacity ("size"/"seats") is the workstation count; meeting rooms are inventory too but excluded from membership occupancy. |
| Company + Member | `companies.csv`, `contacts.csv`, `members.csv` | A "member" in OfficeRnD is a person; the paying entity is usually the company. |
| Membership (plan assignment) | `memberships.csv` | One company can hold several memberships; the office assignment gives `unit_id`; price is the contracted rate, and the resource's listed price is `list_rate`. |
| Opportunity | `deals.csv` | Stage names are operator-configured; map explicitly. |
| Tour/visit records | `tours.csv` | Depending on setup, tours may live in opportunities' stages or in calendar data. |
| Invoice | `invoices.csv` | Status vocabulary differs; map paid/overdue/void explicitly. |
| Booking | `room-bookings.csv` | Distinguish member vs external bookings if your export carries it. |

## Known traps

- Deposits and one-time fees appear in billing exports next to recurring
  fees; separate them before computing MRR.
- "Active" membership filters may include future-dated starts; re-check
  against `start_date` on the as-of date you analyze.
- Discounts may be modeled as separate line items rather than a reduced rate.

Future connector work must start from current OfficeRnD developer docs
(https://developers.officernd.com/) and record findings in
`docs/research/SOURCES.yaml`.
