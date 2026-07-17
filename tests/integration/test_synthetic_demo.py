"""End-to-end verification of the Northstar Coworking Demo dataset.

Expected values in tests/fixtures/synthetic_expected.json were computed BY
HAND from the literal rows in scripts/generate_synthetic_data.py, so these
tests verify the analysis code against an independent source of truth.
"""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from opencoworking.analyze import (
    funnel_report,
    leakage_report,
    occupancy_report,
    source_report,
    speed_to_lead_report,
    vo_reconciliation,
)
from opencoworking.ingest import load_csv
from opencoworking.quality import check_duplicates

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "examples" / "synthetic-space" / "data"
EXPECTED = json.loads(
    (REPO / "tests" / "fixtures" / "synthetic_expected.json").read_text(encoding="utf-8")
)
AS_OF = date.fromisoformat(EXPECTED["as_of"])


@pytest.fixture(scope="module")
def tables():
    names = ["locations", "inventory", "companies", "contacts", "leads", "deals",
             "tours", "memberships", "members", "invoices", "payments",
             "room-bookings", "events", "reviews", "virtual-office-partners"]
    return {n: load_csv(DATA / f"{n}.csv") for n in names}


def test_all_files_present_and_nonempty(tables):
    for name, table in tables.items():
        assert len(table.rows) > 0, f"{name}.csv is empty"
        assert not table.warnings, f"{name}.csv structural warnings: {table.warnings}"


def test_generator_is_deterministic(tmp_path):
    script = REPO / "scripts" / "generate_synthetic_data.py"
    r = subprocess.run([sys.executable, str(script), "--out", str(tmp_path), "--force"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    for f in DATA.glob("*.csv"):
        regenerated = (tmp_path / f.name).read_text(encoding="utf-8")
        committed = f.read_text(encoding="utf-8")
        assert regenerated.replace("\r\n", "\n") == committed.replace("\r\n", "\n"), f.name


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
    discounted = [u["unit_id"] for u in flags["discount_over_25pct"]["units"]]
    assert discounted == exp["flags"]["discount_over_25pct_units"]

    unassigned = next(i for i in report["referential_issues"]
                      if i["type"] == "active_memberships_without_unit")
    assert unassigned["count"] == exp["active_memberships_without_unit_count"]


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


def test_source_normalization_known_answers(tables):
    report = source_report(tables["leads"])
    assert report["by_canonical_source"] == EXPECTED["sources"]
    assert report["blank_sources"] == EXPECTED["sources"]["unknown"]


def test_funnel_known_answers(tables):
    report = funnel_report(tables["leads"], tables["tours"], tables["deals"])
    exp = EXPECTED["funnel"]
    for key in ("leads", "contacted", "leads_with_tour", "tours_completed",
                "tour_no_shows", "deals_won"):
        assert report["counts"][key] == exp[key], key
    assert report["rates"]["tour_show_rate"] == exp["tour_show_rate"]


def test_speed_to_lead_known_answers(tables):
    report = speed_to_lead_report(tables["leads"])
    exp = EXPECTED["speed_to_lead"]
    assert report["responded_leads"] == exp["responded_leads"]
    assert report["leads_without_response"] == exp["leads_without_response"]
    assert report["leads_with_unparseable_created_at"] == []


def test_duplicate_contacts_detected(tables):
    findings = check_duplicates(tables["contacts"].rows, ["email"], "contact")
    # The duplicate pair differs only by email case (CT-9001 / CT-9014).
    assert findings and findings[0].rows == EXPECTED["quality"]["duplicate_contact_email_rows"]


def test_no_real_looking_pii_in_fixtures(tables):
    """Every email must use a .example domain; phones must be 555-01xx."""
    for row in tables["contacts"].rows:
        email = row["email"].lower()
        assert email.endswith(".example"), f"non-synthetic email: {email}"
        assert row["phone"].startswith("555-01"), f"non-reserved phone: {row['phone']}"


def test_cli_end_to_end_on_demo(tmp_path):
    """The documented demo command works from a clean shell."""
    r = subprocess.run(
        [sys.executable, "-m", "opencoworking.cli", "occupancy",
         "--inventory", str(DATA / "inventory.csv"),
         "--memberships", str(DATA / "memberships.csv"),
         "--as-of", EXPECTED["as_of"],
         "--format", "json"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    payload = json.loads(r.stdout)
    office = next(m for m in payload["metrics"] if m["name"] == "office_occupancy")
    assert office["value"] == EXPECTED["occupancy"]["office_occupancy"]["value"]
