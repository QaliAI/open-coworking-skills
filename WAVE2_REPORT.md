# Wave 2 report

Branch `expert-audit-wave-2`, 2026-07-18. Companion documents:
[EXPERT_AUDIT.md](EXPERT_AUDIT.md) (Part A findings),
[RELEASE_READINESS.md](RELEASE_READINESS.md) (consumer/host evidence),
[docs/evals/trigger-collision-report.md](docs/evals/trigger-collision-report.md),
[docs/evals/operator-acceptance-report.md](docs/evals/operator-acceptance-report.md),
[docs/security/adversarial-test-report.md](docs/security/adversarial-test-report.md).

## What was preserved

The baseline architecture survived the adversarial audit intact and was
deliberately NOT rewritten: the 24 stable skills (all kept stable — no
downgrades were warranted; see the audit's skill matrix), the canonical
schema, the stdlib-first package design, the hand-computed-fixture
discipline, the catalog/validator system, and all governance documents.

## What was corrected (audit repairs, each with a regression guard)

1. `load_csv` silently destroyed newlines inside quoted fields → stream
   parsing + tests.
2. Redacted CSV output preserved executable spreadsheet formulas →
   `sanitize_cell` on write + tests.
3. Fields >128 KiB crashed with a raw `_csv.Error` → 32 MiB limit +
   structured error + tests.
4. Quick start crashed with `UnicodeEncodeError` on stock Windows
   consoles (found by CLEAN consumer testing, missed by the original
   "verification") → UTF-8 stream reconfigure + cp1252 subprocess test;
   BrokenPipeError handled.
5. Every `gh skill install` command in the docs was unusable —
   gh 2.92 finds zero skills in hidden `.agents/` without
   `--allow-hidden-dirs` (found by EXECUTING the install) → all docs
   corrected; behavior recorded in the ledger.
6. Six skills' "realistic examples" cited numbers that did not match
   actual demo outputs (incl. literal `[value]` placeholders and a
   figure summing a monthly rate with balances) → corrected to executed
   outputs; validator regex hardened.
7. Two activation-description defects found by executed routing evals
   (lead-source-normalizer overclaim; renewal-preparation missing
   notice-given phrasing) → fixed and re-verified in run 2.
8. Dead OfficeRnD docs URL; SOURCES.yaml YAML syntax error (never
   machine-parsed before) → fixed + ledger parse test.
9. GitHub Actions pinned to commit SHAs (resolved via the GitHub API).
10. Leakage unbilled check now annotates non-monthly billing
    frequencies (annual-prepaid false-positive class).

## What was downgraded

No existing skill was downgraded — the audit looked for grounds
(genericness, overlap, unbacked claims) and found repairable accuracy
defects instead. The skepticism was applied forward: all ten Wave 2
skills enter as **beta**, not stable, despite meeting the mechanical
stable bar — "stable" here also means operator-proven, and they are not
yet. AGENTS.md's directory rule was amended to make beta-in-directory
honest.

## What was added

- **Harbor Works Demo** — second, hand-authored adversarial synthetic
  business (12 CSVs; two time zones; a EUR-formatted rate inside a USD
  dataset; unicode names incl. 田中健; a malformed row; prompt injection
  in a CRM field; formula injection in a company name; skipped stages;
  rescheduled and outcome-less tours; downsizing; expired-but-active
  membership; VO partner conflicts) with expected answers computed by
  hand BEFORE the engine ran; the engine matched on first run.
- **Wave 2 engine** (`src/opencoworking/wave2.py`) + 8 CLI commands
  (total now 18): `reconcile`, `brief`, `forecast`, `renewals`,
  `pricing`, `collections`, `rooms`, `benchmark` — all known-answer
  tested on BOTH businesses.
- **Ten beta skills**: crm-wms-reconciliation, daily-operator-brief,
  occupancy-forecast, renewal-expansion-risk, discount-pricing-audit,
  collections-prioritizer, meeting-event-yield,
  multi-location-benchmark, ai-concierge-knowledge-audit,
  data-migration-readiness — full anatomy, evals (incl. 14 new command
  cases), catalog entries.
- **Trigger/collision system**: 476 machine-readable cases, runner with
  deterministic proxy + manifest/grade interface, and TWO EXECUTED
  LLM-judged routing runs (raw results preserved under docs/evals/).
- **Connector prototypes** (HubSpot, OfficeRnD): read-only, env-var
  credentials never logged or shown in errors, retry/backoff with
  Retry-After, cursor pagination, explicit properties, canonical-row
  output, 14 mocked tests. API docs fetched 2026-07-18 and recorded.
- **Security regression suite**, trigger suite, ledger parse test,
  script-contract tests: 149 tests total (from 91).
- README product sections (starting points, mode diagram, honesty
  tables, what-this-cannot-do, troubleshooting from real failures).

## Tests run and exact results (final gates, fresh `.venv-audit`)

| Gate | Result |
|---|---|
| `pytest` (unit + integration, both businesses) | **149 passed** (110 unit + 39 integration) |
| `validate_skills.py` | 34 skills, 0 problems |
| `check_catalog.py` | 24 stable + 10 beta + 22 planned, consistent |
| `check_references.py` | 0 broken links |
| `generate_readme_catalog.py --check` | up to date |
| `run_evals.py` | **29 command cases executed, all pass**; 105 checklist cases structurally valid |
| `run_trigger_evals.py` | 476 cases valid; proxy executed; **LLM-judged run 2: 476/476** (472/476 before 4 annotated eval-spec corrections) |
| `ruff` / `mypy` (newer versions than build-time) | clean |
| `gh skill publish .agents/skills --dry-run` | spec validation passes (gh 2.92) |
| Secret / PII / placeholder scans | clean |
| Both businesses end-to-end | fixture-verified |
| Clean consumer install (bash + PowerShell + spaced paths) | pass (after cp1252 fix) |
| CI workflows executed locally step-by-step | pass; **never executed on GitHub** (no remote) |

## Remaining limitations (plainly)

1. **Connectors are mocked only.** `connector-prototype (mock-tested)`
   everywhere; the OfficeRnD token endpoint is deliberately a parameter
   because it was not verifiable from fetched pages. No live claim
   exists anywhere.
2. **Host products were not driven end-to-end.** gh CLI install/publish
   paths were executed; Claude Code CLI headless discovery was blocked
   by a revoked OAuth token; Codex is not installed. The LLM-judged
   routing runs used a Claude subagent as the activation judge — strong
   evidence, not a host-product guarantee.
3. **Checklist evals (105) still need a grader**; the deterministic
   floor is the 29 command cases + 476-case routing suite.
4. **Wave 2 betas lack operator validation** — that is exactly why they
   are beta.
5. **Scenario H/I conversation-level quality** was assessed by auditor
   review, not live persona sessions (stated in the acceptance report).

## Installation paths actually tested

`gh skill install --from-local` (project scope, spaced path;
`--agent claude-code` variant; hidden-dir behavior; per-skill limit) and
`gh skill publish --dry-run` — executed with gh 2.92.0 and cleaned up.
Everything else: documented with per-host honesty labels, not executed.

## Skill maturity census

- **Stable (24)**: the original collection, post-repair.
- **Beta (10)**: Wave 2 (engine-backed except the two judgment skills,
  which are checklist-eval'd).
- **Experimental (0)**.
- **Planned (22)**: catalog + ROADMAP.

## Recommended publication decision

**Publish after fixes** — where "fixes" are launch conditions, not code:
(a) accept and watch the first GitHub Actions run (it has never
executed remotely); (b) keep connector labels at mock-tested until a
sandbox test happens; (c) treat Wave 2 as beta in announcements. The
code, tests, docs, and honesty labels are otherwise release-ready per
[RELEASE_READINESS.md](RELEASE_READINESS.md).

## Exact next commands (NOT executed — publication requires explicit authorization)

```bash
# 1. merge the audit branch locally
git checkout main && git merge --no-ff expert-audit-wave-2

# 2. create the remote and push (THE publication step - human decision)
gh repo create QaliAI/open-coworking-skills --public --source . --push

# 3. watch the first CI run; fix anything the ubuntu leg surfaces
gh run watch

# 4. only after green CI and a review pass, consider tagging per
#    docs/skill-authoring/versioning-policy.md (checklist must pass)
```
