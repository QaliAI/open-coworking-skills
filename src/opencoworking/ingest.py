"""CSV/XLSX ingestion with structural inspection.

CSV uses the standard library. XLSX requires the optional ``openpyxl`` extra
(``pip install opencoworking[xlsx]``) and fails with a clear error otherwise.
Source files are never modified.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

# Exports legitimately carry long free-text cells (CRM notes); the csv
# module's 128 KiB default raises a raw _csv.Error mid-iteration. Allow up
# to 32 MiB per field and convert overflows into a structured IngestError.
_MAX_FIELD = 32 * 1024 * 1024
csv.field_size_limit(_MAX_FIELD)

# Rows are plain dicts of column -> raw string value ("" for blank).
Row = dict[str, str]


class IngestError(Exception):
    """Raised when a file cannot be read as tabular data."""


@dataclass
class Table:
    """A loaded tabular export."""

    source: str
    columns: list[str]
    rows: list[Row]
    warnings: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.rows)


def sniff_dialect(sample: str) -> csv.Dialect | type[csv.Dialect]:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.excel


def load_csv(path: str | Path, encoding: str | None = None) -> Table:
    """Load a CSV export. Tries UTF-8 (with BOM), falls back to cp1252."""
    p = Path(path)
    if not p.is_file():
        raise IngestError(f"File not found: {p}")
    encodings = [encoding] if encoding else ["utf-8-sig", "cp1252"]
    last_err: Exception | None = None
    for enc in encodings:
        try:
            text = p.read_text(encoding=enc)
            break
        except UnicodeDecodeError as e:  # pragma: no cover - depends on input
            last_err = e
    else:  # pragma: no cover
        raise IngestError(f"Could not decode {p}: {last_err}")

    warnings: list[str] = []
    dialect = sniff_dialect(text[:4096])
    # Parse from a stream, NOT splitlines(): splitting first destroys
    # newlines embedded inside quoted fields (silent data corruption).
    reader = csv.reader(io.StringIO(text), dialect)
    try:
        header = next(reader)
    except StopIteration:
        raise IngestError(f"Empty file: {p}") from None
    except csv.Error as e:
        raise IngestError(f"Malformed CSV in {p}: {e}") from None

    columns, dupes = _dedupe_columns([h.strip() for h in header])
    if dupes:
        warnings.append(f"Duplicate column names renamed: {', '.join(sorted(dupes))}")

    rows: list[Row] = []
    try:
        for i, raw in enumerate(reader, start=2):
            if not any(cell.strip() for cell in raw):
                continue
            if len(raw) != len(columns):
                warnings.append(f"Row {i}: expected {len(columns)} fields, got {len(raw)}")
                raw = (raw + [""] * len(columns))[: len(columns)]
            rows.append(dict(zip(columns, (c.strip() for c in raw), strict=True)))
    except csv.Error as e:
        raise IngestError(f"Malformed CSV in {p} near row {len(rows) + 2}: {e}") from None
    return Table(source=str(p), columns=columns, rows=rows, warnings=warnings)


def load_xlsx(path: str | Path, sheet: str | None = None) -> Table:
    """Load the first (or named) sheet of an XLSX export. Needs openpyxl."""
    try:
        import openpyxl
    except ImportError as e:
        raise IngestError(
            "XLSX support requires the optional dependency openpyxl. "
            "Install it with: pip install 'opencoworking[xlsx]' "
            "or export the sheet as CSV instead."
        ) from e
    p = Path(path)
    if not p.is_file():
        raise IngestError(f"File not found: {p}")
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    try:
        header = next(it)
    except StopIteration:
        raise IngestError(f"Empty sheet in {p}") from None
    columns, _ = _dedupe_columns([str(h).strip() if h is not None else "" for h in header])
    rows: list[Row] = []
    for raw in it:
        cells = ["" if v is None else str(v).strip() for v in raw]
        if not any(cells):
            continue
        cells = (cells + [""] * len(columns))[: len(columns)]
        rows.append(dict(zip(columns, cells, strict=True)))
    wb.close()
    return Table(source=str(p), columns=columns, rows=rows)


def load_table(path: str | Path) -> Table:
    """Load a CSV or XLSX file based on extension."""
    suffix = Path(path).suffix.lower()
    if suffix in (".csv", ".txt", ".tsv"):
        return load_csv(path)
    if suffix == ".xlsx":
        return load_xlsx(path)
    raise IngestError(f"Unsupported file type '{suffix}'. Supported: .csv, .tsv, .txt, .xlsx")


def _dedupe_columns(names: list[str]) -> tuple[list[str], set[str]]:
    seen: dict[str, int] = {}
    out: list[str] = []
    dupes: set[str] = set()
    for idx, name in enumerate(names):
        base = name or f"column_{idx + 1}"
        if base in seen:
            seen[base] += 1
            dupes.add(base)
            out.append(f"{base}_{seen[base]}")
        else:
            seen[base] = 1
            out.append(base)
    return out, dupes
