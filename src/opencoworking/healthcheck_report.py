"""Render a health-check bundle as one self-contained, print-ready HTML report.

Presentation only: every number comes from the bundle produced by
``healthcheck.run_health_check``, already computed by the engine. The renderer
never calculates, never renames a metric, and never fills a gap: anything the
engine could not measure prints as NOT MEASURABLE with the reason the engine
gave.

Two rules the renderer enforces on itself:

* every value taken from client data is HTML-escaped, so an export cell cannot
  inject markup into the deliverable;
* every text value drawn from client data also passes through the engine's
  deterministic redactor, so a stray identifier in an export cannot leak into a
  document that gets forwarded to a client, their accountant, or a lender.

The draft banner is not removable by this module: only the finalize step
(``health-check-finalize``) produces a report that drops it, and it records who
reviewed it and when.
"""

from __future__ import annotations

import html
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from .redact import Redactor

CLASS_LABELS = {
    "fact": ("FACT", "Quoted from the export; no calculation involved."),
    "calculation": ("CALCULATION", "Arithmetic on the exports, with the formula shown."),
    "inference": ("INFERENCE", "A reading of the facts; not itself measured."),
    "recommendation": ("RECOMMENDATION", "A suggested action; a human decides."),
}

CONFIDENCE_TONE = {"high": "conf-high", "medium": "conf-medium", "low": "conf-low"}

LIMITATION_LABELS = {
    "missing_input": "Not measurable (input missing)",
    "unusable_file": "File not used",
    "superseded_file": "File superseded by an explicit mapping",
    "unidentified_file": "File not identified",
    "unanalysed_file": "File not analysed",
    "context_only_file": "Context only (not analysed)",
    "ambiguous_role": "Ambiguous file role",
    "preflight_blocked": "Blocked at preflight",
    "preflight_warning": "Preflight warning",
    "engine_limit": "Engine limit",
    "review_gate": "Review gate",
}


def _esc(value: Any, redactor: Redactor | None = None) -> str:
    text = "" if value is None else str(value)
    if redactor is not None:
        text = redactor.redact_text(text)
    return html.escape(text, quote=True)


def _badge(kind: str) -> str:
    label, title = CLASS_LABELS.get(kind, (kind.upper(), ""))
    return f'<span class="tag tag-{kind}" title="{_esc(title)}">{_esc(label)}</span>'


def _pct(value: Any) -> str:
    try:
        return f"{float(str(value)) * 100:.1f}%"
    except (TypeError, ValueError):
        return "not measurable"


# Per-render currency label, set once by render_health_check from the bundle's
# detected currency. Empty means the exports carried no hint, and amounts are
# printed exactly as the source system supplied them.
_CURRENCY_SYMBOL = ""


def _money(value: Any) -> str:
    if value is None or value == "":
        return "not quantified"
    try:
        amount = Decimal(str(value))
    except Exception:  # noqa: BLE001 - any unparseable value is simply printed raw
        return _esc(value)
    return f"{_CURRENCY_SYMBOL}{amount:,.2f}" if _CURRENCY_SYMBOL else f"{amount:,.2f}"


def _humanize(name: Any) -> str:
    text = str(name).replace("_", " ").strip()
    return text[:1].upper() + text[1:] if text else text


def _not_measurable(section: str, reason: str, needs: str = "") -> str:
    # Kept free of nested f-string escaping: this project still supports 3.11,
    # where backslashes inside f-strings are a syntax error.
    needs_html = ""
    if needs:
        needs_html = f'<p class="needs">Required input: {_esc(needs)}</p>'
    return ('<div class="not-measurable">'
            + f'<strong>NOT MEASURABLE — {_esc(section)}</strong>'
            + f'<p>{_esc(reason)}</p>'
            + needs_html
            + "</div>")


def _table(headers: list[str], rows: list[list[Any]], redactor: Redactor | None = None,
           empty: str = "No records.") -> str:
    if not rows:
        return f'<p class="muted">{_esc(empty)}</p>'
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_esc(c, redactor)}</td>" for c in row) + "</tr>"
        for row in rows)
    return (f'<table class="grid"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')


def _finding_block(finding: dict[str, Any], redactor: Redactor | None, index: int) -> str:
    kind = str(finding.get("kind", "fact"))
    conf = str(finding.get("confidence", "medium"))
    tone = CONFIDENCE_TONE.get(conf, "conf-medium")
    records = finding.get("records") or []
    data_used = finding.get("data_used") or []
    records_html = (
        f'<p class="records"><span class="lbl">Records</span>'
        f'{_esc(", ".join(str(r) for r in records), redactor)}</p>'
        if records else "")
    return f"""
<article class="finding" id="finding-{index}">
  <header>
    <div class="finding-head">
      <h3>{_esc(finding.get('title'), redactor)}</h3>
      <div class="tags">{_badge(kind)}
        <span class="conf {tone}">confidence: {_esc(conf)}</span>
        <span class="module">{_esc(finding.get('module'))}</span>
      </div>
    </div>
  </header>
  <p class="statement">{_esc(finding.get('statement'), redactor)}</p>
  <dl class="contract">
    <dt>Data used</dt>
    <dd>{_esc('; '.join(str(d) for d in data_used), redactor) or 'not stated'}</dd>
    <dt>Calculation</dt><dd>{_esc(finding.get('calculation'), redactor)}</dd>
    <dt>Confidence</dt><dd>{_esc(conf)} — {_esc(finding.get('confidence_basis'), redactor)}</dd>
    <dt>Limitation</dt><dd>{_esc(finding.get('limitation'), redactor)}</dd>
  </dl>
  {records_html}
</article>"""


def _amount_html(opp: dict[str, Any]) -> str:
    raw = opp.get("monthly_recurring") if opp.get("monthly_recurring") is not None \
        else opp.get("one_time")
    unit = str(opp.get("amount_unit") or "")
    if raw is None:
        return ('<span class="amount amount-soft">not quantified</span>'
                f'<span class="amount-unit">{_esc(unit)}</span>')
    soft = " amount-soft" if opp.get("basis") in {"erosion", "lost"} else ""
    return (f'<span class="amount{soft}">{_money(raw)}</span>'
            f'<span class="amount-unit">{_esc(unit)}</span>')


def _opportunity_block(opp: dict[str, Any], redactor: Redactor | None) -> str:
    amount = _amount_html(opp)
    conf = str(opp.get("confidence", "medium"))
    return f"""
<article class="opportunity" id="{_esc(opp.get('id'))}">
  <div class="opp-head">
    <span class="rank">{_esc(opp.get('rank'))}</span>
    <h3>{_esc(opp.get('title'), redactor)}</h3>
  </div>
  <div class="opp-body">
    <div class="opp-amount">{amount}</div>
    <dl class="contract">
      <dt>Evidence</dt><dd>{_esc(opp.get('evidence'), redactor)}</dd>
      <dt>Calculation</dt><dd>{_esc(opp.get('calculation'), redactor) or 'no amount attached'}</dd>
      <dt>First step</dt><dd>{_esc(opp.get('first_step'), redactor)}</dd>
      <dt>Owner / window</dt><dd>{_esc(opp.get('owner'))} · {_esc(opp.get('window'))}
        days to first impact</dd>
      <dt>Confidence</dt><dd><span class="conf {CONFIDENCE_TONE.get(conf, 'conf-medium')}">
        {_esc(conf)}</span></dd>
      <dt>Limitation</dt><dd>{_esc(opp.get('limitation'), redactor)}</dd>
    </dl>
  </div>
</article>"""


