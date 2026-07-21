"""OfficeRnD read-only connector prototype (mock-tested; never live-tested).

Built against OfficeRnD's public documentation accessed 2026-07-18 (see
docs/research/SOURCES.yaml): base
https://app.officernd.com/api/v2/organizations/{org-slug}, OAuth2
client-credentials (client_id/client_secret -> Bearer token), cursor
pagination via cursorNext/cursorPrev fields. The exact token endpoint URL
was NOT verified from the fetched pages, so token acquisition takes the
token URL as an explicit argument rather than hardcoding an unverified
one - resolve it from https://developer.officernd.com/ before live use.

Credentials: OFFICERND_CLIENT_ID / OFFICERND_CLIENT_SECRET environment
variables (or an already-obtained token). Never logged, never in errors.
Entity availability (members, companies, memberships, contracts,
resources, bookings, invoices, payments, locations) follows the vendor's
ERD; any entity a given plan does not expose surfaces as a structured
not_found/auth error rather than fabricated data.
"""

from __future__ import annotations

import json
import os
from collections.abc import Iterator
from typing import Any

from .base import ConnectorError, HttpTransport, Transport, encode_params, get_json

BASE = "https://app.officernd.com/api/v2/organizations"


def fetch_token(token_url: str, client_id: str | None = None,
                client_secret: str | None = None,
                transport: Transport | None = None) -> str:
    """OAuth2 client-credentials token fetch.

    token_url must come from current OfficeRnD documentation (deliberately
    not hardcoded here - see module docstring).
    """
    cid = client_id or os.environ.get("OFFICERND_CLIENT_ID", "")
    secret = client_secret or os.environ.get("OFFICERND_CLIENT_SECRET", "")
    if not cid or not secret:
        raise ConnectorError("auth", "set OFFICERND_CLIENT_ID and "
                                     "OFFICERND_CLIENT_SECRET")
    t = transport or HttpTransport()
    body = (f"grant_type=client_credentials&client_id={cid}"
            f"&client_secret={secret}").encode()
    status, _, resp = t.request(
        "POST", token_url,
        {"Content-Type": "application/x-www-form-urlencoded"}, body)
    if status != 200:
        raise ConnectorError("auth", "token request rejected "
                                     "(credentials not shown)", status)
    try:
        return str(json.loads(resp.decode())["access_token"])
    except (ValueError, KeyError) as e:
        raise ConnectorError("vendor", f"unexpected token response: {e}") from None


