"""Command-line interface for OpenCoworking deterministic tools.

Every command reads files, writes to stdout or an explicit --output path,
and never modifies inputs. Exit codes: 0 success, 1 usage/input error,
2 analysis produced error-severity findings (useful for CI gating).
No command makes network calls.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from . import __version__
from .analyze import (
    funnel_report,
    inspect_table,
    leakage_report,
    occupancy_report,
    pipeline_report,
    source_report,
    speed_to_lead_report,
    vo_reconciliation,
)
from .economics import unit_economics
from .healthcheck import SERVICE_NAME, PreflightBlocked, run_health_check
from .healthcheck_report import finalize_engagement, write_engagement
from .ingest import IngestError, load_table
from .quality import (
    check_blank_values,
    check_date_parseability,
    check_duplicates,
    quality_score,
)
from .redact import Redactor, collect_names
from .render import findings_markdown, generic_markdown, metrics_markdown, to_json
from .stack_audit import stack_audit
from .wave2 import (
    collections_queue,
    daily_brief,
    location_benchmark,
    occupancy_forecast,
    pricing_audit,
    reconcile_report,
    renewal_scan,
    room_yield,
)


def _parse_as_of(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise SystemExit(f"--as-of must be YYYY-MM-DD, got: {value}") from None


def _load(path: str):
    try:
        return load_table(path)
    except IngestError as e:
        raise SystemExit(f"error: {e}") from None


def _emit(report: dict, args: argparse.Namespace, markdown: str) -> None:
    text = to_json(report) if args.format == "json" else markdown
    if args.output:
        out = Path(args.output)
        if out.exists() and not args.force:
            raise SystemExit(f"error: {out} exists; pass --force to overwrite")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text)


def _health_check_summary(bundle: dict, paths: dict[str, str]) -> str:
    metrics = bundle.get("metrics", {})
    out = [f"# {SERVICE_NAME} — DRAFT, review required",
           f"Client: {bundle['engagement']['client']}  |  as of "
           f"{bundle['engagement']['as_of']}", "", "## Metrics (verified against the engine)"]
    for key in sorted(metrics):
        if key == "metrics.count":
            continue
        out.append(f"- {key}: {metrics[key]}")
    out += ["", "## Findings"]
    for f in bundle.get("findings", []):
        out.append(f"- [{f['kind'].upper()}] ({f['confidence']}) {f['title']}")
    out += ["", "## Top opportunities"]
    for o in bundle.get("opportunities", {}).get("top", []):
        amount = o.get("monthly_recurring") or o.get("one_time") or "not quantified"
        out.append(f"- {o['rank']}. {o['title']} — {amount} ({o['owner']})")
    out += ["", "## Not measurable in this engagement"]
    for n in bundle.get("not_measured", []):
        out.append(f"- {n['module']}: {n['reason']}")
    out += ["", "## Artifacts"]
    for name, path in paths.items():
        out.append(f"- {name}: {path}")
    out += ["", "This is a DRAFT. Nothing was sent to the client. Review the checklist, "
            "then run `opencoworking health-check-finalize` to release it."]
    return "\n".join(out)


def _preflight_refusal(result) -> str:
    lines = ["# Engagement refused by preflight", "",
             "The input folder contains data that must not enter an analysis "
             "engagement. Nothing was analysed and nothing was written.", ""]
    for f in result.files:
        if f.status != "blocked":
            continue
        lines.append(f"## {f.path} (blocked)")
        for finding in f.findings:
            lines.append(f"- {finding['code']}: {finding['message']}")
        lines.append("")
    lines += ["## What to do", "",
              "1. Remove the blocked file(s) from the folder (move credentials back to a "
              "secret store; split a database dump into named exports).",
              "2. Re-run the same command.",
              "3. If a blocked file is genuinely required, re-run with --allow-unsafe: the "
              "override is recorded in the engagement manifest and the report shows it."]
    return "\n".join(lines)


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--format", choices=["markdown", "json"], default="markdown",
                   help="output format (default: markdown)")
    p.add_argument("--output", help="write to this file instead of stdout")
    p.add_argument("--force", action="store_true",
                   help="allow overwriting an existing --output file")
    p.add_argument("--as-of", dest="as_of", default=None,
                   help="report date YYYY-MM-DD (default: today)")


def _demo_input() -> Path | None:
    """Find the committed synthetic health-check export from a checkout.

    The package does not bundle operator fixtures. A demo from an installed
    wheel, outside the repository, says so instead of inventing a dataset.
    """
    candidates = [
        Path.cwd() / "examples" / "health-check-engagement" / "client-export",
        Path(__file__).resolve().parents[2] / "examples" / "health-check-engagement"
        / "client-export",
    ]
    for path in candidates:
        if (path / "inventory.csv").is_file() and (path / "memberships.csv").is_file():
            return path
    return None


def _run_demo(output: str | None, *, force: bool) -> int:
    source = _demo_input()
    if source is None:
        print("error: the synthetic Northstar export was not found. Run `opencoworking "
              "demo` from a checkout of open-coworking-skills, or pass your own folder "
              "to `opencoworking health-check`.")
        return 1
    if output:
        out = Path(output)
    else:
        out = Path(tempfile.mkdtemp(prefix="opencoworking-demo-"))
    try:
        bundle = run_health_check(
            source, client="Northstar Coworking Demo", as_of=date(2026, 7, 1),
            generated_at="2026-07-21T00:00:00+00:00")
    except PreflightBlocked as e:
        print(_preflight_refusal(e.result))
        return 2
    try:
        paths = write_engagement(
            out, bundle,
            command_line="opencoworking demo",
            force=force)
    except FileExistsError as e:
        raise SystemExit(f"error: {e}") from None
    print("Synthetic Northstar Coworking Demo health check (draft, not a client deliverable).")
    print(f"Input: {source}")
    print(_health_check_summary(bundle, paths))
    print("This demo does not finalize the report and does not send it anywhere.")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Windows consoles default to cp1252, which cannot encode characters the
    # reports use (e.g. the warning sign); without this, the quick start
    # crashes with UnicodeEncodeError on a stock PowerShell.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):  # pragma: no cover - exotic streams
                pass
    parser = argparse.ArgumentParser(
        prog="opencoworking",
        description="Deterministic analysis tools for coworking exports. "
                    "Reads CSV/XLSX; never modifies inputs; makes no network calls.",
    )
    parser.add_argument("--version", action="version", version=f"opencoworking {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("inspect", help="identify the likely entity and structure of an export")
    p.add_argument("file", help="CSV or XLSX export")
    _add_common(p)

    p = sub.add_parser("quality", help="data-quality checks on an export")
    p.add_argument("file")
    p.add_argument("--date-columns", default="", help="comma-separated date columns to validate")
    p.add_argument("--key-columns", default="", help="comma-separated duplicate-detection keys")
    p.add_argument("--required", default="", help="comma-separated columns that must be non-blank")
    _add_common(p)

    p = sub.add_parser("occupancy", help="occupancy and revenue dashboard")
    p.add_argument("--inventory", required=True)
    p.add_argument("--memberships", required=True)
    p.add_argument("--discount-flag-pct", type=int, default=25)
    _add_common(p)

    p = sub.add_parser("pipeline", help="pipeline hygiene report from a deals export")
    p.add_argument("--deals", required=True)
    p.add_argument("--stale-days", type=int, default=21)
    _add_common(p)

    p = sub.add_parser("funnel", help="lead-to-member funnel counts")
    p.add_argument("--leads", required=True)
    p.add_argument("--tours", required=True)
    p.add_argument("--deals", required=True)
    _add_common(p)

    p = sub.add_parser("speed-to-lead", help="first-response timing from a leads export")
    p.add_argument("--leads", required=True)
    p.add_argument("--clock", action="store_true",
                   help="use clock time instead of business hours")
    p.add_argument("--open-hour", type=int, default=9)
    p.add_argument("--close-hour", type=int, default=17)
    _add_common(p)

    p = sub.add_parser("sources", help="normalize lead-source labels")
    p.add_argument("--leads", required=True)
    _add_common(p)

    p = sub.add_parser("leakage", help="revenue leakage audit across exports")
    for name in ("leads", "deals", "tours", "memberships", "invoices",
                 "inventory", "payments"):
        p.add_argument(f"--{name}", help=f"{name} export (optional)")
    _add_common(p)

    p = sub.add_parser("vo-reconcile", help="virtual-office partner reconciliation")
    p.add_argument("--partners", required=True)
    p.add_argument("--memberships", required=True)
    p.add_argument("--invoices", required=True)
    _add_common(p)

    p = sub.add_parser("reconcile", help="CRM vs WMS reconciliation across exports")
    p.add_argument("--companies", required=True)
    p.add_argument("--deals", required=True)
    p.add_argument("--memberships", required=True)
    p.add_argument("--contacts")
    p.add_argument("--inventory")
    p.add_argument("--invoices")
    p.add_argument("--wms-companies", dest="wms_companies",
                   help="second company list from the WMS side (enables name matching)")
    _add_common(p)

    p = sub.add_parser("brief", help="daily role-filtered operator action queue")
    p.add_argument("--role", choices=["owner", "community", "sales", "finance"],
                   default="owner")
    for name in ("leads", "deals", "tours", "memberships", "invoices", "inventory"):
        p.add_argument(f"--{name}", help=f"{name} export (optional)")
    _add_common(p)

    p = sub.add_parser("forecast", help="contracted occupancy forecast at horizons")
    p.add_argument("--inventory", required=True)
    p.add_argument("--memberships", required=True)
    p.add_argument("--horizons", default="30,60,90,180",
                   help="comma-separated day horizons (default 30,60,90,180)")
    _add_common(p)

    p = sub.add_parser("renewals", help="portfolio renewal window scan")
    p.add_argument("--memberships", required=True)
    p.add_argument("--invoices")
    p.add_argument("--window-days", type=int, default=90)
    _add_common(p)

    p = sub.add_parser("pricing", help="discount and pricing audit per product x location")
    p.add_argument("--inventory", required=True)
    p.add_argument("--memberships", required=True)
    p.add_argument("--deep-discount-pct", type=int, default=25)
    _add_common(p)

    p = sub.add_parser("collections", help="prioritized internal collections worklist")
    p.add_argument("--invoices", required=True)
    p.add_argument("--payments")
    p.add_argument("--memberships")
    _add_common(p)

    p = sub.add_parser("rooms", help="meeting/event room yield from bookings")
    p.add_argument("--bookings", required=True)
    p.add_argument("--inventory", required=True)
    p.add_argument("--open-hours-per-day", dest="open_hours", type=str, default=None,
                   help="declared bookable hours per day (enables utilization)")
    _add_common(p)

    p = sub.add_parser("economics",
                       help="coverage and contribution from operator-supplied monthly costs")
    p.add_argument("--costs", required=True,
                   help="CSV with category, monthly_amount, kind=fixed|variable; "
                        "optional product and location_id")
    p.add_argument("--inventory")
    p.add_argument("--memberships")
    p.add_argument("--meeting-revenue", dest="meeting_revenue", default=None,
                   help="operator-supplied meeting/event revenue for the same month")
    _add_common(p)

    p = sub.add_parser("stack-audit",
                       help="read-only map of the operator's systems inventory")
    p.add_argument("--systems", required=True,
                   help="CSV with system, category, and optional connection columns")
    _add_common(p)

    p = sub.add_parser("benchmark", help="normalized multi-location scorecard")
    p.add_argument("--locations", required=True)
    p.add_argument("--inventory", required=True)
    p.add_argument("--memberships", required=True)
    p.add_argument("--leads")
    p.add_argument("--tours")
    p.add_argument("--invoices")
    _add_common(p)

    # --- Paid engagement: one command, one deliverable ----------------------
    p = sub.add_parser(
        "health-check",
        help="run a full revenue and operations health check over a client folder "
             "and write a reviewable engagement deliverable")
    p.add_argument("--input", required=True,
                   help="directory of client exports (screened, never modified)")
    p.add_argument("--output", required=True,
                   help="directory to write engagement artifacts into")
    p.add_argument("--client", required=True, help="client name shown on the report")
    p.add_argument("--map", action="append", default=[], metavar="FILE=ENTITY",
                   help="resolve an ambiguous mapping, repeatable "
                        "(e.g. --map crm.csv=deals)")
    p.add_argument("--allow-unsafe", dest="allow_unsafe", action="store_true",
                   help="proceed past a blocking preflight finding; requires "
                        "--unsafe-reason and is recorded in the engagement manifest")
    p.add_argument("--unsafe-reason", default=None,
                   help="why a human accepted a folder that failed preflight "
                        "(required with --allow-unsafe; stored verbatim)")
    p.add_argument("--pii-policy", choices=["report", "strict"], default="report",
                   help="report (default): analyse files that contain identifiers but never "
                        "print them; strict: refuse them")
    p.add_argument("--stale-days", type=int, default=21)
    p.add_argument("--discount-flag-pct", type=int, default=25)
    p.add_argument("--churn-window-days", type=int, default=30)
    p.add_argument("--renewal-window-days", type=int, default=90)
    p.add_argument("--horizons", default="30,60,90,180")
    p.add_argument("--open-hours-per-day", dest="open_hours", default=None)
    p.add_argument("--max-file-mb", type=int, default=64)
    p.add_argument("--generated-at", dest="generated_at", default=None,
                   help="pin the run timestamp (ISO 8601) for a reproducible artifact")
    p.add_argument("--force", action="store_true",
                   help="overwrite existing artifacts in the output directory")
    p.add_argument("--as-of", dest="as_of", default=None,
                   help="report date YYYY-MM-DD (default: today)")
    p.add_argument("--format", choices=["markdown", "json"], default="markdown",
                   help="stdout summary format (artifacts are always written)")

    p = sub.add_parser(
        "health-check-finalize",
        help="release a reviewed draft: writes report.final.html and records the reviewer")
    p.add_argument("--engagement", required=True, help="engagement output directory")
    p.add_argument("--reviewer", required=True, help="name of the human who reviewed it")
    p.add_argument("--attest", required=True,
                   help="reviewer's statement that the human checklist was completed; "
                        "stored in finalized.json and printed on report.final.html")
    p.add_argument("--notes", default=None, help="reviewer notes recorded with the release")
    p.add_argument("--at", dest="finalized_at", default=None,
                   help="finalize timestamp ISO 8601 (default: now)")
    p.add_argument("--force", action="store_true",
                   help="re-finalize an engagement that was already finalized")

    p = sub.add_parser(
        "demo",
        help="run the bundled synthetic Northstar health check and print the draft path")
    p.add_argument("--output", default=None,
                   help="directory for the demo draft (default: a new temp folder)")
    p.add_argument("--force", action="store_true",
                   help="overwrite an existing --output directory's draft artifacts")

    p = sub.add_parser("redact", help="redact PII from an export into a new file")
    p.add_argument("file")
    p.add_argument("--output", required=True, help="destination file (never in-place)")
    p.add_argument("--name-columns", default="",
                   help="comma-separated columns containing person names")
    p.add_argument("--salt", default="opencoworking",
                   help="salt for stable pseudonyms (keep private)")
    p.add_argument("--force", action="store_true")

    args = parser.parse_args(argv)
    as_of = _parse_as_of(getattr(args, "as_of", None))

    if args.command == "inspect":
        report = inspect_table(_load(args.file))
        _emit(report, args, generic_markdown(report, f"Export inspection: {args.file}"))
        return 0

    if args.command == "quality":
        table = _load(args.file)
        findings = []
        for col in filter(None, args.required.split(",")):
            findings += check_blank_values(table.rows, col.strip())
        for col in filter(None, args.date_columns.split(",")):
            findings += check_date_parseability(table.rows, col.strip())
        keys = [c.strip() for c in args.key_columns.split(",") if c.strip()]
        if keys:
            findings += check_duplicates(table.rows, keys, "record")
        report = {"file": args.file, "structure_warnings": table.warnings,
                  "findings": [f.as_dict() for f in findings],
                  "score": quality_score(findings, len(table.rows))}
        _emit(report, args, generic_markdown(report, f"Data quality: {args.file}"))
        return 2 if any(f.severity == "error" for f in findings) else 0

    if args.command == "occupancy":
        report = occupancy_report(_load(args.inventory), _load(args.memberships),
                                  as_of, args.discount_flag_pct)
        _emit(report, args, metrics_markdown(report, "Occupancy and revenue dashboard"))
        return 0

    if args.command == "pipeline":
        report = pipeline_report(_load(args.deals), as_of, args.stale_days)
        _emit(report, args, findings_markdown(report, "Pipeline health"))
        return 0

    if args.command == "funnel":
        report = funnel_report(_load(args.leads), _load(args.tours), _load(args.deals))
        _emit(report, args, generic_markdown(report, "Sales funnel"))
        return 0

    if args.command == "speed-to-lead":
        report = speed_to_lead_report(_load(args.leads), business_hours=not args.clock,
                                      open_hour=args.open_hour, close_hour=args.close_hour)
        _emit(report, args, generic_markdown(report, "Speed to lead"))
        return 0

    if args.command == "sources":
        report = source_report(_load(args.leads))
        _emit(report, args, generic_markdown(report, "Lead sources"))
        return 0

    if args.command == "leakage":
        tables = {name: (_load(getattr(args, name)) if getattr(args, name) else None)
                  for name in ("leads", "deals", "tours", "memberships", "invoices",
                               "inventory", "payments")}
        report = leakage_report(as_of, **tables)
        _emit(report, args, findings_markdown(report, "Revenue leakage audit"))
        return 0

    if args.command == "vo-reconcile":
        report = vo_reconciliation(_load(args.partners), _load(args.memberships),
                                   _load(args.invoices), as_of)
        _emit(report, args, findings_markdown(report, "Virtual-office reconciliation"))
        return 0

    if args.command == "reconcile":
        report = reconcile_report(
            as_of, companies=_load(args.companies), deals=_load(args.deals),
            memberships=_load(args.memberships),
            contacts=_load(args.contacts) if args.contacts else None,
            inventory=_load(args.inventory) if args.inventory else None,
            invoices=_load(args.invoices) if args.invoices else None,
            wms_companies=_load(args.wms_companies) if args.wms_companies else None)
        _emit(report, args, findings_markdown(report, "CRM-WMS reconciliation"))
        return 0

    if args.command == "brief":
        tables = {name: (_load(getattr(args, name)) if getattr(args, name) else None)
                  for name in ("leads", "deals", "tours", "memberships", "invoices",
                               "inventory")}
        report = daily_brief(as_of, args.role, **tables)
        _emit(report, args, generic_markdown(report, f"Daily brief - {args.role}"))
        return 0

    if args.command == "forecast":
        try:
            horizons = tuple(int(h) for h in args.horizons.split(",") if h.strip())
        except ValueError:
            raise SystemExit("--horizons must be comma-separated integers") from None
        report = occupancy_forecast(_load(args.inventory), _load(args.memberships),
                                    as_of, horizons)
        _emit(report, args, generic_markdown(report, "Contracted occupancy forecast"))
        return 0

    if args.command == "renewals":
        report = renewal_scan(_load(args.memberships), as_of,
                              invoices=_load(args.invoices) if args.invoices else None,
                              window_days=args.window_days)
        _emit(report, args, generic_markdown(report, "Renewal window scan"))
        return 0

    if args.command == "pricing":
        report = pricing_audit(_load(args.inventory), _load(args.memberships),
                               as_of, args.deep_discount_pct)
        _emit(report, args, generic_markdown(report, "Discount and pricing audit"))
        return 0

    if args.command == "collections":
        report = collections_queue(
            _load(args.invoices), as_of,
            payments=_load(args.payments) if args.payments else None,
            memberships=_load(args.memberships) if args.memberships else None)
        _emit(report, args, generic_markdown(report, "Collections worklist"))
        return 0

    if args.command == "rooms":
        from decimal import Decimal as _D
        open_hours = _D(args.open_hours) if args.open_hours else None
        report = room_yield(_load(args.bookings), _load(args.inventory), open_hours)
        _emit(report, args, generic_markdown(report, "Meeting and event yield"))
        return 0

    if args.command == "economics":
        try:
            meeting = (Decimal(args.meeting_revenue)
                       if args.meeting_revenue is not None else None)
        except ArithmeticError:
            raise SystemExit("error: --meeting-revenue must be a number") from None
        report = unit_economics(
            as_of, _load(args.costs),
            inventory=_load(args.inventory) if args.inventory else None,
            memberships=_load(args.memberships) if args.memberships else None,
            meeting_revenue=meeting)
        _emit(report, args, generic_markdown(report, "Unit economics"))
        return 0

    if args.command == "stack-audit":
        report = stack_audit(_load(args.systems))
        _emit(report, args, generic_markdown(report, "Tech stack audit"))
        return 0

    if args.command == "benchmark":
        report = location_benchmark(
            as_of, _load(args.locations), _load(args.inventory), _load(args.memberships),
            leads=_load(args.leads) if args.leads else None,
            tours=_load(args.tours) if args.tours else None,
            invoices=_load(args.invoices) if args.invoices else None)
        _emit(report, args, generic_markdown(report, "Multi-location benchmark"))
        return 0

    if args.command == "health-check":
        overrides: dict[str, str] = {}
        for pair in args.map:
            if "=" not in pair:
                raise SystemExit("--map must be FILE=ENTITY")
            src, _, entity = pair.partition("=")
            overrides[src.strip()] = entity.strip()
        try:
            horizons = tuple(int(h) for h in args.horizons.split(",") if h.strip())
        except ValueError:
            raise SystemExit("--horizons must be comma-separated integers") from None
        try:
            open_hours = Decimal(args.open_hours) if args.open_hours else None
        except ArithmeticError:
            raise SystemExit("--open-hours-per-day must be a number") from None
        generated_at = args.generated_at or datetime.now().astimezone().isoformat(
            timespec="seconds")
        if args.allow_unsafe and not (args.unsafe_reason or "").strip():
            raise SystemExit(
                "error: --allow-unsafe requires --unsafe-reason "
                "\"who accepted this folder and why\"")
        if args.unsafe_reason and not args.allow_unsafe:
            raise SystemExit("error: --unsafe-reason is only valid with --allow-unsafe")
        try:
            bundle = run_health_check(
                args.input, client=args.client, as_of=as_of, generated_at=generated_at,
                policy=args.pii_policy, allow_unsafe=args.allow_unsafe,
                unsafe_reason=args.unsafe_reason,
                overrides=overrides, stale_days=args.stale_days,
                discount_pct=args.discount_flag_pct,
                churn_window_days=args.churn_window_days,
                renewal_window_days=args.renewal_window_days, horizons=horizons,
                open_hours=open_hours, max_file_bytes=args.max_file_mb * 1024 * 1024)
        except PreflightBlocked as e:
            print(_preflight_refusal(e.result))
            print(f"\nScreening report: {len(e.result.blocked)} blocked, "
                  f"{len(e.result.warnings)} warning(s), {len(e.result.files)} file(s) "
                  "inspected. Nothing was analysed.")
            return 2
        except FileNotFoundError as e:
            raise SystemExit(f"error: {e}") from None
        except ValueError as e:
            raise SystemExit(f"error: {e}") from None
        command_line = ("opencoworking health-check "
                        f"--input {args.input} --output {args.output} "
                        f"--client \"{args.client}\" --as-of {as_of.isoformat()}")
        try:
            paths = write_engagement(args.output, bundle, command_line=command_line,
                                     force=args.force)
        except FileExistsError as e:
            raise SystemExit(f"error: {e}") from None
        if args.format == "json":
            print(json.dumps({"status": "draft", "review_required": True,
                              "metrics": bundle["metrics"],
                              "not_measured": bundle["not_measured"],
                              "artifacts": paths}, indent=2, default=str))
        else:
            print(_health_check_summary(bundle, paths))
        return 2 if bundle["quality"]["totals"]["errors"] else 0

    if args.command == "health-check-finalize":
        finalized_at = args.finalized_at or datetime.now().astimezone().isoformat(
            timespec="seconds")
        try:
            paths = finalize_engagement(args.engagement, reviewer=args.reviewer,
                                        notes=args.notes, finalized_at=finalized_at,
                                        attestation=args.attest, force=args.force)
        except (FileNotFoundError, FileExistsError, ValueError) as e:
            raise SystemExit(f"error: {e}") from None
        print(f"Finalized: {paths['report']}\nReview record: {paths['record']}\n"
              "The report is released to you; this tool does not send it to the client. "
              "The draft report.html is left in place as the audit trail.")
        return 0

    if args.command == "demo":
        return _run_demo(args.output, force=args.force)

    if args.command == "redact":
        table = _load(args.file)
        out = Path(args.output)
        if out.resolve() == Path(args.file).resolve():
            raise SystemExit("error: --output must differ from the input file")
        if out.exists() and not args.force:
            raise SystemExit(f"error: {out} exists; pass --force to overwrite")
        name_cols = [c.strip() for c in args.name_columns.split(",") if c.strip()]
        redactor = Redactor(salt=args.salt, names=collect_names(table.rows, name_cols))
        import csv as _csv

        from .normalize import sanitize_cell

        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = _csv.DictWriter(fh, fieldnames=table.columns)
            writer.writeheader()
            for row in table.rows:
                # Redacted files get shared onward: neutralize spreadsheet
                # formula injection on the way out.
                writer.writerow({k: sanitize_cell(v)
                                 for k, v in redactor.redact_row(row).items()})
        print(f"Wrote {out} ({redactor.replacements} redactions). "
              "Pattern-based redaction is not a guarantee; review before sharing.")
        return 0

    parser.error(f"unknown command {args.command}")  # pragma: no cover
    return 1  # pragma: no cover


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        # Downstream consumer (head, Select-Object -First) closed the pipe;
        # that is not an error in this program.
        sys.exit(0)
