# Coworking and business systems research

Status date: 2026-07-17. This file records what this repository claims — and
deliberately does not claim — about external systems. Vendor API documentation
was **not** fetched during the initial build; no connector has been tested
against a live vendor API. All current support is therefore limited to export
analysis and mapping documentation, which operators can verify against their
own exports without credentials.

## Support labels (used in `catalog/compatibility.yaml` and adapters)

| Label | Meaning |
|---|---|
| `manual` | Works by pasting information; no export or API needed |
| `export-supported` | The system's standard CSV/XLSX exports are handled by the generic CSV adapter |
| `mapping-documented` | A written field-mapping guide exists in `adapters/<system>/` |
| `connector-prototype` | Read-only API connector code exists but has not been verified against a live account |
| `connector-tested` | Connector verified against a live or sandbox account |
| `official-partner-supported` | The vendor participates in maintenance |

**No system currently carries a label above `mapping-documented`.** Claiming
`connector-prototype` or higher requires fetching current vendor API docs,
recording them in `SOURCES.yaml`, and testing against a sandbox.

## Workspace-management systems (WMS)

Systems operators commonly run: OfficeRnD, Nexudus, Optix, Archie, Spacebring,
Coworks, Cobot, Yardi Kube, Satellite Deskworks, Proximity, Essensys. All of
these expose data exports (CSV and/or reports) from their admin interfaces,
which is the path this repository supports today via `adapters/generic-csv/`
plus per-system mapping guides for the first-wave systems (OfficeRnD, Nexudus,
Optix, Archie).

Known public developer-documentation entry points (recorded for future
connector work; not fetched or verified this build):

- OfficeRnD: https://developers.officernd.com/
- Nexudus: https://developers.nexudus.com/
- Optix: https://developer.optixapp.com/
- Cobot: https://dev.cobot.me/
- Spacebring, Archie, Coworks, Proximity, Satellite Deskworks, Essensys,
  Yardi Kube: start from each vendor's main site; API availability and terms
  must be confirmed per vendor before any connector work.

## CRM and sales

HubSpot, Salesforce, Pipedrive, Zoho, Apollo, Close. All support CSV export of
contacts/companies/deals from their standard UIs, which the generic CSV adapter
handles. `adapters/hubspot/` documents mapping HubSpot's standard CRM export
columns to the vendor-neutral model; operators verify against their own export
because HubSpot column sets vary with custom properties.

## Finance and payments

QuickBooks, Xero, Stripe, Square. Supported today only via exports (invoice
and payment CSVs) mapped through the generic adapter. No financial API
connector exists and none is claimed.

## Marketing, analytics, operations

Google Business Profile, Google Analytics, Google Search Console, Google Ads,
Meta Ads, LinkedIn, Mailchimp, Brevo, Listmonk, Google Workspace, Microsoft
365, Slack, Teams, Kisi, Brivo, Salto, ButterflyMX, Zapier, Make, n8n:
referenced by skills only in `manual` mode (the operator pastes what they see,
or follows a checklist against the vendor UI). The Google Business Profile
audit skill instructs checking current official Google guidance rather than
embedding rules that drift.

## Why exports-first

1. Every listed WMS/CRM can produce a CSV export without API credentials.
2. Exports keep the operator in control of exactly what data leaves the system.
3. Deterministic analysis of a file is testable with fixtures; API behavior is
   not testable without live accounts.
4. Connectors become worthwhile only after mapping is proven on real exports.

## Next research steps (for connector work)

1. Fetch and record current OfficeRnD, Nexudus, Optix, and HubSpot API docs
   (auth model, rate limits, pagination, API versioning) in SOURCES.yaml.
2. Build read-only connector prototypes behind the adapter contract in
   `adapters/README.md`, with env-var credentials and scope minimization.
3. Test against sandbox accounts before raising any support label.
