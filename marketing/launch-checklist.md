# Launch checklist

Human steps. Do not check a box from memory.

## Before the repository is public

- [x] Tests, skill validators, evals, reference check, and secret scan pass on the release commit. Main push run 39331135859. Dependency Review succeeded on the rerun of run 39330961289 after the repository was public.
- [x] Dependabot pull requests #1, #2, #3, and #4 stay open. They are major GitHub Action bumps. Do not merge them to make the board look clean.
- [x] README counts match the catalog: 24 stable, 13 beta, 22 planned, 37 installable skills.
- [x] `npx skills add QaliAI/open-coworking-skills --list` found 37 skills on the public URL.
- [x] Fixtures used for the demo and tests are the synthetic Northstar and Harbor Works sets. No live connector test is claimed.

## Publication

- [x] Pull request #5 merged to `main` as `07e7d0e` on 2026-10-19.
- [x] QaliAI/open-coworking-skills is public.
- [x] Dependency graph answers the SBOM API. Vulnerability alerts, secret scanning, and push protection are enabled.
- [x] Ruleset `protect-main` (id 25436995) is active on `main`. It blocks force-push and deletion and requires secret scan, skill validators, lint, the four test jobs, and Dependency Review. There is no required approving review, so a one-maintainer repository is not locked to a second account. Direct pushes can still be rejected until those checks exist on the commit.
- [x] Discussions are enabled. The public API no longer exposes a mutation to create categories, so the six GitHub defaults remain: Announcements, General, Ideas, Polls, Q&A, Show and tell. Rename them in the GitHub UI if you want Operator Questions, Help / Installation, New Skill Ideas, Integrations, Show & Tell, and Operator Feedback. Issues stay for bugs, features, and data-model changes.
- [x] Topics set: coworking, flex-space, flexible-workspace, agent-skills, ai-agents, claude-code, codex, github-copilot, cursor, workspace-management, officernd, nexudus, hubspot, proptech, coworking-operators, open-source. Host and vendor names are discovery labels. The README still says the connectors are mock-tested.
- [x] Deleted `expert-audit-wave-2` after confirming it was an ancestor of `main`. Dependabot branches stay.
- [x] Tagged v0.1.0 on `7f81c0f` after CI run 39332439973 passed. https://github.com/QaliAI/open-coworking-skills/releases/tag/v0.1.0
- [x] Cloned the public URL and ran `opencoworking demo`. Workstation occupancy 0.5758, office 0.7143, financial 0.6370, logo churn 0.0588 on 1 of 17. Draft only.

## After the tag

- [ ] Capture the screenshots listed in [screenshots/README.md](screenshots/README.md).
- [ ] Send nothing to a third-party community until a human has read that community's rules.
- [ ] Do not buy a listing, a boost, or a newswire.
