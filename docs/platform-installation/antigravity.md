# Antigravity

**Support: community-documented, not vendor-verified by this project.**
Antigravity (Google's agent-first IDE) was not on the official Agent
Skills client showcase at verification time (2026-07-17). Community
installers and third-party guides document Antigravity consuming skills
from the shared project `.agents/skills/` directory. Check Antigravity's
current documentation before relying on this — and open an issue here if
you can confirm behavior either way.

## Install (per community-documented behavior)

```bash
gh skill install QaliAI/open-coworking-skills --all     # once published
# or copy the skill folders into your project's .agents/skills/ manually
```

## Fallback that always works

Paste the relevant `SKILL.md` body into the agent conversation before
your request (see [manual.md](manual.md)) — you lose auto-triggering,
nothing else.

Mode 2 export analysis needs `python -m pip install -e .` from a clone
of this repository.
