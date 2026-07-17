# HubSpot adapter (mapping-documented)

Status: **mapping-documented**. No API connector exists or is claimed. This
guide maps standard HubSpot CRM CSV exports to the canonical model. HubSpot
column headers depend on which properties you include at export time and on
custom properties in your portal — treat the mappings below as the typical
default properties and **verify against your own export** before analysis.

## What to export

In HubSpot: Contacts, Companies, and Deals via each object's export action
(all properties or a chosen set). If you track tours as meetings, also export
meeting activities or use a deal stage that marks the tour.

## Typical mappings

### Contacts → `contacts.csv`
| HubSpot property (typical label) | Canonical |
|---|---|
| Record ID | `contact_id` |
| First Name / Last Name | `first_name` / `last_name` |
| Email | `email` |
| Phone Number | `phone` |
| Associated Company ID | `company_id` |
| Create Date | `created_at` |
| Marketing contact status or legal-basis property | `consent_marketing` (map carefully; these are not identical concepts) |

### Deals → `deals.csv`
| HubSpot property | Canonical | Notes |
|---|---|---|
| Record ID | `deal_id` | |
| Deal Stage | `stage` | Map YOUR pipeline's stage names to `new/qualified/tour/proposal/negotiation/won/lost`. HubSpot stages are portal-specific; do not assume defaults. |
| Amount | `expected_value` | HubSpot amounts are usually TOTAL contract value; the canonical field is MONTHLY. Divide by term where known, otherwise record the assumption. |
| Create Date / Last Activity Date | `created_at` / `updated_at` | "Last activity" ≠ "last modified"; pick one and disclose it. |
| Deal owner | `owner` | |
| Close Date | use for `expected_move_in` only if your team uses it that way | |
| Next step | `next_action` | Often free text; date must come from tasks if tracked there. |

### Leads
HubSpot has no separate lead object in most portals; leads are contacts with
lifecycle stage `lead`/`marketing qualified` etc. Build `leads.csv` from a
contact export filtered by lifecycle stage, with `source` from
"Original Source" (and drill-down properties for detail). First response time
is NOT in a standard contact export — it requires activity data; without it,
skip speed-to-lead rather than approximating.

## Known traps

- Lifecycle stage vs lead status vs deal stage measure different things.
- "Original Source" buckets (Organic Search, Paid Search, Direct Traffic,
  Offline Sources…) are coarser than most operators' source lists; keep the
  drill-down columns when exporting.
- One company with several contacts produces several lead rows; deduplicate
  by deal, not by contact, when counting demand.

Future connector work must start from current HubSpot API docs
(https://developers.hubspot.com/docs) and record findings in
`docs/research/SOURCES.yaml`.
