# Client engagements (never committed)

This directory is the local home for **paid** work: the folder a coworking
operator's exports land in, and the directory the health check writes its
deliverable into. Everything in here except this README is git-ignored on
purpose (see the `engagements/*` rule in [`.gitignore`](../.gitignore)).

Client exports contain member names, contacts, contracts, invoices, and
payment data. They are at least `confidential`, they belong to the client, and
they must not enter this repository, a pull request, an issue, a chat, or a
sample. The synthetic sample engagement that *is* committed lives in
[`examples/health-check-engagement/`](../examples/health-check-engagement/) and
contains no real data.

## Layout convention

```text
engagements/
  <client-slug>/
    client-export/            # exactly what the operator sent. Real data.
    reports/<run-name>/       # generated artifacts, one directory per run
      report.html             # DRAFT — review required
      report.final.html       # only after health-check-finalize
      engagement.json         # manifest: inputs, fingerprints, metrics, status
      REVIEW_CHECKLIST.md     # the human review gate
      finalized.json          # who released it, when
```

Keep one directory per client and per run so a later question ("what did we
tell them in March?") is answerable without re-exporting anything.

## Run one

```bash
opencoworking health-check \
  --input ./engagements/<client-slug>/client-export \
  --output ./engagements/<client-slug>/reports/2026-07 \
  --client "Client Name" \
  --as-of 2026-07-01
```

Then read `REVIEW_CHECKLIST.md`, correct anything the draft gets wrong, and
release it:

```bash
opencoworking health-check-finalize \
  --engagement ./engagements/<client-slug>/reports/2026-07 \
  --reviewer "Your Name" \
  --notes "What you checked and what you changed"
```

The tool never emails, uploads, or otherwise delivers the report. Sending it to
the client is a human step through your own agreed channel.

## Housekeeping

- Screen before you analyse: the run refuses credentials, database dumps,
  payment-card data, and government IDs found in the input folder.
- Do not commit, paste, or attach raw exports. If data has to be shared for a
  second opinion, run `opencoworking redact` first and share the redacted copy.
- Delete or archive an engagement's `client-export/` when your engagement
  agreement says so; the report directory keeps the numbers without the raw
  member rows.
- Full service documentation: [`docs/HEALTH_CHECK_SERVICE.md`](../docs/HEALTH_CHECK_SERVICE.md).
