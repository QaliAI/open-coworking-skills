"""Regression tests for the 2026-11 domain audit corrections.

Each test pins a defect that produced a wrong or unsupported answer:
product-label collisions in unit economics, a coverage figure presented as
break-even, missing leakage totals, a fixed pipeline stage vocabulary,
multi-site requirements called duplicates, and month-to-month exposure
reported as a bare ID list.
"""

from __future__ import annotations

from datetime import date

from opencoworking.analyze import leakage_report, pipeline_report
from opencoworking.economics import _product, unit_economics
from opencoworking.ingest import Table
from opencoworking.wave2 import renewal_scan

AS_OF = date(2026, 7, 1)


def _table(name: str, columns: list[str], rows: list[list[str]]) -> Table:
    return Table(name, columns, [dict(zip(columns, row, strict=True)) for row in rows])


def test_product_labels_resolve_without_substring_collisions() -> None:
    cases = {
        "virtual_office": "virtual_office",
        "virtual-office": "virtual_office",
        "Virtual Office": "virtual_office",
        "mailbox": "virtual_office",
        "vo": "virtual_office",
        "meeting_room": "meeting_room",
        "meeting-room": "meeting_room",
        "meeting_suite": "meeting_room",
        "boardroom": "meeting_room",
        "hot-desk": "desk",
        "dedicated_desk": "desk",
        "workstation": "desk",
        "private-office": "office",
        "team-suite": "office",
        "": "unassigned",
        "mystery_product": "other",
    }
    for label, expected in cases.items():
        assert _product(label) == expected, label


def _costs(rows: list[list[str]]) -> Table:
    return _table("costs", ["category", "monthly_amount", "kind", "product"], rows)


def test_virtual_office_cost_stays_in_its_own_bucket() -> None:
    inventory = _table(
        "inventory",
        ["unit_id", "unit_type", "capacity", "sellable", "out_of_service", "list_price"],
        [
            ["OF-1", "office", "2", "true", "false", "800"],
            ["VO-1", "virtual_office", "1", "true", "false", "300"],
        ],
    )
    memberships = _table(
        "memberships",
        ["membership_id", "unit_id", "status", "start_date", "end_date", "contracted_rate"],
        [
            ["M-1", "OF-1", "active", "2026-01-01", "", "800"],
            ["M-2", "VO-1", "active", "2026-01-01", "", "300"],
        ],
    )
    report = unit_economics(
        AS_OF,
        _costs([["rent", "1600", "fixed", "office"],
                ["vo_mail_fee", "300", "fixed", "virtual_office"]]),
        inventory=inventory,
        memberships=memberships,
    )
    rows = {row["product"]: row for row in report["product_contribution"]}
    assert set(rows) == {"office", "virtual_office"}
    assert rows["office"]["supplied_monthly_cost"] == "1600"
    assert rows["virtual_office"]["supplied_monthly_cost"] == "300"
    assert rows["office"]["contribution"] == "-800"
    assert rows["virtual_office"]["contribution"] == "0"
    assert report["product_mapping"]["unmapped_cost_labels"] == []


def _simple_tables(cost_rows: list[list[str]]) -> tuple[Table, Table, Table]:
    inventory = _table(
        "inventory",
        ["unit_id", "unit_type", "capacity", "sellable", "out_of_service", "list_price"],
        [
            ["OF-1", "office", "2", "true", "false", "800"],
            ["OF-2", "office", "2", "true", "false", "800"],
        ],
    )
    memberships = _table(
        "memberships",
        ["membership_id", "unit_id", "status", "start_date", "end_date", "contracted_rate"],
        [["M-1", "OF-1", "active", "2026-01-01", "", "800"]],
    )
    return _costs(cost_rows), inventory, memberships


def test_coverage_is_labelled_and_break_even_needs_a_per_workstation_cost() -> None:
    costs, inventory, memberships = _simple_tables(
        [["rent", "1600", "fixed", "office"], ["cleaning", "200", "variable", "office"]]
    )
    report = unit_economics(AS_OF, costs, inventory=inventory, memberships=memberships)
    coverage = report["coverage"]
    assert coverage["metric_kind"] == "fixed_cost_coverage"
    assert "fixed-cost coverage" in coverage["not_a_break_even"].lower()
    assert coverage["workstations_to_cover_fixed_costs"] == "4.00"
    assert coverage["break_even_on_contribution"]["status"] == "not_computed"
    assert "variable_per_workstation" in coverage["break_even_on_contribution"]["reason"]
    assert report["variable_monthly"] == "200"

    costs, inventory, memberships = _simple_tables(
        [
            ["rent", "1600", "fixed", "office"],
            ["cleaning", "200", "variable", "office"],
            ["consumables", "50", "variable_per_workstation", "office"],
        ]
    )
    report = unit_economics(AS_OF, costs, inventory=inventory, memberships=memberships)
    coverage = report["coverage"]
    assert report["variable_monthly"] == "200"
    assert report["variable_per_workstation_monthly"] == "50"
    break_even = coverage["break_even_on_contribution"]
    assert break_even["status"] == "measured"
    assert break_even["contribution_per_workstation"] == "350.00"
    assert break_even["workstations_to_break_even"] == "4.57"
    assert break_even["occupancy_to_break_even"] == "1.1425"
    # The coverage figure is unchanged by the new variable row.
    assert coverage["workstations_to_cover_fixed_costs"] == "4.00"


