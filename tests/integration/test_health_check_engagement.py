"""End-to-end verification of the sample health-check engagement.

The committed sample is the artifact a consultant shows before anyone pays, so
it has to be provably reproducible: this test re-runs the documented command,
checks the numbers against hand-computed values, and fails if the committed
report drifts by a single byte (output paths aside).

Expected values come from the same independent source of truth as the rest of
the repository: the "answer key" dataset's own answer key
(``tests/fixtures/synthetic_expected.json``) plus literal hand math recorded
here for the health-check-specific numbers.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from opencoworking.ingest import load_csv

REPO = Path(__file__).resolve().parents[2]
ENGAGEMENT = REPO / "examples" / "health-check-engagement"
CLIENT_EXPORT = ENGAGEMENT / "client-export"
SAMPLE = ENGAGEMENT / "reports" / "northstar-demo"
DEMO_DATA = REPO / "examples" / "synthetic-space" / "data"
EXPECTED = json.loads(
    (REPO / "tests" / "fixtures" / "synthetic_expected.json").read_text(encoding="utf-8"))
AS_OF = "2026-07-01"
GENERATED_AT = "2026-07-21T00:00:00+00:00"
REVIEWER = "Sample Reviewer (open-source demo)"
FINALIZED_AT = "2026-07-22T09:00:00+00:00"

# Hand-computed from the literal rows in the sample export (see the answer key
# for occupancy/leakage/funnel/speed values; the churn and forecast numbers are
# derived here from memberships.csv at the 2026-07-01 as-of date).
HAND_COMPUTED_METRICS = {
    "occupancy.office.numerator": "5",
    "occupancy.office.denominator": "7",
    "occupancy.workstation.numerator": "38",
    "occupancy.workstation.denominator": "66",
    "occupancy.financial.numerator": "11785",
    "occupancy.financial.denominator": "18500",
    "leakage.active_memberships_without_recent_invoice.count": "3",
    "leakage.active_memberships_without_recent_invoice.monthly_amount_at_risk": "2088",
    "leakage.failed_or_overdue_invoices.count": "2",
    "leakage.failed_or_overdue_invoices.amount_outstanding": "2350",
    "leakage.out_of_service_inventory.monthly_list_value_blocked": "1400",
    "leakage.unfollowed_leads.count": "3",
    "leakage.completed_tours_without_next_action.count": "2",
    "leakage.won_deals_without_membership.count": "1",
    "pipeline.deal_count": "12",
    "pipeline.stale_deals.count": "2",
    "pipeline.duplicate_open_deals.count": "1",
    "speed_to_lead.responded_leads": "19",
    "speed_to_lead.leads_without_response": "3",
    "speed_to_lead.median_minutes": "30",
    "speed_to_lead.p90_minutes": "90",
    "speed_to_lead.max_minutes": "220",
    "funnel.counts.leads": "22",
    "funnel.counts.leads_with_tour": "9",
    "funnel.counts.tours_completed": "5",
    "funnel.counts.tour_no_shows": "2",
    "funnel.rates.lead_to_tour": "0.4091",
    "funnel.rates.tour_show_rate": "0.7143",
    "collections.outstanding_total": "2350",
    "collections.queue_size": "2",
    # Churn window 2026-06-01..2026-07-01: base 17 memberships, M-014 canceled
    # on 06-15 (760), M-011 excluded as active-past-end-date. Base MRR 13246.
    "churn.base_memberships": "17",
    "churn.canceled_memberships": "1",
    "churn.base_mrr": "13246",
    "churn.lost_mrr": "760",
    "churn.logo_churn": "0.0588",
    "churn.revenue_churn": "0.0574",
    # Contracted forward view: pool 66, 39 at 30/60 days, 29 at 90/180 days;
    # the only departure inside 90 days is the 3,400/month suite M-005.
    "forecast.h30.occupied": "39",
    "forecast.h90.occupied": "29",
    "forecast.h180.occupied": "29",
    "forecast.departures_by_90d": "M-005",
    "pricing.deep_discount_count": "1",
    "locations.count": "2",
    "renewals.agreements_in_window": "5",
}


def _run_health_check(output: Path, *extra: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "opencoworking.cli", "health-check",
           "--input", "examples/health-check-engagement/client-export",
           "--output", str(output),
           "--client", "Northstar Coworking Demo",
           "--as-of", AS_OF, "--generated-at", GENERATED_AT, *extra]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)


def _normalize(text: str, output_dir: Path | None = None) -> str:
    """Drop the one legitimately run-specific value: the output directory."""
    return re.sub(r"--output\s+\S+", "--output <OUT>", text)


class TestSampleExport:
    def test_committed_export_matches_the_bundled_synthetic_operator(self):
        """The sample must stay content-identical to the demo dataset it documents.

        Compared with line endings normalized: the repository stores text as LF
        and the engine reads exports as text, so a CRLF working tree (Windows)
        and an LF checkout (CI) describe the same engagement.
        """
        for source in sorted(DEMO_DATA.glob("*.csv")):
            copy = CLIENT_EXPORT / source.name
            assert copy.is_file(), f"missing sample export: {source.name}"
            assert (copy.read_bytes().replace(b"\r\n", b"\n")
                    == source.read_bytes().replace(b"\r\n", b"\n")), (
                f"{source.name} drifted; re-copy examples/synthetic-space/data into the "
                "sample engagement and regenerate the committed reports")

    def test_sample_contains_no_real_looking_pii(self):
        for row in load_csv(CLIENT_EXPORT / "contacts.csv").rows:
            assert row["email"].lower().endswith(".example")
            assert row["phone"].startswith("555-01")


class TestRunOnSyntheticOperator:
    def test_command_succeeds_and_writes_the_engagement(self, tmp_path):
        result = _run_health_check(tmp_path, "--force")
        assert result.returncode == 0, result.stderr
        for name in ("report.html", "bundle.json", "preflight.json",
                     "REVIEW_CHECKLIST.md", "engagement.json"):
            assert (tmp_path / name).is_file(), name

    def test_every_headline_number_matches_hand_computation(self, tmp_path):
        assert _run_health_check(tmp_path, "--force").returncode == 0
        bundle = json.loads((tmp_path / "bundle.json").read_text(encoding="utf-8"))
        metrics = bundle["metrics"]
        for key, expected in HAND_COMPUTED_METRICS.items():
            assert metrics.get(key) == expected, (key, metrics.get(key), expected)

    def test_answer_key_values_agree_with_the_shared_fixtures(self, tmp_path):
        assert _run_health_check(tmp_path, "--force").returncode == 0
        metrics = json.loads((tmp_path / "bundle.json").read_text(encoding="utf-8"))["metrics"]
        assert metrics["occupancy.office.value"] == EXPECTED["occupancy"]["office_occupancy"]["value"]
        assert (metrics["occupancy.financial.value"]
                == EXPECTED["occupancy"]["financial_occupancy"]["value"])
        assert metrics["funnel.rates.tour_show_rate"] == EXPECTED["funnel"]["tour_show_rate"]
        assert metrics["speed_to_lead.median_minutes"] == "30"

    def test_no_member_identifier_survives_into_any_artifact(self, tmp_path):
        assert _run_health_check(tmp_path, "--force").returncode == 0
        written = "\n".join(p.read_text(encoding="utf-8")
                            for p in sorted(tmp_path.iterdir()) if p.is_file())
        for row in load_csv(CLIENT_EXPORT / "contacts.csv").rows:
            assert row["email"].lower() not in written.lower()
            assert row["phone"] not in written
            assert f"{row['first_name']} {row['last_name']}" not in written
        for company in load_csv(CLIENT_EXPORT / "companies.csv").rows:
            assert company["name"] not in written
        # The duplicate-contact finding cites the shared email in the engine;
        # the engagement artifacts must carry a pseudonym instead.
        assert "[EMAIL-" in written


class TestCommittedSampleIsReproducible:
    def test_draft_report_matches_a_fresh_run(self, tmp_path):
        assert _run_health_check(tmp_path, "--force").returncode == 0
        for name in ("report.html", "REVIEW_CHECKLIST.md", "engagement.json"):
            fresh = _normalize((tmp_path / name).read_text(encoding="utf-8"), tmp_path)
            committed = _normalize((SAMPLE / name).read_text(encoding="utf-8"), SAMPLE)
            assert fresh == committed, (
                f"{name} drifted from the committed sample; regenerate the sample with "
                "the command in examples/health-check-engagement/README.md")

    def test_committed_final_report_matches_a_fresh_finalize(self, tmp_path):
        assert _run_health_check(tmp_path, "--force").returncode == 0
        cmd = [sys.executable, "-m", "opencoworking.cli", "health-check-finalize",
               "--engagement", str(tmp_path), "--reviewer", REVIEWER,
               "--notes", "Synthetic dataset; checklist walked through to demonstrate "
                          "release.", "--at", FINALIZED_AT]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
        assert result.returncode == 0, result.stderr
        fresh = (tmp_path / "report.final.html").read_text(encoding="utf-8")
        committed = (SAMPLE / "report.final.html").read_text(encoding="utf-8")
        assert fresh == committed, "the committed finalized report drifted"
        assert "DRAFT REPORT" not in committed
        assert REVIEWER in committed


class TestCommittedReportQuality:
    @pytest.fixture(scope="class")
    def report(self):
        return (SAMPLE / "report.html").read_text(encoding="utf-8")

    def test_draft_reports_are_labelled_for_review(self, report):
        assert "DRAFT REPORT — REVIEW REQUIRED" in report
        checklist = (SAMPLE / "REVIEW_CHECKLIST.md").read_text(encoding="utf-8")
        assert "review required" in checklist.lower()
        assert "health-check-finalize" in checklist
        final = (SAMPLE / "report.final.html").read_text(encoding="utf-8")
        assert "DRAFT REPORT" not in final

    def test_all_required_sections_are_present(self, report):
        for heading in ("Executive summary", "Data quality and data handling", "Occupancy",
                        "Revenue leakage", "Sales pipeline", "Speed to lead",
                        "Tour conversion", "Collections and churn", "Top 5 opportunities",
                        "90-day action plan", "Methodology and formulas",
                        "Data limitations"):
            assert heading in report, heading

    def test_classification_and_confidence_contracts_are_visible(self, report):
        for tag in ("FACT", "CALCULATION", "INFERENCE", "RECOMMENDATION"):
            assert tag in report, tag
        for label in ("Data used", "Calculation", "Confidence", "Limitation"):
            assert label in report, label

    def test_no_identification_of_a_human(self, report):
        assert not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(com|net|org|io|example)",
                             report)
        assert "555-01" not in report
        assert not re.search(r"\b(jordan|priya|reyes|natarajan)\b", report, re.I)

    def test_print_styles_are_present(self, report):
        assert "@page{size:A4" in report.replace(" ", "")
        assert "@media print" in report
        assert "break-inside:avoid" in report

    def test_no_fake_causality_language(self, report):
        lowered = report.lower()
        for phrase in ("caused by", "as a result of", "because of the", "led to a",
                       "guaranteed", "we will increase revenue"):
            assert phrase not in lowered, phrase
        assert "no causality is claimed" in lowered

    def test_limitations_and_review_gate_are_stated(self, report):
        # Every module ran for this client, and the report says so explicitly
        # rather than leaving the reader to infer it from missing sections.
        assert "Every diagnostic whose inputs exist ran in this engagement" in report
        assert "no legal, tax, or compliance conclusions" in report.lower()
        assert "not sent to anyone" in report.lower() or "nothing was sent" in report.lower()
        assert "File not identified" in report  # events.csv / reviews.csv
        assert "Context only (not analysed)" in report  # members.csv


class TestEngagementHygieneViaCli:
    def test_preflight_refusal_exits_without_analysing(self, tmp_path):
        client = tmp_path / "client-export"
        client.mkdir()
        (client / "inventory.csv").write_text(
            "unit_id,location_id,unit_type,capacity\nOF-1,LOC-1,office,4\n", encoding="utf-8")
        # Assembled so that no contiguous credential-shaped literal exists in
        # the repository (secret scanners read source text).
        fake_key = "sk_live_" + "51H8xQ2eZvKYlo2C"
        (client / "credentials.csv").write_text(
            "service,api_key\nhubspot," + fake_key + "\n", encoding="utf-8")
        out = tmp_path / "out"
        result = subprocess.run(
            [sys.executable, "-m", "opencoworking.cli", "health-check",
             "--input", str(client), "--output", str(out),
             "--client", "C", "--as-of", AS_OF],
            capture_output=True, text=True, cwd=REPO)
        assert result.returncode == 2
        assert "refused by preflight" in result.stdout
        assert not out.exists(), "a refused engagement must not write artifacts"

    def test_ambiguous_role_can_be_resolved_with_map(self, tmp_path):
        client = tmp_path / "client-export"
        client.mkdir()
        (client / "inventory.csv").write_text(
            "unit_id,location_id,unit_type,capacity,sellable,out_of_service,list_price\n"
            "OF-1,LOC-1,office,4,true,false,1200\n", encoding="utf-8")
        (client / "memberships.csv").write_text(
            "membership_id,company_id,location_id,product,unit_id,start_date,end_date,"
            "contracted_rate,status,complimentary\n"
            "M-1,C-1,LOC-1,private-office,OF-1,2026-01-01,,1200,active,\n", encoding="utf-8")
        # Two files that both look like a deals export.
        for name in ("deals-crm.csv", "deals-wms.csv"):
            (client / name).write_text(
                "deal_id,company_id,stage,expected_value,updated_at\n"
                f"D-{name[-7:-4]},C-1,won,1400,2026-06-25\n", encoding="utf-8")
        out = tmp_path / "out"
        unresolved = subprocess.run(
            [sys.executable, "-m", "opencoworking.cli", "health-check",
             "--input", str(client), "--output", str(out),
             "--client", "C", "--as-of", AS_OF],
            capture_output=True, text=True, cwd=REPO)
        assert unresolved.returncode == 0
        bundle = json.loads((out / "bundle.json").read_text(encoding="utf-8"))
        assert "pipeline" not in bundle["modules"]

        resolved = subprocess.run(
            [sys.executable, "-m", "opencoworking.cli", "health-check",
             "--input", str(client), "--output", str(out),
             "--client", "C", "--as-of", AS_OF, "--map", "deals-crm.csv=deals", "--force"],
            capture_output=True, text=True, cwd=REPO)
        assert resolved.returncode == 0, resolved.stderr
        bundle = json.loads((out / "bundle.json").read_text(encoding="utf-8"))
        assert bundle["metrics"]["pipeline.deal_count"] == "1"
        assert bundle["metrics"]["inputs.file_count"] == "4"


class TestRepositorySafeguards:
    def test_client_engagements_are_git_ignored(self):
        root_ignore = (REPO / ".gitignore").read_text(encoding="utf-8")
        assert "engagements/*" in root_ignore
        assert "!engagements/README.md" in root_ignore
        assert (REPO / "engagements" / "README.md").is_file()

    def test_no_client_export_is_tracked_by_git(self):
        tracked = subprocess.run(["git", "ls-files", "engagements"], capture_output=True,
                                 text=True, cwd=REPO)
        if tracked.returncode != 0:  # pragma: no cover - git unavailable
            pytest.skip("git is not available")
        files = [line for line in tracked.stdout.splitlines() if line.strip()]
        assert files in ([], ["engagements/README.md"]), files
        assert not any(f.lower().endswith((".csv", ".xlsx", ".tsv")) for f in files)

    def test_sample_engagement_is_synthetic_only(self):
        """Any committed export inside examples/ must carry the synthetic markers."""
        for path in (REPO / "examples").rglob("*.csv"):
            if "sample-outputs" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if "@" in text:
                assert ".example" in text.lower() or "example.com" in text.lower(), path
