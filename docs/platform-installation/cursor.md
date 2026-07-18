# Cursor

**Support: native — Cursor appears on the official Agent Skills client
showcase (verified 2026-07-17); exact discovery paths are defined by
Cursor's own docs, which win over this page:**
https://cursor.com/docs/context/skills

## Install

Two dependable routes:

1. **Shared project directory** — `gh skill install
   QaliAI/open-coworking-skills --all` places skills in `.agents/skills/`
   at project scope, the directory multiple hosts (Copilot, Codex,
   Cursor per its docs) share. Check Cursor's skills page for its
   current supported locations and any per-agent flag
   (`gh skill install ... --agent cursor` if listed by `gh`).
2. **Manual copy** — copy chosen skill folders from this repo's
   `.agents/skills/` into the location Cursor's documentation specifies
   for your version.

## Using the skills

Skills trigger by relevance from their descriptions during agent
sessions. Mode 2 export analysis needs the Python package:
`python -m pip install -e .` from a clone of this repository.

If Cursor's current documentation differs from the above, follow Cursor's
documentation and please open an issue here so this page gets corrected.
