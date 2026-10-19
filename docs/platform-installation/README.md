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

The skills CLI discovers `.agents/skills/` without an extra hidden-directory flag. Tested 2026-10-19, with `DISABLE_TELEMETRY=1`, against the public repository:

- `npx skills add QaliAI/open-coworking-skills --list` cloned `https://github.com/QaliAI/open-coworking-skills.git` and found 37 skills.
- `npx skills add QaliAI/open-coworking-skills --skill coworking-pipeline-health -a codex -y --copy` copied that one skill into a temporary project's `.agents/skills/`. The extra flags avoid prompts. The command without them is the interactive form.

```bash
npx skills add QaliAI/open-coworking-skills --list
npx skills add QaliAI/open-coworking-skills --skill coworking-pipeline-health
npx skills add QaliAI/open-coworking-skills --all
```

`--all` was not executed. It installs every skill into every detected agent. The npm package can send anonymous telemetry. Set `DISABLE_TELEMETRY=1` to disable it. Node.js 22.20 or later is required. `-g` installs for the user instead of the project.

GitHub CLI remains supported. It needs the hidden-directory flag:

```bash
gh skill install QaliAI/open-coworking-skills --all --allow-hidden-dirs           # project scope, .agents/skills/
gh skill install QaliAI/open-coworking-skills coworking-pipeline-health --allow-hidden-dirs --agent claude-code --scope user
```

`--allow-hidden-dirs` is REQUIRED: gh (tested: 2.92) finds zero skills in
the hidden `.agents/skills/` directory without it. `gh skill install` was
not re-run against the public URL on 2026-10-19. A local copy still works:
`gh skill install /path/to/clone <skill-name> --from-local --allow-hidden-dirs`
(one named skill per call, or `--all`).
