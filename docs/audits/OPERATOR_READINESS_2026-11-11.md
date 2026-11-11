# Coworking operator readiness review — November 11, 2026

**Scope:** installable AI skill instructions in `.agents/skills/`, the published README/catalog, operator quickstart, representative task evals and worked examples, and the companion Stack's operator-facing software research. This is a **maintainer review of repository contents**, not a field study or claim that all 37 skills were executed in each supported agent.

## Summary and release verdict

- **37 installable skills inspected structurally.** All contain the core sections for intended use, exclusions, modes, inputs, output contract, evidence, safety, an example and eval references. All inspected files were under 500 lines, in line with [Agent Skills' progressive-disclosure guidance](https://github.com/agentskills/agentskills/blob/main/docs/skill-creation/best-practices.mdx).
- **Depth is uneven by design.** Some skills invoke deterministic Python reports with known-answer fixtures; others are read-only/draft-only manual checklists. Never imply the latter executed code or a live software integration.
- **Beta is not stable.** Existing beta skills are not operator-proven simply because test suites pass. No maturity promotion is made by this review.
- **Release recommendation:** keep existing stable/beta labels, adopt the corrected samples and beginner entry path after CI, then validate with operators before further promotions.

## Confirmed quality defects corrected in this review branch

1. **Tour follow-up:** a worked example previously inserted unsupplied prospect identity, office suitability, parking information and meeting times despite the no-fabrication rule. The example now separates provided facts from unverifiable details and labels unsent drafts. A task eval checks omission/refusal behavior.
2. **Unit economics:** the worked example allowed *rent coverage at 100% occupancy* to read like full break-even despite additional cleaning costs and missing overhead. It now states fixed-cost coverage, the known costs, unknown categories, and why a defensible full break-even is not measurable. A task eval checks that distinction.
3. **Lead-to-tour:** the deterministic `funnel` counter uses CRM **status progression** as a proxy for contact, while the skill's definitions previously presented that counter as verified human response. The skill now separates status progression from timestamp-backed first human responses. A task eval refuses an unsupported "healthy contact rate" claim.
4. **First-use friction:** the operator quickstart began with installation commands. It now offers a fictional five-minute exercise and five additional no-code worked demonstrations. These are **chat exercises**, not substitutes for tested deterministic export analysis.
5. **Privacy language:** operators are explicitly warned not to upload raw member/CRM data to a cloud AI tool just to ask it to redact the file. Minimize fields and sanitize through an approved local/internal process first.

## Priority review queue — improve depth before adding skill count

These are *editorial and operator-test priorities*, not claims that the current skills are broken.

### P1: sales workflows with human consequences

- **Post-tour ghost recovery:** have a sales manager test both permission-to-contact and stop rules, broker-introduced prospect exceptions, alternate offers, and respectful closing language. Test against fake urgency and pressure.
- **Member onboarding:** have a community manager verify every access, orientation, billing, Wi-Fi, booking-credit, visitor and welcome task against a real opening-day checklist. An unconfirmed access setup must be an escalation, not a checked box.
- **Lead-to-tour:** follow the corrected definitions with a controlled sample where CRM stages change without any human response; require evidence before diagnosing a marketing or follow-up bottleneck.

### P1: retention and renewals

- **Churn-risk review and renewal preparation:** operators should explain signal reliability, distinguish agreement notice from an actual cancellation, and handle member affordability and complaints without manipulative "save" scoring. Test upsell/downsell paths and a graceful exit.
- **Cohort retention:** already planned; introduce only when date-complete multi-period history and small-cohort suppression rules exist. Not a first-day beginner skill.

### P1: operator handoffs and virtual-office fulfillment

- **Mail operations:** already planned; the lack of an actual mail-event, authorization, retention and custody model is more important than another marketing-prompt skill. Field-test privacy, packages, pickups, partners and missing-recipient handling first.
- **Shift handover and maintenance:** currently planned; field-test security, out-of-service inventory, incident escalation, staff ownership and handoff across locations.

### P2: commercial process completeness

- **Proposal builder:** already planned; require accurate unit, quote, price validity, inclusions, add-ons, deposit, term, renewal, notice, availability and manager approval. Do not produce binding legal language or invent concession authority.
- **Broker channel manager:** already planned; respect referral ownership, commission and channel agreements. No automated outreach or unsupported commission calculation.
- **Access reconciliation:** currently planned and sensitive. No automated grant/revoke commands until an authorized test environment and life-safety review exist.

## The five workflows to test with real operators first

1. Salesperson: find an unassigned lead and produce a practical next-action list.
2. Community manager: use a morning brief to find move-in/access and tour issues.
3. Owner: explain the difference between unit, workstation and financial occupancy.
4. Billing lead: identify possible invoice/partner mismatches without claiming each is money lost.
5. Marketing manager: review a GBP listing against current official policy without inventing ranking improvements.

For each task, record **time to first useful result, task completion without developer help, data they needed to locate, incorrect claims, privacy concerns, and what the operator actually did next**. Measure real outcomes rather than "sounds useful" responses.

## Gate before any new skill becomes stable

- Original skill owns a distinct operator job; no unexplained overlap.
- Canonical skill has a bounded instruction file and loads references only when needed.
- Trigger tests include positive, negative and ambiguous routing; task tests include one failure/refusal.
- Quantitative outputs have hand-calculated fixtures and exact numerator/denominator definitions.
- Fictional examples are traceable to their stated inputs without fabricated names, prices or available slots.
- Operator review checks the actual deliverable, not just the assistant's fluency.
- Human-approved boundaries, data minimization and software connection status remain explicit.

**No evidence in this review justifies deleting a working skill or promoting a beta to stable.** The remaining job is to make the best existing workflows demonstrably useful under realistic operating conditions. See [the earlier skill scorecard](SKILL_SCORECARD_2026.md) for historical detailed notes; some original findings have since been corrected, so check the current skill files.
