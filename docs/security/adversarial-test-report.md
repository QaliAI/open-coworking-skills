# Adversarial security test report

Audit session 2026-07-18, branch `expert-audit-wave-2`. Probes were
executed (not merely designed) against the engine; every confirmed defect
was fixed the same day with a regression test in
`tests/unit/test_security_regressions.py`.

## Executed probes and results

| Probe | Result at audit start | Now |
|---|---|---|
| Embedded newline inside quoted CSV field | **VULNERABLE — silent data corruption**: `splitlines()`-based parsing destroyed the newline with no warning | Fixed (stream parsing); regression test |
| Spreadsheet formula injection through `redact` output | **VULNERABLE**: `=HYPERLINK(...)` survived executable into the redacted CSV — the file most likely to be opened in Excel by a third party | Fixed (`sanitize_cell` on write; negative numbers untouched); regression test |
| Oversized field (>128 KiB) | **DEFECT**: raw `_csv.Error` traceback | Fixed: 32 MiB limit + structured `IngestError`; regression tests (1 MB loads; 33 MB errors cleanly) |
| Invalid encoding bytes | OK — structured `IngestError`, no partial parse | regression test added |
| Broken CSV quoting | OK — parsed with structural warning | covered by probe |
| Unicode names (ö, ł, CJK) | OK roundtrip | asserted in Harbor integration tests |
| Malformed/short row | OK — padded with a counted warning, never silent | asserted in Harbor tests |
| In-place overwrite via `redact --output <input>` | OK — refused | existing unit test |
| Existing-output overwrite without `--force` | OK — refused | existing unit test |
| `..` in explicit `--output` path | Writes where the user pointed — explicit user argument, not traversal of untrusted input; documented behavior | noted |
| Instructions inside CSV cells / CRM notes / reviews | Engine emits them as inert data (correct: refusal is the agent layer's job); planted fixtures exist in both demos (REV-04, HWL-09, HC-OMEN) and skill evals test the agent-side refusal | verified |
| Windows cp1252 console output | **DEFECT (clean-consumer test)**: quick start crashed with `UnicodeEncodeError` on stock consoles | Fixed (stream reconfigure to UTF-8) + cp1252 subprocess regression test; `BrokenPipeError` handled for `head`/`Select-Object` |
| Secret leakage in connector errors | Verified by unit tests: auth failures never echo tokens/secrets | tested |
| PII in logs/error messages | Engine logs nothing; quality findings cite row numbers, not values (except caller-chosen enum columns) | reviewed |
| Unexpected network calls | Core package: zero network code paths (stdlib CSV/JSON only — verified by import review); network exists ONLY in `connectors/` behind explicit clients, GET-only (asserted by test) | reviewed + tested |
| Zip-slip / archive extraction | No archive handling exists anywhere; recorded as a design constraint in the threat model for whoever adds it | n/a |
| Symlink behavior | No symlink-following logic; file reads/writes use explicit user paths | reviewed |
| Malicious filenames | Filenames are never interpreted (entity identification ignores them by design — tested) | verified |

## Supply chain

- Runtime dependencies: **zero** (stdlib core); optional extras
  (`openpyxl`, dev tools) are floor-pinned.
- GitHub Actions: **pinned to commit SHAs** (resolved via the GitHub API
  during the audit, tag names kept as comments); Dependabot watches both
  ecosystems. CI has still never executed on GitHub (no remote) — the
  gitleaks/dependency-review legs run first on push.
- `gh skill publish .agents/skills --dry-run` (official spec validator)
  passes for all 34 skills — executed locally, gh 2.92.

## Untrusted-content stance (unchanged, re-verified)

Imported data is data, never instructions — stated in every ingesting
skill, planted in both demo datasets, and enforced by eval cases
(review REV-04, CRM note HWL-09, transcript-injection case in the
concierge audit, tour-prep note-injection case).

## Residual risks (stated, not hidden)

- Pattern-based PII redaction cannot catch free-text identifiers; human
  review remains mandatory and the tool says so on every run.
- The connectors are mock-tested only; live vendor behavior (auth
  edge cases, undocumented fields) is unverified by definition.
- Checklist-kind evals need a grader; deterministic command evals
  (29) and the executed LLM routing runs are the hard floor.
- `curl`-style SSRF is not applicable (no user-supplied URLs are
  fetched), but `officernd.fetch_token` takes a caller-supplied token
  URL — callers must source it from vendor docs; noted in its docstring.
