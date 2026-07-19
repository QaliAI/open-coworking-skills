"""Command-line interface for OpenCoworking deterministic tools.

Every command reads files, writes to stdout or an explicit --output path,
and never modifies inputs. Exit codes: 0 success, 1 usage/input error,
2 analysis produced error-severity findings (useful for CI gating).
No command makes network calls.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
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
from .ingest import IngestError, load_table
from .quality import (
    check_blank_values,
    check_date_parseability,
    check_duplicates,
    quality_score,
)
from .redact import Redactor, collect_names
from .render import findings_markdown, generic_markdown, metrics_markdown, to_json


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


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--format", choices=["markdown", "json"], default="markdown",
                   help="output format (default: markdown)")
    p.add_argument("--output", help="write to this file instead of stdout")
    p.add_argument("--force", action="store_true",
                   help="allow overwriting an existing --output file")
    p.add_argument("--as-of", dest="as_of", default=None,
                   help="report date YYYY-MM-DD (default: today)")


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
