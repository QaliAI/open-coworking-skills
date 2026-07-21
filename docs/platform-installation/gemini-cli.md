# Gemini CLI

**Support: native — Gemini CLI appears on the official Agent Skills
client showcase (verified 2026-07-17); its own docs define the exact
mechanics and win over this page:**
https://geminicli.com/docs/cli/skills/

## Install

Gemini CLI loads skill metadata at session start and activates full
skill content on demand (via its skills/`activate_skill` mechanism).
Routes:

1. **Work inside a clone** of this repository — project-level discovery
   of `.agents/skills/` per Gemini CLI's current documentation.
2. **Copy** chosen skill folders from `.agents/skills/` into the
   project or user skills directory Gemini CLI's docs specify for your
   version.
3. If `gh skill install` lists a gemini agent target in your gh version,
   `gh skill install QaliAI/open-coworking-skills --all --allow-hidden-dirs --agent <target>`.

## Using the skills

Ask in operator language ("what's our occupancy?", "audit our
pipeline") — descriptions are written to trigger on those phrasings.
Mode 2 needs `python -m pip install -e .` from the repo clone.

If Gemini CLI's current documentation differs from the above, follow it
and open an issue here so this page gets corrected.