class OfficeRnDClient:
    """Read-only access to OfficeRnD entities in canonical rows."""

    def __init__(self, org_slug: str, token: str,
                 transport: Transport | None = None):
        if not org_slug or not token:
            raise ConnectorError("auth", "org_slug and token are required")
        self._base = f"{BASE}/{org_slug}"
        self._headers = {"Authorization": f"Bearer {token}"}
        self._transport = transport or HttpTransport()

    def _paged(self, path: str, params: dict[str, Any] | None = None
               ) -> Iterator[dict[str, Any]]:
        cursor: str | None = None
        while True:
            q: dict[str, Any] = dict(params or {})
            if cursor:
                q["$cursorNext"] = cursor
            data = get_json(self._transport, self._base + path + encode_params(q),
                            self._headers)
            results = data.get("results")
            if results is None:
                results = data.get("_list", []) if "_list" in data else []
            yield from results
            cursor = data.get("cursorNext")
            if not cursor:
                return

    # -- canonical outputs ---------------------------------------------------

    def locations(self) -> list[dict[str, str]]:
        rows = [{
            "location_id": str(o.get("_id", o.get("id", ""))),
            "name": str(o.get("name", "")),
            "address": str((o.get("address") or {}).get("address", "")
                           if isinstance(o.get("address"), dict) else o.get("address", "")),
            "city": "", "market": "",
            "timezone": str(o.get("timezone", "")),
            "opened_on": "", "status": "open", "sellable_workstations": "",
        } for o in self._paged("/locations")]
        rows.sort(key=lambda r: r["location_id"])
        return rows

    def members(self) -> list[dict[str, str]]:
        """OfficeRnD members are PEOPLE (paying entity is the company/team)."""
        rows = []
        for o in self._paged("/members"):
            name = str(o.get("name", "")).strip()
            first, _, last = name.partition(" ")
            rows.append({
                "contact_id": str(o.get("_id", o.get("id", ""))),
                "first_name": first, "last_name": last,
                "email": str(o.get("email", "")),
                "phone": str(o.get("phone", "")),
                "company_id": str(o.get("team", o.get("company", "")) or ""),
                "created_at": str(o.get("createdAt", ""))[:10],
                "consent_marketing": "",
            })
        rows.sort(key=lambda r: r["contact_id"])
        return rows

    def companies(self) -> list[dict[str, str]]:
        rows = [{
            "company_id": str(o.get("_id", o.get("id", ""))),
            "name": str(o.get("name", "")),
            "industry": "", "size": "",
            "created_at": str(o.get("createdAt", ""))[:10],
        } for o in self._paged("/companies")]
        rows.sort(key=lambda r: r["company_id"])
        return rows

    def memberships(self) -> list[dict[str, str]]:
        """Plan assignments -> canonical memberships. Price semantics
        (monthly vs term) and the office/resource assignment field must be
        confirmed per account - see adapters/officernd/README.md traps."""
        rows = []
        for o in self._paged("/memberships"):
            rows.append({
                "membership_id": str(o.get("_id", o.get("id", ""))),
                "company_id": str(o.get("team", o.get("company", "")) or ""),
                "location_id": str(o.get("office", o.get("location", "")) or ""),
                "product": str(o.get("plan", o.get("name", "")) or ""),
                "unit_id": str(o.get("resource", "") or ""),
                "start_date": str(o.get("startDate", ""))[:10],
                "end_date": str(o.get("endDate", "") or "")[:10],
                "term_months": "", "notice_date": "", "renewal_date": "",
                "contracted_rate": str(o.get("price", "")),
                "list_rate": "", "discount_pct": "", "deposit": "",
                "status": "active" if not o.get("endDate") else "",
                "billing_frequency": "", "complimentary": "",
            })
        rows.sort(key=lambda r: r["membership_id"])
        return rows

    def resources(self) -> list[dict[str, str]]:
        rows = []
        for o in self._paged("/resources"):
            rows.append({
                "unit_id": str(o.get("_id", o.get("id", ""))),
                "location_id": str(o.get("office", "") or ""),
                "unit_type": str(o.get("type", "")),
                "name": str(o.get("name", "")),
                "capacity": str(o.get("size", o.get("capacity", "")) or ""),
                "sellable": "", "out_of_service": "",
                "list_price": str(o.get("price", "") or ""),
                "floor": "", "amenities": "", "available_from": "", "notes": "",
            })
        rows.sort(key=lambda r: r["unit_id"])
        return rows

    def bookings(self) -> list[dict[str, str]]:
        rows = []
        for o in self._paged("/bookings"):
            rows.append({
                "booking_id": str(o.get("_id", o.get("id", ""))),
                "location_id": str(o.get("office", "") or ""),
                "room_unit_id": str(o.get("resource", "") or ""),
                "company_id": str(o.get("team", "") or ""),
                "booked_by": str(o.get("member", "") or ""),
                "start_at": str(o.get("start", "")).replace("T", " ")[:16],
                "end_at": str(o.get("end", "")).replace("T", " ")[:16],
                "attendees": "", "amount": str(o.get("price", "") or ""),
                "member_booking": "true" if o.get("member") or o.get("team") else "false",
            })
        rows.sort(key=lambda r: r["booking_id"])
        return rows

    def invoices(self) -> list[dict[str, str]]:
        rows = []
        for o in self._paged("/invoices"):
            rows.append({
                "invoice_id": str(o.get("_id", o.get("id", ""))),
                "company_id": str(o.get("team", o.get("company", "")) or ""),
                "membership_id": "",
                "issue_date": str(o.get("issueDate", o.get("date", "")))[:10],
                "due_date": str(o.get("dueDate", "") or "")[:10],
                "amount": str(o.get("total", o.get("amount", "")) or ""),
                "tax": "", "status": str(o.get("status", "")).lower(),
                "paid_date": "",
            })
        rows.sort(key=lambda r: r["invoice_id"])
        return rows
