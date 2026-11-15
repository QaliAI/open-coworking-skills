# Gap research — 2026

**Repository:** `QaliAI/open-coworking-skills`
**Date:** 2026-10-20
**Companion documents:** `DOMAIN_REALISM_AUDIT_2026.md`,
`IMPLEMENTATION_PLAN_V0.1.1.md`

---

## 0. Method and admission rules

This document contains **only** missing workflows for which current primary
evidence establishes that (a) real operators have the problem, (b) the
problem is materially different from what an existing skill covers, and
(c) the required facts are obtainable from operator-supplied data or
operator-supplied documents.

**Admission rules applied:**

1. **Evidence, not plausibility.** A gap is admitted only with a source that
   establishes it. Where the evidence is a vendor's own operating reality
   (published terms of service, filed financial statements, own API
   documentation), that is stated as vendor-published, not as an industry
   norm.
2. **Absence of evidence is a finding, not an invitation.** Where a
   prevalence figure could not be sourced — coworking CAC, proposal usage,
   coworking handover standards — the gap is either scoped narrowly to
   operators who demonstrably have the artefact, or it is **not admitted**.
3. **The existing library gets the benefit of the doubt.** Each proposal
   names the specific existing skill that overlaps and states why that skill
   cannot absorb it. "It would be nice to have" is not a reason.
4. **No new skill may invent facts the operator did not supply.** Every
   proposal below names its refusal rules, and every refusal rule is about a
   class of output the operator cannot supply or verify.
5. **Forums are pain-point evidence only.** Reddit and Facebook threads
   appear below only to corroborate a pain that a primary source already
   establishes. They never establish a threshold, a formula, a legal
   requirement, or a benchmark.
6. **Hard limit: seven new skills.** This document proposes **three** for the
   next release and two for a later one. Zero would also be defensible.

---

## 1. Gaps admitted for the next release

### 1.1 `coworking-member-offboarding` — P1, beta, R1

**Operator pain.** A coworking departure is not one event; it is a
multi-system, multi-owner sequence with money at the end of it, and it is
the mirror image of the one workflow this library does cover well
(`coworking-member-onboarding`). The library currently has no skill that
owns it. `coworking-cancellation-to-virtual-office` owns only the *save
step*; `coworking-occupancy-forecast` and `coworking-churn-risk-review`
count departures; neither sequences them.

**Persona.** Community manager / front desk, with the operator and finance
holding the money steps.

**Evidence.**

| What it establishes | Source | Date |
|---|---|---|
| Offboarding is at least **three distinct write actions**, not one "cancel": end dates on all active memberships, end dates on all bookable resources, monthly plans made unavailable 30 days before cancellation, *and* invoice generation/charging switched off — the vendor explicitly warns that failing to switch off invoicing "may inadvertently charge your members" | https://help.officernd.com/en/articles/324741-offboarding-from-officernd-flex | 2025-12-04 |
| Cancelling a membership sets an End Date; on that date the membership becomes Terminated and the member becomes Former (unless they hold another active membership or their company is Active); **no pause function exists**; and the **deposit and setup fee are re-invoiced on a new membership unless deselected** | https://help.officernd.com/en/articles/248558-flex-cancel-or-pause-a-membership | accessed 2026-10-20 |
| **Credential state and account state are separate systems.** "A badge carries no account status — nothing that happens to a member's account, their access card or the directory reaches it." Disable is the reversible, record-preserving action; Delete destroys the record | https://offision.com/help/en/visiting/end-a-long-term-badge/ | 2026-10-03 |
| **Cancelling a membership will _not_ automatically revoke that member's Verkada access**; you must deactivate the member or edit access manually, and bulk sync from plan allocations is "a manual process" | https://help.coworksapp.com/en/articles/13269396-how-to-use-the-verkada-access-control-integration | 2026-04-30 |
| A major operator's own contract sets: notice periods of ≥1 month (month-to-month), ≥2 months (3-month term), ≥3 months (>3-month term); a fixed **office restoration fee on departure or relocation** plus repair fees above wear-and-tear; **partial months charged on a daily basis with a month = 30 × daily rate**; non-standard services charged **plus a 30% administration fee**; **deposit/service-retainer return within 30 days** after the agreement ends *and* the account is settled, with outstanding fees deducted; and **mail and packages received after termination are not held, not returned to sender, and may be disposed of without notice** | https://assets.regus.com/terms-and-conditions/en-us-global-terms-and-conditions.pdf | "Global Terms March 2026" |
| Notice **channel and timing are contractual**: 72 hours before the next billing anniversary by email for flex desks, 2 weeks for resident desks, 60 days by email for offices with a 90-day initial commitment, with the final charge collected on the last billing anniversary before the notice period ends | https://platformcoworking.com/refund | 2026-09-30 |
| **No single industry standard for deposits.** Typical amounts run ~$50 hot desk to $200–500 private office; many operators use one month of membership; deposits are a **liability, not income**, until applied; manual spreadsheet tracking is "where deposits get lost" | https://www.mydeskworks.com/blog/security-deposits-in-coworking-spaces-do-you-need-them | 2026-09-14 |
| The concrete failure modes: notice by email never logged with its date; end dates hand-calculated; sales learning about released inventory late; **fobs still working a month later**; members invoiced after leaving; deposit returns taking months; **no move-in condition record, so damage disputes cannot be settled** | https://spiderhunts.com/blog/coworking-member-notice-and-move-out | 2026-09-22 |

**Why the existing skills cannot absorb it.**

- `coworking-member-onboarding` is the mirror image: anchored to a start
  date, forward-only, and its audit mode looks *backwards at joiners*. Its
  structure (dated, owner-assigned, verified checklist) transfers; its
  anchoring does not. Merging would also push a stable R1 skill into R2
  territory because access revocation and status writes are irreversible.
- `coworking-churn-risk-review` is R0 *prevention* with an evidence list.
  Offboarding is *execution* with money. Merging would force churn-risk
  above its risk tier and blur "who might leave" with "who has left".
