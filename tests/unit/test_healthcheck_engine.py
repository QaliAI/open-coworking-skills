"""Health-check engine tests: composition, disclosure, prioritisation, report.

These tests pin the properties that make the deliverable sellable:

* missing inputs become NOT MEASURABLE with a reason, never a number;
* churn arithmetic follows the printed definition (hand-computed here);
* the opportunity ranking rule is deterministic and never sums unlike amounts;
* the rendered report is draft, escaped, and free of personal identifiers.
"""

import json
from datetime import date
from pathlib import Path

import pytest

from opencoworking.healthcheck import (
    churn_window,
    run_health_check,
)
from opencoworking.healthcheck_report import (
    finalize_engagement,
    render_health_check,
    write_engagement,
)
from opencoworking.ingest import Table, load_csv

REPO = Path(__file__).resolve().parents[2]
DEMO = REPO / "examples" / "synthetic-space" / "data"
AS_OF = date(2026, 7, 1)
PINNED = "2026-07-01T00:00:00+00:00"


def demo_bundle(**kwargs):
    return run_health_check(DEMO, client="Northstar Coworking Demo", as_of=AS_OF,
                            generated_at=PINNED, **kwargs)


class TestChurnWindow:
    def test_northstar_churn_is_hand_computable(self):
        # Hand math from memberships.csv at 2026-07-01, window 2026-06-01..07-01:
        # base = 17 memberships (start <= 06-01, no end or end >= 06-01), of which
        # M-011 is excluded (active but past its 05-31 end date), M-018 is pending
        # and starts 07-15 so it is not in the base, M-014 ends 06-15 as canceled.
        # base MRR = 13246 (M-008 is complimentary and contributes 0);
        # lost MRR = 760 (M-014). Logo churn 1/17 = 0.0588; revenue 760/13246 = 0.0574.
        report = churn_window(load_csv(DEMO / "memberships.csv"), AS_OF, 30)
        assert report["base_memberships"] == 17
        assert report["canceled_memberships"] == 1
        assert report["canceled_ids"] == ["M-014"]
        assert report["base_mrr"] == "13246"
        assert report["lost_mrr"] == "760"
        assert report["logo_churn"]["value"] == "0.0588"
        assert report["revenue_churn"]["value"] == "0.0574"
        assert report["excluded_active_past_end_date"] == ["M-011"]

    def test_expired_but_active_membership_is_not_churn(self):
        table = Table("m", ["membership_id", "company_id", "start_date", "end_date",
                            "contracted_rate", "status", "complimentary"],
                      [{"membership_id": "M-1", "company_id": "C-1",
                        "start_date": "2025-01-01", "end_date": "2026-06-01",
                        "contracted_rate": "500", "status": "active", "complimentary": ""}])
        report = churn_window(table, AS_OF, 30)
        assert report["base_memberships"] == 0
        assert report["canceled_memberships"] == 0
        assert report["excluded_active_past_end_date"] == ["M-1"]
        assert report["logo_churn"]["value"] is None
        assert any("zero" in w.lower() for w in report["logo_churn"]["warnings"])

    def test_membership_that_started_inside_the_window_is_not_in_the_base(self):
        table = Table("m", ["membership_id", "start_date", "end_date", "contracted_rate",
                            "status", "complimentary"],
                      [{"membership_id": "M-2", "start_date": "2026-06-10", "end_date": "",
                        "contracted_rate": "300", "status": "active", "complimentary": ""}])
        report = churn_window(table, AS_OF, 30)
        assert report["base_memberships"] == 0


class TestNotMeasurableDisclosure:
    def test_absent_inputs_are_named_not_guessed(self, tmp_path):
        (tmp_path / "invoices.csv").write_text(
            "invoice_id,company_id,membership_id,issue_date,due_date,amount,status\n"
            "INV-1,C-1,M-1,2026-06-01,2026-06-15,500,failed\n", encoding="utf-8")
        bundle = run_health_check(tmp_path, client="C", as_of=AS_OF, generated_at=PINNED)
        skipped = {item["module"]: item for item in bundle["not_measured"]}
        assert "occupancy" in skipped and "inventory" in skipped["occupancy"]["missing_inputs"]
        assert "churn" in skipped
        assert "occupancy" not in bundle["modules"]
        # The invoice-only engagement still produces a real collections number.
        assert bundle["metrics"]["collections.outstanding_total"] == "500"

    def test_report_says_not_measurable_and_why(self, tmp_path):
        (tmp_path / "invoices.csv").write_text(
            "invoice_id,company_id,amount,status\nINV-1,C-1,500,failed\n", encoding="utf-8")
        bundle = run_health_check(tmp_path, client="C", as_of=AS_OF, generated_at=PINNED)
        html = render_health_check(bundle)
        assert "NOT MEASURABLE" in html
        assert "inventory, memberships" in html
        assert "Required input" in html

    def test_no_finding_claims_a_module_that_did_not_run(self, tmp_path):
        (tmp_path / "invoices.csv").write_text(
            "invoice_id,company_id,amount,status\nINV-1,C-1,500,failed\n", encoding="utf-8")
        bundle = run_health_check(tmp_path, client="C", as_of=AS_OF, generated_at=PINNED)
        modules = {str(f["module"]) for f in bundle["findings"]}
        assert "occupancy" not in modules
        assert modules <= {"data quality", "collections", "revenue leakage"}


