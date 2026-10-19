> Current state is [FINAL_RELEASE_AUDIT.md](FINAL_RELEASE_AUDIT.md), dated 2026-10-19. The "no remote" and "CI has never executed on GitHub" rows below were true on 2026-07-18. The repository now has a remote, and GitHub Actions has run.

# Expert audit — OpenCoworking Skills

Independent adversarial audit of the repository as built by the previous
agent. Baseline commit `8ef8832` (main, clean tree), audited 2026-07-18 on
branch `expert-audit-wave-2`. Every check below was run from a **fresh
virtual environment** (`.venv-audit`, Python 3.13.3, freshly-resolved
toolchain: pytest 9.1.1, mypy 2.3.0, ruff 0.15.22 — all newer than the
build-time versions) with `.pytest_cache`/`.mypy_cache`/`.ruff_cache`
deleted first. Nothing in BUILD_REPORT.md was trusted without
re-execution.

## Part 1 — BUILD_REPORT.md claims, verified claim by claim

| Claim | Evidence inspected | Result | Defect / limitation found | Corrective action | Final status |
|---|---|---|---|---|---|
| 24 production skills | `ls .agents/skills` (24 dirs), validator, `gh skill publish --dry-run` (official spec validator, gh 2.92) | **verified** | 6 skills had inaccurate examples (below); 2 had description defects found by routing evals | Examples corrected; descriptions fixed | 24 stable + 10 new beta (Wave 2) |
| 25 planned skills | `check_catalog.py` on baseline | **verified** (25 at baseline) | 2 planned entries later superseded by richer Wave 2 versions | Catalog now 22 planned after 10 promoted-to-built + 2 superseded + 9 added | consistent |
| Deterministic Python package, 10-command CLI | `--help` parse; command count | **verified** (exactly 10) | 3 engine defects found by adversarial probes (below) | Fixed + regression tests; CLI now 18 commands | fixed/extended |
| 15 synthetic CSV datasets | `ls examples/synthetic-space/data` | **verified** (15 files) | Dataset itself sound; PII patterns enforced by test re-ran clean | Second adversarial dataset added (Harbor Works, 12 files, hand-authored) | verified |
| 91 passing tests | `pytest --collect-only` + full run in fresh venv | **verified** (91 collected, 91 passed, 0.5s) | — | Now **149** tests (110 unit + 39 integration), all passing | verified |
| 15 deterministic command evals | `run_evals.py` executed | **verified** (15 executed, all pass) | — | Now 29 command evals | verified |
| 79 checklist evals "not automatically graded" | `run_evals.py` structural count | **verified** (79) | Honest label; still ungraded at baseline | Trigger suite adds 476 machine-readable routing cases, 2 LLM-judged runs EXECUTED | extended |
| Installation docs for multiple hosts | 11 platform docs + real `gh skill install` execution | **partially verified → false in one material respect** | **The documented `gh skill install ... --all` finds ZERO skills**: gh 2.92 skips hidden dirs (`.agents/`) without `--allow-hidden-dirs`; also one named skill per call, and `gh skill list` doesn't exist | All install docs corrected; behavior recorded in SOURCES.yaml; verified by executing install into a temp project (spaces in path), `--agent claude-code` variant, and dry-run publish | corrected |
| Mapping guides, no live connectors | adapters/, absence of connector code | **verified** at baseline | One dead docs URL (`developers.officernd.com` → 404) | URL corrected (`developer.officernd.com`); Wave 2 adds mock-tested prototypes, labeled exactly that | corrected/extended |
| Clean git repo, no remote, no release | `git status`, `git remote`, `git tag` | **verified** | — | still true | verified |
| "Verified against hand-computed fixtures" | Recomputed spot values; fixtures re-asserted in fresh venv; independently authored second dataset | **verified** — and the second dataset's hand-computed answers matched the engine on first run (9/10 tests; the 1 failure was fixture formatting, not arithmetic) | — | strengthened | verified |
| Secret/PII/placeholder scans clean | Re-ran scans + validator | **partially verified** | Validator's placeholder regex missed `[value]`-style tokens — and a stable skill contained them; SOURCES.yaml had a YAML syntax error (never machine-parsed) | Regex hardened; ledger fixed + parse test | fixed |
| README quick start "tested from clean setup" | Full clean-consumer simulation (archive copy → fresh venv → docs commands, bash + PowerShell, spaced paths) | **false on stock Windows** | Quick start **crashed with UnicodeEncodeError** on cp1252 consoles (the ⚠ character); prior verification ran only in a UTF-8 shell | CLI reconfigures streams to UTF-8; cp1252 subprocess regression test; BrokenPipeError handled | fixed |
| CI "internally validated" | YAML parse + every step run locally | **verified with caveat** | Actions pinned only to mutable tags | SHA-pinned all 4 actions (resolved via GitHub API); CI still never executed on GitHub (no remote) — stated, not claimed | improved |
| No unsupported claims | Example-by-example cross-check against actual demo outputs | **false in 6 skills** | speed-to-lead example: `[value]` placeholders + wrong median (25 vs actual 30); lead-to-tour example inherited the wrong 25; owner-report example miscounted "3 website leads"; leakage example summed a monthly rate with balances as "4,438/mo"; renewal example invented "12/12 invoices" and "2 bookings" (actual: 1 and 1); pii-redactor example claimed 44 redactions (actual: 67) | All six corrected to actual executed outputs | fixed |
| Engine correctness | Adversarial probes (security section) | **3 defects** | (1) quoted-newline silent corruption; (2) formula injection through redact output; (3) >128 KiB field crash | All fixed + 13 regression tests | fixed |
| Provenance ledger accurate | URL resolution (9 URLs curl-checked), license statements | **partially verified** | 1 dead URL; 1 YAML syntax error | Both fixed; ledger now parse-tested | fixed |
| Third-party attribution ("copied: none") | THIRD_PARTY_NOTICES, grep for vendor text | **verified** | — | — | verified |

