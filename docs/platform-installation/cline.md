# Cline

**Support: community-documented, not vendor-verified by this project.**
Cline was not on the official Agent Skills client showcase at
verification time (2026-07-17). Community tooling and third-party guides
document Cline consuming skills from the shared project
`.agents/skills/` directory. Check Cline's current documentation before
relying on this — and if you confirm behavior either way, please open an
issue so this page can be upgraded or corrected.

## Install (per community-documented behavior)

Place skills in your project's `.agents/skills/`:

```bash
gh skill install QaliAI/open-coworking-skills --all --allow-hidden-dirs     # once published
# or copy manually — see manual.md
```

## Fallback that always works

Cline follows project instruction files and pasted instructions: open
the relevant `SKILL.md` (e.g.
[coworking-pipeline-health](../../.agents/skills/coworking-pipeline-health/SKILL.md))
and paste its body into the conversation before your request. A skill is
just precise instructions; pasting loses auto-triggering but nothing
else.

Mode 2 export analysis needs `python -m pip install -e .` from a clone
of this repository.
