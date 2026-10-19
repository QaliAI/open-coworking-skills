"""Coworking Revenue & Operations Health Check: one command, one deliverable.

This module composes the deterministic engine (``ingest``, ``preflight``,
``quality``, ``analyze``, ``wave2``, ``metrics``, ``redact``) into a single
repeatable paid-engagement run. It adds no arithmetic of its own: every number
in the bundle comes from an existing engine function, each of which already
carries its formula contract, exclusions, and caveats.

Pipeline of one run:

1. preflight   screen the client folder (secrets, restricted data, PII).
2. identify    guess the entity of each file from column signatures only.
3. map         rename headers onto the canonical schema; log every rename and
               every ambiguity instead of guessing.
4. run         the supported diagnostics, skipping (and disclosing) any module
               whose inputs are missing.
5. findings    fact / calculation / inference / recommendation records, each
               with data used, calculation, confidence, and limitation.
6. prioritise  a documented ranking of the top opportunities.
7. emit        a JSON bundle the report renderer (and tests) consume.

Nothing here sends, charges, or deletes anything, and no client export is ever
copied into the output directory.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

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
from .ingest import Table, load_table
from .metrics import ZERO, logo_churn, revenue_churn
from .normalize import detect_currency, parse_date, parse_money
from .preflight import PreflightResult, normalize_column, scan_directory
from .quality import (
    check_blank_values,
    check_date_parseability,
    check_duplicates,
)
from .redact import Redactor
from .wave2 import (
    collections_queue,
    location_benchmark,
    occupancy_forecast,
    pricing_audit,
    reconcile_report,
    renewal_scan,
    room_yield,
)

SERVICE_NAME = "Coworking Revenue & Operations Health Check"
SERVICE_VERSION = "1.0"

# Canonical column sets, mirrored from schemas/coworking.schema.json
# (tests/unit/test_healthcheck_mapping.py fails if they drift).
CANONICAL_COLUMNS: dict[str, list[str]] = {
    "locations": ["location_id", "name", "address", "city", "market", "timezone",
                  "opened_on", "status", "sellable_workstations"],
    "inventory": ["unit_id", "location_id", "unit_type", "name", "capacity", "sellable",
                  "out_of_service", "list_price", "floor", "amenities", "available_from",
                  "notes"],
    "contacts": ["contact_id", "first_name", "last_name", "email", "phone", "company_id",
                 "created_at", "consent_marketing"],
    "companies": ["company_id", "name", "industry", "size", "created_at"],
    "leads": ["lead_id", "contact_id", "company_id", "location_id", "created_at", "source",
              "campaign", "inquiry_product", "status", "owner", "first_response_at",
              "next_action", "next_action_date", "lost_reason", "expected_move_in"],
    "deals": ["deal_id", "lead_id", "company_id", "location_id", "product", "stage",
              "created_at", "updated_at", "expected_value", "expected_move_in", "owner",
              "next_action", "next_action_date", "lost_reason"],
    "tours": ["tour_id", "lead_id", "deal_id", "location_id", "scheduled_at", "completed_at",
              "status", "toured_product", "host", "next_action"],
    "memberships": ["membership_id", "company_id", "location_id", "product", "unit_id",
                    "start_date", "end_date", "term_months", "notice_date", "renewal_date",
                    "contracted_rate", "list_rate", "discount_pct", "deposit", "status",
                    "billing_frequency", "complimentary"],
    "members": ["member_id", "contact_id", "company_id", "membership_id", "status",
                "onboarded_on"],
    "invoices": ["invoice_id", "company_id", "membership_id", "issue_date", "due_date",
                 "amount", "tax", "status", "paid_date"],
    "payments": ["payment_id", "invoice_id", "amount", "paid_at", "method", "status"],
    "room_bookings": ["booking_id", "location_id", "room_unit_id", "company_id", "booked_by",
                      "start_at", "end_at", "attendees", "amount", "member_booking"],
    "events": ["event_id", "location_id", "name", "date", "attendees", "revenue", "cost"],
    "reviews": ["review_id", "location_id", "platform", "rating", "date", "text", "response"],
    "virtual_office_partners": ["partner_id", "partner_name", "billing_model",
                                "client_company_id", "monthly_fee", "revenue_share_pct",
                                "active", "start_date", "end_date"],
}

# Required columns per entity (schema `required` lists).
REQUIRED_COLUMNS: dict[str, list[str]] = {
    "locations": ["location_id", "name"],
    "inventory": ["unit_id", "location_id", "unit_type", "capacity"],
    "contacts": ["contact_id"],
    "companies": ["company_id", "name"],
    "leads": ["lead_id", "created_at"],
    "deals": ["deal_id", "stage"],
    "tours": ["tour_id", "status"],
    "memberships": ["membership_id", "company_id", "product", "start_date", "status"],
    "members": ["member_id"],
    "invoices": ["invoice_id", "amount", "status"],
    "payments": ["payment_id", "amount", "status"],
    "room_bookings": ["booking_id", "room_unit_id", "start_at", "end_at"],
    "events": ["event_id", "date"],
    "reviews": ["review_id", "platform", "rating"],
    "virtual_office_partners": ["partner_id", "partner_name", "billing_model",
                               "client_company_id"],
}

# Columns the diagnostics need that a vendor export will almost always spell
# differently. Aliases are documented per vendor in adapters/ (e.g. HubSpot
# "Deal Stage", Nexudus "contract price", OfficeRnD/Optix "plan price").
COLUMN_ALIASES: dict[str, dict[str, str]] = {
    "leads": {
        "lead_source": "source", "source_channel": "source", "channel": "source",
        "lead_status": "status", "stage": "status", "state": "status",
        "first_response": "first_response_at", "responded_at": "first_response_at",
        "first_contacted_at": "first_response_at", "response_time_at": "first_response_at",
        "created": "created_at", "created_date": "created_at", "inquiry_date": "created_at",
        "inquiry_at": "created_at", "lead_created_at": "created_at",
        "interested_in": "inquiry_product", "inquiry_type": "inquiry_product",
        "product": "inquiry_product", "product_interest": "inquiry_product",
        "assigned_to": "owner", "owner_name": "owner", "agent": "owner",
        "location": "location_id", "site": "location_id", "building": "location_id",
        "account_id": "company_id", "client_id": "company_id", "customer_id": "company_id",
        "next_step": "next_action", "follow_up": "next_action",
        "follow_up_date": "next_action_date", "next_step_date": "next_action_date",
    },
    "deals": {
        "deal_stage": "stage", "pipeline_stage": "stage", "stage_name": "stage",
        "deal_status": "stage", "state": "stage",
        "amount": "expected_value", "value": "expected_value", "deal_value": "expected_value",
        "monthly_value": "expected_value", "mrr": "expected_value",
        "deal_owner": "owner", "owner_name": "owner", "assigned_to": "owner",
        "last_activity_date": "updated_at", "modified_at": "updated_at",
        "stage_updated_at": "updated_at", "last_modified": "updated_at",
        "created": "created_at", "created_date": "created_at", "deal_created_at": "created_at",
        "next_step": "next_action", "next_step_date": "next_action_date",
        "close_date": "expected_move_in", "expected_close": "expected_move_in",
        "account_id": "company_id", "customer_id": "company_id", "client_id": "company_id",
        "location": "location_id", "site": "location_id",
    },
    "tours": {
        "tour_status": "status", "state": "status",
        "tour_date": "scheduled_at", "scheduled_date": "scheduled_at", "scheduled": "scheduled_at",
        "tour_completed_at": "completed_at", "completed_on": "completed_at",
        "tour_host": "host", "host_name": "host", "guide": "host",
        "next_step": "next_action", "follow_up": "next_action",
        "product": "toured_product", "tour_product": "toured_product",
        "prospect_id": "lead_id", "location": "location_id", "site": "location_id",
    },
    "memberships": {
        "monthly_rate": "contracted_rate", "contract_price": "contracted_rate",
        "price": "contracted_rate", "rate": "contracted_rate",
        "monthly_fee": "contracted_rate", "monthly_revenue": "contracted_rate",
        "agreed_rate": "contracted_rate",
        "list_price": "list_rate", "plan_price": "list_rate", "tariff_price": "list_rate",
        "rack_rate": "list_rate", "standard_price": "list_rate",
        "contract_start": "start_date", "start": "start_date", "commenced_on": "start_date",
        "contract_end": "end_date", "end": "end_date", "expires_on": "end_date",
        "contract_status": "status", "membership_status": "status", "state": "status",
        "product_type": "product", "plan": "product", "membership_type": "product",
        "plan_type": "product", "agreement_type": "product",
        "unit": "unit_id", "space_id": "unit_id", "resource_id": "unit_id",
        "desk_id": "unit_id", "office_id": "unit_id", "assigned_space": "unit_id",
        "account_id": "company_id", "customer_id": "company_id", "client_id": "company_id",
        "organization_id": "company_id", "tenant_id": "company_id",
        "billing_period": "billing_frequency", "frequency": "billing_frequency",
        "is_comp": "complimentary", "comp": "complimentary", "internal": "complimentary",
        "renewal": "renewal_date", "renewal_on": "renewal_date", "renews_on": "renewal_date",
        "notice_given_on": "notice_date", "cancellation_notice_date": "notice_date",
        "term": "term_months", "contract_months": "term_months",
        "security_deposit": "deposit", "discount": "discount_pct",
        "location": "location_id", "site": "location_id",
    },
    "inventory": {
        "space_id": "unit_id", "resource_id": "unit_id", "desk_id": "unit_id",
        "office_id": "unit_id", "inventory_id": "unit_id", "room_id": "unit_id",
        "type": "unit_type", "space_type": "unit_type", "product_type": "unit_type",
        "resource_type": "unit_type", "category": "unit_type",
        "seats": "capacity", "workstations": "capacity", "capacity_workstations": "capacity",
        "max_occupancy": "capacity", "headcount": "capacity",
        "price": "list_price", "list_rate": "list_price", "rack_rate": "list_price",
        "monthly_price": "list_price", "standard_rate": "list_price",
        "is_sellable": "sellable", "available": "sellable", "active": "sellable",
        "oos": "out_of_service", "maintenance": "out_of_service",
        "offline": "out_of_service", "is_out_of_service": "out_of_service",
        "location": "location_id", "site": "location_id", "building_id": "location_id",
    },
    "invoices": {
        "total": "amount", "invoice_total": "amount", "amount_due": "amount",
        "subtotal": "amount", "balance": "amount",
        "invoice_status": "status", "payment_status": "status", "state": "status",
        "invoice_date": "issue_date", "issued_on": "issue_date", "date": "issue_date",
        "due_on": "due_date", "payment_due_date": "due_date",
        "paid_at": "paid_date", "payment_date": "paid_date",
        "client_id": "company_id", "account_id": "company_id", "customer_id": "company_id",
        "contract_id": "membership_id", "subscription_id": "membership_id",
        "plan_id": "membership_id",
    },
    "payments": {
        "payment_date": "paid_at", "date": "paid_at", "paid_on": "paid_at",
        "payment_status": "status", "state": "status",
        "payment_method": "method", "method_type": "method", "type": "method",
        "invoice_ref": "invoice_id", "invoice_number": "invoice_id", "invoice": "invoice_id",
    },
    "contacts": {
        "email_address": "email", "work_email": "email", "primary_email": "email",
        "phone_number": "phone", "mobile": "phone", "mobile_number": "phone",
        "telephone": "phone", "cell": "phone",
        "firstname": "first_name", "given_name": "first_name",
        "lastname": "last_name", "surname": "last_name", "family_name": "last_name",
        "account_id": "company_id", "customer_id": "company_id", "client_id": "company_id",
    },
    "companies": {
        "company_name": "name", "account_name": "name", "organization_name": "name",
        "client_name": "name", "business_name": "name",
        "customer_id": "company_id", "account_id": "company_id", "client_id": "company_id",
        "employee_count": "size", "headcount": "size",
    },
    "locations": {
        "site_id": "location_id", "building_id": "location_id", "location": "location_id",
        "location_name": "name", "site_name": "name", "building_name": "name",
        "tz": "timezone", "time_zone": "timezone",
        "sellable_capacity": "sellable_workstations", "workstation_count": "sellable_workstations",
    },
    "room_bookings": {
        "start": "start_at", "start_time": "start_at", "booking_start": "start_at",
        "end": "end_at", "end_time": "end_at", "booking_end": "end_at",
        "room_id": "room_unit_id", "resource_id": "room_unit_id", "space_id": "room_unit_id",
        "revenue": "amount", "charge": "amount", "total": "amount",
        "is_member": "member_booking", "member_rate": "member_booking",
        "location": "location_id", "account_id": "company_id", "client_id": "company_id",
    },
    "virtual_office_partners": {
        "partner": "partner_name", "provider": "partner_name",
        "billing_type": "billing_model", "model": "billing_model",
        "client_id": "client_company_id", "company_id": "client_company_id",
        "fee": "monthly_fee", "is_active": "active",
    },
    "members": {
        "account_id": "company_id", "client_id": "company_id",
        "onboarded_at": "onboarded_on", "onboarding_date": "onboarded_on",
    },
}

# Date columns worth validating per entity (drives quality checks).
DATE_COLUMNS: dict[str, list[str]] = {
    "leads": ["created_at", "first_response_at", "next_action_date", "expected_move_in"],
    "deals": ["created_at", "updated_at", "next_action_date", "expected_move_in"],
    "tours": ["scheduled_at", "completed_at"],
    "memberships": ["start_date", "end_date", "notice_date", "renewal_date"],
    "invoices": ["issue_date", "due_date", "paid_date"],
    "payments": ["paid_at"],
    "room_bookings": ["start_at", "end_at"],
    "locations": ["opened_on"],
    "virtual_office_partners": ["start_date", "end_date"],
    "contacts": ["created_at"],
    "companies": ["created_at"],
    "members": ["onboarded_on"],
}

PRIMARY_KEYS: dict[str, list[str]] = {
    "locations": ["location_id"], "inventory": ["unit_id"], "contacts": ["contact_id"],
    "companies": ["company_id"], "leads": ["lead_id"], "deals": ["deal_id"],
    "tours": ["tour_id"], "memberships": ["membership_id"], "members": ["member_id"],
    "invoices": ["invoice_id"], "payments": ["payment_id"], "room_bookings": ["booking_id"],
    "events": ["event_id"], "reviews": ["review_id"],
    "virtual_office_partners": ["partner_id"],
}

# Entities the diagnostics never consume: listed, quality-checked, never
# silently treated as one of the analysis inputs.
CONTEXT_ONLY_ENTITIES = {"members", "events", "reviews"}

KIND_ORDER = ("fact", "calculation", "inference", "recommendation")

# Columns that carry money, and the symbols for the ISO codes the broader
# engine can already detect. Nothing is converted between currencies.
MONEY_COLUMNS = ("list_price", "contracted_rate", "list_rate", "amount",
                 "expected_value", "deposit", "monthly_fee")
CURRENCY_SYMBOLS = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3", "CAD": "C$",
                    "AUD": "A$", "JPY": "\u00a5", "INR": "\u20b9", "CHF": "CHF ",
                    "SEK": "SEK ", "NZD": "NZ$"}


def detect_engagement_currency(tables: dict[str, Table]) -> dict[str, object]:
    """Report the currency the exports imply, without converting anything.

    Vendor exports usually carry bare numbers, so this is a courtesy label, not
    a guarantee: mixed or absent hints are stated rather than assumed.
    """
    hints: set[str] = set()
    for table in tables.values():
        cols = [c for c in table.columns if c in MONEY_COLUMNS]
        if not cols:
            continue
        for row in table.rows:
            for col in cols:
                code = detect_currency(row.get(col, ""))
                if code:
                    hints.add(code)
    if len(hints) == 1:
        code = next(iter(hints))
        return {"code": code, "symbol": CURRENCY_SYMBOLS.get(code, f"{code} "),
                "mixed": False, "detected": sorted(hints),
                "note": f"Money columns carry a {code} hint; amounts are printed in "
                        "that currency. No conversion is performed."}
    if hints:
        return {"code": None, "symbol": "", "mixed": True, "detected": sorted(hints),
                "note": "Money columns carry conflicting currency hints "
                        f"({', '.join(sorted(hints))}); amounts are printed as supplied "
                        "and no conversion is performed."}
    return {"code": None, "symbol": "", "mixed": False, "detected": [],
            "note": "The exports carry no currency symbol or code, so amounts are printed "
                    "as the source system supplied them (no currency was assumed and no "
                    "conversion was performed)."}


class PreflightBlocked(Exception):
    """Raised when the preflight refuses the input folder."""

    def __init__(self, result: PreflightResult):
        self.result = result
        super().__init__(
            f"preflight blocked {len(result.blocked)} file(s); see the preflight report")


@dataclass
class MappedInput:
    """One client file, identified and mapped onto the canonical schema."""

    role: str
    source: str
    entity: str | None
    identification: str            # "column signature" | "manual override"
    entity_confidence: float
    rows: int
    columns: list[str]
    renames: dict[str, str] = field(default_factory=dict)
    unmapped_columns: list[str] = field(default_factory=list)
    ambiguous_columns: list[dict[str, object]] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    context_only: bool = False
    notes: list[str] = field(default_factory=list)
    selected: bool = True          # False when another file owns this role
    superseded_by: str | None = None

    @property
    def usable(self) -> bool:
        return not self.missing_required

    def as_dict(self) -> dict[str, object]:
        return {
            "role": self.role, "source": self.source, "entity": self.entity,
            "identification": self.identification,
            "entity_confidence": self.entity_confidence, "rows": self.rows,
            "columns": self.columns, "renames": self.renames,
            "unmapped_columns": self.unmapped_columns,
            "ambiguous_columns": self.ambiguous_columns,
            "missing_required": self.missing_required,
            "context_only": self.context_only, "usable": self.usable,
            "selected": self.selected, "superseded_by": self.superseded_by,
            "notes": self.notes,
        }


# --- Mapping ----------------------------------------------------------------

def normalize_columns(table: Table, entity: str) -> tuple[Table, dict[str, str],
                                                         list[str], list[dict[str, object]]]:
    """Rename a table's headers onto the canonical schema.

    Returns (mapped table, renames, unmapped headers, ambiguities). Exact
    canonical matches win; documented aliases come second. When two source
    columns would map to the same canonical column, NEITHER is mapped and the
    conflict is reported - silently picking one would corrupt every downstream
    metric.
    """
    canonical = set(CANONICAL_COLUMNS.get(entity, []))
    aliases = COLUMN_ALIASES.get(entity, {})
    proposed: dict[str, list[str]] = {}
    for col in table.columns:
        key = normalize_column(col)
        target = key if key in canonical else aliases.get(key)
        if target:
            proposed.setdefault(target, []).append(col)

    renames: dict[str, str] = {}
    ambiguities: list[dict[str, Any]] = []
    for target, sources in proposed.items():
        if len(sources) == 1:
            renames[sources[0]] = target
        else:
            ambiguities.append({
                "canonical_column": target, "source_columns": sources,
                "reason": "more than one source column maps to this canonical column; "
                          "neither is used until the mapping is resolved by hand."})

    claimed = set(renames) | {c for a in ambiguities for c in a["source_columns"]}
    unmapped = [c for c in table.columns if c not in claimed]

    rows = [{renames.get(k, k): v for k, v in row.items()} for row in table.rows]
    mapped = Table(source=table.source, columns=[renames.get(c, c) for c in table.columns],
                   rows=rows, warnings=list(table.warnings))
    return mapped, renames, unmapped, ambiguities


def identify_entity(table: Table, override: str | None = None) -> tuple[str | None, float,
                                                                         str,
                                                                         list[tuple[str, float]]]:
    """Identify a table's entity from column signatures (never from filenames)."""
    report: Any = inspect_table(table)
    candidates = [(str(name), float(score)) for name, score in report.get("candidates", [])]
    if override:
        return override, 1.0, "manual override", candidates
    entity = report.get("likely_entity")
    confidence = float(str(report.get("confidence", 0.0)))
    return (str(entity) if entity else None), confidence, "column signature", candidates


