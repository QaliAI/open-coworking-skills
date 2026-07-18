# Manual installation (any Agent Skills host)

A skill is a folder containing `SKILL.md` (YAML frontmatter + Markdown
instructions) per the open specification at
https://agentskills.io/specification. Any compliant host can use these
skills; only the discovery directory differs.

## 1. Get the skills

```bash
git clone https://github.com/QaliAI/open-coworking-skills.git
```

(Or download the source archive from the repository page.)

## 2. Copy skill folders to your host's skills directory

Each subfolder of `.agents/skills/` is one complete skill. Copy the ones
you want — keep the folder name identical to the skill name (the spec
requires it):

```bash
# bash — example: project-scope shared directory
mkdir -p .agents/skills
cp -r open-coworking-skills/.agents/skills/coworking-pipeline-health .agents/skills/
```

```powershell
# PowerShell
New-Item -ItemType Directory -Force .agents\skills
Copy-Item -Recurse open-coworking-skills\.agents\skills\coworking-pipeline-health .agents\skills\
```

Consult your host's documentation for its directory (`.agents/skills/`,
`.claude/skills/`, `.windsurf/skills/`, `~/.agents/skills/`, ...).

## 3. No-install fallback: paste the skill

Open the skill's `SKILL.md`, paste its body into your assistant's
conversation, then make your request. You lose automatic triggering;
the workflow, formulas, and guardrails all still apply.

## 4. Optional: enable Mode 2 (deterministic export analysis)

```bash
cd open-coworking-skills
python -m pip install -e .
python -m opencoworking.cli --help
```

Skills reference exact `opencoworking` CLI commands for calculations;
without the package, every skill still works in Mode 1 (guided manual).

## Updating

Re-copy after `git pull`. Pin to a tag for stability once releases
exist. Skill folders are self-contained; deleting one uninstalls it.
