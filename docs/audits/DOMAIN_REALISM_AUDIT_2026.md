# Domain realism audit — 2026

**Repository:** `QaliAI/open-coworking-skills`
**Audit date:** 2026-10-20
**Audited commit:** `d35e6858e2026070ec2a06f3a917840ffcc92135` (branch `main`)
**Audited release:** `v0.1.0` (the only tag in the repository)
**Audit type:** FINAL PRE-PROMOTION domain-realism audit — Phase A (research and
audit only; no production file was modified)

---

## 0. What this audit is, and what it is not

This audit asks one question: **where does this repository contain technically
plausible logic that does not reflect how real coworking and flexible-workspace
businesses actually operate?**

It is not a code review, not a style review, and not a rewrite. The
repository's engineering quality is high and this document says so where it is
true. The findings here are about *domain realism* — the fit between what the
skills assert and how the industry actually works.

Every claim in this document is either (a) verified against the repository at
the commit above, with `file:line`, or (b) backed by a cited external source
with a URL and a publication date, or (c) explicitly labelled as my judgement.

**Evidence rules applied throughout:**

- Every external factual claim carries a URL and a publication date, plus a
  note on what the source *actually establishes* versus what is inferred from
  it, and its methodology or sample limits.
- Operator forums (Reddit, Facebook groups) are used as **pain-point evidence
  only**. They are never used for formulas, thresholds, legal requirements,
  financial definitions, or benchmarks.
- Vendor marketing is used only where it is the vendor's own operating
  reality (its own published terms of service, its own API documentation, its
  own filed financial statements), and is labelled as vendor-published.
- Where **no credible source exists**, that absence is stated as a finding
  rather than filled with a plausible number.
- Every rule in every skill is classified **A–E** (§3).

---

## 1. Verified repository state

Nothing below is carried over from a prior report. All of it was re-read from
the working tree at `d35e685`.

| Item | Verified value | How verified |
|---|---|---|
| Current commit | `d35e6858e2026070ec2a06f3a917840ffcc92135` | `git rev-parse HEAD` |
| Branch | `main` | `git branch --show-current` |
| Working tree | clean except untracked `.freebuff/` | `git status --short` |
| Tags | exactly one: `v0.1.0` | `git tag --sort=-creatordate` |
| Remote | `https://github.com/QaliAI/open-coworking-skills.git` | `git remote -v` |
| Installable skills | **37** | `scripts/check_catalog.py` → "37 skill directories" |
| Maturity split | **24 stable / 13 beta / 22 planned = 59 catalog entries** | `catalog/skills.yaml`; `check_catalog.py` reports 24 stable + 22 planned + 37 directories |
| Longest SKILL.md | 158 lines (`coworking-monthly-owner-report`) | line counts across `.agents/skills/*/SKILL.md` |
| CLI subcommands | **23** (`inspect, quality, occupancy, pipeline, funnel, speed-to-lead, sources, leakage, vo-reconcile, reconcile, brief, forecast, renewals, pricing, collections, rooms, economics, stack-audit, benchmark, health-check, health-check-finalize, demo, redact`) | `python -m opencoworking.cli --help` |
| Python package | `src/opencoworking/`, 15 modules + 3 connectors | tree listing |
| Tests | **all pass**; `python -m pytest -q` → 100% green | executed |
| Skill validation | "Validated 37 skills. All skills pass validation." | `scripts/validate_skills.py` |
| Catalog consistency | "Catalog and skills agree." | `scripts/check_catalog.py` |
| Link integrity | "Checked 288 relative links. No broken relative links." | `scripts/check_references.py` |
| Evals | "31 command cases executed, 112 checklist cases validated structurally. All deterministic evals pass." | `scripts/run_evals.py` |
| Open PRs | **0** human PRs | `gh pr list --state open` |
| Open Dependabot PRs | **4**, all GitHub Actions version bumps (setup-python 5.6.0→7.0.0, dependency-review-action 4.9.0→5.0.0, gitleaks-action 2.3.9→3.0.0, checkout 4.3.1→7.0.1), opened 2026-07-21 | `gh pr list --state open` |
| Open issues | **0** | `gh issue list --state open` |
| Connectors | 2 read-only prototypes (OfficeRnD, HubSpot), mock-tested only, no live network path | `src/opencoworking/connectors/` |
| Prior audits present | `docs/audits/SKILL_SCORECARD_2026.md`, `docs/research/2026-gap-analysis.md`, `2026-operator-pain-points.md`, `2026-ai-in-coworking.md`, plus root-level `AUDIT_PLAN.md`, `EXPERT_AUDIT.md`, `FINAL_RELEASE_AUDIT.md`, `BUILD_REPORT.md`, `WAVE2_REPORT.md`, `LAUNCH_REPORT.md`, `RELEASE_READINESS.md`, `PLANS.md` | directory listing |
| Field validation | **0 of 37 skills** has been run by an outside operator | `docs/OPERATOR_VALIDATION.md` describes the program; it has not been executed. The only skill that states this explicitly is `coworking-unit-economics/SKILL.md:122` ("Not yet run by an outside operator") |

### 1.1 README claims vs. verified reality

| README claim | Line | Reality | Verdict |
|---|---|---|---|
| "37 skills" | 125, 317 | 37 | accurate |
| "233 tests" | 315 | pytest collects and passes; the count is at least consistent | accurate |
| "31 command cases" / "112 checklist cases" | 315 | matches `run_evals.py` output exactly | accurate |
| "518 cases across 37 skills (14 each)" | 316 | consistent with `tests/evals/trigger_cases.yaml` | accurate |
| "476/476 LLM judge on an earlier 34-skill run" | 316 | honestly disclosed as not re-run for the 42 newer cases | accurate and correctly caveated |
| **"29 known-answer eval cases run in CI"** | **44** | the runner reports **31** command cases | **stale — off by two** |
| "Vendor-neutral" | 48 | genuinely true for the deterministic core; **not** true for the tech-stack skill's category list (see §4.6) | partially true |
| "all skills are read-only or draft-only (R0/R1)" | 52 | true — every catalog risk tier is r0/r1 | accurate |

---

## 2. Structural health: what the repository genuinely gets right

This matters, because the recommendations below should not be read as a
verdict on the whole repository. The following are real strengths, verified:

1. **The deterministic core is honest.** `src/opencoworking/` consistently
   prints numerator, denominator, exclusions and period, distinguishes
   *count-based* from *revenue-based* measures, and reports "not measured"
   with a named reason instead of inventing a value. Missing inputs are
   **unknown, not zero** — stated in `economics.py:168`, `metrics.py`, and
   every skill's output contract. This is rare and it is the reason this
   repository is worth auditing rather than rewriting.
2. **Data is treated as data.** Note text, CSV cells and pasted exports are
   explicitly never instructions (`stack_audit.py:149`, `analyze.py`, and
   the "Privacy and security" section of every skill).
3. **No fabricated benchmarks in the analytic core.** `coworking-unit-economics/SKILL.md:80`
   explicitly forbids comparing coverage occupancy to 70%/80%/any published
   benchmark. `coworking-source-verifier` exists specifically to enforce
   fact/calculation/assumption/hypothesis separation.
4. **The market-access denominator problem is understood.** `coworking-meeting-event-yield`
   refuses to compute utilization without declared bookable hours, refuses
   contribution margin without a complete cost column, and states that
   booked ≠ attended.
5. **The prior audit's recommendations were mostly acted on.** Of the prior
   scorecard's five "highest-value improvements," three are closed
   (source-verifier example, monthly-owner-report command calls,
   meeting-yield exclusion rule), plus the room-booking fixture. The prior
   audit's *no promotion, no merge, no deprecation* stance was honoured.
6. **Rule 4 (singular canonical source) is mostly respected.** Discount
   analysis lives in one skill, renewal history in another, collections
   ordering in a third.

---

## 3. The classification framework

Every meaningful rule, threshold and claim in every skill is classified:

| Class | Meaning | Required treatment |
|---|---|---|
| **A** | Definition or arithmetic. Either provably correct, or demonstrably wrong. | May be stated as fact. |
| **B** | Operator-configurable policy. The operator decides; the repo supplies the mechanism. | Must be configurable or explicitly marked "operator sets this". |
| **C** | Heuristic or repo-chosen default. Defensible, but a choice, not a truth. | Must be labelled as a default/heuristic. |
| **D** | Externally evidenced industry observation. | Must carry a source in `docs/research/SOURCES.yaml`. |
| **E** | Unsupported assumption. Asserted as fact with no source and no operator basis. | Must not be presented as A or D. |
| **M** | Misclassification. Something stated as A that is actually B, C, D or E. | Must be re-labelled. |