- `coworking-daily-operator-brief` can **emit** offboarding items
  ("access revocation due today", "deposit return overdue") but has no
  dependency chain, no agreement arithmetic, and no multi-system sequence.
- `coworking-collections-prioritizer` explicitly refuses deposit
  application. `coworking-access-audit` (planned) would own the credential
  *audit*, not the departure sequence.

**Minimum inputs.** Member or company ID; product type (hot desk /
dedicated desk / private office / team office / virtual office / day pass /
event-only / broker partner); **the agreement** or the operator's own notice
table (term type, notice period, effective-date rule, cure periods,
proration clause, deposit terms, restoration-fee clause, mail/address
clause); notice-received date and channel, or a confirmed end date; deposit
amount and status; list of credentials issued (badge / fob / app / PIN /
Wi-Fi / printing / locker); operator role map (which named role owns which
step); system list with which system is the system of record for contract
terms; operator's data-retention policy.

**Output.** (1) An end-date calculation that quotes the agreement clause and
shows the arithmetic. (2) A dated, owner-assigned task table with
dependencies, verification evidence, and the responsible role, expanded per
member type. (3) A final-invoice / deposit worksheet with amounts left blank
for human entry. (4) An access reconciliation — issued vs revoked, with
outstanding credentials listed. (5) A "decisions reserved for a human" list
(notice validity, deduction, credit, restoration charge, win-back offer, any
termination). (6) A "what the operator must supply" list for anything
unknown. (7) Four variants: single exit, team/partial-roster exit,
VO-only exit, breach/non-payment exit.

**Deterministic component.** End-date arithmetic from (notice-received date,
term, notice-period rule, billing anniversary) with the clause cited; task
date generation; the issued-vs-revoked credential diff; deposit ledger
reconciliation (paid − applied − refunded); per-member-type step selection;
and a consistency check on the **three-write trap** — billing stop date vs
final invoice date vs access end date.

**Key refusal rules.**
- No end date without the agreement text or the operator's own notice table.
  No default notice period.
- No judgement on notice validity, waiver, or whether an oral notice counts.
- No amounts: not deductions, credits, refunds, damage valuation, or
  restoration charges.
- No access revocation, mail forwarding, status write, or member
  communication without explicit human confirmation (R2/R3 boundary).
- No legal advice on deposits, retention, notice, or service of process.
- No promise that mail will be forwarded, returned, or held.
- No claim that member data is deleted on a fixed schedule.
- No fabrication of reasons for leaving.
- Operator-profile fields the operator has not supplied stay **unknown**.

**Proposed maturity.** `experimental` until the operator supplies a notice
table, role map and deposit ledger; `beta` once evals exist and one operator
has run it against a real departure. **Priority: P1.**

---

### 1.2 `coworking-mail-operations` — P1, beta, R1

**Operator pain.** A coworking front desk receives and re-dispatches mail
and parcels as a daily operational queue, and the workflow has a hard
regulatory floor that is invisible in most operators' own records.

**Persona.** Front desk / community manager.

**Evidence.**

| What it establishes | Source | Date |
|---|---|---|
| **A coworking space providing private offices with single-point mail delivery is legally a CMRA** for Postal Service purposes: "OBCs are considered CMRAs for Postal Service purposes and must comply with the requirements in 1.8" | USPS DMM 508.1.8, https://pe.usps.com/text/dmm300/508.htm (incorporated by reference at 39 CFR 111.1, https://www.ecfr.gov/current/title-39/chapter-I/subchapter-C/part-111/section-111.1) | current at fetch |
| A CMRA must remail for **at least 6 months** after the agency relationship terminates; the customer may opt out of forwarding but **may not instruct disposal or return-to-sender inside that window**; refusal of mail is prohibited for the whole window; at the end of the window only specified classes may be returned with a specific endorsement | same | same |
| PS Form 1583 per addressee (two forms of ID, one with photo); termination date written on the 1583 and entered in the USPS CMRA Customer Registration Database; endorsed 1583s retained 6 months; **quarterly certification due 15 Jan / 15 Apr / 15 Jul / 15 Oct**; non-compliant CMRAs get 30 days then delivery is suspended | same | same |
| **Two independent vendors describe the same operational object model**: item received and photographed → logged → client notified with the photo → client chooses scan / forward / shred / recycle / collect in person → staff record who did what and when → usage record updated with item, instruction, action and postage. Status vocabulary is `new` / `in progress` / `solved` at both | https://traizr.com/virtual-office-software/ ; https://www.spacebring.com/solutions/virtual-office-management-software | undated, fetched 2026-10-20 |
| A major operator's own policy: **no arrival notification for letter mail** (packages yes); packages collected within 30 days, letter mail within 60 days, after which it may be returned to sender at the member's expense, charged a storage fee, or **disposed of**; no forwarding unless contemplated in the membership agreement; couriers not permitted beyond the front desk | https://www.wework.com/legal/wework-membership-agreement-house-rules | updated 2025-09-24 |
| Other operators differ materially — one returns uncollected mail to sender, one does not forward at all, one carves out government/legal mail entirely — so the operator's own policy is the variable, not a universal rule | https://stakspace.com/membership-agreement/ ; https://2727coworking.com/virtual-mailboxes/ ; https://members.patch.work/legal/terms | fetched 2026-10-20 |
| Mail handling is a billable product in at least one major platform ("Storage lockers and mail handling" as a one-off, recurrent or event product; charges include credits applied and tax) | https://learn.nexudus.com/get-started/platform-overview/data-model-overview | undated |

**Why the existing skills cannot absorb it.**
- `coworking-virtual-office-reconciliation` covers **billing** against
  partner records. It has no item-level workflow and no instruction state.
- `coworking-member-onboarding` mentions mail setup for new members only.
- `coworking-vo-compliance-checklist` (planned) is **jurisdiction-specific
  compliance**, which is a different and separate skill — it must not be
  merged in, and this skill must refuse those questions.
