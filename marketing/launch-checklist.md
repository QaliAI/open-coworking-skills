# Launch checklist

Human steps. Do not check a box from memory.

## Before the repository is public

- [x] Tests, skill validators, evals, reference check, and secret scan pass on the release commit. Recorded in CI run 39330214075. Re-check the tip if another commit lands.
- [x] Dependency Review fails with "not supported on this repository" until the dependency graph is enabled. That log did not name a vulnerable package.
- [ ] Dependabot pull requests #1, #2, #3, and #4 stay open. They are major GitHub Action bumps. Do not merge them to make the board look clean.
- [ ] README counts match `catalog/skills.yaml` (24 stable, 13 beta, 22 planned).
- [ ] `npx skills add <local checkout> --list` finds 37 skills. Retest the public URL after publication.
- [ ] No real member file in the tree or in git history. Fixtures are Northstar and Harbor Works.
- [ ] No claim that a connector was live-tested.

## Publication

- [ ] Merge pull request #5 into `main`.
- [ ] Make QaliAI/open-coworking-skills public.
- [ ] Enable the dependency graph. Rerun Dependency Review and record whether the settings error clears.
- [ ] Add a ruleset on `main`: no force-push, no deletion, require the test, lint, validator, and secret-scan checks. Dependency Review can be required only after it can succeed.
- [ ] Enable Discussions with: Operator Questions, Help / Installation, New Skill Ideas, Integrations, Show & Tell, Operator Feedback. Issues stay for bugs, features, and data-model changes.
- [ ] Topics: coworking, flexible-workspace, flex-space, agent-skills, ai-agents, workspace-management, proptech, coworking-operators, open-source. Add claude-code, codex, github-copilot, cursor, officernd, nexudus, hubspot only as discovery labels, with the README still saying connectors are mock-tested.
- [ ] Delete `expert-audit-wave-2` after confirming it is an ancestor of `main`. Leave Dependabot branches until those PRs are closed or merged on purpose.
- [ ] Tag v0.1.0 on the public `main` commit. Release notes separate stable, beta, playbooks, CLI, connectors, limitations, install, privacy, and what is next.
- [ ] Clone the public URL into an empty directory and run `npx skills add QaliAI/open-coworking-skills --list`.

## After the tag

- [ ] Capture the screenshots listed in [screenshots/README.md](screenshots/README.md).
- [ ] Send nothing to a third-party community until a human has read that community's rules.
- [ ] Do not buy a listing, a boost, or a newswire.
