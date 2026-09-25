# Coworking Revenue & Operations Health Check

**A repeatable, human-reviewed paid engagement run on an operator's own
exports — with the open-source engine underneath it.**

This page is the commercial handoff: what the client supplies, what is
delivered, what is deliberately *not* claimed, and how to run the engagement
twice in a row without improvising. It is written for the consultant or
operator delivering the engagement, not for the client.

Nothing here is proprietary. The analysis runs on the same deterministic,
Apache-2.0 tooling in this repository, which the client is free to run
themselves — that is the point. What you are selling is the scoping, the
analysis, the review, and the recommendations, not a locked box.

```bash
opencoworking health-check \
  --input ./engagements/<client-slug>/client-export \
  --output ./engagements/<client-slug>/reports/2026-07 \
  --client "Client Name" \
  --as-of 2026-07-01
```

Then, after reading `REVIEW_CHECKLIST.md` and correcting anything the draft
gets wrong:

```bash
opencoworking health-check-finalize \
  --engagement ./engagements/<client-slug>/reports/2026-07 \
  --reviewer "Your Name" \
  --notes "What you checked and what you changed"
```

The output is `report.html` (draft), reviewed into `report.final.html` — a
print-ready document with `@page` A4 rules, so "print to PDF" gives a client
deliverable without a second tool.

A worked, fully synthetic example of every artifact:
[`examples/health-check-engagement/`](../examples/health-check-engagement/README.md).

---

## 1. What the client supplies

Exports only. No credentials, no API keys, no database access, no screen
sharing is required for the core engagement.

**Minimum viable engagement** (produces occupancy, revenue leakage, and the
data-quality section):

- inventory / units export
- memberships / contracts / subscriptions export

**Full engagement** (adds sales, funnel, collections, churn, partner, and
room analysis): the two above plus any of

- leads / enquiries (with a first-response timestamp)
- deals / opportunities
- tours / bookings-of-tours
- invoices and payments
- companies / accounts and contacts
- locations / sites
- room or event bookings
- virtual-office partner statements

Plus two facts only the operator knows:

- the **as-of date** (the date the numbers describe — usually the month end),
  and
- whether the exports cover **the same period** (a CRM covering the quarter
  and a WMS covering one month will mix periods in funnel and churn counts;
  the report says so, but the answers get better when they align).

Anything not supplied is reported as **NOT MEASURABLE** with the reason. That
is a feature: an engagement with a short data-limitations list is worth more
than one with an invented number.

## 2. Accepted export types

| Format | Status |
|---|---|
| CSV / TSV / TXT (comma, semicolon, tab, or pipe delimited; UTF-8 or cp1252; BOM tolerated) | **works** |
| XLSX (first or named sheet) | **works** with the `xlsx` extra installed: `pip install "opencoworking[xlsx]"` |
| PDF, DOCX, XLS (legacy), archives, images | **not analysed** — listed in the report for human review |
| Live API / database connection | out of scope for this engagement |

Column names do not have to match anything: the engine identifies each file
from its **column signatures** (never from the filename), then renames the
headers it recognises onto its canonical schema — and prints every rename, every
header it could not place, and every ambiguity it refused to guess.

If two files plausibly claim the same role, or two columns claim the same
meaning, the engine uses neither and says so; you resolve it in seconds with
`--map deals.csv=deals`. Vendor field-mapping guides in
[`adapters/`](../adapters/README.md) are the reference for the aliases.

## 3. Delivery process

1. **Scope call (15 min).** Confirm the two facts above, the delivery date, and
   which systems will be exported. Ask for exports, not screenshots.
2. **Receive.** Drop the exports into `engagements/<client-slug>/client-export/`.
   Do not paste them into email, chat, or a ticket.
3. **Screen.** The run's preflight refuses credentials, key material,
   database dumps, payment-card numbers, government IDs, and bank details
   before any analysis happens, and tells you what it refused. It flags — but
   does not block on — identifier columns, so you can decide with the client
   whether they needed to send them at all.
4. **Run** the `health-check` command. Two to three seconds for a normal
   operator's exports. Nothing is uploaded; there are no network calls.
