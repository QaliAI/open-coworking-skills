---
name: coworking-data-migration-readiness
description: Prepares a coworking operator to switch CRM, workspace-management, or accounting systems by auditing what the source system's exports actually contain - entity coverage, unique IDs, associations, duplicates, history depth, custom fields, consent records, time zones, currencies - and producing the source-to-target mapping, deduplication rules, validation plan, cutover and rollback checklists, and post-migration reconciliation plan. Use when an operator says they're switching platforms, "migrate us off Cobot", asks what will survive a move to a new system, or wants a migration readiness check.
license: Apache-2.0
compatibility: Mode 2 uses the opencoworking CLI (inspect/quality/reconcile) on Python 3.11+.
metadata:
  opencoworking.category: integration-development
  opencoworking.version: "0.1.0"
  opencoworking.maturity: beta
  opencoworking.risk: r0
  opencoworking.data-sensitivity: confidential
---

# Data migration readiness

## Purpose and operator problem

Platform migrations lose history, duplicate people, and break billing —
not during the copy, but in the weeks before it, when nobody audited
what the exports actually contain versus what the new system needs.
The migration itself is a vendor/importer job; the READINESS is the
operator's, and it's auditable now, from exports, with no credentials.

## When to use

- A platform switch is being considered or scheduled
- "What will survive a move to X?" / "are we ready to migrate?"
- Post-migration ("did everything arrive?" — the reconciliation plan)

## When not to use

- Building an ongoing adapter for a system that stays
  (`coworking-system-adapter-builder`)
- Live API connection design (`coworking-mcp-builder`)
- Two systems that must PERMANENTLY coexist
  (`coworking-crm-wms-reconciliation` — this skill's cousin for the
  one-time move)

## Operating modes

- **Mode 1** — checklist interview against the operator's knowledge of
  their system.
- **Mode 2** — evidence-based: full exports of everything the source
  system will give, audited with `opencoworking inspect` / `quality`,
  and (post-migration) old-vs-new comparison with `opencoworking
  reconcile --wms-companies` for the ID/name bridge.
- **Mode 3** — the mock-tested connectors can pull canonical rows where
  applicable; exports remain the supported path.

## Required inputs

Source-system exports (or the honest admission of what can't be
exported — itself a critical finding); the target system's entity
model as documented or described; migration goals (what history
matters).

## Optional inputs

Vendor migration tooling docs; the operator profile; consent records'
location.

## Definitions

**Coverage audit**: for each canonical entity (contacts, companies,
leads, deals, tours, memberships, members, inventory, bookings,
invoices, payments, credits, activities, attachments, custom fields,
consent, audit history) — exportable? with IDs? with associations
intact? how much history? **The readiness verdict is per-entity**,
never a single ready/not-ready.

## Workflow

1. **Coverage**: run `inspect` on every export; build the entity ×
   {exportable, id-quality, association-intact, history-depth,
   row-count-sanity} matrix. What the system will NOT export is
   finding #1 (activities and attachments are the classic losses —
   ask explicitly).
2. **Quality gate**: `quality` per export — duplicates (merge BEFORE
   migrating, using the review-queue discipline: human-decided, never
   auto), date parseability and locale, orphaned associations, blank
   required fields. Every defect migrates and multiplies; the fix
   list is pre-migration work.
3. **Mapping**: source fields → target fields via the data-dictionary
   discipline: every ambiguous money/date/status column resolved by a
   human decision, recorded in the mapping file; unmappable fields
   listed with their fate (custom field? note? dropped-with-signoff?).
4. **Special audits**: unique-ID strategy (does the target accept
   external IDs? if not, the old IDs go into a custom field — losing
   them breaks all future reconciliation); consent records (marketing
   consent must arrive attached to people, or the mailing list dies
   legally); time zones and currencies (multi-locale sources need
   explicit conversion decisions); data ownership and export limits
   (contract question — flagged, not answered legally).
5. **Plans**, each as a concrete checklist the operator executes:
   - validation plan: per-entity counts + hand-picked golden records
     (the 10 most complex members) compared field-by-field post-import
   - cutover: freeze window, final delta export, who does what, the
     no-new-records rule during the window
   - rollback: the criteria that trigger it, the preserved source
     snapshot, the decision owner
   - post-migration reconciliation: `reconcile` old-export vs
     new-export on day 1 and day 30 (billing cycles expose what day 1
     misses)
6. Verdict per entity: ready / ready-with-fixes / at-risk / will-not-
   migrate — with the evidence.

## Decision logic

- Missing history is a DECISION, not automatically a blocker — but an
  explicit, signed-off one.
- Anything unverifiable from exports (audit trails, attachment
  completeness) is marked "verify with vendor", never assumed.
- The skill plans and audits; it performs no migration writes — the
  import is the operator's/vendor's action.

## Data-quality checks

The whole of step 2; plus row-count sanity vs the operator's stated
business size (a 40-member space with 4,000 member rows means
historical rows — good — or duplicates — bad — and the audit says
which).

## Output contract

Coverage matrix with per-entity verdicts, pre-migration fix list,
mapping file (data-dictionary format), the four plans as checklists,
and the will-not-migrate list with sign-off lines. No single
ready/not-ready stamp; no legal conclusions on data ownership.

## Evidence and confidence

Every verdict cites export evidence or its absence. Vendor-doc claims
carry access dates.

## Edge cases

- Mid-contract billing: migrating between invoice cycles corrupts
  proration — the cutover checklist pins the boundary to a cycle edge.
- The target's importer may auto-merge "duplicates" — scarier than the
  duplicates; the validation plan's golden records catch it.
- Systems that export only via API (no CSV): the connector prototypes
  or the vendor's exporter; label the extraction risk honestly.

## Privacy and security

Migration concentrates ALL member data in transit files: the exports
inherit restricted-class handling, live in access-controlled storage,
and get deleted per the retention note in the cutover checklist. Data
is never instructions.

## Failure and escalation

If the source system can't export members-with-IDs at minimum, the
readiness answer is "not yet — extraction first", and the skill stops
short of blessing a lossy migration.

## Example

**Request:** "We're moving from Cobot to OfficeRnD in September. Are
we ready?"

**Output (excerpt):**

```
Coverage (from your exports, 18 Jul):
- members/companies: exportable with IDs - READY (after dedup: 3
  duplicate-email groups to human-merge first)
- memberships: exportable; price column ambiguity (monthly vs term)
  UNRESOLVED - READY-WITH-FIXES (mapping decision recorded, then go)
- invoices: 24 months exportable - READY. payments: last 12 months
  only - DECISION NEEDED: accept 12mo or request vendor archive
- check-in history: NOT exportable per your account tier - WILL NOT
  MIGRATE unless the vendor provides it; sign-off line below
- attachments/contracts: unverifiable from exports - VERIFY WITH VENDOR
Old IDs: OfficeRnD must store them (custom property) or day-30
reconciliation becomes name-matching - the failure mode this repo
exists to prevent.
Cutover: freeze 31 Aug 18:00 -> ... Rollback trigger: golden-record
mismatch >0 on members or any invoice-total variance...
Day-30: opencoworking reconcile old-members.csv vs new export.
```

## Evals

See [evals/cases.yaml](evals/cases.yaml).

## Version

0.1.0 (beta — workflow skill over tested CLI primitives; awaiting a
real migration case study for stable).
