# Changelog

All notable changes to this project are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
follow the policy in
[docs/skill-authoring/versioning-policy.md](docs/skill-authoring/versioning-policy.md).

## [Unreleased]

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
