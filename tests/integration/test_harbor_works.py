"""End-to-end verification against the Harbor Works adversarial dataset.

Harbor Works was hand-authored during the independent audit with expected
answers computed by hand BEFORE the engine ran on it, so these tests check
the analysis code against a second, independent source of truth — with
messier data than Northstar (malformed row, unicode, injections, currency
conflict, mixed date conventions).
"""

import json
from datetime import date
from pathlib import Path

import pytest

from opencoworking.analyze import (
    funnel_report,
    leakage_report,
    occupancy_report,
    pipeline_report,
    source_report,
    speed_to_lead_report,
    vo_reconciliation,
)
from opencoworking.ingest import load_csv
from opencoworking.normalize import detect_currency, parse_money
from opencoworking.quality import check_duplicates

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "examples" / "harbor-works" / "data"
EXPECTED = json.loads(
    (REPO / "tests" / "fixtures" / "harbor_expected.json").read_text(encoding="utf-8")
)
AS_OF = date.fromisoformat(EXPECTED["as_of"])


@pytest.fixture(scope="module")
def tables():
    names = ["locations", "inventory", "companies", "contacts", "leads", "deals",
             "tours", "memberships", "invoices", "payments", "room-bookings",
             "virtual-office-partners"]
    return {n: load_csv(DATA / f"{n}.csv") for n in names}


def test_malformed_row_produces_warning_not_silence(tables):
    # HWL-12 is deliberately short; the loader must warn, pad, and continue.
    leads = tables["leads"]
    assert len(leads.warnings) == EXPECTED["quality"]["leads_structural_warning_count"]
    assert "Row 13" in leads.warnings[0]
    assert len(leads.rows) == EXPECTED["funnel"]["leads"]
    hwl12 = next(r for r in leads.rows if r["lead_id"] == "HWL-12")
    assert hwl12["source"] == "" and hwl12["status"] == ""


def test_occupancy_known_answers(tables):
    report = occupancy_report(tables["inventory"], tables["memberships"], AS_OF)
    exp = EXPECTED["occupancy"]
    by_name = {m["name"]: m for m in report["metrics"]}
    for metric in ("office_occupancy", "workstation_occupancy", "financial_occupancy"):
        assert by_name[metric]["numerator"] == exp[metric]["numerator"], metric
        assert by_name[metric]["denominator"] == exp[metric]["denominator"], metric
        assert by_name[metric]["value"] == exp[metric]["value"], metric
    flags = {f["flag"]: f for f in report["flags"]}
    assert flags["out_of_service_units"]["units"] == exp["flags"]["out_of_service_units"]
    assert flags["complimentary_occupancy"]["units"] == exp["flags"]["complimentary_occupancy"]
    assert sorted(flags["missing_list_price"]["units"]) == exp["flags"]["missing_list_price"]
    assert [u["unit_id"] for u in flags["discount_over_25pct"]["units"]] == \
        exp["flags"]["discount_over_25pct_units"]
    issues = {i["type"]: i for i in report["referential_issues"]}
    assert issues["active_memberships_without_unit"]["count"] == \
        exp["active_memberships_without_unit_count"]
    assert issues["membership_unknown_unit"]["membership_id"] == \
        exp["membership_unknown_unit"]["membership_id"]


def test_leakage_known_answers(tables):
    report = leakage_report(
        AS_OF, leads=tables["leads"], deals=tables["deals"], tours=tables["tours"],
        memberships=tables["memberships"], invoices=tables["invoices"],
        inventory=tables["inventory"], payments=tables["payments"])
    exp = EXPECTED["leakage"]
    checks = {f["check"]: f for f in report["findings"]}
    assert checks["unfollowed_leads"]["ids"] == exp["unfollowed_leads"]
    assert checks["stale_open_deals_30d"]["ids"] == exp["stale_open_deals_30d"]
    assert (checks["completed_tours_without_next_action"]["ids"]
            == exp["completed_tours_without_next_action"])
    assert checks["won_deals_without_membership"]["ids"] == exp["won_deals_without_membership"]
    unbilled = checks["active_memberships_without_recent_invoice"]
    assert [i["membership_id"] for i in unbilled["items"]] == \
        exp["active_memberships_without_recent_invoice"]
    assert unbilled["monthly_amount_at_risk"] == exp["unbilled_monthly_amount_at_risk"]
    failed = checks["failed_or_overdue_invoices"]
    assert [i["invoice_id"] for i in failed["items"]] == exp["failed_or_overdue_invoices"]
    assert failed["amount_outstanding"] == exp["failed_overdue_amount"]
    oos = checks["out_of_service_inventory"]
    assert [i["unit_id"] for i in oos["items"]] == exp["out_of_service_inventory"]
    assert oos["monthly_list_value_blocked"] == exp["blocked_monthly_list_value"]
    assert checks["active_status_past_end_date"]["ids"] == exp["active_status_past_end_date"]
    assert report["skipped_checks"] == []


