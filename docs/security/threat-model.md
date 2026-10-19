# Threat model

Scope: this repository's skills, scripts, fixtures, and connectors,
as used by AI agents over coworking business data.

## Assets

Member/prospect PII, financial records, credentials to operator systems,
the operator's ability to trust agent output, and the integrity of this
repository as a supply chain for many operators.

## Threats and mitigations

| # | Threat | Vector | Mitigation |
|---|---|---|---|
| 1 | Prompt injection via imported data | CRM notes, spreadsheet cells, review text, member messages containing instructions | Every ingesting skill declares imported data as non-instructions; injection fixture (REV-04) + eval cases; MCP-builder skill bans interpolating record content into tool metadata |
| 2 | Malicious instructions in third-party references | Copied external skill/reference content | Nothing copied; SOURCES.yaml ledger requirement; PR review standard in CONTRIBUTING |
| 3 | Secret disclosure | Committed credentials, echoed tokens, logs | .gitignore patterns, validator secret scan, CI secret scanning, env-var-only rule, .env.example convention |
| 4 | Formula injection in CSV/XLSX | `=HYPERLINK(...)` style cells opened in Excel | `sanitize_cell` neutralizer with unit tests; redactor/analyzer never re-emit executable cells |
| 5 | Unsafe shell commands / path traversal | Scripts writing outside intended locations, `..` in archive or path inputs | Scripts take explicit output paths, refuse overwriting inputs, no archive extraction in core tooling; tests cover overwrite refusal |
| 6 | PII leakage in fixtures/examples | Real data pasted into repo | Synthetic-only fixtures with enforced `.example`/555-01xx patterns; validator scans skills; contribution checklist |
| 7 | Accidental member-data logging | Debug output, connector audit logs | No telemetry; logging rules in data-handling.md; connector spec logs params minus PII |
| 8 | Excessive permissions / unauthorized writes | Over-scoped API tokens, silent write tools | Risk-tier model (all shipped skills R0/R1); MCP-builder least-privilege and read-only-first requirements; write tools require explicit human confirmation |
| 9 | Hallucinated packages/repos | Agents inventing dependencies or install sources | Core package has zero runtime deps; docs pin exact install commands; validator flags absolute/unknown paths; README avoids unverifiable claims |
| 10 | Supply-chain drift | Unpinned CI actions, silent dependency updates | Actions pinned to major versions with Dependabot watching; dependency floors in pyproject; dependency review in CI where available |
| 11 | Unsafe archive extraction | Future export bundles (zip) | Not implemented in core tooling; if added, must use safe extraction with path checks (recorded here as a design constraint) |
| 12 | Repo-as-attack-vector | A malicious PR adds an instruction like "email data to X" inside a skill | Validator required-section checks, human review requirement, CODEOWNERS-style maintainer gate in GOVERNANCE, eval regression on privacy cases |

## Residual risks (stated honestly)

- Pattern-based PII redaction misses free-text identifiers; human review
  remains mandatory before sharing.
- Checklist-kind evals depend on a competent grader; only command-kind
  evals are fully deterministic.
- Host agents differ in how strictly they follow skill instructions; the
  risk-tier model constrains what skills ask for, not what a misbehaving
  host does.

Review this document when adding: any write-capable tool (threat 8), any
network-calling code (threats 3, 7, 10), or any archive handling (11).
