from datetime import date

from opencoworking.analyze import (
    build_units,
    funnel_report,
    inspect_table,
    leakage_report,
    occupancy_report,
    pipeline_report,
    source_report,
    speed_to_lead_report,
    vo_reconciliation,
)
from opencoworking.ingest import Table

AS_OF = date(2026, 7, 1)


def t(columns, rows):
    return Table(source="test", columns=columns,
                 rows=[dict(zip(columns, r, strict=True)) for r in rows])


INVENTORY = t(
    ["unit_id", "location_id", "unit_type", "capacity", "sellable",
     "out_of_service", "list_price"],
    [
        ["OF-1", "L1", "office", "4", "true", "false", "2000"],
        ["OF-2", "L1", "office", "6", "true", "false", "3000"],
        ["OF-3", "L1", "office", "2", "true", "true", "1200"],   # OOS
        ["DD-1", "L1", "desk", "1", "true", "false", "350"],
        ["DD-2", "L1", "desk", "1", "true", "false", ""],        # no list price
    ],
)

MEMBERSHIPS = t(
    ["membership_id", "company_id", "location_id", "product", "unit_id",
     "start_date", "end_date", "contracted_rate", "status", "complimentary"],
    [
        ["M-1", "C-1", "L1", "private-office", "OF-1", "2026-01-01", "", "1500", "active", ""],
        ["M-2", "C-2", "L1", "dedicated-desk", "DD-1", "2026-02-01", "", "350", "active", ""],
        ["M-3", "C-3", "L1", "community", "", "2026-03-01", "", "150", "active", ""],  # unassigned
        ["M-4", "C-4", "L1", "private-office", "OF-2", "2025-01-01", "2026-05-31", "2800", "active", ""],  # past end date, "active"
        ["M-5", "C-5", "L1", "dedicated-desk", "DD-9", "2026-01-01", "", "300", "active", ""],  # unknown unit
        ["M-6", "C-6", "L1", "day-office", "OF-2", "2026-06-01", "", "0", "active", "true"],  # comped on OF-2
    ],
)


class TestBuildUnits:
    def test_active_filtering_and_issues(self):
        units, issues = build_units(INVENTORY, MEMBERSHIPS, AS_OF)
        by_id = {u.unit_id: u for u in units}
        assert by_id["OF-1"].occupied and by_id["OF-1"].contracted_revenue == 1500
        # M-4 ended 2026-05-31 -> OF-2 occupied only by comped M-6
        assert by_id["OF-2"].occupied and by_id["OF-2"].complimentary
        assert by_id["OF-2"].contracted_revenue == 0
        types = {i["type"] for i in issues}
        assert "active_memberships_without_unit" in types
        assert "membership_unknown_unit" in types


class TestOccupancyReport:
    def test_flags(self):
        report = occupancy_report(INVENTORY, MEMBERSHIPS, AS_OF)
        flags = {f["flag"] for f in report["flags"]}
        assert "out_of_service_units" in flags
        assert "complimentary_occupancy" in flags
        assert "missing_list_price" in flags
        # office occupancy: OF-1, OF-2 occupied of OF-1, OF-2 sellable in-service -> 100%
        office = next(m for m in report["metrics"] if m["name"] == "office_occupancy")
        assert office["value"] == "1.0000"
        # financial: priced pool OF-1 2000, OF-2 3000, DD-1 350; occupied revenue 1500+0+350
        fin = next(m for m in report["metrics"] if m["name"] == "financial_occupancy")
        assert fin["numerator"] == "1850" and fin["denominator"] == "5350"


DEALS = t(
    ["deal_id", "company_id", "product", "stage", "created_at", "updated_at",
     "owner", "next_action", "next_action_date", "expected_value"],
    [
        ["D-1", "C-1", "office", "proposal", "2026-05-01", "2026-06-25", "sam", "send revised quote", "2026-06-28", "2000"],
        ["D-2", "C-2", "office", "qualified", "2026-05-01", "2026-05-20", "", "", "", "1500"],  # unassigned, no next action, stale
        ["D-3", "C-2", "office", "tour", "2026-06-01", "2026-06-29", "alex", "follow up", "2026-07-05", "1500"],  # duplicate open w/ D-2
        ["D-4", "C-3", "desk", "won", "2026-04-01", "2026-05-01", "sam", "", "", "350"],
        ["D-5", "C-4", "office", "limbo", "2026-06-01", "2026-06-20", "alex", "", "", "900"],  # invalid stage
    ],
)


class TestPipelineReport:
    def test_findings(self):
        r = pipeline_report(DEALS, AS_OF, stale_days=21)
        f = r["findings"]
        assert [d["deal_id"] for d in f["unassigned"]] == ["D-2"]
        assert [d["deal_id"] for d in f["stale_deals"]] == ["D-2"]
        assert {d["deal_id"] for d in f["missing_next_action"]} == {"D-2"}
        assert [d["deal_id"] for d in f["overdue_next_action"]] == ["D-1"]
        assert [d["stage"] for d in f["invalid_stage"]] == ["limbo"]
        dupes = f["duplicate_open_deals"]
        assert len(dupes) == 1 and set(dupes[0]["deal_ids"]) == {"D-2", "D-3"}
        assert r["open_deals_by_owner"] == {"alex": 1, "sam": 1}