def discover_inputs(input_dir: str | Path, *, overrides: dict[str, str] | None = None,
                    policy: str = "report", max_file_bytes: int | None = None
                    ) -> tuple[PreflightResult, list[MappedInput], list[dict[str, object]]]:
    """Screen, identify, and map every file in the engagement input folder.

    Returns (preflight, mapped inputs, ambiguity records).
    """
    from .preflight import DEFAULT_MAX_FILE_BYTES

    preflight = scan_directory(
        input_dir, policy=policy,
        max_file_bytes=max_file_bytes or DEFAULT_MAX_FILE_BYTES)
    overrides = overrides or {}
    mapped: list[MappedInput] = []
    for check in preflight.files:
        if check.status == "blocked":
            continue
        rel = check.path
        if not check.readable:
            mapped.append(MappedInput(
                role="(not analysed)", source=rel, entity=None,
                identification="unsupported file", entity_confidence=0.0,
                rows=0, columns=[], context_only=True,
                notes=["not a tabular export; listed for human review only"]))
            continue
        table = load_table(Path(preflight.root) / rel)
        override = overrides.get(rel) or overrides.get(Path(rel).name)
        entity, confidence, how, candidates = identify_entity(table, override)
        if entity is None:
            mapped.append(MappedInput(
                role="(unidentified)", source=rel, entity=None, identification=how,
                entity_confidence=confidence, rows=len(table.rows),
                columns=list(table.columns), context_only=True,
                notes=["column signature did not match any canonical entity; confirm "
                       "the schema by hand"]))
            continue
        if entity not in CANONICAL_COLUMNS:
            raise ValueError(f"--map {rel}={entity}: unknown entity '{entity}'. "
                             f"Known: {', '.join(sorted(CANONICAL_COLUMNS))}")
        mapped_table, renames, unmapped, ambiguous = normalize_columns(table, entity)
        missing = [c for c in REQUIRED_COLUMNS[entity]
                   if c not in mapped_table.columns or
                   all(not str(r.get(c, "")).strip() for r in mapped_table.rows)]
        notes: list[str] = []
        if how == "column signature" and confidence < 1.0:
            notes.append(f"identified from a {int(confidence * 100)}% column-signature match")
        if confidence < 0.75 and how == "column signature":
            notes.append("weak signature match; confirm the mapping before trusting the "
                         "diagnostics built on it")
        if len(candidates) > 1 and how == "column signature":
            second = candidates[1][1]
            if confidence - second <= 0.15:
                notes.append(f"ambiguous with '{candidates[1][0]}' "
                             f"({int(second * 100)}% match) - resolved by --map if wrong")
        mapped.append(MappedInput(
            role=entity, source=rel, entity=entity, identification=how,
            entity_confidence=confidence, rows=len(mapped_table.rows),
            columns=list(mapped_table.columns), renames=renames,
            unmapped_columns=unmapped, ambiguous_columns=ambiguous,
            missing_required=missing,
            context_only=entity in CONTEXT_ONLY_ENTITIES, notes=notes))

    ambiguities = resolve_roles(mapped)
    return preflight, mapped, ambiguities


