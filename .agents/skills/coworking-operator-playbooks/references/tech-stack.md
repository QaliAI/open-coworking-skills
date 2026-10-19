# Tech stack

Question: "Why don't our systems agree?"

## Order

1. `coworking-tech-stack-integration-audit` from a systems inventory the operator fills in.
2. `coworking-crm-wms-reconciliation` when exports exist, to show the row-level result of the gaps.
3. `coworking-data-migration-readiness` only if they are actually changing systems.
4. `coworking-system-adapter-builder` or `coworking-mcp-builder` only when they ask to build something. Writes stay behind human approval.

## Minimum files

A systems inventory. Exports are optional and change the second step from "not yet" to a reconciliation.

## Stop rules

Do not log into a vendor. Do not recommend replacing a platform because a survey named a category leader. Do not treat a blank connection as proof the product is unused. Survey statistics are context, not this operator's score.