## Part 2 — per-skill audit matrix (the original 24)

Columns: **Spec** (Agent Skills compliance — all 34 also pass the official
`gh skill publish --dry-run` validator), **Rout.** (LLM-judged routing,
runs 1→2), **Coworking** (real domain specificity vs generic-with-nouns),
**Example** (example accuracy vs actual outputs), **Det.** (deterministic
backing where needed), **Verdict**.

| Skill | Spec | Rout. | Coworking | Example | Det. | Verdict |
|---|---|---|---|---|---|---|
| context-builder | ✅ | ✅ | ✅ facts/assumptions discipline | ✅ | n/a (profile doc) | stable, keep |
| data-dictionary | ✅ | ✅ | ✅ monthly-vs-term, person-vs-payer traps | ✅ | inspect cmd | stable, keep |
| source-verifier | ✅ | ✅ | ✅ recompute-don't-replace rule | ✅ | occupancy recompute | stable, keep |
| pii-redactor | ✅ | ✅ | ✅ residual-risk honesty | ⚠ fixed (44→67 count) | redact cmd (+injection fix) | stable, keep |
| wms-export-analyzer | ✅ | ✅ | ✅ filename-is-not-evidence | ✅ (rows 10/15/21 verified) | inspect/quality | stable, keep |
| occupancy-revenue-dashboard | ✅ | ✅ | ✅ three-occupancy split is the core domain insight | ✅ (fixture-exact) | occupancy cmd | stable, keep |
| monthly-owner-report | ✅ | ✅ | ✅ | ⚠ fixed (website-leads miscount) | 7 underlying cmds | stable, keep |
| revenue-leakage-audit | ✅ | ✅ | ✅ three never-summed classes | ⚠ fixed ("/mo" mislabel) | leakage cmd | stable, keep |
| pipeline-health | ✅ | ✅ | ✅ row-level findings | ✅ (D-2002 verified) | pipeline cmd | stable, keep |
| speed-to-lead-auditor | ✅ | ✅ | ✅ business-minutes + 4-event taxonomy | ❌ fixed ([value] + wrong median) | speed cmd | stable after fix |
| lead-source-normalizer | ✅ | ⚠→✅ | ✅ never-guess-unmapped | ✅ (counts fixture-exact) | sources cmd | stable; description overclaim fixed |
| lead-to-tour-diagnostic | ✅ | ✅ | ✅ nine-checkpoint causal order | ⚠ fixed (inherited 25) | funnel/speed/sources | stable, keep |
| tour-preparation | ✅ | ✅ | ✅ availability-checked options, injection eval | ✅ (dates/prices verified) | n/a (brief) | stable, keep |
| tour-follow-up | ✅ | ✅ | ✅ refuses generic check-ins | ✅ | n/a (draft) | stable, keep |
| post-tour-ghost-recovery | ✅ | ✅ | ✅ value-per-touch + stop rule | ✅ | leakage selection | stable, keep |
| member-onboarding | ✅ | ✅ | ✅ owner+date+verification per task | ✅ | n/a (checklist) | stable, keep |
| churn-risk-review | ✅ | ✅ | ✅ evidence tiers, no fake scores, event-attendance trap | ✅ (M-004/M-005/M-011 verified) | n/a by design | stable, keep |
| renewal-preparation | ✅ | ⚠→✅ | ✅ three-dates discipline | ⚠ fixed (12/12 invention) | n/a (brief) | stable; notice-phrasing added |
| local-seo-audit | ✅ | ✅ | ✅ product×location matrix, no ranking promises | ✅ | n/a by design | stable, keep |
| google-business-profile-audit | ✅ | ✅ | ✅ policy-first, check-live-guidance rule | ✅ | n/a by design | stable, keep |
| virtual-office-reconciliation | ✅ | ✅ | ✅ partner-billing semantics, escalation-first | ✅ (fixture-exact) | vo-reconcile cmd | stable, keep |
| cancellation-to-virtual-office | ✅ | ✅ | ✅ reason-routing, one-offer rule, no legal claims | ✅ | n/a (offer) | stable, keep |
| mcp-builder | ✅ | ✅ | ✅ read-only-first, injection stance | ✅ (design excerpt) | n/a (dev workflow) | stable, keep |
| system-adapter-builder | ✅ | ✅ | ✅ honest label ladder | ✅ | n/a (dev workflow) | stable, keep |

