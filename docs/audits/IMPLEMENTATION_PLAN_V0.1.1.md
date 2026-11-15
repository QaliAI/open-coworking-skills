# Implementation plan — v0.1.1

**Repository:** `QaliAI/open-coworking-skills`
**Base commit:** `d35e6858e2026070ec2a06f3a917840ffcc92135`
**Date:** 2026-10-20
**Companion documents:** `DOMAIN_REALISM_AUDIT_2026.md`, `GAP_RESEARCH_2026.md`

---

## 1. Priority definitions

| Priority | Definition | Gate for shipping |
|---|---|---|
| **P0** | **Correctness defect.** The code or the skill produces a wrong answer, a false statement about the product, or a deliverable the engine cannot produce. | Fix + regression test + doc fix. Ships as a patch. |
| **P1** | **Materially misleading assumption.** A skill states something untrue, unlabelled or unsupported in a way that could change an operator's decision — or asserts an industry fact with no source. | Fix + source (or rewording) + test where applicable. |
| **P2** | **Significant coverage gap.** The skill's model is materially narrower than the real-world object it models, so it under-serves the operator. | Fix or explicitly document the narrowing. |
| **P3** | **Useful improvement.** Real but low-consequence, or a quality-of-life fix. | Batch into the release. |
| **P4** | **Defer.** Correct to defer; recorded so it is not lost. | Not this release. |

**Hard caps for this release:** at most **7 new skills**; **zero** promotions
to stable; **zero** deprecations.

---

## 2. Release scope recommendation

**Ship v0.1.1 as a correction release, not an expansion release.**

The repository's deterministic core is sound; the defects are concentrated in
(a) one product-mapping function, (b) documentation that promises deliverables
the engine does not produce, (c) a set of industry claims written as facts
without sources, and (d) a handful of genuinely missing object models.

The recommended v0.1.1 scope is:

- **All P0** (2 items — roughly half a day).
- **All P1** (14 items — roughly 3–4 days).
- **All P2** that does not require a new schema entity (roughly 2 days).
- **P3** batch (roughly 1 day).
- **Three P1 new skills** from `GAP_RESEARCH_2026.md`, if and only if the
  P0/P1 corrections are complete and tested first (roughly 4–6 days).

**Total estimated scope:**

| Slice | Estimate | Notes |
|---|---|---|
| P0 (2) | **0.5 day** | One function substitution + one regression test |
| P1 (14) | **3–4 days** | Mostly documentation, labelling and source work; 4 items touch code |
| P2 (14) | **2–3 days** | Mostly engine additions with fixtures |
| P3 (11) | **1 day** | Batch |
| 3 new P1 skills | **4–6 days** | Offboarding, mail operations, broker channel |
| **Total without new skills** | **7–9 days** | |
| **Total with 3 new skills** | **11–15 days** | |
| **Total with all 7 proposed skills** | **16–21 days** | Not recommended for this release |

**Recommendation:** land the correction release first (7–9 days). Add the
three P1 skills in a follow-up release once the correction release has been
reviewed. This keeps the diff auditable and matches the repository's own
"quality over count" rule (`AGENTS.md` rule 1).

---

## 3. P0 — correctness defects

### P0-1 · Virtual-office product bucket is unreachable

**Finding:** F-01. **Location:** `src/opencoworking/economics.py:17-33`.

`_product()` matches aliases by substring in a fixed dictionary order, and
`"office"` (checked first) is a substring of `"virtual_office"` and
`"virtual-office"`. Every virtual-office label is therefore classified as
`office`. Verified: `virtual_office` → `office`, `virtual-office` → `office`,
`Virtual Office` → `office`, `meeting_suite` → `office`. Consequence: the
`virtual_office` product bucket in `product_contribution` can never appear,
and virtual-office costs are silently folded into the `office` line.

**Change.**
1. Replace the substring scan with an **exact-match-then-explicit-alias**
   resolver: normalise the key (`lower`, spaces → `_`, hyphens → `_`), then
   look it up in an explicit alias table. Only fall back to a **longest-first
   substring** match for keys not in the table, and require the matched
   substring to be a **word-boundary** token, not an interior substring.
2. Order the fallback by descending alias length so `meeting_room` is
   classified before `room` and `private_office` before `office`.
3. Add `virtual_office` aliases: `virtual_office`, `virtual-office`,
   `virtual`, `vo`, `mailbox`, `business_address`, `business-address`.