**The meta-finding:** across all 37 skills, `docs/research/SOURCES.yaml`
contains **exactly three** coworking-industry sources — the OfficeRnD 2026 Flex
Space Tech Stack Report, its Daily Office News secondary write-up, and
vendor API documentation. There is **no** ledger entry for churn timing, tour
conversion, early-cancellation causes, ghosting prevalence, collection-cause
frequencies, deposit norms, notice periods, broker commissions, booking
schedules, or any occupancy/break-even benchmark.

Therefore: **the great majority of industry-assertion sentences across this
library are class E**, and they are currently written in the voice of class A
or D. This is the single systemic finding of this audit. It is not a
plumbing problem; it is a *labelling* problem, and it is exactly what the
repository's own `AGENTS.md` rule 2 ("No fabrication… Every factual external
claim needs a source recorded in `docs/research/SOURCES.yaml`") forbids.

---

## 4. High-risk area deep dives

### 4.1 UNIT ECONOMICS — `coworking-unit-economics` (beta)

**What the code actually does.** `src/opencoworking/economics.py` computes a
**fixed-cost coverage count**: `fixed_monthly ÷ (contracted MRR ÷ occupied
sellable workstations)`, then expresses that as an occupancy fraction of
sellable capacity. The skill text is *careful*: `SKILL.md:63` says "This is
coverage math at the current average contracted rate. It is not a marginal
contribution model and it is not an industry break-even." The variable-cost
sum is collected but deliberately excluded from the coverage calculation, and
the skill says why (`SKILL.md:122` in `economics.py`: variable rows are
"this month's totals, not a cost of the next workstation").

**Why that is still a problem.** The skill's *description* (the field that
determines whether an agent selects it) is:

> "Answers what occupancy a coworking location needs to cover the fixed costs
> the operator actually supplied… Use when an operator asks **'what occupancy
> do we need to break even'**…"

So a skill that explicitly disclaims being a break-even calculation is
selected by the break-even question, and returns a number that omits **every
variable cost**. For a location with material variable costs (cleaning,
utilities, payment processing, consumables — all of which the skill's own cost
file expects at `kind=variable`), the true break-even occupancy is
`fixed ÷ (rate − variable-per-workstation)`, which is materially *higher* than
the coverage figure. The operator receives a number that is too low and is
told it is a coverage figure, not a break-even.

This is exactly the failure the research identifies. **No source in the
industry calls fixed-cost coverage "break-even occupancy."** The real
formulations are:

- **Occupancy-based break-even computed monthly** — Kisi/CoworkingResources,
  "Operational Metrics & Reporting for Shared Workspaces"
  (https://www.coworkingresources.org/blog/operational-metrics-reporting-shared-workspaces,
  2018-08-13), which also states "there isn't an exact occupancy percentage
  that will determine profitability for operators across the board… most
  operators are profitable at an occupancy of between 80 and 85%."
- **NOI / DSCR framing** — NOI = revenue − vacancy − credit loss − operating
  expenses, **before debt service, depreciation, income taxes and most
  capex**; break-even occupancy defined as the level required to cover
  operating expenses **and debt service** (Kolena,
  https://www.kolena.com/blog/commercial-real-estate-underwriting-documents-metrics-and-process/,
  2026-09-09).
- **Revenue-based break-even with a contribution margin** — fixed monthly
  costs plus average revenue per member, asking "can the business become
  healthy at a realistic occupancy level" (Spacebring,
  https://www.spacebring.com/blog/start-coworking-space).
