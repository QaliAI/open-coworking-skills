# Coworking operator quickstart (no coding required)

You do **not** need to install software, know GitHub, connect an account, or pay for anything to try these workflows. Start with a **fictional** coworking scenario, decide whether the result helps, then use approved, non-sensitive data from your own space.

> **Important distinction:** A copied prompt in a general chat assistant is a *guided, manual version* of a skill. It does not automatically install the full skill, run the tested Python calculations, or connect to your workspace system. For verified calculations on exports, use the full skill plus its deterministic tools or ask a qualified analyst to check the math.

## Start here: pick one problem

| Your role or question | Start with | What you should get |
| --- | --- | --- |
| Owner / GM: "Are we actually full?" | [Occupancy and revenue](../../.agents/skills/coworking-occupancy-revenue-dashboard/SKILL.md) | Separate occupancy measures, formulas, exclusions, and one next action |
| Sales: "Which leads are slipping?" | [Pipeline health](../../.agents/skills/coworking-pipeline-health/SKILL.md) | Leads without next steps, ambiguous records, and a follow-up list |
| Sales: "How fast do we respond?" | [Speed-to-lead audit](../../.agents/skills/coworking-speed-to-lead-auditor/SKILL.md) | Response-time definition, unanswered leads, and a repeatable daily check |
| Owner / finance: "Are we missing revenue?" | [Revenue leakage](../../.agents/skills/coworking-revenue-leakage-audit/SKILL.md) | Potential mismatches to investigate, **not** assumed lost income |
| Community manager: "What do I do today?" | [Daily operator brief](../../.agents/skills/coworking-daily-operator-brief/SKILL.md) | A prioritized brief based only on information supplied |

If you're unsure, start with **pipeline health**. A small list of fictional leads is enough to understand the workflow.

## Your first 5-minute demonstration: pipeline health

**Step 1 — Open your preferred AI chat.** You can also read the [full pipeline-health instructions](../../.agents/skills/coworking-pipeline-health/SKILL.md). A plain chat prompt is easier to try, but it is not the same as installing that full skill.

**Step 2 — Copy this starter request:**

```text
Act as a careful coworking sales operations assistant. Using ONLY the
fictional lead records below, identify missing owners or next actions,
potentially stale follow-ups, and ambiguous or duplicate records.
First state your proposed definition of "stale" and any dates needed.
Do not invent a current date, response time, lead value, or conversion rate.
For each finding, cite the relevant lead ID and explain why it was flagged.
Provide a short, practical next-action checklist and clearly separate
facts from assumptions. Do not send any messages or change a CRM.

Fictional sample leads (not real people):
ID | Stage | Assigned to | Last activity | Next action
L-101 | New inquiry | Sam | 2026-11-02 | None
L-102 | Tour booked | Lee | 2026-11-09 | Confirm tour
L-103 | Proposal sent | Sam | 2026-10-21 | None
L-104 | New inquiry | Unassigned | 2026-11-10 | Call prospect
L-105 | Closed won | Lee | 2026-10-30 | Confirm onboarding
L-106 | New inquiry | Sam | Missing | None

Use 2026-11-11 as the as-of date. This is a demonstration only.
```

**Step 3 — Check the answer.** A useful response should flag L-101, L-103, and L-106 for missing next actions; L-104 for missing ownership; and L-106 for its missing activity date. L-102 and L-105 have stated next actions. A claim such as "conversion is 25%" is **not supported** by these records. Whether any record is **stale** depends on the explicitly selected stage-specific policy. The assistant must not assume that "closed won" means revenue was collected.

**Step 4 — Take one safe action.** Make a list of records your sales manager should review today. Do not auto-send messages, update the CRM, or treat the sample as real customer information.

**Step 5 — Go deeper if useful.** For full methodology and deterministic export analysis, follow the [technical quickstart](technical-quickstart.md) or work with someone who can run and review the packaged tools.

## Using your own data safely

1. **Start with counts or a synthetic sample.** Replace customer names with fictitious IDs before any AI-chat interaction.
2. **Check your organization's AI and privacy policies before sharing data.** Do **not** paste raw CRM or member exports into a cloud AI chat merely to ask that service to redact them. Redact locally first with an approved tool or an authorized internal process.
3. **Minimize the fields.** A pipeline check often needs a lead ID, stage, assigned role, timestamp and next step—not name, email, telephone, home address, payment information or free-text private notes.
4. **Check time zones and definitions.** "First response" may mean different things in different systems; occupancy may mean workstations, offices or billed memberships. Stop the calculation until the denominator is clear.
5. **Keep final actions human-approved.** These skills are analysis/draft aids, not autonomous sales, billing, access-control or member-messaging systems.

The repository includes a fictional [Northstar coworking sample space](../../examples/synthetic-space/README.md) and detailed instructions for testing full skills against synthetic exports.

## When you are ready to use the full agent skills (optional)

The canonical workflows are in [`.agents/skills/`](../../.agents/skills/). You can give your AI assistant a complete SKILL.md file as instructions or install skills if your chosen agent supports the Agent Skills format. Compatibility and permissions vary by agent; start with the [platform-specific guidance](../platform-installation/README.md). The installation commands in the [repository README](../../README.md) are for technical users, not a prerequisite for the demo above.

For recurring operations, the [operator context builder](../../.agents/skills/coworking-context-builder/SKILL.md) helps document locations, products, membership definitions, hours and software. Review its assumptions; never let an AI-created operator profile silently become the source of truth.

## What to expect—and what not to expect

**Do expect:** practical questions, explicit assumptions, transparent formulas, a reviewable checklist, and suggestions for next steps.

**Do not expect:** access to your systems, automatically calculated audited financials, guaranteed lead generation, verified software integrations, or emails/messages sent for you. A short pasted prompt and a full tested skill have different capabilities. If information is missing, the correct result is "cannot determine yet."

If a result surprises you, check its inputs, definitions and calculation before acting.
