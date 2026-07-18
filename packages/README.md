# packages/

Generated platform-specific distributions land here (e.g. a Claude Code
plugin bundle built from the canonical skills). Nothing is hand-edited in
this directory: the canonical skill source is `.agents/skills/`, and
generated artifacts under `packages/generated/` are gitignored because
they are reproducible.

No packaging script ships yet — `scripts/build_claude_plugin.py` is on
the roadmap (see [ROADMAP.md](../ROADMAP.md), infrastructure backlog).
This placeholder exists so the packaging output location is defined and
documented rather than invented later.
