# Agent Skills landscape, checked 2026-10-19

## Specification

<https://agentskills.io/specification>, fetched 2026-10-19. A skill is a
directory with `SKILL.md`. Required frontmatter is `name` and `description`.
Optional fields are `license`, `compatibility`, `metadata`, and
`allowed-tools`. The name matches the directory. The body should stay under
500 lines, with references loaded on demand. This repository already follows
that contract. The fetch did not change the rules recorded on 2026-07-17.

## Installer that was executed

npm package `skills`, package page fetched 2026-10-19 at version 1.7.4,
<https://www.npmjs.com/package/skills>. The page says Node.js 22.20 or later,
`npx skills add owner/repo`, project scope by default, `-g` for a user install.
Local `npx skills add --help` on Node 24.14.0 also documents:

- `--list` — list skills in the source, install nothing
- `--skill <name>` — install named skills
- `--all` — shorthand for `--skill '*' --agent '*' -y`

Against this checkout, `--list` found 37 skills under `.agents/skills/`.
Installing `coworking-occupancy-revenue-dashboard` with `-a codex -y --copy`
wrote a copy into a temporary project's `.agents/skills/`. The public URL
`QaliAI/open-coworking-skills` was not fetched. The repository was private.

The package page says the CLI collects anonymous usage data unless
`DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` is set. That telemetry belongs to
the installer, not to `opencoworking`.

`gh skill install ... --allow-hidden-dirs` remains the documented GitHub CLI
path. gh 2.92 needed the flag. The skills CLI did not, in the local test.

## Paths that were not verified

`agentskill.sh` was not fetched to a page that showed a working GitHub import.
It is not an install instruction in this repository.

`skills.sh` is the directory the CLI help points at for discovery. This
repository was not submitted. Submission after publication is recorded in
[../DISTRIBUTION.md](../DISTRIBUTION.md) only when it actually happens.

Host support statements for Codex, Claude Code, Copilot, Cursor, Gemini CLI,
OpenCode, Kiro, Windsurf, Cline, and Antigravity stay in
[../platform-installation/README.md](../platform-installation/README.md), dated
from the 2026-07-17 source pass unless a page was re-fetched. The 2026-10-19
pass re-fetched the specification and the skills CLI, not every host guide.

## What a vertical library needs, from the spec and from this repo's own evals

The specification asks for a description that says when to use the skill.
This repository's trigger file is the enforcement: 518 structural cases, of
which 476 were graded by an LLM in an earlier session. A lexical proxy is not
a host. The trigger report says so. New cases are not described as judged.

Skills that only rename a generic business method fail the operator test in
[../audits/SKILL_SCORECARD_2026.md](../audits/SKILL_SCORECARD_2026.md). The
release did not add a skill to raise the count.
