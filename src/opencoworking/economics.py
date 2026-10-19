"""Unit economics from operator-supplied costs. Never invents an expense.

Costs must already be monthly totals. A category that is absent from the file
is unknown, not zero. Break-even is a coverage count at the current average
contracted rate, and the report says so.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from .analyze import _money, build_units
from .ingest import Table
from .metrics import ZERO

_PRODUCTS = {
    "office": {"office", "private_office", "private-office", "suite"},
    "desk": {"desk", "dedicated_desk", "dedicated-desk", "hot_desk", "hot-desk",
             "coworking", "open_desk"},
    "virtual_office": {"virtual", "virtual_office", "virtual-office", "vo",
                       "mailbox", "business_address", "business-address"},
    "meeting_room": {"meeting", "meeting_room", "meeting-room", "event",
                     "training", "conference"},
}


def _product(label: str) -> str:
    key = label.strip().lower().replace(" ", "_")
    for name, aliases in _PRODUCTS.items():
        if key in aliases or any(alias in key for alias in aliases):
            return name
    return "other" if key else "unassigned"


def _amount(row: dict[str, str]) -> Decimal | None:
    for key in ("monthly_amount", "amount", "amount_monthly"):
        if key in row and row.get(key, "").strip():
            return _money(row.get(key, ""))
    return None


def unit_economics(as_of: date, costs: Table, inventory: Table | None = None,
                   memberships: Table | None = None,
                   meeting_revenue: Decimal | None = None) -> dict[str, object]:
    """Coverage math for one location portfolio at ``as_of``.

    ``meeting_revenue`` is used only when the caller passes a figure for the
    same month. It is never estimated from a booking export inside this function.
    """
    problems: list[str] = []
    fixed = ZERO
    variable = ZERO
    categories: list[dict[str, str]] = []
    by_product_cost: dict[str, Decimal] = {}
    has_product = "product" in set(costs.columns)
    for row in costs.rows:
        category = row.get("category", "").strip()
        kind = row.get("kind", "").strip().lower()
        amount = _amount(row)
        if not category or amount is None or kind not in {"fixed", "variable"}:
            problems.append(
                "skipped a cost row missing category, monthly amount, or kind "
                "(fixed|variable); it was not treated as zero")
            continue
        if kind == "fixed":
            fixed += amount
        else:
            variable += amount
        product = _product(row.get("product", "")) if has_product else ""
        item = {"category": category, "kind": kind, "monthly_amount": str(amount)}
        if product:
            item["product"] = product
            by_product_cost[product] = by_product_cost.get(product, ZERO) + amount
        categories.append(item)

    revenue: dict[str, object] = {
        "status": "not_measured",
        "reason": "membership and inventory exports were not both provided",
    }
    coverage: dict[str, object] = {"status": "not_measured",
                                   "reason": "needs fixed costs plus occupied-workstation revenue"}
    product_rows: list[dict[str, object]] = []
    if inventory is not None and memberships is not None:
        units, issues = build_units(inventory, memberships, as_of)
        pool = [u for u in units if u.sellable and not u.out_of_service]
        occupied = [u for u in pool if u.occupied]
        capacity = sum(u.capacity for u in pool)
        occupied_ws = sum(u.capacity for u in occupied)
        mrr = sum((u.contracted_revenue for u in occupied), ZERO)
        by_product_rev: dict[str, Decimal] = {}
        for unit in occupied:
            by_product_rev[_product(unit.unit_type)] = (
                by_product_rev.get(_product(unit.unit_type), ZERO) + unit.contracted_revenue)
        revenue = {
            "status": "measured",
            "period": f"active contracted memberships on {as_of.isoformat()}",
            "sellable_workstations": capacity,
            "occupied_workstations": occupied_ws,
            "contracted_mrr": str(mrr),
            "average_contracted_per_occupied_workstation": (
                str((mrr / occupied_ws).quantize(Decimal("0.01"))) if occupied_ws else None),
            "issues": issues,
            "exclusions": ["out_of_service units", "units with sellable=false",
                           "complimentary revenue is excluded from contracted_mrr "
                           "(the unit still counts as occupied)"],
        }
        if fixed > 0 and occupied_ws > 0 and mrr > 0:
            rate = mrr / occupied_ws
            needed = (fixed / rate).quantize(Decimal("0.01"))
            coverage = {
                "status": "measured",
                "fixed_monthly": str(fixed),
                "workstations_to_cover_fixed_costs": str(needed),
                "occupancy_to_cover_fixed_costs": (
                    str((needed / capacity).quantize(Decimal("0.0001"))) if capacity else None),
                "formula": "fixed monthly costs / (contracted MRR / occupied sellable "
                           "workstations)",
                "assumption": "The next workstation is assumed to earn the current "
                              "average contracted rate. Variable costs in the file are "
                              "this month's totals, not a cost of the next workstation, "
                              "unless every variable row is already a monthly total the "
                              "operator wants held aside. This is coverage math, not a "
                              "marginal contribution model, and not an industry benchmark.",
            }
        else:
            coverage = {"status": "not_measured",
                        "reason": "fixed costs, occupied workstations, or contracted MRR is zero"}
        if has_product:
            for product in sorted(set(by_product_rev) | set(by_product_cost)):
                rev = by_product_rev.get(product, ZERO)
                cost = by_product_cost.get(product, ZERO)
                product_rows.append({
                    "product": product,
                    "contracted_mrr": str(rev),
                    "supplied_monthly_cost": str(cost),
                    "contribution": str(rev - cost),
                    "note": "Cost is only what the file assigned to this product. "
                            "Unassigned costs stay in the location total.",
                })
        else:
            product_rows = []
    if meeting_revenue is not None:
        meeting_cost = by_product_cost.get("meeting_room")
        revenue_meeting: dict[str, object] = {
            "status": "operator_supplied",
            "monthly_revenue": str(meeting_revenue),
            "note": "Meeting and event revenue was passed in by the operator for this "
                    "month. It was not estimated from bookings.",
        }
        if meeting_cost is not None:
            revenue_meeting["supplied_monthly_cost"] = str(meeting_cost)
            revenue_meeting["contribution"] = str(meeting_revenue - meeting_cost)
        else:
            revenue_meeting["contribution"] = None
            revenue_meeting["contribution_note"] = (
                "No cost row was labeled meeting_room. Contribution was not computed.")
    else:
        revenue_meeting = {"status": "not_measured",
                           "reason": "no meeting revenue figure was supplied"}

    return {
        "as_of": as_of.isoformat(),
        "cost_rows_used": len(categories),
        "fixed_monthly": str(fixed),
        "variable_monthly": str(variable),
        "categories": categories,
        "categories_not_in_the_file_are": "unknown, not zero",
        "revenue": revenue,
        "meeting_and_event": revenue_meeting,
        "coverage": coverage,
        "product_contribution": product_rows or {
            "status": "not_measured",
            "reason": "product contribution needs a product column on the cost file "
                      "and both inventory and memberships",
        },
        "problems": problems,
        "definitions": [
            "fixed_monthly = sum of cost rows whose kind is fixed",
            "variable_monthly = sum of cost rows whose kind is variable",
            "workstations_to_cover_fixed_costs = fixed_monthly / average contracted "
            "revenue per occupied sellable workstation",
            "average contracted revenue uses the same occupied sellable in-service "
            "pool as the occupancy dashboard, with complimentary contracted revenue "
            "excluded from the numerator and the workstation still in the denominator",
            "no rent, payroll, CAM, or software figure is filled in when absent",
        ],
    }
