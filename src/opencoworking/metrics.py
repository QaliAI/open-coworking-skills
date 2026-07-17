"""Coworking metric calculations with explicit formula contracts.

Coworking terminology is NOT standardized across operators or platforms.
Every function documents its exact numerator, denominator, and exclusions,
and returns a MetricResult carrying that contract so reports can print it.
Nothing here invents a value: when inputs are missing the result says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

ZERO = Decimal("0")


@dataclass
class MetricResult:
    """A calculated metric plus the contract that produced it."""

    name: str
    value: Decimal | None
    numerator: Decimal
    denominator: Decimal
    formula: str
    exclusions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": None if self.value is None else str(self.value),
            "numerator": str(self.numerator),
            "denominator": str(self.denominator),
            "formula": self.formula,
            "exclusions": self.exclusions,
            "warnings": self.warnings,
        }


def _ratio(name: str, num: Decimal, den: Decimal, formula: str,
           exclusions: list[str] | None = None,
           warnings: list[str] | None = None) -> MetricResult:
    value = None if den == 0 else (num / den).quantize(Decimal("0.0001"))
    w = list(warnings or [])
    if den == 0:
        w.append("Denominator is zero; metric undefined.")
    return MetricResult(name, value, num, den, formula, list(exclusions or []), w)


# --- Occupancy -------------------------------------------------------------

@dataclass
class Unit:
    """A sellable inventory unit as of the report date."""

    unit_id: str
    unit_type: str            # office | desk | workstation | room | ...
    capacity: int             # workstations contained
    sellable: bool
    out_of_service: bool
    occupied: bool            # has an active assignment
    complimentary: bool = False
    list_price: Decimal | None = None
    contracted_revenue: Decimal = ZERO


def office_occupancy(units: list[Unit], unit_types: tuple[str, ...] = ("office",)) -> MetricResult:
    """Occupied offices / sellable offices (count-based).

    Numerator: sellable, in-service units of the given types with an active
    assignment (complimentary assignments COUNT as occupied here — they consume
    the unit — but are reported separately as a warning).
    Denominator: sellable, in-service units of the given types.
    Excludes: out-of-service and non-sellable units.
    """
    pool = [u for u in units if u.unit_type in unit_types and u.sellable and not u.out_of_service]
    occupied = [u for u in pool if u.occupied]
    comped = [u for u in occupied if u.complimentary]
    warnings = []
    if comped:
        warnings.append(
            f"{len(comped)} occupied unit(s) are complimentary/internal; "
            "count-based occupancy includes them but they produce no revenue."
        )
    return _ratio(
        "office_occupancy",
        Decimal(len(occupied)),
        Decimal(len(pool)),
        "occupied sellable in-service offices / sellable in-service offices",
        exclusions=["out-of-service units", "non-sellable units"],
        warnings=warnings,
    )


def workstation_occupancy(units: list[Unit]) -> MetricResult:
    """Occupied workstation capacity / sellable workstation capacity.

    Numerator: sum of capacity of occupied, sellable, in-service units.
    Denominator: sum of capacity of sellable, in-service units.
    A 6-person office counts 6 workstations whether 1 or 6 people sit in it —
    this measures contracted inventory consumption, not attendance.
    """
    pool = [u for u in units if u.sellable and not u.out_of_service]
    num = Decimal(sum(u.capacity for u in pool if u.occupied))
    den = Decimal(sum(u.capacity for u in pool))
    return _ratio(
        "workstation_occupancy", num, den,
        "workstation capacity of occupied sellable in-service units / "
        "total sellable in-service workstation capacity",
        exclusions=["out-of-service units", "non-sellable units"],
    )


def financial_occupancy(units: list[Unit]) -> MetricResult:
    """Contracted recurring revenue / list-price potential of sellable inventory.

    Numerator: contracted monthly recurring revenue of occupied sellable
    in-service units (complimentary units contribute 0).
    Denominator: sum of list prices of ALL sellable in-service units.
    Units with no list price are excluded from BOTH sides and reported,
    because including them on one side only would bias the ratio.
    """
    pool = [u for u in units if u.sellable and not u.out_of_service]
    priced = [u for u in pool if u.list_price is not None]
    unpriced = [u for u in pool if u.list_price is None]
    num = sum((u.contracted_revenue for u in priced if u.occupied), ZERO)
    den = sum((u.list_price for u in priced), ZERO)  # type: ignore[misc]
    warnings = []
    if unpriced:
        warnings.append(
            f"{len(unpriced)} sellable unit(s) have no list price and are "
            "excluded from financial occupancy on both sides."
        )
    return _ratio(
        "financial_occupancy", num, den,
        "contracted recurring revenue of occupied priced units / "
        "list-price total of all priced sellable in-service units",
        exclusions=["out-of-service units", "non-sellable units",
                    "units without a list price (both sides)"],
        warnings=warnings,
    )


# --- Funnel ----------------------------------------------------------------

def conversion_rate(name: str, converted: int, total: int, stage_desc: str) -> MetricResult:
    """Simple stage conversion: converted / total, with explicit stage naming."""
    return _ratio(name, Decimal(converted), Decimal(total), stage_desc)


# --- Churn / retention -----------------------------------------------------

def logo_churn(canceled_members: int, members_at_start: int, period: str) -> MetricResult:
    """Memberships canceled during period / active memberships at period start.

    Count-based ("logo") churn. Excludes members who joined and canceled within
    the same period from the denominator (they were not active at start); the
    caller is responsible for that filtering and should disclose it.
    """
    return _ratio(
        "logo_churn", Decimal(canceled_members), Decimal(members_at_start),
        f"memberships canceled in {period} / active memberships at start of {period}",
        exclusions=["members who both joined and canceled inside the period "
                    "(not in the start-of-period denominator)"],
    )


def revenue_churn(mrr_lost: Decimal, mrr_at_start: Decimal, period: str) -> MetricResult:
    """Recurring revenue lost to cancellations+downgrades / MRR at period start.

    Gross revenue churn: expansion is NOT netted against losses. Report
    expansion separately to avoid hiding churn behind upsells.
    """
    return _ratio(
        "revenue_churn", mrr_lost, mrr_at_start,
        f"recurring revenue lost to cancellations and downgrades in {period} / "
        f"recurring revenue at start of {period} (gross; expansion reported separately)",
    )


# --- Speed to lead ---------------------------------------------------------

def business_minutes_between(
    start: datetime, end: datetime,
    open_hour: int = 9, close_hour: int = 17,
    workdays: tuple[int, ...] = (0, 1, 2, 3, 4),
) -> int:
    """Minutes between two datetimes counting only business hours.

    Both datetimes must be in the LOCATION's local time; callers convert
    time zones first. Hours outside [open_hour, close_hour) on workdays
    (Mon=0..Sun=6) do not count. If end <= start, returns 0.
    """
    if end <= start:
        return 0
    total = 0
    cursor = start
    while cursor.date() <= end.date():
        if cursor.weekday() in workdays:
            day_open = datetime.combine(cursor.date(), datetime.min.time()).replace(hour=open_hour)
            day_close = datetime.combine(cursor.date(), datetime.min.time()).replace(hour=close_hour)
            lo = max(cursor if cursor.date() == start.date() else day_open, day_open)
            hi = min(end if cursor.date() == end.date() else day_close, day_close)
            if hi > lo:
                total += int((hi - lo).total_seconds() // 60)
        cursor = datetime.combine(cursor.date() + timedelta(days=1), datetime.min.time())
    return total


# --- ARPM / RevPAW ---------------------------------------------------------

def revenue_per_sellable_workstation(
    recurring_revenue: Decimal, units: list[Unit]
) -> MetricResult:
    """Monthly recurring revenue / total sellable in-service workstation capacity."""
    den = Decimal(sum(u.capacity for u in units if u.sellable and not u.out_of_service))
    return _ratio(
        "revenue_per_sellable_workstation", recurring_revenue, den,
        "monthly recurring revenue / sellable in-service workstation capacity",
        exclusions=["out-of-service units", "non-sellable units",
                    "one-time revenue (bookings, day passes) unless caller includes it"],
    )


def average_revenue_per_active_membership(
    recurring_revenue: Decimal, active_memberships: int
) -> MetricResult:
    """Monthly recurring revenue / count of active memberships."""
    return _ratio(
        "average_revenue_per_active_membership",
        recurring_revenue, Decimal(active_memberships),
        "monthly recurring membership revenue / active memberships",
        exclusions=["one-time revenue", "canceled and paused memberships"],
    )


# --- Aging -----------------------------------------------------------------

def days_between(earlier: date, later: date) -> int:
    """Whole days from earlier to later (negative if reversed)."""
    return (later - earlier).days
