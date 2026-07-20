# Operator acceptance report

Audit session 2026-07-18, branch `expert-audit-wave-2`.

## Method — what "executed" means here

Three evidence layers, kept distinct:

1. **Executed deterministically**: the scenario's CLI command(s) were run
   against both synthetic businesses and outputs verified against
   hand-computed fixtures (`tests/fixtures/*.json`, `tests/integration/`).
2. **Executed as routing**: the scenario's operator phrasing was routed by
   the LLM activation judge (trigger run 2, 476/476 —
   [trigger-collision-report.md](trigger-collision-report.md)).
3. **Assessed by auditor review**: conversation-level qualities (asked for
   missing info, avoided unnecessary questions, proportionate output)
   were evaluated against the skills' written workflows and eval
   checklists — NOT against live agent conversations. This is the honest
   limit of this report; live persona sessions remain open work.

## Personas covered

Owner (single- and multi-location), community manager, sales manager,
marketing manager, finance/bookkeeping, consultant, technical integrator —
each scenario below names its persona.

## Scenarios

### A. "Why are we not reaching occupancy goals?" (single-location owner)

Routing → occupancy-dashboard (+ forecast for the forward view): ✅ (run 2).
Executed: `occupancy` on both businesses — office/workstation/financial
with formulas and flags verified to fixtures (Northstar 5/7, 38/66,
11785/18500; Harbor 3/5, 35/57, 11400/18530); `forecast` verified
(39/39/29/29). Facts vs hypothesis separation: enforced by output design
(formula contracts; flags carry "why"). Prioritized actions: dashboard's
decision summary names units and monthly values. Proportionate: single-
screen output. **Verdict: pass** (layers 1+2 executed; layer 3 assessed).

### B. "Which prospects need action today?" (sales manager)

Routing → daily-operator-brief (collision case allowed pipeline-health;
judge chose brief): ✅. Executed: `brief --role sales` on both businesses —
Harbor correctly surfaces the stale "scheduled" tour HWT-05 and ghosted
HWT-02; Northstar surfaces D-2007's overdue promise. Missing-info conduct:
skipped classes are listed (verified by eval case). **Verdict: pass.**

### C. "Why do CRM totals not match active memberships?" (technical integrator / owner)

Routing → crm-wms-reconciliation: ✅ (run 2 direct + indirect). Executed:
`reconcile` on Harbor — HC-PORTAL (won, no membership), 9 pre-CRM
memberships correctly framed as history, both planted value conflicts
(HC-ANCHOR 1600v3300, HC-EMBER 300v600), unknown-unit PDX-D9, duplicate
person HCT-01/12 in review queue; never merges (unit-tested).
**Verdict: pass.**

### D. "Which upcoming renewals are at risk?" (community manager / owner)

Routing → renewal-expansion-risk: ✅. Executed: `renewals` on Northstar —
five agreements ordered by cliff (M-004 with payment friction + 28.6%
jump; M-005 notice-given; M-001 multi-membership), M2M held aside,
no-score rule printed. **Verdict: pass.**

### E. "Are discounts masking weak financial occupancy?" (owner)

Routing → discount-pricing-audit (collision with dashboard resolved
correctly): ✅. Executed: `pricing` on both — Northstar office cut
270.00/ws with 14.3% weighted discount, OF-105 as the single dominant
driver; Harbor PDX-S1 28.1%. Refusals verified in eval cases (no market
claims, no price coordination). **Verdict: pass.**

### F. "Which failed payments deserve attention first?" (finance user)

Routing → collections-prioritizer: ✅ (a run-1 miss that Wave 2 fixed).
Executed: `collections` on Northstar — INV-1004 before INV-1006 (same
age, larger balance), renewal-before-pricing context flag on Delta,
sends-nothing rule printed. **Verdict: pass.**

### G. "Are meeting and event spaces producing enough revenue?" (GM)

Routing → meeting-event-yield: ✅. Executed: `rooms` on Northstar —
MR-2 65.00/booked-hour, EV-1 225.00 (n=1 labeled), member-amenity rooms
labeled as retention value not failure; utilization honestly omitted
until `--open-hours-per-day` given (then 0.0500 verified).
**Verdict: pass.**

### H. "Prepare the monthly owner report." (owner; consultant persona for methodology)

Routing → monthly-owner-report: ✅. Executed: all seven underlying
commands the skill orchestrates ran against both businesses with
fixture-verified outputs; the assembled 12-section narrative itself is a
Mode-1 agent deliverable — **assessed by auditor review** against the
skill's section contract and eval checklist, not executed end-to-end as
a live conversation. **Verdict: pass with the layer-3 caveat.**

### I. "Audit this Google Business Profile and local landing-page data." (marketing manager)

Routing → gbp-audit + local-seo-audit (complementary pair; ambiguous
cases accept both): ✅. No deterministic layer exists for these skills by
design (policy-sensitive, Mode 1). **Assessed by auditor review**:
workflows demand current-official-guidance checks and policy-safe-only
tactics; injection resistance (REV-04-style review) and
review-gating/VO-eligibility refusals covered by eval cases.
**Verdict: pass at layer 3; no layer-1 claim exists or is made.**

### J. "Reconcile virtual-office partner clients and payouts." (owner / bookkeeper)

Routing → virtual-office-reconciliation: ✅. Executed: `vo-reconcile` on
both businesses — Northstar C-PARTB/C-PARTC/C-DIRECTVO triple verified to
fixtures; Harbor HC-SIREN (partner client with no service record —
escalation-first) and HC-MISTRAL double-billing candidate verified.
**Verdict: pass.**

## Cross-scenario findings

- **Formulas visible**: every deterministic output carries numerator/
  denominator/exclusions — verified in generated outputs, not just docs.
- **Limitations visible**: skipped checks, blind spots, and honest
  omissions (utilization without declared hours) appear in the outputs
  themselves.
- **Action orientation**: dashboard/leakage/brief/collections outputs end
  in record-level actions; verified in sample outputs.
- **Understandable to role**: assessed (layer 3) — outputs use operator
  vocabulary; the consultant/integrator personas additionally get
  methodology blocks.
- **Open gap (recorded, not hidden)**: no scenario was executed as a live
  multi-turn conversation with a persona through a production host. The
  eval suite's checklist cases define exactly what such runs must check.
