# Operator pain points, checked 2026-10-19

This note records what was actually fetched. It is not a survey run by this
project. Every percentage below comes from a vendor or a vendor write-up.
None of them is encoded as a default in the CLI.

## Source

OfficeRnD, "The 2026 Flex Space Tech Stack Report" landing page,
<https://www.officernd.com/campaign/flex-space-tech-stack-report/>,
fetched 2026-10-19. Volume 2. 334 coworking and flex operators, responses
collected from 2024 through mid-2026 and de-duplicated by organisation.
The page says those respondents represent $5.4M of combined annual recurring
revenue on the OfficeRnD platform. North America is 45% of responses, Europe
21%, UK and Ireland 15%, Australia and New Zealand 9%. Sixty percent run one
or two locations. Four percent run more than 30. This is a vendor-platform
sample. It is not an independent census.

Secondary reading, used only where it adds a comparison the landing page did
not state: Daily Office News, "Flex operators have more software than ever.
So why is the admin still manual?", 2026-10-07,
<https://www.dailyofficenews.com/flex-operators-have-more-software-than-ever-so-why-is-the-admin-still-manual/>.
The article says it is reporting the OfficeRnD survey, including a figure
Allwork.Space had carried. Where the two pages differ, the OfficeRnD page wins.

Ledger: [SOURCES.yaml](SOURCES.yaml).

## Findings

### Integration gaps

- **Problem.** Operators own the software and still retype the work. The landing page says 68% name integration gaps as their top technology challenge, ahead of cost, training, and AI. 66% want easier integration rather than vendor consolidation.
- **Evidence.** Same page. Connection data from 1,276 OfficeRnD accounts: the average operator has 1.65 of five core systems connected. Fourteen percent have connected nothing. One account of 1,276 has all five. The page's category leaders for the comparison are payments (Stripe 77% to 85%), CRM (HubSpot 53% to 54%), accounting (QuickBooks 43% to 38%, Xero flat at 29%), and door access (Salto 37% to 36%). The five categories named in the methodology blurb are payments, accounting, CRM, door access, and Wi-Fi.
- **Coverage.** `coworking-tech-stack-integration-audit` (beta) maps the systems the operator lists and flags disconnects, missing systems of record, weak IDs, manual re-entry, and write-enabled tools. It does not call OfficeRnD, and it does not treat 1.65 as the operator's own number.
- **Adequate.** Adequate as a read-only map. Not adequate as a live integration.
- **Improvement.** Keep it beta until an operator fills a systems sheet from a real stack.
- **New skill.** The audit skill is the one this finding justifies. A second "integration" skill would duplicate it.
- **Priority.** 5.

Daily Office News adds, as a secondary account of the same survey: accounting called essential by 57% and connected by 40%; door access essential 54% and connected 30%; lack of real-time data 27%, up from 17%. Those comparisons are not on the landing page text we fetched. Cite the article if you use them.

### Time sinks: billing, member communication, quotes

- **Problem.** The repetitive week is invoicing and billing (27%), member communication (21%), and contracts and quotes (20%). On multi-location operators only, the page says invoicing falls to eighth. The two lists are not the same operation.
- **Evidence.** OfficeRnD landing page, fetched 2026-10-19.
- **Coverage.** Collections and revenue leakage cover the billing side when invoices exist. The concierge knowledge audit covers approved answers, not a support queue. Proposals are still planned (`coworking-proposal-builder`).
- **Adequate.** Billing analysis is adequate for exports. Communication and proposals are not covered by a tested workflow.
- **Improvement.** Do not promote the proposal skill until a terms checklist and legal-boundary evals exist. The roadmap already says that.
- **New skill.** Not in this release.
- **Priority.** 4 for proposals, 3 for a separate support-triage skill. Support triage overlaps the daily brief and the concierge audit. It was not added.

### AI use is shallow, and the comparison is fragile

- **Problem.** The landing page says 18% are using AI. Operators who do use it still copy data between tools, according to the Daily Office News reading (two-thirds of AI users paste manually or depend on developers). The same article says OfficeRnD cautioned that a drop from 26% to 18% is not a clean comparison, because the later instrument asked about specific functions.
- **Evidence.** 18% on the OfficeRnD page. The drop and the paste finding are Daily Office News, 2026-10-07, and should be quoted as that article's reading.
- **Coverage.** `coworking-ai-concierge-knowledge-audit` checks answers against approved sources, escalation, and action permissions. It does not turn a bot on.
- **Adequate.** Adequate as a readiness audit. Not a front-desk product.
- **Improvement.** The skill's workflow now asks for channels, a named human escalation path, and an action-permission list. It does not run a live booking test.
- **New skill.** No separate "AI front desk" skill. The playbook `ai-front-desk` calls this audit.
- **Priority.** 4.

### Occupancy language

- **Problem.** Operators say "we are full" and mean different denominators: offices, desks, or revenue against list price.
- **Evidence.** This is a property of the data model already in this repository, confirmed by the Northstar known answers, not by the OfficeRnD survey. The survey does not define those three ratios.
- **Coverage.** `coworking-occupancy-revenue-dashboard` (stable).
- **Adequate.** Yes, for exports that use the canonical columns.
- **New skill.** No.
- **Priority.** Already shipped.

## What this pass did not read

Private Global Workspace Association channels, vendor Slack workspaces, and
full Reddit threads were not fetched. A pain point from those places is not
in this file. Do not backfill one from memory.
