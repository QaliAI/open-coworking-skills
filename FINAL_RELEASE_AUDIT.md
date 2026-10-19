# Final release audit

Date: 2026-10-19. Auditor: the release session working in this checkout.
Repository: [QaliAI/open-coworking-skills](https://github.com/QaliAI/open-coworking-skills).
Branch inspected: `health-check-service` (open pull request #5), compared with `main`.

This file replaces July 2026 status sentences in older reports. Those reports
keep their original dates. A banner on each one points here.

## What was independently verified

`gh repo view` on 2026-10-19: visibility **PRIVATE**, default branch `main`,
discussions **off**, topics empty, no homepage. `main` is not protected
(GitHub returns 403 on branch protection until the repository is public or
the account has GitHub Pro). No tags and no GitHub release.

Open pull requests:

| PR | Title | Disposition |
|---|---|---|
| #5 | health-check: repeatable paid engagement | Open, head `health-check-service`. This release absorbs it. |
| #4 | bump actions/setup-python 5.6.0 → 7.0.0 | Leave open. Major action bump. CI on that PR failed on 2026-07-21. |
| #3 | bump actions/dependency-review-action 4.9.0 → 5.0.0 | Leave open. Major action bump. |
| #2 | bump gitleaks/gitleaks-action 2.3.9 → 3.0.0 | Leave open. Major action bump. |
| #1 | bump actions/checkout 4.3.1 → 7.0.1 | Leave open. Major action bump. CI also warns that Node 20 actions are deprecated. That is not a reason to jump major versions unread. |

`origin/expert-audit-wave-2` is an ancestor of `origin/main` (`git merge-base --is-ancestor` exited 0). It is safe to delete after this release is on `main`. No other stale feature branch was found.

GitHub Actions on the last recorded PR #5 run: Ubuntu and Windows, Python 3.11 and 3.12, lint, skill validators, and the secret scan passed. Dependency Review failed because the dependency graph and GitHub Advanced Security are not enabled on this private repository. The job log did not name a vulnerable package. That is a settings failure.

## Counts in this working tree

Counted on 2026-10-19 from the files, not from older reports.

| Item | Count | How it was counted |
|---|---|---|
| Stable skills | 24 | `catalog/skills.yaml` status field, and frontmatter |
| Beta skills | 13 | same (the original 10, plus unit economics, tech-stack audit, operator playbooks) |
| Planned skills | 22 | catalog only; no directory |
| Installable skill directories | 37 | `.agents/skills/*/SKILL.md` |
| CLI commands | 23 | `add_parser` calls in `src/opencoworking/cli.py` |
| Collected tests | 233 | `pytest --collect-only` via a collection hook |
| Command evals executed | 31 | `python scripts/run_evals.py` |
| Checklist evals, structure only | 112 | same run |
| Trigger cases | 518 | `python scripts/run_trigger_evals.py` (37 × 14) |
| LLM-judged trigger cases | 476 | historical run, 34 skills. The 42 new cases are not judged. |
| Playbooks | 8 | `catalog/playbooks.yaml` |

The 23 commands are: `inspect`, `quality`, `occupancy`, `pipeline`, `funnel`, `speed-to-lead`, `sources`, `leakage`, `vo-reconcile`, `reconcile`, `brief`, `forecast`, `renewals`, `pricing`, `collections`, `rooms`, `economics`, `stack-audit`, `benchmark`, `health-check`, `health-check-finalize`, `demo`, `redact`.

Do not publish 149 tests, 226 tests, 18 commands, 24+10 skills, or `0.1.0-dev`. The package version in `pyproject.toml` and `src/opencoworking/__init__.py` is `0.1.0`. Older README text said `0.1.0-dev`. That sentence is corrected in the README.

## Connectors and adapters

| Surface | Maturity |
|---|---|
| `adapters/generic-csv` | Implemented. The CLI reads canonical CSV. |
| `src/opencoworking/connectors/hubspot.py` | Read-only prototype. Tests use a mock transport. Not live-tested and not sandbox-tested. |
| `src/opencoworking/connectors/officernd.py` | Same. |
| `adapters/nexudus`, `optix`, `archie` | Mapping notes only. |
| `adapters/hubspot`, `adapters/officernd` | Mapping notes plus the prototypes above. |

There is no top-level `connectors/` directory. The code lives under `src/opencoworking/connectors/`. `adapters/README.md` no longer calls the next connector "future" as if none existed. Any further connector is still read-only by contract.

## Documentation that was wrong

These statements were in the tree and are corrected or bannered:

- "no remote" and "CI has not run on GitHub" in `BUILD_REPORT.md`, `EXPERT_AUDIT.md`, `WAVE2_REPORT.md`, `RELEASE_READINESS.md`, `README.md`, and `docs/security/adversarial-test-report.md`.
- README "149 tests", "18-command", "24 stable + 10 beta", and `0.1.0-dev`.
- README heading "Sell a coworking health check". It now says "Run a complete coworking health check". Consultant use is secondary in `docs/HEALTH_CHECK_SERVICE.md`.
- Source-verifier example used occupancy 76% (38/50) and 92%. The Northstar known answers are office 0.7143 (5/7), workstation 0.5758 (38/66), and financial 0.6370 (11785/18500). Logo churn in the health-check window is 0.0588 (1 of 17), not 5.6% of 18.
- Monthly owner report sections asked for churn, renewals, collections, and rooms without naming the commands. The workflow now names `forecast`, `renewals`, `collections`, and `rooms`, and it drops a section when the file is absent.
- Unsourced sentences in speed-to-lead ("answers first usually hosts the first tour") and tour follow-up ("closes materially better") were removed.
- `adapters/README.md` said "a future connector" as if the prototypes did not exist.

`python scripts/check_references.py` reported 242 relative links and no broken ones after these edits. Re-run it after any new link.

## Skill quality

The reading scorecard is `docs/audits/SKILL_SCORECARD_2026.md`. No skill was merged, split, deprecated, or promoted. Beta stays beta until an operator runs it on real redacted data.

Three additions met the bar for a beta skill:

- `coworking-unit-economics` — coverage from supplied costs only. Missing rent or payroll is unknown, not zero. No published "70% break-even" figure is encoded.
- `coworking-tech-stack-integration-audit` — a map of systems the operator lists. Justified by the OfficeRnD 2026 landing page (see the research docs). Vendor sample, not a census.
- `coworking-operator-playbooks` — eight operator questions that call existing skills. Not a new metric engine. No presale playbook.

Not built, and not promoted from planned: booking-flow audit, member-support triage, mail operations, access-credential audit, proposal builder, broker channel manager. Reasons are in `docs/research/2026-gap-analysis.md`. A landlord pack is an audience of the monthly owner report, not a second skill.

## Health check safeguards

`health-check --allow-unsafe` now requires `--unsafe-reason`. The reason is stored on the engagement. A boolean alone is not enough.

`health-check-finalize` requires `--attest`. `report.final.html` is refused when the reviewer or the attestation is blank. The green banner says it records an attestation. It does not prove the checklist was followed.

The Northstar sample was regenerated with the pinned timestamps already in the integration test. `bundle.json` and `preflight.json` stay uncommitted. The sample README documents `--attest`.

`opencoworking demo` runs that synthetic health check as a draft. It does not finalize and it does not send anything.

## Installation

`npx skills` (npm package `skills` 1.7.4 on the package page that day; local CLI help confirmed the flags) supports:

```bash
npx skills add QaliAI/open-coworking-skills --list
npx skills add QaliAI/open-coworking-skills --skill coworking-pipeline-health
npx skills add QaliAI/open-coworking-skills --all
```

Tested against the local checkout, not against GitHub, because the repository was private: `--list` found 37 skills; one skill copied into a temporary project's `.agents/skills/` for the Codex agent. `--all` was not executed. The help text defines it as `--skill '*' --agent '*' -y`, which would write into every detected agent. The public URL must be retested after publication.

`gh skill install` still needs `--allow-hidden-dirs` (verified historically on gh 2.92). The skills CLI did not need that flag in the local test.

The skills CLI can send anonymous telemetry. `DISABLE_TELEMETRY=1` disables it. This repository's Python code does not.

`agentskill.sh` import was not verified. It is not documented as a working install path.

## Security, privacy, license

- Skills remain R0 or R1. No skill sends email, charges a card, or writes to a vendor.
- Fixtures are the Northstar and Harbor Works synthetic operators. The health-check sample test rejects real-looking contact data.
- `docs/research/SOURCES.yaml` records outside sources. Usage is `studied` except the Apache-2.0 text, which is `copied` as the license requires.
- No live HubSpot, OfficeRnD, Stripe, or Supabase call was made in this audit. Connector tests stay on mocks.
- A full secret scan of git history is a release gate and is recorded in `LAUNCH_REPORT.md` when it is run. Do not treat this paragraph as that scan.

## Launch blockers that were still open when this audit was written

1. The working tree was not yet committed, and pull request #5 was not merged.
2. The repository was private, so the public `npx skills add QaliAI/...` URL was untested.
3. Dependency Review cannot pass until the dependency graph is enabled, which for this account requires the repository to be public or Advanced Security to be enabled.
4. Branch protection cannot be set while the repository is private on a free plan.
5. Discussions were off.
6. The 42 new trigger cases have no LLM judge run.
7. No outside operator has run a beta skill. Beta must not be relabeled stable.
8. Dependabot majors #1–#4 stay open on purpose.

`LAUNCH_REPORT.md` is the document that says which of these were closed.
