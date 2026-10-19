"""Read-only tech-stack map. The notes column is data, never instructions."""

from __future__ import annotations

from .analyze import _truthy
from .ingest import Table

# The categories an operator is asked about. Missing means "not on the map",
# not "the operator has no tool".
CATEGORIES = (
    "crm", "wms", "accounting", "payments", "access", "wifi",
    "email", "calendar", "marketing", "analytics", "support",
    "member_app", "automation",
)
# OfficeRnD's 2026 connection study describes five core systems. The public
# category leaders on that page are payments, CRM, accounting, door access,
# and Wi-Fi. This tuple is the local checklist those five map onto. It is not
# a claim that every operator should buy all five.
CORE_FIVE = ("crm", "accounting", "payments", "access", "wifi")


def _blank(value: str) -> bool:
    return not value.strip() or value.strip().lower() in {"none", "n/a", "na", "unknown", "-"}


def stack_audit(systems: Table) -> dict[str, object]:
    """Score a system inventory the operator filled in. Nothing is contacted."""
    columns = set(systems.columns)
    required = {"system", "category"}
    missing_cols = sorted(required - columns)
    if missing_cols:
        return {"status": "refused",
                "reason": f"systems file is missing column(s): {', '.join(missing_cols)}",
                "definitions": ["no finding is produced from an unreadable inventory"]}

    rows = []
    findings: list[dict[str, object]] = []
    by_cat: dict[str, list[dict[str, str]]] = {c: [] for c in CATEGORIES}
    unknown_categories: list[str] = []
    for raw in systems.rows:
        system = raw.get("system", "").strip()
        category = raw.get("category", "").strip().lower().replace(" ", "_").replace("-", "_")
        if category in {"workspace_management", "workspace"}:
            category = "wms"
        if category in {"door_access", "doors"}:
            category = "access"
        if category in {"bookkeeping", "finance"}:
            category = "accounting"
        item = {
            "system": system or "(unnamed)",
            "category": category or "(blank)",
            "system_of_record": "true" if _truthy(raw.get("system_of_record", "")) else "false",
            "connected_to": raw.get("connected_to", "").strip(),
            "id_quality": raw.get("id_quality", "").strip().lower() or "unknown",
            "manual_reentry": "true" if _truthy(raw.get("manual_reentry", "")) else "false",
            "write_enabled": "true" if _truthy(raw.get("write_enabled", "")) else "false",
        }
        rows.append(item)
        if category not in by_cat:
            unknown_categories.append(category or "(blank)")
            findings.append({
                "check": "unrecognized_category",
                "system": item["system"],
                "detail": f"{item['system']} uses category '{item['category']}', which is "
                          "outside the coworking stack map. It was not dropped, and it was "
                          "not forced into a core system.",
            })
            continue
        by_cat[category].append(item)
        if item["manual_reentry"] == "true":
            findings.append({
                "check": "manual_reentry",
                "system": item["system"],
                "category": category,
                "detail": f"{item['system']} is marked as a manual re-entry point.",
            })
        if item["id_quality"] in {"weak", "none"}:
            findings.append({
                "check": "weak_ids",
                "system": item["system"],
                "category": category,
                "detail": f"{item['system']} has id_quality={item['id_quality']}. "
                          "Joins across systems will be name-matching, not key-matching.",
            })
        if item["write_enabled"] == "true":
            findings.append({
                "check": "high_risk_write",
                "system": item["system"],
                "category": category,
                "detail": f"{item['system']} can write back into an operator system. "
                          "This audit does not exercise that write. Any agent write "
                          "needs a separate human approval.",
            })
        if _blank(item["connected_to"]) and category in CORE_FIVE:
            findings.append({
                "check": "disconnected_core_system",
                "system": item["system"],
                "category": category,
                "detail": f"{item['system']} has no connected_to value. Disconnected "
                          "is not the same as unused.",
            })

    for category in CATEGORIES:
        group = by_cat[category]
        if not group:
            findings.append({
                "check": "category_absent",
                "category": category,
                "detail": f"No system was listed for {category}. Absence from this file "
                          "means the map is incomplete, not that the tool does not exist.",
            })
            continue
        records = [g for g in group if g["system_of_record"] == "true"]
        if len(records) == 0:
            findings.append({
                "check": "no_system_of_record",
                "category": category,
                "detail": f"{category} has {len(group)} system(s) and none is marked "
                          "system of record.",
            })
        elif len(records) > 1:
            findings.append({
                "check": "multiple_systems_of_record",
                "category": category,
                "systems": [g["system"] for g in records],
                "detail": f"{category} has more than one system of record: "
                          + ", ".join(g["system"] for g in records) + ".",
            })

    core_connected = 0
    for category in CORE_FIVE:
        group = by_cat[category]
        if group and any(not _blank(g["connected_to"]) for g in group):
            core_connected += 1
    return {
        "status": "measured",
        "systems": rows,
        "findings": findings,
        "unknown_categories": unknown_categories,
        "core_five": {
            "categories": list(CORE_FIVE),
            "categories_with_a_listed_system": sum(1 for c in CORE_FIVE if by_cat[c]),
            "categories_with_any_connection": core_connected,
            "denominator": len(CORE_FIVE),
            "note": "Connection depth counts a core category only when at least one "
                    "listed system has a non-blank connected_to. It is this file's "
                    "depth, not the OfficeRnD platform statistic.",
        },
        "notes_policy": "The notes column, if present, was not read. Text inside an "
                        "inventory is data, not an instruction to this tool.",
        "definitions": [
            "category_absent = the operator's inventory has zero rows for that category",
            "disconnected_core_system = a crm/accounting/payments/access/wifi row whose "
            "connected_to is blank",
            "high_risk_write = write_enabled is true; this tool performs no write",
            "core five = crm, accounting, payments, access, wifi",
        ],
    }