- There is **no `mail_item` entity** in `schemas/coworking.schema.json`;
  the catalogue already names "Mail-event schema addition" as this skill's
  evidence gate.

**Minimum inputs.** A `mail_items` table (new canonical entity): item ID,
client/company ID, received date, item type (letter / parcel), sender,
photo reference, status, instruction (scan / forward / shred / recycle /
collect), instruction requested date, action taken, action completed date,
staff ID, postage cost, forwarding address, disposition. Plus `memberships`
(for termination dates and service level) and an **operator-supplied mail
policy**: collection window in days for letters and parcels, notification
commitment, disposal/return rule, forwarding rule, any government or legal
mail carve-out.

**Output.** (1) A daily worklist ordered by SLA urgency — items awaiting
client instruction, items awaiting staff action, items past the collection
window, items for terminated clients. (2) SLA breach flags. (3) Unclaimed
mail aging buckets. (4) A **post-termination handling report**: for each
terminated client with post-termination items, whether the operator's own
declared rule and the published six-month postal remail floor are in
conflict, or whether the outcome cannot be determined. (5) A coverage block
naming every check that could not run.

**Deterministic component.** Aging arithmetic; an instruction-vs-status
state machine (`new` → awaiting instruction → in progress → solved, with
closed-account as an orthogonal flag); collection-window breach detection;
post-termination window computation; conflict detection between the
operator's declared disposal/return rule and the six-month remail floor;
usage rollup per client (items received / scanned / forwarded / postage) as
counts — **not** money.

**Key refusal rules.**
- **Never** state whether the operator *is* a CMRA. Say: "if this address is
  a USPS-registered CMRA or an OBC with single-point delivery, the following
  published postal rule applies" and cite it.
- **Never** give legal advice, **never** state that an address is usable for
  registered agent or service of process, **never** interpret a statute.
- **Never** tell the operator to dispose of, return to sender, or refuse
  mail. Report what was done and what the operator's own policy says.
- **Never** assert a jurisdiction-specific rule.
- If a client has a service-of-process or registered-agent relationship,
  flag **do-not-touch** and escalate; do not apply the normal instruction
  workflow.
- Never handle or reproduce scanned mail contents; never carry a photo of an
  item into skill output beyond a reference.
- Never recommend a collection window. Report breach; the answer is the
  operator's.
- Do not fold in client billing. `coworking-virtual-office-reconciliation`
  owns the money.

**Proposed maturity.** `beta` (the object model is converged across two
vendors and the regulatory clock is citable; the log schema is new and
needs one operator run). **Priority: P1.**

---

### 1.3 `coworking-broker-channel-manager` (re-scoped) — P1, beta, R1

**Operator pain.** The broker, aggregator and referral channel carries
**material contractual cost and attribution risk** that no current skill
sees. The library mentions brokers only as an edge case: source-label
mapping (`coworking-lead-source-normalizer:84`), pre-qualified late leads
(`coworking-speed-to-lead-auditor:115`), "route via the broker" in follow-up
(`coworking-tour-follow-up:118-119`), and broker tours missing from the CRM
tour record (`coworking-lead-to-tour-diagnostic:130`).

**Persona.** Owner / GM (channel economics), sales manager (lead ownership).

**Evidence.** Five executed operator programmes and two marketplace
agreements were read in full; the object model recurs across all of them.

| What it establishes | Source | Date |
|---|---|---|
| Submission mechanics, conditional acceptance, client consent to pass contact details, fee base exclusions, **clawback** (broker returns fees if the client withdraws; if the member reduces space after move-in, the *member* owes), a **5-business-day dispute window** with waiver, and disqualification for false leads / misstating the broker's relationship / common-control referrals | https://wek8s-hydra-referrals-bucket.s3.amazonaws.com/en-US/broker-terms.pdf | "Final 8/1/26" |
| Banded commission with a **cap of the first 3 years per transaction**; month-to-month paid on **one month's fee, first month only, and only for the first deal in that market**; **relocation within the same market counts as a Renewal, not New Business**; invoicing must occur within 90 days or the fee is forfeited; payment triggered by the later of 60 days from bank details / 30 days from a compliant invoice / 30 days from receipt of the member's service retainer / start of the post-early-termination period | https://wek8s-hydra-referrals-bucket.s3.amazonaws.com/en-US/Regional+Rider+-+USC.pdf | "Final 6/1/26" |
| The operator is the **sole interface with the lead** and retains sole control over price, discount, collection, and execution of the agreement in its own name; commission is paid **only if the broker was the first entity to refer**; a **Qualified Lead expires 6 months after acceptance**; no commission for a lead previously submitted by another broker, for anyone who previously contacted the operator, or for an existing/past member | https://www.industriousoffice.com/broker-terms | agreement dated 2024 |
| A four-part payment trigger (executed agreement **and** first month + taxes + security deposit paid **and** member occupying **and** a valid broker invoice), renewal commission only "with active broker participation", and — where more than one broker is involved — "Launch Workplaces shall take direction from the member/prospect as to which broker shall be paid" | https://launchworkplaces.com/broker-program/ ; https://launchworkplaces.com/wp-content/uploads/2022/04/Broker-Terms-and-Conditions-.pdf | 2022-04-21 |
| **Marketplace tail fees.** LiquidSpace: a guest who clicked Message Host / Inquiry / Schedule a Tour in the past 6 months, or received a "Hot Lead", or had a prior Monthly Reservation that terminated within 6 months, triggers a **10% obligation for up to 12 months** on any resulting direct license agreement. Hourly service charge is 20% for LiquidSpace-originated guests and 10% for host-originated. The host pays the shortfall if charges exceed collections. Fee changes and cancellations **must be actioned through the platform** | https://www.liquidspace.com/terms/host-terms | last revised 2024-03-15 |
| A **15% live-booking fee** (operator receives 85%) and a **non-solicitation clause** restricting the operator from directly soliciting member-app members, plus a prohibition on using that member data for marketing | https://resources.yardi.com/legal/coworkingcafe/agreement-for-operators/ | version 2025-10-30 |
| An **occupancy-tiered** commission (20% at 0–33% full, 15% at 33–66%, 10% past 66%), a 24-hour operator decline right, and an explicit **no clawback** policy | https://www.upsuite.com/coworking-operator-faq/ | undated |
| **Commission rates are not comparable as percentages** because the units differ: e|spaces pays "2 months' rent" for a 12-month deal; WeWork pays 10%/5%/2.5% of monthly fees banded; Launch pays the greater of 10% of TCV for 12 months or 5% of TCV; Industrious pays 10% then 2%/mo. **No sampled primary source states a universal commission percentage.** | (above) | (above) |
| A material connection between an operator paying a broker and the broker's "review" of the space must be disclosed; the disclosure must clearly communicate the nature of the connection | 16 CFR §255.5, https://www.ecfr.gov/current/title-16/chapter-I/subchapter-B/part-255 | current at fetch |
| **No sampled primary source imposes a numeric tour or proposal SLA on the operator in the broker channel.** The only numeric windows are dispute windows and a 24-hour operator decline right. | (above) | (above) |

