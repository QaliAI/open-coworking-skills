"""Regression tests for defects found in the 2026-07-18 adversarial audit.

Each test reproduces a confirmed vulnerability or silent-corruption bug and
must keep failing loudly if the fix regresses.
"""

import pytest

from opencoworking.cli import main
from opencoworking.ingest import IngestError, load_csv


class TestEmbeddedNewlines:
    """AUDIT: splitlines()-based parsing destroyed newlines inside quoted
    fields with no warning (silent data corruption)."""

    def test_quoted_newline_preserved(self, tmp_path):
        p = tmp_path / "notes.csv"
        p.write_bytes(b'lead_id,notes\nL-1,"line one\nline two"\nL-2,plain\n')
        t = load_csv(p)
        assert len(t.rows) == 2
        assert t.rows[0]["notes"] == "line one\nline two"

    def test_crlf_inside_quotes(self, tmp_path):
        p = tmp_path / "notes.csv"
        p.write_bytes(b'a,b\n"x\r\ny",2\n')
        t = load_csv(p)
        assert t.rows[0]["a"] == "x\r\ny" or t.rows[0]["a"] == "x\ny"


class TestOversizedFields:
    """AUDIT: fields over csv's 128 KiB default raised a raw _csv.Error."""

    def test_multi_megabyte_field_loads(self, tmp_path):
        p = tmp_path / "big.csv"
        p.write_text("a,b\n" + "x" * 1_000_000 + ",2\n", encoding="utf-8")
        t = load_csv(p)
        assert len(t.rows) == 1
        assert len(t.rows[0]["a"]) == 1_000_000

    def test_absurd_field_is_structured_error(self, tmp_path):
        p = tmp_path / "huge.csv"
        p.write_text("a,b\n" + "x" * (33 * 1024 * 1024) + ",2\n", encoding="utf-8")
        with pytest.raises(IngestError):
            load_csv(p)


class TestRedactFormulaInjection:
    """AUDIT: redacted output CSV preserved executable spreadsheet formulas -
    the one file most likely to be opened in Excel by a third party."""

    def test_formula_neutralized_in_redacted_output(self, tmp_path):
        src = tmp_path / "inj.csv"
        src.write_text(
            'contact_id,first_name,email,notes\n'
            'C-1,Eve,eve@example.com,"=HYPERLINK(""http://evil.example"",""x"")"\n',
            encoding="utf-8",
        )
        dest = tmp_path / "inj.redacted.csv"
        assert main(["redact", str(src), "--output", str(dest),
                     "--name-columns", "first_name"]) == 0
        out = load_csv(dest)
        cell = out.rows[0]["notes"]
        assert cell.startswith("'="), f"formula not neutralized: {cell!r}"
        # And negative numbers must survive untouched.
        src2 = tmp_path / "neg.csv"
        src2.write_text("invoice_id,amount\nI-1,-450.25\n", encoding="utf-8")
        dest2 = tmp_path / "neg.redacted.csv"
        assert main(["redact", str(src2), "--output", str(dest2)]) == 0
        assert load_csv(dest2).rows[0]["amount"] == "-450.25"


class TestInvalidEncoding:
    def test_undecodable_bytes_are_structured_error(self, tmp_path):
        p = tmp_path / "bad.csv"
        p.write_bytes(b"a,b\n\xff\xfe\x9d,2\n")
        with pytest.raises(IngestError):
            load_csv(p)