def _metric_cards(occupancy: dict[str, Any], redactor: Redactor | None) -> str:
    cards = []
    for metric in occupancy.get("metrics", []):
        warnings = "".join(f"<li>{_esc(w, redactor)}</li>"
                           for w in metric.get("warnings", []))
        exclusions = ", ".join(str(e) for e in metric.get("exclusions", []))
        tone = "metric-card"
        value = metric.get("value")
        if value is None:
            tone += " metric-undefined"
        cards.append(f"""
<div class="{tone}">
  <div class="metric-name">{_esc(metric.get('name'))}</div>
  <div class="metric-value">{_pct(value) if value is not None else "undefined"}</div>
  <div class="metric-frac">{_esc(metric.get('numerator'))} / {_esc(metric.get('denominator'))}</div>
  <p class="formula">{_esc(metric.get('formula'))}</p>
  <p class="exclusions"><span class="lbl">Excludes</span> {_esc(exclusions)}</p>
  {f'<ul class="warnlist">{warnings}</ul>' if warnings else ''}
</div>""")
    return f'<div class="metric-grid">{"".join(cards)}</div>' if cards else ""


def _preflight_block(bundle: dict[str, Any], redactor: Redactor | None) -> str:
    pre = bundle.get("preflight", {})
    rows = []
    for f in pre.get("files", []):
        findings = "; ".join(str(x.get("message")) for x in f.get("findings", []))
        rows.append([f.get("path"), f.get("status"), f.get("rows", "—"),
                     ", ".join(f.get("pii_columns", [])) or "—",
                     findings or "—"])
    body = _table(["File", "Preflight", "Rows", "Identifier columns found", "Notes"],
                  rows, redactor)
    override = ("<p class='callout callout-warn'><strong>Unsafe override in effect.</strong> "
                "This run proceeded past a blocking preflight finding with --allow-unsafe. "
                "The override is recorded in the engagement manifest.</p>"
                if pre.get("blocking_count") and bundle.get("engagement", {}).get(
                    "allow_unsafe") else "")
    return body + override + f'<p class="muted">{_esc(pre.get("guarantee_note"))}</p>'


def _data_handling_block(bundle: dict[str, Any], redactor: Redactor | None) -> str:
    pre = bundle.get("preflight", {})
    files = bundle.get("inputs", {}).get("files", [])
    redactions = int(str((bundle.get("data_handling") or {})
                         .get("identifiers_redacted", 0)))
    with_identifiers = [f"{f['source']} ({', '.join(f['pii_columns'][:4])})"
                        for f in files if f.get("pii_columns")]
    items = [
        f"{pre.get('file_count', 0)} file(s) were screened before any analysis; "
        f"{pre.get('blocking_count', 0)} blocked and {pre.get('warning_count', 0)} "
        "flagged for human review.",
        (f"{redactions} identifier-shaped value(s) were replaced with stable pseudonyms "
         "anywhere they occurred in this report and its machine-readable bundle."
         if redactions else
         "No identifier-shaped value was found in the analysed outputs, so nothing needed "
         "redacting."),
        ("Files carrying identifier columns: " + "; ".join(with_identifiers)
         + ". Those columns were used for their metrics only and are never printed."
         if with_identifiers else "No file declared identifier columns."),
        "No export row is copied into this report directory: the report and its bundle "
        "carry aggregates, classifications, and record identifiers (M-011, INV-1004) only.",
        "Pattern-based screening and redaction reduce risk; they do not certify a folder "
        "or a document. The reviewer confirms both before release (REVIEW_CHECKLIST.md).",
        "This tool makes no network calls, uploads nothing, and sends nothing to anyone.",
    ]
    return ("<h3>How your data was handled</h3><ul class='assumptions'>"
            + "".join(f"<li>{_esc(i, redactor)}</li>" for i in items) + "</ul>")


def _quality_block(bundle: dict[str, Any], redactor: Redactor | None) -> str:
    quality = bundle.get("quality", {})
    rows = []
    for f in quality.get("files", []):
        rows.append([
            f.get("source"),
            f.get("role"),
            f.get("rows"),
            f.get("identification", "—"),
            "yes" if f.get("checked") else "no",
            len(f.get("renamed_columns", {}) or {})
            if isinstance(f.get("renamed_columns"), dict) else f.get("renamed_columns", 0),
            ", ".join(f.get("unmapped_columns", []) or []) or "—",
            ", ".join(f.get("missing_required", []) or []) or "—",
            f"{f.get('errors', 0)} err / {f.get('warnings', 0)} warn",
        ])
    out = _table(["File", "Role", "Rows", "Identified by", "Analysed", "Renamed cols",
                  "Unmapped headers", "Missing required", "Checks"], rows, redactor)
    details = []
    for f in quality.get("files", []):
        for finding in f.get("findings", []):
            details.append(f"<li><strong>{_esc(f.get('source'), redactor)}</strong> · "
                           f"{_esc(finding.get('severity'))} · "
                           f"{_esc(finding.get('check'))}: "
                           f"{_esc(finding.get('message'), redactor)}</li>")
    if details:
        out += f'<ul class="findings-list">{"".join(details)}</ul>'
    amb = bundle.get("inputs", {}).get("ambiguities", [])
    if amb:
        out += "<h3>Ambiguous mappings refused</h3>"
        out += _table(["Type", "Role", "Files", "What happened", "How to resolve"],
                      [[a.get("type"), a.get("role") or a.get("canonical_column"),
                        ", ".join(a.get("sources", []) or a.get("source_columns", [])),
                        a.get("reason"), a.get("resolution", "resolve the column by hand")]
                       for a in amb], redactor)
    return out


def _occupancy_section(bundle: dict[str, Any], redactor: Redactor | None,
                       not_measured: dict[str, dict[str, Any]]) -> str:
    out = []
    occ = bundle.get("modules", {}).get("occupancy")
    if isinstance(occ, dict):
        out.append(_metric_cards(occ, redactor))
        flags = occ.get("flags", [])
        if flags:
            rows = []
            for flag in flags:
                units = flag.get("units", [])
                if units and isinstance(units[0], dict):
                    listed = ", ".join(str(u.get("unit_id")) for u in units[:10])
                else:
                    listed = ", ".join(str(u) for u in units[:10])
                rows.append([flag.get("flag"), len(units), listed, flag.get("why")])
            out.append("<h3>Occupancy flags (named units, not estimates)</h3>")
            out.append(_table(["Flag", "Units", "Unit IDs", "Why it matters"], rows, redactor))
        issues = occ.get("referential_issues", [])
        if issues:
            out.append("<h3>Referential issues found while joining inventory to memberships</h3>")
            out.append("<ul class='findings-list'>" + "".join(
                f"<li>{_esc(str(i), redactor)}</li>" for i in issues) + "</ul>")
    else:
        out.append(_not_measurable("Occupancy",
                                   not_measured.get("occupancy", {}).get("reason", ""),
                                   "inventory + memberships exports"))

    forecast = bundle.get("modules", {}).get("forecast")
    if isinstance(forecast, dict):
        rows = [[f"{h.get('horizon_days')} days", h.get("date"),
                 f"{h.get('contracted_occupied_capacity')} / {h.get('sellable_capacity')}",
                 _pct(h.get("contracted_occupancy")),
                 ", ".join(str(x) for x in h.get("departures", [])) or "—",
                 ", ".join(str(x) for x in h.get("arrivals", [])) or "—"]
                for h in forecast.get("horizons", [])]
        out.append("<h3>Contracted forward view (what is already signed, nothing "
                   "assumed)</h3>")
        out.append(_table(["Horizon", "Date", "Occupied capacity", "Occupancy",
                           "Recorded departures", "Arrivals"], rows, redactor))
        out.append("<ul class='assumptions'>" + "".join(
            f"<li>{_esc(a, redactor)}</li>" for a in forecast.get("assumptions", [])) + "</ul>")
    else:
        out.append(_not_measurable("Contracted forward view",
                                   not_measured.get("forecast", {}).get("reason", ""),
                                   "inventory + memberships exports"))
    return "\n".join(out)