**Why the existing skills cannot absorb it.** No existing skill models
registration, attribution regime, fee basis, payment trigger, cap, dispute
window, renewal/expansion treatment, or marketplace tail exposure. The
catalogue already declares the hole: `coworking-operator-playbooks/SKILL.md:97`
says "Do not stretch a playbook to cover … broker commission math. Those
remain planned." The pipeline skill keys on company + product
(`analyze.py:242-249`) and has no channel dimension at all.

**Minimum inputs.** (1) **The operator's own channel terms file** — one
record per counterparty with the operative document, its date, and the
verbatim rule text for registration, attribution, fee basis and bands and fee
base, term, cap, renewal, expansion, payment trigger, invoice deadline,
dispute window, early-termination treatment, exclusivity, non-solicitation
and confidentiality. **Without this file the skill must refuse to compute
any fee.** (2) A channel/lead table in canonical columns: channel ID,
counterparty type (broker / marketplace / aggregator / reseller / member
referral / vendor referral), counterparty name, lead ID, submitted date,
accepted date, expiry date, requirement summary, tour dates, operator
account or member ID, membership start, contract term, contracted monthly
fee, discount, list price, fee basis as stated, fee computed, fee invoiced,
fee paid, trigger evidence (signed / first payment / move-in / retainer),
renewal events, expansion events, dispute notes. (3) As-of date and reporting
period. (4) Counterparty invoices or reports (optional but decisive).

**Output.** (1) A **channel register** — per counterparty: role class,
agreement and date, rule citations, fee basis verbatim, trigger, renewal
and expansion treatment, cap, confidentiality flag. (2) An **attribution
reconciliation** — per lead: who submitted, who the agreement says is owed,
what the CRM says, conflict flag, expiry and house-lead status. (3) A
**commission ledger** — expected (per the agreement) vs invoiced vs paid,
with the rule text attached to each row; variance lines; clawback and
recapture exposure flagged. (4) A **marketplace tail-fee exposure** report —
per member, whether a platform-claimed window applies *under that
platform's stated rule*, labelled "your agreement says X", never "you owe X"
as a market fact. (5) **Net-of-fee performance per channel**, each figure
carrying numerator, denominator, exclusions and period, reconciling to a
stated rule, with disagreements surfaced as findings.

**Deterministic component.** Fee computation from the operator's own stated
basis (rate, band schedule, fee base, cap, term) against expected vs
invoiced vs paid; attribution conflict detection against the operator's own
attribution rule; expiry and house-lead determination from the operator's
own windows; tail-window determination from the operator's own platform
agreement; net-of-fee arithmetic per channel per period.

**Key refusal rules.**
- **Without the operator's own agreement, refuse to compute any fee.** Never
  substitute a market rate, a benchmark, or another operator's programme.
- **Never set, recommend, or "fair" a commission rate.** It is the
  operator's commercial term.
- Never state what a platform "owes" the operator or what the operator
  "owes" a platform as a market fact; only what the operator's own
  agreement says.
- Never determine contract terms, legal obligations, or the effect of a
  dispute-window waiver; route to the operator's counsel.
- Never merge with a broker's own client relationship or imply the operator
  may contact a referred client directly where the agreement forbids it.
- Do not include counterparty-confidential agreement terms in any output
  that leaves the operator's system; treat the terms file as confidential.
- Never produce a "relationship playbook" or etiquette guidance; that is
  not derivable from evidence.

**Proposed maturity.** `beta` once the terms-file schema and the commission
ledger have known-answer fixtures against at least one operator's own
agreement. **Priority: P1.**

**Mandatory re-scope.** The catalogue's current description ("Per-channel
net-of-fee performance and **relationship playbook**") must change. The
"relationship playbook" output is opinion, not evidence, and would violate
the library's own rules. Replace it with "channel obligations checklist,
every item quoted from the operator's own agreement."

---

## 2. Gaps admitted for a later release

### 2.1 `coworking-location-feasibility` (underwriting) — P2, experimental, R0

**Operator pain.** The library's coverage is almost entirely backward-looking
(what happened, what is contracted) and is explicitly incomplete on
forward-looking location decisions. `coworking-operator-playbooks/SKILL.md:36`
says so: "A new location or presale plan. Those skills are still planned. Say
so. Do not fake a launch playbook."

**Persona.** Owner / GM, investor, landlord, and a consultant underwriting a
site.

**Evidence.**

