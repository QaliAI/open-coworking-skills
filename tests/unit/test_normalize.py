from datetime import date
from decimal import Decimal

from opencoworking.normalize import (
    detect_currency,
    normalize_source,
    parse_date,
    parse_datetime,
    parse_money,
    sanitize_cell,
)


class TestParseDate:
    def test_iso(self):
        assert parse_date("2026-03-04") == date(2026, 3, 4)

    def test_iso_timestamp(self):
        assert parse_date("2026-03-04T10:15:00Z") == date(2026, 3, 4)

    def test_named_month(self):
        assert parse_date("4 Mar 2026") == date(2026, 3, 4)
        assert parse_date("March 4, 2026") == date(2026, 3, 4)

    def test_slash_month_first_default(self):
        assert parse_date("03/04/2026") == date(2026, 3, 4)

    def test_slash_day_first_flag(self):
        assert parse_date("03/04/2026", day_first=True) == date(2026, 4, 3)

    def test_unparseable_returns_none(self):
        assert parse_date("not a date") is None
        assert parse_date("") is None

    def test_unambiguous_dmy_falls_through(self):
        # 25 can't be a month, so day-first format matches even without flag.
        assert parse_date("25/12/2026") == date(2026, 12, 25)


class TestParseDatetime:
    def test_iso_z(self):
        dt = parse_datetime("2026-03-04T10:15:00Z")
        assert dt is not None and dt.hour == 10

    def test_space_format(self):
        dt = parse_datetime("2026-03-04 09:30:00")
        assert dt is not None and dt.minute == 30

    def test_bad(self):
        assert parse_datetime("soon") is None


class TestParseMoney:
    def test_plain(self):
        assert parse_money("450") == Decimal("450")

    def test_symbol_and_commas(self):
        assert parse_money("$1,200.50") == Decimal("1200.50")

    def test_european(self):
        assert parse_money("1.200,50") == Decimal("1200.50")

    def test_parens_negative(self):
        assert parse_money("(300)") == Decimal("-300")

    def test_trailing_code(self):
        assert parse_money("950 USD") == Decimal("950")

    def test_blank_and_junk(self):
        assert parse_money("") is None
        assert parse_money("TBD") is None

    def test_currency_detection(self):
        assert detect_currency("€100") == "EUR"
        assert detect_currency("100 GBP") == "GBP"
        assert detect_currency("100") is None


class TestNormalizeSource:
    def test_google_ads_variants(self):
        for raw in ("Google Ads", "adwords", "google ppc"):
            assert normalize_source(raw)[0] == "google-ads"

    def test_gbp_before_organic(self):
        assert normalize_source("Google Maps")[0] == "google-business-profile"
        assert normalize_source("GMB")[0] == "google-business-profile"

    def test_organic(self):
        assert normalize_source("google organic")[0] == "organic-search"

    def test_walk_in(self):
        assert normalize_source("Walk-In")[0] == "walk-in"
        assert normalize_source("walkin")[0] == "walk-in"

    def test_referral(self):
        assert normalize_source("Member Referral")[0] == "referral"

    def test_blank(self):
        assert normalize_source("  ") == ("unknown", "unknown")

    def test_unmapped_preserved(self):
        canonical, conf = normalize_source("Carrier Pigeon")
        assert conf == "unmapped"
        assert canonical == "carrier-pigeon"

    def test_extra_rules_win(self):
        canonical, conf = normalize_source("Pigeon", extra_rules=[("pigeon", "pigeon-post")])
        assert (canonical, conf) == ("pigeon-post", "exact")


class TestSanitizeCell:
    def test_formula_neutralized(self):
        assert sanitize_cell("=HYPERLINK('http://evil')") == "'=HYPERLINK('http://evil')"
        assert sanitize_cell("@SUM(A1)") == "'@SUM(A1)"

    def test_negative_number_untouched(self):
        assert sanitize_cell("-450.25") == "-450.25"

    def test_plain_text_untouched(self):
        assert sanitize_cell("Suite 210") == "Suite 210"