class TestOpportunityRanking:
    def test_northstar_ranking_is_deterministic(self):
        bundle = demo_bundle()
        top = bundle["opportunities"]["top"]
        ids = [o["id"] for o in top]
        # Recurring revenue at risk first (3,400 departing suite; 2,088 unbilled),
        # then the one-time balance, then a lost-revenue item.
        assert ids == ["opp-departures", "opp-unbilled", "opp-collections", "opp-churn",
                       "opp-oos"]
        assert [o["monthly_recurring"] for o in top[:2]] == ["3400", "2088"]
        assert top[2]["one_time"] == "2350"

    def test_ranking_rule_is_printed_and_never_sums(self):
        bundle = demo_bundle()
        rule = bundle["opportunities"]["ranking_rule"]
        assert "recurring revenue at risk" in rule
        assert "never summed" in rule
        assert "not added together" in bundle["opportunities"]["amount_policy"]
        # The one real anti-pattern this guards: a single fabricated headline total.
        flat = json.dumps(bundle["opportunities"]).lower()
        for banned in ("grand_total", "total_opportunity", "combined_amount"):
            assert banned not in flat
        bases = {o["basis"] for o in bundle["opportunities"]["opportunities"]}
        assert {"recurring", "one_time", "erosion", "lost", "unquantified"} <= bases

    def test_erosion_items_are_labelled_not_cash(self):
        bundle = demo_bundle()
        by_id = {o["id"]: o for o in bundle["opportunities"]["opportunities"]}
        assert by_id["opp-oos"]["basis"] == "erosion"
        assert "erosion" in by_id["opp-oos"]["amount_unit"]
        assert by_id["opp-churn"]["basis"] == "lost"
        assert "already left" in by_id["opp-churn"]["amount_unit"]

    def test_action_plan_only_uses_the_ranked_top_five(self):
        bundle = demo_bundle()
        plan = bundle["action_plan"]["buckets"]
        planned = [item["opportunity_id"] for bucket in plan.values() for item in bucket]
        assert sorted(planned) == sorted(o["id"] for o in bundle["opportunities"]["top"])
        assert set(plan) == {"days_0_14", "days_15_45", "days_46_90"}
        # Every planned action carries the evidence and limitation of its finding.
        for bucket in plan.values():
            for item in bucket:
                assert item["evidence"] and item["first_step"] and item["limitation"]


class TestReportSafety:
    def test_draft_banner_until_finalized(self, tmp_path):
        bundle = demo_bundle()
        draft = render_health_check(bundle)
        assert "DRAFT REPORT — REVIEW REQUIRED" in draft
        assert "health-check-finalize" in draft
        final = render_health_check(bundle, finalized=True, reviewer="A. Reviewer",
                                    finalized_at="2026-07-22T09:00:00+00:00",
                                    notes="checked")
        assert "DRAFT REPORT" not in final
        assert "REVIEWED &amp; FINALIZED" in final
        assert "A. Reviewer" in final

    def test_client_values_are_escaped_and_identifiers_redacted(self, tmp_path):
        (tmp_path / "locations.csv").write_text(
            "location_id,name,timezone,sellable_workstations\n"
            'LOC-1,"<script>alert(1)</script> ops@example.com",America/Chicago,10\n',
            encoding="utf-8")
        (tmp_path / "inventory.csv").write_text(
            "unit_id,location_id,unit_type,capacity,sellable,out_of_service,list_price\n"
            "OF-1,LOC-1,office,4,true,false,1200\n", encoding="utf-8")
        (tmp_path / "memberships.csv").write_text(
            "membership_id,company_id,location_id,product,unit_id,start_date,status,"
            "contracted_rate,complimentary\n"
            "M-1,C-1,LOC-1,private-office,OF-1,2026-01-01,active,1200,\n", encoding="utf-8")
        report = render_health_check(
            run_health_check(tmp_path, client="C", as_of=AS_OF, generated_at=PINNED))
        assert "<script>alert(1)</script>" not in report
        assert "&lt;script&gt;" in report
        assert "ops@example.com" not in report

    def test_report_never_contains_member_identifiers(self):
        report = render_health_check(demo_bundle())
        contacts = load_csv(DEMO / "contacts.csv")
        for row in contacts.rows:
            assert row["email"].lower() not in report.lower()
            assert row["phone"] not in report
            assert f"{row['first_name']} {row['last_name']}" not in report
        for company in load_csv(DEMO / "companies.csv").rows:
            assert company["name"] not in report

    def test_findings_carry_the_whole_confidence_contract(self):
        bundle = demo_bundle()
        assert bundle["findings"]
        for finding in bundle["findings"]:
            assert finding["kind"] in {"fact", "calculation", "inference", "recommendation"}
            assert finding["data_used"]
            assert finding["calculation"]
            assert finding["confidence"] in {"high", "medium", "low"}
            assert finding["confidence_basis"]
            assert finding["limitation"]

    def test_report_is_print_ready(self):
        report = render_health_check(demo_bundle())
        assert "@page" in report and "@media print" in report
        assert "break-inside:avoid" in report
        for heading in ("Executive summary", "Data quality and data handling", "Occupancy",
                        "Revenue leakage", "Sales pipeline", "Speed to lead",
                        "Tour conversion", "Collections and churn", "Top 5 opportunities",
                        "90-day action plan", "Methodology and formulas",
                        "Data limitations"):
            assert heading in report, heading