def test_vo_reconciliation_known_answers(tables):
    report = vo_reconciliation(tables["virtual-office-partners"], tables["memberships"],
                               tables["invoices"], AS_OF)
    exp = EXPECTED["vo_reconciliation"]
    assert report["active_vo_memberships"] == exp["active_vo_memberships"]
    assert report["active_partner_clients"] == exp["active_partner_clients"]
    got: dict[str, list[str]] = {}
    for f in report["findings"]:
        got.setdefault(f["check"], []).append(f["company_id"])
    assert got == exp["findings"]


def test_sources_funnel_speed_known_answers(tables):
    assert source_report(tables["leads"])["by_canonical_source"] == EXPECTED["sources"]
    funnel = funnel_report(tables["leads"], tables["tours"], tables["deals"])
    exp = EXPECTED["funnel"]
    for key in ("leads", "contacted", "leads_with_tour", "tours_completed",
                "tour_no_shows", "deals_won"):
        assert funnel["counts"][key] == exp[key], key
    assert funnel["rates"]["tour_show_rate"] == exp["tour_show_rate"]
    speed = speed_to_lead_report(tables["leads"])
    assert speed["responded_leads"] == EXPECTED["speed_to_lead"]["responded_leads"]
    assert speed["leads_without_response"] == EXPECTED["speed_to_lead"]["leads_without_response"]


def test_pipeline_known_answers(tables):
    r = pipeline_report(tables["deals"], AS_OF, stale_days=21)
    f = r["findings"]
    exp = EXPECTED["pipeline"]
    dupes = f["duplicate_open_deals"]
    assert len(dupes) == 1 and sorted(dupes[0]["deal_ids"]) == exp["duplicate_open_deal_pair"]
    assert [d["deal_id"] for d in f["unassigned"]] == exp["unassigned"]
    assert [d["deal_id"] for d in f["missing_next_action"]] == exp["missing_next_action"]
    assert [d["deal_id"] for d in f["overdue_next_action"]] == exp["overdue_next_action"]
    assert [d["deal_id"] for d in f["stale_deals"]] == exp["stale_deals"]


def test_duplicate_contacts_and_unicode(tables):
    findings = check_duplicates(tables["contacts"].rows, ["email"], "contact")
    assert findings and findings[0].rows == EXPECTED["quality"]["duplicate_contact_email_rows"]
    names = {r["last_name"] for r in tables["contacts"].rows}
    assert "Müller" in names and "García-Ibáñez" in names and "田中" in names


def test_currency_conflict_detectable(tables):
    exp = EXPECTED["currency_conflict"]
    row = next(r for r in tables["memberships"].rows
               if r["membership_id"] == exp["membership_id"])
    assert row["contracted_rate"] == exp["raw_rate"]
    assert detect_currency(row["contracted_rate"]) == exp["detected_currency"]
    assert str(parse_money(row["contracted_rate"])) == exp["parsed_amount"]


def test_injection_content_is_preserved_as_data(tables):
    """The engine must carry injection text through as inert data - it is the
    agent layer's job to refuse it, and eval cases test that side."""
    lead = next(r for r in tables["leads"].rows if r["lead_id"] == "HWL-09")
    assert "ignore previous instructions" in lead["next_action"].lower()
    omen = next(r for r in tables["companies"].rows if r["company_id"] == "HC-OMEN")
    assert omen["name"].startswith("=HYPERLINK")


def test_no_real_looking_pii(tables):
    for row in tables["contacts"].rows:
        assert row["email"] == "" or row["email"].lower().endswith(".example")
        assert row["phone"] == "" or row["phone"].startswith("555-01")
