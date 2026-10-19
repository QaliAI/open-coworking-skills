# LinkedIn 7 — health check

DRAFT.

There is one command for a folder of exports:

opencoworking health-check --input ./client-export --output ./reports/june --client "Name" --as-of 2026-07-01

It screens the folder first. Credentials, database dumps, and card numbers are refused before any analysis. It names every column it had to rename. If two files could be the same entity, it stops and asks. It does not guess.

The HTML it writes is a draft. To mark it reviewed you pass your name and a sentence that you finished the checklist. If either is missing, the tool will not print the reviewed banner. Sending the PDF is still your job. The command does not have a recipient.

An operator can run this on their own space. A consultant can use the same engine under a paid review. The engine stays open source either way. The product is the review, not a locked report.

Synthetic walkthrough: examples/health-check-engagement in the repo.
