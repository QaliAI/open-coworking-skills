# Roadmap

The machine-readable source of truth is [`catalog/skills.yaml`](catalog/skills.yaml)
(22 planned entries with inputs, outputs, risk, evidence needed, and
planned evals). This file explains the sequencing — planned skills are
**not** in `.agents/skills/` until they meet the bar in
[GOVERNANCE.md](GOVERNANCE.md).

## Wave 2 — DELIVERED 2026-07-18 (as beta)

Ten skills shipped as beta with an 8-command engine extension and
mock-tested HubSpot/OfficeRnD connector prototypes; see
[WAVE2_REPORT.md](WAVE2_REPORT.md). **Beta → stable requires**: operator
validation on real (redacted) data, and for the connectors a sandbox
test before any label above mock-tested.

## Wave 3 (next) — highest operator value per effort

| Item | Why next | What it needs |
|---|---|---|
| Operator validation program for the 10 betas | The only path from beta to stable | 2-3 operators running skills on redacted real exports; feedback issues |
| Live-host routing runs | Trigger suite has the manifest/grade interface ready | Claude Code/Codex sessions executing the 476-case manifest |
| Connector sandbox tests | Prototypes are mock-tested only | HubSpot developer sandbox + OfficeRnD trial org; record in SOURCES.yaml |
| `coworking-proposal-builder` | Every won deal passes through a proposal; dispute-causing omissions are preventable | Terms checklist vetted against common disputes; legal-boundary evals |
| `coworking-booking-flow-audit` | Complements the SEO audit's conversion findings | Friction rubric + application cases |
| `coworking-mail-operations` | VO reconciliation exposes fulfillment risk; daily ops needs the worklist | Mail-event schema addition, SLA fixtures |
| OfficeRnD + Nexudus converter scripts (stage 2 adapters) | Mapping guides exist; converters remove the manual reshaping step | Synthetic vendor-shaped fixtures, ambiguity-refusal tests, verifying operators |

## Wave 4 — breadth

Cohort retention, event planner, feedback loop, review
response drafter, broker channel manager, shift handover, maintenance
tracker, launch planning pair, listing syndication audit (full list with
requirements: catalog).

## Wave 5 — connected mode (beyond prototypes)

HubSpot and OfficeRnD read-only prototypes exist (mock-tested, Wave 2).
This wave: sandbox validation for those two, then Nexudus/Optix/Archie
prototypes per the `coworking-mcp-builder` requirements — fresh vendor
docs recorded in SOURCES.yaml, sandbox fixtures, least-privilege scopes,
labels raised only on actual verification. Connected mode stays optional
forever — Modes 1-2 remain the fully supported path.

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
