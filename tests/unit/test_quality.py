from opencoworking.quality import (
    check_blank_values,
    check_date_parseability,
    check_duplicates,
    check_required_columns,
    quality_score,
)


def test_required_columns():
    assert check_required_columns(["a", "b"], ["a", "c"])[0].severity == "error"
    assert check_required_columns(["a", "b"], ["a"]) == []


def test_blank_values():
    rows = [{"source": "web"}, {"source": ""}, {"source": "  "}]
    f = check_blank_values(rows, "source")[0]
    assert f.rows == [2, 3]
    assert "67%" in f.message


def test_duplicates_case_insensitive():
    rows = [
        {"email": "A@x.com"}, {"email": "b@x.com"}, {"email": "a@x.com"},
        {"email": ""},
    ]
    f = check_duplicates(rows, ["email"], "contact")[0]
    assert set(f.rows) == {1, 3}


def test_no_duplicates():
    assert check_duplicates([{"e": "a"}, {"e": "b"}], ["e"], "x") == []


def test_date_parseability_mixed_formats():
    rows = [{"d": "2026-01-05"}, {"d": "01/06/2026"}, {"d": "yesterday"}]
    findings = check_date_parseability(rows, "d")
    checks = {f.check for f in findings}
    assert "unparseable_dates" in checks and "mixed_date_formats" in checks


def test_quality_score_floor():
    from opencoworking.quality import Finding
    findings = [Finding("x", "error", "")] * 10
    assert quality_score(findings, 5)["score"] == 0