def resolve_roles(mapped: list[MappedInput]) -> list[dict[str, object]]:
    """Decide which file owns each role; never merge two files into one role.

    A single file per role is used. When several claim the same role, an
    explicit ``--map`` (recorded as a manual override) wins, and the others are
    marked superseded so the report can say which file was not used. With no
    override, NONE of them is used and the ambiguity is reported.
    """
    by_role: dict[str, list[MappedInput]] = {}
    for item in mapped:
        if item.role.startswith("("):
            continue
        by_role.setdefault(item.role, []).append(item)
    out: list[dict[str, object]] = []
    for role, items in sorted(by_role.items()):
        if len(items) == 1:
            continue
        manual = [i for i in items if i.identification == "manual override"]
        if len(manual) == 1:
            winner = manual[0]
            for item in items:
                if item is not winner:
                    item.selected = False
                    item.superseded_by = winner.source
            continue
        for item in items:
            item.selected = False
        sources = sorted(i.source for i in items)
        out.append({
            "type": "duplicate_role", "role": role, "sources": sources,
            "reason": ("more than one file maps to this role and more than one (or no) "
                       "manual override was given; none of them is used."),
            "resolution": f"--map <file>={role} for exactly one of: {', '.join(sources)}"})
    return out


# --- Composed diagnostics ---------------------------------------------------

def _empty(entity: str) -> Table:
    return Table(source="(absent)", columns=list(CANONICAL_COLUMNS[entity]), rows=[])


def _load_tables(input_dir: str | Path, mapped: list[MappedInput],
                 ambiguity_roles: set[str]) -> dict[str, Table]:
    dir_path = Path(input_dir)
    out: dict[str, Table] = {}
    for item in mapped:
        if item.role.startswith("(") or item.role in ambiguity_roles or not item.selected:
            continue
        if item.entity is None or not item.usable:
            continue
        table, _renames, _unmapped, _amb = normalize_columns(
            load_table(dir_path / item.source), item.entity)
        out[item.role] = table
    return out


def churn_window(memberships: Table, as_of: date, window_days: int = 30) -> dict[str, object]:
    """Ended-membership churn for the trailing window, using the metric contracts.

    Base = memberships active at the window start (start on/before the start and
    no end date, or an end date on/after it). Canceled = those whose end date
    falls inside the window and whose status is a terminal one. Memberships
    marked active past their end date are excluded from churn and reported
    separately: that is a data-integrity problem, not churn.
    """
    period_start = as_of - timedelta(days=window_days)
    terminal = {"canceled", "cancelled", "expired", "ended", "terminated", "inactive"}
    base: list[dict[str, str]] = []
    stuck: list[str] = []
    for m in memberships.rows:
        start = parse_date(m.get("start_date", ""))
        end = parse_date(m.get("end_date", ""))
        status = m.get("status", "").strip().lower()
        if status == "active" and end is not None and end < as_of:
            stuck.append(m.get("membership_id", "?"))
            continue
        if start is None or start > period_start:
            continue
        if end is not None and end < period_start:
            continue
        base.append(m)

    canceled = [m for m in base
                if (e := parse_date(m.get("end_date", ""))) is not None
                and period_start <= e <= as_of
                and m.get("status", "").strip().lower() in terminal]

    def _rate(row: dict[str, str]) -> Decimal:
        if str(row.get("complimentary", "")).strip().lower() in {"1", "true", "yes", "y", "x"}:
            return ZERO
        return parse_money(row.get("contracted_rate", "")) or ZERO

    base_mrr = sum((_rate(m) for m in base), ZERO)
    lost_mrr = sum((_rate(m) for m in canceled), ZERO)
    period = f"{period_start.isoformat()}..{as_of.isoformat()}"
    logo = logo_churn(len(canceled), len(base), period)
    revenue = revenue_churn(lost_mrr, base_mrr, period)
    return {
        "window_days": window_days,
        "period": {"from": period_start.isoformat(), "to": as_of.isoformat()},
        "base_memberships": len(base),
        "canceled_memberships": len(canceled),
        "canceled_ids": [m.get("membership_id", "?") for m in canceled],
        "base_mrr": str(base_mrr),
        "lost_mrr": str(lost_mrr),
        "logo_churn": logo.as_dict(),
        "revenue_churn": revenue.as_dict(),
        "excluded_active_past_end_date": stuck,
        "definition": (
            "Base = memberships whose start_date <= window start and (no end_date or "
            "end_date >= window start). Canceled = base memberships whose end_date falls "
            "inside the window with a terminal status. Churn is gross: expansion is not "
            "netted against losses. Memberships marked active past their end date are "
            "excluded and reported as a data-integrity finding."),
        "caveat": "Members who both joined and left inside the window were not in the "
                  "base and are excluded; notice dates are not treated as end dates.",
    }


def run_modules(tables: dict[str, Table], as_of: date, *, stale_days: int = 21,
                discount_pct: int = 25, churn_window_days: int = 30,
                renewal_window_days: int = 90, horizons: tuple[int, ...] = (30, 60, 90, 180),
                open_hours: Decimal | None = None) -> dict[str, Any]:
    """Run every diagnostic whose inputs exist; record the rest as not measured."""
    modules: dict[str, Any] = {}
    not_measured: list[dict[str, Any]] = []

    def need(*roles: str) -> bool:
        return all(r in tables for r in roles)

    def skip(name: str, needs: tuple[str, ...]) -> None:
        missing = [r for r in needs if r not in tables]
        not_measured.append({
            "module": name,
            "missing_inputs": missing,
            "reason": f"needs {', '.join(needs)}; not supplied in this engagement "
                      f"(missing: {', '.join(missing)})"})

    # Occupancy / revenue dashboard.
    if need("inventory", "memberships"):
        modules["occupancy"] = occupancy_report(tables["inventory"], tables["memberships"],
                                                as_of, discount_pct)
    else:
        skip("occupancy", ("inventory", "memberships"))

    # Forward contracted view.
    if need("inventory", "memberships"):
        modules["forecast"] = occupancy_forecast(tables["inventory"], tables["memberships"],
                                                 as_of, horizons)
    else:
        skip("forecast", ("inventory", "memberships"))

    # Pricing / discount audit.
    if need("inventory", "memberships"):
        modules["pricing"] = pricing_audit(tables["inventory"], tables["memberships"],
                                           as_of, discount_pct)
    else:
        skip("pricing", ("inventory", "memberships"))

    # Multi-location benchmark.
    if need("locations", "inventory", "memberships"):
        modules["locations"] = location_benchmark(
            as_of, tables["locations"], tables["inventory"], tables["memberships"],
            leads=tables.get("leads"), tours=tables.get("tours"),
            invoices=tables.get("invoices"))
    else:
        skip("locations", ("locations", "inventory", "memberships"))

    # Revenue leakage across whatever exists.
    if tables:
        modules["leakage"] = leakage_report(
            as_of, leads=tables.get("leads"), deals=tables.get("deals"),
            tours=tables.get("tours"), memberships=tables.get("memberships"),
            invoices=tables.get("invoices"), inventory=tables.get("inventory"),
            payments=tables.get("payments"))
    else:
        skip("leakage", ("any export",))

    # Pipeline health.
    if need("deals"):
        modules["pipeline"] = pipeline_report(tables["deals"], as_of, stale_days)
    else:
        skip("pipeline", ("deals",))

    # Speed to lead.
    if need("leads"):
        modules["speed_to_lead"] = speed_to_lead_report(tables["leads"])
    else:
        skip("speed_to_lead", ("leads",))

    # Lead sources.
    if need("leads"):
        modules["lead_sources"] = source_report(tables["leads"])
    else:
        skip("lead_sources", ("leads",))

    # Lead-to-tour / funnel.
    if need("leads", "tours"):
        funnel: Any = funnel_report(tables["leads"], tables["tours"],
                                    tables.get("deals", _empty("deals")))
        if "deals" not in tables:
            counts = dict(funnel["counts"])
            rates = dict(funnel["rates"])
            counts.pop("deals_won", None)
            rates.pop("lead_to_won", None)
            funnel["counts"] = counts
            funnel["rates"] = rates
            funnel["caveats"] = list(funnel.get("caveats", [])) + [
                "No deals export was supplied, so won-deal counts and lead-to-won are "
                "NOT MEASURABLE in this engagement."]
        modules["funnel"] = funnel
    else:
        skip("funnel", ("leads", "tours"))

    # Collections.
    if need("invoices"):
        modules["collections"] = collections_queue(
            tables["invoices"], as_of, payments=tables.get("payments"),
            memberships=tables.get("memberships"))
    else:
        skip("collections", ("invoices",))

    # Churn + renewal window.
    if need("memberships"):
        modules["churn"] = churn_window(tables["memberships"], as_of, churn_window_days)
        modules["renewals"] = renewal_scan(
            tables["memberships"], as_of, invoices=tables.get("invoices"),
            window_days=renewal_window_days)
    else:
        skip("churn", ("memberships",))
        skip("renewals", ("memberships",))

    # Cross-system reconciliation (CRM vs WMS).
    if need("companies", "deals", "memberships"):
        modules["reconcile"] = reconcile_report(
            as_of, companies=tables["companies"], deals=tables["deals"],
            memberships=tables["memberships"], contacts=tables.get("contacts"),
            inventory=tables.get("inventory"), invoices=tables.get("invoices"))
    else:
        skip("reconcile", ("companies", "deals", "memberships"))

    # Virtual office partner reconciliation.
    if need("virtual_office_partners", "memberships", "invoices"):
        modules["virtual_office"] = vo_reconciliation(
            tables["virtual_office_partners"], tables["memberships"], tables["invoices"], as_of)
    else:
        skip("virtual_office", ("virtual_office_partners", "memberships", "invoices"))

    # Meeting / event room yield.
    if need("room_bookings", "inventory"):
        modules["rooms"] = room_yield(tables["room_bookings"], tables["inventory"], open_hours)
    else:
        skip("rooms", ("room_bookings", "inventory"))

    return {"modules": modules, "not_measured": not_measured}