4. Reject the ambiguous cases rather than guessing: `meeting_suite` and any
   key containing both `office` and `virtual` must resolve to a single
   canonical bucket **or** return `unmapped`, never a guess. The report must
   list unmapped labels so the operator can extend the table.
5. Keep `other` and `unassigned` for genuinely unknown labels, and print the
   unmapped set in the output so a wrong classification is visible.

**Tests.**
- Unit: a table-driven test over the full alias set asserting the exact
  expected canonical bucket for each label, including the four currently
  misclassified labels.
- Regression: an end-to-end `unit_economics` case with a `virtual_office`
  cost row and a virtual-office membership, asserting that
  `product_contribution` contains a `virtual_office` row, that the `office`
  row's `supplied_monthly_cost` excludes the VO cost, and that the VO
  contribution is not a phantom negative.
- Test must live in `tests/unit/` (the fixture directory
  `tests/fixtures/unit-economics/` currently has no virtual-office row —
  that is why the bug survived).

**Estimate.** 3 hours including tests.

**Risk.** Low. The change is contained to one function. The only behavioural
change for existing users is that virtual-office costs stop being reported
inside the office line — which is the fix.

---

### P0-2 · The skill selected for "break even" answers with a coverage figure

**Finding:** F-02. **Location:** `coworking-unit-economics/SKILL.md:3, 26,
63`; `src/opencoworking/economics.py:108-125`.

The skill's description (the field an agent uses to select it) includes the
trigger **"what occupancy do we need to break even"**. The skill then returns
a fixed-cost coverage figure that omits every variable cost. For any location
with material variable costs, the true break-even occupancy
(`fixed ÷ (rate − variable per workstation)`) is materially higher. The
operator gets a number that is too low, selected by a question the skill
itself disclaims.

**Change.**
1. **Rename the metric in the output** to what it is, everywhere:
   `workstations_to_cover_fixed_costs` stays; add an explicit
   `metric_kind: "fixed_cost_coverage"` and a `not_a_break_even` statement
   inside the `coverage` block, not only in the skill prose.
2. **Add a contribution-margin path that is opt-in and operator-supplied.**
   Accept an optional `kind=variable_per_workstation` cost row (a per-unit
   variable cost, not a monthly total) and, when present, compute and report
   `break_even_occupancy_on_contribution` alongside the coverage figure — with
   its own formula string. When no such row exists, the coverage figure is
   returned alone and the report states *"break-even not computed: no
   per-workstation variable cost supplied"*.
3. **Refuse the mislabel in the skill text.** The description's trigger list
   must keep the phrase operators actually use, but the skill must open with
   the distinction: *"You asked for break-even. This skill computes
   fixed-cost coverage. Break-even needs a variable cost per workstation;
   give me that row and I will compute it. Otherwise this number omits your
   variable costs and will be too low."*
4. **Do not** add NOI, EBITDA, cash flow or capex to this skill (see
   `GAP_RESEARCH_2026.md` §2.1 — that belongs to a location-feasibility
   skill, which does not exist yet).
5. Update the example at `SKILL.md:112-114` so the output shows the
   distinction working, including the case where the operator supplied only
   a monthly cleaning total and no per-workstation variable cost.

**Tests.**
- Known-answer: the existing fixture (`tests/fixtures/unit-economics/`) gains
  a `variable_per_workstation` row and a second expected output asserting the
  contribution-based break-even.
- Negative test: with only the monthly cleaning row, the report contains
  `break_even_occupancy_on_contribution: null` and the
  `not_a_break_even` string.
- The existing known-answer values (1600 fixed, 200 variable, 4.00
  workstations, 100% occupancy) must **not change**.

**Estimate.** 4 hours including tests and doc.

**Risk.** Low. The existing coverage figure is unchanged; a second,
opt-in figure is added.

---

## 4. P1 — materially misleading assumptions

### P1-1 · Unsourced industry claims across the library (F-06, F-12, F-13, F-15, F-16, F-34)

**Locations:** the 60+ class-E sentences listed in
`DOMAIN_REALISM_AUDIT_2026.md` §4.7; `catalog/skills.yaml` (28 repeats).

This is the largest P1 by surface area and the one with the clearest
mechanical fix.