**Downgrade decisions**: none of the 24 warranted downgrade — every skill
has unique operational logic, coworking-specific edge cases, and eval
coverage; the defects found were example/description accuracy issues,
all repaired. The audit's skepticism instead applied FORWARD: the ten
Wave 2 skills enter as **beta** despite meeting the mechanical stable
bar, because "stable" should also mean operator-proven (AGENTS.md
amended to make the directory rule honest). Near-duplicate risk between
renewal-expansion-risk / renewal-preparation / churn-risk-review was
examined and resolved by scope (portfolio scan → member brief → out-of-
window signals), with negative triggers enforcing the boundaries —
routing run 2 confirms zero cross-activations.

## Part 3 — what the audit added

- **Harbor Works Demo**: second, independently hand-authored adversarial
  dataset (12 files: 2 time zones, EUR/USD conflict, unicode, malformed
  row, injections, skipped stages, rescheduled tours, downsizing,
  partner-billing mess) with expected answers computed before the engine
  ran; 10 integration tests.
- **Trigger/collision suite**: 476 machine-readable cases + runner;
  two LLM-judged routing runs EXECUTED (326/336 → 476/476);
  [full report](docs/evals/trigger-collision-report.md).
- **Security regression suite** (13 tests) and the fixes it guards;
  [adversarial report](docs/security/adversarial-test-report.md).
- **Clean-consumer + host-install execution evidence**;
  [RELEASE_READINESS.md](RELEASE_READINESS.md).
- **Wave 2**: 8 engine analyses + 18-command CLI, 10 beta skills, 2
  mock-tested connectors; [WAVE2_REPORT.md](WAVE2_REPORT.md).

## Bottom line

The baseline repository was substantially real: counts honest, tests
green in a fresh environment, fixtures genuinely hand-computed, no
fabricated capabilities. The audit found and fixed: 3 engine defects
(one silent-corruption, one injection, one crash), 1 clean-consumer
crash on stock Windows, 1 materially broken documented install command,
6 inaccurate skill examples, 2 description defects, 2 provenance defects,
and unpinned CI actions. Everything found was either repaired with a
regression guard or stated plainly as a limitation.
