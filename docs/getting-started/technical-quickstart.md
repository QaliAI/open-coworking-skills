# Technical quickstart

For developers, analysts, and technically-inclined operators.

## Install

Requires Python 3.11+ and git. Works on Windows, macOS, Linux.

```bash
git clone https://github.com/QaliAI/open-coworking-skills.git
cd open-coworking-skills
python -m pip install -e ".[dev]"
```

(PowerShell: identical commands. XLSX support: `python -m pip install -e ".[xlsx,dev]"`.)

## Verify everything works

```bash
python -m pytest                          # unit + integration tests
python scripts/validate_skills.py         # 24 skills pass
python scripts/run_evals.py               # deterministic eval cases pass
```

## Run the synthetic demo

```bash
python -m opencoworking.cli occupancy `
  --inventory examples/synthetic-space/data/inventory.csv `
  --memberships examples/synthetic-space/data/memberships.csv `
  --as-of 2026-07-01
```

(Backtick continuation is PowerShell; use `\` in bash, or one line in
either.) You should see office occupancy 71.4% (5/7), workstation 57.6%
(38/66), financial 63.7% — with the formulas and flags printed. Every
number is verified against hand-computed fixtures in
`tests/fixtures/synthetic_expected.json`.

More commands:

```bash
python -m opencoworking.cli --help
python -m opencoworking.cli inspect examples/synthetic-space/data/leads.csv
python -m opencoworking.cli leakage --as-of 2026-07-01 --deals examples/synthetic-space/data/deals.csv --tours examples/synthetic-space/data/tours.csv
python -m opencoworking.cli redact examples/synthetic-space/data/contacts.csv --output contacts.redacted.csv --name-columns first_name,last_name
```

Every command: reads inputs, never modifies them, writes only to stdout
or an explicit `--output`, makes zero network calls, `--format json` for
machine-readable output.

## Use with your own data

1. Export CSVs from your WMS/CRM.
2. `opencoworking inspect` to identify and sanity-check them.
3. Map columns to the canonical headers
   ([adapters/generic-csv](../../adapters/generic-csv/README.md);
   vendor guides in [adapters/](../../adapters/README.md); the
   `coworking-data-dictionary` skill automates the conversation).
4. `opencoworking quality` before trusting any analysis.
5. Run the analyses.

## Install the skills into your agent

The canonical skills live in `.agents/skills/` — the directory Codex
reads natively from a repo checkout and `gh skill install` targets.
Per-host instructions: [docs/platform-installation/](../platform-installation/).

## Repository layout

See [AGENTS.md](../../AGENTS.md) for the map and the engineering rules;
[docs/skill-authoring/](../skill-authoring/quality-standard.md) to write
skills; [CONTRIBUTING.md](../../CONTRIBUTING.md) to submit them.
