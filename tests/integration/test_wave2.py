"""Wave 2 engine tests against both synthetic businesses.

Expected values were computed by hand from the literal CSV rows before the
wave2 module ran on them (documented per-test), continuing the audit's
independent-source-of-truth discipline.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

from opencoworking.ingest import Table, load_csv
from opencoworking.wave2 import (
    collections_queue,
    daily_brief,
    location_benchmark,
    occupancy_forecast,
    pricing_audit,
    reconcile_report,
    renewal_scan,
    room_yield,
)

REPO = Path(__file__).resolve().parents[2]
NORTH = REPO / "examples" / "synthetic-space" / "data"
HARBOR = REPO / "examples" / "harbor-works" / "data"
AS_OF = date(2026, 7, 1)


def t(name, base=NORTH):
    return load_csv(base / f"{name}.csv")


class TestForecast:
    def test_northstar_horizons_hand_computed(self):
        # Hand math: pool 66. Occupied now 38. M-018 (pending, DD-102 cap 1)
        # starts 7/15 -> +1 from H30. M-005 (ST-201 cap 10) ends 8/31 ->
        # gone at H90 (9/29). Expect 39,39,29,29.
        r = occupancy_forecast(t("inventory"), t("memberships"), AS_OF)
        got = [(h["horizon_days"], h["contracted_occupied_capacity"],
                h["contracted_occupancy"]) for h in r["horizons"]]
        assert got == [(30, "39", "0.5909"), (60, "39", "0.5909"),
                       (90, "29", "0.4394"), (180, "29", "0.4394")]
        h30 = r["horizons"][0]
        h90 = r["horizons"][2]
        assert h30["arrivals"] == ["M-018"]
        assert h90["departures"] == ["M-005"]
        assert any("Contracted layer only" in a for a in r["assumptions"])

    def test_harbor_departure_at_180_only(self):
        # HWM-03 (PDX-S1 cap 8) ends 9/30: still active at H90 (9/29),
        # departed at H180 (12/28). Occupied now 35 -> 27 at 180.
        r = occupancy_forecast(t("inventory", HARBOR), t("memberships", HARBOR), AS_OF)
        by_days = {h["horizon_days"]: h for h in r["horizons"]}
        assert by_days[90]["contracted_occupied_capacity"] == "35"
        assert by_days[180]["contracted_occupied_capacity"] == "27"
        assert by_days[180]["departures"] == ["HWM-03"]


class TestCollections:
    def test_northstar_queue_hand_computed(self):
        # INV-1004 (2000) and INV-1006 (350), both due 6/15 -> 16d overdue,
        # band 16-30; same age -> larger amount first. Total 2350.
        r = collections_queue(t("invoices"), AS_OF, memberships=t("memberships"))
        ids = [(q["invoice_id"], q["days_overdue"], q["aging_band"]) for q in r["queue"]]
        assert ids == [("INV-1004", 16, "16-30"), ("INV-1006", 16, "16-30")]
        assert r["outstanding_total"] == "2350"
        delta = r["queue"][0]
        # C-DELTA renewal 8/1 within 60d -> billing-before-renewal context.
        assert any("renewal" in c for c in delta["context"])
        assert "sends nothing" in r["rules"][0]

    def test_first_problem_from_good_payer_tone(self):
        inv = Table("x", ["invoice_id", "company_id", "membership_id", "issue_date",
                          "due_date", "amount", "status"],
                    [{"invoice_id": "I-1", "company_id": "C-1", "membership_id": "M-1",
                      "issue_date": "2026-05-01", "due_date": "2026-05-15",
                      "amount": "500", "status": "paid"},
                     {"invoice_id": "I-2", "company_id": "C-1", "membership_id": "M-1",
                      "issue_date": "2026-06-01", "due_date": "2026-06-15",
                      "amount": "500", "status": "failed"}])
        r = collections_queue(inv, AS_OF)
        assert "First-ever issue" in r["queue"][0]["suggested_internal_step"]


class TestRooms:
    def test_northstar_yield_hand_computed(self):
        # MR-1: 2+2+1=5h rev 0; MR-2: 2+2+8=12h rev 60+180+540=780 (65/h);
        # EV-1: 4h rev 900 (225/h); MR-3: 1h rev 0.
        r = room_yield(t("room-bookings"), t("inventory"))
        by_room = {x["room"]: x for x in r["rooms"]}
        assert by_room["MR-2"]["booked_hours"] == "12"
        assert by_room["MR-2"]["gross_revenue"] == "780"
        assert by_room["MR-2"]["revenue_per_booked_hour"] == "65.00"
        assert by_room["EV-1"]["revenue_per_booked_hour"] == "225.00"
        assert by_room["MR-1"]["member_bookings"] == 3
        assert by_room["MR-2"]["nonmember_bookings"] == 2
        assert "utilization" not in by_room["MR-2"]
        assert "no bookable hours declared" in r["utilization_note"]

    def test_utilization_with_declared_hours(self):
        r = room_yield(t("room-bookings"), t("inventory"), Decimal("10"))
        by_room = {x["room"]: x for x in r["rooms"]}
        # Observed period 3 Jun..26 Jun = 24 days -> 240 bookable hours;
        # MR-2 booked 12h -> 0.05.
        assert r["observed_period"]["days"] == 24
        assert by_room["MR-2"]["bookable_hours_assumed"] == "240"
        assert by_room["MR-2"]["utilization"] == "0.0500"


class TestPricing:
    def test_northstar_office_cut_hand_computed(self):
        # LOC-NOR offices (sellable in-service): OF-101/102/103/105 ->
        # 4 units, 3 occupied, capacity 20, MRR 1300+2100+2000=5400,
        # rev/ws 270.00; discounts 100+0+800 over (5400+900)=14.3%.
        r = pricing_audit(t("inventory"), t("memberships"), AS_OF)
        cut = next(c for c in r["cuts"]
                   if c["location_id"] == "LOC-NOR" and c["product"] == "office")
        assert (cut["units"], cut["occupied_units"], cut["capacity"]) == (4, 3, 20)
        assert cut["monthly_recurring"] == "5400"
        assert cut["revenue_per_workstation"] == "270.00"
        assert cut["mrr_weighted_discount_pct"] == "14.3"
        assert [d["unit_id"] for d in r["deep_discounts"]] == ["OF-105"]
        assert any("No market-price comparison" in c for c in r["caveats"])

    def test_harbor_deep_discounts(self):
        r = pricing_audit(t("inventory", HARBOR), t("memberships", HARBOR), AS_OF)
        assert [d["unit_id"] for d in r["deep_discounts"]] == ["PDX-S1"]
        assert r["deep_discounts"][0]["discount_pct"] == "28.1"


class TestRenewalScan:
    def test_northstar_window_hand_computed(self):
        # Cliffs in [7/1, 9/29]: M-004/M-007/M-013 renewal 8/1 (31d),
        # M-005 end 8/31 (61d), M-001 renewal 9/1 (62d). Ordered by days.
        r = renewal_scan(t("memberships"), AS_OF, invoices=t("invoices"))
        got = [(a["membership_id"], a["days_to_cliff"]) for a in r["agreements_in_window"]]
        assert got == [("M-004", 31), ("M-007", 31), ("M-013", 31),
                       ("M-005", 61), ("M-001", 62)]
        by_id = {a["membership_id"]: a for a in r["agreements_in_window"]}
        assert any("payment friction" in e for e in by_id["M-004"]["risk_evidence"])
        assert any("notice already given" in e for e in by_id["M-005"]["risk_evidence"])
        assert any("multiple active memberships" in e for e in by_id["M-001"]["risk_evidence"])
        assert r["month_to_month_active"] == ["M-008"]
        assert "no numeric risk score" in r["no_score_note"].lower()


class TestBrief:
    def test_owner_brief_northstar_hand_computed(self):
        r = daily_brief(AS_OF, "owner", leads=t("leads"), deals=t("deals"),
                        tours=t("tours"), memberships=t("memberships"),
                        invoices=t("invoices"), inventory=t("inventory"))
        classes: dict[str, int] = {}
        for i in r["items"]:
            classes[i["class"]] = classes.get(i["class"], 0) + 1
        assert classes == {"new_leads_awaiting_response": 3, "renewals_due": 3,
                           "failed_or_overdue_invoices": 2, "out_of_service": 1,
                           "data_blockers": 1}
        assert all({"why", "owner", "urgency", "evidence", "action", "confidence"}
                   <= set(i) for i in r["items"])

    def test_sales_brief_excludes_finance_items(self):
        r = daily_brief(AS_OF, "sales", leads=t("leads"), deals=t("deals"),
                        tours=t("tours"), invoices=t("invoices"))
        assert all(i["class"] != "failed_or_overdue_invoices" for i in r["items"])
        # D-2007 overdue next action + lead-level overdues appear for sales.
        assert any(i["evidence"] == "D-2007" for i in r["items"])
        # Harbor-style stale scheduled tour class exists in northstar too? T-3006
        # is future (7/3): appears as upcoming, not stale.
        assert any(i["class"] == "tours_upcoming" and i["evidence"] == "T-3006"
                   for i in r["items"])

    def test_harbor_stale_scheduled_tour_flagged(self):
        r = daily_brief(AS_OF, "sales", tours=t("tours", HARBOR))
        stale = [i for i in r["items"] if i["class"] == "tours_without_next_action"]
        assert {i["evidence"] for i in stale} == {"HWT-02", "HWT-05"}


class TestReconcile:
    def test_harbor_cross_checks_hand_computed(self):
        r = reconcile_report(AS_OF, companies=t("companies", HARBOR),
                             deals=t("deals", HARBOR),
                             memberships=t("memberships", HARBOR),
                             contacts=t("contacts", HARBOR),
                             inventory=t("inventory", HARBOR),
                             invoices=t("invoices", HARBOR))
        checks = {}
        for f in r["findings"]:
            checks.setdefault(f["check"], []).append(f)
        assert checks["won_deals_without_membership"][0]["ids"] == ["HC-PORTAL"]
        # 13 membership companies minus 4 with won deals (ANCHOR, DELTA,
        # EMBER, FJORD) = 9 without CRM deals.
        assert checks["memberships_without_won_deal"][0]["count"] == 9
        # HC-ANCHOR: deal 1600 vs memberships 3300; HC-EMBER: 300 vs 600.
        value_conflicts = {f["company_id"] for f in checks["conflicting_contract_values"]}
        assert value_conflicts == {"HC-ANCHOR", "HC-EMBER"}
        assert checks["assignments_to_unknown_inventory"][0]["ids"] == ["PDX-D9"]
        dupes = [q for q in r["review_queue"] if q["type"] == "duplicate_person"]
        assert dupes and dupes[0]["contact_ids"] == ["HCT-01", "HCT-12"]
        assert "do not auto-merge" in dupes[0]["action"]

    def test_probable_name_match_never_merged(self):
        crm = Table("crm", ["company_id", "name"],
                    [{"company_id": "CRM-1", "name": "Anchor Analytics, Inc."}])
        wms = Table("wms", ["company_id", "name"],
                    [{"company_id": "WMS-9", "name": "Anchor Analytics LLC"}])
        empty = Table("e", ["deal_id", "company_id", "stage", "product",
                            "expected_value", "location_id", "expected_move_in"], [])
        mems = Table("m", ["membership_id", "company_id", "status", "product",
                           "contracted_rate", "location_id", "start_date",
                           "complimentary", "unit_id"], [])
        r = reconcile_report(AS_OF, companies=crm, deals=empty, memberships=mems,
                             wms_companies=wms)
        assert r["match_summary"]["probable_name_matches"] == 1
        q = r["review_queue"][0]
        assert q["type"] == "probable_company_match" and q["confidence"] == 0.8
        assert "NOT merged" in q["action"]


class TestBenchmark:
    def test_northstar_normalized_hand_computed(self):
        # NOR: cap 50, occupied 31 (0.62), MRR 9465, 189.30/ws, 17 leads,
        # 7 toured -> 0.4118. RIV: cap 16, occupied 7 (0.4375), MRR 2320,
        # 145.00/ws, 5 leads, 2 toured -> 0.4.
        r = location_benchmark(AS_OF, t("locations"), t("inventory"), t("memberships"),
                               leads=t("leads"), tours=t("tours"), invoices=t("invoices"))
        by_loc = {e["location_id"]: e for e in r["locations"]}
        nor, riv = by_loc["LOC-NOR"], by_loc["LOC-RIV"]
        assert (nor["sellable_capacity"], nor["workstation_occupancy"]) == (50, "0.6200")
        assert nor["revenue_per_sellable_workstation"] == "189.30"
        assert (nor["leads"], nor["lead_to_tour"]) == (17, "0.4118")
        assert (riv["sellable_capacity"], riv["workstation_occupancy"]) == (16, "0.4375")
        assert riv["revenue_per_sellable_workstation"] == "145.00"
        assert nor["failed_or_overdue_invoices"] == 2
        assert "per sellable workstation" in r["normalization"]

    def test_harbor_two_locations(self):
        r = location_benchmark(AS_OF, t("locations", HARBOR), t("inventory", HARBOR),
                               t("memberships", HARBOR))
        by_loc = {e["location_id"]: e for e in r["locations"]}
        # PDX pool 37 occupied 19 (O1 2 + O2 5 + S1 8 + D1-4 4);
        # BOS pool 20 occupied 16 (O1 4 + S1 12).
        assert by_loc["HW-PDX"]["workstation_occupancy"] == "0.5135"
        assert by_loc["HW-BOS"]["workstation_occupancy"] == "0.8000"


class TestMissingInputsDisclosed:
    def test_brief_skips_are_listed(self):
        r = daily_brief(AS_OF, "owner", invoices=t("invoices"))
        assert any("leads" in s for s in r["skipped_classes"])

    def test_reconcile_skips_name_matching_without_second_list(self):
        r = reconcile_report(AS_OF, companies=t("companies"), deals=t("deals"),
                             memberships=t("memberships"))
        assert any("wms-companies" in s for s in r["skipped_checks"])
        assert r["match_summary"]["exact_id_matches"] is None
