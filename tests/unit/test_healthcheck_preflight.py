"""Preflight screening tests for the paid-engagement health check.

An engagement starts by receiving files from an operator, which is exactly when
a credentials file, a database dump, or a payment-card spreadsheet is most
likely to arrive. These tests pin the refusals, and pin the false-positive
guards that keep ordinary invoice numbers from being treated as card data.
"""

import pytest

from opencoworking.healthcheck import PreflightBlocked, run_health_check
from opencoworking.preflight import scan_directory

# Fixture credentials for these tests. They are assembled from parts and kept
# deliberately low-entropy: the preflight patterns are keyword-driven, so a
# low-entropy placeholder still exercises them, and the repository's own secret
# scan stays clean (storing a realistic-looking credential to prove credentials
# are caught is its own hazard).
FAKE_PEM_BLOCK = "-----BEGIN RSA " + "PRIVATE KEY-----"
FAKE_AWS_ID = "AKIA" + "IOSFODNN7EXAMPLE"
FAKE_AWS_BODY = "aaaaaaaa-" + "bbbb-cccc-dddd"
FAKE_PASSWORD = "hunter2-" + "do-not-share"
FAKE_SESSION_VALUE = "T0pSecret" + "Value123"

INVENTORY = ("unit_id,location_id,unit_type,capacity,sellable,out_of_service,list_price\n"
             "OF-1,LOC-1,office,4,true,false,1200\n")
MEMBERSHIPS = ("membership_id,company_id,location_id,product,unit_id,start_date,end_date,"
               "contracted_rate,status,complimentary\n"
               "M-1,C-1,LOC-1,private-office,OF-1,2026-01-01,,1200,active,\n")


def _write(path, name, text):
    (path / name).write_text(text, encoding="utf-8")
    return path / name


def _minimal_engagement(root):
    _write(root, "inventory.csv", INVENTORY)
    _write(root, "memberships.csv", MEMBERSHIPS)
    return root


class TestBlocksSecrets:
    def test_credentials_file_is_blocked(self, tmp_path):
        secret = chr(34) + FAKE_PASSWORD + chr(34)
        _write(tmp_path, "credentials.json", "{\"password\": " + secret + "}\n")
        result = scan_directory(tmp_path)
        assert not result.ok
        assert result.blocked[0].path == "credentials.json"
        codes = {f["code"] for f in result.blocked[0].findings}
        assert "sensitive_filename" in codes

    def test_cloud_key_in_a_csv_cell_is_blocked(self, tmp_path):
        _write(tmp_path, "notes.csv", f"id,note\n1,{FAKE_AWS_ID} was used\n")
        result = scan_directory(tmp_path)
        assert not result.ok
        assert "aws_access_key_id" in result.blocked[0].secret_patterns_hit

    def test_private_key_block_is_blocked(self, tmp_path):
        _write(tmp_path, "id_rsa.pem", FAKE_PEM_BLOCK + "\nMIIE\n")
        result = scan_directory(tmp_path)
        assert not result.ok
        codes = {f["code"] for f in result.blocked[0].findings}
        assert "blocked_file_type" in codes

    def test_database_dump_is_blocked(self, tmp_path):
        _write(tmp_path, "members.sql", "INSERT INTO members VALUES (1);\n")
        result = scan_directory(tmp_path)
        assert not result.ok
        assert any(f["code"] == "blocked_file_type" for f in result.blocked[0].findings)

    def test_aws_secret_assignment_is_blocked(self, tmp_path):
        _write(tmp_path, "config.csv",
               "key,value\n" + "aws_secret_access_key," + FAKE_AWS_BODY + "\n")
        result = scan_directory(tmp_path)
        assert not result.ok

    def test_oversized_file_is_blocked(self, tmp_path):
        big = tmp_path / "huge.csv"
        big.write_text("a,b\n" + "x" * 5000, encoding="utf-8")
        result = scan_directory(tmp_path, max_file_bytes=1000)
        assert not result.ok
        assert any("exceeds" in f["message"] for f in result.blocked[0].findings)


