"""HubSpot read-only connector prototype (mock-tested; never live-tested).

Built against HubSpot's public documentation accessed 2026-07-18 (see
docs/research/SOURCES.yaml): base https://api.hubapi.com, CRM v3 object
endpoints, Bearer private-app token auth, cursor pagination via
paging.next.after, tiered rate limits (roughly 100-190 requests/10s per
private app depending on subscription - respected here via retry/backoff,
not assumed away). HubSpot has begun rolling out calendar-versioned
object endpoints; this prototype uses the widely-deployed v3 paths and
records that choice - re-verify before any live use.

Credentials: HUBSPOT_ACCESS_TOKEN environment variable (a private-app
token whose scopes should be limited to crm.objects.*.read for the
objects actually used). The token is never logged and never appears in
errors.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

from .base import ConnectorError, HttpTransport, Transport, encode_params, get_json

BASE = "https://api.hubapi.com"
PAGE_SIZE = 100

# Explicit property lists - request only what the canonical model needs.
CONTACT_PROPS = ["firstname", "lastname", "email", "phone", "createdate",
                 "associatedcompanyid"]
COMPANY_PROPS = ["name", "industry", "numberofemployees", "createdate"]
DEAL_PROPS = ["dealname", "dealstage", "pipeline", "amount", "createdate",
              "hs_lastmodifieddate", "closedate", "hubspot_owner_id"]


class HubSpotClient:
    """Read-only access to HubSpot CRM objects in canonical rows."""

    def __init__(self, token: str | None = None, transport: Transport | None = None):
        tok = token or os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
        if not tok:
            raise ConnectorError(
                "auth", "no token: set HUBSPOT_ACCESS_TOKEN (private-app token with "
                        "read-only CRM scopes)")
        self._headers = {"Authorization": f"Bearer {tok}",
                         "Content-Type": "application/json"}
        self._transport = transport or HttpTransport()

    # -- raw paged reads -----------------------------------------------------

    def _paged(self, path: str, params: dict[str, Any]) -> Iterator[dict[str, Any]]:
        after: str | None = None
        while True:
            q = dict(params)
            q["limit"] = PAGE_SIZE
            if after:
                q["after"] = after
            data = get_json(self._transport, BASE + path + encode_params(q),
                            self._headers)
            yield from data.get("results", [])
            after = (data.get("paging") or {}).get("next", {}).get("after")
            if not after:
                return

    def _objects(self, object_type: str, properties: list[str],
                 associations: str | None = None) -> Iterator[dict[str, Any]]:
        params: dict[str, Any] = {"properties": ",".join(properties)}
        if associations:
            params["associations"] = associations
        return self._paged(f"/crm/v3/objects/{object_type}", params)

    def list_owners(self) -> list[dict[str, str]]:
        """Owners (for deal/lead ownership names)."""
        return [{"owner_id": str(o.get("id", "")),
                 "email": str(o.get("email", "")),
                 "name": f"{o.get('firstName', '')} {o.get('lastName', '')}".strip()}
                for o in self._paged("/crm/v3/owners", {})]

    def list_pipelines(self) -> list[dict[str, Any]]:
        """Deal pipelines and their stage labels (stage mapping is per-portal
        and must be confirmed by the operator, never assumed)."""
        data = get_json(self._transport, BASE + "/crm/v3/pipelines/deals",
                        self._headers)
        return [{"pipeline_id": p.get("id"), "label": p.get("label"),
                 "stages": [{"stage_id": s.get("id"), "label": s.get("label")}
                            for s in p.get("stages", [])]}
                for p in data.get("results", [])]

    # -- canonical outputs ---------------------------------------------------

    def contacts(self) -> list[dict[str, str]]:
        rows = []
        for o in self._objects("contacts", CONTACT_PROPS):
            p = o.get("properties", {}) or {}
            rows.append({
                "contact_id": str(o.get("id", "")),
                "first_name": p.get("firstname") or "",
                "last_name": p.get("lastname") or "",
                "email": p.get("email") or "",
                "phone": p.get("phone") or "",
                "company_id": p.get("associatedcompanyid") or "",
                "created_at": (p.get("createdate") or "")[:10],
                "consent_marketing": "",
            })
        rows.sort(key=lambda r: r["contact_id"])
        return rows

    def companies(self) -> list[dict[str, str]]:
        rows = []
        for o in self._objects("companies", COMPANY_PROPS):
            p = o.get("properties", {}) or {}
            rows.append({
                "company_id": str(o.get("id", "")),
                "name": p.get("name") or "",
                "industry": p.get("industry") or "",
                "size": p.get("numberofemployees") or "",
                "created_at": (p.get("createdate") or "")[:10],
            })
        rows.sort(key=lambda r: r["company_id"])
        return rows

    def deals(self, stage_map: dict[str, str] | None = None) -> list[dict[str, str]]:
        """Deals in canonical rows.

        stage_map maps portal-specific stage IDs to the canonical stages
        (new/qualified/tour/proposal/negotiation/won/lost). Without a map,
        the raw stage id is kept verbatim and analyses that need canonical
        stages must refuse - never guess a portal's stage semantics.
        Amounts: HubSpot 'amount' is usually TOTAL contract value, not
        monthly - the raw value is emitted under expected_value with that
        caveat carried in the adapter guide.
        """
        rows = []
        for o in self._objects("deals", DEAL_PROPS, associations="companies"):
            p = o.get("properties", {}) or {}
            assoc = (o.get("associations", {}) or {}).get("companies", {})
            company_ids = [str(r.get("id", "")) for r in assoc.get("results", [])]
            raw_stage = p.get("dealstage") or ""
            rows.append({
                "deal_id": str(o.get("id", "")),
                "lead_id": "",
                "company_id": company_ids[0] if company_ids else "",
                "location_id": "",
                "product": "",
                "stage": (stage_map or {}).get(raw_stage, raw_stage),
                "created_at": (p.get("createdate") or "")[:10],
                "updated_at": (p.get("hs_lastmodifieddate") or "")[:10],
                "expected_value": p.get("amount") or "",
                "expected_move_in": (p.get("closedate") or "")[:10],
                "owner": p.get("hubspot_owner_id") or "",
                "next_action": "",
                "next_action_date": "",
                "lost_reason": "",
            })
        rows.sort(key=lambda r: r["deal_id"])
        return rows
