"""PII redaction for coworking data.

Replaces emails, phone numbers, and (optionally) known person names with
stable pseudonyms so redacted data stays joinable across files. Deterministic:
the same input with the same salt produces the same pseudonyms.

This is pattern-based redaction. It reduces, but cannot guarantee elimination
of, personal data — a human must still review anything leaving the operator's
control. That caveat is repeated in the skill that uses this module.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Phone: international or national formats with 7+ digits, tolerant of
# separators. Deliberately conservative to avoid eating invoice numbers.
PHONE_RE = re.compile(
    r"(?<![\d/-])(\+?\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)"
)
# Payment-card-like sequences (13-19 digits with optional separators),
# validated with Luhn before redaction to avoid false positives.
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


@dataclass
class Redactor:
    """Stateful redactor producing stable pseudonyms."""

    salt: str = "opencoworking"
    names: list[str] = field(default_factory=list)
    counters: dict[str, dict[str, str]] = field(default_factory=dict)
    replacements: int = 0

    def _token(self, kind: str, value: str) -> str:
        bucket = self.counters.setdefault(kind, {})
        key = value.lower()
        if key not in bucket:
            digest = hashlib.sha256(f"{self.salt}:{kind}:{key}".encode()).hexdigest()[:8]
            bucket[key] = f"[{kind.upper()}-{digest}]"
        return bucket[key]

    def redact_text(self, text: str) -> str:
        def email_sub(m: re.Match[str]) -> str:
            self.replacements += 1
            return self._token("email", m.group(0))

        def phone_sub(m: re.Match[str]) -> str:
            self.replacements += 1
            return self._token("phone", m.group(0))

        def card_sub(m: re.Match[str]) -> str:
            digits = re.sub(r"\D", "", m.group(0))
            if 13 <= len(digits) <= 19 and _luhn_ok(digits):
                self.replacements += 1
                return self._token("card", digits)
            return m.group(0)

        out = EMAIL_RE.sub(email_sub, text)
        out = CARD_RE.sub(card_sub, out)
        out = PHONE_RE.sub(phone_sub, out)
        for name in sorted(self.names, key=len, reverse=True):
            if not name.strip():
                continue
            pattern = re.compile(rf"\b{re.escape(name.strip())}\b", re.I)
            if pattern.search(out):
                out = pattern.sub(self._token("name", name), out)
                self.replacements += 1
        return out

    def redact_row(self, row: dict[str, str]) -> dict[str, str]:
        return {k: self.redact_text(v) for k, v in row.items()}


def collect_names(rows: list[dict[str, str]], name_columns: list[str]) -> list[str]:
    """Gather distinct person names from the given columns of a table."""
    names: set[str] = set()
    for row in rows:
        for col in name_columns:
            v = row.get(col, "").strip()
            if v and len(v) >= 3:
                names.add(v)
    return sorted(names)