class TestBlocksRestrictedPersonalData:
    def test_payment_card_number_is_blocked(self, tmp_path):
        # 4111 1111 1111 1111 is Luhn-valid and therefore treated as card data.
        _write(tmp_path, "customers.csv", "company_id,card_number\nC-1,4111111111111111\n")
        result = scan_directory(tmp_path)
        assert not result.ok
        assert "payment_card_number" in result.blocked[0].restricted_columns

    def test_non_luhn_digit_string_is_not_card_data(self, tmp_path):
        # A long invoice reference must not be mistaken for a card number.
        _write(tmp_path, "invoices.csv",
               "invoice_id,amount,status\nINV-1234567890123457,450,paid\n")
        result = scan_directory(tmp_path)
        assert result.ok, [f.findings for f in result.blocked]

    def test_restricted_column_is_blocked(self, tmp_path):
        _write(tmp_path, "contacts.csv", "contact_id,ssn\nCT-1,123-45-6789\n")
        result = scan_directory(tmp_path)
        assert not result.ok
        assert "ssn" in result.blocked[0].restricted_columns

    def test_identifier_columns_warn_but_do_not_block(self, tmp_path):
        _write(tmp_path, "contacts.csv",
               "contact_id,first_name,email,phone,notes\n"
               "CT-1,Jordan,jordan@example.com,555-0101,asked for a corner office\n")
        result = scan_directory(tmp_path)
        assert result.ok
        check = result.files[0]
        assert check.status == "warning"
        assert {"email", "phone"} <= set(check.pii_columns)
        assert check.free_text_columns == ["notes"]

    def test_strict_policy_blocks_identifier_files(self, tmp_path):
        _write(tmp_path, "contacts.csv",
               "contact_id,email\nCT-1,jordan@example.com\n")
        result = scan_directory(tmp_path, policy="strict")
        assert not result.ok
        assert any(f["code"] == "pii_policy_strict" for f in result.blocked[0].findings)

    def test_email_shaped_values_in_unhinted_columns_are_flagged(self, tmp_path):
        _write(tmp_path, "notes.csv", "note_id,body\nN-1,write to ops@example.com\n")
        result = scan_directory(tmp_path)
        codes = {f["code"] for f in result.files[0].findings}
        assert "personal_data_values" in codes
        assert result.ok


class TestScanBehaviour:
    def test_missing_directory_raises(self, tmp_path):
        with pytest.raises(NotADirectoryError):
            scan_directory(tmp_path / "nope")

    def test_hidden_and_office_files_are_excluded(self, tmp_path):
        _minimal_engagement(tmp_path)
        _write(tmp_path, ".env", "SECRET=1\n")
        _write(tmp_path, "~$inventory.csv", "a,b\n1,2\n")
        result = scan_directory(tmp_path)
        assert sorted(f.path for f in result.files) == ["inventory.csv", "memberships.csv"]
        assert ".env" in result.excluded and "~$inventory.csv" in result.excluded

    def test_scan_never_modifies_inputs(self, tmp_path):
        _minimal_engagement(tmp_path)
        before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
        scan_directory(tmp_path)
        after = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
        assert before == after

    def test_paths_with_spaces_work(self, tmp_path):
        spaced = tmp_path / "client exports 2026"
        spaced.mkdir()
        _minimal_engagement(spaced)
        result = scan_directory(spaced)
        assert result.ok and len(result.files) == 2


class TestPreflightGateOnARun:
    def test_run_refuses_a_folder_with_secrets(self, tmp_path):
        _minimal_engagement(tmp_path)
        _write(tmp_path, "credentials.csv",
               "name,password\nsvc," + FAKE_SESSION_VALUE + "\n")
        with pytest.raises(PreflightBlocked) as excinfo:
            run_health_check(tmp_path, client="C", as_of=_date(), generated_at="now")
        assert [f.path for f in excinfo.value.result.blocked] == ["credentials.csv"]

    def test_allow_unsafe_records_the_override(self, tmp_path):
        from datetime import date
        _minimal_engagement(tmp_path)
        _write(tmp_path, "credentials.csv",
               "name,password\nsvc," + FAKE_SESSION_VALUE + "\n")
        bundle = run_health_check(tmp_path, client="C", as_of=date(2026, 7, 1),
                                  generated_at="2026-07-01T00:00:00+00:00",
                                  allow_unsafe=True)
        assert bundle["engagement"]["allow_unsafe"] is True
        assert bundle["preflight"]["blocking_count"] == 1
        assert any(item["type"] == "preflight_blocked" for item in bundle["limitations"])


def _date():
    from datetime import date
    return date(2026, 7, 1)
