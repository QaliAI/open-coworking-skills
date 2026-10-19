# Distribution

Updated 2026-10-19. A row is "working" only after a command was run.

## Install paths

| Tool | Command | Test on 2026-10-19 | Limitation |
|---|---|---|---|
| skills CLI (`npx skills`) | `npx skills add QaliAI/open-coworking-skills --list` | Local checkout path only. Found 37 skills. | Public GitHub form needs a public repository. Retest after publication and record the result in `LAUNCH_REPORT.md`. |
| skills CLI | `npx skills add <source> --skill coworking-occupancy-revenue-dashboard -a codex -y --copy` | Installed one skill into a temporary project's `.agents/skills/`. | `--copy` was used so the temp project did not symlink back into this repo. |
| skills CLI | `npx skills add <source> --all` | Flag exists. Help text: `--skill '*' --agent '*' -y`. **Not executed.** | Would write into every agent detected on the machine. |
| GitHub CLI | `gh skill install QaliAI/open-coworking-skills --all --allow-hidden-dirs` | Not re-run this session. Historical note: gh 2.92 finds zero skills without `--allow-hidden-dirs`. | Hidden directory. |
| agentskill.sh | none | Not verified. | Do not document an import button that was not used. |
| skills.sh | none | Not submitted. | Submit only after the repository is public, and only if the directory's own flow accepts a GitHub repo without a paid placement. |

Node.js 22.20 or later is required by the skills CLI package page (version 1.7.4 when fetched). The CLI can send anonymous telemetry. Set `DISABLE_TELEMETRY=1`. The `opencoworking` package does not.

Project install is the default. `-g` is user-level.

## Directories

No directory received a submission in the session that wrote this file.
Low-quality directories and "awesome list" pull requests are out of scope
unless the list's rules are read and the entry is factual. Paid placement
is out of scope.

## Package version

The Python package version is 0.1.0. There is no npm package for the skills
themselves. `npx skills` installs from the Git repository. It does not
publish this project to the npm registry.