def _leakage_section(bundle: dict[str, Any], redactor: Redactor | None,
                     not_measured: dict[str, dict[str, Any]]) -> str:
    leak = bundle.get("modules", {}).get("leakage")
    if not isinstance(leak, dict):
        return _not_measurable("Revenue leakage",
                               not_measured.get("leakage", {}).get("reason", ""),
                               "any export")
    out = []
    findings = leak.get("findings", [])
    if not findings:
        out.append('<p class="muted">No leakage finding from the checks that ran. '
                   'That means the checks found nothing; it does not mean the checks '
                   'were exhaustive.</p>')
    for f in findings:
        amounts = []
        if "monthly_amount_at_risk" in f:
            amounts.append(f"<li><strong>{_money(f['monthly_amount_at_risk'])}</strong> per "
                           "month, recurring rate at risk</li>")
        if "amount_outstanding" in f:
            amounts.append(f"<li><strong>{_money(f['amount_outstanding'])}</strong> "
                           "one-time balance outstanding</li>")
        if "monthly_list_value_blocked" in f:
            amounts.append(f"<li><strong>{_money(f['monthly_list_value_blocked'])}</strong> "
                           "per month of list value blocked (erosion, not cash)</li>")
        records = f.get("ids") or [
            i.get("membership_id") or i.get("invoice_id") or i.get("unit_id")
            or i.get("company_id") for i in f.get("items", [])]
        amounts_html = ''.join(amounts)
        if amounts_html:
            amounts_html = f'<ul class="amounts">{amounts_html}</ul>'
        records_html = ''
        if records:
            listed = _esc(", ".join(str(r) for r in records[:15]), redactor)
            records_html = ("<p class='records'><span class='lbl'>Records</span>"
                            + listed + "</p>")
        title = _esc(_humanize(f.get('check')))
        count = _esc(f.get('count'))
        detail = _esc(f.get('detail'), redactor)
        out.append("<div class='finding'><div class='finding-head'>"
                   f"<h3>{title}</h3><div class='tags'>"
                   f"<span class='count'>{count} record(s)</span></div></div>"
                   f"<p class='statement'>{detail}</p>{amounts_html}{records_html}</div>")
    skipped = leak.get("skipped_checks", [])
    if skipped:
        out.append('<div class="not-measurable"><strong>NOT MEASURABLE — checks skipped '
                   'for missing inputs</strong><ul>' + "".join(
                       f"<li>{_esc(s, redactor)}</li>" for s in skipped) + "</ul></div>")
    out.append('<p class="callout"><strong>Amounts are never summed into one total.</strong> '
               f'{_esc(leak.get("quantification_note"), redactor)} A recurring rate and a '
               'one-time balance describe different money, and erosion of list value is '
               'potential, not cash.</p>')
    return "\n".join(out)


def _pipeline_section(bundle: dict[str, Any], redactor: Redactor | None,
                      not_measured: dict[str, dict[str, Any]]) -> str:
    pipe = bundle.get("modules", {}).get("pipeline")
    if not isinstance(pipe, dict):
        return _not_measurable("Sales pipeline",
                               not_measured.get("pipeline", {}).get("reason", ""),
                               "deals export")
    out = ["<h3>Stage mix (all deals in the export)</h3>",
           _table(["Stage", "Deals"],
                  [[k, v] for k, v in (pipe.get("stage_counts") or {}).items()], redactor)]
    findings = pipe.get("findings", {})
    rows = [[name.replace("_", " "), len(items)] for name, items in findings.items()]
    out.append("<h3>Hygiene rules and what they caught</h3>")
    out.append(_table(["Rule", "Open deals affected"], rows, redactor))
    stale = findings.get("stale_deals", [])
    if stale:
        out.append(f'<h3>Stale open deals (untouched {_esc(pipe.get("stale_threshold_days"))}'
                   " days or more)</h3>")
        out.append(_table(["Deal", "Stage", "Owner", "Days since update"],
                          [[d.get("deal_id"), d.get("stage"), d.get("owner") or "(unowned)",
                            d.get("days_since_update")] for d in stale], redactor))
    unassigned = findings.get("unassigned", [])
    if unassigned:
        out.append("<h3>Open deals with no owner</h3>")
        out.append(_table(["Deal", "Stage"],
                          [[d.get("deal_id"), d.get("stage")] for d in unassigned], redactor))
    dupes = findings.get("duplicate_open_deals", [])
    if dupes:
        out.append("<h3>Duplicate open deals (same company and product)</h3>")
        out.append(_table(["Company", "Product", "Deal IDs"],
                          [[d.get("company_id"), d.get("product"),
                            ", ".join(str(x) for x in d.get("deal_ids", []))] for d in dupes],
                          redactor))
    out.append(f'<p class="muted">Open deals by owner: '
               f'{_esc(pipe.get("open_deals_by_owner"), redactor)}</p>')
    return "\n".join(out)


def _speed_section(bundle: dict[str, Any], redactor: Redactor | None,
                   not_measured: dict[str, dict[str, Any]]) -> str:
    stl = bundle.get("modules", {}).get("speed_to_lead")
    if not isinstance(stl, dict):
        return _not_measurable("Speed to lead",
                               not_measured.get("speed_to_lead", {}).get("reason", ""),
                               "leads export")
    if stl.get("median_minutes") is None:
        return _not_measurable(
            "Speed to lead",
            "no lead in this export has both a created_at and a first_response_at value.",
            "leads export with first-response timestamps")
    cards: list[list[Any]] = [
        ["Median first response", f"{stl.get('median_minutes')} minutes"],
             ["90th percentile", f"{stl.get('p90_minutes')} minutes"],
             ["Slowest response", f"{stl.get('max_minutes')} minutes"],
             ["Leads with a recorded response", stl.get("responded_leads")],
             ["Leads with no recorded response",
              len(stl.get("leads_without_response", []) or [])],
             ["Measurement basis", stl.get("basis")]]
    out = [_table(["Measure", "Value"], cards, redactor)]
    no_resp = stl.get("leads_without_response", []) or []
    if no_resp:
        out.append("<h3>Leads with no recorded first response</h3>")
        out.append(_table(["Lead"], [[x] for x in no_resp], redactor))
    unparseable = stl.get("leads_with_unparseable_created_at", []) or []
    if unparseable:
        out.append(_not_measurable("Some leads", "created_at could not be parsed, so those "
                                   "leads were excluded from the timing distribution.",
                                   "clean created_at values"))
    out.append(f'<p class="callout">{_esc(stl.get("caveat"), redactor)}</p>')
    return "\n".join(out)


def _funnel_section(bundle: dict[str, Any], redactor: Redactor | None,
                    not_measured: dict[str, dict[str, Any]]) -> str:
    funnel = bundle.get("modules", {}).get("funnel")
    if not isinstance(funnel, dict):
        return _not_measurable("Tour conversion",
                               not_measured.get("funnel", {}).get("reason", ""),
                               "leads + tours exports")
    counts = funnel.get("counts", {})
    rates = funnel.get("rates", {})
    rows = [[k.replace("_", " "), v] for k, v in counts.items()]
    rate_rows = [[k.replace("_", " "), _pct(v)] for k, v in rates.items()]
    out = ["<h3>Counts</h3>", _table(["Gate", "Count"], rows, redactor),
           "<h3>Rates (definition printed beneath)</h3>",
           _table(["Rate", "Value"], rate_rows, redactor)]
    defs = funnel.get("definitions", {})
    out.append("<ul class='assumptions'>" + "".join(
        f"<li><strong>{_esc(k)}</strong>: {_esc(v, redactor)}</li>" for k, v in defs.items())
        + "</ul>")
    caveats = funnel.get("caveats", [])
    if caveats:
        out.append("<ul class='assumptions'>" + "".join(
            f"<li>{_esc(c, redactor)}</li>" for c in caveats) + "</ul>")
    sources = bundle.get("modules", {}).get("lead_sources")
    if isinstance(sources, dict):
        out.append("<h3>Where the leads came from (normalized labels)</h3>")
        out.append(_table(["Source bucket", "Leads"],
                          [[k, v] for k, v in (sources.get("by_canonical_source") or {}).items()],
                          redactor))
        unmapped = sources.get("unmapped_labels") or {}
        if unmapped:
            out.append("<p class='muted'>Labels the normalizer refused to guess: "
                       + _esc(", ".join(f"{k} ({v})" for k, v in unmapped.items()), redactor)
                       + "</p>")
    return "\n".join(out)


