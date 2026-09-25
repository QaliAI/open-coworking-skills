"""Engagement preflight: screen a client export folder before any analysis.

Paid engagements start by receiving files from an operator. The failure modes
that matter most are the boring ones: a credentials file swept into a zip, a
full database dump, a spreadsheet full of payment-card numbers, or an export
with direct-contact columns nobody remembered to redact.

This module scans a client-supplied directory and returns a deterministic
verdict per file. It never modifies, moves, or copies an input; it only reads
(and only a bounded prefix for content patterns). Blocking issues stop the
engagement until a human either removes the file or passes ``--allow-unsafe``,
which is recorded in the engagement manifest.

Categories
----------
``blocked``  secrets or restricted data (credentials, key material, payment
             card numbers, government IDs, bank details, database dumps).
``warning``  personal data present, free-text columns, unsupported file
             types, oversized files. Analysis continues; handling is logged.
``ok``       tabular, readable, nothing sensitive detected.

Nothing here is a guarantee: pattern scanning reduces risk, it does not
certify a folder is safe. The report says so.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .ingest import IngestError, load_table
from .redact import CARD_RE, EMAIL_RE, _luhn_ok  # single source of truth for patterns

# --- File-level rules -------------------------------------------------------

TABULAR_SUFFIXES = {".csv", ".tsv", ".txt", ".xlsx"}
BLOCKED_SUFFIXES = {
    ".pem", ".key", ".ppk", ".pfx", ".p12", ".jks", ".keystore", ".asc", ".gpg",
    ".sql", ".db", ".sqlite", ".sqlite3", ".dump", ".bak", ".kdbx", ".env",
}
BLOCKED_NAME_PATTERNS = [
    re.compile(r"^\.env", re.I),
    re.compile(r"(credential|secret|password|passwd|api[-_]?key|token|id_rsa|private[-_]?key)",
               re.I),
    re.compile(r"(full|entire|whole)[-_]?(dump|backup|database|db)", re.I),
]
# Files reviewers should look at but which never block: we simply do not
# analyse them, and say so.
REVIEW_SUFFIXES = {".pdf", ".doc", ".docx", ".xls", ".zip", ".7z", ".rar", ".png",
                   ".jpg", ".jpeg", ".msg", ".eml", ".json", ".xml"}

DEFAULT_MAX_FILE_BYTES = 64 * 1024 * 1024   # 64 MiB
SECRET_SCAN_BYTES = 4 * 1024 * 1024         # content patterns over the first 4 MiB

# --- Content patterns ------------------------------------------------------

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws_access_key_id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    # Separators cover CSV cells ('key,value') as well as key=value files.
    ("aws_secret_access_key",
     re.compile(r"aws_?secret_?access_?key\s*[:=,]\s*[\"']?\S{16,}", re.I)),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}\b")),
    ("stripe_live_key", re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{10,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b")),
    ("basic_auth_url", re.compile(r"://[^/\s:@]{2,}:[^/\s@]{2,}@")),
    ("generic_secret_assignment",
     re.compile(r"\b(?:password|passwd|client_secret|api_key|apikey|access_token|"
                r"refresh_token|secret_key|private_key)\b\s*[:=,]\s*[\"']?\S{6,}", re.I)),
]

# Columns whose mere presence means restricted data: these should never travel
# through an analytics engagement.
RESTRICTED_COLUMNS = {
    "password", "password_hash", "passwd", "ssn", "social_security_number",
    "national_id", "passport_number", "passport_no", "drivers_license",
    "license_number", "dob", "date_of_birth", "birth_date", "card_number",
    "card_no", "credit_card", "cc_number", "cvv", "cvc", "iban", "swift",
    "bank_account", "account_number", "routing_number", "tax_id", "vat_id",
    "security_answer", "pin", "otp_seed", "mfa_seed", "api_key", "secret",
}

# Columns carrying direct identifiers. Presence is a warning, not a block:
# analysis needs them far less often than operators assume, and the redactor
# handles what must appear.
PII_COLUMN_HINTS = {
    "email", "email_address", "contact_email", "personal_email", "phone",
    "phone_number", "mobile", "mobile_number", "cell", "telephone", "fax",
    "first_name", "last_name", "full_name", "given_name", "surname",
    "family_name", "contact_name", "member_name", "fullname", "display_name",
    "address", "street", "street_address", "postal_code", "zip", "date_of_birth",
    "linkedin", "twitter", "instagram", "whatsapp", "emergency_contact",
    "emergency_phone",
}

FREE_TEXT_COLUMN_HINTS = {
    "notes", "note", "comments", "comment", "description", "message", "text",
    "summary", "details", "internal_notes", "review_text", "body", "reason",
    "lost_reason", "body_html",
}


def normalize_column(name: str) -> str:
    """Lowercase, strip punctuation, collapse separators to single underscores."""
    cleaned = re.sub(r"[^0-9A-Za-z]+", "_", name.strip().lower())
    return re.sub(r"_+", "_", cleaned).strip("_")


@dataclass
class FileCheck:
    """Preflight verdict for one client-supplied file."""

    path: str                 # path relative to the engagement input root
    size_bytes: int
    status: str               # ok | warning | blocked
    findings: list[dict[str, str]] = field(default_factory=list)
    pii_columns: list[str] = field(default_factory=list)
    restricted_columns: list[str] = field(default_factory=list)
    free_text_columns: list[str] = field(default_factory=list)
    readable: bool = False
    rows: int | None = None
    columns: list[str] = field(default_factory=list)
    secret_patterns_hit: list[str] = field(default_factory=list)
    content_scanned: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "path": self.path, "size_bytes": self.size_bytes, "status": self.status,
            "findings": self.findings, "pii_columns": self.pii_columns,
            "restricted_columns": self.restricted_columns,
            "free_text_columns": self.free_text_columns,
            "readable_as_table": self.readable, "rows": self.rows,
            "columns": self.columns, "secret_patterns_hit": self.secret_patterns_hit,
            "content_scanned": self.content_scanned,
        }

    def _add(self, code: str, severity: str, message: str) -> None:
        self.findings.append({"code": code, "severity": severity, "message": message})
        if severity == "blocked":
            self.status = "blocked"
        elif severity == "warning" and self.status != "blocked":
            self.status = "warning"


@dataclass
class PreflightResult:
    """Verdict for a whole engagement input directory."""

    root: str
    files: list[FileCheck]
    policy: str                    # report | strict
    max_file_bytes: int
    excluded: list[str] = field(default_factory=list)   # dirs/files skipped by rule
    notes: list[str] = field(default_factory=list)

    @property
    def blocked(self) -> list[FileCheck]:
        return [f for f in self.files if f.status == "blocked"]

    @property
    def warnings(self) -> list[FileCheck]:
        return [f for f in self.files if f.status == "warning"]

    @property
    def ok(self) -> bool:
        return not self.blocked

    def as_dict(self) -> dict[str, object]:
        return {
            "input_root": self.root,
            "policy": self.policy,
            "max_file_bytes": self.max_file_bytes,
            "file_count": len(self.files),
            "files": [f.as_dict() for f in self.files],
            "blocking_count": len(self.blocked),
            "warning_count": len(self.warnings),
            "excluded": self.excluded,
            "notes": self.notes,
            "guarantee_note": "Pattern-based screening reduces risk; it does not "
                              "certify that a folder is free of personal or secret data.",
        }


def _scan_content(path: Path) -> tuple[list[str], list[str], bool]:
    """Return (secret pattern names hit, restricted-column names hit, scanned).

    Reads at most SECRET_SCAN_BYTES. Payment-card numbers are validated with
    Luhn so invoice IDs and long account codes do not trip the check.
    """
    try:
        raw = path.read_bytes()[:SECRET_SCAN_BYTES]
    except OSError:
        return [], [], False
    text = raw.decode("utf-8", errors="replace")
    hits = [name for name, pattern in SECRET_PATTERNS if pattern.search(text)]
    restricted: set[str] = set()
    if any(_luhn_ok(m) for m in CARD_RE.findall(text)
           if 13 <= len(re.sub(r"\D", "", m)) <= 19):
        restricted.add("payment_card_number")
    return hits, sorted(restricted), True


def check_file(path: Path, root: Path, *, policy: str = "report",
               max_file_bytes: int = DEFAULT_MAX_FILE_BYTES) -> FileCheck:
    """Screen one file. Never raises on unreadable or odd inputs."""
    rel = str(path.relative_to(root)) if path != root else path.name
    check = FileCheck(path=rel.replace("\\", "/"),
                      size_bytes=path.stat().st_size if path.exists() else 0,
                      status="ok")
    suffix = path.suffix.lower()
    name = path.name

    if check.size_bytes > max_file_bytes:
        check._add("oversized_file", "blocked",
                   f"{check.size_bytes} bytes exceeds the {max_file_bytes}-byte limit; "
                   "large dumps must be split into named exports before analysis.")
    for pattern in BLOCKED_NAME_PATTERNS:
        if pattern.search(name):
            check._add("sensitive_filename", "blocked",
                       f"filename '{name}' matches a credentials/secret/dump pattern.")
            break
    if suffix in BLOCKED_SUFFIXES:
        check._add("blocked_file_type", "blocked",
                   f"'{suffix}' files can carry credentials or whole-database dumps "
                   "and are never analysed by this tool.")
    if suffix in REVIEW_SUFFIXES:
        check._add("not_tabular", "warning",
                   f"'{suffix}' is not an analysable export; it is listed for human "
                   "review only.")

    # Content patterns. XLSX is a zip container, so content is read per-sheet
    # below instead of raw bytes.
    if suffix != ".xlsx" and path.is_file():
        hits, restricted, scanned = _scan_content(path)
        check.content_scanned = scanned
        for hit in hits:
            check.secret_patterns_hit.append(hit)
            check._add("secret_pattern", "blocked",
                       f"content matches '{hit}' - this file looks like it contains a "
                       "credential; remove it before running an engagement.")
        for col in restricted:
            check.restricted_columns.append(col)
            check._add("restricted_data", "blocked",
                       f"content contains {col.replace('_', ' ')} patterns; restricted "
                       "data must not enter an analysis engagement.")

    if suffix in TABULAR_SUFFIXES and check.status != "blocked":
        try:
            table = load_table(path)
        except IngestError as e:
            check._add("unreadable", "warning", f"could not be read as a table: {e}")
            return check
        check.readable = True
        check.rows = len(table.rows)
        check.columns = list(table.columns)
        if table.warnings:
            check._add("structural_warnings", "warning",
                       "; ".join(table.warnings[:3]))
        if not table.rows:
            check._add("empty_table", "warning", "header present but no data rows.")
        for col in table.columns:
            key = normalize_column(col)
            if key in RESTRICTED_COLUMNS:
                check.restricted_columns.append(col)
                check._add("restricted_column", "blocked",
                           f"column '{col}' is restricted data and must be removed "
                           "before analysis.")
            elif key in PII_COLUMN_HINTS:
                check.pii_columns.append(col)
            elif key in FREE_TEXT_COLUMN_HINTS:
                check.free_text_columns.append(col)
        if check.pii_columns:
            check._add("personal_data_columns", "warning",
                       "contains direct identifiers in: "
                       + ", ".join(check.pii_columns[:8]))
        if check.free_text_columns:
            check._add("free_text_columns", "warning",
                       "free-text columns can contain personal data and unstructured "
                       "third-party content: " + ", ".join(check.free_text_columns[:8]))
        # Any email-shaped value anywhere (not just hinted columns) is a warning.
        if not check.pii_columns:
            for row in table.rows[:200]:
                if any(EMAIL_RE.search(v) for v in row.values()):
                    check._add("personal_data_values", "warning",
                               "email-shaped values found in columns that are not named "
                               "as contact fields.")
                    break
        if policy == "strict" and (check.pii_columns or check.free_text_columns):
            check._add("pii_policy_strict", "blocked",
                       "--pii-policy strict refuses files carrying identifiers; supply a "
                       "redacted export instead.")
    return check


def scan_directory(input_dir: str | Path, *, policy: str = "report",
                   max_file_bytes: int = DEFAULT_MAX_FILE_BYTES) -> PreflightResult:
    """Screen every candidate file under ``input_dir`` (non-recursive at depth 1+)."""
    root = Path(input_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"input directory not found: {root}")
    files: list[FileCheck] = []
    excluded: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part.startswith(".") or part in {"node_modules", "__pycache__"}
               for part in rel_parts):
            excluded.append(str(path.relative_to(root)).replace("\\", "/"))
            continue
        if path.name.startswith("~$"):
            excluded.append(str(path.relative_to(root)).replace("\\", "/"))
            continue
        files.append(check_file(path, root, policy=policy, max_file_bytes=max_file_bytes))
    notes = [
        "Screening reads files; it never copies, moves, or modifies them.",
        "Only files in the engagement's own input directory are considered.",
        "Blocked files must be removed (or overridden with --allow-unsafe, which is "
        "recorded in the engagement manifest) before analysis runs.",
    ]
    return PreflightResult(root=str(root), files=files, policy=policy,
                           max_file_bytes=max_file_bytes, excluded=sorted(excluded),
                           notes=notes)
