"""Render analysis reports as human-readable Markdown.

JSON output comes straight from the report dicts; this module only formats.
"""

from __future__ import annotations

import json
from typing import Any


def to_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, ensure_ascii=False, default=str)


def _h(level: int, text: str) -> str:
    return f"{'#' * level} {text}\n"


def _kv_table(d: dict[str, Any]) -> str:
    lines = ["| Item | Value |", "|---|---|"]
    for k, v in d.items():
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines) + "\n"


def metrics_markdown(report: dict[str, Any], title: str) -> str:
    """Render an occupancy-style report (metrics + flags + issues)."""
    out = [_h(1, title), f"As of: {report.get('as_of', '?')}\n"]
    for m in report.get("metrics", []):
        value = m.get("value")
        pct = f"{float(value) * 100:.1f}%" if value is not None else "undefined"
        out.append(_h(2, f"{m['name']}: {pct}"))
        out.append(f"- Formula: {m['formula']}")
        out.append(f"- Numerator: {m['numerator']}  |  Denominator: {m['denominator']}")
        if m.get("exclusions"):
            out.append(f"- Excludes: {'; '.join(m['exclusions'])}")
        for w in m.get("warnings", []):
            out.append(f"- ⚠ {w}")
        out.append("")
    flags = report.get("flags", [])
    if flags:
        out.append(_h(2, "Flags"))
        for f in flags:
            units = f.get("units", [])
            shown = ", ".join(str(u) for u in units[:10])
            more = f" (+{len(units) - 10} more)" if len(units) > 10 else ""
            out.append(f"- **{f['flag']}** ({len(units)}): {shown}{more}\n  {f['why']}")
        out.append("")
    issues = report.get("referential_issues", [])
    if issues:
        out.append(_h(2, "Data issues"))
        for i in issues:
            out.append(f"- {json.dumps(i, default=str)}")
        out.append("")
    return "\n".join(out)


def findings_markdown(report: dict[str, Any], title: str) -> str:
    """Render a findings-style report (leakage, pipeline, reconciliation)."""
    out = [_h(1, title), f"As of: {report.get('as_of', '?')}\n"]
    findings = report.get("findings")
    if isinstance(findings, dict):  # pipeline style: named finding lists
        for name, items in findings.items():
            if not items:
                continue
            out.append(_h(2, f"{name.replace('_', ' ')} ({len(items)})"))
            for item in items[:25]:
                out.append(f"- {json.dumps(item, default=str)}")
            if len(items) > 25:
                out.append(f"- ...and {len(items) - 25} more")
            out.append("")
    elif isinstance(findings, list):  # leakage style
        if not findings:
            out.append("No findings from the checks that ran.\n")
        for f in findings:
            out.append(_h(2, f"{f.get('check', 'finding')} ({f.get('count', '?')})"))
            out.append(f"{f.get('detail', '')}")
            for key in ("monthly_amount_at_risk", "amount_outstanding",
                        "monthly_list_value_blocked"):
                if key in f:
                    out.append(f"- {key.replace('_', ' ')}: {f[key]}")
            ids = f.get("ids") or [i.get("membership_id") or i.get("invoice_id")
                                   or i.get("unit_id") for i in f.get("items", [])]
            if ids:
                out.append(f"- Records: {', '.join(str(i) for i in ids[:15])}")
            out.append("")
    for key in ("skipped_checks",):
        if report.get(key):
            out.append(_h(2, "Checks skipped (missing inputs)"))
            for s in report[key]:
                out.append(f"- {s}")
            out.append("")
    for key in ("caveat", "quantification_note", "note"):
        if report.get(key):
            out.append(f"> {report[key]}\n")
    return "\n".join(out)


def generic_markdown(report: dict[str, Any], title: str) -> str:
    """Fallback renderer: top-level scalars as a table, rest as JSON blocks."""
    out = [_h(1, title)]
    scalars = {k: v for k, v in report.items() if isinstance(v, (str, int, float))}
    if scalars:
        out.append(_kv_table(scalars))
    for k, v in report.items():
        if k in scalars:
            continue
        out.append(_h(2, k.replace("_", " ")))
        out.append("```json")
        out.append(json.dumps(v, indent=2, default=str))
        out.append("```\n")
    return "\n".join(out)
