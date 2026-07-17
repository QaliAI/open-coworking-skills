"""Export analyses over the vendor-neutral coworking schema.

Every function takes loaded Tables (see ingest.py) whose columns follow the
canonical schema in schemas/ (mapped from vendor exports via the data
dictionary). Functions return plain dict reports that carry findings,
formula contracts, and data-quality caveats. They never guess: missing
inputs produce explicit warnings, not invented numbers.
"""

from __future__ import annotations

import statistics
from datetime import date, timedelta
from decimal import Decimal

from .ingest import Table
from .metrics import (
    Unit,
    ZERO,
    financial_occupancy,
    office_occupancy,
    workstation_occupancy,
)
from .normalize import normalize_source, parse_date, parse_datetime, parse_money

Row = dict[str, str]

# Column signatures used to guess what entity an unknown export contains.
ENTITY_SIGNATURES: dict[str, set[str]] = {
    "leads": {"lead_id", "source", "inquiry_product", "first_response_at"},
    "deals": {"deal_id", "stage", "expected_value"},
    "tours": {"tour_id", "scheduled_at", "toured_product"},
    "contacts": {"contact_id", "email", "first_name"},
    "companies": {"company_id", "industry"},
    "inventory": {"unit_id", "unit_type", "capacity", "list_price"},
    "memberships": {"membership_id", "contracted_rate", "start_date"},
    "invoices": {"invoice_id", "due_date", "amount"},
    "payments": {"payment_id", "paid_at", "method"},
    "locations": {"location_id", "timezone", "sellable_workstations"},
    "members": {"member_id", "onboarded_on"},
    "room_bookings": {"booking_id", "start_at", "attendees"},
    "virtual_office_partners": {"partner_id", "billing_model"},
}


def _truthy(v: str) -> bool:
    return v.strip().lower() in {"1", "true", "yes", "y", "x"}


def _money(v: str) -> Decimal | None:
    return parse_money(v)


# --- Export inspection ------------------------------------------------------

def inspect_table(table: Table) -> dict[str, object]:
    """Identify the likely entity and structural issues of an unknown export.

    Deliberately ignores the filename: identification uses column overlap with
    known entity signatures only, and reports its confidence.
    """
    cols = {c.lower() for c in table.columns}
    scores: list[tuple[str, float]] = []
    for entity, sig in ENTITY_SIGNATURES.items():
        overlap = len(cols & sig) / len(sig)
        if overlap > 0:
            scores.append((entity, round(overlap, 2)))
    scores.sort(key=lambda t: -t[1])
    best = scores[0] if scores and scores[0][1] >= 0.5 else None
    return {
        "source": table.source,
        "rows": len(table.rows),
        "columns": table.columns,
        "structure_warnings": table.warnings,
        "likely_entity": best[0] if best else None,
        "confidence": best[1] if best else 0.0,
        "candidates": scores[:3],
        "note": "Entity identified from column names only; filenames are ignored. "
                "Confirm the mapping before analysis.",
    }


# --- Occupancy --------------------------------------------------------------

