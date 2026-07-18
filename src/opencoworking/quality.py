"""Data-quality checks for coworking exports.

Each check returns Finding objects with severity, affected rows, and a plain
statement of what is wrong and why it matters. Checks never modify data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .normalize import parse_date

Row = dict[str, str]


@dataclass
class Finding:
    check: str
    severity: str          # info | warning | error
    message: str
    rows: list[int] = field(default_factory=list)  # 1-based data row numbers

    def as_dict(self) -> dict[str, object]:
        return {"check": self.check, "severity": self.severity,
                "message": self.message, "rows": self.rows[:50]}


def check_required_columns(columns: list[str], required: list[str]) -> list[Finding]:
    missing = [c for c in required if c not in columns]
    if missing:
        return [Finding("required_columns", "error",
                        f"Missing required column(s): {', '.join(missing)}")]
    return []


def check_blank_values(rows: list[Row], column: str, label: str | None = None) -> list[Finding]:
    blanks = [i for i, r in enumerate(rows, 1) if not r.get(column, "").strip()]
    if blanks:
        pct = round(100 * len(blanks) / len(rows)) if rows else 0
        return [Finding("blank_values", "warning",
                        f"{len(blanks)} of {len(rows)} rows ({pct}%) have no value in "
                        f"'{label or column}'.", blanks)]
    return []


def check_duplicates(rows: list[Row], key_columns: list[str], entity: str) -> list[Finding]:
    """Exact-match duplicates on the given key columns (case-insensitive)."""
    seen: dict[tuple[str, ...], int] = {}
    dupes: list[int] = []
    groups = 0
    for i, r in enumerate(rows, 1):
        key = tuple(r.get(c, "").strip().lower() for c in key_columns)
        if not any(key):
            continue
        if key in seen:
            if seen[key] > 0:
                groups += 1
                dupes.append(seen[key])
                seen[key] = -seen[key]  # mark first occurrence reported
            dupes.append(i)
        else:
            seen[key] = i
    if dupes:
        return [Finding("duplicates", "warning",
                        f"{groups} duplicate {entity} group(s) on ({', '.join(key_columns)}) "
                        f"covering {len(dupes)} rows.", sorted(set(abs(x) for x in dupes)))]
    return []


def check_date_parseability(rows: list[Row], column: str) -> list[Finding]:
    bad: list[int] = []
    formats_seen: set[str] = set()
    for i, r in enumerate(rows, 1):
        v = r.get(column, "").strip()
        if not v:
            continue
        if parse_date(v) is None:
            bad.append(i)
        else:
            if "/" in v:
                formats_seen.add("slash")
            elif "-" in v and v[:4].isdigit():
                formats_seen.add("iso")
            else:
                formats_seen.add("other")
    findings: list[Finding] = []
    if bad:
        findings.append(Finding("unparseable_dates", "error",
                                f"{len(bad)} value(s) in '{column}' could not be parsed as dates.",
                                bad))
    if len(formats_seen) > 1:
        findings.append(Finding(
            "mixed_date_formats", "warning",
            f"Column '{column}' mixes date formats ({', '.join(sorted(formats_seen))}). "
            "Slash dates were interpreted month-first; verify this matches the "
            "source system's locale."))
    return findings


def check_allowed_values(rows: list[Row], column: str, allowed: set[str],
                         entity: str) -> list[Finding]:
    bad_rows: list[int] = []
    bad_values: set[str] = set()
    for i, r in enumerate(rows, 1):
        v = r.get(column, "").strip().lower()
        if v and v not in allowed:
            bad_rows.append(i)
            bad_values.add(r.get(column, "").strip())
    if bad_rows:
        sample = ", ".join(sorted(bad_values)[:8])
        return [Finding("unexpected_values", "warning",
                        f"{len(bad_rows)} {entity} row(s) have values in '{column}' outside the "
                        f"expected set: {sample}", bad_rows)]
    return []


def quality_score(findings: list[Finding], row_count: int) -> dict[str, object]:
    """Blunt 0-100 score: errors cost 15, warnings 5, floor 0.

    The score exists to rank datasets and track improvement, not to certify
    quality; the findings list is the real output.
    """
    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    score = max(0, 100 - 15 * errors - 5 * warnings)
    return {"score": score, "errors": errors, "warnings": warnings, "rows": row_count,
            "note": "Heuristic ranking aid; read the findings, not just the number."}