| What it establishes | Source | Date |
|---|---|---|
| A real operator's stated centre lifecycle: **pre-committed occupancy at opening of 25–30%** ("standard with most of our new centres"), **12 months to 65–70% occupancy and break-even**, and **30–32 months to recover the entire payback**; pre-leasing 20–25% before committing to a building | Smartworks IPO earnings call, https://d14ooopotgqw8y.cloudfront.net/uploads/Transcript_Earnings_Call_12082025_3b20f5fd61.pdf | call 2025-08-12 |
| The same lifecycle as an annual-report diagram: "operational cost breakeven during the transition from developing to mature… Any incremental utilisation beyond this point flows entirely to unit-level profitability"; capex is a real line (maintenance capex ~6–8% of gross block, ~12–15% of initial capex per sf) | Smartworks FY2025-26 Annual Report, https://nsearchives.nseindia.com/annual_reports/AR_31688_SMARTWORKS_2025_2026_A_18887547_07092026161734.pdf | 2026-09 |
| **Accounting profit ≠ cash.** Under Ind AS 116 (≈IFRS 16) lease accounting "mechanically inflates reported EBITDA… relative to a cash-cost view"; FY26 free cash flow was **negative** (≈−Rs 31.5 crore) despite positive EBITDA; DSCR 0.82× | same; https://www.multibagg.ai/market-pulse/articles/smartworks-fy26-93183 | 2026 |
| A listed flex operator's own cash bridge: Adjusted EBITDA $531m → less depreciation of landlord contributions, working capital, **maintenance capex** → cash flow from operations → growth capex → cash inflow before corporate activities; **99% of new centre deals were capital-light** | IWG plc Annual Report 2025, https://investors.iwgplc.com/~/media/Files/I/IWG-IR/reports-and-presentations/2026/iwg-annual-report-2025-16-03-2026.pdf | 2026-03-16 |
| Ramp slower than plan is the norm: RevPAR at 18 months "slightly slower than the original 18 month expectations", and **19,000 rooms were dropped from the pipeline when unopened 24 months after signing** | IWG Investor Day, https://investors.iwgplc.com/~/media/Files/I/IWG-IR/reports-and-presentations/2025/iwg-Investor-day-presentation.pdf | 2025-12-04 |
| The **cash-vs-accounting distinction** is explicit in the market's own underwriting product: 60 months of monthly NOI with the running total beneath it, "how deep the space goes, the month it turns, and the month the early losses are earned back"; stress test levers are the rent the floor carries, the free months, and the office prices; yield-on-cost compares stabilised NOI to total project cost | https://coworkingconsulting.com/decide/ ; https://coworkingconsulting.com/flex-space-pro-forma/ | undated (vendor marketing — establishes the *shape* of the deliverable, not a benchmark) |
| **Pricing is a market output, not an owner input**: "if comparable flex spaces in the trade area are priced at $350 per desk and your cost structure requires $500, no amount of design quality closes that gap"; three-part test — does local demand exist at the density this model requires, does the asset support the experience the market expects, does local pricing support the margin the buildout creates | https://www.denswap.com/blog/are-coworking-spaces-profitable-real-info-for-cre-owners-2026 | 2026-03-17 |
| The standard three-case occupancy stress frame: best 85% / expected 70% / worst 50% | https://www.loopnet.com/cre-explained/investing/how-much-does-it-cost-to-open-a-coworking-space/ (2025-12-12) and .../is-coworking-real-estate-profitable/ (2025-11-07) | 2025 | 
| The coworking-specific cost taxonomy: fixed (rent/debt service, CAM minimums, property taxes, building insurance, buildout and TI, FF&E, core IT and cabling, access control, salaried staff, long-term service contracts) and variable (cleaning tied to occupancy, utilities, coffee and consumables, marketing, printing, part-time staffing, events, usage-scaled maintenance, payment processing); contingency 10–15% of buildout; 3–5% of monthly revenues held as capital reserves; "12 to 18 months of negative cash flow before you hit break-even occupancy" | https://www.loopnet.com/cre-explained/investing/how-much-does-it-cost-to-open-a-coworking-space/ ; .../is-coworking-real-estate-profitable/ | 2025 | 
| Lease-versus-member-commitment mismatch is "the core risk of the coworking model": 5–10 year operator leases against month-to-month or annual member memberships | https://www.coworks.com/blog/the-coworking-operators-glossary-of-commercial-real-estate-terms | 2026-06-11 |
| Flexible-office inventory and pricing context: US flexible office inventory **+18% YoY as of Q2 2026**, **3.1% of total US office inventory**, suburban locations +39% (2024–2026) vs urban +22% | https://www.cushmanwakefield.com/en/united-states/news/2026/10/global-trends-in-flexible-office-2026---us | 2026-10-13 |
| 9,384 active US coworking locations, 166.36 Msf, median membership $219, meeting room $45, virtual office $169, day pass $34; the top 5 brands are ~23% of locations and ~77% are independents | https://www.coworkingcafe.com/blog/national-coworking-report/ (Q2'26) | 2026-07-23 | 
| Enterprise demand shape: 89% of employers require ≥3 days/week, but **actual average attendance is 2.9 days against a 3.2-day target**; 73% of organisations hit effective capacity on peak days while only 34% do on average days | https://www.cbre.com/insights/reports/2026-americas-office-occupier-sentiment-survey (2026-07-30); https://www.cbre.com/insights/reports/2025-americas-office-occupier-sentiment-survey (2025) | 2026 / 2025 |
| Hybrid work share is the structural ceiling: 52% hybrid, 26% exclusively remote, 22% on-site; hybrid workers average ≈2.3 days in office per week | https://www.gallup.com/401384/indicator-hybrid-work.aspx | data 2026-05 |

**Why the existing skills cannot absorb it.** `coworking-unit-economics`
answers a fixed-cost coverage question for an **operating** location and
explicitly disclaims being a break-even model. `coworking-occupancy-forecast`
projects **contracted** occupancy forward and is correct to include no
pipeline. Neither models a build-out, a lease, a ramp, a cash trough, or a
payback. `coworking-launch-plan` (planned) is a launch *timeline*, not a
financial model.

**Minimum inputs.** All operator-supplied, no inference: location size and
sellable inventory by type; lease terms (base rent, escalation, free/abated
months, TI allowance or turnkey, restoration obligation, deposit or LC,
personal guarantee, operating expense or CAM treatment); build-out budget by
line (hard cost, soft cost, AV, IT, furniture, contingency) and duration;
opening payroll and pre-opening costs; working-capital reserve policy; target
price sheet by product; committed and pre-sold memberships at opening with
their dates; marketing launch budget; the operator's own required return
(DSCR, cash-on-cash, payback months) if any; and — **separately and
explicitly** — the operator's own comparable pricing evidence for the trade
area, which the skill must accept as an input rather than source itself.

