# Build report — initial OpenCoworking Skills build

Build completed: 2026-07-18. Environment: Windows 11, git 2.49, Python
3.13.3 (package floor 3.11), gh CLI 2.92 authenticated as `QaliAI`,
Node 24 (unused). Codex CLI was not installed locally; Codex behavior is
documented from official docs, not locally executed.

## What was built

### Repository structure (all directories have working content)

```
.agents/skills/          24 production skills, each SKILL.md + evals/cases.yaml
.github/                 CI workflow, 4 issue templates + config, PR template, dependabot
adapters/                generic-csv (implemented) + hubspot/officernd/nexudus/optix/archie mapping guides
assets/                  original SVG wordmark
catalog/                 skills.yaml (24 stable + 25 planned), categories.yaml, compatibility.yaml
docs/                    getting-started (2), guides (7), integrations, platform-installation (11+index),
                         research (3), security (2), skill-authoring (4)
examples/                synthetic-space (15 CSVs + README), sample-requests, sample-outputs (CLI-generated)
packages/                documented placeholder for generated distributions
references/              data-model, formulas, terminology
schemas/                 coworking.schema.json (15 entities) + README
scripts/                 generate_synthetic_data, validate_skills, check_catalog,
                         check_references, run_evals, generate_readme_catalog
src/opencoworking/       ingest, normalize, redact, metrics, quality, analyze, render, cli
tests/                   unit (5 files), integration (1), fixtures (hand-computed expected answers)
+ governance files: AGENTS, PLANS, README, ROADMAP, CONTRIBUTING, GOVERNANCE, SECURITY,
  SUPPORT, CODE_OF_CONDUCT, CHANGELOG, CITATION.cff, LICENSE, NOTICE, THIRD_PARTY_NOTICES,
  .env.example, .gitignore, .gitattributes, pyproject.toml
```

### Production skills completed (24/24 target)

Foundation: context-builder, data-dictionary, source-verifier, pii-redactor.
BI: wms-export-analyzer, occupancy-revenue-dashboard, monthly-owner-report,
revenue-leakage-audit. Sales: pipeline-health, speed-to-lead-auditor,
lead-source-normalizer, lead-to-tour-diagnostic, tour-preparation,
tour-follow-up, post-tour-ghost-recovery. Community: member-onboarding,
churn-risk-review, renewal-preparation. Marketing: local-seo-audit,
google-business-profile-audit. Virtual office: virtual-office-reconciliation,
cancellation-to-virtual-office. Integration: mcp-builder,
system-adapter-builder.

Every skill: spec-compliant frontmatter (validated), 20-item anatomy
(validator-enforced sections), worked example, evals (triggers +
tasks; 15 command-based known-answer cases across the collection), all
R0/R1 risk.

### Planned skills cataloged

25 planned skills across all 12 categories in `catalog/skills.yaml`, each
with problem, inputs/outputs, risk, priority, evidence needed, and planned
evals; sequencing in ROADMAP.md. None occupy `.agents/skills/`.

### Scripts and adapters completed

- `opencoworking` CLI: inspect, quality, occupancy, pipeline, funnel,
  speed-to-lead, sources, leakage, vo-reconcile, redact. Stdlib-only
  core; XLSX via optional openpyxl extra; no network calls, no telemetry,
  never overwrites inputs.
- Generic CSV adapter fully implemented (it IS the canonical format).
- Mapping guides for HubSpot, OfficeRnD, Nexudus, Optix, Archie —
  honestly labeled `mapping-documented`; **no live connector exists and
  none is claimed**.

### Systems researched

Agent-skill side (fetched, recorded in SOURCES.yaml with dates): Agent
Skills spec, client showcase, Codex skills docs, Claude Code skills docs,
`gh skill install` manual, Windsurf/Cline/Antigravity status. Coworking
vendor APIs were NOT fetched this build — recorded as future work;
support labels are capped accordingly.

## Tests run and results (final verification, 2026-07-18)

| Check | Result |
|---|---|
| `python -m pytest` | 91 passed (80 unit + 11 integration) |
| `scripts/validate_skills.py` | 24 skills, 0 problems |
| `scripts/check_catalog.py` | consistent (24 stable, 25 planned) |
| `scripts/check_references.py` | 148 links, 0 broken |
| `scripts/run_evals.py` | 15 command cases pass, 79 checklist cases structurally valid |
| `scripts/generate_readme_catalog.py --check` | up to date |
| `ruff check src scripts tests` | clean |
| `mypy` (src) | clean |
| Synthetic demo regeneration | byte-identical (determinism test) |
| Secret scan (pattern grep + validator) | nothing found |
| PII scan (emails in fixtures) | all `.example`; enforced by test |
| Placeholder scan | none in stable content |
| CI/template YAML | parses |