**Change.**
1. For **every** industry-assertion sentence in every `SKILL.md`, choose one:
   - **Source it.** Add a `docs/research/SOURCES.yaml` entry with the URL,
     date, what it establishes, methodology and limits, and re-classify the
     sentence as class D. Apply this to the claims that research *does*
     support — e.g. `coworking-lead-source-normalizer:84-85` ("brokers and
     marketplaces usually carry fees that change ROI math") becomes class D
     on the strength of the LiquidSpace, Yardi and WeWork agreements; and
     `coworking-meeting-event-yield:18` ("rooms are the second revenue
     line") becomes class D **against** the GWA/Deskmag 2025 ranking, which
     puts private offices first, desk memberships second and meeting space
     third — so the claim must be corrected, not merely sourced.
   - **Reword it.** Strip the industry claim and keep the operator problem.
     Most of these sentences are motivational framing; the skill's mechanism
     does not depend on them. Example: "Churn risk is highest in the first
     60 days, and most early cancellations trace to broken basics" becomes
     "A broken first month — access that never worked, an invoice that
     surprised them, nobody to meet — is the failure this checklist is
     built to prevent."
   - **Delete it.** Where the claim adds nothing.
2. **Do the catalog in the same pass.** `catalog/skills.yaml` `problem:`
   strings that repeat a reworded claim must be rewritten to match, because
   `scripts/generate_readme_catalog.py` publishes them into the README
   table. Re-run `python scripts/generate_readme_catalog.py` and commit the
   regenerated README section.
3. **Two specific corrections:**
   - `coworking-system-adapter-builder/SKILL.md:20` — "edit all **24** skills"
     → the correct current number, or better, remove the number entirely and
     say "every skill that touches this entity" (which stays true as the
     library grows).
   - `coworking-renewal-preparation/SKILL.md:163-164` — delete the invented
     "60 days to fill 3,500/mo" statistic. The skill's sibling
     `coworking-occupancy-forecast/SKILL.md:85` promises no invented
     fill-time statistics; this example must not contradict it.
4. Add a **CI check**: a small script that scans `SKILL.md` and
   `catalog/skills.yaml` for a denylist of unsourced-claim patterns
   (`top-three`, `most operators`, `most common`, `best practice`,
   `typically`, `modal cause`, `industry standard`, `proves`, `shows that`)
   and fails the build when a hit is not accompanied by a `SOURCES.yaml`
   key. This makes the fix permanent rather than a one-off sweep.

**Tests.** The CI denylist script, plus `scripts/check_catalog.py` and
`scripts/validate_skills.py` must still pass.

**Estimate.** 2 days. It is ~60 sentences across 30 files plus ~28 catalog
strings, and it must be done carefully rather than by search-and-replace.

**Risk.** Low mechanically; moderate in review time. The prose quality
matters — the claims were doing rhetorical work.

---

### P1-2 · Churn review: unsourced thresholds, false Mode 2, conflated states (F-04, F-05, F-23, F-26, F-36)

**Locations:** `coworking-churn-risk-review/SKILL.md:5, 41-43, 59-69, 81-84,
99, 123-125`; `src/opencoworking/wave2.py:463-513`.

**Change.**
1. **Separate the four states** in the indicator table and in the tiering:
   - **Confirmed departure** — notice served *and* end date recorded. Not a
     risk. Route to offboarding.
   - **Known movement** — notice recorded, end date in the future. A
     transition, not a prediction. Excluded from risk tiers.
   - **Renewal approaching** — end/renewal date inside the window.
   - **At risk** — predictive indicators only.
   `notice_date` moves out of the risk indicator list into the state table.
2. **Make every window operator-configurable, with a labelled default.**
   Add `--cliff-days`, `--payment-days`, `--complaint-days` to the
   `renewals` command (or a new `churn` command that wraps `renewal_scan`
   plus the churn-window logic already in `healthcheck.py:561-611`). Each
   default must be printed as a **repo default, not a fact**, and the skill
   text must say so: *"Default windows are this repository's choices, not
   industry rules. Change them for your location."*
3. **Remove the "≥3 members share a cause" systemic threshold** as an
   automatic verdict. Replace it with: *"When several members share a
   cause, report the count and the grouped evidence; whether that is
   systemic is the operator's call."*
4. **Name the command.** Either add `opencoworking churn` (a thin wrapper
   over `renewal_scan` + `churn_window`) and reference it in Mode 2, or
   change the frontmatter `compatibility:` line and the Mode 2 text to
   reference `opencoworking renewals`. The current state — a frontmatter
   promising the package and a body naming no command — is false.
5. **Quantify month-to-month exposure.** Replace the bare ID list with
   `month_to_month_exposure`: count of M2M active agreements, their
   aggregate MRR, and the number whose notice window would close inside the
   operator's own notice period. Rolling exposure, stated as exposure.
6. **Downgrade maturity** `stable` → `beta` until an operator has run it
   (§P3-4).

**Tests.** Known-answer on the existing synthetic renewal data for each
window; a test asserting that a membership with `notice_date` set appears in
the *known-movement* bucket and **not** in a risk tier; a test for M2M
exposure arithmetic.

**Estimate.** 1 day.

**Risk.** Medium — this changes a stable skill's semantics. Mitigate by
keeping the output fields backward-compatible and adding rather than
removing.

---

### P1-3 · Member onboarding: unsourced premise, self-contradicting example, hard-coded team size (F-06, F-07, F-21, F-30)

**Location:** `coworking-member-onboarding/SKILL.md:17-19, 76-78, 94,
139-163`.

**Change.**
1. Reword `:17-19` per P1-1 (no "highest in the first 60 days", no "most
   early cancellations").
2. **Fix the example.** Replace "Intro: Kai (film) ↔ Grace at Charlie
   Content (media adjacency, from sales notes)" with the general
   community-channel introduction the workflow at `:76-78` already requires
   — the request supplies no interests, so the example must not assert any.
   The example is the highest-leverage place in the whole library to teach
   the rule, because it is what an agent imitates.
3. **Make the team-size threshold configurable.** Replace "Team joins (5+
   people)" with "Team joins (team size threshold the operator sets; default
   5)". Add a field to the operator profile.
4. **Add the `compatibility:` frontmatter line** or drop the Mode 2 claim
   (Mode 2 has no command today — `:38-40`).

**Tests.** Eval case asserting the generated plan for a member with no
stated interests contains a general community-channel introduction and no
named counterpart. Eval case for the team-size threshold at the configured
value.

**Estimate.** 0.5 day.

**Risk.** Low.

---

### P1-4 · Leakage audit promises three totals the engine does not produce (F-08)

**Location:** `coworking-revenue-leakage-audit/SKILL.md:91-95`;
`src/opencoworking/analyze.py:380-513`; `catalog/skills.yaml:101`.

**Change.** Implement the contract rather than delete it, because the
three-way separation is the correct idea:
1. Add a `totals` block to `leakage_report` with exactly the three keys the
   skill names — `billing_at_risk`, `pipeline_at_risk`, `idle_list_value` —
   each with its own numerator, exclusions and period, and each carrying a
   `never_summed_with` note. Do **not** add a grand total.
2. `pipeline_at_risk` requires an amount on `stale_open_deals_30d`, which
   currently carries none. Add `unweighted_expected_value` to that finding,
   computed as the sum of `expected_value` over the listed stale open deals
   — labelled **unweighted pipeline**, exactly as the skill says.
3. Make the 30-day stale window and the 45-day invoice window
   **CLI-configurable** (`--stale-days`, `--invoice-window-days`), matching
   `pipeline --stale-days`, and label both as repo defaults in the output.
4. Update `catalog/skills.yaml` if the key names change.

**Tests.** Known-answer on the synthetic demo: the three totals, each
correct, and an assertion that **no** combined total appears anywhere in
the output.

**Estimate.** 0.5 day.

**Risk.** Low.

---

### P1-5 · Pipeline health: stage vocabulary, missing Mode 2 outputs, coarse duplicates (F-09, F-10, F-11, F-39)

**Location:** `coworking-pipeline-health/SKILL.md:55, 67-71, 79-81`;
`src/opencoworking/analyze.py:200-254, 257-303, 242-249`.

**Change.**
1. **Operator-configurable stage vocabulary.** Add `--open-stage` (repeatable)
   and `--closed-stage` to the `pipeline` command, defaulting to the
   engine's current set. When an operator supplies their own stages, their
   names are used and **no `invalid_stage` finding is raised for any
   supplied name**. Update the SKILL.md list to match the engine's eight
   open stages *and* state that the list is configurable.
2. **Implement the owner workload flag.** Compute the median of open deals
   per owner and flag owners with `> 2×` the median — the threshold
   **configurable** (`--overload-median-multiple`, default 2) and labelled
   a repo default. Print the median (the skill already promises to name
   it).
3. **Implement stage-to-stage conversion.** Extend `funnel_report` to
   compute per-stage counts and rates where the data supports it, and
   identify the largest absolute drop-off stage. Enforce the skill's own
   ≥10-records gate: below it, report counts and **no** rate judgment.
4. **Refine duplicate detection.** Keep `company + product` as one finding
   type, but add a **location** dimension so that legitimate simultaneous
   requirements in different locations are not flagged, and add a
   `same_company_same_product_same_location_multiple_deals` distinction.
   Where a company holds multiple open requirements for the same product,
   report it as **"multiple simultaneous requirements"** and ask the
   operator to confirm, rather than asserting a duplicate.
5. Add a **channel dimension** to the pipeline output where a channel
   column exists (broker / marketplace / referral / direct), labelled
   single-touch and self-reported.

**Tests.** Fixture with an operator-specific stage name (`contract_sent`)
asserting zero `invalid_stage` findings; a workload fixture with a clear
outlier; a stage-conversion fixture asserting the ≥10 gate suppresses the
rate below threshold; a multi-requirement fixture asserting no duplicate
finding across locations.

**Estimate.** 1 day.

**Risk.** Medium — `pipeline_report` is used by the health check. Keep the
output keys backward-compatible.

---

### P1-6 · Tech-stack audit has no business-object dimension (F-14)

**Location:** `coworking-tech-stack-integration-audit/SKILL.md:42-63`;
`src/opencoworking/stack_audit.py:10-19`.

**Change.** Add an **object** dimension without breaking the existing
system view:
1. Accept an optional `objects` table with columns `object`,
`system_of_record`, `consumers`, `direction`, `sync_method`, `latency`,
`canonical_id`, `write_owner`, `error_handling`, `audit_trail`,
`manual_reentry`. The recognised object vocabulary is the vendor-neutral
one: **contact, company, lead, deal, agreement, membership, member,
resource, booking, invoice, payment, access entitlement, consent**.
2. Emit an **object ownership matrix**: object → system of record →
consumers → direction → sync method → latency → canonical ID → write owner
→ error/retry reality → audit trail → manual re-entry risk.
3. Emit deterministic findings from that table: **two systems of record for
   one object**, an object with **no system of record**, an object whose
   **write owner is not the system of record**, an object with **no canonical
   ID**, and an object with **manual re-entry** — with the two systems and
   the object named.
4. Keep the existing system-level findings exactly as they are. The object
   view is **additive**.
5. Update the skill text so Mode 2 is real for the object dimension, and
   so the answer to "who owns the membership, and where is it retyped?" is
   produced by the command rather than by prose in Mode 1.
6. Reference the evidence in the skill's references file so the operator can
   see *why* the checks exist: the derived-access model, the
   cancellation-does-not-revoke-access finding, the six-hour accounting
   transfer, the duplicate-contact failure mode, and the webhook
   auto-disable. These belong in `references/`, cited, not asserted in the
   skill body.

**Tests.** Fixture with an object table asserting each finding type; a
known-answer matrix.

**Estimate.** 1 day.

**Risk.** Low — additive.

---

### P1-7 · Meeting yield: flat utilization denominator (F-17)

**Location:** `coworking-meeting-event-yield/SKILL.md:97-100`;
`src/opencoworking/wave2.py:783-786, 840-843`.

**Change.** Replace the single scalar with an **optional operator-declared
schedule**:
1. Accept `--schedule <csv>` with `day_of_week`, `open_at`, `close_at`,
   `closed` and optional `location_id` / `room_unit_id`. When absent, keep
   today's flat behaviour **and its existing note**.
2. When a schedule is supplied, compute bookable hours per room from the
   declared schedule, excluding closed days, and print the denominator
   construction in the output.
3. Keep the existing "weekends included" note when no schedule is supplied.
4. Do **not** attempt blackout or closure detection from bookings — it is
   not observable in an export.

**Tests.** Fixture with a weekday-only schedule asserting the denominator
and utilization; a regression test asserting the flat path is unchanged.

**Estimate.** 0.75 day.

**Risk.** Low — the existing default path is preserved.

---

### P1-8 · Canonical schema: `room_booking` cannot express the exclusions the engine expects (F-40)

**Location:** `schemas/coworking.schema.json`;
`src/opencoworking/wave2.py:661-677`.

The engine excludes cancelled and no-show bookings only when the export
carries a status/flag column — but the canonical `room_booking` entity
defines no `status`, no `booking_source` and no `cancellation_reason`, so in
practice the exclusion path rarely fires and the "booked is not attended"
caveat is the operator's only protection.

**Change.** Extend `room_booking` with **optional** `status`,
`booking_source`, `cancellation_reason` and `attended` fields, documented
as the vendor fields they map to, with the source vendor export field lists
recorded in `SOURCES.yaml`. Keep them optional so existing adapters keep
working. Update the meeting-yield skill and the data dictionary to name
them.

**Tests.** Schema validation test; a fixture with a `status` column asserting
the exclusion path fires and a blank status stays in.

**Estimate.** 0.5 day.

**Risk.** Low.

---

## 5. P2 — significant coverage gaps

| ID | Finding | Change | Estimate |
|---|---|---|---|
| **P2-1** | F-03 product contribution compares two taxonomies | Derive revenue product from the **membership's** `product` field (with a documented fallback to `unit_type` when the membership has none), so cost and revenue share one axis; print the mapping used per row | 0.5 d |
| **P2-2** | F-18 unimplemented rules promised in four skills | Implement or remove: sub-3-unit low-volume label and the >30%-unpriced reliability note (discount-pricing); >10%-unpriced low-confidence label (occupancy-dashboard); sub-10-lead funnel gate (benchmark). **Implement** — all four are cheap and each is a real operator question | 0.5 d |
| **P2-3** | F-19 speed-to-lead promises segmentation with no engine | Implement segmentation by source, owner and created-hour bucket, with the ≥10 gate and counts-only below it | 0.5 d |
| **P2-4** | F-20 lead-to-tour promises nine checkpoints, engine computes four | Either implement the missing checkpoints or narrow the skill to the four and move the rest into a clearly-labelled "operator-supplied observation" section. **Narrow** — the extra checkpoints are not derivable from the canonical schema | 0.5 d |
| **P2-5** | F-23 month-to-month is an ID list, not an exposure | Fold into P1-2 (M2M exposure count + MRR + notice-window closings) | (in P1-2) |
| **P2-6** | F-25 adapter-builder's support ladder omits `manual` | Add the `manual` rung to match `docs/research/coworking-systems.md` and the 30 systems in `catalog/compatibility.yaml`; adjust the "no label above export-supported" rule so it does not mislabel a `manual` system | 0.25 d |
| **P2-7** | F-24 leakage windows not configurable | Folded into P1-4 | (in P1-4) |
| **P2-8** | F-26 churn Mode 2 names no command | Folded into P1-2 | (in P1-2) |
| **P2-9** | F-27 mcp-builder output contract claims implemented code | Rewrite the output contract as a **design** deliverable, and reference the shipped `src/opencoworking/connectors/` prototypes with their mock-only status stated plainly | 0.25 d |
| **P2-10** | F-28 renewal-preparation batch trigger competes with renewal-expansion-risk | Delete the batch trigger from `coworking-renewal-preparation/SKILL.md:25-26` and from its `evals/cases.yaml:5`; route batch questions to `coworking-renewal-expansion-risk` | 0.25 d |
| **P2-11** | F-14 object dimension | Folded into P1-6 | (in P1-6) |
| **P2-12** | F-22 "24 skills" | Folded into P1-1 | (in P1-1) |
| **P2-13** | Broker/aggregator channel dimension in pipeline and funnel | Add a `channel` column to the canonical `lead`/`deal` entities (optional) and a channel breakdown to the pipeline output, labelled single-touch and self-reported | 0.5 d |
| **P2-14** | `cost_class` on canonical source buckets | Extend `normalize.py` buckets with a `cost_class` attribute (commission-bearing / per-referral / paid-media / shared-brand / no-fee-known / unknown) and surface it in the source report — the cheapest high-value addition in the whole plan | 0.5 d |

**P2 subtotal: ~3 days.**

---

## 6. P3 — useful improvements

| ID | Finding | Change | Estimate |
|---|---|---|---|
| P3-1 | F-29 ghost-recovery's only command eval re-runs the leakage audit | Add an eval that exercises the sequence logic, not the leakage check | 0.25 d |
| P3-2 | F-30 member-onboarding Mode 2 has no command | Add a `compatibility:` line and either implement an audit command or re-scope Mode 2 to Mode 1 | 0.25 d |
| P3-3 | F-31/F-32 catalog overclaims | Bring `catalog/skills.yaml` outputs strings into line with what the skills and engine actually produce (`expiring-promo list`, `segment patterns`, `nine-checkpoint funnel localization`, `workload`, `never-summed totals`) | 0.25 d |
| P3-4 | F-36/F-37 two skills shipped `stable` that oversell | Downgrade `coworking-churn-risk-review` and `coworking-mcp-builder` to `beta` in both the SKILL.md frontmatter and `catalog/skills.yaml`; regenerate the README table | 0.25 d |
| P3-5 | F-33 dead `unbilled_memberships` class | Either emit the class from the leakage check or remove it from `ROLE_CLASSES` | 0.25 d |
| P3-6 | F-35 README "29 known-answer eval cases" | Update to the true count (31) and add a CI assertion that the README count matches the runner output | 0.1 d |
| P3-7 | F-38 zero field validation | Execute the `docs/OPERATOR_VALIDATION.md` program with six operators covering the six named cohorts; record outcomes in `docs/evals/operator-acceptance-report.md` | 2–4 weeks elapsed, not engineering time |
| P3-8 | Prior scorecard's remaining open items | Close the prior audit's five open items and the lead-to-tour item it omitted from its own list | 0.5 d (overlaps P1-1, P1-2, P1-3, P2-9, P2-10) |
| P3-9 | `coworking-crm-wms-reconciliation` has no Northstar case and its version line was not narrowed | Add the Northstar case or narrow the version line, as the prior audit required | 0.25 d |
| P3-10 | Pipeline trigger narrowing applied to prose only | Narrow `evals/cases.yaml:5` and `tests/evals/trigger_cases.yaml:261,277` to match the SKILL.md | 0.25 d |
| P3-11 | `coworking-system-adapter-builder` support-ladder alignment | Covered by P2-6 | — |

**P3 subtotal: ~1.5 days** (excluding P3-7, which is elapsed time).

---

## 7. P4 — defer

| ID | Item | Why deferred |
|---|---|---|
| P4-1 | `coworking-location-feasibility` (new skill) | Real gap, but requires the operator to supply a lease and build-out model before it produces anything, and no operator case exists. Build after v0.1.1 ships. See `GAP_RESEARCH_2026.md` §2.1 |
| P4-2 | `coworking-acquisition-cost-review` (new skill) | Build after the `cost_class` extension (P2-14) exists and one operator has a real spend file. See `GAP_RESEARCH_2026.md` §2.2 |
| P4-3 | `coworking-member-offboarding` (new skill) | High value and well evidenced, but it is a *new* skill and this release's scope should be corrective. Ship in the following release |
| P4-4 | `coworking-mail-operations` (new skill) | Same, plus it needs a schema addition and a documented vendor export field list |
| P4-5 | `coworking-broker-channel-manager` (new skill) | Same, plus the operator's own channel terms file |
| P4-6 | `coworking-booking-exceptions` (new skill) | Depends on P1-7 and P1-8 landing first |
| P4-7 | `coworking-proposal-terms-check` (new skill) | Depends on a source-cited required-terms inventory |
| P4-8 | `coworking-shift-continuity` | Needs three real operator handover artefacts from ≥2 operators |
| P4-9 | Service-recovery widening of `coworking-maintenance-tracker` | Fold in when that planned skill is built |
| P4-10 | Enterprise requirements checklist | Fold into `coworking-tour-preparation` when enterprise volume appears in real usage |
| P4-11 | Booking-flow-audit catalogue entry (website-conversion version) | **Merge** into `coworking-local-seo-audit` + `coworking-lead-to-tour-diagnostic` and fix the catalogue category — this is a catalogue correction, not a deferral, and should ship with P1-1 |
| P4-12 | Any new skill beyond the seven proposed | Out of scope |

**Note on P4-11:** it is listed here because the *operational* booking-outcome
skill is deferred, but the *catalogue category fix* is a P1-1 deliverable and
must not be deferred.

---

## 8. Sequencing and dependencies

```
P0-1 (economics._product) ──┐
P0-2 (break-even naming) ───┤──► P1-1 (unsourced claims sweep, incl. catalog)
                             │         │
                             │         ├──► P1-7 (room schedule) ──► P1-8 (room_booking schema)
                             │         │                              │
                             │         └──► P3-3 (catalog overclaims)
                             │
                             └──► P2-1 (product taxonomy alignment)

P1-2 (churn states + windows) ──► P2-5, P2-7, P2-8
P1-4 (leakage totals)         ──► P2-7
P1-5 (pipeline)               ──► P2-13 (channel dimension)
P1-6 (tech stack objects)
P2-14 (cost_class)            ──► P4-2 (acquisition-cost skill, later release)
```

**Hard rule:** P1-1 (the unsourced-claims sweep) should be the **last**
substantive edit before the release, because it touches 30 files and any
other concurrent edit raises the chance of a merge conflict or an
accidentally reverted claim.

---

## 9. Release checklist for v0.1.1

Everything below must pass before the tag:

```bash
python -m pytest -q
python scripts/validate_skills.py
python scripts/check_catalog.py
python scripts/check_references.py
python scripts/run_evals.py
python scripts/run_trigger_evals.py
python scripts/generate_readme_catalog.py   # regenerate, then commit the diff
```

Plus, for v0.1.1 specifically:

- [ ] The CI denylist script for unsourced-claim patterns exists and passes.
- [ ] Every class-E sentence in `DOMAIN_REALISM_AUDIT_2026.md` §4.7 is
      either sourced in `SOURCES.yaml` or reworded.
- [ ] The catalog's `problem:` strings no longer repeat a reworded claim.
- [ ] `catalog/skills.yaml` maturity matches each SKILL.md's
      `opencoworking.maturity` — including the two downgrades.
- [ ] Every output key promised in a SKILL.md's "Output contract" exists in
      the engine, and every key promised in `catalog/skills.yaml`'s `outputs:`
      exists in the skill. (This is the check that would have caught F-08,
      F-09, F-10, F-19, F-20, F-31, F-32.)
- [ ] The four open Dependabot PRs are merged or closed.
- [ ] `CHANGELOG.md` records the P0/P1 items in plain language, including
      the virtual-office product-bucketing correction — an operator who
      relied on the old figure needs to know it changed.
- [ ] The version is bumped to 0.1.1 in `pyproject.toml` and in every
      SKILL.md `opencoworking.version` that changed.
- [ ] **No skill is promoted to stable.** Promotion is gated on field
      validation (P3-7), not on this release.

---

## 10. Answering the brief's questions directly

**What is actually wrong?** Six things, in order of risk:
1. The virtual-office product bucket is unreachable (P0-1) — the engine
   reports a wrong product mix.
2. A skill selected by the break-even question answers with a fixed-cost
   coverage figure that omits variable costs (P0-2).
3. ~60 industry claims across the library are stated as fact with no source,
   28 of them published in the README via the generated catalogue (P1-1).
4. Four SKILL.md output contracts name deliverables the engine does not
   produce, one of which (`pipeline_at_risk`) is not computable as specified
   (P1-4, P1-5, P2-2, P2-3).
5. A stable skill (churn review) has four invented thresholds, a false Mode
   2 claim, and conflates notice-given with predicted churn (P1-2).
6. The onboarding example teaches the opposite of its own rule (P1-3).

**What is merely incomplete?** The tech-stack audit's object dimension, the
room scheduling model, the `room_booking` schema fields, the broker channel
dimension, the contribution-margin path in unit economics, month-to-month
exposure quantification, and the entire offboarding / broker / mail /
enterprise / acquisition-cost / feasibility workflow set. None of these
produces a wrong answer today; they mean the library answers a narrower
question than the operator asked.

**The five highest-risk existing assumptions.**
1. That fixed-cost coverage answers a break-even question (P0-2).
2. That a product label containing "office" identifies an office
   (P0-1).
3. That churn concentrates in the first 60 days and traces to broken basics
   (P1-3).
4. That 60 / 90 / 14 days and 3 shared members are meaningful churn
   thresholds (P1-2).
5. That a pipeline has one stage vocabulary and that "owner overload" and
   "biggest drop-off stage" need no computation (P1-5).

**Strongest genuinely missing skills.** In priority order:
`coworking-member-offboarding`, `coworking-mail-operations`,
`coworking-broker-channel-manager` (re-scoped) — all three have converged,
independently corroborated object models and citable constraints. Then
`coworking-location-feasibility` and `coworking-acquisition-cost-review`
for a later release. See `GAP_RESEARCH_2026.md`.

**What should NOT be built.** An attribution-model or multi-touch engine; a
marketing-mix or incrementality runner; an LTV:CAC scorer; a shift-handover
note generator; a standalone member-service skill (fold it into
`coworking-maintenance-tracker`); a proposal *builder* (narrow it to a terms
check); a "generate a handover note" skill; a channel-ROI recommender; a
break-even occupancy benchmark; and anything that invents demand, absorption
or pricing.

**Is the repository safe to promote while these issues are pending?** It is
safe to **publish and use** — every defect found here lands in a report a
human reads, nothing sends, charges, deletes, or revokes access, and the
deterministic core does not fabricate market benchmarks or legal
requirements. It is **not yet safe to promote** (badge stable, market as
validated) without closing at least P0-1, P0-2 and P1-1: one of those
produces a wrong money answer, one mislabels the answer to a money
question, and one publishes 28 unsourced industry claims in the README
table. Estimated effort to close all P0 and P1: **4–5 days**. With the three
P1 new skills: **11–15 days**.