def _collections_churn_section(bundle: dict[str, Any], redactor: Redactor | None,
                               not_measured: dict[str, dict[str, Any]]) -> str:
    out = ["<h3>Collections</h3>"]
    coll = bundle.get("modules", {}).get("collections")
    if isinstance(coll, dict):
        out.append(_table(
            ["Measure", "Value"],
            [["Invoices in the worklist", len(coll.get("queue", []))],
             ["Total outstanding (one-time balances)", _money(coll.get("outstanding_total"))]],
            redactor))
        rows = [[q.get("invoice_id"), q.get("company_id"), _money(q.get("amount")),
                 q.get("days_overdue"), q.get("aging_band"), q.get("payment_history"),
                 q.get("suggested_internal_step"),
                 "; ".join(str(c) for c in q.get("context", [])) or "—"]
                for q in coll.get("queue", [])]
        out.append("<h4>Prioritized internal worklist (oldest first, then largest)</h4>")
        out.append(_table(["Invoice", "Company", "Amount", "Days overdue", "Band",
                           "History", "Suggested internal step", "Context"],
                          rows, redactor))
        out.append("<ul class='assumptions'>" + "".join(
            f"<li>{_esc(r, redactor)}</li>" for r in coll.get("rules", [])) + "</ul>")
    else:
        out.append(_not_measurable("Collections",
                                   not_measured.get("collections", {}).get("reason", ""),
                                   "invoices export"))

    out.append("<h3>Churn and retention</h3>")
    churn = bundle.get("modules", {}).get("churn")
    if isinstance(churn, dict):
        logo = churn.get("logo_churn", {})
        rev = churn.get("revenue_churn", {})
        out.append(_table(["Measure", "Value"], [
            ["Churn window", f"{churn.get('period', {}).get('from')} to "
                             f"{churn.get('period', {}).get('to')} "
                             f"({churn.get('window_days')} days)"],
            ["Memberships in the base at window start", churn.get("base_memberships")],
            ["Memberships that ended inside the window", churn.get("canceled_memberships")],
            ["Logo churn", _pct(logo.get("value"))],
            ["Recurring revenue churn (gross)",
             f"{_pct(rev.get('value'))} — {_money(churn.get('lost_mrr'))} of "
             f"{_money(churn.get('base_mrr'))}"],
        ], redactor))
        out.append(f'<p class="formula"><span class="lbl">Formula</span>'
                   f'{_esc(logo.get("formula"), redactor)}</p>')
        out.append(f'<p class="formula"><span class="lbl">Formula</span>'
                   f'{_esc(rev.get("formula"), redactor)}</p>')
        out.append(f'<p class="callout">{_esc(churn.get("definition"), redactor)}</p>')
        out.append(f'<p class="muted">{_esc(churn.get("caveat"), redactor)}</p>')
        excluded = churn.get("excluded_active_past_end_date") or []
        if excluded:
            out.append('<div class="not-measurable"><strong>Excluded from churn — data '
                       'integrity problem first</strong><p>Memberships marked active past '
                       'their end date: '
                       + _esc(", ".join(str(x) for x in excluded), redactor)
                       + ". They are left out of the churn arithmetic because the export "
                         "does not say whether they were renewed or have ended.</p></div>")
    else:
        out.append(_not_measurable("Churn",
                                   not_measured.get("churn", {}).get("reason", ""),
                                   "memberships export"))

    renewals = bundle.get("modules", {}).get("renewals")
    if isinstance(renewals, dict):
        in_window = renewals.get("agreements_in_window", []) or []
        out.append(f"<h4>Agreements reaching a cliff in the next "
                   f"{_esc(renewals.get('window_days'))} days</h4>")
        out.append(_table(
            ["Membership", "Company", "Cliff", "Days", "Contracted", "List",
             "Evidence (no score attached)"],
            [[a.get("membership_id"), a.get("company_id"), a.get("cliff_date"),
              a.get("days_to_cliff"), _money(a.get("contracted_rate")),
              _money(a.get("list_rate")),
              "; ".join(str(e) for e in a.get("risk_evidence", [])) or "no flags"]
             for a in in_window], redactor,
            empty="No active agreement reaches a recorded cliff inside the window."))
        m2m = renewals.get("month_to_month_active", []) or []
        if m2m:
            out.append("<p class='muted'>Month-to-month agreements (no end date recorded, "
                       "listed separately): "
                       + _esc(", ".join(str(m) for m in m2m), redactor) + "</p>")
        out.append(f'<p class="muted">{_esc(renewals.get("no_score_note"), redactor)}</p>')
    else:
        out.append(_not_measurable("Renewal window",
                                   not_measured.get("renewals", {}).get("reason", ""),
                                   "memberships export"))
    return "\n".join(out)