def build_units(inventory: Table, memberships: Table,
                as_of: date, location_id: str | None = None) -> tuple[list[Unit], list[dict[str, object]]]:
    """Join inventory and memberships into metric-ready Units.

    A membership is active on as_of when status == 'active' and
    start_date <= as_of and (no end_date or end_date >= as_of).
    Returns (units, issues) where issues record referential problems:
    memberships pointing at unknown units, multiple active memberships on one
    unit, and active memberships with no unit assignment.
    """
    issues: list[dict[str, object]] = []
    active_by_unit: dict[str, list[Row]] = {}
    unassigned: list[Row] = []
    known_units = {r.get("unit_id", "").strip() for r in inventory.rows}

    for m in memberships.rows:
        if location_id and m.get("location_id", "").strip() != location_id:
            continue
        status = m.get("status", "").strip().lower()
        start = parse_date(m.get("start_date", ""))
        end = parse_date(m.get("end_date", ""))
        active = (status == "active" and start is not None and start <= as_of
                  and (end is None or end >= as_of))
        if not active:
            continue
        unit_id = m.get("unit_id", "").strip()
        if not unit_id:
            unassigned.append(m)
        elif unit_id not in known_units:
            issues.append({"type": "membership_unknown_unit",
                           "membership_id": m.get("membership_id", "?"),
                           "unit_id": unit_id})
        else:
            active_by_unit.setdefault(unit_id, []).append(m)

    if unassigned:
        issues.append({"type": "active_memberships_without_unit",
                       "count": len(unassigned),
                       "membership_ids": [m.get("membership_id", "?") for m in unassigned][:20],
                       "note": "Not an error for floating/community memberships, but they are "
                               "excluded from unit occupancy and shown separately."})

    units: list[Unit] = []
    for r in inventory.rows:
        if location_id and r.get("location_id", "").strip() != location_id:
            continue
        uid = r.get("unit_id", "").strip()
        assigned = active_by_unit.get(uid, [])
        if len(assigned) > 1:
            issues.append({"type": "multiple_active_memberships_on_unit", "unit_id": uid,
                           "membership_ids": [m.get("membership_id", "?") for m in assigned]})
        contracted = sum(((_money(m.get("contracted_rate", "")) or ZERO) for m in assigned), ZERO)
        comped = any(_truthy(m.get("complimentary", "")) for m in assigned)
        try:
            capacity = int(r.get("capacity", "") or 0)
        except ValueError:
            capacity = 0
            issues.append({"type": "bad_capacity", "unit_id": uid,
                           "value": r.get("capacity", "")})
        units.append(Unit(
            unit_id=uid,
            unit_type=r.get("unit_type", "").strip().lower(),
            capacity=capacity,
            sellable=_truthy(r.get("sellable", "true") or "true"),
            out_of_service=_truthy(r.get("out_of_service", "")),
            occupied=bool(assigned),
            complimentary=comped,
            list_price=_money(r.get("list_price", "")),
            contracted_revenue=ZERO if comped else contracted,
        ))
    return units, issues


def occupancy_report(inventory: Table, memberships: Table, as_of: date,
                     discount_flag_pct: int = 25) -> dict[str, object]:
    """Occupancy dashboard: physical vs financial, with distortion flags."""
    units, issues = build_units(inventory, memberships, as_of)
    metrics = [
        office_occupancy(units).as_dict(),
        workstation_occupancy(units).as_dict(),
        financial_occupancy(units).as_dict(),
    ]
    flags: list[dict[str, object]] = []
    oos = [u.unit_id for u in units if u.out_of_service]
    if oos:
        flags.append({"flag": "out_of_service_units", "units": oos,
                      "why": "Excluded from occupancy denominators; each is capacity "
                             "producing no revenue."})
    comped = [u.unit_id for u in units if u.occupied and u.complimentary]
    if comped:
        flags.append({"flag": "complimentary_occupancy", "units": comped,
                      "why": "Counted as occupied but contribute zero revenue; they inflate "
                             "count-based occupancy relative to financial occupancy."})
    unpriced = [u.unit_id for u in units if u.sellable and not u.out_of_service
                and u.list_price is None]
    if unpriced:
        flags.append({"flag": "missing_list_price", "units": unpriced,
                      "why": "Excluded from financial occupancy on both sides."})
    discounted = []
    for u in units:
        if u.occupied and not u.complimentary and u.list_price and u.list_price > 0:
            disc = (u.list_price - u.contracted_revenue) / u.list_price * 100
            if disc >= discount_flag_pct:
                discounted.append({"unit_id": u.unit_id, "discount_pct": str(round(disc, 1))})
    if discounted:
        flags.append({"flag": f"discount_over_{discount_flag_pct}pct", "units": discounted,
                      "why": "Occupied but materially below list; physical occupancy hides "
                             "the revenue gap."})
    return {"as_of": as_of.isoformat(), "unit_count": len(units),
            "metrics": metrics, "flags": flags, "referential_issues": issues}


# --- Pipeline health --------------------------------------------------------

OPEN_STAGES = {"new", "contacted", "qualified", "tour_booked", "tour", "tour_completed",
               "proposal", "negotiation"}