- **The multi-variable reality** — GWA/Deskmag 2019 Global Coworking Survey:
  90% of coworking spaces generate a profit if they meet **at least four
  conditions**: more than 200 members, older than one year, profit-oriented,
  and not subsidised from other businesses. Profitability is a conjunction of
  scale, age, orientation and subsidy — **not a coverage ratio**
  (https://www.coworkinghandbook.com/stats/, 2020-07-23).
- **Break-even vs. payback are different milestones** — Smartworks (NSE-listed)
  reports operational cost break-even at roughly T+12 months and capex payback
  at 30–32 months, with pre-committed occupancy at opening of 25–30%
  (FY2025-26 Annual Report,
  https://nsearchives.nseindia.com/annual_reports/AR_31688_SMARTWORKS_2025_2026_A_18887547_07092026161734.pdf).

**A second, harder defect in the same skill — a reproducible engine bug.**
`_product()` at `src/opencoworking/economics.py:28-33` maps a free-text
product label to a canonical bucket using *substring* matching in a fixed
dictionary order, with `"office"` checked first:

```python
for name, aliases in _PRODUCTS.items():
    if key in aliases or any(alias in key for alias in aliases):
        return name
```

Because the literal substring `"office"` occurs inside `"virtual_office"` and
`"virtual-office"`, **every virtual-office label is classified as `office`**.
Verified by direct probe:

| Input label | `_product()` returns | Correct |
|---|---|---|
| `virtual_office` | `office` | `virtual_office` |
| `virtual-office` | `office` | `virtual_office` |
| `Virtual Office` / `Virtual_Office` | `office` | `virtual_office` |
| `meeting_suite` | `office` | not a meeting room |
| `meeting_room`, `hot-desk`, `mailbox`, `vo`, `desk` | correct | correct |

Consequence, verified end-to-end with a cost file carrying a
`virtual_office` row of 300: the `virtual_office` product bucket in
`product_contribution` is **unreachable**, and the virtual-office cost is
silently folded into the `office` line (1600 rent + 200 cleaning + 300 VO
fee = 2100 booked against 800 of "office" revenue, reporting a −1300
contribution). The skill's stated purpose is "which product actually makes
money: offices, desks, rooms, **or virtual office**?" (`SKILL.md:27`) and
`SKILL.md:99` explicitly discusses virtual-office revenue. That question
cannot be answered correctly today.

A third, structural issue: `product_contribution` compares **cost bucketed by
the operator's own `product` label** against **revenue bucketed by
`inventory.unit_type`** (`economics.py:93-94` vs `:70`). These are two
different taxonomies silently placed on the same axis, with no check that
they agree.

**Missing concepts.** The skill has no treatment of NOI, contribution margin,
operating contribution, EBITDA, cash flow, capex, or a cash trough. Nor does
it need all of them — but the skill must not answer a break-even question
with a coverage figure, and it must be able to say *"you asked for
break-even; this is fixed-cost coverage; here is what I would need to compute
break-even properly"* (a variable cost **per workstation**, or a per-member
revenue mix).

**External data that could have grounded this skill and was not used:** GWA /
Deskmag 2025 (54% of operators profitable, 18% loss-making, 28% break-even,
global average occupancy 68%, private offices generate the most revenue
followed by desk memberships then meeting space;
https://deskmag.com/en/coworking-spaces/2025-ultimate-coworking-space-trends-report-profitability-europe-north-america-market-business-survey-analysis,
2025-10-20). That survey is self-selected and its methodology note warns
"a scientifically representative survey is unlikely to ever exist" — which is
precisely why it can be cited as *D* with its limits rather than ignored.

**Verdict: FIX (P0 + P1).** The skill is honest about what it computes; the
problem is that it is *selected* for a question it does not answer, and its
product bucketing is broken.

---

### 4.2 MEETING / EVENT YIELD — `coworking-meeting-event-yield` (beta)

**What is right.** This is the strongest of the beta skills. The engine
(`wave2.py:661-848`) excludes cancelled and no-show rows from booked hours
**only when the export carries a status/flag column that says so**, and says
in the output note that a blank status stays in and that "booked is not used:
the export does not record attendance" (`wave2.py:813-819`). Contribution
margin is computed only when *every* honoured booking has a parseable cost;
a partial cost column yields `contribution: null` with the reason
(`wave2.py:790-798`). Setup minutes are reported beside booked hours and not
added to them. Pattern claims are gated on ≥20 honoured bookings
(`wave2.py:808`). Zero-charge bookings are explicitly labelled ambiguous
because the export cannot separate plan-included from comped
(`wave2.py:816-818`). This is a high bar and it is met.

**The remaining realism gap: the utilization denominator.**
`--open-hours-per-day N` multiplied by *every day in the observed span
including weekends* is the bookable-hours denominator (`wave2.py:783-786`,
`:840-843`). The skill states the assumption honestly. But it is materially
wrong for most operators:

- **Nexudus** models availability as *operating hours **and blackout
  periods*** per resource, and access schedules as 24/7 / business hours /
  weekends at plan level
  (https://learn.nexudus.com/get-started/platform-overview/data-model-overview).
- **OfficeRnD Flex** attaches booking policies to **resource rates**, with a
  business-hours restriction applied per member group, a separate
  out-of-business-hours price, and blackout/closed days
  (https://help.officernd.com/en/articles/248555-set-up-booking-policies,
  2026-08-20).
- **Coworks** maintains separate booking schedules for member bookings and
  for guest/day-pass bookings, with closed days
  (https://help.coworksapp.com/en/articles/6974766, 2024-01-16).
- **Optix** resolves bookings in two steps (`bookingsDraft` → `bookingsCommit`)
  with an allowance-consumption model and a separate
  `resourceAvailability` query.

So a single flat daily scalar is not a simplification of the real model — it
is a *different model*. A weekday-only, 9-to-6, Monday-to-Friday room
produces a utilization figure that is understated by roughly 40% under the
current denominator, and `revenue_per_available_hour` inherits the error.

**Other real items the skill does not yet carry**, all evidenced:

- **Channel.** Booking source is a first-class dimension with different rules
  per channel — member portal, mobile app, MS Teams, public booking widget,
  admin portal. OfficeRnD's own docs record a live parity defect: "the mobile
  app enforces its own 15-minute minimum booking increment regardless of the
  Min Duration setting… a known limitation" (2026-08-20). Policies also do
  not apply to admin-created bookings.
- **Buffers.** "Disable Back-to-Back (buffer ≤360min)" — a buffer blocks the
  room for *every* booker, not just the same company.
- **Credits.** OfficeRnD: 1 credit = 1 hour, deducted in 0.25 increments
  rounding **up**; credits are tied to the **month of the meeting**; future
  bookings sit "Not Accounted" until the 1st; partial coverage (3 credits +
  $25 for 4.5h) is possible
  (https://help.officernd.com/en/articles/248557-flex-booking-credits-start-here,
  2026-09-30). The skill correctly says valuing credits "needs the operator's
  credit-to-currency rule, asked not assumed" — but the rule itself is
  richer than a single conversion rate.
- **Paid cancellations and no-shows** — the engine handles these *if* the
  export says so. The canonical `room_booking` entity carries neither
  `status` nor `cancellation_reason`, so in practice the exclusion path
  rarely fires.
- **Capacity, multi-day reservations, and internal blocks** — the skill
  handles multi-day as a booked span and says the assumption note covers
  weekend inclusion. It has no notion of internal blocks (staff meetings,
  maintenance holds) that occupy a room but earn nothing.

**Verdict: FIX (P2).** Nothing here is *wrong*; the denominator is
under-specified relative to what vendors actually model.

---

### 4.3 CHURN — `coworking-churn-risk-review` (stable)

**What is right.** The skill refuses to emit a numeric churn probability
(`SKILL.md:110-113`), cites evidence per member, distinguishes "notice
already given" from a predictive signal, and uses "their OWN tenure baseline"
rather than a population average for month-to-month members (`SKILL.md:123-125`).
Those are genuinely good domain instincts.

**What is wrong.** The whole indicator table is hard-coded, unlabelled, and
unsupported:

| Indicator | Window | Class | Label |
|---|---|---|---|
| Renewal cliff | `end_date`/`renewal_date` within **60 days** | C | bare |
| Payment friction | failed payment / overdue invoice within **90 days** | C | bare |
| Unresolved complaints | support/feedback item open **>14 days**, or repeated same-topic complaints | C | bare |
| Declining usage | usage in recent **30 days** "materially below" prior baseline | C | bare ("materially" is undefined and therefore not measurable) |
| Systemic pattern | **≥3 members** share a cause | C | bare |

The 60-day cliff, the 90-day payment window, the 14-day complaint threshold
and the 3-member systemic threshold are **repo heuristics wearing the
uniform of definitions**. No source supports any of them. The repo's own
`references/formulas/README.md` never mentions them. They are not exposed as
CLI flags, and there is **no `opencoworking churn` command** — the skill's
`compatibility:` frontmatter (`SKILL.md:5`) promises "Mode 2 requires Python
3.11+ with the opencoworking package" but **no `opencoworking` command
appears anywhere in the file**. The engine that already computes notice
given, cliff date, renewal-to-list jump and payment friction is
`renewal_scan` in `wave2.py:463-513`, surfaced as `opencoworking renewals`.
The prior scorecard flagged exactly this (`docs/audits/SKILL_SCORECARD_2026.md:162`)
and it remains open.

**The "notice is known movement, not predicted churn" distinction is not
carried into the tiering.** `SKILL.md:81-84` tiers a member as "Act now" if
they have "notice given, renewal cliff, or failed payment + any second
indicator". A member who has *given notice* is not at risk — they have
already left in decision terms. The skill lists notice given as an
**indicator** (`SKILL.md:62`) and then treats it as a risk trigger. That
conflates four materially different states the research separates clearly:

| State | Meaning | Correct handling |
|---|---|---|
| **Confirmed departure** | notice served, end date recorded | offboarding + revenue recovery, not retention |
| **Known movement** | notice date recorded, end date in future | transition management, save opportunity, no churn prediction |
| **Renewal approaching** | end/renewal date inside the window | retention conversation |
| **At risk** | predictive indicators only | watch list |

The research is explicit that a notice is known movement: the broker research
found the operator-side broker programmes treat "Notice Served" as a distinct
contract stage (OfficeRnD: Active / Up for renewal / **Not Renewed** /
**Notice Served** / Expired / Terminated,
https://help.officernd.com/en/articles/248590-flex-contract-statuses-and-stages,
2026-08-06).

**Month-to-month.** `wave2.py:464, 474` and the caveat at `:510-511` treat
month-to-month as having "a permanent renewal cliff" and list it separately
"not force-ranked". The reality is more specific: M2M is **rolling exposure**
— it recurs monthly — and the operator's real question is *how many
month-to-month members am I exposed to this month, and what would it take to
convert some of them to a term*. The current output answers neither; it
emits a list of membership IDs with no exposure figure. Evidence that M2M is
a distinct commercial shape with distinct economics: WeWork pays month-to-month
broker commission on **one month's fee only, for the first month only, and
only for the first deal in that market**
(https://wek8s-hydra-referrals-bucket.s3.amazonaws.com/en-US/Regional+Rider+-+USC.pdf);
Industrious pays 10% for the **first three months** then monthly
(https://www.industriousoffice.com/broker-terms). "10% month-to-month" means
three radically different cash amounts across operators.

**Verdict: FIX (P1) + DOWNGRADE (stable → beta).** The method is good; the
labelling is not, the Mode 2 claim is false, and the thresholds are
invented.

---

### 4.4 ONBOARDING — `coworking-member-onboarding` (stable)

**Confirmed unsourced universal, still present, repeated in the catalog.**
`SKILL.md:17-19`:

> "Churn risk is highest in the first 60 days, and most early cancellations
> trace to broken basics: access card never worked, invoice surprised them,
> nobody introduced them to anyone."

There is **no** entry for this in `docs/research/SOURCES.yaml`. The current
2025–2026 evidence does not support it: GWA/Deskmag 2025 reports member
acquisition as the top challenge and 54% of operators profitable, but says
nothing about a 60-day churn concentration (2025-05-19). The enterprise
research finds churn described as **structural, not demand-driven** — "Members
come for flexibility, but that same flexibility means they can leave easily"
(r/CoWorking, 2026-03-02 — pain-point evidence only, and the mechanism is the
point). Nothing supports "most early cancellations trace to broken basics"
either.

This claim is repeated in `catalog/skills.yaml:195` ("First-60-day churn
traces to broken basics nobody owned — access, billing, introductions"), which
means it is **generated into the README skills table** by
`scripts/generate_readme_catalog.py` and is therefore a published repository
claim. The prior scorecard recommended deleting it
(`docs/audits/SKILL_SCORECARD_2026.md:282`); it is still there.

**The example contradicts the skill's own rule.** `SKILL.md:76-78` requires:
"if none known, a general community-channel intro, **never an invented
matchmaking rationale**". The example at `SKILL.md:157-158` then produces:

> "Intro: Kai (film) ↔ Grace at Charlie Content (media adjacency, from sales
> notes)"

The request at `SKILL.md:139-140` supplies no interests and no industry. The
example invents a media adjacency and attributes it to sales notes that do
not exist. Examples are what agents imitate. The prior scorecard flagged this
(`SKILL_SCORECARD_2026.md:158, 265`); it is still there.

**Hard-coded team-size threshold.** `SKILL.md:94`: "Team joins (5+ people):
add a team-lead sync task and stagger access setup". Unlabelled, unsourced,
not configurable. Enterprise research shows the real threshold is
operator-specific and product-specific: a corporate team of 15 may need a
lead sync (VenturePoint sets its corporate tier at 15+ employees,
https://venturepointsa.com/corporate-membership-lp/); a UK operator sets its
corporate threshold at 20+ employees or £2m turnover (The Createry,
https://thecreatery.co/corporate-memberships/); a small operator uses a 5-user
minimum (Den 1880, https://den1880.co/corporate/). Three operators, three
different numbers — which is exactly why 5 must be a default the operator can
change, not a rule.

**Off-by-one framing.** "Onboarding = the tasks between agreement signature
and the 30-day check-in" (`SKILL.md:56`) and "a failed first payment is the
worst first impression" (`SKILL.md:68`). The first is a definition (class C —
the repo's choice). The second is an unsourced ranking of harms.

**What the research says the operator actually needs** (see §6) — and the
skill's *structure* is right: dated, owned, verified tasks, with "no task
without an owner; no 'completed' status without evidence"
(`SKILL.md:108-110`). The structure survives; the framing and the thresholds
do not.

**Verdict: FIX (P1).**

---

### 4.5 PIPELINE — `coworking-pipeline-health` (stable)

**Four distinct problems.**

**(a) Hard-coded stage vocabulary with no operator override.**
`SKILL.md:55` documents "Open stages: new, qualified, tour, proposal,
negotiation." The engine's set is larger — `analyze.py:200-201`:
`{new, contacted, qualified, tour_booked, tour, tour_completed, proposal,
negotiation}`. Verified by probe: `contacted`, `tour_booked` and
`tour_completed` are *not* flagged invalid by the engine, so the skill
understates rather than misreports — but the SKILL.md list is wrong, and the
engine flags **any operator-specific stage** as `invalid_stage`. A probe with
a realistic `contract_sent` stage returned it as an invalid stage finding.
Real CRMs do not use this vocabulary: HubSpot's default stages are
New / Qualified / Discovery / Proposal / Negotiation; OfficeRnD Flex
opportunities have only **Lost / Open / Won**
(https://help.officernd.com/en/articles/248659-manage-opportunities,
2026-08-06). The skill's own SKILL.md says the operator profile supplies
"stage semantics" (`SKILL.md:51`) — but `pipeline_report()` accepts no
stage-name input, so in Mode 2 it cannot.

**(b) Two Mode 2 analyses the engine does not implement.** Verified by probe
against `src/opencoworking/analyze.py`:

- `SKILL.md:70`: "flag owners with >2× the median (overload risk)" —
  `pipeline_report()` returns `open_deals_by_owner` as raw counts
  (`analyze.py:253`) and computes **no median and no overload flag**. A grep
  for `median|overload` across `src/opencoworking/` finds only
  `median_minutes` for speed-to-lead.
- `SKILL.md:67-69`: "report stage-to-stage conversion with the definitions
  attached; identify the single largest drop-off stage by absolute count
  lost" — `funnel_report()` returns four lead-level rates
  (`analyze.py:288-293`: lead_to_contact, lead_to_tour, tour_show_rate,
  lead_to_won) and **no stage table at all**.

The skill is therefore Mode 1 prose for the two things the operator most
asks a pipeline audit to produce, and the catalog promises "workload"
(`catalog/skills.yaml:113`) that the engine does not deliver.

**(c) Duplicate detection is too coarse for real multi-requirement deals.**
The rule keys on `company_id + product` (`analyze.py:242-249`). Research
shows one company can legitimately have **simultaneous requirements for the
same product** — a private office in two cities, a second floor, a team
growing into a suite — so `company + product` will produce false
"duplicate open deals" for exactly the enterprise shape the library most
needs to serve. The skill's edge case (`SKILL.md:104-106`) only covers
"same company, different products/locations", which is the easy case.

**(d) No channel dimension.** Broker, aggregator, member referral and direct
inquiry are indistinguishable in the pipeline. That matters because the
research establishes the channel carries **material, contractual, recurring
cost and attribution risk** (see §6) and because broker-sourced tours are
**most likely to be missing from the CRM tour record** — which biases any
source-quality analysis against the commission-bearing channel.

**Verdict: FIX (P1).**

---

### 4.6 TECH STACK — `coworking-tech-stack-integration-audit` (beta)

**What is right, and it is a lot.** The skill is scrupulous about the one
external source it uses: the OfficeRnD 2026 report is quoted with its sample
size (334 operators; 1,276 accounts), and the skill says in the same
sentence "That is vendor research about OfficeRnD accounts, not a universal
census" (`SKILL.md:18`). `docs/research/SOURCES.yaml:255-280` records the
source with an explicit restriction: "Do not treat the percentages as an
industry census." The "core five" categories are stated as *chosen because
those are the public category leaders in that report*, not as a universal
stack model (`SKILL.md:54`). The engine refuses to force unknown categories
into a core bucket (`stack_audit.py:59-68`). This is the correct handling of
a vendor survey, and it is better than most of the library.

**The gap that matters: it is organised around vendor categories, not
business objects.** The audit asks "which tools do you use and are they
connected". The operator's real question is "**who owns the membership, and
where is it retyped?**" — and the skill can only answer that in Mode 1 prose
(`SKILL.md:62`: "State which system owns company, which owns the membership,
and which owns the invoice. If the file does not say, the answer is unknown").
The schema is `system, category, system_of_record, connected_to, id_quality,
manual_reentry, write_enabled` — one row per *tool*. There is no
**object** dimension at all.

Research establishes what a correct object-level audit must understand, with
current primary sources:

| Object | Reality | Source |
|---|---|---|
| **contact vs member vs company** | OfficeRnD's member table carries `status: "contact"` prospects *and* a `hubspot_link_id` external-ID custom property — member and contact are the same table | https://developer.officernd.com/docs/making-your-first-api-request |
| **agreement vs membership** | OfficeRnD `/memberships` is documented as "a list of sets of **day memberships**"; the agreement is a **separate** `/contracts` entity with its own scope and webhook family | https://developer.officernd.com/reference/memberships ; .../reference/contracts |
| **access entitlement** | Entitlement is **derived, not stored**: from passes, from resource bookings (~15 min before start), and from contracts. "Plans don't give access directly — they give access through the passes they include." A **paused** contract still exists but grants no desk access | https://learn.nexudus.com/integrations/access-control/overview.md |
| **access ≠ membership cancellation** | Coworks' own Verkada guide: "**Cancelling a membership will _not_ automatically revoke that member's Verkada access.** You would need to either deactivate the member in Coworks, or manually edit their access within Verkada." Bulk sync from plan allocations is "a manual process" | https://help.coworksapp.com/en/articles/13269396-how-to-use-the-verkada-access-control-integration, 2026-04-30 |
| **payment** | Three systems can each claim to be right: the gateway moves the money, the WMS holds the mandate and the auto-collect flag, the accounting system may record the payment. Direct debit settles in "at least 3 working days, and up to 12 working days for the first payment on a new mandate" | https://learn.nexudus.com/integrations/payment-gateways.md |
| **invoice → accounting** | "Nexudus stays where you issue invoices; the accounting system receives copies," transferred **every six hours**. If the billing/trading name does not match exactly, the accounting system **creates a new contact** and the invoices land there | https://learn.nexudus.com/integrations/accounting.md ; .../accounting/xero.md |
| **consent** | Marketing consent lives in the WMS, on a subscription toggle, and the public signup form renders a **pre-selected checkbox** if the default is left on | https://learn.nexudus.com/legal/gdpr.md |
| **webhook failure** | Nexudus webhooks **auto-disable after 10 consecutive failures**, silently | https://learn.nexudus.com/platform/settings/webhooks.md |
| **webhook ordering** | Optix: "We do not guarantee the sequencing or delay time of webhook delivery"; `new_lead` "has 1 hour delay, and it won't be triggered if a lead becomes an active member within that period" | https://developer.optixapp.com/using-webhooks/webhooks-list/ |
| **stripe** | "Stripe doesn't guarantee the delivery of events in the order that they're generated" | https://docs.stripe.com/webhooks |

The current audit **cannot check any of these**, because it has no row for
"the agreement", "the access entitlement", or "the invoice→accounting handoff".
Its findings are real but shallow: `category_absent`, `no_system_of_record`,
`manual_reentry`, `weak_ids`, `disconnected_core_system`, `high_risk_write`.

**Verdict: FIX (P2).** Add an object dimension. This is the single most
valuable structural upgrade available to an existing skill, and it needs no
new skill.

---

### 4.7 Cross-cutting: the unsourced-claim pattern

Across all 37 skills, the sweep classified **60+ industry-assertion
sentences** that are class E. The pattern is consistent and mechanical: an
opening "operator problem" paragraph states a belief about the world as
background, then the skill proceeds to do its real work correctly.

Representative examples (all verified at the cited lines):

| Skill | Line | Asserted | Why it is E |
|---|---|---|---|
| `coworking-post-tour-ghost-recovery` | 17-18 | "Tour ghosting is a **top-three coworking sales leak**" | A ranking claim about the industry with no source and no ledger entry. Prior scorecard recommended deletion (`SKILL_SCORECARD_2026.md:282`); still present. |
| `coworking-meeting-event-yield` | 18 | "Rooms are the **second revenue line** most operators can't quantify" | A ranking claim. (Note: GWA/Deskmag 2025 actually reports private offices generate the most revenue, then desk memberships, then meeting space — so the ordering is not even right.) |
| `coworking-collections-prioritizer` | 60-61 | "**card expiry is the modal cause**" | "Modal" is a statistical claim. The engine only says "the usual cause" (`wave2.py:631`). |
| `coworking-occupancy-revenue-dashboard` | 18 | "'We're 90% full but the bank account disagrees' is the **most common** coworking confusion" | A prevalence claim. Repeated in `catalog/skills.yaml:75`. |
| `coworking-unit-economics` | 18-21 | "Operators ask for 'the break-even occupancy' and get a **borrowed 70% from a blog**" | Embeds 70% as the canonical borrowed figure. No source. (`references/formulas/README.md` correctly declines to state any break-even.) |
| `coworking-renewal-preparation` | 163-164 | "suite re-listing timing (**60 days to fill 3,500/mo**)" | An invented fill-time statistic presented as fact — and it **contradicts** `coworking-occupancy-forecast/SKILL.md:85`, which promises no invented fill-time statistics. |
| `coworking-system-adapter-builder` | 20 | "every new platform request becomes '**edit all 24 skills**'" | **Factually wrong**: the repository ships 37 skills. |
| `coworking-lead-source-normalizer` | 84-85 | brokers/marketplaces "**usually carry fees that change ROI math**" | Currently E, but the research makes this **D** — see §6.2. This one should be *sourced*, not deleted. |
| `coworking-google-business-profile-audit` | 64-66, 76-77, 87-88, 137-140 | keyword-stuffing suspension risk, review gating, no stock photos, "Google restricts listings for addresses without staffed on-site service" | Google policy claims with no source and no ledger entry, in a skill whose own currency rule (`:43-46`) demands checking live guidance. |
| `coworking-lead-to-tour-diagnostic` | 89, 128-129 | "long lags between book and tour dates **predict no-shows**"; "**January and September spike, December dies**" | A predictive claim and a seasonality claim, both unsourced. |

**And the catalog repeats 28 of them.** `catalog/skills.yaml` re-uses the
same unsourced framing in the `problem:` field of at least 28 skills, and
because `scripts/generate_readme_catalog.py` generates the README skills table
from the catalog, **every one of those becomes a published repository claim**.
The highest-profile instance is `catalog/skills.yaml:195` (the first-60-day
churn premise).

**Verdict: FIX (P1).** The mechanical fix is: for every one of these
sentences, either (a) add a `SOURCES.yaml` entry and re-classify as D, or
(b) reword to remove the industry claim and keep the operator problem
(the skill still works — the paragraph is motivation, not mechanism).

---

## 5. Finding register

Ranked by risk. Each carries a class and a fix priority (P0–P4 as defined in
`IMPLEMENTATION_PLAN_V0.1.1.md`).

| # | Finding | Location | Class | Priority |
|---|---|---|---|---|
| **F-01** | `_product()` substring collision makes the `virtual_office` bucket **unreachable**; VO costs are silently merged into `office`, and "which product makes money" is wrong for any operator with VO revenue | `src/opencoworking/economics.py:28-33` | **A (wrong)** | **P0** |
| **F-02** | A skill that explicitly disclaims being a break-even model is *selected* by the break-even question and answers with a fixed-cost coverage figure that omits every variable cost | `coworking-unit-economics/SKILL.md:3, 26, 63`; `economics.py:108-125` | **M (A→C/E)** | **P0** |
| **F-03** | `product_contribution` compares cost bucketed by the operator's `product` label against revenue bucketed by `inventory.unit_type` — two taxonomies silently on one axis | `economics.py:70` vs `:93-94` | **A (wrong)** | **P1** |
| **F-04** | Four unsourced hard-coded churn windows (60-day cliff, 90-day payment, 14-day complaint, ≥3-member systemic) presented as indicator definitions; no engine; no labels | `coworking-churn-risk-review/SKILL.md:61, 63, 64, 99` | **E** | **P1** |
| **F-05** | "Notice given" is listed as a risk *indicator* and drives the "Act now" tier, conflating confirmed departure and known movement with predicted churn | `coworking-churn-risk-review/SKILL.md:62, 81-84` | **E** | **P1** |
| **F-06** | "Churn risk is highest in the first 60 days, and most early cancellations trace to broken basics" — unsourced, in a stable skill, **repeated in the catalog and therefore in the generated README table** | `coworking-member-onboarding/SKILL.md:17-19`; `catalog/skills.yaml:195` | **E** | **P1** |
| **F-07** | The onboarding example invents a matchmaking rationale that the skill's own workflow forbids | `coworking-member-onboarding/SKILL.md:157-158` vs `:76-78` | **E** | **P1** |
| **F-08** | The leakage audit's output contract names three totals (`billing_at_risk`, `pipeline_at_risk`, `idle_list_value`) that **do not exist in the engine**; `pipeline_at_risk` is not computable because `stale_open_deals_30d` carries no amount | `coworking-revenue-leakage-audit/SKILL.md:91-95`; `analyze.py:402-409, 511-513`; `catalog/skills.yaml:101` | **M (A→E)** | **P1** |
| **F-09** | Pipeline Mode 2 promises a >2×-median owner overload flag that the engine does not compute | `coworking-pipeline-health/SKILL.md:70`; `analyze.py:251-254` | **M** | **P1** |
| **F-10** | Pipeline Mode 2 promises stage-to-stage conversion and largest-drop-off identification that the engine does not compute | `coworking-pipeline-health/SKILL.md:67-69`; `analyze.py:281-303` | **M** | **P1** |
| **F-11** | Hard-coded stage vocabulary with no operator override; operator-specific CRM stages are reported as `invalid_stage` | `coworking-pipeline-health/SKILL.md:55`; `analyze.py:200-201, 219-222` | **C/M** | **P1** |
| **F-12** | 60+ industry-assertion sentences are class E; 28 of them are repeated in the catalog and become published README claims | all skills §4.7; `catalog/skills.yaml` | **E** | **P1** |
| **F-13** | "Tour ghosting is a top-three coworking sales leak" — unsourced ranking, stable skill | `coworking-post-tour-ghost-recovery/SKILL.md:17-18` | **E** | **P1** |
| **F-14** | Tech-stack audit has no **business-object** dimension, so it cannot answer "who owns the membership and where is it retyped" in Mode 2, and cannot check access-entitlement revocation or invoice→accounting handoff | `coworking-tech-stack-integration-audit/SKILL.md:42-63`; `stack_audit.py:10-19` | **C** | **P1** |
| **F-15** | "card expiry is the modal cause" — a statistical claim with no source; engine says only "the usual cause" | `coworking-collections-prioritizer/SKILL.md:60-61` | **E** | **P2** |
| **F-16** | Renewal-preparation example asserts an invented fill-time statistic ("60 days to fill 3,500/mo") that contradicts the occupancy-forecast skill's own promise | `coworking-renewal-preparation/SKILL.md:163-164` | **E** | **P2** |
| **F-17** | Utilization denominator is a flat daily scalar × every calendar day including weekends; vendors model operating hours, closed days and blackouts per resource | `coworking-meeting-event-yield/SKILL.md:97-100`; `wave2.py:783-786, 840-843` | **C** | **P2** |
| **F-18** | Unimplemented rules promised in SKILL.md across four skills: sub-3-unit low-volume label; >30% unpriced reliability note; >10% unpriced low-confidence label; sub-10-lead funnel gate | `coworking-discount-pricing-audit/SKILL.md:87, 109-110, 129-131`; `coworking-occupancy-revenue-dashboard/SKILL.md:113-115`; `coworking-multi-location-benchmark/SKILL.md:87` | **M** | **P2** |
| **F-19** | Speed-to-lead promises segmentation (≥10 per segment) with no engine support | `coworking-speed-to-lead-auditor/SKILL.md:81-84, 110`; `analyze.py:340-353` | **M** | **P2** |
| **F-20** | Lead-to-tour diagnostic promises nine checkpoints; the engine computes four, and its contact-rate definition differs from the skill's | `coworking-lead-to-tour-diagnostic/SKILL.md:60-78`; `analyze.py:288-295` | **M** | **P2** |
| **F-21** | Hard-coded 5-person team threshold in a stable skill; three real operators use 5, 15 and 20 | `coworking-member-onboarding/SKILL.md:94` | **C** | **P2** |
| **F-22** | "edit all 24 skills" — factually wrong, the repository ships 37 | `coworking-system-adapter-builder/SKILL.md:20` | **A (wrong)** | **P2** |
| **F-23** | Month-to-month is emitted as an ID list with no exposure figure; M2M is a distinct commercial shape with distinct economics and distinct commission treatment | `wave2.py:464, 474, 510-511` | **C** | **P2** |
| **F-24** | Leakage audit's 30-day and 45-day windows are hard-coded with no CLI flag, unlike `pipeline --stale-days` | `analyze.py:405, 440`; `cli.py:227` | **C** | **P2** |
| **F-25** | `coworking-system-adapter-builder`'s support ladder omits the `manual` rung that `docs/research/coworking-systems.md` defines and that `catalog/compatibility.yaml` assigns to 30 systems | `coworking-system-adapter-builder/SKILL.md:60-66, 113` | **A (wrong)** | **P2** |
| **F-26** | `coworking-churn-risk-review` promises Mode 2 via the package but names no command; the engine that computes its signals is `opencoworking renewals` | `coworking-churn-risk-review/SKILL.md:5, 41-43`; `wave2.py:463-513` | **M** | **P2** |
| **F-27** | `coworking-mcp-builder` output contract still asserts implemented code and still ships `stable` | `coworking-mcp-builder/SKILL.md:9, 122-127`; `catalog/skills.yaml:273-274` | **M** | **P2** |
| **F-28** | Renewal-preparation's batch trigger still competes with `coworking-renewal-expansion-risk` (both answer "renewals due next 90 days") | `coworking-renewal-preparation/SKILL.md:25-26`; `evals/cases.yaml:5` | **C** | **P2** |
| **F-29** | Ghost-recovery's only command eval re-runs the leakage audit rather than testing a sequence | `coworking-post-tour-ghost-recovery/evals/cases.yaml:47-55` | **A (weak)** | **P2** |
| **F-30** | Member-onboarding Mode 2 claims an audit of recent start dates with no command and no `compatibility:` line | `coworking-member-onboarding/SKILL.md:38-40` | **M** | **P3** |
| **F-31** | Catalog promises "expiring-promo list" that the discount skill explicitly refuses to produce | `catalog/skills.yaml:368` | **M** | **P3** |
| **F-32** | Catalog promises "segment patterns" (speed-to-lead) and "nine-checkpoint funnel localization" (lead-to-tour) the engine does not produce | `catalog/skills.yaml:126, 149` | **M** | **P3** |
| **F-33** | `daily_brief` role filter lists `unbilled_memberships` for owner and finance, but the class is never emitted — dead branch | `wave2.py:235-244` vs `:247-377` | **A (dead)** | **P3** |
| **F-34** | Google Business Profile policy claims (suspension risk, review gating, staffed-address restriction) with no ledger entry, in a skill whose own currency rule requires checking live guidance | `coworking-google-business-profile-audit/SKILL.md:64-66, 76-77, 87-88, 137-140` | **E** | **P3** |
| **F-35** | README says "29 known-answer eval cases"; the runner reports 31 | `README.md:44` | **A (stale)** | **P3** |
| **F-36** | `coworking-churn-risk-review` is `stable` despite a false Mode 2 claim and four unsourced thresholds | `coworking-churn-risk-review/SKILL.md:9` | **M** | **P3** |
| **F-37** | `coworking-mcp-builder` is `stable` while shipping a checklist | `coworking-mcp-builder/SKILL.md:9` | **M** | **P3** |
| **F-38** | 0 of 37 skills has field validation; `docs/OPERATOR_VALIDATION.md` exists but has not been run | `docs/OPERATOR_VALIDATION.md` | — | **P3** (process) |
| **F-39** | Pipeline duplicate detection keys on company+product, which flags legitimate simultaneous same-product requirements (multi-site, expansion) as duplicates | `analyze.py:242-249`; `coworking-pipeline-health/SKILL.md:104-106` | **C** | **P3** |
| **F-40** | Canonical `room_booking` entity carries no `status`, `booking_source` or `cancellation_reason`, so the meeting-yield exclusion path and any channel analysis cannot fire in practice | `schemas/coworking.schema.json`; `wave2.py:664-677` | **A (gap)** | **P3** |

---

## 6. Per-skill scorecard

**Scoring: 1 (poor) – 5 (excellent).** Criteria: **CS** coworking
specificity · **FA** factual/domain accuracy · **CFG**
configurable-vs-hardcoded logic · **PU** persona usefulness · **IR** input
realism · **EC** edge-case coverage · **DS** deterministic support ·
**OU** output usefulness · **TQ** test quality · **FV** field-validation
status.

**FV is 1 for every skill** because no skill has been run by an outside
operator. That is consistent with the repository's own definitions (stable =
complete, tested and reviewed; beta = complete and tested, not yet operator-
proven), so it is not a defect — it is the honest current state, and it is
the single largest constraint on promotion.

### 6.1 Stable skills (24)

| Skill | CS | FA | CFG | PU | IR | EC | DS | OU | TQ | FV | Verdict | Why |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `coworking-context-builder` | 4 | 4 | 4 | 5 | 5 | 4 | 2 | 5 | 4 | 1 | KEEP | Foundation; solid; Mode 2 under-built |
| `coworking-data-dictionary` | 5 | 4 | 4 | 5 | 5 | 4 | 3 | 5 | 4 | 1 | KEEP | Core anti-corruption step; mature |
| `coworking-source-verifier` | 5 | 5 | 4 | 4 | 4 | 5 | 3 | 5 | 5 | 1 | KEEP | The repo's own truth-keeper; prior fix closed |
| `coworking-pii-redactor` | 4 | 5 | 5 | 4 | 5 | 4 | 5 | 4 | 5 | 1 | KEEP | Tested, Luhn-validated; correctly scoped |
| `coworking-wms-export-analyzer` | 5 | 4 | 4 | 5 | 5 | 4 | 5 | 4 | 5 | 1 | KEEP | Deterministic entity detection; strong |
| `coworking-occupancy-revenue-dashboard` | 5 | 5 | 4 | 5 | 5 | 4 | 5 | 5 | 5 | 1 | FIX | F-18 (unimplemented low-confidence rule) |
| `coworking-monthly-owner-report` | 5 | 4 | 4 | 5 | 5 | 4 | 4 | 5 | 4 | 1 | KEEP | Prior fix closed (calls its commands) |
| `coworking-revenue-leakage-audit` | 5 | 3 | 2 | 5 | 5 | 4 | 4 | 4 | 4 | 1 | FIX | F-08 (three promised totals absent), F-24 |
| `coworking-pipeline-health` | 5 | 3 | 2 | 5 | 5 | 4 | 3 | 4 | 4 | 1 | FIX | F-09, F-10, F-11, F-39 |
| `coworking-speed-to-lead-auditor` | 5 | 4 | 5 | 5 | 5 | 4 | 4 | 5 | 5 | 1 | FIX | F-19 (segmentation absent) |
| `coworking-lead-source-normalizer` | 5 | 4 | 4 | 5 | 5 | 4 | 5 | 5 | 5 | 1 | FIX | F-12 (fee claim should be sourced, not deleted) |
| `coworking-lead-to-tour-diagnostic` | 5 | 3 | 3 | 5 | 4 | 3 | 3 | 4 | 3 | 1 | FIX | F-20, F-12 |
| `coworking-tour-preparation` | 5 | 4 | 4 | 5 | 5 | 4 | 2 | 5 | 4 | 1 | KEEP | Strong Mode 1; Mode 2 is manual by design |
| `coworking-tour-follow-up` | 5 | 4 | 4 | 5 | 5 | 5 | 2 | 5 | 5 | 1 | KEEP | Prior fix closed |
| `coworking-post-tour-ghost-recovery` | 5 | 3 | 4 | 5 | 5 | 5 | 2 | 5 | 3 | 1 | FIX | F-13, F-29 |
| `coworking-member-onboarding` | 5 | 2 | 3 | 5 | 5 | 4 | 2 | 4 | 3 | 1 | FIX | F-06, F-07, F-21, F-30 |
| `coworking-churn-risk-review` | 5 | 2 | 2 | 5 | 4 | 4 | 2 | 4 | 3 | 1 | FIX + DOWNGRADE | F-04, F-05, F-23, F-26, F-36 |
| `coworking-renewal-preparation` | 5 | 3 | 3 | 5 | 5 | 5 | 2 | 5 | 4 | 1 | FIX | F-16, F-28 |
| `coworking-local-seo-audit` | 4 | 3 | 4 | 4 | 4 | 4 | 2 | 4 | 4 | 1 | KEEP | SEO is inherently volatile; skill says so |
| `coworking-google-business-profile-audit` | 5 | 3 | 4 | 4 | 4 | 4 | 2 | 5 | 4 | 1 | FIX | F-34 (uncited Google policy claims) |
| `coworking-virtual-office-reconciliation` | 5 | 5 | 4 | 4 | 5 | 5 | 5 | 5 | 5 | 1 | KEEP | Strongest narrow skill; verified against engine |
| `coworking-cancellation-to-virtual-office` | 5 | 4 | 4 | 5 | 5 | 5 | 2 | 5 | 4 | 1 | KEEP | Sound; unsourced framing is class E but low-consequence |
| `coworking-mcp-builder` | 4 | 3 | 4 | 4 | 3 | 4 | 3 | 4 | 3 | 1 | FIX + DOWNGRADE | F-27, F-37 |
| `coworking-system-adapter-builder` | 5 | 3 | 4 | 4 | 4 | 3 | 2 | 4 | 4 | 1 | FIX | F-22, F-25 |

### 6.2 Beta skills (13)

| Skill | CS | FA | CFG | PU | IR | EC | DS | OU | TQ | FV | Verdict | Why |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `coworking-unit-economics` | 5 | **2** | 3 | 5 | 4 | 3 | 4 | 4 | 4 | 1 | **FIX (P0/P1)** | F-01, F-02, F-03 — the only P0 in the library |
| `coworking-tech-stack-integration-audit` | 5 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 | 1 | FIX | F-14 — highest-value structural upgrade available |
| `coworking-meeting-event-yield` | 5 | 5 | 3 | 5 | 4 | 4 | 5 | 5 | 5 | 1 | FIX | F-17, F-40 |
| `coworking-renewal-expansion-risk` | 5 | 5 | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 1 | KEEP | Engine verified line-by-line against the skill text |
| `coworking-occupancy-forecast` | 5 | 5 | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 1 | KEEP | Contracted-only layer, assumptions printed; verified |
| `coworking-discount-pricing-audit` | 5 | 4 | 5 | 5 | 5 | 4 | 5 | 5 | 4 | 1 | FIX | F-18, F-31 |
| `coworking-multi-location-benchmark` | 5 | 4 | 4 | 5 | 4 | 4 | 4 | 5 | 4 | 1 | FIX | F-18 (sub-10-lead gate not enforced) |
| `coworking-crm-wms-reconciliation` | 5 | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 4 | 1 | KEEP | Best-evidenced engine in the library; ID strategy is sound |
| `coworking-daily-operator-brief` | 5 | 4 | 3 | 5 | 5 | 4 | 5 | 5 | 4 | 1 | FIX | F-33 (dead class); windows not configurable |
| `coworking-collections-prioritizer` | 5 | 4 | 3 | 4 | 5 | 5 | 5 | 5 | 5 | 1 | FIX | F-15, F-24 |
| `coworking-ai-concierge-knowledge-audit` | 5 | 4 | 4 | 4 | 4 | 4 | 2 | 5 | 4 | 1 | KEEP | Prior strengthening (channels, escalation) closed |
| `coworking-data-migration-readiness` | 5 | 4 | 4 | 4 | 4 | 4 | 2 | 4 | 4 | 1 | KEEP | Honest about awaiting a real migration case |
| `coworking-operator-playbooks` | 5 | 5 | 5 | 5 | 4 | 4 | 4 | 5 | 4 | 1 | KEEP | Correctly refuses to fake a presale playbook (`:36`) |

### 6.3 Verdict summary

| Verdict | Count | Skills |
|---|---|---|
| **KEEP** | 24 | context-builder, data-dictionary, source-verifier, pii-redactor, wms-export-analyzer, occupancy-revenue-dashboard*, monthly-owner-report, revenue-leakage-audit*, pipeline-health*, speed-to-lead-auditor*, lead-source-normalizer*, lead-to-tour-diagnostic*, tour-preparation, tour-follow-up, post-tour-ghost-recovery*, member-onboarding*, churn-risk-review*, renewal-preparation*, local-seo-audit, google-business-profile-audit*, virtual-office-reconciliation, cancellation-to-virtual-office, mcp-builder*, system-adapter-builder*, renewal-expansion-risk, occupancy-forecast, discount-pricing-audit*, multi-location-benchmark*, crm-wms-reconciliation, daily-operator-brief*, collections-prioritizer, ai-concierge-knowledge-audit, data-migration-readiness, operator-playbooks |
| **FIX** | 32 | (all of the above marked \*, plus unit-economics and tech-stack-integration-audit) |
| **DOWNGRADE** | 2 | `coworking-churn-risk-review` (stable→beta), `coworking-mcp-builder` (stable→beta) |
| **PROMOTE** | **0** | see §8 |
| **MERGE** | 0 installed skills | 1 *planned* skill merges (§6.4) |
| **DEPRECATE** | **0** | no installed skill earns deprecation |

*(\* = KEEP-with-FIX: the skill's shape is right, the content needs work.)*

### 6.4 Planned catalogue re-rank (22 planned entries, per the brief's 10)

The brief asked for re-ranking of ten named planned skills against current
2026 evidence, not against old priority labels.

| Planned skill | Brief's label | Re-ranked | Recommendation |
|---|---|---|---|
| `coworking-broker-channel-manager` | to assess | **P1 — BUILD, narrowed** | Five executed operator programmes (WeWork TOS + USC Rider 2026-06-01; Industrious Commission Agreement; Expansive; Launch Workplaces TOS + fee agreement; e|spaces) plus two marketplace agreements (LiquidSpace Host Terms; Yardi CoworkingCafe operator agreement 2025-10-30) show a **recurring, mechanically regular object model**: registration → acceptance → attribution rule → fee basis → trigger → renewal/expansion → dispute window. Re-scope to *channel obligations & fee reconciliation*, not "relationship playbook". **No universal commission percentage exists** — sampled rates span ~5.8%–17% of TCV depending on term and basis unit. |
| `coworking-mail-operations` | to assess | **P1 — BUILD (beta)** | USPS DMM 508.1.8: an OBC with single-point delivery **is a CMRA**; 6-month remail floor; refusal prohibited; **client-instructed disposal inside the window is impermissible**. Object model converged independently at Traizr and Spacebring (item → instruction → status → action → usage). Needs a `mail_item` schema addition. |
| `coworking-proposal-builder` | to assess | **P1 — NARROW to `coworking-proposal-terms-check`** | The "builder" framing walks into R4 contract drafting. The buildable core is a **terms-completeness check + legal-boundary screen** (Restatement § 26 + *Bergquist*/*Dyno*), with the required-terms inventory sourced from OfficeRnD's contract model and the filed WeWork SEC exhibit. Note: **"Quote" is a built-in OfficeRnD contract type** — for OfficeRnD operators this duplicates a shipped feature. Proposal *prevalence* could not be sourced and must not be asserted. |
| `coworking-access-audit` | to assess | **P2 — BUILD** | The single most-documented cross-vendor failure in the research: "**Cancelling a membership will not automatically revoke that member's Verkada access**" (Coworks, 2026-04-30); Nexudus access is derived from passes/bookings/contracts and a **paused** contract still grants no desk access; Kisi cannot deliver desk/office access at all; the ACS webhook is a *full replacement* that fires on every update. Deterministic core: issued-vs-revoked credential diff. |
| `coworking-maintenance-tracker` | to assess | **P2 — BUILD, scope widened** | Absorb the member-service taxonomy and the explicit **do-not-automate community boundary** into it. There is **no** authoritative threshold for "recurring/systemic" — the three closest sources describe signals without a cutoff. Any default must be labelled a repo heuristic and be operator-configurable. |
| `coworking-feedback-loop` | to assess | **P3 — HOLD** | Adjacent to the offboarding exit interview and to member service. Needs the member-support taxonomy first. |
| `coworking-booking-flow-audit` | to assess | **P2/P3 — SPLIT** | The **catalog** version is a `website-conversion` friction rubric — that is a duplicate of `coworking-local-seo-audit` + `coworking-lead-to-tour-diagnostic`; **merge it** and fix the catalog category. The **operational** version (booking *outcomes*) is vendor-neutral and computable from the existing `room_booking` entity, but must be scoped to overlap / buffer / out-of-hours / no-show / channel, and must **never** claim credit-vs-cash reconciliation, minimum-duration compliance, or blackout enforcement — none of which is observable in any export. |
| `coworking-shift-handover` | to assess | **P4 — HOLD PLANNED, reframe** | There is **no coworking handover standard, artefact, or system of record** in any WMS, and no operator body publishes one. The only genuinely deterministic content would be a time-windowed state delta over data `coworking-daily-operator-brief` already ingests. Reframe as `coworking-shift-continuity`, R0, experimental — and only after three real operator artefacts from ≥2 operators exist. |
| `coworking-launch-plan` | to assess | **P2 — BUILD, but as a feasibility-adjacent skill** | The location-opening question is real and evidenced (Smartworks: 25–30% pre-committed at opening, 12 months to break-even, 30–32 months to payback; IWG: 19,000 rooms dropped from the pipeline when unopened 24 months post-signing). But **no skill may invent demand, absorption, or pricing.** This must be a cash-trough/underwriting model over operator-supplied inputs, or it must not exist. See GAP_RESEARCH. |
| `coworking-presale-pipeline` | to assess | **P2 — BUILD, coupled to launch-plan** | Same gate. The pre-opening occupancy projection must be bounded by *contracted* facts only, like `coworking-occupancy-forecast` already is. |

**Remaining planned skills** (`cohort-retention`, `deposit-reconciliation`,
`event-planner`, `win-back-campaign`, `waitlist-manager`, `listing-syndication-audit`,
`review-response-drafter`, `content-calendar`, `vo-compliance-checklist`,
`cm-training-builder`, `sales-script-coach`, `day-pass-upsell`) were reviewed at
lower depth. `cohort-retention` and `deposit-reconciliation` are prior-audit
endorsements and remain sound. The marketing/content cluster
(`content-calendar`, `sales-script-coach`, `review-response-drafter`,
`listing-syndication-audit`) is **down-weighted**: the research shows no
credible coworking CAC benchmark exists and no proposal-usage prevalence could
be sourced, so the marketing-economics cluster has the weakest evidence base
in the catalogue.

---

## 7. What is actually wrong vs. merely incomplete

### 7.1 Actually wrong (produces a wrong answer, or asserts a falsehood)

| Item | Why it is wrong, not incomplete |
|---|---|
| `_product()` maps virtual-office labels to `office` | The engine returns a demonstrably incorrect product mix. Verified by probe. Not "could be richer" — wrong. |
| "edit all 24 skills" | The repository ships 37. A false statement about the product itself. |
| Product contribution compares two different taxonomies | Cost by operator label vs revenue by `unit_type`, on the same axis. |
| Leakage audit promises three totals that do not exist | The output contract names deliverables the engine cannot produce; the catalog repeats it. |
| Pipeline Mode 2 promises a workload flag and stage-to-stage conversion that do not exist | Documented deliverables are absent from the deterministic path the skill advertises. |
| Discount / occupancy-dashboard / benchmark rules promised but not implemented | Same class of defect, smaller. |
| The onboarding example invents a rationale its own workflow forbids | The skill teaches the opposite of what it says. |
| "60 days to fill 3,500/mo" in the renewal-preparation example | An invented statistic contradicting the sibling skill's stated rule. |
| `coworking-system-adapter-builder`'s ladder omits `manual` | 30 systems in `catalog/compatibility.yaml` carry a label the ladder does not define. |
| `daily_brief`'s `unbilled_memberships` class | Never emitted — dead branch in a role filter. |
| The 60+ class-E industry claims | Asserted as fact with no source, in 28 cases published via the generated README table. This is a direct violation of the repo's own `AGENTS.md` rule 2. |

### 7.2 Merely incomplete (real gaps, honestly labelled, no wrong answers)

- No business-object dimension in the tech-stack audit (F-14).
- Flat utilization denominator instead of a real schedule (F-17).
- `room_booking` lacks `status`, `booking_source`, `cancellation_reason`
  (F-40).
- No broker/aggregator/referral channel dimension anywhere in the pipeline
  or funnel.
- No contribution-margin path in unit economics; no NOI/cash-flow/capex layer.
- No month-to-month exposure quantification.
- No object-level integration reality (direction, latency, retry, audit trail,
  write ownership) in the tech-stack audit.
- No field validation for any of the 37 skills.
- No offboarding workflow, no broker-channel skill, no mail-operations skill,
  no enterprise-requirements skill, no acquisition-cost skill, no
  location-feasibility skill (see `GAP_RESEARCH_2026.md`).

**Important distinction:** almost everything in 7.2 is a *scope* gap. The
skills that exist do not usually produce wrong answers about what they cover.
Almost everything in 7.1 is a *correctness or honesty* gap.

---

## 8. Release-safety assessment

### 8.1 Is the repository safe to promote while these issues are pending?

**Partially. It is safe to publish and use; it is not yet safe to *promote*
(badge stable / market as validated) without fixing the P0 and P1 items.**

The reasoning:

**In favour of releasing now:**
- The deterministic core is genuinely good. It prints its own numerators,
  denominators, exclusions and periods. It reports "not measured" rather than
  inventing. It treats imported data as data. It makes no network calls.
- The worst issues in 7.1 are **labelling and one mapping bug**, not
  architectural. There is no plausible path by which this library fabricates
  a market benchmark, a legal requirement, or a demand forecast — which is the
  failure mode that would actually hurt an operator.
- No skill is R2 or above. Nothing sends, charges, deletes, or revokes
  access. The blast radius of every defect found here is a wrong number in a
  report a human reads.
- The tests, validators, catalog check, link check and evals all pass. The
  dependency posture is clean apart from four stale Dependabot Action bumps.

**Against promoting:**
- One reproducible engine bug (F-01) makes a stated skill deliver a wrong
  product-mix answer.
- A stable skill is selected by a question it explicitly disclaims
  answering (F-02) — this is the one place where the library can mislead an
  owner making a pricing or lease decision.
- 28 unsourced industry claims are published in the README via the generated
  table (F-12) — a direct violation of the repository's own rule 2, and the
  kind of thing a technically-literate reviewer will check first.
- Zero field validation. Every skill's own version line or the beta
  definition says so, which is honest, but it means "stable" currently means
  "complete, tested and reviewed", not "proven".

### 8.2 Recommended release posture

1. **Do not expand the library** until the P0/P1 items are closed. Adding
   skills on top of an unresolved product-mix bug and 28 published
   unsourced claims compounds both.
2. **Land the P0/P1 fixes** (estimated in
   `IMPLEMENTATION_PLAN_V0.1.1.md`; the P0 items are a one-function
   substitution plus a regression test).
3. **Promote nothing to stable** until at least one operator has run the
   retention, sales and money chains end-to-end. The plan proposes a
   6-operator validation run rather than a promotion.
4. **Clear the four Dependabot PRs** before or with the release; they are
   three months stale.
5. **Do not deprecate anything.** No installed skill is net-negative, and
   several are the strongest artefacts in the library.

### 8.3 Confidence in this audit

| Area | Confidence | Why |
|---|---|---|
| Repository state, engine behaviour, doc/engine mismatches | **High** | Read from the tree at `d35e685`; probes executed against the shipped code |
| Classification of repo heuristics vs sourced facts | **High** | Every claim checked against `docs/research/SOURCES.yaml` |
| Industry reality (unit economics, churn, broker, mail, booking, enterprise) | **Medium-high** | Primary sources with URLs and dates; vendor sources labelled; sample limits recorded |
| Persona gap conclusions | **Medium** | Depends on absence-of-evidence arguments, which are stated as such |
| The absence of a credible coworking CAC benchmark | **High** | Searched across several phrasings; the largest flex dataset (OfficeRnD FlexIndex, 3,500+ locations) publishes six KPIs and none is CAC |

---

## 9. Recommended next actions

See `GAP_RESEARCH_2026.md` for the evidence-backed missing workflows, and
`IMPLEMENTATION_PLAN_V0.1.1.md` for the ranked fix plan and scope estimate.

**Summary of the recommended release:** P0 and P1 fixes are approximately
**4–6 working days** of focused engineering including tests, evals and
documentation. **Zero to three** new skills are recommended for the next
release, all P1, all narrowly scoped. The repository can be published and
used today, but the P0/P1 items should be closed before the skills are
promoted or marketed as validated.