def _extra_sections(bundle: dict[str, Any], redactor: Redactor | None) -> str:
    """Optional modules that ran because the inputs existed."""
    out = []
    modules = bundle.get("modules", {})
    locations = modules.get("locations")
    if isinstance(locations, dict):
        out.append("<h3>Location scorecard (normalized per sellable workstation)</h3>")
        rows = []
        for loc in locations.get("locations", []):
            rows.append([loc.get("name"), loc.get("sellable_capacity"),
                         _pct(loc.get("workstation_occupancy")),
                         _pct(loc.get("financial_occupancy")),
                         _money(loc.get("revenue_per_sellable_workstation")),
                         loc.get("leads", "—"), _pct(loc.get("lead_to_tour"))
                         if loc.get("lead_to_tour") else "—",
                         loc.get("failed_or_overdue_invoices", "—")])
        out.append(_table(["Location", "Sellable capacity", "Workstation occupancy",
                           "Financial occupancy", "Revenue / workstation", "Leads",
                           "Lead to tour", "Failed/overdue"], rows, redactor))
        out.append(f'<p class="muted">{_esc(locations.get("normalization"), redactor)}</p>')

    recon = modules.get("reconcile")
    if isinstance(recon, dict):
        summary = recon.get("match_summary", {})
        out.append("<h3>CRM and WMS reconciliation</h3>")
        out.append(_table(["Measure", "Value"],
                          [[k.replace("_", " "), v] for k, v in summary.items()], redactor))
        rows = [[f.get("check"), f.get("company_id") or f.get("membership_id") or "—",
                 f.get("detail")] for f in recon.get("findings", [])]
        out.append(_table(["Check", "Record", "Detail"], rows, redactor,
                          empty="No cross-system disagreement found in the supplied exports."))
        queue = recon.get("review_queue", []) or []
        if queue:
            out.append("<p class='muted'>Items awaiting a human decision (never merged "
                       "automatically): "
                       + _esc("; ".join(str(q) for q in queue[:6]), redactor) + "</p>")
        out.append(f'<p class="muted">{_esc(recon.get("id_strategy"), redactor)}</p>')

    vo = modules.get("virtual_office")
    if isinstance(vo, dict):
        out.append("<h3>Virtual office / partner reconciliation</h3>")
        out.append(_table(["Measure", "Value"],
                          [["Active virtual-office memberships", vo.get("active_vo_memberships")],
                           ["Active partner-billed clients", vo.get("active_partner_clients")]],
                          redactor))
        rows = [[f.get("check"), f.get("company_id") or "—", f.get("partner") or "—",
                 f.get("detail")] for f in vo.get("findings", [])]
        out.append(_table(["Check", "Company", "Partner", "Detail"], rows, redactor,
                          empty="No virtual-office mismatch found in the supplied exports."))
        out.append(f'<p class="muted">{_esc(vo.get("caveat"), redactor)}</p>')

    rooms = modules.get("rooms")
    if isinstance(rooms, dict):
        out.append("<h3>Meeting and event room yield</h3>")
        rows = [[r.get("room"), r.get("unit_type"), r.get("bookings"),
                 r.get("booked_hours"), _money(r.get("gross_revenue")),
                 _money(r.get("revenue_per_booked_hour")),
                 r.get("utilization", "not measured (no bookable hours declared)"),
                 r.get("zero_charge_bookings")]
                for r in rooms.get("rooms", [])]
        out.append(_table(["Room", "Type", "Bookings", "Booked hours", "Gross revenue",
                           "Revenue / hour", "Utilization", "Zero-charge bookings"],
                          rows, redactor))
        out.append(f'<p class="muted">{_esc(rooms.get("utilization_note"), redactor)}</p>')

    pricing = modules.get("pricing")
    if isinstance(pricing, dict) and pricing.get("deep_discounts"):
        out.append("<h3>Units priced well below list</h3>")
        rows = [[d.get("unit_id"), d.get("product"), _money(d.get("contracted")),
                 _money(d.get("list")), f"{d.get('discount_pct')}%"]
                for d in pricing.get("deep_discounts", [])]
        out.append(_table(["Unit", "Product", "Contracted", "List", "Below list"],
                          rows, redactor))
        out.append("<ul class='assumptions'>" + "".join(
            f"<li>{_esc(c, redactor)}</li>" for c in pricing.get("caveats", [])) + "</ul>")
    return "\n".join(out) if out else ""


def _methodology(bundle: dict[str, Any], redactor: Redactor | None,
                 command_line: str | None) -> str:
    engagement = bundle.get("engagement", {})
    rows = [
        ["Service", bundle.get("service", {}).get("name")],
        ["Service version", bundle.get("service", {}).get("version")],
        ["Engine version", bundle.get("service", {}).get("engine_version")],
        ["Client", engagement.get("client")],
        ["As-of date (every metric is stated at this date)", engagement.get("as_of")],
        ["Run at", engagement.get("generated_at")],
        ["Churn window", f"{engagement.get('churn_window_days')} days"],
        ["Renewal window", f"{engagement.get('renewal_window_days')} days"],
        ["Staleness threshold", f"{engagement.get('stale_days')} days"],
        ["Deep-discount threshold", f"{engagement.get('discount_pct')}%"],
        ["Forward horizons", ", ".join(str(h) for h in engagement.get("horizons", []))],
        ["Input screening policy", engagement.get("pii_policy")],
        ["Currency", str((bundle.get("context", {}).get("currency") or {})
                         .get("note"))],
        ["Command", command_line or "see the engagement manifest"],
    ]
    out = ["<h3>Engagement parameters</h3>", _table(["Item", "Value"], rows, redactor)]
    out.append("<h3>Formulas used (numerator / denominator / exclusions)</h3>")
    formula_rows = []
    occ = bundle.get("modules", {}).get("occupancy")
    if isinstance(occ, dict):
        for m in occ.get("metrics", []):
            formula_rows.append([m.get("name"), m.get("numerator"), m.get("denominator"),
                                 m.get("formula"), ", ".join(m.get("exclusions", []))])
    out.append(_table(["Metric", "Numerator", "Denominator", "Formula", "Excludes"],
                      formula_rows, redactor))
    findings = bundle.get("findings", [])
    out.append("<h3>Every finding in this engagement</h3>")
    out.append(_table(
        ["#", "Class", "Module", "Finding", "Confidence", "Limitation"],
        [[i, CLASS_LABELS.get(str(f.get("kind")), ("?", ""))[0], f.get("module"),
          f.get("title"), f.get("confidence"), f.get("limitation")]
         for i, f in enumerate(findings, 1)], redactor))
    out.append("<h3>Classification legend</h3>")
    out.append("<ul class='assumptions'>" + "".join(
        f"<li><strong>{_esc(v[0])}</strong> — {_esc(v[1])}</li>"
        for _, v in sorted(CLASS_LABELS.items())) + "</ul>")
    out.append("<h3>Input fingerprints (reproducibility)</h3>")
    out.append("<p class='muted'>Content fingerprints are line-ending independent, so the "
               "same exports produce this report on any operating system.</p>")
    out.append(_table(["File", "Content fingerprint"],
                      [[k, v] for k, v in (bundle.get("inputs", {}).get("fingerprints")
                                           or {}).items()], redactor))
    opp = bundle.get("opportunities", {})
    out.append("<h3>How opportunities were ranked</h3>")
    out.append(f'<p>{_esc(opp.get("ranking_rule"), redactor)}</p>')
    out.append(f'<p>{_esc(opp.get("amount_policy"), redactor)}</p>')
    return "\n".join(out)


def _limitations_section(bundle: dict[str, Any], redactor: Redactor | None) -> str:
    grouped: dict[str, list[str]] = {}
    for item in bundle.get("limitations", []):
        grouped.setdefault(str(item.get("type")), []).append(str(item.get("detail")))
    out = []
    if not grouped.get("missing_input"):
        out.append('<p class="callout">Every diagnostic whose inputs exist ran in this '
                   "engagement: no module was skipped for missing data. Anything the "
                   "supplied exports cannot answer is labelled NOT MEASURABLE inside the "
                   "relevant section rather than estimated.</p>")
    order = ["missing_input", "unusable_file", "ambiguous_role", "superseded_file",
             "unidentified_file", "unanalysed_file", "context_only_file",
             "preflight_blocked", "preflight_warning", "engine_limit", "review_gate"]
    for key in order + [k for k in sorted(grouped) if k not in order]:
        items = grouped.get(key)
        if not items:
            continue
        out.append(f"<h3>{_esc(LIMITATION_LABELS.get(key, key))}</h3>")
        out.append("<ul class='assumptions'>" + "".join(
            f"<li>{_esc(i, redactor)}</li>" for i in items) + "</ul>")
    return "\n".join(out)


def _findings_for(bundle: dict[str, Any], redactor: Redactor | None,
                  *modules: str) -> str:
    """Render the finding records belonging to one report section."""
    wanted = set(modules)
    picked = [f for f in bundle.get("findings", []) if str(f.get("module")) in wanted]
    if not picked:
        return ""
    blocks = "".join(_finding_block(f, redactor, i)
                     for i, f in enumerate(picked, 1))
    return '<h3>Findings</h3><div class="findings">' + blocks + "</div>"


