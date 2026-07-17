from opencoworking.redact import Redactor, collect_names


class TestRedactor:
    def test_email_redacted_and_stable(self):
        r = Redactor(salt="test")
        a = r.redact_text("Contact jane.doe@example.com please")
        b = r.redact_text("jane.doe@example.com again")
        assert "jane.doe@example.com" not in a
        token = a.split()[1]
        assert token.startswith("[EMAIL-") and token in b

    def test_phone_redacted(self):
        r = Redactor(salt="test")
        out = r.redact_text("Call +1 (415) 555-0134 today")
        assert "555-0134" not in out and "[PHONE-" in out

    def test_invoice_number_not_eaten(self):
        r = Redactor(salt="test")
        out = r.redact_text("Invoice INV-2026-0042 due")
        assert "INV-2026-0042" in out

    def test_card_number_luhn(self):
        r = Redactor(salt="test")
        # 4539578763621486 passes Luhn (standard test number pattern)
        out = r.redact_text("card 4539578763621486 on file")
        assert "4539578763621486" not in out and "[CARD-" in out

    def test_non_luhn_digits_left(self):
        r = Redactor(salt="test")
        out = r.redact_text("tracking 1234567890123456 code")
        assert "1234567890123456" in out  # fails Luhn -> not a card

    def test_name_redaction(self):
        r = Redactor(salt="test", names=["Jane Doe"])
        out = r.redact_text("Jane Doe visited; JANE DOE signed.")
        assert "Jane" not in out and "[NAME-" in out

    def test_row_redaction_counts(self):
        r = Redactor(salt="test")
        row = {"email": "a@b.co", "note": "call 415-555-0134"}
        red = r.redact_row(row)
        assert "[EMAIL-" in red["email"] and "[PHONE-" in red["note"]
        assert r.replacements == 2


def test_collect_names():
    rows = [{"first": "Jane", "name": "Jane Doe"}, {"first": "", "name": "Bo Li"}]
    assert collect_names(rows, ["name"]) == ["Bo Li", "Jane Doe"]
