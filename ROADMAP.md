# Roadmap

The machine-readable source of truth is [`catalog/skills.yaml`](catalog/skills.yaml)
(25 planned entries with inputs, outputs, risk, evidence needed, and
planned evals). This file explains the sequencing and what "done" requires
— planned skills are **not** in `.agents/skills/` and won't be until they
meet the stable bar in [GOVERNANCE.md](GOVERNANCE.md).

## Wave 2 (next) — highest operator value per effort

| Item | Why next | What remains before stable |
|---|---|---|
| `coworking-meeting-room-utilization` | Rooms are the #2 revenue line with zero analysis today | Booking-hours engine + opening-hours edge fixtures, known-answer tests |
| `coworking-collections-prioritizer` | Failed payments already surfaced by leakage audit; ordering them is the obvious next step | Aging-band rules, respectful-tone review, ordering known-answers |
| `coworking-proposal-builder` | Every won deal passes through a proposal; dispute-causing omissions are preventable | Terms checklist vetted against common disputes; legal-boundary evals |
| `coworking-booking-flow-audit` | Complements the SEO audit's conversion findings | Friction rubric + application cases |
| `coworking-mail-operations` | VO reconciliation exposes fulfillment risk; daily ops needs the worklist | Mail-event schema addition, SLA fixtures |
| OfficeRnD + Nexudus converter scripts (stage 2 adapters) | Mapping guides exist; converters remove the manual reshaping step | Synthetic vendor-shaped fixtures, ambiguity-refusal tests, verifying operators |

## Wave 3 — breadth

Cohort retention, pricing review, event planner, feedback loop, review
response drafter, broker channel manager, shift handover, maintenance
tracker, launch planning pair, listing syndication audit (full list with
requirements: catalog).

## Wave 4 — connected mode

Read-only connector prototypes (HubSpot first, then OfficeRnD/Nexudus/
Optix/Archie) per the `coworking-mcp-builder` requirements: fresh vendor
docs recorded in SOURCES.yaml, sandbox fixtures, least-privilege scopes,
support labels raised only on live verification. Connected mode stays
optional forever — Modes 1-2 remain the fully supported path.

## Infrastructure backlog

- `scripts/build_claude_plugin.py` — package canonical skills as a Claude
  Code plugin (single-source, generated artifact)
- macOS CI leg once the workflow is stable and cost-appropriate
- Property-based tests for `normalize.parse_date`/`parse_money`
- Multi-language documentation once operator demand shows up

## Not planned

Anything R3+ (auto-sending member communications, payment execution,
record deletion), engagement-bait marketing automations, member
surveillance analytics, and scraping of third-party platforms. These are
out of scope by design, not by omission.