def _executive_summary(bundle: dict[str, Any], redactor: Redactor | None) -> str:
    engagement = bundle.get("engagement", {})
    modules = bundle.get("modules", {})
    opp = bundle.get("opportunities", {})
    out = [f'<p class="lede">Prepared for <strong>{_esc(engagement.get("client"), redactor)}'
           f'</strong> at <strong>{_esc(engagement.get("as_of"))}</strong>, from the exports '
           "supplied for this engagement. Every number below is in the sections that follow, "
           "with its formula and its limitation attached.</p>"]

    bullets: list[str] = []
    occ = modules.get("occupancy")
    if isinstance(occ, dict):
        metrics = {str(m["name"]): m for m in occ.get("metrics", [])}
        bullets.append(
            "Occupancy reads three different ways: "
            f"<strong>{_pct(metrics.get('office_occupancy', {}).get('value'))}</strong> by "
            "office count, "
            f"<strong>{_pct(metrics.get('workstation_occupancy', {}).get('value'))}</strong> "
            "by workstation, and "
            f"<strong>{_pct(metrics.get('financial_occupancy', {}).get('value'))}</strong> by "
            "contracted revenue against list potential.")
    leak = modules.get("leakage")
    if isinstance(leak, dict):
        by_check = {str(f["check"]): f for f in leak.get("findings", [])}
        unbilled = by_check.get("active_memberships_without_recent_invoice")
        if unbilled:
            bullets.append(
                f"<strong>{_money(unbilled['monthly_amount_at_risk'])}</strong> per month of "
                f"recurring rate sits on {unbilled['count']} active membership(s) with no "
                "invoice in the last 45 days.")
        failed = by_check.get("failed_or_overdue_invoices")
        if failed:
            bullets.append(
                f"<strong>{_money(failed['amount_outstanding'])}</strong> in already failed or "
                f"overdue balances across {failed['count']} invoice(s).")
        blocked = by_check.get("out_of_service_inventory")
        if blocked:
            bullets.append(
                f"<strong>{_money(blocked['monthly_list_value_blocked'])}</strong> per month of "
                f"list value is idle on {blocked['count']} out-of-service unit(s).")
        unfollowed = by_check.get("unfollowed_leads")
        if unfollowed:
            bullets.append(f"<strong>{unfollowed['count']}</strong> lead(s) never received a "
                           "recorded first response.")
        ghost = by_check.get("completed_tours_without_next_action")
        if ghost:
            bullets.append(f"<strong>{ghost['count']}</strong> completed tour(s) have no "
                           "recorded next step.")
    forecast = modules.get("forecast")
    if isinstance(forecast, dict):
        horizons = {int(h["horizon_days"]): h for h in forecast.get("horizons", [])}
        h90 = horizons.get(90) or (list(horizons.values())[-1] if horizons else None)
        if h90:
            dep = [str(x) for x in h90.get("departures", [])]
            bullets.append(
                f"Contracted occupancy is "
                f"<strong>{_pct(h90.get('contracted_occupancy'))}</strong> at "
                f"{h90['horizon_days']} days"
                + (f", with {len(dep)} recorded departure(s) "
                   f"({', '.join(_esc(d, redactor) for d in dep)})" if dep else "")
                + ".")
    if bullets:
        out.append("<ul class='summary'>" + "".join(f"<li>{b}</li>" for b in bullets)
                   + "</ul>")
    out.append('<p class="callout"><strong>No causality is claimed anywhere in this '
               "report.</strong> Every statement is labelled FACT, CALCULATION, INFERENCE, "
               "or RECOMMENDATION. Where two numbers move together, that is reported as a "
               "coincidence in the data, not as a cause.</p>")

    top = opp.get("top", [])
    if top:
        rows = []
        for o in top:
            raw = (o.get("monthly_recurring") if o.get("monthly_recurring") is not None
                   else o.get("one_time"))
            amount = _money(raw) if raw is not None else "not quantified"
            rows.append([o.get("rank"), o.get("title"), amount, o.get("amount_unit"),
                         o.get("owner"), o.get("confidence")])
        out.append("<h4>The five things to do first</h4>")
        out.append(_table(["#", "Opportunity", "Measured amount", "Amount basis", "Owner",
                           "Confidence"], rows, redactor))
    return "\n".join(out)


def render_review_checklist(bundle: dict[str, Any]) -> str:
    """The human review gate, as a file the reviewer can tick through.

    Deliberately blunt: a draft that skips this list is the one that embarrasses
    the engagement.
    """
    engagement = bundle.get("engagement", {})
    quality = bundle.get("quality", {})
    totals = quality.get("totals", {})
    ambiguous = bundle.get("inputs", {}).get("ambiguities", [])
    not_measured = bundle.get("not_measured", [])
    weak = [f"{f['source']} -> {f['role']} ({int(float(f['entity_confidence']) * 100)}%)"
            for f in bundle.get("inputs", {}).get("files", [])
            if f.get("entity") and float(str(f.get("entity_confidence", 0))) < 1.0]
    lines = [
        "# Review checklist — DRAFT, review required",
        "",
        f"**Client:** {engagement.get('client')}  ",
        f"**As of:** {engagement.get('as_of')}  ",
        f"**Generated:** {engagement.get('generated_at')}  ",
        "**Report:** report.html (draft — not for delivery until finalized)",
        "",
        "This report is not sent anywhere by the tool. A human releases it.",
        "",
        "## Before you read the numbers",
        "",
        "- [ ] Confirm the client name and as-of date above are the period you agreed.",
        f"- [ ] Confirm the exports supplied are complete for that period "
        f"({totals.get('files_checked', 0)} export(s) were analysed).",
        f"- [ ] Resolve the {totals.get('errors', 0)} error-severity data-quality "
        "finding(s) or decide to disclose them in the report.",
    ]
    if ambiguous:
        lines.append(f"- [ ] Resolve {len(ambiguous)} ambiguous file-role mapping(s) "
                     "(the affected diagnostics are NOT MEASURABLE until you do).")
    if weak:
        lines.append("- [ ] Confirm the identification of every file matched below 100%: "
                     + "; ".join(weak))
    lines += [
        "",
        "## Reading the numbers",
        "",
        "- [ ] Re-check the three occupancy numbers against the operator's WMS screen.",
        "- [ ] Re-check every quantified amount against the records listed beneath it.",
        "- [ ] Confirm each of the two occupancy spreads is explained by the named flags, "
        "not by a story.",
        "- [ ] Spot-check two findings straight from the raw export.",
        "- [ ] Confirm you agree with the ranking of the top opportunities "
        "(the ranking rule is printed in the methodology section).",
        "- [ ] Re-read every INFERENCE and RECOMMENDATION and confirm you are willing to "
        "stand behind it in the client conversation.",
        "- [ ] Confirm every INCONCLUSIVE item is reported as NOT MEASURABLE rather than "
        "guessed.",
        "",
        "## Data handling",
        "",
        "- [ ] Search the report for `@` and phone-shaped strings: no identifier may appear.",
        "- [ ] Confirm no client export was copied into the report directory.",
        "- [ ] Confirm the review checklist for data retention in your engagement "
        "agreement covers these files (delete or archive per policy).",
        "",
        "## Release",
        "",
        "- [ ] Record your notes and any edits the report needs.",
        "- [ ] Run `opencoworking health-check-finalize --engagement <dir> "
        "--reviewer \"<your name>\"` to produce report.final.html.",
        "- [ ] Confirm the finalized report still carries the data limitations section.",
        "- [ ] Send the report to the client only through your own agreed channel.",
        "",
        "## What this engagement cannot tell the client",
        "",
    ]
    for item in not_measured:
        lines.append(f"- NOT MEASURABLE — {item['module']}: {item['reason']}")
    lines += [
        "- No market benchmark, no comparison with other operators, no revenue "
        "prediction, no legal or tax advice.",
        "",
        "Generated by the open-source OpenCoworking engine. Draft until a human "
        "finalizes it.",
        "",
    ]
    return "\n".join(lines)


