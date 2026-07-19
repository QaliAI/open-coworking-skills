# GitHub Copilot / VS Code

**Support: native (verified 2026-07-17 against the `gh skill install`
manual and the official client showcase — see SOURCES.yaml).**

## Via GitHub CLI (recommended)

Inside the repository where you want the skills (once this repo is
published):

```bash
gh skill install QaliAI/open-coworking-skills --all --allow-hidden-dirs
```

Defaults: agent `github-copilot`, project scope, destination
`.agents/skills/` — shared with Codex, Cursor and other hosts reading
that directory, so one install serves several tools.

Useful variants:

```bash
gh skill install QaliAI/open-coworking-skills --allow-hidden-dirs                # interactive picker
gh skill install QaliAI/open-coworking-skills coworking-pipeline-health --allow-hidden-dirs --pin v0.1.0
gh skill install QaliAI/open-coworking-skills --all --allow-hidden-dirs --scope user
gh skill install /path/to/local/clone coworking-pipeline-health --from-local --allow-hidden-dirs   # before it's published (one skill per call)
```

`--allow-hidden-dirs` is required because this repo keeps skills in the
hidden `.agents/skills/` directory (verified against gh 2.92, which finds
zero skills here without it). Note gh installs one named skill per call;
use `--all` for everything.

## Manual

Copy skill folders into your repo's `.agents/skills/` (see
[manual.md](manual.md)).

## Using the skills

In Copilot Chat / agent mode, skills activate by relevance from their
descriptions. Mode 2 export analysis needs the Python package
(`python -m pip install -e .` from a clone of this repo).

Live documentation:
https://docs.github.com/en/copilot/concepts/agents/about-agent-skills and
https://cli.github.com/manual/gh_skill_install
