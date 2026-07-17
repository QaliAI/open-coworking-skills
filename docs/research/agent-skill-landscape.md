# Agent skill landscape research

Access date for all primary sources: **2026-07-17**. Full ledger: [SOURCES.yaml](SOURCES.yaml).

## The standard

The [Agent Skills specification](https://agentskills.io/specification) defines a
skill as a directory containing a `SKILL.md` (YAML frontmatter + Markdown body)
with optional `scripts/`, `references/`, and `assets/` folders.

Verified frontmatter contract:

| Field | Required | Constraint |
|---|---|---|
| `name` | yes | ≤64 chars; lowercase `a-z0-9-`; no leading/trailing/consecutive hyphens; must match folder name |
| `description` | yes | ≤1024 chars; what the skill does **and** when to use it |
| `license` | no | short license name or bundled file reference |
| `compatibility` | no | ≤500 chars; only when there are real environment requirements |
| `metadata` | no | arbitrary string map; use namespaced keys |
| `allowed-tools` | no | experimental; support varies by host |

Progressive disclosure tiers: metadata (~100 tokens, always loaded) →
`SKILL.md` body (<5000 tokens recommended, loaded on activation) → resources
(loaded on demand). Keep `SKILL.md` under 500 lines; keep file references one
level deep from `SKILL.md`.

## Host support (verified 2026-07-17)

From the official [client showcase](https://agentskills.io/clients.md):

- **Claude Code** — native; `.claude/skills` (project), `~/.claude/skills`
  (personal), plugins; `/skill-name` invocation. Extends the standard with
  invocation control, subagent execution, dynamic context injection.
- **OpenAI Codex** — native; reads `.agents/skills` (repo), `~/.agents/skills`
  (user), `/etc/codex/skills` (admin); `$skill-creator`, `$skill-installer`.
- **GitHub Copilot / VS Code** — native; installable via `gh skill install`
  which writes to `.agents/skills/` at project scope.
- **Cursor, Gemini CLI, OpenCode, Kiro, Goose, Roo Code, Amp, Factory, Junie,
  OpenHands, Letta, Tabnine, TRAE, Snowflake Cortex Code, Databricks Genie
  Code** and ~25 more — listed with per-host setup docs.

Not on the official showcase as of the access date: **Windsurf** (documents
`.windsurf/skills/` in its own Cascade docs), **Cline** and **Antigravity**
(community tooling and third-party guides document them consuming the shared
`.agents/skills` project directory). Installation docs in
`docs/platform-installation/` label these honestly.

## Installation via GitHub CLI

`gh skill install OWNER/REPO [skill[@version]]` — verified from the
[manual](https://cli.github.com/manual/gh_skill_install):

- Default: project scope, writes into `.agents/skills/` of the current repo
- `--agent claude-code|github-copilot|...`, `--scope user`, `--pin <ref>`,
  `--all`, `--from-local`, `--force`
- Discovery: any `.../SKILL.md` path in the source repo, so this repository's
  `.agents/skills/*/SKILL.md` layout is discoverable.

## Patterns adopted (independently implemented)

From studying the spec's authoring guides and the general shape of strong
public skill repos (Anthropic skills, Superpowers — concepts only, nothing
copied):

1. **Trigger-rich descriptions** — state the job and the operator phrases that
   should activate it; avoid overlap between skills.
2. **Progressive disclosure** — short SKILL.md workflow; formulas, field maps,
   and edge-case detail in skill `references/`; deterministic work in scripts.
3. **Eval folders per skill** — positive/negative/ambiguous trigger prompts
   plus task cases with expected observable outcomes.
4. **One job per skill** — diagnostics separated from drafting, drafting
   separated from sending (which this repo does not do at all — R3+ actions
   always require explicit human confirmation).
5. **Deterministic scripts over model arithmetic** — anything with a right
   answer (metrics, reconciliation, normalization) runs in tested Python, and
   the model interprets results.

## Decisions

- Canonical directory: **`.agents/skills/`** — the only location natively read
  by Codex from a repo checkout and the default target of `gh skill install`.
  Claude Code project use is documented via symlink/copy or plugin packaging in
  `docs/platform-installation/claude-code.md`.
- Frontmatter uses only spec fields; project data lives under namespaced
  `metadata` keys (`opencoworking.*`), so spec-compliant hosts that ignore
  unknown metadata still work.
- No duplicate per-platform skill trees. `scripts/build_claude_plugin.py` is a
  future packaging step recorded in ROADMAP, not a second source of truth.
