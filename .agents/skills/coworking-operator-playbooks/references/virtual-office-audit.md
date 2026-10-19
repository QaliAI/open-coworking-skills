# Virtual office audit

Question: "Do our virtual-office and mail-client numbers match?"

## Order

1. `coworking-wms-export-analyzer` on the partner statement, the membership export, and invoices.
2. `coworking-data-dictionary` so a partner client is not mapped as a private-office membership.
3. `coworking-virtual-office-reconciliation`.
4. `coworking-cancellation-to-virtual-office` only for office members who already gave notice.

## Minimum files

Partner client list, memberships, and invoices. A direct-sold virtual-office list if it is separate from the partner list.

## Stop rules

A partner-billed client with no local invoice is not automatically unbilled. Jurisdiction, CMRA, and registered-agent questions are out of scope. Mail scanning operations are a planned skill and are not performed here. Do not give legal advice.
