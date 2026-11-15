# Changelog

All notable changes to this project are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
follow the policy in
[docs/skill-authoring/versioning-policy.md](docs/skill-authoring/versioning-policy.md).

## [Unreleased]

### Domain audit, engine corrections, and three new skills (2026-11-15)

#### Fixed
- Virtual-office product labels were classified as `office` because `office`
  matched as an interior substring; `meeting_suite` also collapsed into
  office. The resolver now matches exact aliases first, falls back only on
  whole tokens (longest first), and reports unmapped labels instead of
  guessing.
- The coverage figure is now labelled `metric_kind: fixed_cost_coverage` with
  an explicit `not_a_break_even` statement, and a break-even figure on
  contribution is computed when the operator supplies a
  `variable_per_workstation` cost row. The existing coverage values are
  unchanged.
- `pipeline` now accepts operator stage names (`--open-stage`), computes the
  median open-deal count and an overload flag (`--overload-median-multiple`),
  reports a stage snapshot with an explicit caveat instead of implying cohort
  conversion, and separates multi-location simultaneous requirements from
  duplicates.
- `leakage` now emits the three separate totals the skill promised
  (`billing_at_risk`, `pipeline_at_risk`, `idle_list_value`) plus the
  unweighted stale-deal value, with `--stale-days` and
  `--invoice-window-days`.
- `renewals` now reports month-to-month exposure as a count and contracted
  MRR, not an ID list.
- `schemas`: `room_booking` gains optional `status`, `booking_source`,
  `cancellation_reason`, `attended` and `cost`; new `mail_item` entity.
- Skill text: removed unsourced ranking, prevalence, seasonality and
  fill-time claims; removed the onboarding example that invented a
  matchmaking rationale; corrected the "24 skills" count.
- `coworking-churn-risk-review`: notice given is no longer scored as
  predicted churn; the windows are labelled repo defaults; the `renewals`
  command is named. Downgraded to beta.
- `coworking-mcp-builder`: the output contract now describes a design and
  scaffold, not implemented code. Downgraded to beta.

#### Added
- `coworking-member-offboarding` (experimental) - end-date arithmetic from
  the agreement, an owned task table, access reconciliation, and a
  final-invoice and deposit worksheet with amounts left to a human.
- `coworking-mail-operations` (beta) - a daily worklist ordered by lateness,
  aging per item type, and a post-termination conflict check against the
  operator's policy and the published six-month postal remail floor.
- `coworking-broker-channel-manager` (beta) - a channel register quoted from
  the operator's own agreements, an attribution reconciliation, and a
  commission ledger of expected versus invoiced versus paid.

### Audit + Wave 2 (2026-07-18, branch expert-audit-wave-2)

#### Fixed (independent adversarial audit — see EXPERT_AUDIT.md)
- CSV loader silently destroyed newlines inside quoted fields
- Redacted CSV output preserved executable spreadsheet formulas
- Fields over 128 KiB crashed with a raw csv error
- Quick start crashed with UnicodeEncodeError on cp1252 Windows consoles
- Documented `gh skill install` commands found zero skills (missing
  `--allow-hidden-dirs`); all installation docs corrected
- Six skill examples cited numbers that did not match actual outputs
- Two activation descriptions fixed (found by executed routing evals)
- Dead OfficeRnD docs URL; SOURCES.yaml YAML syntax error
- GitHub Actions pinned to commit SHAs

#### Added (Wave 2)
- Harbor Works Demo: second hand-authored adversarial synthetic business
  with independently computed expected answers
- Eight new deterministic analyses + CLI commands (18 total): reconcile,
  brief, forecast, renewals, pricing, collections, rooms, benchmark
- Ten beta skills: crm-wms-reconciliation, daily-operator-brief,
  occupancy-forecast, renewal-expansion-risk, discount-pricing-audit,
  collections-prioritizer, meeting-event-yield,
  multi-location-benchmark, ai-concierge-knowledge-audit,
  data-migration-readiness
- Read-only HubSpot and OfficeRnD connector prototypes (mock-tested
  only; env-var credentials; never live-validated)
- Trigger/collision eval suite: 476 cases, runner, two executed
  LLM-judged routing runs (476/476 on run 2)
- Security regression suite; tests grew 91 → 149

### Added
- Initial repository build: 24 production skills across foundation,
  business intelligence, sales, community/retention, marketing, virtual
  office, and integration development.
- `opencoworking` Python package (stdlib core): ingestion, normalization,
  PII redaction, occupancy/funnel/churn metrics, pipeline and leakage
  analyses, virtual-office reconciliation, CLI.
- Vendor-neutral data model: JSON Schemas, data-model/formula/terminology
  references, generic CSV adapter, mapping guides for HubSpot, OfficeRnD,
  Nexudus, Optix, Archie.
- Northstar Coworking Demo synthetic workspace with hand-computed
  expected-answer fixtures and integration tests.
- Skill catalog (24 stable + 25 planned), validators, deterministic eval
  runner, README catalog generation.
- Governance, security, contribution, and platform-installation
  documentation.

No release has been tagged yet; a `0.1.0` tag will be cut only after the
release checklist in docs/skill-authoring/versioning-policy.md passes.
