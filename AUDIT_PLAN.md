# Audit plan — expert-audit-wave-2

Auditor role: independent principal engineer / skills evaluator / security
reviewer. All BUILD_REPORT.md claims treated as unverified until proven.

- Baseline commit: `8ef88324bd9524a64f40a60322d7f1b9dcbb5abc` (main, clean tree)
- Branch: `expert-audit-wave-2`
- Audit date: 2026-07-18
- Environment: Windows 11, PowerShell + Git Bash, Python 3.13.3, git 2.49,
  gh 2.92 (authed QaliAI). Codex CLI not installed.

## Part A — adversarial audit

- [ ] A1 Fresh venv, documented clean install, run EVERY documented check;
      independently count tests, evals, CLI commands, skills, datasets
- [ ] A2 Determinism: regenerate demo, byte-compare; spaces-in-path tests
- [ ] A3 Claim-by-claim table → EXPERT_AUDIT.md
- [ ] A4 Per-skill audit matrix (24 skills): specificity, spec compliance,
      descriptions, overlap/collision, examples vs actual demo outputs,
      eval coverage, maturity honesty. Downgrade weak skills.
- [ ] A5 Trigger/collision eval system: ≥14 prompts/skill machine-readable,
      deterministic runner; record executed vs prepared →
      docs/evals/trigger-collision-report.md
- [ ] A6 Second adversarial dataset: Harbor Works Demo (2 locations, TZ +
      currency conflict, injections, unicode, malformed rows, duplicate
      contacts, skipped stages, VO payout mismatches...) with expected
      answers computed independently of the engine; integration tests
- [ ] A7 Operator acceptance scenarios A–J across 8 personas →
      docs/evals/operator-acceptance-report.md
- [ ] A8 Host installation tests (gh CLI skill tooling, Claude Code local;
      Codex documented-only) — record exact commands/versions
- [ ] A9 Clean consumer simulation in temp dir with spaces →
      RELEASE_READINESS.md
- [ ] A10 Security adversarial tests (CSV injection, embedded newlines,
      encodings, traversal, oversized fields, secret/PII leakage, network
      calls, action pinning) → docs/security/adversarial-test-report.md;
      repair + regression tests
- [ ] A11 Provenance/licensing: URLs resolve, ledger accuracy

## Part B — Wave 2 (after defects repaired)

Candidate skills (stable only if full standard met; otherwise beta/planned
with stated gaps): crm-wms-reconciliation (top priority), daily-operator-
brief, occupancy-forecast, renewal-expansion-risk, discount-pricing-audit,
collections-prioritizer, meeting-event-yield, multi-location-benchmark,
ai-concierge-knowledge-audit, data-migration-readiness.

Plus: read-only HubSpot and OfficeRnD connector prototypes (env-var creds,
pagination, retries, mocked tests; status labeled honestly — no live
claim), README/product improvements, WAVE2_REPORT.md.

## Rules

No remote, no publish, no tags. Local commits allowed. Preserve sound
work; targeted fixes. Prepared-but-unexecuted tests are never reported as
passing.
