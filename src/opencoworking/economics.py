"""Unit economics from operator-supplied costs. Never invents an expense.

Costs must already be monthly totals. A category that is absent from the file
is unknown, not zero. Break-even is a coverage count at the current average
contracted rate, and the report says so.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from .analyze import _money, build_units
from .ingest import Table
from .metrics import ZERO

# Exact aliases only. Substring matching is deliberately not used for the
# first pass: "office" is a substring of "virtual_office", and matching it
# first silently folded every virtual-office cost into the office bucket.
_PRODUCT_ALIASES: dict[str, str] = {
    "office": "office",
    "private_office": "office",
    "private_suite": "office",
    "office_suite": "office",
    "team_suite": "office",
    "team_office": "office",
    "desk": "desk",
    "hot_desk": "desk",
    "dedicated_desk": "desk",
    "dedicated": "desk",
    "flex_desk": "desk",
    "open_desk": "desk",
    "workstation": "desk",
    "coworking": "desk",
    "virtual_office": "virtual_office",
    "virtual": "virtual_office",
    "vo": "virtual_office",
    "mailbox": "virtual_office",
    "mail_box": "virtual_office",
    "business_address": "virtual_office",
    "registered_office": "virtual_office",
    "address_service": "virtual_office",
    "meeting_room": "meeting_room",
    "meeting": "meeting_room",
    "boardroom": "meeting_room",
    "board_room": "meeting_room",
    "conference": "meeting_room",
    "training": "meeting_room",
    "event": "meeting_room",
    "room": "meeting_room",
    "rooms": "meeting_room",
}

# Longest first, and only as a whole-token fallback, so "meeting_room" wins
# over "room" and "private_office" wins over "office".
_ALIASES_BY_LENGTH = tuple(sorted(_PRODUCT_ALIASES, key=len, reverse=True))


def _normalise_label(label: str) -> str:
    key = (label or "").strip().lower().replace("-", "_").replace(" ", "_")
    return re.sub(r"_+", "_", key).strip("_")


def _product(label: str) -> str:
    """Map a free-text product label to a canonical bucket.

    Exact alias first, then a whole-token fallback. An unrecognised non-empty
    label returns ``other`` and is reported to the operator rather than being
    guessed into a bucket.
    """
    key = _normalise_label(label)
    if not key:
        return "unassigned"
    if key in _PRODUCT_ALIASES:
        return _PRODUCT_ALIASES[key]
    padded = f"_{key}_"
    for alias in _ALIASES_BY_LENGTH:
        if f"_{alias}_" in padded:
            return _PRODUCT_ALIASES[alias]
    return "other"


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
    variable_per_workstation = ZERO
    categories: list[dict[str, str]] = []
    by_product_cost: dict[str, Decimal] = {}
    unmapped_cost_labels: set[str] = set()
    has_product = "product" in set(costs.columns)
    valid_kinds = {"fixed", "variable", "variable_per_workstation"}
    for row in costs.rows:
        category = row.get("category", "").strip()
        kind = row.get("kind", "").strip().lower()
        amount = _amount(row)
        if not category or amount is None or kind not in valid_kinds:
            problems.append(
                "skipped a cost row missing category, monthly amount, or a kind of "
                "fixed|variable|variable_per_workstation; it was not treated as zero")
            continue
        if kind == "fixed":
            fixed += amount
        elif kind == "variable":
            variable += amount
        else:
            variable_per_workstation += amount
        raw_product = row.get("product", "")
        product = _product(raw_product) if has_product else ""
        if product == "other" and raw_product.strip():
            unmapped_cost_labels.add(raw_product.strip())
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
    product_mapping: dict[str, object] = {
        "status": "not_measured",
        "reason": "product mapping needs a product column on the cost file and both "
                  "inventory and memberships",
    }
    if inventory is not None and memberships is not None:
        units, issues = build_units(inventory, memberships, as_of)
        pool = [u for u in units if u.sellable and not u.out_of_service]
        occupied = [u for u in pool if u.occupied]
        capacity = sum(u.capacity for u in pool)
        occupied_ws = sum(u.capacity for u in occupied)
        mrr = sum((u.contracted_revenue for u in occupied), ZERO)
        by_product_rev: dict[str, Decimal] = {}
        unmapped_unit_types: set[str] = set()
        for unit in occupied:
            bucket = _product(unit.unit_type)
            if bucket == "other" and (unit.unit_type or "").strip():
                unmapped_unit_types.add(unit.unit_type.strip())
            by_product_rev[bucket] = (
                by_product_rev.get(bucket, ZERO) + unit.contracted_revenue)
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
            if variable_per_workstation > 0:
                margin_per_ws = rate - variable_per_workstation
                if margin_per_ws > 0:
                    be_needed = (fixed / margin_per_ws).quantize(Decimal("0.01"))
                    break_even: dict[str, object] = {
                        "status": "measured",
                        "metric_kind": "break_even_occupancy_on_contribution",
                        "variable_cost_per_workstation": str(variable_per_workstation),
                        "contribution_per_workstation": str(
                            margin_per_ws.quantize(Decimal("0.01"))),
                        "workstations_to_break_even": str(be_needed),
                        "occupancy_to_break_even": (
                            str((be_needed / capacity).quantize(Decimal("0.0001")))
                            if capacity else None),
                        "formula": "fixed monthly costs / (average contracted revenue per "
                                   "occupied sellable workstation - variable cost per "
                                   "workstation)",
                        "period": f"costs as supplied for one month; memberships active on "
                                  f"{as_of.isoformat()}",
                        "exclusions": ["variable rows supplied as monthly totals are not "
                                       "treated as a per-workstation cost"],
                    }
                else:
                    break_even = {
                        "status": "not_computed",
                        "reason": "the supplied variable cost per workstation is greater "
                                  "than or equal to the average contracted rate; no positive "
                                  "contribution exists to cover fixed costs"}
            else:
                break_even = {
                    "status": "not_computed",
                    "reason": "break-even not computed: no variable_per_workstation cost "
                              "row was supplied"}
            coverage = {
                "status": "measured",
                "metric_kind": "fixed_cost_coverage",
                "not_a_break_even": "This is fixed-cost coverage. It omits every variable "
                                    "cost supplied as a monthly total, so for a location "
                                    "with material variable costs the true break-even "
                                    "occupancy is higher. Supply a kind=variable_per_"
                                    "workstation row to compute break-even on "
                                    "contribution.",
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
                "break_even_on_contribution": break_even,
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
                            "Revenue is the contracted MRR of occupied units whose "
                            "inventory unit_type maps to the same bucket. A row is a "
                            "comparison of the two supplied labels, not a full product "
                            "P&L. Unassigned costs stay in the location total.",
                })
            product_mapping = {
                "cost_axis": "the product column on the operator's cost file",
                "revenue_axis": "the inventory unit_type of each occupied unit",
                "shared_resolver": "both labels pass through the same alias table; "
                                   "exact alias first, then a whole-token fallback",
                "unmapped_cost_labels": sorted(unmapped_cost_labels),
                "unmapped_unit_types": sorted(unmapped_unit_types),
                "note": "An unmapped label is reported, not guessed. Add it to the "
                        "operator's product column with a recognised name or keep it out "
                        "of product contribution.",
            }
        else:
            product_rows = []
            product_mapping = {
                "status": "not_measured",
                "reason": "the cost file has no product column"}
            unmapped_cost_labels = set()
            unmapped_unit_types = set()
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
        "variable_per_workstation_monthly": str(variable_per_workstation),
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
        "product_mapping": product_mapping,
        "problems": problems,
        "definitions": [
            "fixed_monthly = sum of cost rows whose kind is fixed",
            "variable_monthly = sum of cost rows whose kind is variable; these are "
            "this month's totals, not a per-workstation rate",
            "variable_per_workstation_monthly = sum of cost rows whose kind is "
            "variable_per_workstation; this is the only variable figure used in the "
            "break-even calculation",
            "workstations_to_cover_fixed_costs = fixed_monthly / average contracted "
            "revenue per occupied sellable workstation (fixed-cost coverage)",
            "workstations_to_break_even = fixed_monthly / (average contracted revenue "
            "per occupied sellable workstation - variable cost per workstation)",
            "average contracted revenue uses the same occupied sellable in-service "
            "pool as the occupancy dashboard, with complimentary contracted revenue "
            "excluded from the numerator and the workstation still in the denominator",
            "no rent, payroll, CAM, or software figure is filled in when absent",
        ],
    }
