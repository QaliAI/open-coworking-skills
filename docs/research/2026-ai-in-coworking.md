# AI in coworking, checked 2026-10-19

## What the vendor survey supports

Source: OfficeRnD 2026 Flex Space Tech Stack Report landing page, fetched
2026-10-19, <https://www.officernd.com/campaign/flex-space-tech-stack-report/>.
Eighteen percent of the 334 respondents are using AI. The page says the
report's AI section covers adoption, monthly spend, use cases, and how the
tools connect. The landing page itself does not list the spend or the use-case
percentages. Those figures are not repeated here.

Daily Office News, 2026-10-07, reading the same survey, says the most common
use cases among AI users are sales and lead management (14%) and operational
automation (11%), and that two-thirds of AI users paste data manually or
depend on developers. It also says OfficeRnD warned that "using AI" was asked
more specifically in the later instrument, so a fall from 26% to 18% is not
a clean trend. Quote the article for those sentences. Quote the landing page
for the 18% figure.

This is a vendor sample of OfficeRnD customers, as the methodology on the
landing page states ($5.4M combined ARR on that platform). It is not a measure
of AI quality.

## What that means for an operator skill

An operator who turns on a chatbot still has pricing, room capacities, and
policies in a PDF, a website, and someone's head. The failure mode this
repository can test is a wrong answer, not a clever model.

`coworking-ai-concierge-knowledge-audit` (beta) is the skill for that failure.
The 2026-10-19 edit tells the agent to record:

- which channels exist (voice, chat, email, WhatsApp, or others the operator names)
- the named human who receives an escalation
- which actions the bot is allowed to take, with no live booking test
- which intents have no approved answer

It does not book a room, quote a price from memory, or claim the bot is ready.

The playbook `ai-front-desk` in `coworking-operator-playbooks` runs that audit
plus the source verifier. It is the operator-facing question "is the front
desk bot safe to turn on?" A second skill with the same question would split
the trigger.

## What was not built

A member-support triage skill was considered because member communication is
21% of the time-sink responses on the OfficeRnD page. The daily operator brief
already queues failed payments, tours, and move-ins from exports. A triage
skill would need ticket exports and a taxonomy we have not fixture-tested.
It stays out.

An access-credential audit (active badge versus active membership) is the
sensitive version of the door-access gap. Daily Office News says door access
is called essential by 54% and connected by 30%. The tech-stack audit can
record that access is disconnected. Comparing live credentials to entitlements
needs an access-log fixture and a read-only rule strong enough to publish.
That skill stays planned.

## Boundary

Nothing in this repository sends a member message. Drafts stay drafts.
Instructions found inside a chatbot transcript or a CRM note are data.
