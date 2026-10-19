# Launch report

Date: 2026-10-19. This file records what was verified and published. It does
not replace [FINAL_RELEASE_AUDIT.md](FINAL_RELEASE_AUDIT.md), which is the
audit written before publication.

## State found

The repository was private. `main` was unprotected. There was no release.
Pull request #5, "health-check: repeatable paid engagement", was open.
Dependabot pull requests #1–#4 were open major GitHub Action bumps.
Dependency Review failed because the dependency graph was not available,
not because the job named a vulnerable package. The product commit under
review was `3d67117` on `health-check-service`.

## Research

Recorded in [docs/research/](docs/research/) and
[docs/research/SOURCES.yaml](docs/research/SOURCES.yaml). Pages actually
fetched on 2026-10-19 include the OfficeRnD Flex Space Tech Stack Report
landing page (vendor sample: 334 operators, 68% naming integration gaps),
a Daily Office News secondary write-up of that survey, the Agent Skills
specification, the skills CLI package page, the skills.sh FAQ, and the
agentskill.sh creators page. Private GWA communities, full Reddit threads,
and live vendor sandboxes were not used as evidence.

## Material gaps

Integration depth and an operator question that does not name a skill were
the gaps that justified new work. Booking-flow, member-support triage,
mail operations, access-credential audit, proposal builder, broker channel,
and a presale playbook stayed planned. A landlord pack is an audience of
the monthly owner report, not a second skill. Beta skills still have no
outside operator. Forty-two trigger cases added for the three new skills
are structurally valid and have not been scored by an LLM judge. The
historical judge remains 476/476 on the earlier 34 skills.

## Skills

Improved in the release commit: meeting and event yield, monthly owner
report, pipeline health, source verifier, speed-to-lead, tour follow-up,
and the health-check safeguards. An unsafe override now requires
`--unsafe-reason`. Finalizing a report requires a reviewer name and
`--attest`.

Added, all beta: `coworking-unit-economics`,
`coworking-tech-stack-integration-audit`, `coworking-operator-playbooks`.

None merged, split, or deprecated.

Catalog after the release: 24 stable, 13 beta, 22 planned, 37 installable
directories. CLI commands: 23.

## Playbooks

Eight, inside `coworking-operator-playbooks`: revenue recovery, sales
conversion, 90-day occupancy, retention, virtual-office audit, monthly
owner, AI front desk readiness, and tech stack. The operator guide is
[docs/CHOOSE_A_PLAYBOOK.md](docs/CHOOSE_A_PLAYBOOK.md). There is no presale
playbook.

## Tests and evals

On `3d67117` and again on merge commit `07e7d0e`:

| Check | Result |
|---|---|
| Tests collected | 233 |
| Command evals executed | 31 |
| Checklist cases | 112, structurally valid |
| Trigger cases | 518 in the file. Structure valid. 476/476 were judged earlier. The 42 new cases were not judged. |
| Main push CI | [run 39331135859](https://github.com/QaliAI/open-coworking-skills/actions/runs/39331135859). Secret scan, validators, lint, type-check, and all four test jobs passed. Dependency Review is skipped on push. |
| Pull request CI, rerun after publication | [run 39330961289](https://github.com/QaliAI/open-coworking-skills/actions/runs/39330961289). Dependency Review succeeded, along with the other jobs. |

A clean clone of the public repository ran `opencoworking demo` and
reproduced the synthetic Northstar pins: workstation occupancy 0.5758
(38/66), office occupancy 0.7143 (5/7), financial occupancy 0.6370
(11785/18500), logo churn 0.0588 (1 of 17). The demo writes a draft and
does not finalize or send. Harbor Works is covered by the test jobs, not
by a second demo command.

## Publication actions

- Merged pull request #5. Merge commit `07e7d0e07134a3e8f11461eb3602e685c4606e79`.
- Made https://github.com/QaliAI/open-coworking-skills public.
- Enabled secret scanning, push protection, and vulnerability alerts.
- Dependency graph SBOM endpoint returned 11 packages.
- Set 16 topics: coworking, flex-space, flexible-workspace, agent-skills, ai-agents, claude-code, codex, github-copilot, cursor, workspace-management, officernd, nexudus, hubspot, proptech, coworking-operators, open-source. Vendor and host names are discovery labels. Connectors remain mock-tested.
- Enabled Discussions. The public GraphQL schema has no mutation for creating categories. Defaults remain: Announcements, General, Ideas, Polls, Q&A, Show and tell.
- Deleted remote branch `expert-audit-wave-2` after confirming it was an ancestor of `main`. Dependabot branches were left in place.
- Public install tests, telemetry disabled: `--list` found 37 skills; `--skill coworking-pipeline-health` copied into a temporary Codex project. `--all` was not run.
- Social preview is GitHub's generated card. No custom image was uploaded.
- Tagged v0.1.0 on `7f81c0f` after CI run 39332439973 passed.
- Ruleset `protect-main` (id 25436995) is active. It blocks force-push and deletion of `main` and requires Secret scan, Skills/catalog/references/evals, Lint and type-check, the four test jobs, and Dependency review. It does not require an approving review. The current admin cannot bypass it.

Release: https://github.com/QaliAI/open-coworking-skills/releases/tag/v0.1.0

## Installation

```bash
npx skills add QaliAI/open-coworking-skills --list
npx skills add QaliAI/open-coworking-skills --skill coworking-pipeline-health
npx skills add QaliAI/open-coworking-skills --all
```

Set `DISABLE_TELEMETRY=1` to opt out of skills CLI telemetry. The Python
package has none. `--all` was not executed during release testing.

```bash
gh skill install QaliAI/open-coworking-skills --all --allow-hidden-dirs
python -m pip install -e .
python -m opencoworking.cli demo
```

`gh skill install` was not re-run against the public URL in this session.

## Directories

None. skills.sh lists a repository from opted-in install telemetry, and
the release test opted out. agentskill.sh requires a signed-in GitHub
connect. No webhook was added. No awesome-list pull request was opened.
No money was spent.

## Marketing

The kit is in [marketing/](marketing/). It includes positioning, ten
LinkedIn drafts, an X thread and five follow-ups, Reddit drafts, YouTube
scripts, a Product Hunt package, a Show HN draft, industry and vendor
outreach, a 30-day calendar, the operator validation invite and form, and
a metrics plan. No screenshots or generated images were added.
[marketing/screenshots/README.md](marketing/screenshots/README.md) lists
the shots still needed.

## Posts

Nothing was published. Every social, community, Product Hunt, Hacker News,
industry, and vendor piece is a draft. Do not post the 30-day follow-up
while its brackets are empty. Do not send the operator invite until a
human chooses the recipients.

## Remaining limitations

- No outside operator has run a beta skill.
- The 42 new trigger cases have no LLM judge.
- Connectors are mock-tested only. There is no vendor endorsement.
- Dependabot pull requests #1–#4 are unmerged major version bumps.
- Discussion categories still use GitHub's default names.
- `--all`, `gh skill install` against the public URL, and a wizard were not run. The wizard stays a v0.2 idea.
- Ghost recovery, member onboarding, churn review, renewal preparation, and the MCP builder were not rewritten in this release.
- No custom social image and no GitHub Pages site.

## Next five actions

1. Rename the six discussion categories in the GitHub UI. The API cannot do it.
2. Ask one operator to run a playbook on redacted exports and keep the notes in [docs/OPERATOR_VALIDATION.md](docs/OPERATOR_VALIDATION.md).
3. Read Dependabot pull requests #1–#4 before merging any of them.
4. Capture the screenshots listed in marketing, from the synthetic demo only.
5. Connect agentskill.sh or leave a normal opted-in `npx skills` install to list the repo on skills.sh. Do not add a webhook just to force a listing.
