# Five first wins: no-code coworking AI demos

**For owners, GMs, sales teams and community managers.** Choose one scenario, copy its request into your preferred AI chat, and see the result before you touch real data. All names, spaces, figures and dates below are fictional. These are **manual demonstrations**, not installed agent skills, financial audits or connected integrations.

For a step-by-step first walkthrough, see the [operator quickstart](operator-quickstart.md). For reproducible calculations, use the complete linked SKILL.md and the repository's tested data tools. **Never paste unredacted member or prospect records, passwords or payment details into an unapproved AI service.**

## 1. Sales: find unattended leads

**You want:** a practical follow-up review rather than another generic recommendation to "improve CRM hygiene."

**Skill:** [Pipeline health](../../.agents/skills/coworking-pipeline-health/SKILL.md)

```text
Review this fictional coworking pipeline as of 2026-11-11. Identify missing
owners, missing next actions and unknown activity dates. Cite exact IDs.
Do not invent first-response timestamps, lead values or conversion rates.
Explain that staleness requires a defined stage-specific policy.
Return three actions a sales manager can take today. Do not send messages.

ID | Stage | Owner | Last activity | Next step
P1 | New | Alex | 2026-11-10 | None
P2 | Tour booked | Pat | 2026-11-09 | Confirm tour
P3 | Proposal | Alex | Unknown | None
P4 | New | Unassigned | 2026-11-11 | Call prospect
```

**Check:** P1 and P3 lack next steps; P3 lacks a usable activity date; P4 lacks an owner. P2 has a next step. **Do not** treat "proposal" as revenue or claim that a lead is stale without stating an agreed stage policy.

## 2. Owner: understand why "full" has multiple meanings

**You want:** to distinguish sellable capacity from contracted utilization.

**Skill:** [Occupancy and revenue dashboard](../../.agents/skills/coworking-occupancy-revenue-dashboard/SKILL.md)

```text
Using ONLY this fictional snapshot, calculate simple private-office
unit occupancy and explicitly label what cannot be computed.
There are 10 private-office units: 6 occupied under active agreements,
2 available and vacant, 1 offline for repairs, and 1 reserved for
internal use. Do not assume desk counts, paid rates, collections,
membership churn or coworking desk utilization.
Show numerator, denominator, exclusions and at least two plausible
denominator conventions. End with a simple operator decision.
This is an illustrative unit-count exercise, not the full skill's
three-way occupancy calculation.
```

**Check:** 6 of 10 total physical units = **60%** by a gross-unit count; 6 of 8 when repair and internal-use units are excluded = **75%** under that explicitly stated denominator. Neither tells you collected revenue, workstation occupancy, or whether the reserved unit is genuinely unsellable. Verify the inventory policy before calling either figure your operating occupancy.

## 3. Community: build a morning priority brief

**You want:** a repeatable opening routine that distinguishes urgent from routine.

**Skill:** [Daily operator brief](../../.agents/skills/coworking-daily-operator-brief/SKILL.md)

```text
Create a morning coworking operator brief using only these fictional
notes. Mark unknowns, assign no real staff member, and avoid invented
deadlines. Prioritize member safety and service interruptions first,
then scheduled commitments, then routine work.
- Meeting room A's door lock intermittently fails to latch.
- A prospect tour is scheduled for 10:00 local time.
- Two packages are waiting for logging.
- A new member is arriving today; access setup is unconfirmed.
- A community event is planned next week.
Output a short opening checklist with who should verify each item
(role only), an escalation recommendation and a handoff note.
```

**Check:** Door security and access verification warrant early checks; the tour has a stated time; packages and next week's event should not outrank an unresolved access/security issue. Do not assert the door is safe, access has been granted, or a team member has been assigned.

## 4. Sales: diagnose response speed without fake statistics

**You want:** a speed-to-lead audit that knows when information is missing.

**Skill:** [Speed-to-lead auditor](../../.agents/skills/coworking-speed-to-lead-auditor/SKILL.md)

```text
These are fictional coworking inquiries. Determine which response
times are calculable and which records need more data. Use UTC times.
Do NOT assume business hours, business-hour SLAs, or missing replies.
L1 inquiry 2026-11-10 14:00 UTC; first human reply 14:25 UTC
L2 inquiry 2026-11-10 15:00 UTC; first human reply unknown
L3 inquiry 2026-11-10 16:00 UTC; first human reply 17:10 UTC
Report raw elapsed response times only. State what is needed for
a business-hours metric. Do not label an unknown reply as definitively
unanswered or claim any improvement.
```

**Check:** L1 = **25 minutes**; L3 = **70 minutes**; L2 = **unknown**, not zero, and not verified unanswered. Business-hours response analysis requires the operator's location, time zone, opening hours and holiday rules.

## 5. Marketing: audit a local listing without inventing policy

**You want:** a grounded Google Business Profile checklist.

**Skill:** [Google Business Profile audit](../../.agents/skills/coworking-google-business-profile-audit/SKILL.md)

```text
Prepare a manual GBP review checklist for a fictional coworking space.
Known details: website links to the main office location; opening
hours on the website are Mon-Fri 9am-5pm; the GBP hours have not been
verified; the website says it offers meeting rooms and virtual offices;
there is no evidence yet about signage, on-site staffing or whether
the virtual-office offering qualifies for a separate profile.
Separate confirmed facts, unknowns and next checks. Do not invent
Google policy or promise search rankings; flag any eligibility issue
for review against current official Google guidance.
Return a five-item action checklist and an evidence log template.
```

**Check:** It should ask someone to verify live GBP hours, categories, address eligibility, website/location consistency and supporting evidence. Offering virtual offices **does not automatically establish eligibility** for a separate GBP profile; current official rules must be checked.

---

## Before you use a result with your own business

1. **Check the inputs and denominator.** Do the stated definitions match your operation?
2. **Check the evidence.** Every numerical claim should be reproducible from the stated sample.
3. **Check the limits.** Manual chat prompts are helpful teaching tools but do not execute the repository's deterministic code.
4. **Use minimum-necessary data.** Replace identifiers locally and follow your approved privacy/AI policy before submitting anything.
5. **Keep a human decision point.** No demo authorizes sending messages, charging members, changing access or editing a CRM.

You can use the companion [Open Coworking Stack](https://open-coworking-stack.vercel.app/) to investigate software options. Its directory is not proof that any product is integrated with these manual AI prompts.