CLOSED_STAGES = {"won", "lost"}


def pipeline_report(deals: Table, as_of: date, stale_days: int = 21) -> dict[str, object]:
    """Pipeline hygiene: aging, missing next actions, ownership, duplicates."""
    findings: dict[str, list[dict[str, object]]] = {
        "stale_deals": [], "missing_next_action": [], "overdue_next_action": [],
        "unassigned": [], "invalid_stage": [], "duplicate_open_deals": [],
    }
    stage_counts: dict[str, int] = {}
    owner_open: dict[str, int] = {}
    open_by_key: dict[tuple[str, str], list[str]] = {}

    for r in deals.rows:
        did = r.get("deal_id", "?")
        stage = r.get("stage", "").strip().lower()
        stage_counts[stage or "(blank)"] = stage_counts.get(stage or "(blank)", 0) + 1
        if stage and stage not in OPEN_STAGES | CLOSED_STAGES:
            findings["invalid_stage"].append({"deal_id": did, "stage": stage})
            continue
        if stage in CLOSED_STAGES:
            continue
        owner = r.get("owner", "").strip()
        if not owner:
            findings["unassigned"].append({"deal_id": did, "stage": stage})
        else:
            owner_open[owner] = owner_open.get(owner, 0) + 1
        updated = parse_date(r.get("updated_at", "")) or parse_date(r.get("created_at", ""))
        if updated and (as_of - updated).days >= stale_days:
            findings["stale_deals"].append(
                {"deal_id": did, "stage": stage, "owner": owner or None,
                 "days_since_update": (as_of - updated).days})
        na, nad = r.get("next_action", "").strip(), parse_date(r.get("next_action_date", ""))
        if not na:
            findings["missing_next_action"].append({"deal_id": did, "stage": stage,
                                                    "owner": owner or None})
        elif nad and nad < as_of:
            findings["overdue_next_action"].append(
                {"deal_id": did, "next_action": na, "due": nad.isoformat(),
                 "days_overdue": (as_of - nad).days})
        key = (r.get("company_id", "").strip().lower(), r.get("product", "").strip().lower())
        if all(key):
            open_by_key.setdefault(key, []).append(did)

    for (company, product), ids in open_by_key.items():
        if len(ids) > 1:
            findings["duplicate_open_deals"].append(
                {"company_id": company, "product": product, "deal_ids": ids})

    return {"as_of": as_of.isoformat(), "deal_count": len(deals.rows),
            "stage_counts": dict(sorted(stage_counts.items())),
            "open_deals_by_owner": dict(sorted(owner_open.items())),
            "stale_threshold_days": stale_days, "findings": findings}


def funnel_report(leads: Table, tours: Table, deals: Table) -> dict[str, object]:
    """Stage-to-stage conversion counts with explicit definitions.

    Counts are entity-linked where the data allows (tours joined to leads by
    lead_id) and fall back to totals with a disclosed caveat otherwise.
    """
    lead_ids = {r.get("lead_id", "").strip() for r in leads.rows if r.get("lead_id", "").strip()}
    contacted = sum(1 for r in leads.rows
                    if r.get("status", "").strip().lower() not in {"", "new"})
    tours_booked_leads = {r.get("lead_id", "").strip() for r in tours.rows
                          if r.get("lead_id", "").strip() in lead_ids}
    tours_completed = [r for r in tours.rows
                       if r.get("status", "").strip().lower() == "completed"]
    no_shows = [r for r in tours.rows if r.get("status", "").strip().lower() == "no_show"]
    scheduled_or_done = [r for r in tours.rows
                         if r.get("status", "").strip().lower() in
                         {"completed", "no_show", "scheduled"}]
    won = [r for r in deals.rows if r.get("stage", "").strip().lower() == "won"]
    caveats = []
    if len(tours_booked_leads) < len(tours.rows):
        caveats.append("Some tours reference lead_ids absent from the leads export; "
                       "lead-to-tour uses matched tours only.")
    show_den = len([r for r in scheduled_or_done
                    if r.get("status", "").strip().lower() in {"completed", "no_show"}])
    return {
        "counts": {
            "leads": len(lead_ids), "contacted": contacted,
            "leads_with_tour": len(tours_booked_leads),
            "tours_completed": len(tours_completed), "tour_no_shows": len(no_shows),
            "deals_won": len(won),
        },
        "rates": {
            "lead_to_contact": _rate(contacted, len(lead_ids)),
            "lead_to_tour": _rate(len(tours_booked_leads), len(lead_ids)),
            "tour_show_rate": _rate(len(tours_completed), show_den),
            "lead_to_won": _rate(len(won), len(lead_ids)),
        },
        "definitions": {
            "lead_to_contact": "leads with status beyond 'new' / all leads",
            "lead_to_tour": "distinct leads with >=1 tour record / all leads",
            "tour_show_rate": "completed tours / (completed + no-show tours); "
                              "still-scheduled tours excluded",
            "lead_to_won": "won deals / all leads (period alignment is the caller's "
                           "responsibility and can distort this rate)",
        },
        "caveats": caveats,
    }