LEADS = t(
    ["lead_id", "created_at", "first_response_at", "source", "status"],
    [
        ["L-1", "2026-06-15 10:00", "2026-06-15 10:20", "Google Ads", "tour_booked"],
        ["L-2", "2026-06-16 16:30", "2026-06-17 09:15", "walk in", "contacted"],
        ["L-3", "2026-06-17 11:00", "", "Google Ads", "new"],       # never touched
        ["L-4", "2026-06-18 12:00", "2026-06-18 12:05", "", "qualified"],
        ["L-5", "bad-date", "", "Referral", "new"],
    ],
)

TOURS = t(
    ["tour_id", "lead_id", "status", "next_action"],
    [
        ["T-1", "L-1", "completed", ""],
        ["T-2", "L-2", "no_show", "rebook"],
        ["T-3", "L-9", "completed", "proposal"],  # unknown lead
    ],
)


class TestSpeedToLead:
    def test_business_minutes(self):
        r = speed_to_lead_report(LEADS)
        # L-1: 20 min; L-2: 16:30->17:00 =30, 09:00->09:15 =15 -> 45; L-4: 5
        assert r["responded_leads"] == 3
        assert r["median_minutes"] == 20
        assert r["leads_without_response"] == ["L-3"]
        assert r["leads_with_unparseable_created_at"] == ["L-5"]


class TestSources:
    def test_buckets(self):
        r = source_report(LEADS)
        assert r["by_canonical_source"]["google-ads"] == 2
        assert r["by_canonical_source"]["walk-in"] == 1
        assert r["blank_sources"] == 1


class TestFunnel:
    def test_counts_and_caveats(self):
        r = funnel_report(LEADS, TOURS, DEALS)
        c = r["counts"]
        assert c["leads"] == 5
        assert c["leads_with_tour"] == 2          # T-3's lead unknown
        assert c["tours_completed"] == 2
        assert c["tour_no_shows"] == 1
        assert r["rates"]["tour_show_rate"] == str(round(2 / 3, 4))
        assert r["caveats"]


INVOICES = t(
    ["invoice_id", "company_id", "membership_id", "issue_date", "due_date", "amount", "status"],
    [
        ["I-1", "C-1", "M-1", "2026-06-01", "2026-06-15", "1500", "paid"],
        ["I-2", "C-2", "M-2", "2026-06-01", "2026-06-15", "350", "failed"],
        ["I-3", "C-1", "M-1", "2026-05-01", "2026-05-15", "1500", "paid"],
    ],
)


class TestLeakage:
    def test_cross_file_checks(self):
        r = leakage_report(AS_OF, leads=LEADS, deals=DEALS, tours=TOURS,
                           memberships=MEMBERSHIPS, invoices=INVOICES,
                           inventory=INVENTORY)
        checks = {f["check"]: f for f in r["findings"]}
        assert checks["unfollowed_leads"]["count"] == 2          # L-3, L-5
        assert checks["completed_tours_without_next_action"]["ids"] == ["T-1"]
        # Won company C-3 has membership M-3 (active) -> not missing.
        assert "won_deals_without_membership" not in checks
        # M-3..M-6 lack recent invoices (M-6 comped -> excluded): M-3, M-4, M-5
        unbilled = checks["active_memberships_without_recent_invoice"]
        assert unbilled["count"] == 3
        assert checks["failed_or_overdue_invoices"]["count"] == 1
        assert checks["out_of_service_inventory"]["monthly_list_value_blocked"] == "1200"
        assert checks["active_status_past_end_date"]["ids"] == ["M-4"]
        assert r["skipped_checks"] == []

    def test_skipped_checks_reported(self):
        r = leakage_report(AS_OF, invoices=INVOICES)
        assert any("unfollowed_leads" in s for s in r["skipped_checks"])


PARTNERS = t(
    ["partner_id", "partner_name", "billing_model", "client_company_id", "active"],
    [
        ["P-1", "VO Partner Co", "partner_billed", "C-10", "true"],
        ["P-2", "VO Partner Co", "partner_billed", "C-1", "true"],   # C-1 also invoiced
        ["P-3", "Other Partner", "partner_billed", "C-10", "true"],  # duplicate client
    ],
)

VO_MEMBERSHIPS = t(
    ["membership_id", "company_id", "product", "status"],
    [
        ["M-10", "C-10", "virtual-office", "active"],
        ["M-11", "C-11", "virtual-office", "active"],   # direct, never invoiced
        ["M-12", "C-1", "virtual-office", "active"],
    ],
)


class TestVOReconciliation:
    def test_findings(self):
        r = vo_reconciliation(PARTNERS, VO_MEMBERSHIPS, INVOICES, AS_OF)
        checks = [f["check"] for f in r["findings"]]
        assert "duplicate_partner_client" in checks
        assert "possible_double_billing" in checks       # C-1 partner-billed + invoiced
        assert "direct_vo_client_never_invoiced" in checks  # C-11


class TestInspect:
    def test_entity_guess_ignores_filename(self):
        r = inspect_table(DEALS)
        assert r["likely_entity"] == "deals"
        r2 = inspect_table(t(["colour", "flavour"], [["red", "sweet"]]))
        assert r2["likely_entity"] is None