def write_engagement(output_dir: str | Path, bundle: dict[str, Any], *,
                     command_line: str, force: bool = False) -> dict[str, str]:
    """Write the draft engagement artifacts. Never writes client data out."""
    out = Path(output_dir)
    artifacts = {
        "report": out / "report.html",
        "bundle": out / "bundle.json",
        "preflight": out / "preflight.json",
        "checklist": out / "REVIEW_CHECKLIST.md",
        "manifest": out / "engagement.json",
    }
    existing = [str(p) for p in artifacts.values() if p.exists()]
    if existing and not force:
        raise FileExistsError(
            "engagement output already exists; pass --force to regenerate: "
            + ", ".join(existing))
    out.mkdir(parents=True, exist_ok=True)
    (artifacts["report"]).write_text(
        render_health_check(bundle, command_line=command_line), encoding="utf-8")
    (artifacts["checklist"]).write_text(render_review_checklist(bundle), encoding="utf-8")
    (artifacts["preflight"]).write_text(
        json.dumps(bundle.get("preflight", {}), indent=2, ensure_ascii=False, default=str),
        encoding="utf-8")
    manifest = {
        "service": bundle.get("service"),
        "engagement": bundle.get("engagement"),
        "command": command_line,
        "status": "draft",
        "review_required": True,
        "inputs": {k: v for k, v in bundle.get("inputs", {}).items()
                   if k != "files"},
        "input_files": [{"source": f["source"], "role": f["role"], "rows": f["rows"],
                         "entity_confidence": f["entity_confidence"]}
                        for f in bundle.get("inputs", {}).get("files", [])],
        "metrics": bundle.get("metrics"),
        "findings": [{"id": f["id"], "kind": f["kind"], "module": f["module"],
                      "title": f["title"], "confidence": f["confidence"]}
                     for f in bundle.get("findings", [])],
        "not_measured": bundle.get("not_measured"),
        "artifacts": {k: v.name for k, v in artifacts.items()},
        "data_handling": {
            "client_exports_copied": False,
            "report_contains_personal_identifiers": False,
            "identifiers_redacted": (bundle.get("data_handling") or {})
            .get("identifiers_redacted", 0),
            "note": "Only aggregate metrics, record identifiers, and column names are "
                    "written to this directory. Raw export rows are never copied, and every "
                    "string is passed through the engine's deterministic redactor.",
        },
    }
    (artifacts["manifest"]).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    (artifacts["bundle"]).write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return {k: str(v) for k, v in artifacts.items()}


