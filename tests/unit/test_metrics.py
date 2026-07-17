from datetime import datetime
from decimal import Decimal

from opencoworking.metrics import (
    Unit,
    average_revenue_per_active_membership,
    business_minutes_between,
    financial_occupancy,
    logo_churn,
    office_occupancy,
    revenue_churn,
    revenue_per_sellable_workstation,
    workstation_occupancy,
)


def _u(uid, utype="office", cap=4, sellable=True, oos=False, occupied=False,
       comp=False, price=None, rev="0"):
    return Unit(uid, utype, cap, sellable, oos, occupied, comp,
                None if price is None else Decimal(price), Decimal(rev))


class TestOfficeOccupancy:
    def test_known_answer(self):
        # 4 sellable in-service offices, 3 occupied -> 75%
        units = [
            _u("A", occupied=True), _u("B", occupied=True), _u("C", occupied=True),
            _u("D"),
            _u("E", oos=True, occupied=False),      # excluded: out of service
            _u("F", sellable=False, occupied=True), # excluded: not sellable
            _u("G", utype="desk", occupied=True),   # excluded: not an office
        ]
        r = office_occupancy(units)
        assert r.value == Decimal("0.75")
        assert r.numerator == 3 and r.denominator == 4

    def test_comped_warning(self):
        units = [_u("A", occupied=True, comp=True), _u("B")]
        r = office_occupancy(units)
        assert r.value == Decimal("0.5")
        assert any("complimentary" in w for w in r.warnings)

    def test_zero_denominator(self):
        r = office_occupancy([_u("E", oos=True)])
        assert r.value is None
        assert r.warnings


class TestWorkstationOccupancy:
    def test_capacity_weighting(self):
        # Occupied: 6-cap office + 1-cap desk = 7; pool: 6+1+3 = 10 -> 70%
        units = [
            _u("A", cap=6, occupied=True),
            _u("B", utype="desk", cap=1, occupied=True),
            _u("C", cap=3),
        ]
        r = workstation_occupancy(units)
        assert r.value == Decimal("0.7")


class TestFinancialOccupancy:
    def test_known_answer_with_exclusions(self):
        units = [
            _u("A", occupied=True, price="1000", rev="800"),   # discounted
            _u("B", occupied=True, comp=True, price="1000", rev="0"),  # comped
            _u("C", price="1000"),                              # vacant
            _u("D", occupied=True, price=None, rev="500"),      # unpriced: excluded both sides
        ]
        r = financial_occupancy(units)
        # numerator 800 + 0, denominator 3000 -> 26.67%
        assert r.numerator == Decimal("800")
        assert r.denominator == Decimal("3000")
        assert r.value == Decimal("0.2667")
        assert any("no list price" in w for w in r.warnings)


class TestChurn:
    def test_logo_churn(self):
        r = logo_churn(3, 60, "2026-06")
        assert r.value == Decimal("0.05")

    def test_revenue_churn_gross(self):
        r = revenue_churn(Decimal("1500"), Decimal("30000"), "2026-06")
        assert r.value == Decimal("0.05")
        assert "gross" in r.formula


class TestBusinessMinutes:
    def test_same_day(self):
        # Tue 2026-07-14 10:00 -> 11:30 = 90 business minutes
        a = datetime(2026, 7, 14, 10, 0)
        b = datetime(2026, 7, 14, 11, 30)
        assert business_minutes_between(a, b) == 90

    def test_overnight(self):
        # Tue 16:30 -> Wed 09:45: 30 min Tue + 45 min Wed = 75
        a = datetime(2026, 7, 14, 16, 30)
        b = datetime(2026, 7, 15, 9, 45)
        assert business_minutes_between(a, b) == 75

    def test_over_weekend(self):
        # Fri 2026-07-17 16:00 -> Mon 2026-07-20 09:30: 60 + 30 = 90
        a = datetime(2026, 7, 17, 16, 0)
        b = datetime(2026, 7, 20, 9, 30)
        assert business_minutes_between(a, b) == 90

    def test_created_out_of_hours(self):
        # Created Sat, answered Mon 09:10 -> 10 business minutes
        a = datetime(2026, 7, 18, 14, 0)
        b = datetime(2026, 7, 20, 9, 10)
        assert business_minutes_between(a, b) == 10

    def test_reversed_is_zero(self):
        a = datetime(2026, 7, 14, 10, 0)
        assert business_minutes_between(a, a) == 0


class TestRevenueMetrics:
    def test_revpaw(self):
        units = [_u("A", cap=6), _u("B", cap=4, oos=True), _u("C", utype="desk", cap=10)]
        r = revenue_per_sellable_workstation(Decimal("8000"), units)
        assert r.denominator == Decimal("16")  # 6 + 10; OOS excluded
        assert r.value == Decimal("500")

    def test_arpm(self):
        r = average_revenue_per_active_membership(Decimal("9000"), 30)
        assert r.value == Decimal("300")
