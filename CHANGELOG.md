# Changelog

All notable changes to this project are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
follow the policy in
[docs/skill-authoring/versioning-policy.md](docs/skill-authoring/versioning-policy.md).

## [Unreleased]

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
