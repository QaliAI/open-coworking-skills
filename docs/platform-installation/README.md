# Platform installation

The canonical skills live in [`.agents/skills/`](../../.agents/skills/)
in the Agent Skills open format (https://agentskills.io/specification), so
one copy serves every compatible host. Support statements below were
verified against the sources recorded in
[docs/research/SOURCES.yaml](../research/SOURCES.yaml) on 2026-07-17;
host software changes — each page links the vendor's live documentation,
which wins over anything written here.

| Host | Support | Guide |
|---|---|---|
| OpenAI Codex | native (verified) | [codex.md](codex.md) |
| Claude Code | native (verified) | [claude-code.md](claude-code.md) |
| GitHub Copilot / VS Code | native (verified) | [github-copilot.md](github-copilot.md) |
| Cursor | native (official showcase) | [cursor.md](cursor.md) |
| Gemini CLI | native (official showcase) | [gemini-cli.md](gemini-cli.md) |
| OpenCode | native (official showcase) | [opencode.md](opencode.md) |
| Kiro | native (official showcase) | [kiro.md](kiro.md) |
| Windsurf | vendor-documented adapter path | [windsurf.md](windsurf.md) |
| Cline | community-documented | [cline.md](cline.md) |
| Antigravity | community-documented | [antigravity.md](antigravity.md) |
| Anything else | manual | [manual.md](manual.md) |

Fastest cross-host path where GitHub CLI ≥ the version shipping `gh skill`
is installed:

```bash
gh skill install QaliAI/open-coworking-skills --all           # project scope, .agents/skills/
gh skill install QaliAI/open-coworking-skills coworking-pipeline-health --agent claude-code --scope user
```

(Requires this repository to be published on GitHub; until then, clone
locally and use `gh skill install --from-local .` or the manual method.)
