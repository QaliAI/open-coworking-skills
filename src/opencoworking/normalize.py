"""Normalization utilities: dates, money, lead sources, and safe CSV cells.

All functions are deterministic and side-effect free.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# --- Dates -----------------------------------------------------------------

# Order matters: ISO first (unambiguous), then formats with month names,
# then slash formats interpreted per the day_first flag.
_ISO = ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M")
_NAMED = ("%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y", "%b %d %Y")
_SLASH_MDY = ("%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m/%d/%Y %H:%M")
_SLASH_DMY = ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d/%m/%Y %H:%M")


def parse_date(value: str, day_first: bool = False) -> date | None:
    """Parse a date string in common export formats; None if unparseable.

    Ambiguous slash dates (e.g. 03/04/2026) are interpreted as month-first
    unless ``day_first`` is True. Callers analysing exports should surface
    which convention was assumed rather than silently trusting it.
    """
    v = value.strip()
    if not v:
        return None
    # Strip timezone suffixes like 'Z' or '+00:00' for date-only purposes.
    v = re.sub(r"(Z|[+-]\d{2}:?\d{2})$", "", v).strip()
    slash = _SLASH_DMY + _SLASH_MDY if day_first else _SLASH_MDY + _SLASH_DMY
    for fmt in _ISO + _NAMED + slash:
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    # Final attempt: ISO with microseconds / fromisoformat
    try:
        return datetime.fromisoformat(v).date()
    except ValueError:
        return None


def parse_datetime(value: str) -> datetime | None:
    """Parse an ISO-ish timestamp; None if unparseable."""
    v = value.strip()
    if not v:
        return None
    v = v.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(v)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None


# --- Money -----------------------------------------------------------------

_CURRENCY_SIGNS = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR", "C$": "CAD"}
_MONEY_RE = re.compile(r"^[^\d\-.(]*(\(?)\s*(-?[\d.,\s]+)\s*(\)?)\s*[A-Za-z]{0,3}$")


def parse_money(value: str) -> Decimal | None:
    """Parse a money string ('$1,200.50', '1.200,50 €', '(300)') to Decimal.

    Returns None when the value is empty or not a number. Parenthesised values
    are treated as negative. Currency symbols/codes are ignored; use
    ``detect_currency`` if the currency itself matters.
    """
    v = value.strip()
    if not v:
        return None
    m = _MONEY_RE.match(v)
    if not m:
        return None
    open_paren, num, close_paren = m.groups()
    num = num.replace(" ", "")
    # European style: 1.234,56 -> 1234.56
    if "," in num and "." in num:
        if num.rfind(",") > num.rfind("."):
            num = num.replace(".", "").replace(",", ".")
        else:
            num = num.replace(",", "")
    elif "," in num:
        # Treat a comma followed by exactly 2 digits at end as decimal sep.
        if re.search(r",\d{2}$", num):
            num = num.replace(",", ".")
        else:
            num = num.replace(",", "")
    try:
        d = Decimal(num)
    except InvalidOperation:
        return None
    if open_paren and close_paren:
        d = -d
    return d


def detect_currency(value: str) -> str | None:
    """Return an ISO currency code hinted by the string, if any."""
    v = value.strip()
    m = re.search(r"\b([A-Z]{3})\b", v)
    if m and m.group(1) in {"USD", "EUR", "GBP", "CAD", "AUD", "JPY", "INR", "CHF", "SEK", "NZD"}:
        return m.group(1)
    for sign, code in _CURRENCY_SIGNS.items():
        if sign in v:
            return code
    return None


# --- Lead sources ----------------------------------------------------------

# Canonical lead-source buckets. Operators can extend via extra_rules.
_SOURCE_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"google\s*(ads|adwords|ppc|paid|cpc)|adwords", re.I), "google-ads"),
    (re.compile(r"\bgbp\b|google\s*(business|maps|my\s*business)|\bgmb\b", re.I), "google-business-profile"),
    (re.compile(r"google|organic|seo|search(?!\s*console)", re.I), "organic-search"),
    (re.compile(r"\b(meta|facebook|instagram|fb|ig)\b\s*(ads?)?", re.I), "meta"),
    (re.compile(r"linked\s*in", re.I), "linkedin"),
    (re.compile(r"walk\s*[- ]?in|drop\s*[- ]?in|street", re.I), "walk-in"),
    (re.compile(r"referr?al|word\s*of\s*mouth|\bwom\b|member\s*referr?", re.I), "referral"),
    (re.compile(r"broker|agent|liquid\s*space|liquidspace|upsuite|coworker\.com|deskpass|instant\s*offices?", re.I), "broker-marketplace"),
    (re.compile(r"event|open\s*house|meetup|tour\s*day", re.I), "event"),
    (re.compile(r"web\s*site|website|web\s*form|contact\s*form|landing", re.I), "website"),
    (re.compile(r"e-?mail|newsletter|mailchimp|brevo", re.I), "email-marketing"),
    (re.compile(r"phone|call|inbound\s*call", re.I), "phone"),
    (re.compile(r"partner|virtual\s*office\s*provider|\bvo\s*partner\b", re.I), "partner"),
]


def normalize_source(
    value: str, extra_rules: list[tuple[str, str]] | None = None
) -> tuple[str, str]:
    """Map a raw lead-source label to a canonical bucket.

    Returns (canonical, confidence) where confidence is 'exact' (rule match),
    'unknown' (blank), or 'unmapped' (no rule matched; original kept).
    """
    v = value.strip()
    if not v:
        return ("unknown", "unknown")
    if extra_rules:
        for pattern, target in extra_rules:
            if re.search(pattern, v, re.I):
                return (target, "exact")
    for pattern, target in _SOURCE_RULES:
        if pattern.search(v):
            return (target, "exact")
    return (v.lower().strip().replace(" ", "-"), "unmapped")


# --- CSV safety ------------------------------------------------------------

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_cell(value: str) -> str:
    """Neutralize spreadsheet formula injection in a cell destined for CSV.

    Cells starting with =, +, -, @ are prefixed with a single quote so
    spreadsheet apps treat them as text. Pure numbers (including negatives)
    are left alone.
    """
    v = value
    if v and v.startswith(_FORMULA_PREFIXES):
        try:
            float(v.replace(",", ""))
            return v  # plain negative/positive number, safe
        except ValueError:
            return "'" + v
    return v
