# Claude Code

**Support: native (verified 2026-07-17 against the official Claude Code
skills documentation — see SOURCES.yaml).** Claude Code implements the
Agent Skills standard; skills load from `.claude/skills` (project),
`~/.claude/skills` (personal), and plugins.

## Via GitHub CLI (once this repo is on GitHub)

```bash
gh skill install QaliAI/open-coworking-skills --all --agent claude-code            # project
gh skill install QaliAI/open-coworking-skills coworking-pipeline-health --agent claude-code --scope user
```

## Manual — project scope

From your project root:

```bash
# bash
mkdir -p .claude/skills
cp -r /path/to/open-coworking-skills/.agents/skills/* .claude/skills/
```

```powershell
# PowerShell
New-Item -ItemType Directory -Force .claude\skills
Copy-Item -Recurse \path\to\open-coworking-skills\.agents\skills\* .claude\skills\
```

Working directly inside a clone of this repository also works well:
Claude Code reads the repo's `AGENTS.md`, and you can point it at any
skill by path.

## Manual — personal scope

Same copy into `~/.claude/skills/` (PowerShell: `$HOME\.claude\skills`).

## Using the skills

Claude activates skills by relevance from their descriptions, or invoke
directly: `/coworking-occupancy-revenue-dashboard`. Mode 2 needs the
Python package installed (`python -m pip install -e .` in the repo).

Note: symlinking instead of copying keeps installs in sync with
`git pull`, but symlink behavior on Windows requires developer mode —
copying is the dependable default.

Live documentation: https://code.claude.com/docs/en/skills
