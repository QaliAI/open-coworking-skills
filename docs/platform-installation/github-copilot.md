# GitHub Copilot / VS Code

**Support: native (verified 2026-07-17 against the `gh skill install`
manual and the official client showcase — see SOURCES.yaml).**

## Via GitHub CLI (recommended)

Inside the repository where you want the skills (once this repo is
published):

```bash
gh skill install QaliAI/open-coworking-skills --all
```

Defaults: agent `github-copilot`, project scope, destination
`.agents/skills/` — shared with Codex, Cursor and other hosts reading
that directory, so one install serves several tools.

Useful variants:

```bash
gh skill install QaliAI/open-coworking-skills                       # interactive picker
gh skill install QaliAI/open-coworking-skills coworking-pipeline-health --pin v0.1.0
gh skill install QaliAI/open-coworking-skills --scope user          # all your projects
gh skill install /path/to/local/clone --from-local --all            # before it's published
```

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
