import subprocess
import sys

import pytest

from opencoworking.cli import main
from opencoworking.ingest import IngestError, load_csv, load_table


@pytest.fixture()
def leads_csv(tmp_path):
    p = tmp_path / "my leads export.csv"  # path with spaces on purpose
    p.write_text(
        "lead_id,created_at,first_response_at,source,status\n"
        "L-1,2026-06-15 10:00,2026-06-15 10:20,Google Ads,contacted\n"
        "L-2,2026-06-16 09:00,,walk in,new\n",
        encoding="utf-8",
    )
    return p


class TestLoadCsv:
    def test_basic(self, leads_csv):
        table = load_csv(leads_csv)
        assert table.columns[0] == "lead_id"
        assert len(table.rows) == 2

    def test_missing_file(self, tmp_path):
        with pytest.raises(IngestError):
            load_csv(tmp_path / "nope.csv")

    def test_duplicate_headers_renamed(self, tmp_path):
        p = tmp_path / "d.csv"
        p.write_text("id,id,name\n1,2,x\n", encoding="utf-8")
        table = load_csv(p)
        assert table.columns == ["id", "id_2", "name"]
        assert table.warnings

    def test_ragged_row_padded(self, tmp_path):
        p = tmp_path / "r.csv"
        p.write_text("a,b,c\n1,2\n", encoding="utf-8")
        table = load_csv(p)
        assert table.rows[0] == {"a": "1", "b": "2", "c": ""}
        assert table.warnings

    def test_semicolon_delimiter(self, tmp_path):
        p = tmp_path / "s.csv"
        p.write_text("a;b\n1;2\n", encoding="utf-8")
        table = load_csv(p)
        assert table.rows[0] == {"a": "1", "b": "2"}

    def test_unsupported_extension(self, tmp_path):
        p = tmp_path / "x.parquet"
        p.write_text("", encoding="utf-8")
        with pytest.raises(IngestError):
            load_table(p)

    def test_bom(self, tmp_path):
        p = tmp_path / "bom.csv"
        p.write_bytes(b"\xef\xbb\xbfa,b\n1,2\n")
        assert load_csv(p).columns == ["a", "b"]


class TestCli:
    def test_inspect_json(self, leads_csv, capsys):
        assert main(["inspect", str(leads_csv), "--format", "json"]) == 0
        out = capsys.readouterr().out
        assert '"likely_entity": "leads"' in out

    def test_speed_to_lead(self, leads_csv, capsys):
        assert main(["speed-to-lead", "--leads", str(leads_csv), "--format", "json"]) == 0
        assert '"median_minutes": 20' in capsys.readouterr().out

    def test_quality_error_exit_code(self, tmp_path):
        p = tmp_path / "bad.csv"
        p.write_text("d\nnot-a-date\n", encoding="utf-8")
        assert main(["quality", str(p), "--date-columns", "d", "--format", "json"]) == 2

    def test_output_refuses_overwrite(self, leads_csv, tmp_path, capsys):
        dest = tmp_path / "report.md"
        dest.write_text("precious", encoding="utf-8")
        with pytest.raises(SystemExit):
            main(["sources", "--leads", str(leads_csv), "--output", str(dest)])
        assert dest.read_text(encoding="utf-8") == "precious"

    def test_redact_never_in_place(self, leads_csv):
        with pytest.raises(SystemExit):
            main(["redact", str(leads_csv), "--output", str(leads_csv)])

    def test_redact_roundtrip(self, tmp_path):
        src = tmp_path / "contacts.csv"
        src.write_text(
            "contact_id,first_name,last_name,email,phone\n"
            "C-1,Jane,Doe,jane@example.com,415-555-0134\n",
            encoding="utf-8",
        )
        dest = tmp_path / "contacts.redacted.csv"
        assert main(["redact", str(src), "--output", str(dest),
                     "--name-columns", "first_name,last_name"]) == 0
        text = dest.read_text(encoding="utf-8")
        assert "jane@example.com" not in text and "555-0134" not in text
        assert "Jane" not in text
        # Source untouched
        assert "jane@example.com" in src.read_text(encoding="utf-8")

    def test_module_entrypoint_help(self):
        r = subprocess.run([sys.executable, "-m", "opencoworking.cli", "--help"],
                           capture_output=True, text=True)
        assert r.returncode == 0 and "Deterministic analysis tools" in r.stdout
