"""Wave 2 analyses: reconciliation, daily brief, forecast, renewal scan,
pricing audit, collections queue, room yield, and location benchmark.

Same contract as analyze.py: canonical-schema Tables in, plain dict reports
out, explicit definitions, no invented values, missing inputs disclosed.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal

from .analyze import OPEN_STAGES, _money, _truthy, build_units
from .ingest import Table
from .metrics import ZERO
from .normalize import parse_date, parse_datetime

Row = dict[str, str]

# --- CRM <-> WMS reconciliation ---------------------------------------------

_NAME_NOISE = re.compile(r"\b(inc|llc|ltd|gmbh|co|corp|company|demo)\b\.?|[^a-z0-9 ]", re.I)


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", _NAME_NOISE.sub("", name.lower())).strip()


def reconcile_report(as_of: date, companies: Table, deals: Table,
                     memberships: Table, contacts: Table | None = None,
                     inventory: Table | None = None, invoices: Table | None = None,
                     wms_companies: Table | None = None) -> dict[str, object]:
    """Reconcile CRM-side records (deals/contacts) against WMS-side records
    (memberships/inventory/invoices) sharing the canonical schema.

    Matching key is company_id. When a separate WMS company list is provided,
    companies are additionally matched by normalized name; name matches are
    PROBABLE (confidence 0.8) and are queued for human review - records are
    never merged by this function.
    """
    findings: list[dict[str, object]] = []
    review_queue: list[dict[str, object]] = []
    skipped: list[str] = []

    crm_companies = {r.get("company_id", "").strip(): r for r in companies.rows
                     if r.get("company_id", "").strip()}

    # Company matching across systems (only when a second list exists).
    exact = probable = 0
    if wms_companies is not None:
        wms_by_id = {r.get("company_id", "").strip(): r for r in wms_companies.rows}
        by_name = {_norm_name(r.get("name", "")): cid for cid, r in wms_by_id.items()}
        for cid, r in crm_companies.items():
            if cid in wms_by_id:
                exact += 1
                crm_n, wms_n = _norm_name(r.get("name", "")), _norm_name(
                    wms_by_id[cid].get("name", ""))
                if crm_n and wms_n and crm_n != wms_n:
                    findings.append({"check": "conflicting_company_names", "company_id": cid,
                                     "crm_name": r.get("name", ""),
                                     "wms_name": wms_by_id[cid].get("name", ""),
                                     "detail": "Same ID, different names; fix at the source."})
            elif _norm_name(r.get("name", "")) in by_name:
                probable += 1
                review_queue.append({
                    "type": "probable_company_match", "confidence": 0.8,
                    "crm_company_id": cid,
                    "wms_company_id": by_name[_norm_name(r.get("name", ""))],
                    "basis": "normalized name equality; IDs differ",
                    "action": "Human decision required - records are NOT merged."})
    else:
        skipped.append("cross-system company name matching (needs --wms-companies)")

    # Deals vs memberships, per company.
    won_by_company: dict[str, list[Row]] = {}
    for r in deals.rows:
        cid = r.get("company_id", "").strip()
        if cid and r.get("stage", "").strip().lower() == "won":
            won_by_company.setdefault(cid, []).append(r)
    mem_by_company: dict[str, list[Row]] = {}
    for r in memberships.rows:
        cid = r.get("company_id", "").strip()
        if cid and r.get("status", "").strip().lower() in {"active", "pending"}:
            mem_by_company.setdefault(cid, []).append(r)

    missing_membership = sorted(set(won_by_company) - set(mem_by_company))
    if missing_membership:
        exposure = ZERO
        for cid in missing_membership:
            for d in won_by_company[cid]:
                exposure += _money(d.get("expected_value", "")) or ZERO
        findings.append({"check": "won_deals_without_membership",
                         "count": len(missing_membership), "ids": missing_membership,
                         "monthly_exposure": str(exposure),
                         "detail": "CRM says sold; WMS has no active/pending membership."})
    missing_deal = sorted(set(mem_by_company) - set(won_by_company))
    if missing_deal:
        mrr = ZERO
        for cid in missing_deal:
            for m in mem_by_company[cid]:
                if not _truthy(m.get("complimentary", "")):
                    mrr += _money(m.get("contracted_rate", "")) or ZERO
        findings.append({"check": "memberships_without_won_deal",
                         "count": len(missing_deal), "ids": missing_deal,
                         "monthly_recurring": str(mrr),
                         "detail": "WMS bills these companies; CRM never recorded a won "
                                   "deal - history, migration gap, or untracked sale."})

    # Per-company value/product/location/date conflicts (one-to-many aware:
    # a company with several memberships is compared in aggregate, never
    # flattened to a single row).
    for cid in sorted(set(won_by_company) & set(mem_by_company)):
        deal_value = sum((_money(d.get("expected_value", "")) or ZERO
                          for d in won_by_company[cid]), ZERO)
        mem_value = sum((_money(m.get("contracted_rate", "")) or ZERO
                         for m in mem_by_company[cid]
                         if not _truthy(m.get("complimentary", ""))), ZERO)
        if deal_value > 0 and mem_value > 0:
            delta = abs(deal_value - mem_value)
            if delta / max(deal_value, mem_value) > Decimal("0.10"):
                findings.append({"check": "conflicting_contract_values", "company_id": cid,
                                 "crm_monthly": str(deal_value), "wms_monthly": str(mem_value),
                                 "detail": "CRM and WMS monthly values differ by >10%; "
                                           "one system is wrong or an upsell/discount went "
                                           "unrecorded."})
        deal_products = {d.get("product", "").strip().lower() for d in won_by_company[cid]}
        mem_products = {m.get("product", "").strip().lower() for m in mem_by_company[cid]}
        if deal_products and mem_products and not deal_products & mem_products:
            findings.append({"check": "conflicting_product_types", "company_id": cid,
                             "crm_products": sorted(deal_products),
                             "wms_products": sorted(mem_products),
                             "detail": "No overlap between sold and billed products."})
        deal_locs = {d.get("location_id", "").strip() for d in won_by_company[cid]} - {""}
        mem_locs = {m.get("location_id", "").strip() for m in mem_by_company[cid]} - {""}
        if deal_locs and mem_locs and not deal_locs & mem_locs:
            findings.append({"check": "conflicting_locations", "company_id": cid,
                             "crm_locations": sorted(deal_locs),
                             "wms_locations": sorted(mem_locs),
                             "detail": "Sold at one location, billed at another."})
        for d in won_by_company[cid]:
            move_in = parse_date(d.get("expected_move_in", ""))
            if move_in is None:
                continue
            maybe_starts = [parse_date(m.get("start_date", "")) for m in mem_by_company[cid]]
            valid_starts: list[date] = [s for s in maybe_starts if s is not None]
            if valid_starts and min(abs((s - move_in).days) for s in valid_starts) > 14:
                findings.append({"check": "conflicting_start_dates", "company_id": cid,
                                 "deal_id": d.get("deal_id", "?"),
                                 "expected_move_in": move_in.isoformat(),
                                 "membership_starts": [s.isoformat() for s in valid_starts],
                                 "detail": "Expected move-in and membership start differ "
                                           "by more than 14 days."})

    # Structural cross-checks.
    if contacts is not None:
        seen: dict[str, str] = {}
        for r in contacts.rows:
            email = r.get("email", "").strip().lower()
            if email and email in seen:
                review_queue.append({"type": "duplicate_person", "confidence": 0.9,
                                     "contact_ids": [seen[email], r.get("contact_id", "?")],
                                     "basis": f"same email ({email})",
                                     "action": "Human merge decision; do not auto-merge."})
            elif email:
                seen[email] = r.get("contact_id", "?")
        orphans = [r.get("contact_id", "?") for r in contacts.rows
                   if not r.get("company_id", "").strip()]
        if orphans:
            findings.append({"check": "contacts_without_company", "count": len(orphans),
                             "ids": orphans[:25],
                             "detail": "No durable link to a paying entity."})
    else:
        skipped.append("duplicate people / orphan contacts (needs contacts)")

    if inventory is not None:
        active_units = {m.get("unit_id", "").strip() for rows in mem_by_company.values()
                        for m in rows if m.get("unit_id", "").strip()
                        and m.get("status", "").strip().lower() == "active"}
        known_units = {r.get("unit_id", "").strip() for r in inventory.rows}
        ghost_units = sorted(active_units - known_units)
        if ghost_units:
            findings.append({"check": "assignments_to_unknown_inventory",
                             "count": len(ghost_units), "ids": ghost_units,
                             "detail": "Memberships assigned to units the inventory "
                                       "export does not contain."})
    else:
        skipped.append("inventory assignment checks (needs inventory)")

    if invoices is not None:
        canceled_recent = [m for m in memberships.rows
                          if m.get("status", "").strip().lower() == "canceled"
                          and (e := parse_date(m.get("end_date", ""))) is not None
                          and (as_of - e).days <= 60]
        for m in canceled_recent:
            cid = m.get("company_id", "").strip()
            open_deals = [d for d in deals.rows
                          if d.get("company_id", "").strip() == cid
                          and d.get("stage", "").strip().lower() in OPEN_STAGES]
            if open_deals:
                findings.append({"check": "cancellation_not_reflected_in_crm",
                                 "company_id": cid,
                                 "membership_id": m.get("membership_id", "?"),
                                 "open_deal_ids": [d.get("deal_id", "?") for d in open_deals],
                                 "detail": "WMS shows a recent cancellation while CRM still "
                                           "carries open deals for the same company."})
    else:
        skipped.append("cancellation reflection check (needs invoices context)")

    return {
        "as_of": as_of.isoformat(),
        "match_summary": {
            "companies_in_crm": len(crm_companies),
            "companies_with_won_deals": len(won_by_company),
            "companies_with_active_memberships": len(mem_by_company),
            "exact_id_matches": exact if wms_companies is not None else None,
            "probable_name_matches": probable if wms_companies is not None else None,
        },
        "findings": findings,
        "review_queue": review_queue,
        "skipped_checks": skipped,
        "id_strategy": "Durable fix: one shared company_id (the WMS id is usually the "
                       "better anchor - it bills) stored as an external-ID field in the "
                       "CRM, plus contact email as the person-level key. Never rely on "
                       "name equality.",
        "methodology": "Company-ID equality is the only automatic match. Name matches "
                       "are probable (0.8) and human-reviewed. Aggregates compare "
                       "per-company sums so one-to-many relationships are not flattened. "
                       "Nothing is merged by this tool.",
    }


# --- Daily operator brief ----------------------------------------------------

ROLE_CLASSES = {
    "owner": {"renewals_due", "cancellations_upcoming", "failed_or_overdue_invoices",
              "unbilled_memberships", "out_of_service", "data_blockers",
              "new_leads_awaiting_response"},
    "community": {"move_ins", "cancellations_upcoming", "tours_upcoming",
                  "data_blockers"},
    "sales": {"new_leads_awaiting_response", "overdue_follow_ups", "tours_today",
              "tours_upcoming", "tours_without_next_action"},
    "finance": {"failed_or_overdue_invoices", "unbilled_memberships", "renewals_due"},
}


def daily_brief(as_of: date, role: str, leads: Table | None = None,
                deals: Table | None = None, tours: Table | None = None,
                memberships: Table | None = None, invoices: Table | None = None,
                inventory: Table | None = None) -> dict[str, object]:
    """Role-filtered action queue for one day. Every item carries why/owner/
    urgency/evidence/action; item classes with missing inputs are skipped
    and listed."""
    items: list[dict[str, object]] = []
    skipped: list[str] = []

    def add(cls: str, urgency: str, why: str, evidence: str, action: str,
            owner: str, confidence: str = "high") -> None:
        items.append({"class": cls, "urgency": urgency, "why": why,
                      "evidence": evidence, "action": action, "owner": owner,
                      "confidence": confidence})

    if leads is not None:
        for r in leads.rows:
            if (r.get("status", "").strip().lower() in {"", "new"}
                    and not r.get("first_response_at", "").strip()):
                created = parse_datetime(r.get("created_at", ""))
                age = f"{(as_of - created.date()).days}d old" if created else "age unknown"
                add("new_leads_awaiting_response", "today",
                    f"Uncontacted lead ({age}); response speed decides tours",
                    r.get("lead_id", "?"), "Make first human contact", "sales")
            nad = parse_date(r.get("next_action_date", ""))
            if nad and nad < as_of and r.get("status", "").strip().lower() not in {"won", "lost"}:
                add("overdue_follow_ups", f"{(as_of - nad).days}d overdue",
                    f"Promised action '{r.get('next_action', '?')}' not done",
                    r.get("lead_id", "?"), "Do or reschedule the action", "sales")
    else:
        skipped.append("lead items (needs leads)")

    if deals is not None:
        for r in deals.rows:
            nad = parse_date(r.get("next_action_date", ""))
            if (nad and nad < as_of
                    and r.get("stage", "").strip().lower() in OPEN_STAGES):
                add("overdue_follow_ups", f"{(as_of - nad).days}d overdue",
                    f"Deal action '{r.get('next_action', '?')}' overdue",
                    r.get("deal_id", "?"), "Complete the recorded next action", "sales")
    else:
        skipped.append("deal follow-ups (needs deals)")

    if tours is not None:
        for r in tours.rows:
            sched = parse_datetime(r.get("scheduled_at", ""))
            status = r.get("status", "").strip().lower()
            if sched and status == "scheduled":
                delta = (sched.date() - as_of).days
                if delta == 0:
                    add("tours_today", "today", "Tour happening today",
                        r.get("tour_id", "?"), "Run prep (coworking-tour-preparation)",
                        "sales")
                elif 0 < delta <= 2:
                    add("tours_upcoming", f"in {delta}d", "Tour within 2 days",
                        r.get("tour_id", "?"), "Confirm attendance + prep brief", "sales")
                elif delta < 0:
                    add("tours_without_next_action", f"{-delta}d stale",
                        "Tour still 'scheduled' in the past - outcome never recorded",
                        r.get("tour_id", "?"), "Record outcome; rebook or close", "sales",
                        confidence="medium")
            if status == "completed" and not r.get("next_action", "").strip():
                add("tours_without_next_action", "this week",
                    "Completed tour with no next step - prime ghost territory",
                    r.get("tour_id", "?"), "Set next action / follow up", "sales")
    else:
        skipped.append("tour items (needs tours)")

    if memberships is not None:
        for r in memberships.rows:
            status = r.get("status", "").strip().lower()
            start = parse_date(r.get("start_date", ""))
            end = parse_date(r.get("end_date", ""))
            renewal = parse_date(r.get("renewal_date", ""))
            mid = r.get("membership_id", "?")
            if status == "pending" and start and 0 <= (start - as_of).days <= 7:
                add("move_ins", f"in {(start - as_of).days}d",
                    "Move-in this week; onboarding tasks must be done before day one",
                    mid, "Run onboarding checklist", "community")
            if status == "active" and end and 0 <= (end - as_of).days <= 30:
                add("cancellations_upcoming", f"in {(end - as_of).days}d",
                    "Agreement ends within 30 days",
                    mid, "Exit/retention conversation + re-listing plan", "community")
            if status == "active" and renewal and 0 <= (renewal - as_of).days <= 60:
                add("renewals_due", f"in {(renewal - as_of).days}d",
                    "Renewal inside 60 days",
                    mid, "Prepare renewal brief", "owner")
            if status == "active" and end and end < as_of:
                add("data_blockers", "now",
                    "Marked active but past its end date - corrupts every report",
                    mid, "Fix status or record the renewal", "owner")
    else:
        skipped.append("membership items (needs memberships)")

    if invoices is not None:
        for r in invoices.rows:
            if r.get("status", "").strip().lower() in {"failed", "overdue"}:
                due = parse_date(r.get("due_date", ""))
                days = f"{(as_of - due).days}d overdue" if due else "overdue"
                add("failed_or_overdue_invoices", days,
                    f"{r.get('status')} invoice for {r.get('amount', '?')}",
                    r.get("invoice_id", "?"), "Collections queue (verify, then contact)",
                    "finance")
    else:
        skipped.append("invoice items (needs invoices)")

    if inventory is not None:
        for r in inventory.rows:
            if _truthy(r.get("out_of_service", "")):
                price = r.get("list_price", "") or "unpriced"
                add("out_of_service", "review weekly",
                    f"Unit out of service ({price}/mo list idle)",
                    r.get("unit_id", "?"), "Confirm repair date or re-list", "owner",
                    confidence="medium")
    else:
        skipped.append("inventory items (needs inventory)")

    role_key = role.lower()
    if role_key not in ROLE_CLASSES:
        role_key = "owner"
    allowed = ROLE_CLASSES[role_key]
    filtered = [i for i in items if i["class"] in allowed]
    order = {"today": 0, "now": 0}
    filtered.sort(key=lambda i: (order.get(str(i["urgency"]), 1), str(i["class"])))
    return {"as_of": as_of.isoformat(), "role": role_key,
            "items": filtered, "item_count": len(filtered),
            "all_classes_present": sorted({str(i["class"]) for i in items}),
            "skipped_classes": skipped,
            "note": "Queue built from provided exports only; anything living outside "
                    "these files (email threads, verbal promises) is invisible here."}


# --- Occupancy forecast ------------------------------------------------------

def occupancy_forecast(inventory: Table, memberships: Table, as_of: date,
                       horizons: tuple[int, ...] = (30, 60, 90, 180)) -> dict[str, object]:
    """CONTRACTED-ONLY forward occupancy: active agreements minus known ends,
    plus signed pending move-ins. No probabilities, no pipeline - the skill
    layers scenarios on top with disclosed assumptions."""
    pool = ZERO
    unit_caps: dict[str, int] = {}
    for r in inventory.rows:
        if _truthy(r.get("sellable", "true") or "true") and not _truthy(
                r.get("out_of_service", "")):
            try:
                cap = int(r.get("capacity", "") or 0)
            except ValueError:
                cap = 0
            unit_caps[r.get("unit_id", "").strip()] = cap
            pool += cap

    results = []
    for days in horizons:
        h = as_of + timedelta(days=days)
        occupied = ZERO
        arrivals: list[str] = []
        departures: list[str] = []
        for m in memberships.rows:
            status = m.get("status", "").strip().lower()
            start = parse_date(m.get("start_date", ""))
            end = parse_date(m.get("end_date", ""))
            unit = m.get("unit_id", "").strip()
            ucap = unit_caps.get(unit)
            if ucap is None:  # floating/VO/unknown units don't consume unit capacity
                continue
            active_at_h = (status in {"active", "pending"} and start is not None
                           and start <= h and (end is None or end >= h))
            if active_at_h:
                occupied += ucap
                if status == "pending" or (start and start > as_of):
                    arrivals.append(m.get("membership_id", "?"))
            elif (status == "active" and start is not None and start <= as_of
                  and end is not None and as_of <= end < h):
                departures.append(m.get("membership_id", "?"))
        pct = None if pool == 0 else str((occupied / pool).quantize(Decimal("0.0001")))
        results.append({"horizon_days": days, "date": h.isoformat(),
                        "contracted_occupied_capacity": str(occupied),
                        "sellable_capacity": str(pool),
                        "contracted_occupancy": pct,
                        "arrivals": arrivals, "departures": departures})
    return {
        "as_of": as_of.isoformat(), "horizons": results,
        "assumptions": [
            "Contracted layer only: active agreements minus recorded end dates, plus "
            "signed pending move-ins. No renewal probability is applied - agreements "
            "with no end date are assumed to continue.",
            "Sellable capacity held constant; out-of-service units assumed to stay "
            "out of service (update the inventory to change this).",
            "Floating/hot-desk/virtual memberships without unit assignments are "
            "excluded from unit-capacity occupancy.",
            "No pipeline or probabilistic layer is included here; scenario layers "
            "must state their own assumptions."],
    }


# --- Renewal / expansion scan ------------------------------------------------

def renewal_scan(memberships: Table, as_of: date, invoices: Table | None = None,
                 window_days: int = 90) -> dict[str, object]:
    """Portfolio scan of agreements reaching renewal/end inside the window,
    with per-agreement evidence lists (never a numeric score)."""
    horizon = as_of + timedelta(days=window_days)
    payment_flags: dict[str, list[str]] = {}
    if invoices is not None:
        for r in invoices.rows:
            if r.get("status", "").strip().lower() in {"failed", "overdue"}:
                payment_flags.setdefault(r.get("membership_id", "").strip(), []).append(
                    f"{r.get('invoice_id', '?')} {r.get('status')}")

    by_company: dict[str, int] = {}
    for m in memberships.rows:
        if m.get("status", "").strip().lower() == "active":
            by_company[m.get("company_id", "").strip()] = \
                by_company.get(m.get("company_id", "").strip(), 0) + 1

    in_window: list[dict[str, object]] = []
    month_to_month: list[str] = []
    for m in memberships.rows:
        if m.get("status", "").strip().lower() != "active":
            continue
        mid = m.get("membership_id", "?")
        end = parse_date(m.get("end_date", ""))
        renewal = parse_date(m.get("renewal_date", ""))
        cliff = min((d for d in (end, renewal) if d is not None), default=None)
        if cliff is None:
            if not (m.get("term_months", "") or "").strip():
                month_to_month.append(mid)
            continue
        if not (as_of <= cliff <= horizon):
            continue
        contracted = _money(m.get("contracted_rate", ""))
        list_rate = _money(m.get("list_rate", ""))
        evidence: list[str] = []
        if m.get("notice_date", "").strip():
            evidence.append(f"notice already given ({m.get('notice_date')})")
        if contracted is not None and list_rate is not None and list_rate > 0 \
                and contracted < list_rate:
            jump = ((list_rate - contracted) / list_rate * 100).quantize(Decimal("0.1"))
            evidence.append(f"renewal-to-list jump would be {jump}% "
                            "(renewal-shock risk)")
        for flag in payment_flags.get(mid.strip(), []):
            evidence.append(f"payment friction: {flag}")
        if by_company.get(m.get("company_id", "").strip(), 0) > 1:
            evidence.append("company holds multiple active memberships "
                            "(expansion relationship - handle as one account)")
        in_window.append({
            "membership_id": mid, "company_id": m.get("company_id", "?"),
            "cliff_date": cliff.isoformat(),
            "days_to_cliff": (cliff - as_of).days,
            "contracted_rate": None if contracted is None else str(contracted),
            "list_rate": None if list_rate is None else str(list_rate),
            "risk_evidence": evidence,
            "next_step": "coworking-renewal-preparation brief" if evidence
            else "standard renewal confirmation"})
    in_window.sort(key=lambda i: int(str(i["days_to_cliff"])))
    return {"as_of": as_of.isoformat(), "window_days": window_days,
            "agreements_in_window": in_window,
            "month_to_month_active": month_to_month,
            "caveats": [
                "Usage, support history, and team-size changes are not in these "
                "exports; evidence lists cover only dates, pricing, payments, and "
                "multi-membership structure.",
                "Month-to-month agreements have a permanent renewal cliff and are "
                "listed separately, not force-ranked."],
            "no_score_note": "Deliberately no numeric risk score: evidence lists "
                             "only, per the explainability rule."}


# --- Discount / pricing audit ------------------------------------------------

def pricing_audit(inventory: Table, memberships: Table, as_of: date,
                  deep_discount_pct: int = 25) -> dict[str, object]:
    """Discount dependence and yield per product x location (sellable,
    in-service units only). Makes no market-price claims."""
    units, _ = build_units(inventory, memberships, as_of)
    unit_meta = {r.get("unit_id", "").strip():
                 (r.get("location_id", "").strip(), r.get("unit_type", "").strip().lower())
                 for r in inventory.rows}
    cuts: dict[tuple[str, str], dict[str, Decimal | int]] = {}
    deep: list[dict[str, object]] = []
    for u in units:
        if not u.sellable or u.out_of_service:
            continue
        loc, utype = unit_meta.get(u.unit_id, ("?", u.unit_type))
        c = cuts.setdefault((loc, utype), {
            "units": 0, "occupied": 0, "capacity": 0, "mrr": ZERO,
            "list_total": ZERO, "discount_value": ZERO})
        c["units"] += 1
        c["capacity"] += u.capacity
        if u.occupied:
            c["occupied"] += 1
            c["mrr"] += u.contracted_revenue
        if u.list_price is not None:
            c["list_total"] += u.list_price
            if u.occupied and not u.complimentary:
                gap = u.list_price - u.contracted_revenue
                if gap > 0:
                    c["discount_value"] += gap
                    pct = (gap / u.list_price * 100).quantize(Decimal("0.1"))
                    if pct >= deep_discount_pct:
                        deep.append({"unit_id": u.unit_id, "location_id": loc,
                                     "product": utype,
                                     "contracted": str(u.contracted_revenue),
                                     "list": str(u.list_price),
                                     "discount_pct": str(pct)})
    table = []
    for (loc, utype), c in sorted(cuts.items()):
        cap = int(c["capacity"])
        mrr = Decimal(c["mrr"])
        discount_value = Decimal(c["discount_value"])
        rev_per_ws = None if cap == 0 else str((mrr / cap).quantize(Decimal("0.01")))
        disc_share = None
        denom = mrr + discount_value
        if denom > 0:
            disc_share = str((discount_value / denom * 100).quantize(Decimal("0.1")))
        table.append({
            "location_id": loc, "product": utype,
            "units": int(c["units"]), "occupied_units": int(c["occupied"]),
            "capacity": cap, "monthly_recurring": str(c["mrr"]),
            "revenue_per_workstation": rev_per_ws,
            "mrr_weighted_discount_pct": disc_share,
            "definition": "revenue_per_workstation = contracted MRR of the cut / total "
                          "sellable in-service capacity of the cut (vacant units drag "
                          "the number down by design); discount % = forgone list value "
                          "/ (MRR + forgone), MRR-weighted, occupied priced units only"})
    return {"as_of": as_of.isoformat(), "cuts": table,
            "deep_discounts": deep,
            "caveats": [
                "Promotional expiry dates are not modeled in the schema; discount "
                "duration requires the operator's promo records.",
                f"Deep-discount threshold: {deep_discount_pct}% (configurable).",
                "No market-price comparison is made - that requires credible market "
                "evidence this tool does not have. Repricing decisions are human."]}


# --- Collections queue -------------------------------------------------------

def collections_queue(invoices: Table, as_of: date, payments: Table | None = None,
                      memberships: Table | None = None) -> dict[str, object]:
    """Humane, prioritized INTERNAL worklist for failed/overdue invoices.
    Sends nothing; concludes nothing legal."""
    history: dict[str, dict[str, int]] = {}
    for r in invoices.rows:
        cid = r.get("company_id", "").strip()
        h = history.setdefault(cid, {"paid": 0, "problem": 0})
        status = r.get("status", "").strip().lower()
        if status == "paid":
            h["paid"] += 1
        elif status in {"failed", "overdue"}:
            h["problem"] += 1

    mem_context: dict[str, list[str]] = {}
    if memberships is not None:
        for m in memberships.rows:
            cid = m.get("company_id", "").strip()
            notes = []
            end = parse_date(m.get("end_date", ""))
            renewal = parse_date(m.get("renewal_date", ""))
            if m.get("status", "").strip().lower() == "active":
                if end and 0 <= (end - as_of).days <= 60:
                    notes.append(f"agreement ends {end.isoformat()}")
                if renewal and 0 <= (renewal - as_of).days <= 60:
                    notes.append(f"renewal {renewal.isoformat()} - resolve billing "
                                 "BEFORE renewal pricing talk")
                dep = _money(m.get("deposit", ""))
                if dep and dep > 0:
                    notes.append(f"deposit held {dep}")
            if notes:
                mem_context.setdefault(cid, []).extend(notes)

    keyed: list[tuple[int, Decimal, dict[str, object]]] = []
    for r in invoices.rows:
        if r.get("status", "").strip().lower() not in {"failed", "overdue"}:
            continue
        due = parse_date(r.get("due_date", ""))
        days: int | None = (as_of - due).days if due else None
        band = ("0-15" if days is not None and days <= 15 else
                "16-30" if days is not None and days <= 30 else
                "31+" if days is not None else "unknown")
        cid = r.get("company_id", "").strip()
        h = history.get(cid, {"paid": 0, "problem": 0})
        first_problem = h["paid"] > 0 and h["problem"] == 1
        approach = {
            "0-15": "Verify the payment method actually failed (card expiry is the "
                    "usual cause), then a friendly heads-up from the CM",
            "16-30": "Personal contact from someone the member knows; ask, don't dun",
            "31+": "Owner/GM conversation; agree a plan in writing",
            "unknown": "Fix the missing due date first",
        }[band]
        if first_problem:
            approach = "First-ever issue from a good payer - assume card expiry, " \
                       "lead with helpfulness. " + approach
        amount = _money(r.get("amount", "")) or ZERO
        keyed.append((days or 0, amount, {
            "invoice_id": r.get("invoice_id", "?"), "company_id": cid,
            "amount": r.get("amount", "?"), "status": r.get("status", ""),
            "days_overdue": days, "aging_band": band,
            "payment_history": f"{h['paid']} paid / {h['problem']} problem in export",
            "context": mem_context.get(cid, []),
            "suggested_internal_step": approach}))
    keyed.sort(key=lambda kv: (-kv[0], -kv[1]))
    queue = [item for _, _, item in keyed]
    total = sum((amt for _, amt, _ in keyed), ZERO)
    return {"as_of": as_of.isoformat(), "queue": queue,
            "outstanding_total": str(total),
            "rules": ["Internal worklist only: this tool sends nothing.",
                      "No legal conclusions; escalation beyond conversation is a "
                      "human + professional-advice decision.",
                      "History counts come from the provided export only."]}


# --- Meeting / event yield ---------------------------------------------------

_EXCLUDED_BOOKING_STATUS = {"cancelled", "canceled", "no_show", "noshow"}


def _excluded_booking(row: Row, columns: set[str]) -> bool:
    """True only when the export itself says the booking did not happen.

    A blank status is not a no-show. Booked hours stay inclusive unless a
    status, no_show, or cancellation column identifies the row.
    """
    if "status" in columns:
        status = row.get("status", "").strip().lower().replace(" ", "_").replace("-", "_")
        if status in _EXCLUDED_BOOKING_STATUS:
            return True
    for col in ("no_show", "cancelled", "canceled"):
        if col in columns and _truthy(row.get(col, "")):
            return True
    return False


def _daypart(hour: int) -> str:
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    return "evening"


def room_yield(bookings: Table, inventory: Table,
               daily_open_hours: Decimal | None = None) -> dict[str, object]:
    """Per-room booked hours, revenue, and mix. Utilization only when the
    operator declares daily bookable hours; otherwise honestly omitted.

    Cancelled bookings and no-shows are excluded from booked hours only when
    the export carries a status or flag column that says so. Costs and setup
    time are reported only when those columns exist, and a partial cost column
    does not become a contribution margin.
    """
    from dataclasses import dataclass
    from dataclasses import field as _field

    @dataclass
    class _RoomAgg:
        unit_type: str
        bookings: int = 0
        booked_hours: Decimal = _field(default_factory=lambda: ZERO)
        revenue: Decimal = _field(default_factory=lambda: ZERO)
        member_bookings: int = 0
        nonmember_bookings: int = 0
        zero_charge_bookings: int = 0
        excluded_bookings: int = 0
        setup_minutes: Decimal = _field(default_factory=lambda: ZERO)
        supplied_cost: Decimal = _field(default_factory=lambda: ZERO)
        cost_rows: int = 0

    columns = set(bookings.columns)
    has_status = bool(columns & {"status", "no_show", "cancelled", "canceled"})
    has_setup = "setup_minutes" in columns
    has_cost = "cost" in columns
    room_types = {r.get("unit_id", "").strip(): r.get("unit_type", "").strip().lower()
                  for r in inventory.rows}
    per_room: dict[str, _RoomAgg] = {}
    dates: list[date] = []
    dayparts = {"morning": 0, "afternoon": 0, "evening": 0}
    unparseable = 0
    excluded_total = 0
    for b in bookings.rows:
        start = parse_datetime(b.get("start_at", ""))
        end = parse_datetime(b.get("end_at", ""))
        if start is None or end is None or end <= start:
            unparseable += 1
            continue
        rid = b.get("room_unit_id", "").strip()
        room = per_room.setdefault(rid, _RoomAgg(room_types.get(rid, "unknown")))
        if _excluded_booking(b, columns):
            room.excluded_bookings += 1
            excluded_total += 1
            continue
        dates.append(start.date())
        hours = Decimal(int((end - start).total_seconds())) / 3600
        amount = _money(b.get("amount", "")) or ZERO
        member = _truthy(b.get("member_booking", ""))
        room.bookings += 1
        room.booked_hours += hours
        room.revenue += amount
        dayparts[_daypart(start.hour)] += 1
        if member:
            room.member_bookings += 1
        else:
            room.nonmember_bookings += 1
        if amount == 0:
            room.zero_charge_bookings += 1
        if has_setup:
            raw_setup = b.get("setup_minutes", "").strip()
            if raw_setup:
                try:
                    room.setup_minutes += Decimal(raw_setup)
                except ArithmeticError:
                    pass
        if has_cost:
            parsed_cost = _money(b.get("cost", ""))
            if parsed_cost is not None:
                room.supplied_cost += parsed_cost
                room.cost_rows += 1
    period = (min(dates).isoformat(), max(dates).isoformat()) if dates else (None, None)
    span_days = (max(dates) - min(dates)).days + 1 if dates else 0
    rooms_out = []
    honored = sum(dayparts.values())
    for rid, agg in sorted(per_room.items()):
        booked = agg.booked_hours
        out: dict[str, object] = {
            "room": rid, "unit_type": agg.unit_type, "bookings": agg.bookings,
            "booked_hours": str(booked),
            "gross_revenue": str(agg.revenue),
            "revenue_per_booked_hour": (str((agg.revenue / booked).quantize(Decimal("0.01")))
                                        if booked > 0 else None),
            "member_bookings": agg.member_bookings,
            "nonmember_bookings": agg.nonmember_bookings,
            "zero_charge_bookings": agg.zero_charge_bookings,
            "excluded_bookings": agg.excluded_bookings,
        }
        if has_setup:
            out["setup_hours"] = str((agg.setup_minutes / 60).quantize(Decimal("0.01")))
        if daily_open_hours is not None and span_days > 0:
            bookable = daily_open_hours * span_days
            out["bookable_hours_assumed"] = str(bookable)
            out["utilization"] = str((booked / bookable).quantize(Decimal("0.0001")))
            if bookable > 0:
                out["revenue_per_available_hour"] = str(
                    (agg.revenue / bookable).quantize(Decimal("0.01")))
        if has_cost:
            if agg.cost_rows == agg.bookings and agg.bookings > 0:
                out["operator_supplied_cost"] = str(agg.supplied_cost)
                out["contribution"] = str(agg.revenue - agg.supplied_cost)
            else:
                out["contribution"] = None
                out["contribution_note"] = (
                    "Cost column was partial or blank; contribution margin was not "
                    "computed. Missing costs are unknown, not zero.")
        rooms_out.append(out)
    result: dict[str, object] = {
        "observed_period": {"from": period[0], "to": period[1], "days": span_days},
        "rooms": rooms_out,
        "excluded_bookings": excluded_total,
        "unparseable_bookings": unparseable,
        "dayparts": {
            **dayparts,
            "bookings_counted": honored,
            "pattern_claim_allowed": honored >= 20,
            "basis": "honored bookings with a parseable start; morning <12, "
                     "afternoon <17, evening otherwise, in the timestamp's own clock",
        },
        "definitions": [
            "booked_hours = sum(end-start) of parseable bookings that were not "
            "identified as cancelled or no-show",
            "booked is not used: the export does not record attendance",
            "zero_charge bookings include member-plan-included AND comped bookings - "
            "the export cannot distinguish them unless a cost or charge-type column "
            "is present; label accordingly",
            "revenue_per_booked_hour = gross revenue / booked hours (per room)",
            "revenue_per_available_hour = gross revenue / declared bookable hours, "
            "and only when bookable hours were declared",
            "setup_hours are reported beside booked hours and are not added to them",
        ],
    }
    if has_status:
        result["booking_status_note"] = (
            f"{excluded_total} booking(s) were excluded from booked hours because a "
            "status, no_show, or cancellation column marked them cancelled or no-show. "
            "Rows with a blank status stayed in booked hours.")
    else:
        result["booking_status_note"] = (
            "No status, no_show, or cancelled column was present. Cancelled bookings "
            "and no-shows could not be separated, so every parseable booking is in "
            "booked hours. Booked is not the same as used.")
    if daily_open_hours is None:
        result["utilization_note"] = ("Utilization omitted: no bookable hours declared. "
                                      "Pass --open-hours-per-day to compute it; booked "
                                      "hours alone are reported instead.")
    else:
        result["utilization_note"] = (f"Utilization assumes {daily_open_hours} bookable "
                                      "hours every day of the observed period, including "
                                      "weekends - adjust if your rooms close. "
                                      "revenue_per_available_hour uses that same denominator.")
    if not has_cost:
        result["contribution_note"] = (
            "No cost column was supplied. Contribution margin was not computed. "
            "Do not treat gross revenue as profit.")
    return result


# --- Multi-location benchmark ------------------------------------------------

def location_benchmark(as_of: date, locations: Table, inventory: Table,
                       memberships: Table, leads: Table | None = None,
                       tours: Table | None = None,
                       invoices: Table | None = None) -> dict[str, object]:
    """Per-location scorecard normalized per sellable workstation so small
    locations compare fairly with big ones."""
    rows_out = []
    for loc in locations.rows:
        lid = loc.get("location_id", "").strip()
        units, issues = build_units(inventory, memberships, as_of, location_id=lid)
        pool_units = [u for u in units if u.sellable and not u.out_of_service]
        cap = sum(u.capacity for u in pool_units)
        occ_cap = sum(u.capacity for u in pool_units if u.occupied)
        mrr = sum((u.contracted_revenue for u in pool_units if u.occupied), ZERO)
        priced = [u for u in pool_units if u.list_price is not None]
        list_total = sum((u.list_price or ZERO for u in priced), ZERO)
        fin = (sum((u.contracted_revenue for u in priced if u.occupied), ZERO)
               / list_total) if list_total > 0 else None
        entry: dict[str, object] = {
            "location_id": lid, "name": loc.get("name", "?"),
            "sellable_capacity": cap,
            "workstation_occupancy": (str((Decimal(occ_cap) / cap).quantize(Decimal("0.0001")))
                                      if cap else None),
            "financial_occupancy": None if fin is None else str(fin.quantize(Decimal("0.0001"))),
            "monthly_recurring": str(mrr),
            "revenue_per_sellable_workstation": (str((mrr / cap).quantize(Decimal("0.01")))
                                                 if cap else None),
            "referential_issue_count": len(issues),
        }
        if leads is not None:
            loc_leads = [r for r in leads.rows if r.get("location_id", "").strip() == lid]
            entry["leads"] = len(loc_leads)
            entry["leads_per_10_workstations"] = (
                str((Decimal(len(loc_leads)) * 10 / cap).quantize(Decimal("0.1")))
                if cap else None)
            if tours is not None:
                lead_ids = {r.get("lead_id", "").strip() for r in loc_leads}
                toured = {r.get("lead_id", "").strip() for r in tours.rows
                          if r.get("lead_id", "").strip() in lead_ids}
                entry["lead_to_tour"] = (str(round(len(toured) / len(loc_leads), 4))
                                         if loc_leads else None)
        if invoices is not None and memberships is not None:
            loc_members = {m.get("company_id", "").strip() for m in memberships.rows
                           if m.get("location_id", "").strip() == lid}
            problems = [r for r in invoices.rows
                        if r.get("company_id", "").strip() in loc_members
                        and r.get("status", "").strip().lower() in {"failed", "overdue"}]
            entry["failed_or_overdue_invoices"] = len(problems)
        rows_out.append(entry)
    return {"as_of": as_of.isoformat(), "locations": rows_out,
            "normalization": "Occupancies are ratios; revenue and lead volume are "
                             "normalized per sellable workstation (x10 for leads) so "
                             "location size does not masquerade as performance.",
            "caveats": [
                "Product mix differs between locations; compare like cuts before "
                "concluding (see pricing_audit per product).",
                "Invoice attribution is company-based; multi-location companies "
                "blur per-location collections.",
                "Data availability differs per location; missing fields lower "
                "confidence, not performance."]}