Metric correctness is anchored by `tests/fixtures/synthetic_expected.json`
— computed BY HAND from the literal demo rows (office occupancy 5/7,
workstation 38/66, financial 11785/18500, leakage/VO/funnel finding IDs)
and asserted by integration tests, so the analysis code is checked
against an independent source of truth.

## Known limitations (honest)

1. **CI has not executed on GitHub** — no remote exists yet. The workflow
   YAML is valid and every step was run locally on Windows; the
   ubuntu leg, gitleaks action, and dependency-review run first on push.
2. **Checklist evals need a grader** — the 79 behavioral cases are
   structurally validated and written as observable expectations, but
   only the 15 command cases are fully deterministic.
3. **Vendor mapping guides are documentation-grade** — verified against
  the shape of standard exports as described, not against live accounts;
   each guide says "verify against your own export".
4. **No connector, no MCP server ships** — the two integration skills
   produce designs/workflows, deliberately.
5. **Codex/host behavior** is documented from official sources, not
   executed here (Codex CLI not installed; other hosts not run).
6. **PowerShell compatibility**: all README/guide commands are single-line
   and run identically in PowerShell and bash; the one multi-line example
   shows both continuation syntaxes.
7. **Redaction is pattern-based** — stated in the skill, the module
   docstring, and the CLI output.

## Security findings

None outstanding. Design-time constraints recorded in
`docs/security/threat-model.md` (12 threats with mitigations, 3 residual
risks stated). Repo contains no secrets, no real PII, and an intentional,
clearly-labeled injection fixture (REV-04) used by evals.

## Licensing findings

Apache-2.0 (canonical text fetched from apache.org). Nothing copied from
any third party except that license text; SOURCES.yaml records every
source studied with license notes; THIRD_PARTY_NOTICES.md states the
"copied: none" position and the obligations process. DCO adopted for
contributions.

## Files you may want to review first

1. `catalog/skills.yaml` — the planned-skill priorities are my judgment.
2. `references/formulas/README.md` — the project's metric definitions;
   if you manage to different definitions, they are configurable but the
   defaults should match your instincts.
3. `.agents/skills/coworking-monthly-owner-report/SKILL.md` — the section
   order is opinionated.
4. `catalog/compatibility.yaml` — host-support wording (native vs
   community) is deliberately conservative.
5. `CITATION.cff` + install commands — all use `QaliAI` (the
   authenticated gh user) as owner; if you'll publish under a different
   org, search-replace `QaliAI/open-coworking-skills`.

## Recommended next development wave

See ROADMAP.md Wave 2: meeting-room utilization, collections prioritizer,
proposal builder, booking-flow audit, mail operations, and the
OfficeRnD/Nexudus converter scripts — plus finding one verifying operator
per vendor guide to harden the mappings.

## Exact commands

Run the demo:

```
python -m pip install -e ".[dev]"
python -m pytest
python -m opencoworking.cli occupancy --inventory examples/synthetic-space/data/inventory.csv --memberships examples/synthetic-space/data/memberships.csv --as-of 2026-07-01
python -m opencoworking.cli leakage --as-of 2026-07-01 --leads examples/synthetic-space/data/leads.csv --deals examples/synthetic-space/data/deals.csv --tours examples/synthetic-space/data/tours.csv --memberships examples/synthetic-space/data/memberships.csv --invoices examples/synthetic-space/data/invoices.csv --inventory examples/synthetic-space/data/inventory.csv
```

Install the skills locally (host-specific detail in
`docs/platform-installation/`):

```
# Claude Code, project scope (PowerShell):
New-Item -ItemType Directory -Force .claude\skills
Copy-Item -Recurse <this-repo>\.agents\skills\* .claude\skills\
# Codex: work inside this repo (reads .agents/skills natively), or copy to $HOME/.agents/skills
# After publishing: gh skill install QaliAI/open-coworking-skills --all
```

Publish later (NOT executed — requires your explicit authorization):

```
gh repo create QaliAI/open-coworking-skills --public --source . --push   # creates remote + pushes main
# then: enable Discussions, branch protection requiring the CI checks,
# verify the Actions run is green, and only after that consider tagging
# v0.1.0 per docs/skill-authoring/versioning-policy.md
```

## Commit history of this build

scaffold (governance/licensing/research) → tooling (package + unit tests)
→ domain (schemas/references/adapters/demo + known-answer tests) → skills
(24 + evals) → catalog + validators → docs/CI/README → this report.