class TestEngagementFiles:
    def test_write_and_finalize_flow(self, tmp_path):
        out = tmp_path / "engagement"
        bundle = demo_bundle()
        paths = write_engagement(out, bundle, command_line="opencoworking health-check ...")
        assert set(paths) == {"report", "bundle", "preflight", "checklist", "manifest"}
        assert "DRAFT REPORT" in (out / "report.html").read_text(encoding="utf-8")
        checklist = (out / "REVIEW_CHECKLIST.md").read_text(encoding="utf-8")
        assert "review required" in checklist.lower()
        manifest = (out / "engagement.json").read_text(encoding="utf-8")
        assert '"review_required": true' in manifest
        assert '"client_exports_copied": false' in manifest

        final = finalize_engagement(out, reviewer="A. Reviewer", notes="ok",
                                    finalized_at="2026-07-22T09:00:00+00:00")
        final_html = Path(final["report"]).read_text(encoding="utf-8")
        assert "DRAFT REPORT" not in final_html and "A. Reviewer" in final_html
        record = (out / "finalized.json").read_text(encoding="utf-8")
        assert '"sent_to_client": false' in record
        # The draft is kept as the audit trail.
        assert (out / "report.html").exists()

    def test_write_refuses_to_overwrite_without_force(self, tmp_path):
        out = tmp_path / "engagement"
        bundle = demo_bundle()
        write_engagement(out, bundle, command_line="cmd")
        with pytest.raises(FileExistsError):
            write_engagement(out, bundle, command_line="cmd")
        write_engagement(out, bundle, command_line="cmd", force=True)

    def test_finalize_requires_a_draft(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            finalize_engagement(tmp_path, reviewer="A", notes=None, finalized_at="now")

    def test_reviewing_twice_needs_force(self, tmp_path):
        out = tmp_path / "engagement"
        write_engagement(out, demo_bundle(), command_line="cmd")
        finalize_engagement(out, reviewer="A", notes=None, finalized_at="now")
        with pytest.raises(FileExistsError):
            finalize_engagement(out, reviewer="B", notes=None, finalized_at="later")

    def test_input_fingerprints_ignore_line_endings(self, tmp_path):
        """A Windows checkout (CRLF) and a Linux checkout (LF) must agree.

        Without normalization the committed sample report could not be reproduced
        on CI, and a reviewer could not tell whether a report was regenerated
        from the same data or from a slightly different one.
        """
        files = {
            "inventory.csv": "unit_id,location_id,unit_type,capacity,sellable,"
                             "out_of_service,list_price\nOF-1,LOC-1,office,4,true,false,1200\n",
            "memberships.csv": "membership_id,company_id,location_id,product,unit_id,"
                               "start_date,status,contracted_rate,complimentary\n"
                               "M-1,C-1,LOC-1,private-office,OF-1,2026-01-01,active,1200,\n",
        }
        lf_dir = tmp_path / "lf"
        crlf_dir = tmp_path / "crlf"
        for directory, newline in ((lf_dir, "\n"), (crlf_dir, "\r\n")):
            directory.mkdir()
            for name, text in files.items():
                (directory / name).write_bytes(text.replace("\n", newline).encode())
        lf = run_health_check(lf_dir, client="C", as_of=AS_OF, generated_at=PINNED)
        crlf = run_health_check(crlf_dir, client="C", as_of=AS_OF, generated_at=PINNED)
        assert (lf["inputs"]["fingerprints"] == crlf["inputs"]["fingerprints"])
        assert lf["metrics"] == crlf["metrics"]
        assert render_health_check(lf) == render_health_check(crlf)

    def test_report_directory_holds_no_export_rows(self, tmp_path):
        out = tmp_path / "engagement"
        write_engagement(out, demo_bundle(), command_line="cmd")
        written = "".join(p.read_text(encoding="utf-8")
                          for p in out.iterdir() if p.is_file())
        contacts = load_csv(DEMO / "contacts.csv")
        for row in contacts.rows:
            assert row["email"].lower() not in written.lower()
            assert row["phone"] not in written
