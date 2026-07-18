# Windsurf

**Support: vendor-documented adapter path.** Windsurf was not on the
official Agent Skills client showcase at verification time (2026-07-17),
but Windsurf's own Cascade documentation describes SKILL.md skills read
from `.windsurf/skills/` in the project:
https://docs.windsurf.com/windsurf/cascade/skills — that page wins over
this one.

## Install

Copy skills into the Windsurf-specific project directory (no duplicate
maintenance — copy from the canonical source on update):

```bash
# bash
mkdir -p .windsurf/skills
cp -r /path/to/open-coworking-skills/.agents/skills/* .windsurf/skills/
```

```powershell
# PowerShell
New-Item -ItemType Directory -Force .windsurf\skills
Copy-Item -Recurse \path\to\open-coworking-skills\.agents\skills\* .windsurf\skills\
```

The SKILL.md files need no modification — same format.

## Using the skills

Cascade activates skills from frontmatter relevance. Mode 2 needs
`python -m pip install -e .` from the repo clone.

Honesty note: this project has not independently tested Windsurf
activation behavior; if you find differences, please open an issue.
