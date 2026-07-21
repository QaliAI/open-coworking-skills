# Adapters

Adapters map external systems into the vendor-neutral model in `schemas/` so
skills never depend on any one platform. Current support levels use the labels
defined in [`docs/research/coworking-systems.md`](../docs/research/coworking-systems.md).

| Adapter | Status | What exists |
|---|---|---|
| [generic-csv](generic-csv/README.md) | **implemented** | Canonical CSV format consumed directly by `opencoworking` CLI; fully tested |
| [hubspot](hubspot/README.md) | connector-prototype (mock-tested) | Mapping guide + read-only API prototype (`src/opencoworking/connectors/hubspot.py`), mocked tests only |
| [officernd](officernd/README.md) | connector-prototype (mock-tested) | Mapping guide + read-only API prototype (`src/opencoworking/connectors/officernd.py`), mocked tests only |
| [nexudus](nexudus/README.md) | mapping-documented | Field-mapping guide for Nexudus exports |
| [optix](optix/README.md) | mapping-documented | Field-mapping guide for Optix exports |
| [archie](archie/README.md) | mapping-documented | Field-mapping guide for Archie exports |

HubSpot and OfficeRnD now carry `connector-prototype (mock-tested)`: read-only
client code exists, exercised only against mocked transports with synthetic
fixtures - **no live or sandbox validation has been performed**, and offline
Modes 1-2 never require them. Vendor export column names vary by plan, version,
custom fields, and locale — the guides tell you what to look for and how to
verify, not exact strings to trust blindly.

## Adapter contract

A future connector (API or MCP server) must expose read-only accessors that
emit rows in the canonical schema for: contacts, companies, leads, deals,
tours, memberships, members, inventory, bookings, invoices, payments,
check-ins, events. Requirements:

- Read-only by default; any write capability is separate, opt-in, and gated
  by explicit human approval (risk R2+)
- Credentials via environment variables only; never printed, never logged
- Minimal scopes; documented permissions; documented API version
- Pagination and rate-limit handling with backoff
- Deterministic output ordering for testability
- Test fixtures recorded from a sandbox account, PII-scrubbed

See the `coworking-system-adapter-builder` skill for the authoring workflow.
