# OpenAI Codex

**Support: native (verified 2026-07-17 against the official Codex skills
documentation — see SOURCES.yaml).**

Codex discovers Agent Skills from, in order: `.agents/skills` in the
current repo, `~/.agents/skills` (user), `/etc/codex/skills` (admin),
plus built-ins.

## Project scope (recommended)

Clone or vendor this repository so `.agents/skills/` sits at your
project root — Codex finds the skills automatically:

```bash
git clone https://github.com/QaliAI/open-coworking-skills.git
cd open-coworking-skills
codex
```

Or copy just the skills you want into your own repo's `.agents/skills/`.

## User scope (all projects)

```bash
# bash
mkdir -p ~/.agents/skills
cp -r open-coworking-skills/.agents/skills/* ~/.agents/skills/
```

```powershell
# PowerShell
New-Item -ItemType Directory -Force "$HOME\.agents\skills"
Copy-Item -Recurse open-coworking-skills\.agents\skills\* "$HOME\.agents\skills\"
```

## Using the skills

Codex surfaces skills by relevance; invoke explicitly with `/skills` or
by `$`-mentioning a skill (e.g. `$coworking-pipeline-health`). Codex also
offers `$skill-installer` for installing curated skills.

Mode 2 (export analysis) additionally needs the Python package:
`python -m pip install -e .` from the repo root.

Live documentation: https://developers.openai.com/codex/skills