# --- Data quality -----------------------------------------------------------

def quality_section(mapped: list[MappedInput], tables: dict[str, Table]) -> dict[str, Any]:
    """Per-file structural quality checks (blanks, dates, duplicate keys)."""
    files: list[dict[str, Any]] = []
    used_sources = {t.source for t in tables.values()}
    for item in mapped:
        if item.role.startswith("(") or item.entity is None:
            continue
        table = tables.get(item.role)
        # A file whose role is owned by another file (or which was refused as
        # ambiguous) is listed but never re-checked against someone else's table.
        if table is None or item.source not in used_sources:
            files.append({
                "source": item.source, "role": item.role, "rows": item.rows,
                "checked": False,
                "note": (f"not analysed: {item.superseded_by} owns this role"
                         if item.superseded_by else
                         "not used by the diagnostics (ambiguous, unusable, or context "
                         "only)")})
            continue
        findings = []
        for col in REQUIRED_COLUMNS[item.entity]:
            if col in table.columns:
                findings += [f.as_dict() for f in check_blank_values(table.rows, col)]
        for col in DATE_COLUMNS.get(item.entity, []):
            if col in table.columns:
                findings += [f.as_dict() for f in check_date_parseability(table.rows, col)]
        keys = [k for k in PRIMARY_KEYS.get(item.entity, []) if k in table.columns]
        if keys:
            findings += [f.as_dict() for f in check_duplicates(table.rows, keys, item.entity)]
        files.append({
            "source": item.source, "role": item.role, "rows": table.__len__(),
            "entity": item.entity, "checked": True,
            "renamed_columns": len(item.renames),
            "unmapped_columns": item.unmapped_columns,
            "ambiguous_columns": item.ambiguous_columns,
            "missing_required": item.missing_required,
            "findings": findings,
            "errors": sum(1 for f in findings if f["severity"] == "error"),
            "warnings": sum(1 for f in findings if f["severity"] == "warning"),
        })
    totals = {
        "files_checked": sum(1 for f in files if f.get("checked")),
        "errors": sum(int(f.get("errors", 0)) for f in files),
        "warnings": sum(int(f.get("warnings", 0)) for f in files),
    }
    return {"files": files, "totals": totals}


# --- Findings ---------------------------------------------------------------

def _humanize_flag(name: Any) -> str:
    """Turn an engine flag key such as out_of_service_units into words."""
    text = str(name).replace("_", " ").strip()
    return text[:1].upper() + text[1:] if text else text


def _finding(fid: str, module: str, kind: str, title: str, statement: str,
             data_used: list[str], calculation: str, confidence: str,
             confidence_basis: str, limitation: str,
             records: list[str] | None = None) -> dict[str, object]:
    assert kind in KIND_ORDER, kind
    return {
        "id": fid, "module": module, "kind": kind, "title": title,
        "statement": statement, "data_used": data_used, "calculation": calculation,
        "confidence": confidence, "confidence_basis": confidence_basis,
        "limitation": limitation, "records": (records or [])[:25],
    }


def _pct(value: object) -> str:
    try:
        return f"{float(str(value)) * 100:.1f}%"
    except (TypeError, ValueError):
        return "n/a"


def _confidence_for(errors: int, warnings: int, *, denominator: int | None = None,
                    exact_mapping: bool = True) -> tuple[str, str]:
    """Documented confidence rule shared by every finding in the report."""
    basis: list[str] = []
    if errors:
        basis.append(f"{errors} error-severity data-quality finding(s) on the inputs")
    if warnings:
        basis.append(f"{warnings} warning-severity data-quality finding(s)")
    if denominator is not None and denominator < 10:
        basis.append(f"small denominator ({denominator} records)")
    if not exact_mapping:
        basis.append("column mapping is not an exact canonical match")
    if errors or (denominator is not None and denominator < 5):
        return "low", "; ".join(basis) or "incomplete inputs"
    if warnings or (denominator is not None and denominator < 10) or not exact_mapping:
        return "medium", "; ".join(basis)
    return "high", "inputs complete, mapping exact, no data-quality findings on the records used"


def _qcounts(quality: dict[str, Any], roles: set[str]) -> tuple[int, int]:
    errors = warnings = 0
    for f in quality["files"]:
        if f.get("role") in roles:
            errors += int(f.get("errors", 0))
            warnings += int(f.get("warnings", 0))
    return errors, warnings


