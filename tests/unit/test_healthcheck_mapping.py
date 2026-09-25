"""Mapping tests: identify entities, rename headers, refuse ambiguity.

The health check is only as honest as its mapping step. These tests pin three
properties that make the rest of the report trustworthy:

* the canonical column sets never drift from ``schemas/coworking.schema.json``;
* every alias is a real, normalised spelling of a canonical column;
* anything ambiguous is refused and reported, never silently chosen.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from opencoworking.healthcheck import (
    CANONICAL_COLUMNS,
    COLUMN_ALIASES,
    REQUIRED_COLUMNS,
    discover_inputs,
    normalize_columns,
    run_health_check,
)
from opencoworking.ingest import Table, load_csv
from opencoworking.preflight import normalize_column

REPO = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((REPO / "schemas" / "coworking.schema.json").read_text(encoding="utf-8"))
AS_OF = date(2026, 7, 1)

# schema $defs names are singular; the engine's entity keys are the export names.
SCHEMA_TO_ENTITY = {
    "location": "locations", "inventory_unit": "inventory", "contact": "contacts",
    "company": "companies", "lead": "leads", "deal": "deals", "tour": "tours",
    "membership": "memberships", "member": "members", "invoice": "invoices",
    "payment": "payments", "room_booking": "room_bookings", "event": "events",
    "review": "reviews", "virtual_office_partner": "virtual_office_partners",
}


class TestSchemaAlignment:
    def test_canonical_columns_match_the_schema(self):
        for def_name, entity in SCHEMA_TO_ENTITY.items():
            expected = list(SCHEMA["$defs"][def_name]["properties"])
            assert CANONICAL_COLUMNS[entity] == expected, entity

    def test_required_columns_match_the_schema(self):
        for def_name, entity in SCHEMA_TO_ENTITY.items():
            expected = list(SCHEMA["$defs"][def_name].get("required", []))
            assert REQUIRED_COLUMNS[entity] == expected, entity

    def test_entity_signatures_cover_the_analysed_entities(self):
        from opencoworking.analyze import ENTITY_SIGNATURES

        assert set(ENTITY_SIGNATURES) <= set(CANONICAL_COLUMNS)
        # events and reviews have no column signature on purpose: nothing in
        # the health check consumes them, so they stay un-identified context.
        assert set(CANONICAL_COLUMNS) - set(ENTITY_SIGNATURES) == {"events", "reviews"}

    def test_aliases_point_at_real_canonical_columns(self):
        for entity, aliases in COLUMN_ALIASES.items():
            canonical = set(CANONICAL_COLUMNS[entity])
            for alias, target in aliases.items():
                assert normalize_column(alias) == alias, (entity, alias)
                assert target in canonical, (entity, alias, target)
                assert alias not in canonical, (entity, alias)


class TestColumnRenaming:
    def test_hubspot_style_headers_are_renamed_and_logged(self):
        table = Table("crm.csv", ["Deal ID", "Deal Stage", "Amount", "Deal Owner",
                                  "Last Activity Date", "Company ID"],
                      [{"Deal ID": "D-1", "Deal Stage": "proposal", "Amount": "1,400",
                        "Deal Owner": "casey", "Last Activity Date": "2026-06-20",
                        "Company ID": "C-1"}])
        mapped, renames, unmapped, ambiguous = normalize_columns(table, "deals")
        assert renames == {"Deal ID": "deal_id", "Deal Stage": "stage",
                           "Amount": "expected_value", "Deal Owner": "owner",
                           "Last Activity Date": "updated_at", "Company ID": "company_id"}
        assert unmapped == [] and ambiguous == []
        assert mapped.rows[0]["stage"] == "proposal"
        assert mapped.rows[0]["expected_value"] == "1,400"

    def test_nexudus_style_price_and_contract_headers(self):
        table = Table("contracts.csv",
                      ["Membership ID", "Account ID", "Contract Price", "Tariff Price",
                       "Contract Start", "Membership Status", "Product Type"],
                      [{"Membership ID": "M-1", "Account ID": "C-1",
                        "Contract Price": "1300", "Tariff Price": "1400",
                        "Contract Start": "2025-09-01", "Membership Status": "active",
                        "Product Type": "private-office"}])
        mapped, renames, unmapped, ambiguous = normalize_columns(table, "memberships")
        assert renames["Contract Price"] == "contracted_rate"
        assert renames["Tariff Price"] == "list_rate"
        assert renames["Contract Start"] == "start_date"
        assert renames["Membership Status"] == "status"
        assert unmapped == [] and ambiguous == []

    def test_unknown_headers_are_listed_not_guessed(self):
        table = Table("weird.csv", ["deal_id", "stage", "vibe_score", "account_manager_note"],
                      [{"deal_id": "D-1", "stage": "won", "vibe_score": "9",
                        "account_manager_note": "great chat"}])
        _, renames, unmapped, ambiguous = normalize_columns(table, "deals")
        assert renames == {"deal_id": "deal_id", "stage": "stage"}
        assert unmapped == ["vibe_score", "account_manager_note"]
        assert ambiguous == []

    def test_two_columns_for_one_target_are_refused(self):
        table = Table("deals.csv", ["deal_id", "stage", "Deal Stage"],
                      [{"deal_id": "D-1", "stage": "won", "Deal Stage": "proposal"}])
        _, renames, _, ambiguous = normalize_columns(table, "deals")
        assert "stage" not in renames.values()
        assert ambiguous and ambiguous[0]["canonical_column"] == "stage"
        assert sorted(ambiguous[0]["source_columns"]) == ["Deal Stage", "stage"]


class TestEntityIdentification:
    def test_filenames_are_ignored(self, tmp_path):
        (tmp_path / "leads.csv").write_text(
            "deal_id,company_id,stage,expected_value\nD-1,C-1,won,1400\n", encoding="utf-8")
        _, mapped, _ = discover_inputs(tmp_path)
        assert mapped[0].role == "deals"
        assert mapped[0].identification == "column signature"

    def test_unidentified_file_becomes_context_only(self, tmp_path):
        (tmp_path / "reviews.csv").write_text(
            "review_id,platform,rating,text\nR-1,google,5,nice space\n", encoding="utf-8")
        (tmp_path / "mystery.csv").write_text("alpha,beta\n1,2\n", encoding="utf-8")
        _, mapped, _ = discover_inputs(tmp_path)
        mystery = next(m for m in mapped if m.source == "mystery.csv")
        assert mystery.role == "(unidentified)" and mystery.context_only
        assert any("column signature did not match" in n for n in mystery.notes)

    def test_manual_override_wins(self, tmp_path):
        (tmp_path / "export-1.csv").write_text(
            "deal_id,company_id,stage,expected_value\nD-1,C-1,won,1400\n", encoding="utf-8")
        _, mapped, _ = discover_inputs(tmp_path, overrides={"export-1.csv": "leads"})
        assert mapped[0].role == "leads"
        assert mapped[0].identification == "manual override"

    def test_unknown_override_entity_is_an_error(self, tmp_path):
        (tmp_path / "export-1.csv").write_text("deal_id,stage\nD-1,won\n", encoding="utf-8")
        with pytest.raises(ValueError):
            discover_inputs(tmp_path, overrides={"export-1.csv": "unicorns"})

    def test_partial_signature_is_flagged_as_weak(self, tmp_path):
        (tmp_path / "maybe-leads.csv").write_text(
            "lead_id,source\nL-1,google\n", encoding="utf-8")
        _, mapped, _ = discover_inputs(tmp_path)
        assert mapped[0].entity_confidence == pytest.approx(0.5)
        assert any("weak signature match" in n for n in mapped[0].notes)


class TestAmbiguityAndMissingInputs:
    def test_two_files_for_one_role_are_refused(self, tmp_path):
        (tmp_path / "deals-a.csv").write_text(
            "deal_id,stage,expected_value\nD-1,won,1400\n", encoding="utf-8")
        (tmp_path / "deals-b.csv").write_text(
            "deal_id,stage,expected_value\nD-2,lost,900\n", encoding="utf-8")
        _, _, ambiguities = discover_inputs(tmp_path)
        assert len(ambiguities) == 1
        assert ambiguities[0]["type"] == "duplicate_role"
        assert "--map" in ambiguities[0]["resolution"]
        bundle = run_health_check(tmp_path, client="C", as_of=AS_OF,
                                  generated_at="2026-07-01T00:00:00+00:00")
        # Neither file is used, so the pipeline is honestly not measurable.
        assert any(item["module"] == "pipeline" for item in bundle["not_measured"])
        assert "pipeline" not in bundle["modules"]

    def test_map_resolves_a_duplicate_role(self, tmp_path):
        (tmp_path / "deals-a.csv").write_text(
            "deal_id,stage,expected_value\nD-1,won,1400\n", encoding="utf-8")
        (tmp_path / "deals-b.csv").write_text(
            "deal_id,stage,expected_value\nD-2,lost,900\n", encoding="utf-8")
        bundle = run_health_check(
            tmp_path, client="C", as_of=AS_OF, generated_at="2026-07-01T00:00:00+00:00",
            overrides={"deals-a.csv": "deals"})
        assert bundle["metrics"]["pipeline.deal_count"] == "1"
        superseded = [f for f in bundle["inputs"]["files"] if f["superseded_by"]]
        assert [f["source"] for f in superseded] == ["deals-b.csv"]
        assert any(item["type"] == "superseded_file" for item in bundle["limitations"])

    def test_missing_required_column_makes_a_file_unusable(self, tmp_path):
        (tmp_path / "memberships.csv").write_text(
            "membership_id,company_id,product,contracted_rate,unit_id\n"
            "M-1,C-1,private-office,1200,OF-1\n", encoding="utf-8")
        bundle = run_health_check(tmp_path, client="C", as_of=AS_OF,
                                  generated_at="2026-07-01T00:00:00+00:00")
        unusable = bundle["inputs"]["unusable"]
        assert unusable and unusable[0]["source"] == "memberships.csv"
        assert sorted(unusable[0]["missing_required"]) == ["start_date", "status"]
        assert any(item["type"] == "unusable_file" for item in bundle["limitations"])


class TestMappingAgainstTheBundledDemo:
    def test_every_demo_file_is_identified_exactly(self):
        data = REPO / "examples" / "synthetic-space" / "data"
        _, mapped, ambiguities = discover_inputs(data)
        assert ambiguities == []
        for item in mapped:
            assert item.missing_required == [], item.source
            assert item.unmapped_columns == [], item.source
            assert item.ambiguous_columns == [], item.source
            if item.source in {"events.csv", "reviews.csv"}:
                # No signature exists for these; they are context, not inputs.
                assert item.role == "(unidentified)" and item.context_only
            else:
                assert item.entity_confidence == 1.0, (item.source, item.entity_confidence)

    def test_renames_are_only_applied_when_needed(self):
        # Canonical files must be passed through untouched - no silent renames.
        table = load_csv(REPO / "examples" / "synthetic-space" / "data" / "memberships.csv")
        mapped, renames, unmapped, ambiguous = normalize_columns(table, "memberships")
        assert renames == {c: c for c in table.columns}
        assert unmapped == [] and ambiguous == []
        assert mapped.rows == table.rows
