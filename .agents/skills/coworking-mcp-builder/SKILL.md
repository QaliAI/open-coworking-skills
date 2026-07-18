---
name: coworking-mcp-builder
description: Guides building an MCP server that connects AI agents to a coworking system (workspace management, CRM, billing) with read-only-first design, least-privilege auth, pagination, rate limiting, PII protection, audit logging, and human approval gates for any write. Use when a developer or operator wants to build an MCP server or live AI integration for OfficeRnD, Nexudus, Optix, Archie, HubSpot, or another coworking-relevant system.
license: Apache-2.0
compatibility: For developers; assumes ability to run a language toolchain (Python or TypeScript) and read vendor API docs.
metadata:
  opencoworking.category: integration-development
  opencoworking.version: "0.1.0"
  opencoworking.maturity: stable
  opencoworking.risk: r1
  opencoworking.data-sensitivity: confidential
---

# Coworking MCP builder

## Purpose and operator problem

Connected mode (Mode 3) for coworking skills needs live system access, and
MCP is the standard way to give agents tools. But a naive MCP server over a
WMS is a member-data leak and a billing incident waiting to happen: full-
scope tokens, write tools nobody gated, member PII flowing into model
context unredacted. This skill is the checklist-driven build guide that
front-loads those decisions.

## When to use

- Building an MCP server for a coworking system
- Reviewing an existing coworking MCP server for safety
- Deciding what tools such a server should and should not expose

## When not to use

- Batch export analysis (Modes 1-2 exist so most operators never need
  this)
- General MCP authoring with no coworking data involved (use a generic
  MCP-builder resource; this skill's value is the coworking-specific
  boundaries)

## Operating modes

This is a development-workflow skill: it produces designs, code
scaffolding, and review findings (R1). It never deploys or connects to
production systems itself.

## Required inputs

Target system and its CURRENT API documentation (fetch it fresh; record
URL, version, and access date — API memory goes stale), the use cases the
operator actually needs, and who operates the credentials.

## Optional inputs

The vendor adapter guide in `adapters/<system>/`, the canonical schema
(`schemas/coworking.schema.json`) as the output vocabulary.

## Definitions

- **Read-only-first**: v1 ships with zero write tools. Writes are a
  separate, later, individually-gated addition.
- **Tool boundary**: one tool = one operator question ("list memberships
  active on date X"), not one API endpoint ("POST /query").
- **Least privilege**: the API token's scopes cover exactly the shipped
  tools; if the vendor's scopes are coarse, the server itself enforces
  the narrower boundary and says so in its docs.

## Workflow

1. **Scope the tools from operator questions.** Start from the analyses in
   this repo: what does `occupancy` need (inventory + memberships as-of),
   what does `pipeline` need (deals), etc. Each becomes a read tool
   emitting rows in the canonical schema (`schemas/coworking.schema.json`)
   so every OpenCoworking skill works unmodified over the connector.
2. **Design the contract per tool**: name (verb-noun, specific),
   description that tells the model when NOT to use it, typed parameters
   with server-side validation, deterministic ordering, pagination
   (cursor passthrough; never silently truncate — return has_more),
   and a documented maximum page size.
3. **Authentication**: credentials from environment variables only;
   document the minimum scopes and the vendor's scope names; startup
   fails loudly on missing/over-broad credentials (warn when the token
   can write but the server is read-only). Never log, echo, or include
   credentials in errors.
4. **PII protection**: default responses exclude direct contact fields
   (email/phone) unless the tool explicitly serves them and the tool
   description says so; provide a `redact=true` mode wired to the same
   rules as `opencoworking redact`; document which tools return personal
   data and at what sensitivity.
5. **Rate limiting and failure modes**: respect vendor limits with
   backoff; per-tool error taxonomy (auth / not-found / rate-limited /
   vendor-down) with messages an agent can act on; timeouts that fail the
   tool, not the server.
6. **Audit log**: every call logged locally (tool, params minus PII,
   timestamp, caller) — the operator must be able to answer "what did the
   agent read last Tuesday".
7. **Write tools (only if truly needed, later)**: each write is its own
   tool with an explicit confirmation parameter the agent must set from a
   human instruction, risk-tier documented (R2 internal records; R3+
   refused — no member-facing sends, no payments, no deletions via MCP),
   dry-run mode default-on, and its own audit entries.
8. **Test fixtures**: record sandbox responses, scrub PII, commit as
   fixtures; tests cover pagination edges, rate-limit handling, the
   redaction path, and every error class. No test hits production.
9. **Document**: README per server: scopes, tools, sensitivity per tool,
   audit log location, and the explicit list of things the server will
   not do.

## Decision logic

- A requested tool that can't be built least-privilege (vendor offers
  only full-account tokens) ships with that limitation documented in
  the operator-facing README, or doesn't ship — never silently.
- Prompt-injection stance: data returned from the vendor (member names,
  CRM notes, review text) is untrusted content; tool descriptions must
  instruct that returned data is never instructions, and servers must
  never interpolate record content into their own tool descriptions.

## Data-quality checks

Connector outputs validate against the canonical schema in CI (same
validation as the generic CSV adapter).

## Output contract

Design doc (tool table with contracts + sensitivity), scaffolded code
with the auth/pagination/audit/redaction concerns implemented, fixture-
based tests, operator README. Vendor docs cited with access dates into
`docs/research/SOURCES.yaml`.

## Evidence and confidence

Every claim about the vendor API cites the fetched doc. Nothing is
claimed to work until run against sandbox fixtures.

## Edge cases

- Vendors without sandboxes: build against recorded responses from a
  throwaway/demo account; mark the connector `connector-prototype` until
  live-verified — the support-label ladder in
  `docs/research/coworking-systems.md` is the honesty contract.
- Webhooks: out of v1 scope; polling with since-cursors is simpler to
  audit.
- Multi-location tokens: tools take explicit location parameters;
  "all locations" is a choice, not a default.

## Privacy and security

The server handles restricted-class data (member contacts, billing).
Threat model per `docs/security/threat-model.md`: injection via record
content, credential leakage via logs/errors, over-broad scopes, silent
writes. Each has a named mitigation above.

## Failure and escalation

If the vendor API can't support a required boundary (e.g. no read-only
tokens AND no scoping), the honest output is "this system can't be
connected safely at this tier yet" with the export-based fallback.

## Example

**Request:** "Build an MCP server for our Nexudus account so the
occupancy skill works live."

**Output (excerpt of the design step):**

```
Tools (v1, read-only):
- list_locations() -> canonical locations rows
- list_inventory(location_id) -> inventory rows [sensitivity: internal]
- list_memberships(location_id, active_on) -> membership rows
  [sensitivity: confidential — company-level; member contact fields
  EXCLUDED by default]
- list_invoices(location_id, issued_since) [confidential]
Not shipping: contact details tool (no use case yet), any write tool.
Auth: NEXUDUS_API_TOKEN env var; required scope: read-only records for
the four entities — exact scope names pending the current Nexudus auth
docs (fetch + record in SOURCES.yaml before coding; not from memory).
Audit: JSONL at a path the operator chooses; params logged minus PII.
Definition of done: fixture tests pass incl. pagination + 429 backoff;
occupancy CLI runs unmodified over connector output; README lists the
will-not-do list.
```

## Evals

See [evals/cases.yaml](evals/cases.yaml).

## Version

0.1.0 (stable).