5. **Review** against `REVIEW_CHECKLIST.md`. This step is not optional and is
   not automatable: the report is labelled **DRAFT REPORT — REVIEW REQUIRED**
   until a human releases it. Correct the draft, then re-run if the data was
   wrong, or note the correction in the reviewer notes.
6. **Finalize** with `health-check-finalize`. It records who reviewed the
   report, when, and with what notes.
7. **Deliver** the report through your own agreed channel, and hold the walkthrough
   call (45–60 min). Walk the top opportunities in ranked order; every one has
   its evidence, its confidence, and its limitation printed next to it, so
   objections are answered inside the document.
8. **Retain or delete** the raw export folder per the engagement agreement. The
   report directory keeps the numbers; it never contains raw member rows.

Typical effort: 2 hours of analyst time for a two-location operator with clean
exports; 4–6 hours when the mapping needs resolving and the findings need
verifying against the operator's own screens.

## 4. What the report contains

Thirteen sections, in fixed order, each of which either carries its own numbers
or states NOT MEASURABLE with the reason:

| Section | Source modules |
|---|---|
| Executive summary | all of the below, plus the labelled top 5 |
| Data quality and data handling | WMS/CRM export analysis, data dictionary mapping, preflight screening |
| Occupancy | occupancy/revenue dashboard (three occupancy variants + named distortion flags), contracted forward view |
| Revenue leakage | leakage audit (billing gaps, process gaps, idle inventory, unstarted agreements) |
| Sales pipeline | pipeline health (staleness, ownership, next actions, duplicates) |
| Speed to lead | speed-to-lead auditor (business-minute first responses, untouched leads) |
| Tour conversion | lead-to-tour diagnostic / funnel, source normalization, ghosted-tour counts |
| Collections and churn | collections prioritizer, churn window, renewal/retention scan |
| Portfolio detail | multi-location benchmark, CRM↔WMS reconciliation, virtual-office reconciliation, room yield, discount audit |
| Top 5 opportunities | the ranked, quantified shortlist |
| 90-day action plan | the same opportunities, sequenced into 0–14 / 15–45 / 46–90 days |
| Methodology and formulas | every numerator, denominator, exclusion, threshold, and input fingerprint |
| Data limitations | missing inputs, unusable files, ambiguities, and the engine's hard limits |

Every finding is labelled **FACT**, **CALCULATION**, **INFERENCE**, or
**RECOMMENDATION**, and every major finding states four things: the data used,
the calculation, the confidence with its basis, and the limitation. Amounts are
kept on separate bases — recurring rate at risk, one-time balance, revenue that
already left, erosion of list value — and are **never summed into one headline
number**.

## 5. What cannot be inferred (say this out loud on the call)

- **No market context.** No industry benchmarks, no "spaces like yours", no
  market rents. Every number describes the client's own exports.
- **No attendance.** Occupancy is contracted inventory consumption, not
  physical presence; nobody is in the exports, and no access-log data is used.
- **No causality.** Two numbers moving together in one month is reported as a
  coincidence in the data. Where a cause would be useful, it is labelled
  INFERENCE with the reasoning shown, or left as an open question.
- **No prediction.** The forward view is contracted arithmetic: signed
  agreements, recorded end dates, signed pending move-ins. No renewal
  probability, no pipeline weighting.
- **No revenue guarantee.** Findings are what the exports support; the leak
  figures are potential, and each one carries the caveat that says so.
- **Not legal, tax, financial, or compliance advice.** Escalations and disputes
  are routed to the client's professionals.
- **Nothing about what happened outside the exports.** Calls, DMs, verbal
  promises, off-system agreements, and support history are invisible; the
  report says the counts are of what the systems hold.
- **Nothing is sent, charged, or changed.** Every module is read-only. The
  collections worklist is an internal to-do list with a suggested tone, never a
  message to a member.

## 6. Privacy expectations

- **Client data stays local.** No network calls, no telemetry, no uploads, no
  account. The engagement runs on the machine holding the exports.
- **One directory per client**, git-ignored: [`engagements/README.md`](../engagements/README.md).
  Client exports are never committed, attached to issues, or used as fixtures.
