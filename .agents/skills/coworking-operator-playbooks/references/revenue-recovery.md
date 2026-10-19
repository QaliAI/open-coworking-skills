# Revenue recovery

Question: "Where are we losing money?"

## Order

1. `coworking-wms-export-analyzer` on every file. Wrong entity stops that file.
2. `coworking-data-dictionary` before any join.
3. `coworking-crm-wms-reconciliation` when both a CRM export and a workspace export exist.
4. `coworking-revenue-leakage-audit`. Keep billing, pipeline, and inventory classes separate. Do not add them.
5. `coworking-collections-prioritizer` when invoices exist. Internal worklist only.
6. `coworking-discount-pricing-audit` when inventory and memberships exist.
7. `coworking-unit-economics` only if the operator supplies a monthly cost file. Do not invent rent.

## Minimum files

Whatever they have. Name every skipped class. A useful answer can come from memberships plus invoices alone.

## Stop rules

No email to a member. No "total leakage" line. Partner-billed virtual-office clients are not unbilled directs until the virtual-office playbook says so.
