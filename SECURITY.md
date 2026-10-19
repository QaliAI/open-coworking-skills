# Security policy

## Reporting a vulnerability

Report security issues privately via GitHub's "Report a vulnerability"
(Security Advisories) feature on this repository once it is public, or by
email to the maintainer address listed in the repository settings. Do not
open public issues for security problems. You should receive an initial
response within 7 days.

In scope: anything that could expose member/operator data, execute
unintended actions, leak credentials, or make skills take unauthorized
higher-risk actions (see the risk model below).

## Threat model summary

Skills are executable behavioral instructions for AI agents operating over
sensitive business and member data. Full analysis:
[docs/security/threat-model.md](docs/security/threat-model.md). Data
handling rules: [docs/security/data-handling.md](docs/security/data-handling.md).

Key protections built into this repository:

- **Prompt injection**: every skill that ingests CRM notes, spreadsheet
  cells, reviews, or messages instructs the agent that imported data is
  data, never instructions. The synthetic dataset includes an injection
  fixture (`reviews.csv` REV-04) and eval cases test the refusal.
- **Risk tiers R0-R4**: public skills are R0 (read-only) or R1 (drafts).
  No skill in this repository sends messages, modifies records, or touches
  money. Drafts are always handed to a human to send.
- **Secrets**: no credentials in the repo; `.env.example` files carry
  variable names only; the validator scans for secret patterns; scripts
  never print credentials.
- **CSV/formula injection**: `opencoworking.normalize.sanitize_cell`
  neutralizes formula-prefix cells in generated CSV output.
- **PII**: no real member data anywhere, fixtures are synthetic
  (`.example` domains, 555-01xx phones — enforced by an integration
  test); a tested redactor (`opencoworking redact`) exists for operator
  data.
- **No telemetry, no network calls**: the Python package makes zero
  network requests and uploads nothing.
- **Supply chain**: the core package has zero runtime dependencies;
  optional extras are pinned by floor; CI actions are pinned; Dependabot
  monitors updates.

## Hardening guidance for users

1. Run analyses locally on exports; you never need to give this project
   credentials to get value (Modes 1-2).
2. Redact member PII before sharing any export with anyone.
3. Treat connectors as read-only, environment-variable credentialed, and
   minimally scoped. The HubSpot and OfficeRnD clients are prototypes
   tested against mocked HTTP, not live accounts. See `adapters/README.md`.
4. Review agent-generated drafts before sending; nothing in this repo is
   designed to act on members directly.