**Output.** A **monthly cash-flow model** over the operator's horizon: rent,
other fixed costs, variable costs, contracted revenue by product, capex and
TI draws, pre-opening costs, and the resulting cash balance; the **cash
trough** (its month and depth); **operating break-even month** and
**capex payback month** reported separately; contribution margin per product;
and a **sensitivity table** over the operator's own stated levers (rent,
free months, build-out cost, ramp speed, price, occupancy). Every figure
carries numerator, denominator, exclusions and period.

**Deterministic component.** Monthly cash-flow arithmetic; trough detection;
break-even and payback month detection with the two reported separately;
contribution per product; one-way sensitivity over operator-supplied levers.

**Key refusal rules.**
- **Never** invent or source demand, absorption, pricing, or a market
  occupancy benchmark. Where the operator has not supplied a comparable
  pricing input, the price line is *not modelled* and the skill says so.
- **Never** report a single "break-even occupancy" figure. Report the
  operating break-even month, the cash trough, and the payback month
  separately, because they are different answers and the market's own
  operators report all three.
- Never annualise a lease term's rent without stating the escalation
  assumption the operator supplied.
- Never treat accounting break-even as cash break-even; if the operator
  cannot supply lease-accounting treatment, report pre-lease cash and label
  it.
- Never present an operator's own target return as the market's requirement.
- Never model a pipeline as demand. Contracted and pre-sold only; scenarios
  are labelled scenarios.

**Proposed maturity.** `experimental` — it requires the operator to supply a
lease and build-out model before it can produce anything, and there is no
operator case yet. **Priority: P2.** If Phase B does not reach it, it is
correct to defer rather than ship a partial version.

---

### 2.2 `coworking-acquisition-cost-review` — P2, beta, R0

**Not** an attribution model and **not** a channel-ROI tool. See §4.

