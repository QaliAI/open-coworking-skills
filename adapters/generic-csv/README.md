# Generic CSV adapter (implemented)

The generic CSV format IS the canonical model: files whose headers match the
property names in [`schemas/coworking.schema.json`](../../schemas/coworking.schema.json).
Anything the `opencoworking` CLI or the analytical skills consume is in this
format. Mapping any system into OpenCoworking means producing these files.

## Files and headers

| File | Required columns | Full column set |
|---|---|---|
| `locations.csv` | `location_id, name` | see schema `$defs/location` |
| `inventory.csv` | `unit_id, location_id, unit_type, capacity` | `$defs/inventory_unit` |
| `contacts.csv` | `contact_id` | `$defs/contact` |
| `companies.csv` | `company_id, name` | `$defs/company` |
| `leads.csv` | `lead_id, created_at` | `$defs/lead` |
| `deals.csv` | `deal_id, stage` | `$defs/deal` |
| `tours.csv` | `tour_id, status` | `$defs/tour` |
| `memberships.csv` | `membership_id, company_id, product, start_date, status` | `$defs/membership` |
| `members.csv` | `member_id` | `$defs/member` |
| `invoices.csv` | `invoice_id, amount, status` | `$defs/invoice` |
| `payments.csv` | `payment_id, amount, status` | `$defs/payment` |
| `room-bookings.csv` | `booking_id, room_unit_id, start_at, end_at` | `$defs/room_booking` |
| `events.csv` | `event_id, date` | `$defs/event` |
| `reviews.csv` | `review_id, platform, rating` | `$defs/review` |
| `virtual-office-partners.csv` | `partner_id, partner_name, billing_model, client_company_id` | `$defs/virtual_office_partner` |

Conventions:

- UTF-8 (BOM tolerated), comma-separated; semicolon/tab auto-detected
- Dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM` in the **location's** zone
- Money: plain decimal, monthly amounts unless the column says otherwise
- Booleans: `true`/`false` (`yes`/`no`/`1`/`0` tolerated)
- Blank means unknown — never invent a default when converting

## Converting a vendor export

1. Export from your system (see the per-vendor guides in `adapters/`).
2. Run `opencoworking inspect your-export.csv` to see what the file looks like.
3. Use the `coworking-data-dictionary` skill to build a column mapping.
4. Rename/reshape columns to the canonical headers (spreadsheet or script).
5. Run `opencoworking quality` on the result before any analysis.

A worked example lives in `examples/synthetic-space/` — 15 canonical files for
the fictional Northstar Coworking Demo, including deliberate data problems.