def _rate(num: int, den: int) -> str | None:
    return None if den == 0 else str(round(num / den, 4))


# --- Speed to lead ----------------------------------------------------------

def speed_to_lead_report(leads: Table, business_hours: bool = True,
                         open_hour: int = 9, close_hour: int = 17) -> dict[str, object]:
    """First-response timing from created_at to first_response_at.

    Uses business minutes (location-local timestamps assumed) when
    business_hours is True. Leads without a first response are reported
    separately, never averaged in as zero.
    """
    from .metrics import business_minutes_between

    minutes: list[int] = []
    no_response: list[str] = []
    unparseable: list[str] = []
    for r in leads.rows:
        created = parse_datetime(r.get("created_at", ""))
        responded = parse_datetime(r.get("first_response_at", ""))
        lid = r.get("lead_id", "?")
        if created is None:
            unparseable.append(lid)
            continue
        if responded is None:
            no_response.append(lid)
            continue
        if business_hours:
            minutes.append(business_minutes_between(created, responded,
                                                    open_hour, close_hour))
        else:
            minutes.append(max(0, int((responded - created).total_seconds() // 60)))
    out: dict[str, object] = {
        "responded_leads": len(minutes),
        "leads_without_response": no_response,
        "leads_with_unparseable_created_at": unparseable,
        "basis": (f"business minutes {open_hour:02d}:00-{close_hour:02d}:00 Mon-Fri, "
                  "location-local timestamps" if business_hours else "clock minutes"),
        "caveat": "first_response_at must be the first human contact attempt, not an "
                  "automated acknowledgment; verify what the source system stores.",
    }
    if minutes:
        out["median_minutes"] = int(statistics.median(minutes))
        out["p90_minutes"] = int(sorted(minutes)[max(0, int(len(minutes) * 0.9) - 1)])
        out["max_minutes"] = max(minutes)
    return out


# --- Lead sources -----------------------------------------------------------

def source_report(leads: Table) -> dict[str, object]:
    """Normalize raw source labels into canonical buckets."""
    buckets: dict[str, int] = {}
    unmapped: dict[str, int] = {}
    blank = 0
    for r in leads.rows:
        canonical, conf = normalize_source(r.get("source", ""))
        buckets[canonical] = buckets.get(canonical, 0) + 1
        if conf == "unknown":
            blank += 1
        elif conf == "unmapped":
            unmapped[r.get("source", "").strip()] = unmapped.get(r.get("source", "").strip(), 0) + 1
    return {"total_leads": len(leads.rows),
            "by_canonical_source": dict(sorted(buckets.items(), key=lambda kv: -kv[1])),
            "blank_sources": blank,
            "unmapped_labels": unmapped,
            "note": "Unmapped labels kept verbatim (lowercased); review and extend the "
                    "mapping rather than guessing."}


# --- Revenue leakage --------------------------------------------------------

def leakage_report(as_of: date, leads: Table | None = None, deals: Table | None = None,
                   tours: Table | None = None, memberships: Table | None = None,
                   invoices: Table | None = None, inventory: Table | None = None,
                   payments: Table | None = None) -> dict[str, object]:
    """Cross-file revenue leakage audit. Each check runs only when its inputs
    exist; skipped checks are listed so absence of a finding is never mistaken
    for absence of a problem."""
    findings: list[dict[str, object]] = []
    skipped: list[str] = []

    if leads is not None:
        unworked = [r.get("lead_id", "?") for r in leads.rows
                    if r.get("status", "").strip().lower() in {"", "new"}
                    and not r.get("first_response_at", "").strip()]
        if unworked:
            findings.append({"check": "unfollowed_leads", "count": len(unworked),
                             "ids": unworked[:25],
                             "detail": "Leads still 'new' with no recorded first response."})
    else:
        skipped.append("unfollowed_leads (needs leads)")

    if deals is not None:
        stale = [r.get("deal_id", "?") for r in deals.rows
                 if r.get("stage", "").strip().lower() in OPEN_STAGES
                 and (d := parse_date(r.get("updated_at", ""))) is not None
                 and (as_of - d).days >= 30]
        if stale:
            findings.append({"check": "stale_open_deals_30d", "count": len(stale),
                             "ids": stale[:25],
                             "detail": "Open deals untouched for 30+ days."})
    else:
        skipped.append("stale_open_deals_30d (needs deals)")

    if tours is not None:
        ghosts = [r.get("tour_id", "?") for r in tours.rows
                  if r.get("status", "").strip().lower() == "completed"
                  and not r.get("next_action", "").strip()]
        if ghosts:
            findings.append({"check": "completed_tours_without_next_action",
                             "count": len(ghosts), "ids": ghosts[:25],
                             "detail": "Completed tours with no recorded next step."})
    else:
        skipped.append("completed_tours_without_next_action (needs tours)")

    if deals is not None and memberships is not None:
        won_companies = {r.get("company_id", "").strip() for r in deals.rows
                         if r.get("stage", "").strip().lower() == "won"
                         and r.get("company_id", "").strip()}
        member_companies = {r.get("company_id", "").strip() for r in memberships.rows
                            if r.get("status", "").strip().lower() in {"active", "pending"}}
        missing = sorted(won_companies - member_companies)
        if missing:
            findings.append({"check": "won_deals_without_membership", "count": len(missing),
                             "ids": missing[:25],
                             "detail": "Companies with a won deal but no active or pending "
                                       "membership; possible unstarted or unrecorded agreements."})
    else:
        skipped.append("won_deals_without_membership (needs deals + memberships)")

    if memberships is not None and invoices is not None:
        window = as_of - timedelta(days=45)
        invoiced = {r.get("membership_id", "").strip() for r in invoices.rows
                    if (d := parse_date(r.get("issue_date", ""))) is not None and d >= window}
        unbilled = []
        for r in memberships.rows:
            if (r.get("status", "").strip().lower() == "active"
                    and not _truthy(r.get("complimentary", ""))
                    and r.get("membership_id", "").strip() not in invoiced):
                rate = _money(r.get("contracted_rate", ""))
                unbilled.append({"membership_id": r.get("membership_id", "?"),
                                 "monthly_rate": None if rate is None else str(rate)})
        if unbilled:
            at_risk = sum((Decimal(u["monthly_rate"]) for u in unbilled
                           if u["monthly_rate"]), ZERO)
            findings.append({"check": "active_memberships_without_recent_invoice",
                             "count": len(unbilled), "items": unbilled[:25],
                             "monthly_amount_at_risk": str(at_risk),
                             "detail": "Active, non-complimentary memberships with no invoice "
                                       "issued in the last 45 days."})
    else:
        skipped.append("active_memberships_without_recent_invoice (needs memberships + invoices)")

    if invoices is not None:
        failed = [{"invoice_id": r.get("invoice_id", "?"),
                   "amount": r.get("amount", "")}
                  for r in invoices.rows
                  if r.get("status", "").strip().lower() in {"failed", "overdue"}]
        if failed:
            amt = sum((_money(f["amount"]) or ZERO for f in failed), ZERO)
            findings.append({"check": "failed_or_overdue_invoices", "count": len(failed),
                             "items": failed[:25], "amount_outstanding": str(amt),
                             "detail": "Invoices failed or past due."})
    else:
        skipped.append("failed_or_overdue_invoices (needs invoices)")

    if inventory is not None:
        blocked = []
        for r in inventory.rows:
            if _truthy(r.get("out_of_service", "")):
                price = _money(r.get("list_price", ""))
                blocked.append({"unit_id": r.get("unit_id", "?"),
                                "monthly_list_price": None if price is None else str(price)})
        if blocked:
            amt = sum((Decimal(b["monthly_list_price"]) for b in blocked
                       if b["monthly_list_price"]), ZERO)
            findings.append({"check": "out_of_service_inventory", "count": len(blocked),
                             "items": blocked, "monthly_list_value_blocked": str(amt),
                             "detail": "Units marked out of service; verify each is "
                                       "genuinely unusable rather than forgotten."})
    else:
        skipped.append("out_of_service_inventory (needs inventory)")

    if memberships is not None:
        expired = [r.get("membership_id", "?") for r in memberships.rows
                   if r.get("status", "").strip().lower() == "active"
                   and (d := parse_date(r.get("end_date", ""))) is not None and d < as_of]
        if expired:
            findings.append({"check": "active_status_past_end_date", "count": len(expired),
                             "ids": expired[:25],
                             "detail": "Memberships marked active past their end date; either "
                                       "renewals were not recorded or billing may be wrong."})
    else:
        skipped.append("active_status_past_end_date (needs memberships)")

    return {"as_of": as_of.isoformat(), "findings": findings, "skipped_checks": skipped,
            "quantification_note": "Amounts are sums of the listed records only; no "
                                   "extrapolation is applied."}


# --- Virtual office reconciliation ------------------------------------------

def vo_reconciliation(partners: Table, memberships: Table, invoices: Table,
                      as_of: date) -> dict[str, object]:
    """Reconcile virtual-office clients across partner records, memberships,
    and invoices. Direct-billed clients should have operator invoices;
    partner-billed clients should NOT be double-billed by the operator."""
    findings: list[dict[str, object]] = []
    vo_memberships = {r.get("company_id", "").strip(): r for r in memberships.rows
                      if "virtual" in r.get("product", "").strip().lower()
                      and r.get("status", "").strip().lower() == "active"}
    partner_clients: dict[str, Row] = {}
    for r in partners.rows:
        if not _truthy(r.get("active", "true")):
            continue
        cid = r.get("client_company_id", "").strip()
        if cid in partner_clients:
            findings.append({"check": "duplicate_partner_client", "company_id": cid,
                             "detail": "Client appears under multiple active partner records."})
        partner_clients[cid] = r

    invoiced_companies = {r.get("company_id", "").strip() for r in invoices.rows}

    for cid, p in partner_clients.items():
        if cid and cid not in vo_memberships:
            findings.append({"check": "partner_client_without_membership", "company_id": cid,
                             "partner": p.get("partner_name", "?"),
                             "detail": "Partner bills for this client but no active virtual-office "
                                       "membership exists; fulfillment obligation may be untracked."})
        if p.get("billing_model", "").strip().lower() == "partner_billed" and cid in invoiced_companies:
            findings.append({"check": "possible_double_billing", "company_id": cid,
                             "partner": p.get("partner_name", "?"),
                             "detail": "Partner-billed client also has operator invoices; verify "
                                       "the operator invoices are for add-ons, not the base service."})

    for cid, m in vo_memberships.items():
        if cid in partner_clients:
            continue
        if cid not in invoiced_companies:
            findings.append({"check": "direct_vo_client_never_invoiced", "company_id": cid,
                             "membership_id": m.get("membership_id", "?"),
                             "detail": "Active direct virtual-office membership with no invoice "
                                       "on record."})

    return {"as_of": as_of.isoformat(),
            "active_vo_memberships": len(vo_memberships),
            "active_partner_clients": len(partner_clients),
            "findings": findings,
            "caveat": "Reconciliation matches on company_id only; name-based fuzzy matching "
                      "is deliberately not attempted. Fix IDs at the source."}