def test_leakage_emits_three_separate_totals() -> None:
    deals = _table(
        "deals",
        ["deal_id", "company_id", "stage", "updated_at", "expected_value"],
        [["D-1", "C-1", "qualified", "2026-05-01", "1000"]],
    )
    memberships = _table(
        "memberships",
        ["membership_id", "company_id", "status", "end_date", "contracted_rate",
         "complimentary", "billing_frequency"],
        [["M-1", "C-1", "active", "", "500", "false", "monthly"]],
    )
    invoices = _table(
        "invoices", ["invoice_id", "membership_id", "issue_date", "amount", "status"], []
    )
    inventory = _table(
        "inventory", ["unit_id", "out_of_service", "list_price"], [["OF-9", "true", "900"]]
    )
    report = leakage_report(
        AS_OF, deals=deals, memberships=memberships, invoices=invoices, inventory=inventory
    )
    totals = report["totals"]
    assert totals["billing_at_risk"]["monthly_amount"] == "500"
    assert totals["pipeline_at_risk"]["unweighted_pipeline_value"] == "1000"
    assert totals["idle_list_value"]["monthly_list_value"] == "900"
    assert "never added" in totals["not_a_total"]
    assert totals["billing_at_risk"]["never_summed_with"]


def test_pipeline_accepts_operator_stages_and_flags_overload() -> None:
    deals = _table(
        "deals",
        ["deal_id", "company_id", "product", "location_id", "stage", "updated_at", "owner"],
        [
            ["D-1", "C-1", "office", "L-1", "contract_sent", "2026-06-30", "sam"],
            ["D-2", "C-2", "office", "L-1", "qualified", "2026-06-30", "alex"],
            ["D-3", "C-3", "desk", "L-1", "qualified", "2026-06-30", "riley"],
            ["D-4", "C-4", "desk", "L-1", "qualified", "2026-06-30", "riley"],
            ["D-5", "C-5", "desk", "L-1", "qualified", "2026-06-30", "riley"],
            ["D-6", "C-6", "desk", "L-1", "qualified", "2026-06-30", "riley"],
        ],
    )
    report = pipeline_report(
        deals, AS_OF, open_stages=["qualified", "contract_sent"], overload_multiple=2.0
    )
    assert report["findings"]["invalid_stage"] == []
    assert report["median_open_deals_per_owner"] == 1.0
    assert [f["owner"] for f in report["findings"]["overloaded_owners"]] == ["riley"]
    assert report["stage_snapshot"]["counts"] == {"qualified": 5, "contract_sent": 1}
    assert "not a cohort" in report["stage_snapshot"]["caveat"]


def test_multi_location_requirement_is_not_a_duplicate() -> None:
    deals = _table(
        "deals",
        ["deal_id", "company_id", "product", "location_id", "stage", "updated_at"],
        [
            ["D-1", "C-1", "office", "L-1", "qualified", "2026-06-30"],
            ["D-2", "C-1", "office", "L-2", "qualified", "2026-06-30"],
        ],
    )
    report = pipeline_report(deals, AS_OF)
    assert report["findings"]["duplicate_open_deals"] == []
    assert len(report["findings"]["multiple_simultaneous_requirements"]) == 1
    assert report["findings"]["multiple_simultaneous_requirements"][0]["locations"] == [
        "l-1", "l-2"
    ]


def test_month_to_month_is_reported_as_exposure() -> None:
    memberships = _table(
        "memberships",
        ["membership_id", "company_id", "status", "term_months", "contracted_rate"],
        [["M-8", "C-8", "active", "", "350"]],
    )
    report = renewal_scan(memberships, AS_OF)
    assert report["month_to_month_active"] == ["M-8"]
    exposure = report["month_to_month_exposure"]
    assert exposure["count"] == 1
    assert exposure["contracted_mrr"] == "350"
    assert exposure["period"] == "active as of 2026-07-01"