- **Screening before analysis.** Credentials, key material, database dumps,
  card numbers, government IDs, and bank details are refused outright, and the
  refusal is recorded. `--pii-policy strict` additionally refuses files whose
  columns carry identifiers; `--allow-unsafe` can override a block and the
  override is stamped into the manifest and the report.
- **No identifiers in the deliverable.** Findings cite record identifiers
  (`M-011`, `INV-1004`, `OF-104`), not people. Contact fields are used for
  their metrics, never printed, and any value that is printed passes through the
  engine's deterministic redactor.
- **No raw rows in the report directory.** The report, the manifest, and the
  bundle carry metrics, classifications, and record IDs — never export rows.
- **Not a guarantee.** Pattern-based screening reduces risk; it does not certify
  a folder is clean. The report says so, and the checklist asks you to confirm
  it yourself.
- **State the retention rule in your engagement agreement.** The tool has no
  opinion on how long the client's exports may sit on your disk.

## 7. Review checklist (the human gate)

Shipped into every engagement as `REVIEW_CHECKLIST.md`; the short version:

- Confirm the client name, as-of date, and period coverage match the agreement.
- Read the Data quality section: resolve or disclose every error-severity
  finding, and confirm the identification of any file matched below 100 %.
- Resolve ambiguous mappings, or confirm the affected section is reported as
  NOT MEASURABLE.
- Re-check the three occupancy numbers against the operator's own screen.
- Re-check every quantified amount against the records listed beneath it, and
  spot-check two findings straight from the raw export.
- Confirm each INFERENCE and RECOMMENDATION is one you will stand behind in the
  room, and that nothing labelled NOT MEASURABLE is implied to be measured.
- Search the report for `@` and phone-shaped strings before it leaves your desk.
- Record your notes and the corrections, then finalize.

A report that ships without this pass is the only way this engagement fails.

## 8. Follow-on engagements (natural next steps)

The health check is deliberately an entry point, not the whole product. The
report's own findings create the follow-ons, each of which is an existing skill
in this repository used in depth:

| Follow-on | Triggered by | Skill / tool |
|---|---|---|
| Renewal- and retention-season programme | renewal cliffs, notice given, renewal-shock evidence | `coworking-renewal-preparation`, `coworking-churn-risk-review`, `opencoworking renewals` |
| Lead-to-lease rebuild | uncontacted leads, response tail, ghosted tours | `coworking-speed-to-lead-auditor`, `coworking-tour-follow-up`, `coworking-post-tour-ghost-recovery` |
| Billing-gap cleanup | unbilled active memberships, expired-but-active contracts | `coworking-collections-prioritizer`, `coworking-revenue-leakage-audit` |
| `CRM ↔ WMS` reconciliation project | conflicting values, unstarted won deals, ghost units | `coworking-crm-wms-reconciliation` |
| Virtual-office / partner audit | partner-client and double-billing findings | `coworking-virtual-office-reconciliation` |
| Pricing and discount reset | deep discounts, missing list prices | `coworking-discount-pricing-audit` |
| Data-dictionary and reporting fix | ambiguous mappings, unmapped headers, mixed date formats | `coworking-data-dictionary`, `coworking-system-adapter-builder` |
| Monthly operating rhythm | the owner wanting this every month | `coworking-monthly-owner-report`, `opencoworking brief` |

Pricing, packaging, and proposals are business decisions outside this
repository. The technical advice this document can give: sell the review and
the walkthrough, keep the tool free for the client to run, and let the
follow-on work be scoped from what the report's own findings justify.

## 9. Honest limitations of the engagement itself

- The engine's maturity labels are in the [README](../README.md) and
  [`catalog/skills.yaml`](../catalog/skills.yaml): `stable` means complete,
  tested, and reviewed; `beta` means complete and engine-tested but not yet
  operator-proven. Do not present a beta skill's area with more confidence than
  the report prints.
- No vendor system has been live- or sandbox-tested. The engine works on
  exports; the mapping aliases are documented, not guaranteed. Expect one round
  of mapping fixes on the first engagement with a new system.
- Quality checks catch what a schema can express. Business truth — whether a
  stage name means what it says, whether a move-in date is real — is the
  operator's to confirm, and the report says so.
- This document contains no testimonials, client counts, benchmarks, or
  outcome promises, because there are none to cite. Keep it that way.