def build_findings(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Assemble the fact / calculation / inference / recommendation records."""
    modules: dict[str, Any] = bundle["modules"]
    quality: dict[str, Any] = bundle["quality"]
    mapped: list[dict[str, Any]] = bundle["inputs"]["files"]
    findings: list[dict[str, Any]] = []

    def data_used(*roles: str) -> list[str]:
        return [f"{f['source']} ({f['rows']} rows)" for f in mapped if f.get("role") in roles]

    # --- Data quality (facts) ---
    totals = quality["totals"]
    findings.append(_finding(
        "dq-001", "data quality", "fact",
        "Every input file was identified and structurally checked",
        f"{totals['files_checked']} export(s) were read, identified from column signatures, "
        f"and checked for blank required values, unparseable dates, and duplicate keys "
        f"({totals['errors']} error-severity and {totals['warnings']} warning-severity "
        "finding(s)).",
        [str(f["source"]) + f" ({f['rows']} rows)" for f in mapped],
        "Counts of the checks in the Data quality section; no estimation.",
        _confidence_for(int(totals["errors"]), int(totals["warnings"]))[0],
        _confidence_for(int(totals["errors"]), int(totals["warnings"]))[1],
        "Quality checks only cover structural problems the schema can express; business "
        "rules (correct stage names, real move-in dates) still need human verification."))
    for f in mapped:
        match_conf = float(str(f.get("entity_confidence", 0.0)))
        if (f.get("identification") == "column signature" and match_conf < 1.0
                and f.get("entity")):
            findings.append(_finding(
                f"dq-map-{str(f['source'])}", "data quality", "fact",
                f"{f['role']}: identified with a {int(match_conf * 100)}% column-signature "
                "match",
                f"{f['source']} was identified as '{f['role']}' from its column names "
                f"({int(match_conf * 100)}% of the canonical signature columns present). "
                f"{len(f.get('renames', {}))} column(s) were renamed and "
                f"{len(f.get('unmapped_columns', []))} header(s) were left unmapped.",
                [f"{f['source']} ({f['rows']} rows)"],
                "Fraction of canonical signature columns present, per inspect_table.",
                "medium",
                "identification is a column-signature heuristic and never uses filenames",
                "A wrong entity match would misroute every metric downstream; confirm the "
                "mapping."))
        for amb in f.get("ambiguous_columns", []) or []:
            findings.append(_finding(
                f"dq-amb-{str(f['source'])}-{amb['canonical_column']}", "data quality",
                "fact", f"{f['role']}: ambiguous column mapping for "
                        f"'{amb['canonical_column']}'",
                f"Source column(s) {', '.join(amb['source_columns'])} all map to canonical "
                f"'{amb['canonical_column']}', so none was used.",
                [f"{f['source']} columns: {', '.join(amb['source_columns'])}"],
                "No calculation: the mapping was refused rather than guessed.",
                "high", "the conflict is exact and needs no judgement",
                f"Metrics depending on '{amb['canonical_column']}' are NOT MEASURABLE until "
                "the operator states which column is authoritative."))

    # --- Occupancy (calculations) ---
    occ = modules.get("occupancy")
    if isinstance(occ, dict):
        metrics = {str(m["name"]): m for m in occ.get("metrics", [])}
        office = metrics.get("office_occupancy", {})
        work = metrics.get("workstation_occupancy", {})
        fin = metrics.get("financial_occupancy", {})
        errs, warns = _qcounts(quality, {"inventory", "memberships"})
        den = int(str(office.get("denominator", 0)) or 0)
        conf, why = _confidence_for(errs, warns, denominator=den)
        findings.append(_finding(
            "occ-001", "occupancy", "calculation",
            f"Occupancy is three different numbers: {_pct(office.get('value'))} by office "
            f"count, {_pct(work.get('value'))} by workstation, {_pct(fin.get('value'))} "
            "financially",
            f"Office count {office.get('numerator')}/{office.get('denominator')}; "
            f"workstations {work.get('numerator')}/{work.get('denominator')}; "
            f"contracted revenue {fin.get('numerator')}/{fin.get('denominator')} of list "
            "potential.",
            data_used("inventory", "memberships"),
            "office = occupied sellable in-service offices / sellable in-service offices; "
            "workstation = capacity of occupied units / capacity of sellable in-service "
            "units; financial = contracted MRR of occupied priced units / list total of all "
            "priced sellable in-service units.",
            conf, why,
            "Occupancy measures contracted inventory consumption, not attendance: no "
            "access-log data is involved, and units without a list price are excluded from "
            "the financial ratio on both sides."))
        spread = None
        try:
            spread = abs(float(str(office.get("value"))) - float(str(fin.get("value"))))
        except (TypeError, ValueError):
            spread = None
        if spread is not None and spread >= 0.05:
            findings.append(_finding(
                "occ-002", "occupancy", "calculation",
                f"Physical occupancy overstates paid occupancy by "
                f"{round(spread * 100, 1)} percentage points",
                f"Office-count occupancy ({_pct(office.get('value'))}) minus financial "
                f"occupancy ({_pct(fin.get('value'))}) = "
                f"{round(spread * 100, 1)} percentage points. The named drivers are listed "
                "in the occupancy flags (out-of-service units, complimentary units, "
                "discounted units, unpriced units).",
                data_used("inventory", "memberships"),
                "difference between the two occupancy metrics at this as-of date",
                conf, why,
                "A spread is arithmetic, not a cause: the flags name which units contribute, "
                "and attributing the gap to a strategy needs operator context."))
        flags = occ.get("flags", [])
        if flags:
            def _flag_units(flag: dict[str, Any]) -> str:
                parts = []
                for unit in flag["units"][:5]:
                    if isinstance(unit, dict):
                        parts.append(f"{unit.get('unit_id')} "
                                     f"({unit.get('discount_pct')}% below list)")
                    else:
                        parts.append(str(unit))
                return ", ".join(parts)

            findings.append(_finding(
                "occ-003", "occupancy", "fact",
                f"{len(flags)} occupancy distortion flag(s) name specific units",
                "; ".join(f"{_humanize_flag(f['flag'])} ({len(f['units'])}): "
                          f"{_flag_units(f)}" for f in flags),
                data_used("inventory", "memberships"),
                "engine flags from occupancy_report (no estimation)",
                "high", "flags quote unit IDs straight from the inventory export",
                "Flags identify where the number is distorted; whether the distortion is "
                "intentional (comped desk, promotional rate) is an operator decision."))

    # --- Forward contracted view (calculation) ---
    forecast = modules.get("forecast")
    if isinstance(forecast, dict):
        horizons = {int(h["horizon_days"]): h for h in forecast.get("horizons", [])}
        h90 = horizons.get(90) or (list(horizons.values())[-1] if horizons else None)
        if h90:
            errs, warns = _qcounts(quality, {"memberships", "inventory"})
            dep = [str(x) for x in h90.get("departures", [])]
            arr = [str(x) for x in h90.get("arrivals", [])]
            findings.append(_finding(
                "rev-001", "occupancy", "calculation",
                f"Contracted occupancy is {_pct(h90.get('contracted_occupancy'))} at "
                f"{h90['horizon_days']} days ({h90['date']})",
                f"Contracted occupied capacity {h90.get('contracted_occupied_capacity')} of "
                f"{h90.get('sellable_capacity')} sellable workstations; "
                f"{len(dep)} recorded departure(s) ({', '.join(dep) or 'none'}) and "
                f"{len(arr)} arrival(s) ({', '.join(arr) or 'none'}) inside the horizon.",
                data_used("inventory", "memberships"),
                "active agreements minus recorded end dates plus signed pending move-ins / "
                "sellable capacity, per occupancy_forecast",
                _confidence_for(errs, warns)[0], _confidence_for(errs, warns)[1],
                "Contracted layer only: agreements with no end date are assumed to continue "
                "and no renewal probability is applied. Sales pipeline is not included."))

    # --- Revenue leakage (facts + calculations) ---
    leak = modules.get("leakage")
    if isinstance(leak, dict):
        by_check = {str(f["check"]): f for f in leak.get("findings", [])}
        unbilled = by_check.get("active_memberships_without_recent_invoice")
        if unbilled:
            errs, warns = _qcounts(quality, {"memberships", "invoices"})
            findings.append(_finding(
                "rev-002", "revenue leakage", "calculation",
                f"{unbilled['count']} active membership(s) with no invoice in 45 days: "
                f"{unbilled['monthly_amount_at_risk']}/month at risk",
                " ".join(str(i.get("note", "")) for i in unbilled["items"]).strip()
                or "No billing-frequency caveat applied to these records.",
                data_used("memberships", "invoices"),
                "sum of contracted_rate for active, non-complimentary memberships whose "
                "membership_id has no invoice issued in the 45 days to the as-of date",
                _confidence_for(errs, warns,
                                denominator=int(unbilled["count"]))[0],
                _confidence_for(errs, warns, denominator=int(unbilled["count"]))[1],
                "A missing invoice is not proof of missing revenue: prepaid, annual, or "
                "partner-billed arrangements can legitimately sit outside the 45-day window. "
                "Verify each record before billing."))
        failed = by_check.get("failed_or_overdue_invoices")
        if failed:
            errs, warns = _qcounts(quality, {"invoices"})
            findings.append(_finding(
                "rev-003", "collections", "calculation",
                f"{failed['count']} invoice(s) failed or overdue, "
                f"{failed['amount_outstanding']} outstanding",
                "Aging and the suggested internal approach per invoice are in the "
                "Collections section.",
                data_used("invoices"),
                "sum of the amount column for invoices with status failed or overdue",
                _confidence_for(errs, warns, denominator=int(failed["count"]))[0],
                _confidence_for(errs, warns, denominator=int(failed["count"]))[1],
                "Export status is a snapshot: payments may have landed since the export was "
                "produced, and deposits or credits already applied are not netted off."))
        blocked = by_check.get("out_of_service_inventory")
        if blocked:
            findings.append(_finding(
                "rev-004", "revenue leakage", "fact",
                f"{blocked['count']} unit(s) out of service, "
                f"{blocked['monthly_list_value_blocked']}/month of list value idle",
                "Units: " + ", ".join(str(i["unit_id"]) for i in blocked["items"]),
                data_used("inventory"),
                "sum of list_price for units flagged out_of_service",
                "high", "quote of the inventory export's own out_of_service flag",
                "List value is potential, not lost revenue: the unit may be genuinely "
                "unusable. The finding is a question about the repair date, not a number to "
                "book."))
        stuck = by_check.get("active_status_past_end_date")
        if stuck:
            findings.append(_finding(
                "dq-002", "data quality", "fact",
                f"{stuck['count']} membership(s) marked active past their end date",
                "Records: " + ", ".join(str(i) for i in stuck["ids"]),
                data_used("memberships"),
                "status == 'active' and end_date < as-of date",
                "high", "exact date comparison against the membership export",
                "Either a renewal was never recorded or billing is continuing on an expired "
                "agreement; both corrupt every occupancy and retention number until fixed."))
        ghost = by_check.get("completed_tours_without_next_action")
        if ghost:
            findings.append(_finding(
                "conv-001", "tour conversion", "fact",
                f"{ghost['count']} completed tour(s) with no recorded next step",
                "Tours: " + ", ".join(str(t) for t in ghost["ids"]),
                data_used("tours"),
                "status == 'completed' and next_action is blank",
                "high", "direct read of two columns",
                "An empty next-action field means the outcome was not recorded; the "
                "follow-up may still have happened outside the CRM."))
        won_missing = by_check.get("won_deals_without_membership")
        if won_missing:
            findings.append(_finding(
                "rev-005", "revenue leakage", "fact",
                f"{won_missing['count']} won deal(s) with no active or pending membership",
                "Companies: " + ", ".join(str(i) for i in won_missing["ids"]),
                data_used("deals", "memberships"),
                "companies with a won deal minus companies with an active/pending membership",
                "medium", "depends on company_id being consistent across both systems",
                "Recorded outside the WMS, still onboarding, or a duplicate company ID; the "
                "CRM-WMS reconciliation section is the place to resolve it."))
        for finding in leak.get("findings", []):
            if finding["check"] not in {"unfollowed_leads", "stale_open_deals_30d"}:
                continue
            findings.append(_finding(
                f"pipe-{finding['check']}", "sales pipeline", "fact",
                f"{finding['count']} record(s) in check '{finding['check']}'",
                str(finding.get("detail", "")),
                data_used("leads", "deals"),
                "count of records matching the check's stated rule",
                "high", "the check is a direct column comparison",
                "Records outside these exports (spreadsheets, inboxes, verbal promises) are "
                "invisible to every count in this report."))

    # --- Pipeline (calculations) ---
    pipe = modules.get("pipeline")
    if isinstance(pipe, dict):
        f = pipe.get("findings", {})
        errs, warns = _qcounts(quality, {"deals"})
        den = int(pipe.get("deal_count", 0))
        conf, why = _confidence_for(errs, warns, denominator=den)
        counts = {name: len(items) for name, items in f.items() if items}
        findings.append(_finding(
            "pipe-001", "sales pipeline", "calculation",
            f"Pipeline hygiene: {sum(counts.values())} issue(s) across {den} deal(s)",
            "; ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "no hygiene issues",
            data_used("deals"),
            f"counts of open deals matching each rule at a staleness threshold of "
            f"{pipe.get('stale_threshold_days')} days; open deals by owner: "
            f"{pipe.get('open_deals_by_owner')}",
            conf, why,
            "Hygiene only: this measures how well the pipeline is maintained, not whether "
            "the deals are winnable. Stage names must be the operator's own."))
        findings.append(_finding(
            "pipe-002", "sales pipeline", "inference",
            "Stale and unowned open deals are the pattern most likely to hide lost revenue",
            "Stale deals and unassigned deals appear together in this dataset's counts "
            "above; deals nobody touched and nobody owns cannot be forecast or chased.",
            data_used("deals"),
            "No calculation: this is a reading of the two counted rules together.",
            "medium", "inference from counts, not from deal outcomes",
            "Deal outcomes are unknown - the export has no win/loss over time, so this is a "
            "priority signal, not a measured loss."))

    # --- Speed to lead (calculation) ---
    stl = modules.get("speed_to_lead")
    if isinstance(stl, dict):
        no_resp = len(stl.get("leads_without_response", []) or [])
        median = stl.get("median_minutes")
        findings.append(_finding(
            "speed-001", "speed to lead", "calculation",
            f"Median first response {median} {stl.get('basis')}, tail to "
            f"{stl.get('max_minutes')} minutes",
            f"{stl.get('responded_leads')} lead(s) received a recorded first response; "
            f"{no_resp} lead(s) have none at all"
            + (f" (p90 {stl.get('p90_minutes')} minutes)" if stl.get("p90_minutes") else ""),
            data_used("leads"),
            f"median/p90/max of {stl.get('basis')} between created_at and first_response_at; "
            "leads without a first response are excluded from the distribution and counted "
            "separately",
            "medium" if median is None else _confidence_for(0, 0)[0],
            "distribution is computed from the timestamps the source system stores",
            "first_response_at may record an automated acknowledgement rather than a human "
            "contact attempt; an unrecorded call is indistinguishable from no response."))

    # --- Funnel / tour conversion (calculations) ---
    funnel = modules.get("funnel")
    if isinstance(funnel, dict):
        counts = funnel.get("counts", {})
        rates = funnel.get("rates", {})
        if not any((counts.get("tours_completed"), counts.get("tour_no_shows"))):
            pass
        findings.append(_finding(
            "conv-002", "tour conversion", "calculation",
            f"Funnel: {counts.get('leads')} leads -> {counts.get('leads_with_tour')} with a "
            f"tour ({_pct(rates.get('lead_to_tour'))}) -> {counts.get('tours_completed')} "
            "tours completed",
            f"Contacted {counts.get('contacted')} ({_pct(rates.get('lead_to_contact'))}); "
            f"tours completed {counts.get('tours_completed')}; no-shows "
            f"{counts.get('tour_no_shows')} (show rate {_pct(rates.get('tour_show_rate'))}); "
            f"won deals {counts.get('deals_won', 'not measured')}",
            data_used("leads", "tours", "deals"),
            "; ".join(f"{k} = {v}" for k, v in funnel.get("definitions", {}).items()),
            _confidence_for(0, 0, denominator=int(counts.get("leads") or 0))[0],
            "rates follow the definitions printed in the methodology section",
            "Counts are period-mixed unless the exports cover one period: a tour booked last "
            "quarter can appear against this quarter's leads. "
            + " ".join(str(c) for c in funnel.get("caveats", []))))

    # --- Churn / renewals (calculations) ---
    churn = modules.get("churn")
    if isinstance(churn, dict):
        logo = churn.get("logo_churn", {})
        rev = churn.get("revenue_churn", {})
        errs, warns = _qcounts(quality, {"memberships"})
        conf, why = _confidence_for(errs, warns, denominator=int(churn.get("base_memberships", 0)))
        findings.append(_finding(
            "churn-001", "churn", "calculation",
            f"Trailing {churn['window_days']}-day churn: "
            f"{churn.get('canceled_memberships')} of {churn.get('base_memberships')} "
            f"memberships ({_pct(logo.get('value'))}), "
            f"{churn.get('lost_mrr')} MRR lost ({_pct(rev.get('value'))})",
            f"Window {churn['period']['from']} to {churn['period']['to']}; base MRR "
            f"{churn.get('base_mrr')}.",
            data_used("memberships"),
            str(churn.get("definition")),
            conf, why, str(churn.get("caveat"))))
    renewals = modules.get("renewals")
    if isinstance(renewals, dict):
        in_window = renewals.get("agreements_in_window", []) or []
        mrr_at_cliff = ZERO
        for a in in_window:
            if a.get("contracted_rate"):
                mrr_at_cliff += Decimal(str(a["contracted_rate"]))
        findings.append(_finding(
            "churn-002", "churn", "calculation",
            f"{len(in_window)} agreement(s) reach a renewal or end cliff in the next "
            f"{renewals.get('window_days')} days ({mrr_at_cliff} monthly)",
            "Cliffs: " + ", ".join(f"{a['membership_id']} on {a['cliff_date']} "
                                   f"({a['days_to_cliff']}d)" for a in in_window[:10]),
            data_used("memberships", "invoices"),
            "min(end_date, renewal_date) inside the window for active memberships; sum of "
            "the listed contracted rates",
            "high" if len(in_window) >= 5 else "medium",
            "dates and rates are read directly from the membership export",
            "Deliberately no risk score: the evidence lists (notice given, renewal-to-list "
            "jump, payment friction, multi-membership accounts) are attached to each "
            "agreement in the bundle for a human to weigh."))

    # --- Cross-system + virtual office (facts) ---
    recon = modules.get("reconcile")
    if isinstance(recon, dict) and recon.get("findings"):
        checks: dict[str, list[dict[str, object]]] = {}
        for f in recon["findings"]:
            checks.setdefault(str(f["check"]), []).append(f)
        findings.append(_finding(
            "rev-006", "revenue leakage", "fact",
            f"CRM and WMS disagree in {len(recon['findings'])} place(s)",
            "; ".join(f"{k}: {len(v)}" for k, v in sorted(checks.items())),
            data_used("companies", "deals", "memberships"),
            "company_id equality is the only automatic match; name matches are probable "
            "(0.8) and queued for human review",
            "medium", "cross-system matching depends on shared company identifiers",
            "Nothing is merged or corrected by this tool; conflicting records need a human "
            "decision about which system is authoritative."))
    vo = modules.get("virtual_office")
    if isinstance(vo, dict) and vo.get("findings"):
        vo_checks: dict[str, int] = {}
        for f in vo["findings"]:
            vo_checks[str(f["check"])] = vo_checks.get(str(f["check"]), 0) + 1
        findings.append(_finding(
            "rev-007", "revenue leakage", "fact",
            f"Virtual-office reconciliation raised {len(vo['findings'])} finding(s)",
            "; ".join(f"{k}: {v}" for k, v in sorted(vo_checks.items())),
            data_used("virtual_office_partners", "memberships", "invoices"),
            "partner-billed clients with operator invoices, partner clients without a "
            "membership, direct clients never invoiced",
            "medium", "matches on company_id only; fuzzy name matching is deliberately not "
                      "attempted",
            "Double billing and unbilled fulfillment both need partner statements to "
            "confirm; the export alone cannot settle them."))

    # --- Rooms (calculation) ---
    rooms = modules.get("rooms")
    if isinstance(rooms, dict) and rooms.get("rooms"):
        booked = sum(Decimal(str(r["booked_hours"])) for r in rooms["rooms"])
        revenue = sum(Decimal(str(r["gross_revenue"])) for r in rooms["rooms"])
        findings.append(_finding(
            "rooms-001", "rooms", "calculation",
            f"Meeting and event rooms booked {booked} hours for {revenue} gross",
            "Per-room yield and (when bookable hours are declared) utilization are in the "
            "bundle.",
            data_used("room_bookings", "inventory"),
            "sum of booking durations and amounts; zero-charge bookings include both "
            "plan-included and comped bookings, which the export cannot separate",
            "medium", "booking exports frequently omit internal or plan-included usage",
            "Utilization is only reported when the operator declares bookable hours per day."))

    return findings


# --- Opportunities and action plan -----------------------------------------

SEVERITY_RANK = {"data integrity": 0, "revenue leakage": 1, "churn": 2, "sales pipeline": 3,
                 "tour conversion": 4, "speed to lead": 5, "occupancy": 6, "rooms": 7}


BASIS_RANK = {"recurring": 0, "one_time": 1, "lost": 2, "erosion": 3, "unquantified": 4}


def build_opportunities(bundle: dict[str, Any]) -> dict[str, Any]:
    """Rank opportunities by a documented, deterministic rule.

    Order: measured recurring revenue at risk (largest first), then measured
    one-time balances, then revenue that already left, then erosion of list
    value, then unquantified items by severity class and id. Nothing is
    extrapolated to fill a number, and no two amounts are ever added together.
    """
    modules: dict[str, Any] = bundle["modules"]
    leak: dict[str, Any] = modules.get("leakage") or {}
    by_check = {str(f["check"]): f for f in leak.get("findings", [])}
    candidates: list[dict[str, Any]] = []

    def add(cid: str, title: str, module: str, basis: str, recurring: Decimal | None,
            one_time: Decimal | None, evidence: str, first_step: str, owner: str,
            window: str, confidence: str, limitation: str, records: list[str] | None = None,
            calculation: str = "") -> None:
        candidates.append({
            "id": cid, "title": title, "module": module, "basis": basis,
            "monthly_recurring": None if recurring is None else str(recurring),
            "one_time": None if one_time is None else str(one_time),
            "erosion_basis": basis == "erosion",
            "evidence": evidence, "first_step": first_step, "owner": owner,
            "window": window, "confidence": confidence, "limitation": limitation,
            "records": (records or [])[:10], "calculation": calculation,
        })

    unbilled = by_check.get("active_memberships_without_recent_invoice")
    if unbilled:
        add("opp-unbilled", "Bill or correct the active memberships with no invoice in 45 days",
            "revenue leakage", "recurring", Decimal(str(unbilled["monthly_amount_at_risk"])),
            None,
            "; ".join(str(i["membership_id"]) for i in unbilled["items"][:8]),
            "Run the billing-gap list past finance and re-issue or correct each record.",
            "finance", "now", "high",
            "Includes partner-billed or prepaid arrangements that may be correct as they are; "
            "verify each record before billing.",
            calculation="sum of contracted_rate for active, non-complimentary memberships with "
                        "no invoice issued in 45 days")

    failed = by_check.get("failed_or_overdue_invoices")
    if failed:
        add("opp-collections",
            "Work the failed and overdue invoice queue in aging order",
            "revenue leakage", "one_time", None, Decimal(str(failed["amount_outstanding"])),
            "; ".join(str(i["invoice_id"]) for i in failed["items"][:8]),
            "Start with the oldest band, verify the payment method, then make personal contact.",
            "finance", "now", "medium",
            "Export status is a snapshot; some invoices may already be settled or partially "
            "credited.",
            calculation="sum of invoice amounts with status failed or overdue")

    blocked = by_check.get("out_of_service_inventory")
    if blocked:
        add("opp-oos", "Set a repair-or-relist date for the out-of-service units",
            "revenue leakage", "erosion", Decimal(str(blocked["monthly_list_value_blocked"])),
            None,
            "Units: " + ", ".join(str(i["unit_id"]) for i in blocked["items"]),
            "Confirm the repair date with facilities; if none exists, re-list or repurpose.",
            "owner", "30", "medium",
            "List value, not lost revenue: the unit may be genuinely unusable.",
            calculation="sum of list_price for units flagged out_of_service")

    forecast = modules.get("forecast")
    departing_mrr = ZERO
    departing: list[str] = []
    if isinstance(forecast, dict):
        horizons = {int(h["horizon_days"]): h for h in forecast.get("horizons", [])}
        h90 = horizons.get(90) or (list(horizons.values())[-1] if horizons else None)
        if h90:
            ids = {str(m) for m in h90.get("departures", [])}
            memberships: Any = (bundle.get("tables") or {}).get("memberships")
            for mid in sorted(ids):
                departing.append(mid)
            if memberships is not None:
                for row in memberships.rows:
                    if row.get("membership_id", "") in ids:
                        rate = parse_money(row.get("contracted_rate", "")) or ZERO
                        departing_mrr += rate
    if departing:
        add("opp-departures",
            "Backfill or renew the contracts ending inside 90 days",
            "churn", "recurring", departing_mrr if departing_mrr > 0 else None, None,
            "Departing agreements: " + ", ".join(departing),
            "List the releasing inventory now and open a renewal conversation per agreement.",
            "sales", "30", "high",
            "End dates are recorded intentions; a renewal can still change the picture, and "
            "MRR is only shown when the contracted rates are present.",
            calculation="sum of contracted_rate for memberships with a recorded departure "
                        "inside the 90-day horizon")

    churn = modules.get("churn")
    if isinstance(churn, dict) and churn.get("lost_mrr") and Decimal(str(churn["lost_mrr"])) > 0:
        add("opp-churn", "Review what left in the trailing churn window",
            "churn", "lost", Decimal(str(churn["lost_mrr"])), None,
            "Canceled: " + ", ".join(str(i) for i in churn.get("canceled_ids", [])),
            "Interview the departing accounts for the real reason and check the pattern "
            "against onboarding and support history.",
            "community", "30", "medium",
            "Churn is gross and rate-based; expansion is not netted off and departures may "
            "have been deliberate plan changes.",
            calculation="sum of contracted_rate for base memberships ending inside the window")

    if by_check.get("active_status_past_end_date"):
        add("opp-data-integrity",
            "Fix the memberships marked active past their end date",
            "data quality", "unquantified", None, None,
            "Records: " + ", ".join(str(i) for i in
                                    by_check["active_status_past_end_date"]["ids"]),
            "Confirm with each member whether the agreement was renewed or has ended, then "
            "correct the status so occupancy and retention stop being wrong.",
            "owner", "now", "high",
            "Whether money is missing depends on the billing history this export does not "
            "contain.",
            calculation="status == active and end_date < as-of date")

    pipe = modules.get("pipeline")
    if isinstance(pipe, dict):
        f = pipe.get("findings", {})
        if f.get("stale_deals"):
            add("opp-stale-deals", "Give every stale open deal a next action or a verdict",
                "sales pipeline", "unquantified", None, None,
                f"{len(f['stale_deals'])} deal(s) untouched for "
                f"{pipe.get('stale_threshold_days')}+ days",
                "Work the stale list first: an explicit next action or a close decision.",
                "sales", "30", "medium",
                "Deal value in the export is an expectation, not a contract, so no monthly "
                "figure is attached here.",
                records=[str(d.get("deal_id")) for d in f["stale_deals"][:10]])
        if f.get("missing_next_action"):
            add("opp-missing-actions",
                "Close the record-keeping gap on open deals with no next action",
                "sales pipeline", "unquantified", None, None,
                f"{len(f['missing_next_action'])} open deal(s) have no recorded next action",
                "Adopt one rule for what 'next action' means and backfill the open records.",
                "sales", "30", "high",
                "A blank field may reflect a real conversation recorded elsewhere.",
                records=[str(d.get("deal_id")) for d in f["missing_next_action"][:10]])

    unfollowed = by_check.get("unfollowed_leads")
    if unfollowed:
        add("opp-uncontacted-leads",
            "Reply to the leads that never received a first response",
            "speed to lead", "unquantified", None, None,
            f"{unfollowed['count']} lead(s) still 'new' with no first response: "
            + ", ".join(str(i) for i in unfollowed["ids"][:8]),
            "Reply today and assign after-hours coverage so the next ones do not repeat.",
            "sales", "now", "high",
            "An unrecorded call is indistinguishable from no contact in this export.",
            records=[str(i) for i in unfollowed["ids"][:10]])

    ghost = by_check.get("completed_tours_without_next_action")
    if ghost:
        add("opp-ghosted-tours",
            "Set the next step on the completed tours with no follow-up recorded",
            "tour conversion", "unquantified", None, None,
            "Tours: " + ", ".join(str(t) for t in ghost["ids"][:8]),
            "Recover them with a value-specific follow-up rather than a generic check-in.",
            "sales", "now", "high",
            "The outcome may exist in a rep's inbox; this only measures what the CRM holds.",
            records=[str(t) for t in ghost["ids"][:10]])

    won_missing = by_check.get("won_deals_without_membership")
    if won_missing:
        add("opp-won-no-membership",
            "Resolve the won deals that never became memberships",
            "revenue leakage", "unquantified", None, None,
            "Companies: " + ", ".join(str(i) for i in won_missing["ids"][:8]),
            "Check each company in the WMS: onboarding gap, off-system agreement, or a "
            "duplicate ID.",
            "owner", "now", "medium",
            "No value is shown because a won deal's expected_value is not a billed rate.",
            records=[str(i) for i in won_missing["ids"][:10]])

    pricing = modules.get("pricing")
    if isinstance(pricing, dict) and pricing.get("deep_discounts"):
        forgone = ZERO
        for d in pricing["deep_discounts"]:
            forgone += (parse_money(str(d["list"])) or ZERO) - (parse_money(str(d["contracted"]))
                                                               or ZERO)
        add("opp-discounts", "Decide the end date for the deep discounts",
            "occupancy", "erosion", forgone if forgone > 0 else None, None,
            "; ".join(f"{d['unit_id']} at {d['discount_pct']}% below list"
                      for d in pricing["deep_discounts"]),
            "Confirm whether each discount is promotional (and when it ends) or permanent "
            "pricing that should be reflected in the list price.",
            "owner", "90", "medium",
            "Forgone list value is not lost revenue; some discounts were given for a reason "
            "worth keeping.",
            calculation="sum over deep-discounted units of (list_price - contracted_rate)")

    speed = modules.get("speed_to_lead")
    if isinstance(speed, dict) and int(speed.get("max_minutes") or 0) > 0:
        add("opp-response-tail", "Give after-hours enquiries an owner",
            "speed to lead", "unquantified", None, None,
            f"Median {speed.get('median_minutes')} minutes but the slowest response took "
            f"{speed.get('max_minutes')} minutes",
            "Agree a first-response standard and a named after-hours rota.",
            "sales", "30", "medium",
            "One slow response may be an outlier; the pattern needs a few months to confirm.",
            calculation="median and maximum of business-minute first responses")

    for cand in candidates:
        cand["severity_rank"] = SEVERITY_RANK.get(str(cand["module"]), 9)
        cand["basis_rank"] = BASIS_RANK.get(str(cand["basis"]), 9)

    BASIS_UNITS = {
        "recurring": "per month of recurring revenue at risk",
        "one_time": "one-time balance outstanding",
        "lost": "per month of recurring revenue that has already left",
        "erosion": "per month of list value; erosion, not cash",
        "unquantified": "not quantified - no measured amount exists in these exports",
    }

    def sort_key(c: dict[str, object]) -> tuple[int, float, int, str]:
        amount = c["monthly_recurring"] if c["monthly_recurring"] is not None \
            else c["one_time"]
        value = 0.0 if amount is None else -float(str(amount))
        return (int(str(c["basis_rank"])), value, int(str(c["severity_rank"])), str(c["id"]))

    ranked = sorted(candidates, key=sort_key)
    for i, c in enumerate(ranked, 1):
        c["rank"] = i
        c["amount_unit"] = BASIS_UNITS.get(str(c["basis"]), "not quantified")
    return {
        "ranking_rule": (
            "1) measured recurring revenue at risk, largest first; 2) measured one-time "
            "balances, largest first; 3) recurring revenue that has already left; 4) erosion "
            "of list value; 5) unquantified items ordered by severity class (data integrity, "
            "revenue leakage, churn, sales pipeline, tour conversion, speed to lead, "
            "occupancy, rooms) and then by id. Amounts are never extrapolated and never "
            "summed across different bases."),
        "amount_policy": (
            "Every amount is a sum of the records listed behind it, at the basis stated "
            "(recurring at risk, one-time balance, revenue already departed, or erosion of "
            "list value). Recurring and one-time amounts are deliberately not added "
            "together, and 'erosion' figures are potential, not cash."),
        "opportunities": ranked,
        "top": ranked[:5],
    }


def build_action_plan(opportunities: dict[str, Any]) -> dict[str, Any]:
    """Turn the ranked opportunities into a 90-day plan with named owners."""
    buckets: dict[str, list[dict[str, Any]]] = {"days_0_14": [], "days_15_45": [],
                                                "days_46_90": []}
    window_map = {"now": "days_0_14", "30": "days_15_45", "90": "days_46_90"}
    for c in opportunities.get("top", []):
        bucket = window_map.get(str(c.get("window")), "days_15_45")
        buckets[bucket].append({
            "opportunity_id": c["id"], "action": c["title"], "owner": c["owner"],
            "first_step": c["first_step"], "evidence": c["evidence"],
            "confidence": c["confidence"], "limitation": c["limitation"],
            "basis": c["basis"], "amount_unit": c.get("amount_unit"),
            "monthly_recurring": c["monthly_recurring"], "one_time": c["one_time"],
        })
    labels = {
        "days_0_14": "Next 14 days",
        "days_15_45": "Days 15-45",
        "days_46_90": "Days 46-90",
    }
    return {"buckets": buckets, "labels": labels,
            "note": "Actions are drawn only from the ranked opportunities above, each "
                    "traceable to a finding with its own evidence and limitation. Owners are "
                    "role labels (owner, finance, sales, community), not names."}


# --- Metrics (flat, for verification) --------------------------------------

def flat_metrics(bundle: dict[str, Any]) -> dict[str, str]:
    """Dotted metric map: the exact numbers a reviewer re-checks first."""
    modules: dict[str, Any] = bundle["modules"]
    out: dict[str, str] = {}

    def put(key: str, value: object) -> None:
        if value is None:
            return
        out[key] = str(value)

    occ = modules.get("occupancy")
    if isinstance(occ, dict):
        for m in occ.get("metrics", []):
            name = str(m["name"]).replace("_occupancy", "")
            put(f"occupancy.{name}.value", m.get("value"))
            put(f"occupancy.{name}.numerator", m.get("numerator"))
            put(f"occupancy.{name}.denominator", m.get("denominator"))
        put("occupancy.flag_count", len(occ.get("flags", [])))
    leak = modules.get("leakage")
    if isinstance(leak, dict):
        for f in leak.get("findings", []):
            check = str(f["check"])
            put(f"leakage.{check}.count", f.get("count"))
            for key in ("monthly_amount_at_risk", "amount_outstanding",
                        "monthly_list_value_blocked"):
                if key in f:
                    put(f"leakage.{check}.{key}", f[key])
    pipe = modules.get("pipeline")
    if isinstance(pipe, dict):
        put("pipeline.deal_count", pipe.get("deal_count"))
        for name, items in pipe.get("findings", {}).items():
            put(f"pipeline.{name}.count", len(items))
    stl = modules.get("speed_to_lead")
    if isinstance(stl, dict):
        put("speed_to_lead.responded_leads", stl.get("responded_leads"))
        put("speed_to_lead.leads_without_response",
            len(stl.get("leads_without_response", []) or []))
        for key in ("median_minutes", "p90_minutes", "max_minutes"):
            put(f"speed_to_lead.{key}", stl.get(key))
    funnel = modules.get("funnel")
    if isinstance(funnel, dict):
        for k, v in funnel.get("counts", {}).items():
            put(f"funnel.counts.{k}", v)
        for k, v in funnel.get("rates", {}).items():
            put(f"funnel.rates.{k}", v)
    coll = modules.get("collections")
    if isinstance(coll, dict):
        put("collections.outstanding_total", coll.get("outstanding_total"))
        put("collections.queue_size", len(coll.get("queue", [])))
    churn = modules.get("churn")
    if isinstance(churn, dict):
        put("churn.base_memberships", churn.get("base_memberships"))
        put("churn.canceled_memberships", churn.get("canceled_memberships"))
        put("churn.base_mrr", churn.get("base_mrr"))
        put("churn.lost_mrr", churn.get("lost_mrr"))
        put("churn.logo_churn", churn.get("logo_churn", {}).get("value"))
        put("churn.revenue_churn", churn.get("revenue_churn", {}).get("value"))
    renewals = modules.get("renewals")
    if isinstance(renewals, dict):
        put("renewals.agreements_in_window", len(renewals.get("agreements_in_window", [])))
        put("renewals.month_to_month", len(renewals.get("month_to_month_active", [])))
    forecast = modules.get("forecast")
    if isinstance(forecast, dict):
        for h in forecast.get("horizons", []):
            days = int(h["horizon_days"])
            put(f"forecast.h{days}.occupied", h.get("contracted_occupied_capacity"))
            put(f"forecast.h{days}.capacity", h.get("sellable_capacity"))
            put(f"forecast.h{days}.occupancy", h.get("contracted_occupancy"))
            if days <= 90:
                for mid in h.get("departures", []):
                    out.setdefault("forecast.departures_by_90d", "")
                    out["forecast.departures_by_90d"] = (
                        out["forecast.departures_by_90d"] + f"{mid},").rstrip(",")
    pricing = modules.get("pricing")
    if isinstance(pricing, dict):
        put("pricing.deep_discount_count", len(pricing.get("deep_discounts", [])))
    locations = modules.get("locations")
    if isinstance(locations, dict):
        put("locations.count", len(locations.get("locations", [])))
    out["inputs.file_count"] = str(bundle["inputs"]["file_count"])
    out["inputs.mapped_roles"] = ",".join(sorted(
        str(f["role"]) for f in bundle["inputs"]["files"]
        if not str(f["role"]).startswith("(")))
    out["findings.count"] = str(len(bundle["findings"]))
    out["metrics.count"] = str(len(out))
    return out


# --- Top-level run ----------------------------------------------------------

def _fingerprint(path: Path) -> str:
    """Content fingerprint of an export, normalized to LF line endings.

    The engine reads exports as text, so a Windows checkout (CRLF) and a Linux
    checkout (LF) must fingerprint identically - otherwise a report generated
    on one machine could not be reproduced on the other.
    """
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return f"sha256:{hashlib.sha256(data).hexdigest()[:16]} ({len(data)} normalized bytes)"


def run_health_check(input_dir: str | Path, *, client: str, as_of: date,
                     generated_at: str, policy: str = "report",
                     allow_unsafe: bool = False,
                     unsafe_reason: str | None = None,
                     overrides: dict[str, str] | None = None,
                     stale_days: int = 21, discount_pct: int = 25,
                     churn_window_days: int = 30, renewal_window_days: int = 90,
                     horizons: tuple[int, ...] = (30, 60, 90, 180),
                     open_hours: Decimal | None = None,
                     max_file_bytes: int | None = None) -> dict[str, Any]:
    """Run one health check and return the full engagement bundle.

    Raises PreflightBlocked when the screening refuses the folder and
    ``allow_unsafe`` was not passed. An override without a non-empty
    ``unsafe_reason`` is refused: the reason is part of the record.
    """
    reason = (unsafe_reason or "").strip()
    if allow_unsafe and not reason:
        raise ValueError(
            "--allow-unsafe requires unsafe_reason: who accepted the folder and why")
    if reason and not allow_unsafe:
        raise ValueError("unsafe_reason is only valid together with allow_unsafe")
    preflight, mapped, ambiguities = discover_inputs(
        input_dir, overrides=overrides, policy=policy, max_file_bytes=max_file_bytes)
    if not preflight.ok and not allow_unsafe:
        raise PreflightBlocked(preflight)

    ambiguous_roles = {str(a["role"]) for a in ambiguities}
    tables = _load_tables(input_dir, mapped, ambiguous_roles)
    run = run_modules(tables, as_of, stale_days=stale_days, discount_pct=discount_pct,
                      churn_window_days=churn_window_days,
                      renewal_window_days=renewal_window_days, horizons=horizons,
                      open_hours=open_hours)
    quality = quality_section(mapped, tables)

    context = _context_section(tables, as_of, preflight, allow_unsafe, reason, policy)
    context["currency"] = detect_engagement_currency(tables)
    bundle: dict[str, Any] = {
        "service": {"name": SERVICE_NAME, "version": SERVICE_VERSION,
                    "engine_version": __version__, "status": "draft",
                    "review_required": True,
                    "status_label": "DRAFT REPORT - REVIEW REQUIRED"},
        "engagement": {
            "client": client,
            "as_of": as_of.isoformat(),
            "generated_at": generated_at,
            "input_root": str(input_dir),
            "churn_window_days": churn_window_days,
            "renewal_window_days": renewal_window_days,
            "stale_days": stale_days,
            "discount_pct": discount_pct,
            "horizons": list(horizons),
            "allow_unsafe": allow_unsafe,
            "pii_policy": policy,
            **({"unsafe_reason": reason} if allow_unsafe else {}),
        },
        "preflight": preflight.as_dict(),
        "inputs": {
            "file_count": len(mapped),
            "files": [m.as_dict() for m in mapped],
            "ambiguities": ambiguities,
            "context_only": [m.source for m in mapped if m.context_only],
            "unusable": [{"source": m.source, "missing_required": m.missing_required}
                         for m in mapped if m.missing_required and not m.context_only],
            "fingerprints": {
                str(f.path): _fingerprint(Path(preflight.root) / f.path)
                for f in preflight.files},
        },
        "context": context,
        "quality": quality,
        "modules": run["modules"],
        "not_measured": run["not_measured"],
        "tables": tables,
    }
    bundle["findings"] = build_findings(bundle)
    bundle["opportunities"] = build_opportunities(bundle)
    bundle["action_plan"] = build_action_plan(bundle["opportunities"])
    bundle["metrics"] = flat_metrics(bundle)
    bundle["limitations"] = _limitations(bundle)
    del bundle["tables"]
    return sanitize_bundle(bundle)


def sanitize_bundle(bundle: dict[str, Any],
                    salt: str = "opencoworking-health-check") -> dict[str, Any]:
    """Redact identifier-shaped strings everywhere in the bundle.

    Reports and the emitted JSON both travel onward (to the client, their
    accountant, a lender). Some engine outputs legitimately quote values from
    the export - a duplicated-contact finding cites the shared email, for
    example - so every string in the bundle is passed through the deterministic
    redactor before it is returned or written. Record identifiers (M-011,
    INV-1004) and unit IDs are unaffected: they are not personal data and the
    report depends on them.
    """
    redactor = Redactor(salt=salt)

    def walk(node: object) -> object:
        if isinstance(node, str):
            return redactor.redact_text(node)
        if isinstance(node, list):
            return [walk(item) for item in node]
        if isinstance(node, dict):
            return {key: walk(value) for key, value in node.items()}
        return node

    clean = walk(bundle)
    assert isinstance(clean, dict)
    clean["data_handling"] = {
        "identifiers_redacted": redactor.replacements,
        "method": "deterministic pseudonyms (emails, phone numbers, Luhn-valid card "
                  "numbers) applied to every string in this bundle",
        "note": "Pattern-based redaction reduces risk; a reviewer still confirms the "
                "deliverable before it leaves the desk.",
    }
    return clean


def _context_section(tables: dict[str, Table], as_of: date, preflight: PreflightResult,
                     allow_unsafe: bool, unsafe_reason: str, policy: str) -> dict[str, object]:
    locations = tables.get("locations")
    names = []
    if locations is not None:
        names = [r.get("name", r.get("location_id", "?")) for r in locations.rows]
    memberships = tables.get("memberships")
    active = 0
    if memberships is not None:
        active = sum(1 for r in memberships.rows
                     if r.get("status", "").strip().lower() == "active")
    return {
        "operator_profile_note": (
            "This engagement used no saved operator profile and no KPI targets; every "
            "definition in this report is the engine's printed formula. Targets and "
            "definitions supplied by the operator belong in a context file and are not "
            "assumed here."),
        "as_of": as_of.isoformat(),
        "locations": names,
        "location_count": len(names),
        "active_memberships": active,
        "input_root": preflight.root,
        "pii_policy": policy,
        "unsafe_override_used": allow_unsafe,
        **({"unsafe_reason": unsafe_reason} if allow_unsafe else {}),
        "pii_handling": (
            "Direct identifiers in the exports are never printed in this report, and no "
            "client export is copied into the report directory. Any identifier that has to "
            "appear in a finding is passed through the engine's deterministic redactor "
            "(stable pseudonyms, so records stay joinable)."),
    }


def _limitations(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Everything a reviewer must not over-claim, gathered in one place."""
    out: list[dict[str, Any]] = []
    for item in bundle.get("not_measured", []):
        out.append({"type": "missing_input",
                    "detail": f"{item['module']}: NOT MEASURABLE - {item['reason']}"})
    for item in bundle["inputs"]["unusable"]:
        out.append({"type": "unusable_file",
                    "detail": f"{item['source']} is missing required column(s) "
                              f"{', '.join(item['missing_required'])}; it was not used."})
    for amb in bundle["inputs"]["ambiguities"]:
        out.append({"type": "ambiguous_role", "detail": str(amb["reason"]) + " " +
                                                str(amb["resolution"])})
    for item in bundle["inputs"]["files"]:
        if item.get("superseded_by"):
            out.append({"type": "superseded_file",
                        "detail": f"{item['source']} was not analysed: "
                                  f"{item['superseded_by']} was named as the authoritative "
                                  f"file for the {item['role']} role."})
        elif str(item.get("role")) == "(unidentified)":
            out.append({"type": "unidentified_file",
                        "detail": f"{item['source']} matched no canonical entity from its "
                                  "column names, so no diagnostic used it; it is listed for "
                                  "human review only."})
        elif str(item.get("role")) == "(not analysed)":
            out.append({"type": "unanalysed_file",
                        "detail": f"{item['source']} is not a tabular export and was not "
                                  "analysed."})
        elif item.get("context_only"):
            out.append({"type": "context_only_file",
                        "detail": f"{item['source']} was identified as '{item['role']}' "
                                  "but no diagnostic in this engagement consumes that "
                                  "export."})
    for f in bundle["preflight"]["files"]:
        if f["status"] == "blocked":
            out.append({"type": "preflight_blocked",
                        "detail": f"{f['path']} was blocked: "
                                  + "; ".join(x["message"] for x in f["findings"])})
        elif f["status"] == "warning":
            out.append({"type": "preflight_warning",
                        "detail": f"{f['path']}: "
                                  + "; ".join(x["message"] for x in f["findings"])})
    out += [
        {"type": "engine_limit",
         "detail": "No market rates, benchmarks, or comparisons with other operators: every "
                   "number describes this operator's own exports only."},
        {"type": "engine_limit",
         "detail": "No attendance or utilization data is involved; occupancy is contracted "
                   "inventory consumption, not physical presence."},
        {"type": "engine_limit",
         "detail": "Period alignment is the reviewer's responsibility: exports that cover "
                   "different date ranges mix periods in funnel and churn counts."},
        {"type": "engine_limit",
         "detail": "Anything living outside the supplied exports (email threads, verbal "
                   "promises, off-system agreements, support history) is invisible here."},
        {"type": "engine_limit",
         "detail": "No legal, tax, or compliance conclusions; escalations beyond a "
                   "conversation are for professionals."},
        {"type": "review_gate",
         "detail": "This document is a draft until an operator reviews it and runs the "
                   "finalize step. Nothing is sent to anyone by this tool."},
    ]
    return out