**Operator pain.** `coworking-lead-source-normalizer` normalises labels and
explicitly refuses to judge channel quality; `coworking-lead-to-tour-diagnostic`
localises funnel breaks. Neither accepts a spend file. Yet
`references/formulas/README.md:72-73` already *defines* CAC ("marketing +
sales spend in period / new customers won in period. Requires spend data;
without it, skills must not estimate it") and no skill implements it.

**Persona.** Owner / GM, marketing lead.

**Evidence.**

| What it establishes | Source | Date |
|---|---|---|
| **There is no credible coworking CAC benchmark.** The largest flex dataset (3,500+ locations) publishes six KPIs — Revenue Occupancy 74.49%, Desk Occupancy 73.05%, Private Office Occupancy 71.34%, RevPOD $520.15, RevPAD $379.98, Price/Hour $44.38 — and **none is CAC or marketing spend** | https://www.officernd.com/blog/coworking-statistics/ (FlexIndex Q4 2025) | 2026-02-19 |
| Member acquisition is the **largest** operator challenge by far | GWA/Deskmag 2025, https://deskmag.com/en/coworking-spaces/2025-global-coworking-space-trends-europe-north-america-market-business-survey-analysis-report | 2025-05-19 |
| Channel economics are **contractual and large**, and **not one thing**: LiquidSpace charges 20% of collected fees on hourly bookings for platform-originated guests and 10% for host-originated, plus a 10% monthly fee on monthly reservations, plus a 12-month tail on qualifying off-platform agreements | https://www.liquidspace.com/terms/host-terms | 2024-03-15 |
| Yardi's CoworkingCafe operator agreement imposes a **15% live-booking fee** and premium listing fees | https://resources.yardi.com/legal/coworkingcafe/agreement-for-operators/ | 2025-10-30 |
| Broker programmes pay 10%/5%/2.5% of monthly fees banded over three years, or 2% of net membership fee on renewals — a recurring tail, not a one-time cost | WeWork USC Rider 2026-06-01; Industrious broker terms (see §1.3) | 2026 / 2024 |
| Referral economics are two-sided: referrer credits of $50–$500 **and** a separate referee credit, payable only after 3–6 months of tenure, and "if the referred person or team is already in contact with a broker, we will not honor the referral" | https://www.thrive-canton.com/referral-thrivecanton ; https://shiftworkspaces.com/referral-program/ | undated; 2024-12-17 |
| **Gross contracted revenue ≠ collected revenue**: domestic card is 2.9% + 30¢, ACH 0.8% | https://stripe.com/pricing | current at fetch |
| A coworking source field is **single-touch and self-reported**: OfficeRnD Flex has no built-in source field — "Source" is a user-created String custom property, and opportunity statuses are only 0% Lost / 10% Open / 100% Won | https://help.officernd.com/en/articles/248659-manage-opportunities ; .../249178-community-glossary | 2026-08-06; 2025-01-07 |
| **Causal claims from observational source data are not supportable.** Across 25 large field experiments, "selection bias, due to the targeted nature of advertising, is a crippling concern for widely employed observational methods"; median campaign sizes needed are 9× for a profitability read and 62× for a 10% ROI tolerance | Lewis & Rao, "The Unfavorable Economics of Measuring the Returns to Advertising", QJE 130(4):1941–1973, https://ungated.research.bowdoin.edu/article/2601 | November 2015 |
| Observational methods "often fail to produce the same effects as the randomized experiments, even after conditioning on extensive demographic and behavioral variables" | Gordon et al., "A Comparison of Approaches to Advertising Measurement: Evidence from Big Field Experiments at Facebook", https://www.kellogg.northwestern.edu/faculty/gordon_b/files/fb_comparison.pdf | 2018-04-12 |
| Payback without gross margin is a **revenue-recovery period**, not a payback; LTV:CAC "can look excellent while cashflow is broken" | https://www.maxio.com/saaspedia/cac-payback | undated |

**Why the existing skills cannot absorb it.**
`coworking-lead-source-normalizer` is deliberately scoped to label hygiene
and says so ("Judging channel quality (that's pipeline/funnel work AFTER
normalization)"; "Attribution modeling — out of scope. This skill cleans
labels, it does not re-attribute"). `coworking-lead-to-tour-diagnostic` is a
funnel-break localiser whose entire logic is "find the FIRST broken
checkpoint" — cost is not a checkpoint, and adding it would confuse the
causal ordering it depends on. `coworking-unit-economics` accepts a cost file
but answers an occupancy question from a *fixed-cost* file, and its rules
forbid reading typical costs from the market.

**Minimum inputs.** A named **spend file**: period, one row per cost line,
amount, category, and gross-vs-net of tax, with categories separating at
minimum paid media / agency / marketplace commission / broker commission /
referral credit / event / content / other; a `channel_class` (paid |
commission-bearing | per-referral | shared-brand | unallocated) and a
`cost_basis` (cash | credit | offset — referral credits are opportunity cost,
not cash; marketplace commissions are net-of-gross); a **denominator
definition** (new memberships started vs new companies vs new contracts vs
net new members, and any size threshold); **stated exclusions** (expansions,
reactivations, transfers, internal memberships, comped memberships, and
whether sales labour is included); a **cohort period and look-back window**;
a **revenue definition** (contracted MRR / first-year contract value /
collected cash) and, for a true payback, a gross margin figure; and a
**volume floor** for any per-channel figure.

**Output.** (1) A **pooled acquisition cost** with the denominator,
exclusions, cohort, window and period printed on the face of the number.
(2) A **fee-aware channel table**: per canonical source bucket, the directly
attributable fees and spend, the number of new members naming that bucket,
and cost per member — each row carrying the single-touch caveat.
(3) A **revenue-recovery period**, and a payback period **only if margin was
supplied** — otherwise the metric is relabelled. (4) A **hypothesis queue**,
not conclusions: for each unanswerable question (dark social, branded
interception, multi-touch), the named question and the cheapest test that
could answer it.

**Deterministic component.** Cost-line classification and totals; pooled
cost per new customer with exclusions applied; fee-aware per-bucket cost per
member; revenue-recovery and payback arithmetic on the operator's declared
revenue and margin basis; cohort/window join.

**Key refusal rules.**
- No CAC without a named spend file. No "typical coworking CAC", no proxy, no
  back-solve from revenue.
- No per-channel CAC where spend and members cannot be joined to the same
  cohort and window.
- No LTV:CAC ratio without a sourced lifetime basis and a churn base.
- **No causal language.** Not "ads brought in N members", not "SEO has our
  best ROI", not "referrals convert better than paid search".
- No comparison to a published benchmark, and **no quoting a SaaS payback
  median as a coworking target**.
- No blended CAC presented without its denominator definition.
- No payback without gross margin.
- No treatment of a missing cost line as zero. No treatment of the
  operator's own time, events, content, or landlord co-marketing as zero.
- No platform-reported conversion count treated as a member count.
- No per-channel figure where the channel has fewer than 10 new customers in
  the window.

**Two cheap extensions to existing skills, in place of a new skill, where
possible:** add a `cost_class` attribute to the canonical source buckets in
`normalize.py` (commission-bearing / per-referral / paid-media /
shared-brand / no-fee-known / unknown), and add a cost-class annotation plus
a broker caveat to checkpoint 8 of `coworking-lead-to-tour-diagnostic` —
because broker-sourced tours are the ones most likely to be missing from the
tour record, which biases source-quality analysis *against* the
commission-bearing channel.

**Proposed maturity.** `beta`. **Priority: P2.**

---

## 3. Gaps deliberately NOT admitted

### 3.1 A dedicated member service / service-recovery skill — NOT ADMITTED as a new skill

The pain is real and evidenced (complaint taxonomy, service-recovery steps,
the fact that issues raised by email or at the desk produce no trend data,
unclear escalation paths). But:

- `coworking-maintenance-tracker` (planned) already owns the ticket /
  work-order domain, which covers roughly 12 of the 16 taxonomy rows.
- `coworking-feedback-loop` (planned) owns feedback capture;
  `coworking-cm-training-builder` (planned) owns service-recovery training;
  `coworking-access-audit` (planned) owns access reconciliation.
- The service-recovery *chain* (acknowledge → triage → assign → commit →
  close → detect recurrence → escalate) is generic service-management
  practice documented across three independent sources, not a
  coworking-specific method. A coworking-specific skill would mostly restate
  vendor content.

**Recommendation: widen `coworking-maintenance-tracker` instead.** Add the
member-facing intake taxonomy (issue → typical owner → recurrence signal →
automatable vs human-only) and the explicit do-not-automate community
boundary to its front half when it is built. Note: **no authoritative
source supports a specific number** for classifying an issue as
"recurring" or "systemic" — the three closest sources describe the signals
without a cutoff. Any default must be labelled a repo heuristic and be
operator-configurable.

### 3.2 An attribution / multi-touch / MMM / incrementality capability — NOT ADMITTED

There is nothing to model. The mainstream models are collapsing (GA4
deprecated first-click, linear, time-decay and position-based in November
2023, leaving three models, all of which exclude direct traffic from credit),
the data does not exist (a WMS holding one source string per record cannot
reconstruct a path), and the causal layer is unaffordable (informative
experiments need >10M person-weeks). A skill producing "channel ROI" from a
single self-reported field would violate `coworking-lead-source-normalizer`'s
own contract and `coworking-source-verifier`'s fact/assumption separation.

### 3.3 A dedicated enterprise-sales skill — NOT ADMITTED as a new skill yet

The need is real and large: corporates are 47% of flex occupancy worldwide,
up from 13% in 2020; enterprise buying is driven by speed to occupancy,
capex avoidance, headcount mismatch and mobility, with security and data
privacy outweighing conventional perks; a master contract with per-site
coverage, cost-centre billing, role-based entitlements, a pilot with KPIs and
a named account manager is a different product from a desk membership; and
"a member" can be one agreement covering 150 people, so any analysis that
silently conflates people, seats, agreements and bookings is wrong by orders
of magnitude.

But the buildable content is a **requirements-coverage matrix** (requirement →
why it matters → captured where → sign-off owner → status), and that
requires the operator's own requirements and inventory to be useful. It also
overlaps materially with `coworking-tour-preparation` (requirements and
inventory matching) and `coworking-unit-economics` (product contribution and
pricing). **Recommendation:** add an enterprise requirements checklist as a
section of `coworking-tour-preparation` when enterprise volume appears in
real usage, and re-evaluate at that point. Do not build a standalone
"enterprise sales" skill now — it would be a content skill that drifts.

### 3.4 `coworking-shift-handover` — NOT ADMITTED to build

There is **no coworking handover standard, no artefact, and no system of
record** in any coworking WMS (targeted searches across Optix, Nexudus,
Coworks, OfficeRnD, Spacebring and Archie returned nothing), and no operator
body publishes one. The only genuinely deterministic content it would add is
a time-windowed state delta over data `coworking-daily-operator-brief`
already ingests — which is the duplication argument that killed the "member
support triage" idea in the 2026 gap analysis. If built later, it should be
`coworking-shift-continuity`, R0 read-only state-delta, experimental, and
only after three real operator handover artefacts from at least two operators
exist. **Do not build a "generate a handover note" skill** — it has no
testable artefact and no export.

### 3.5 `coworking-booking-flow-audit` as currently described — NOT ADMITTED; MERGE + SPLIT

The catalogue's current entry is categorised `website-conversion` with a
friction-rubric brief ("flow walkthrough … step-by-step friction findings
with field-level fixes"). That is a manual rubric with no deterministic
component and no canonical model, and it duplicates `coworking-local-seo-audit`
(which already owns conversion checks) and `coworking-lead-to-tour-diagnostic`
(which already owns funnel failure-mode separation).

**Recommendation: merge the catalogue version into those two skills today
and fix the category.** The *operational* need — booking **outcomes** — is a
genuinely different and vendor-neutral skill, computable from the
`room_booking` entity the repo already has: interval-overlap detection per
room, buffer-gap detection, out-of-hours detection against an operator-declared
schedule, no-show rate from a cancellation-reason field, and channel mix from
a booking-source field. It must be scoped to exactly those, and must **never**
claim credit-vs-cash reconciliation, minimum-duration compliance, blackout
enforcement, or calendar-sync integrity — none of which is observable in any
export, and the first of which the repo has already proven is not separable
from a booking export. Gate on: extending `room_booking` with `status`,
`booking_source` and `cancellation_reason` from a **documented** vendor export
field list; an operator-supplied booking-config input; and known-answer
fixtures. **Priority: P3, next release after the P1 items.**

### 3.6 `coworking-proposal-builder` as described — NARROW, not admitted as a builder

The "builder" framing is exactly the frame that walks the skill into R4
contract drafting. The buildable, citable, non-legal core is a
**terms-completeness checklist + a legal-boundary screen**, justified by what
a real coworking agreement contains (the OfficeRnD contract/Quote model and
the WeWork membership agreement filed with the SEC) rather than by any claimed
dispute taxonomy — no source quantifies coworking disputes caused by missing
proposal terms. Two corrections must be carried into any future build: a
coworking membership is a **services** contract, so UCC 2-204 does not
govern it (common-law Restatement §§ 24/26 does); and **"Quote" is a
built-in OfficeRnD contract type**, so for OfficeRnD operators a quote
generator duplicates a shipped feature. Proposal **prevalence could not be
sourced** and must not be asserted. **Priority: P3**, and it must not grow a
quote component that duplicates the broker-channel skill.

### 3.7 Marketing-content and script skills — down-weighted

`coworking-content-calendar`, `coworking-sales-script-coach`,
`coworking-review-response-drafter`, `coworking-listing-syndication-audit`
and `coworking-day-pass-upsell` remain planned, but the research for this
audit found **no credible coworking CAC benchmark and no sourced
proposal-usage prevalence**, and no public operator-community corpus of
coworking sales or booking pain comparable to the OfficeRnD survey. These
remain legitimate future work, but they currently have the **weakest evidence
base in the catalogue** and should be ranked below the P1 items.

---

## 4. Summary: proposed additions and their priority

| Skill | New? | Priority | Maturity | Risk | Blocking gate |
|---|---|---|---|---|---|
| `coworking-member-offboarding` | new | **P1** | experimental→beta | R1 | operator notice table, role map, deposit ledger |
| `coworking-mail-operations` | new | **P1** | beta | R1 | `mail_item` schema addition from a documented vendor export field list; known-answer fixtures |
| `coworking-broker-channel-manager` | new (re-scoped) | **P1** | beta | R1 | operator's own channel terms file; commission ledger fixtures |
| `coworking-location-feasibility` | new | P2 | experimental | R0 | operator lease/build-out model; comparable pricing supplied by operator, never sourced |
| `coworking-acquisition-cost-review` | new | P2 | beta | R0 | spend-file schema; operator denominator definition |
| `coworking-booking-exceptions` | new (split) | P3 | beta | R0 | `room_booking` extension from a documented export field list; operator booking config |
| `coworking-proposal-terms-check` | new (narrowed) | P3 | beta | R1 | source-cited required-terms inventory; legal-boundary evals |

**Total proposed: 7.** Recommended for the **next** release: the three P1
items plus the two cheap extensions to existing skills (`cost_class` on
canonical source buckets; a cost-class annotation on lead-to-tour
checkpoint 8). Recommended for the **following** release: the P2 items.

**Zero new skills is also a defensible outcome for the next release** if the
P0/P1 corrections in `IMPLEMENTATION_PLAN_V0.1.1.md` are preferred as the
sole scope. The P1 additions are worth building because their object models
are evidenced, convergent, and cheap to test — but the repository does not
need them to be correct and publishable.
