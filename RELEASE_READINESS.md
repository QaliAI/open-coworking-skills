> Current state is [FINAL_RELEASE_AUDIT.md](FINAL_RELEASE_AUDIT.md), dated 2026-10-19. This file records the July 2026 readiness review. Do not quote its skill counts or CI statements as the present repository.

# Release readiness

Audit session 2026-07-18. This file records the CLEAN CONSUMER and HOST
INSTALLATION evidence — what was actually executed, with exact commands
and versions — plus the readiness checklist.

## Environment

Windows 11, Python 3.13.3, git 2.49.0.windows.1, gh 2.92.0, PowerShell
5.1 + Git Bash. Claude Code CLI 2.1.154 installed. Codex CLI not
installed.

## Clean consumer simulation (executed)

Simulated a brand-new user in a temp directory **containing spaces**
(`...\Temp\claude audit dir\consumer test copy`):

1. Clone-equivalent copy: `git archive HEAD | tar -x -C "<dir>"` ✅
2. Fresh venv: `python -m venv .venv` ✅
3. Install: `python -m pip install -e .` ✅ (zero runtime deps)
4. `python -m opencoworking.cli --help` ✅
5. First analysis (README quick start occupancy command):
   **failed at first attempt** — `UnicodeEncodeError` on cp1252 stdout
   (the report's ⚠ character). **Fixed** (CLI reconfigures streams to
   UTF-8) and re-executed: ✅ in Git Bash AND PowerShell 5.1
   (exit 0; earlier PowerShell 255 was `Select-Object -First` closing
   the pipe — now handled as BrokenPipeError → 0).
6. Demo generation to a spaced path: ✅ byte-identical (determinism
   verified twice + against committed files)
7. Redaction to a spaced output path: ✅ (67 redactions)

Remaining quick-start caveat (pre-publish): the README's
`git clone https://github.com/QaliAI/open-coworking-skills.git` cannot
work until the repository is published — inherent, stated in the docs'
"until published" notes.

## Host installation (executed where possible)

### GitHub CLI skill tooling — EXECUTED, gh 2.92.0

```
gh skill install "C:/Users/omino/Documents/open-coworking-skills" --from-local
  -> "no standard skills found, but 24 skill(s) exist in hidden directories"
gh skill install <repo> coworking-pipeline-health --from-local --allow-hidden-dirs
  -> installed to .agents/skills/ in a temp project (spaced path) ✅
gh skill install <repo> coworking-context-builder --from-local --allow-hidden-dirs --agent claude-code
  -> installed to .claude/skills/ ✅; SKILL.md + references/ + evals/ copied;
     frontmatter re-serialized by gh (metadata preserved, local-path added)
gh skill publish .agents/skills --dry-run
  -> spec validation PASSES for all skills (only warning: no git remote) ✅
```

Findings baked into the docs: `--allow-hidden-dirs` is REQUIRED (without
it gh finds zero skills here); one named skill per invocation (or
`--all`); `gh skill list` does not exist in 2.92. Temp installs were
removed afterward.

### Claude Code — partially executed

The trigger-routing evaluations were executed through Claude
(subagent as activation judge — see
[docs/evals/trigger-collision-report.md](docs/evals/trigger-collision-report.md)).
A headless CLI discovery test (`claude -p` in a project with installed
skills) could not run: the CLI's OAuth token was revoked in the audit
shell (401). **Status: install path documented and file-level verified;
CLI-level discovery not locally verified.**

### Codex — documented, not locally verified

CLI not installed. `.agents/skills` discovery is vendor-documented
(SOURCES.yaml, accessed 2026-07-17); no local execution claim is made.

### Other hosts (Cursor, Gemini CLI, OpenCode, Kiro, Windsurf, Cline, Antigravity)

Documented against official/community sources with per-host honesty
labels; none locally executed. See
[docs/platform-installation/README.md](docs/platform-installation/README.md).

## Readiness checklist (state at end of audit)

| Gate | Status |
|---|---|
| Fresh-venv tests (149: 110 unit + 39 integration) | ✅ pass |
| Validators (skills/catalog/references/README-table) | ✅ pass |
| Deterministic evals (29 command cases) | ✅ pass |
| Trigger suite structural + LLM-judged run 2 | ✅ 476/476 (see report for what "executed" means) |
| Both synthetic businesses end-to-end | ✅ fixture-verified |
| Clean consumer install (bash + PowerShell, spaced paths) | ✅ after cp1252 fix |
| Security probes + regressions | ✅ (see adversarial report) |
| Secret / PII / placeholder scans | ✅ clean |
| Link check | ✅ clean |
| Actions SHA-pinned; SOURCES.yaml parse-tested | ✅ |
| CI executed on GitHub | ❌ not possible pre-publish — first push must be watched |
| Live/sandbox connector validation | ❌ none (mock-tested only, labeled) |
| Live host-product routing runs (Claude Code CLI / Codex) | ❌ prepared, not executed |
| Operator validation of Wave 2 betas | ❌ pending (why they are beta) |

## Recommendation

**Publish after fixes** — specifically, after the three ❌ items above
are accepted as known-and-labeled launch conditions (they cannot be
closed pre-publish or without live accounts). Exact publish commands are
in [WAVE2_REPORT.md](WAVE2_REPORT.md); nothing has been published,
pushed, or tagged by this audit.
