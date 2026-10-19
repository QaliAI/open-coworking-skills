"""Known answers for the v0.1.0 additions: room status, unit economics, stack audit."""

from datetime import date
from decimal import Decimal

from opencoworking.economics import unit_economics
from opencoworking.ingest import Table, load_csv
from opencoworking.stack_audit import stack_audit
from opencoworking.wave2 import room_yield

ROOT_ECON = "tests/fixtures/unit-economics"
AS_OF = date(2026, 7, 1)


def test_cancelled_and_no_show_leave_booked_hours():
    bookings = Table(
        "b",
        ["booking_id", "room_unit_id", "start_at", "end_at", "amount",
         "member_booking", "status"],
        [
            {"booking_id": "1", "room_unit_id": "MR-1", "start_at": "2026-06-03T09:00:00",
             "end_at": "2026-06-03T11:00:00", "amount": "100", "member_booking": "false",
             "status": "confirmed"},
            {"booking_id": "2", "room_unit_id": "MR-1", "start_at": "2026-06-03T13:00:00",
             "end_at": "2026-06-03T14:00:00", "amount": "50", "member_booking": "true",
             "status": "no_show"},
            {"booking_id": "3", "room_unit_id": "MR-1", "start_at": "2026-06-04T18:00:00",
             "end_at": "2026-06-04T20:00:00", "amount": "0", "member_booking": "true",
             "status": "cancelled"},
        ])
    inventory = Table("i", ["unit_id", "unit_type"],
                      [{"unit_id": "MR-1", "unit_type": "meeting_room"}])
    report = room_yield(bookings, inventory, Decimal("10"))
    room = report["rooms"][0]
    assert room["bookings"] == 1
    assert room["booked_hours"] == "2"
    assert room["gross_revenue"] == "100"
    assert room["excluded_bookings"] == 2
    assert report["excluded_bookings"] == 2
    assert report["dayparts"]["morning"] == 1
    assert report["dayparts"]["pattern_claim_allowed"] is False
    assert "excluded" in report["booking_status_note"]
    # 2 days in period (3 Jun and only honored booking is 3 Jun — cancelled is excluded
    # so dates are only the honored start). One day, 10 bookable hours, 2 booked.
    assert room["bookable_hours_assumed"] == "10"
    assert room["revenue_per_available_hour"] == "10.00"


def test_missing_status_column_keeps_every_parseable_booking():
    bookings = Table(
        "b",
        ["booking_id", "room_unit_id", "start_at", "end_at", "amount", "member_booking"],
        [{"booking_id": "1", "room_unit_id": "MR-1", "start_at": "2026-06-03T09:00:00",
          "end_at": "2026-06-03T10:00:00", "amount": "0", "member_booking": "true"}])
    inventory = Table("i", ["unit_id", "unit_type"],
                      [{"unit_id": "MR-1", "unit_type": "meeting_room"}])
    report = room_yield(bookings, inventory)
    assert report["rooms"][0]["booked_hours"] == "1"
    assert "could not be separated" in report["booking_status_note"]
    assert "Contribution margin was not computed" in report["contribution_note"]


def test_partial_cost_does_not_become_margin():
    bookings = Table(
        "b",
        ["booking_id", "room_unit_id", "start_at", "end_at", "amount",
         "member_booking", "cost"],
        [
            {"booking_id": "1", "room_unit_id": "MR-1", "start_at": "2026-06-03T09:00:00",
             "end_at": "2026-06-03T10:00:00", "amount": "100", "member_booking": "false",
             "cost": "20"},
            {"booking_id": "2", "room_unit_id": "MR-1", "start_at": "2026-06-03T11:00:00",
             "end_at": "2026-06-03T12:00:00", "amount": "100", "member_booking": "false",
             "cost": ""},
        ])
    inventory = Table("i", ["unit_id", "unit_type"],
                      [{"unit_id": "MR-1", "unit_type": "meeting_room"}])
    room = room_yield(bookings, inventory)["rooms"][0]
    assert room["contribution"] is None
    assert "unknown, not zero" in room["contribution_note"]


def test_unit_economics_coverage_is_hand_computed():
    report = unit_economics(
        AS_OF, load_csv(f"{ROOT_ECON}/costs.csv"),
        inventory=load_csv(f"{ROOT_ECON}/inventory.csv"),
        memberships=load_csv(f"{ROOT_ECON}/memberships.csv"),
        meeting_revenue=Decimal("300"))
    # Occupied sellable capacity 2, contracted MRR 800, average 400.
    # Fixed rent 1600 / 400 = 4.00 workstations. Capacity 4 -> 100% coverage occupancy.
    assert report["fixed_monthly"] == "1600"
    assert report["variable_monthly"] == "200"
    assert report["revenue"]["occupied_workstations"] == 2
    assert report["revenue"]["contracted_mrr"] == "800"
    assert report["coverage"]["workstations_to_cover_fixed_costs"] == "4.00"
    assert report["coverage"]["occupancy_to_cover_fixed_costs"] == "1.0000"
    office = next(row for row in report["product_contribution"]
                  if row["product"] == "office")
    assert office["contribution"] == "-1000"
    assert report["meeting_and_event"]["contribution"] is None
    assert "unknown, not zero" in report["categories_not_in_the_file_are"]


def test_unit_economics_refuses_to_invent_costs():
    empty = Table("c", ["category", "monthly_amount", "kind"], [])
    report = unit_economics(AS_OF, empty)
    assert report["fixed_monthly"] == "0"
    assert report["revenue"]["status"] == "not_measured"
    assert report["coverage"]["status"] == "not_measured"


def test_stack_audit_flags_absence_and_writes_without_contacting_anyone():
    report = stack_audit(load_csv("tests/fixtures/stack-audit/systems.csv"))
    checks = {item["check"] for item in report["findings"]}
    assert "category_absent" in checks
    assert "disconnected_core_system" in checks
    assert "high_risk_write" in checks
    assert "manual_reentry" in checks
    assert "weak_ids" in checks
    assert "no_system_of_record" in checks  # access has Salto, not marked SoR
    # crm is connected. payments and access are listed but blank. accounting and wifi are absent.
    assert report["core_five"]["categories_with_a_listed_system"] == 3
    assert report["core_five"]["categories_with_any_connection"] == 1
    assert "not read" in report["notes_policy"]