def finalize_engagement(output_dir: str | Path, *, reviewer: str, notes: str | None,
                        finalized_at: str, force: bool = False) -> dict[str, str]:
    """Produce the released report from a reviewed draft. Nothing is sent."""
    out = Path(output_dir)
    bundle_path = out / "bundle.json"
    if not bundle_path.is_file():
        raise FileNotFoundError(f"no bundle.json in {out}; run health-check first")
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    report = out / "report.final.html"
    record = out / "finalized.json"
    if (report.exists() or record.exists()) and not force:
        raise FileExistsError(
            f"{out} is already finalized; pass --force to re-finalize")
    report.write_text(
        render_health_check(bundle, finalized=True, reviewer=reviewer, notes=notes,
                            finalized_at=finalized_at), encoding="utf-8")
    record.write_text(json.dumps({
        "status": "finalized",
        "review_required": False,
        "reviewer": reviewer,
        "reviewer_notes": notes,
        "finalized_at": finalized_at,
        "final_report": report.name,
        "draft_report": "report.html",
        "sent_to_client": False,
        "note": "The tool does not deliver reports. Sending to the client is a human, "
                "manual step outside this tool.",
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"report": str(report), "record": str(record)}


def _styles() -> str:
    return """
:root{--ink:#16202e;--muted:#5b6779;--line:#d9dfe8;--accent:#0f4c81;--accent-soft:#eaf1f8;
--pos:#1c6b4a;--warn:#8a5a00;--bad:#9b2c2c;--chip:#f4f6f9;}
*{box-sizing:border-box}
body{margin:0;padding:32px 40px 64px;color:var(--ink);
font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
background:#fff;max-width:1080px;margin-inline:auto}
h1{font-size:27px;line-height:1.25;margin:0 0 4px}
h2{font-size:20px;margin:38px 0 10px;padding-bottom:6px;border-bottom:2px solid var(--accent);
color:var(--accent)}
h3{font-size:16px;margin:24px 0 8px}
h4{font-size:14px;margin:18px 0 6px;text-transform:uppercase;letter-spacing:.04em;
color:var(--muted)}
p{margin:8px 0}
.sub{color:var(--muted);margin-top:0}
.banner{padding:14px 18px;border-radius:8px;margin:18px 0 26px;font-weight:600;
letter-spacing:.02em;border:2px solid}
.banner-draft{background:#fff4e5;border-color:#d98324;color:#7a4300}
.banner-final{background:#eaf6ef;border-color:#2f7d54;color:#134a30}
.banner ul{margin:8px 0 0;font-weight:400}
.tag{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.06em;
padding:2px 7px;border-radius:999px;text-transform:uppercase}
.tag-fact{background:#e8eef5;color:#23486b}
.tag-calculation{background:#e6f0ea;color:#1c6b4a}
.tag-inference{background:#fdf0dc;color:#8a5a00}
.tag-recommendation{background:#f0e9f7;color:#5b3a86}
.conf{font-size:11.5px;padding:2px 8px;border-radius:999px;border:1px solid var(--line)}
.conf-high{background:#eaf6ef;color:var(--pos);border-color:#bcdcc9}
.conf-medium{background:#fdf7e8;color:var(--warn);border-color:#e8d9a8}
.conf-low{background:#fbeded;color:var(--bad);border-color:#e3bcbc}
.module{font-size:11.5px;color:var(--muted)}
.count{font-size:11.5px;color:var(--muted)}
.finding{border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:8px;
padding:14px 18px;margin:14px 0;break-inside:avoid;background:#fff}
.finding-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
.finding-head h3{margin:0}
.tags{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;align-items:center}
.statement{margin:8px 0 4px}
dl.contract{display:grid;grid-template-columns:132px 1fr;gap:2px 14px;margin:10px 0 0;
font-size:13.5px}
dl.contract dt{color:var(--muted);font-weight:600}
dl.contract dd{margin:0}
.records,.muted{font-size:12.5px;color:var(--muted)}
.lbl{display:inline-block;min-width:58px;color:var(--muted);font-weight:600;
text-transform:uppercase;font-size:10.5px;letter-spacing:.05em}
table.grid{width:100%;border-collapse:collapse;margin:10px 0 16px;font-size:13px;
break-inside:avoid}
table.grid th{background:var(--accent-soft);text-align:left;padding:7px 9px;
border:1px solid var(--line);font-size:12px;text-transform:uppercase;letter-spacing:.03em;
color:#26506f}
table.grid td{padding:7px 9px;border:1px solid var(--line);vertical-align:top}
table.grid tbody tr:nth-child(even){background:#fafbfd}
.not-measurable{border:1px dashed #b48b3c;background:#fffaf0;border-radius:8px;
padding:12px 16px;margin:14px 0;break-inside:avoid}
.not-measurable strong{color:#8a5a00}
.not-measurable p{margin:4px 0}
.not-measurable .needs{font-size:12.5px;color:var(--muted)}
.callout{background:var(--chip);border-left:3px solid var(--accent);padding:10px 14px;
border-radius:6px;font-size:13.5px}
.callout-warn{background:#fff4e5;border-left-color:#d98324}
.metric-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;
margin:14px 0}
.metric-card{border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:8px;
padding:12px 14px;break-inside:avoid}
.metric-undefined{border-top-color:#b48b3c}
.metric-name{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.metric-value{font-size:26px;font-weight:700;margin:2px 0}
.metric-frac{font-size:12.5px;color:var(--muted)}
.formula{font-size:12.5px;color:#33445c;background:#f7f9fc;border-radius:6px;padding:6px 9px}
.exclusions{font-size:12px;color:var(--muted);margin:6px 0 0}
ul.warnlist{margin:6px 0 0;padding-left:18px;font-size:12.5px;color:var(--warn)}
ul.summary{margin:10px 0;padding-left:20px}
ul.summary li{margin:6px 0}
ul.assumptions{margin:8px 0;padding-left:20px;font-size:13px;color:#33445c}
ul.findings-list{margin:8px 0;padding-left:20px;font-size:13px}
.opportunity{border:1px solid var(--line);border-radius:10px;margin:16px 0;overflow:hidden;
break-inside:avoid}
.opp-head{display:flex;gap:12px;align-items:center;background:var(--accent-soft);
padding:10px 14px}
.opp-head h3{margin:0;font-size:15.5px}
.rank{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;
border-radius:50%;background:var(--accent);color:#fff;font-weight:700;font-size:13px;
flex:0 0 auto}
.opp-body{padding:12px 14px}
.opp-amount{margin-bottom:6px}
.amount{font-size:22px;font-weight:700;color:var(--pos)}
.amount-soft{font-size:15px;color:var(--muted);font-weight:600}
.amount-unit{font-size:12.5px;color:var(--muted);margin-left:8px}
.lede{font-size:15.5px}
footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);font-size:12.5px;
color:var(--muted)}
.signature{border:1px solid var(--line);border-radius:8px;padding:12px 16px;margin:16px 0;
break-inside:avoid}
@page{size:A4;margin:14mm}
@media print{
  body{padding:0;font-size:10.5pt;max-width:none}
  h1{font-size:19pt}h2{font-size:14pt}h3{font-size:12pt}
  h2,h3,h4{break-after:avoid}
  .finding,.metric-card,.opportunity,.not-measurable,.signature,table.grid{break-inside:avoid}
  a{color:inherit;text-decoration:none}
  .no-print{display:none}
}
"""


def render_health_check(bundle: dict[str, Any], *, finalized: bool = False,
                        reviewer: str | None = None, finalized_at: str | None = None,
                        notes: str | None = None,
                        command_line: str | None = None) -> str:
    """Render the bundle as one self-contained HTML document."""
    global _CURRENCY_SYMBOL
    redactor = Redactor(salt="opencoworking-health-check")
    _CURRENCY_SYMBOL = str((bundle.get("context", {}).get("currency") or {})
                           .get("symbol") or "")
    engagement = bundle.get("engagement", {})
    service = bundle.get("service", {})
    title = f"{service.get('name')} — {_esc(engagement.get('client'), redactor)}"
    not_measured = {str(m["module"]): m for m in bundle.get("not_measured", [])}

    if finalized:
        banner = (
            '<div class="banner banner-final">REVIEWED &amp; FINALIZED'
            f'<ul><li>Reviewed by: {_esc(reviewer)}</li>'
            f'<li>Finalized at: {_esc(finalized_at)}</li>'
            '<li>This report was read and released by a human. The tool never sends '
            'anything to anyone.</li></ul></div>')
        signature = f"""
<section class="signature">
  <h3>Reviewer sign-off</h3>
  <p><strong>{_esc(reviewer)}</strong> reviewed the draft against the data limitations and
  release checklist and released this report at {_esc(finalized_at)}.</p>
  {f'<p><span class="lbl">Reviewer notes</span>{_esc(notes)}</p>' if notes else ''}
</section>"""
    else:
        banner = (
            '<div class="banner banner-draft">DRAFT REPORT — REVIEW REQUIRED'
            '<ul>'
            '<li>No number in this report has been reviewed by a human yet.</li>'
            '<li>Check the Data quality and Data limitations sections before using any '
            'figure.</li>'
            '<li>Run <code>opencoworking health-check-finalize</code> after review to '
            'produce the released version.</li>'
            '<li>The tool does not email, publish, or send this report to anyone.</li>'
            '</ul></div>')
        signature = ""

    sections = [
        ("Executive summary", _executive_summary(bundle, redactor)),
        ("Data quality and data handling",
         _preflight_block(bundle, redactor) + _data_handling_block(bundle, redactor)
         + _quality_block(bundle, redactor)
         + _findings_for(bundle, redactor, "data quality")),
        ("Occupancy", _occupancy_section(bundle, redactor, not_measured)
         + _findings_for(bundle, redactor, "occupancy")),
        ("Revenue leakage", _leakage_section(bundle, redactor, not_measured)
         + _findings_for(bundle, redactor, "revenue leakage")),
        ("Sales pipeline", _pipeline_section(bundle, redactor, not_measured)
         + _findings_for(bundle, redactor, "sales pipeline")),
        ("Speed to lead", _speed_section(bundle, redactor, not_measured)
         + _findings_for(bundle, redactor, "speed to lead")),
        ("Tour conversion", _funnel_section(bundle, redactor, not_measured)
         + _findings_for(bundle, redactor, "tour conversion")),
        ("Collections and churn", _collections_churn_section(bundle, redactor, not_measured)
         + _findings_for(bundle, redactor, "collections", "churn")),
    ]
    extra = _extra_sections(bundle, redactor)
    if extra:
        sections.append(("Portfolio detail (locations, systems, rooms, pricing)",
                         extra + _findings_for(bundle, redactor, "rooms")))
    top = bundle.get("opportunities", {}).get("top", [])
    sections.append(("Top 5 opportunities",
                     "".join(_opportunity_block(o, redactor) for o in top)
                     or '<p class="muted">No opportunity was measurable from the supplied '
                        'exports.</p>'))
    plan = bundle.get("action_plan", {})
    plan_rows = []
    for key, items in plan.get("buckets", {}).items():
        for item in items:
            plan_rows.append([plan.get("labels", {}).get(key, key), item.get("action"),
                              item.get("owner"), item.get("first_step"),
                              item.get("confidence")])
    sections.append(("90-day action plan",
                     _table(["Window", "Action", "Owner", "First step", "Confidence"],
                            plan_rows, redactor,
                            empty="No actions: nothing was measurable.")
                     + f'<p class="muted">{_esc(plan.get("note"), redactor)}</p>'))
    sections.append(("Methodology and formulas", _methodology(bundle, redactor, command_line)))
    sections.append(("Data limitations", _limitations_section(bundle, redactor)))

    body = "\n".join(
        f'<section class="report-section" id="s{i}"><h2>{i}. {_esc(name)}</h2>{content}'
        "</section>"
        for i, (name, content) in enumerate(sections, 1))

    toc = "".join(f'<li><a href="#s{i}">{_esc(name)}</a></li>'
                  for i, (name, _) in enumerate(sections, 1))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="generator" content="{_esc(service.get('name'))} {_esc(service.get('version'))}">
<meta name="robots" content="noindex,nofollow">
<style>{_styles()}</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <p class="sub">Coworking revenue and operations review · as of
     {_esc(engagement.get('as_of'))} · generated {_esc(engagement.get('generated_at'))}</p>
</header>
{banner}
<nav class="no-print" aria-label="Contents">
  <h4>Contents</h4>
  <ol>{toc}</ol>
</nav>
{body}
{signature}
<footer>
  <p><strong>{_esc(service.get('name'))}</strong> v{_esc(service.get('version'))}, engine
  {_esc(service.get('engine_version'))}. Produced by the open-source OpenCoworking engine —
  the same deterministic tools the operator can run themselves, with no vendor lock-in.</p>
  <p>Read-only analysis: this document was generated from exports supplied by the operator.
  No client export was copied into the report directory, no personal identifier is printed,
  and nothing was sent to anyone. Figures describe the supplied exports only; they are not
  market benchmarks, and no revenue or retention outcome is promised.</p>
</footer>
</body>
</html>
"""
