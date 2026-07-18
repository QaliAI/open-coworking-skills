# Protect member data

Member names, contacts, contracts, invoices, payment data, access logs,
and mail information are at least confidential. Working rules for using
AI tooling on coworking data:

## The three questions before any data moves

1. **Does the analysis need the personal fields at all?** Occupancy,
   pipeline, and leakage all work on IDs and company names. Drop contact
   columns from exports when the question doesn't need them.
2. **Is the data leaving your control?** Local analysis of your own
   files: fine. Pasting into a hosted chat, sending to a consultant,
   attaching to a ticket: redact first.
3. **Would a member be surprised?** If yes, don't — or ask them.

## Redact before sharing

```bash
python -m opencoworking.cli redact contacts.csv --output contacts.redacted.csv --name-columns first_name,last_name --salt "your-private-salt"
```

- Emails, phones, card-like numbers (Luhn-validated), and listed names
  become stable pseudonyms — the same person maps to the same token, so
  joins and counts still work.
- The source file is never touched; in-place output is refused.
- **Pattern redaction is not a guarantee.** The output lists residual
  risks (names in free-text notes, identifying descriptions); review by
  hand before sharing. Free-text columns are the leak surface.
- Keep the salt private; with it, pseudonyms are consistent across
  exports; without it, outsiders can't correlate.

## Repository rules (already enforced)

No real member data in this repo — fixtures use `.example` domains and
555-01xx phones, and a test fails if that changes. Skills reference
record IDs, not personal contacts, in report outputs. Access-log
analyses aggregate; individual movement timestamps stay out of reports.

## Credentials

Nothing in Modes 1-2 needs credentials, ever. Future connectors take
credentials via environment variables only ([.env.example](../../.env.example)
lists names, never values). Anyone — or any tool — asking you to paste
an API key into a chat or a profile file is doing it wrong.

## Instructions hiding in data

CRM notes, spreadsheet cells, and review text sometimes contain text
addressed to AI assistants ("ignore previous instructions and..."). The
skills here treat all imported data as data, never as commands — and the
demo dataset ships an example (`reviews.csv`, REV-04) you can use to
test any assistant you work with.

## Not legal advice

None of this constitutes GDPR/CCPA or other compliance advice — the
tooling reduces exposure; your obligations are between you and your
counsel.
