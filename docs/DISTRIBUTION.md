# Distribution

Updated 2026-10-19. A row is "working" only after a command was run.

## Install paths

| Tool | Command | Test on 2026-10-19 | Limitation |
|---|---|---|---|
| skills CLI (`npx skills`) | `npx skills add QaliAI/open-coworking-skills --list` | Public URL, telemetry off. Cloned the public GitHub repo and found 37 skills. | |
| skills CLI | `npx skills add QaliAI/open-coworking-skills --skill coworking-pipeline-health -a codex -y --copy` | Public URL. Copied that skill into a temporary project's `.agents/skills/`. | `-a`, `-y`, and `--copy` were used so the test did not prompt or symlink. |
| skills CLI | `npx skills add QaliAI/open-coworking-skills --all` | Flag exists. Help text: `--skill '*' --agent '*' -y`. **Not executed.** | Would write into every agent detected on the machine. |
| GitHub CLI | `gh skill install QaliAI/open-coworking-skills --all --allow-hidden-dirs` | Not re-run this session. Historical note: gh 2.92 finds zero skills without `--allow-hidden-dirs`. | Hidden directory. |
| agentskill.sh | none | Creators page fetched. Listing requires connecting a GitHub account in their settings. | No webhook was added. A webhook would send push events to a third party. |
| skills.sh | none | FAQ fetched. The directory lists a repo when opted-in CLI installs report it. | This release test set `DISABLE_TELEMETRY=1`, so it did not submit the repo. Pack creation requires a Vercel login, which was not used. |

Node.js 22.20 or later is required by the skills CLI package page (version 1.7.4 when fetched). The CLI can send anonymous telemetry. Set `DISABLE_TELEMETRY=1`. The `opencoworking` package does not.

Project install is the default. `-g` is user-level.

## Directories

No directory received a submission. skills.sh indexes opted-in installs
rather than a form. agentskill.sh requires an interactive GitHub connect
before a maintainer can claim skills. No awesome-list pull request was
opened. Paid placement is out of scope.

## Package version

The Python package version is 0.1.0. There is no npm package for the skills
themselves. `npx skills` installs from the Git repository. It does not
publish this project to the npm registry.
