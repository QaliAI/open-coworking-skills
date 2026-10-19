# Gap analysis, 2026-10-19

Decisions for this release. "New skill" means a directory under
`.agents/skills/`. A playbook is a reference inside
`coworking-operator-playbooks`, not an extra metric.

Priority is 5 (do it in this release) down to 1 (leave planned).

| Question | Evidence | Existing coverage | Decision | Priority |
|---|---|---|---|---|
| Tech-stack integration audit | OfficeRnD landing page, fetched 2026-10-19: 68% cite integration gaps; 1.65 of five core systems connected across 1,276 accounts. Vendor sample. | CRM/WMS reconciliation handles one month of records, not the map of systems. | **Built** `coworking-tech-stack-integration-audit` (beta). Notes cells are ignored. Writes are flagged, never performed. | 5 |
| AI front desk / concierge | Same survey: 18% using AI. Answer quality is a local failure mode this repo can test. | `coworking-ai-concierge-knowledge-audit` | **Strengthened.** Channels, escalation owner, action permissions, intent gaps. No second skill. Playbook `ai-front-desk` routes to it. | 4 |
| Unit economics / break-even | Operators ask what occupancy covers rent. Public "about 70%" figures are market-specific and were not adopted. | Occupancy dashboard reports three ratios. It does not take a cost file. | **Built** `coworking-unit-economics` (beta). Missing costs stay unknown. Products with different bases are not summed. | 5 |
| Meeting-room yield | Booked is not used. Cancellations and no-shows change the denominator. | `coworking-meeting-event-yield` (beta) and `room_yield` | **Upgraded** the engine and the skill text. Utilization only with declared bookable hours. Partial cost does not produce a contribution. | 4 |
| Self-service booking / checkout | Quotes and contracts are 20% of time-sink responses on the OfficeRnD page. That is not a tested checkout rubric. | Planned `coworking-booking-flow-audit` | **Stays planned.** Promoting it to beta would publish an untested skill. | 3 |
| Member support triage | Member communication is 21% of time-sink responses. | Daily brief plus concierge audit | **Not built.** Overlaps those two. A ticket taxonomy is not fixture-tested. | 2 |
| Landlord reporting | Management agreements are a real audience split. No new formula. | Monthly owner report | **Audience rules** inside the existing skill. Collections omitted unless the operator confirms the agreement requires them. Not legal advice. | 4 |
| Mail / virtual office operations | VO reconciliation is shipped. Daily mail queues are jurisdiction-sensitive. | `coworking-virtual-office-reconciliation` (stable). Mail operations planned. | **Stays planned.** No CMRA or legal advice. Playbook `virtual-office-audit` uses the reconciliation skill. | 2 |
| Access credential versus entitlement | Secondary source: door access essential 54%, connected 30% (Daily Office News, 2026-10-07). | Tech-stack audit can mark access disconnected. | **Stays planned.** Read-only, and not safe to improvise from a badge export in this release. | 3 |
| Proposals, brokers, commissions | Quotes are a time sink. Broker economics differ from direct leads. | Pipeline health is hygiene, not a proposal or a fee. | **Stay planned.** `coworking-proposal-builder` and broker channel manager are unchanged. | 3 |
| Presale / new location | Launch skills are still planned. | None shipped. | **No playbook.** The operator-playbooks skill says so and refuses to invent one. | 1 |
| "Where are we losing money?" and the other operator questions | Operators should not have to know skill file names. | The primitive skills exist. | **Built** eight playbooks in one beta skill. See [../CHOOSE_A_PLAYBOOK.md](../CHOOSE_A_PLAYBOOK.md). | 5 |

## Playbooks shipped

1. Revenue recovery — "Where are we losing money?"
2. Sales conversion — "Why aren't leads converting?"
3. 90-day occupancy — "What will be vacant, and what do we need to sell?"
4. Retention — "Who should we talk to before they leave?"
5. Virtual-office audit
6. Monthly owner, including the landlord audience
7. AI front desk readiness
8. Tech stack

## Counts after the decisions

24 stable, 13 beta, 22 planned. The three new betas are the two analyses and
the playbook router. Thirty-four skills would also have been an acceptable
library. These three each had a distinct operator question, a refusal rule,
and a test.

No beta skill is marked stable. Operator evidence is the promotion gate, in
[../OPERATOR_VALIDATION.md](../OPERATOR_VALIDATION.md).
