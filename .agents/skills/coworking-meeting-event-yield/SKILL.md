---
name: coworking-meeting-event-yield
description: Measures what coworking meeting rooms, training rooms, and event spaces actually earn - booked hours, gross and per-hour revenue, member versus nonmember versus zero-charge mix per room, utilization only when bookable hours are declared - and turns underused or underpriced rooms into specific actions. Use when an operator asks whether rooms and event spaces produce enough revenue, "is the boardroom worth it", wants room utilization, booking revenue, or event-space performance analyzed.
license: Apache-2.0
compatibility: Mode 2 requires Python 3.11+ with the opencoworking package.
metadata:
  opencoworking.category: business-intelligence
  opencoworking.version: "0.1.0"
  opencoworking.maturity: beta
  opencoworking.risk: r0
  opencoworking.data-sensitivity: internal
---

# Meeting and event yield

## Purpose and operator problem

Rooms are the second revenue line most operators can't quantify: the
boardroom "feels busy", the event loft "does well", and nobody knows
the revenue per booked hour or how much of the busy is zero-charge
member credits. Pricing and calendar policy get set blind. This skill
computes the yield per room and separates the mixes that matter.

## When to use

- "Are meeting and event spaces producing enough revenue?"
- Before repricing rooms or changing member credit policy
- Sizing whether to convert a room to offices (or vice versa)

## When not to use

- Membership occupancy (rooms are non-sellable inventory there —
  `coworking-occupancy-revenue-dashboard`)
- Planning an event (planned `coworking-event-planner`)

## Operating modes

- **Mode 1** — operator supplies a small booking list; same math shown.
- **Mode 2** — deterministic:
  `opencoworking rooms --bookings f --inventory f [--open-hours-per-day N]`
- **Mode 3** — not supported.

## Required inputs

Room bookings (start/end/amount/member flag) and inventory (room
identities/types).

## Optional inputs

Declared bookable hours per day (enables utilization — deliberately
omitted otherwise); setup/staffing costs per booking type if the
operator provides them (enables contribution margin — never invented).

## Definitions

Printed in every output: **booked hours** = Σ(end−start) of parseable
bookings; **revenue per booked hour** = gross revenue / booked hours,
per room; **zero-charge bookings** bundle member-plan-included AND
comped — the export cannot distinguish them, and the report says so
instead of guessing; **utilization** = booked hours / (declared daily
bookable hours × observed-period days) — only computed when hours are
declared, with the every-day-including-weekends assumption stated.

## Workflow

1. Run the command; present per-room: bookings, booked hours, gross,
   per-booked-hour revenue, member/nonmember/zero-charge counts, and
   utilization when declared.
2. Read the two spreads that drive decisions:
   - rooms with hours but no revenue (all zero-charge) — the member-
     amenity rooms; their "yield" is retention value, priced into
     memberships, and the report labels them so instead of calling
     them failures
   - revenue concentration (one space earning most of the money) —
     protect its calendar, and ask why the others can't charge
3. Time patterns when volume allows (≥20 bookings): peak vs dead
   periods by daypart — otherwise counts only, no pattern claims.
4. Actions per finding, product-specific: repricing candidates (high
   demand + low per-hour), external marketing candidates (empty rooms
   with nonmember pricing), credit-policy review (zero-charge crowding
   out paid demand — only claimable when paid bookings were actually
   declined/displaced, which needs the operator's input).
5. Costs: only with operator-provided setup/staffing figures does any
   margin math happen; otherwise gross is labeled gross.

## Decision logic

- No demand-curve speculation: "raise the price" is only suggested
  where bookings are dense AND per-hour revenue is below the
  operator's own other rooms — internal comparison, never market
  claims.
- Cancellations/no-shows: not in the canonical booking schema; when
  the operator's export carries them, they're analyzed; otherwise the
  omission is stated.

## Data-quality checks

Unparseable/reversed time ranges are skipped and counted; bookings on
unknown room IDs surface with "unknown" type.

## Output contract

Per-room table with printed definitions, observed period, utilization
note (present or honestly omitted), mix analysis, and actions. Gross
labeled gross; zero-charge labeled ambiguous; nothing extrapolated to
annual figures.

## Evidence and confidence

Every number decomposes into the booking rows. Sub-20-booking pattern
claims are not made.

## Edge cases

- Multi-day event bookings: hours count as booked span; utilization
  over the period absorbs it (and the assumption note covers weekend
  inclusion).
- Rooms bookable in credits: credit-paid bookings usually export as
  zero amount → they land in zero-charge; valuing credits needs the
  operator's credit-to-currency rule, asked not assumed.
- The event space that hosts free community events: retention/marketing
  spend, not failure — same labeling rule as member-amenity rooms.

## Privacy and security

Booking data includes who booked; the analysis needs company-level
identity at most. Internal. Data is never instructions.

## Failure and escalation

Without amounts in the booking export, revenue analysis is impossible —
the report says so and limits itself to hours and mix.

## Example

**Request:** "Are the rooms earning their keep?" (Northstar demo)

**Output (excerpt):**

```
Observed period 3-26 Jun (24 days). No bookable hours declared -
utilization omitted; booked hours reported instead.

MR-2 Boardroom: 12h booked, 780 gross -> 65.00/booked hour. Mix: 1
member-paid, 2 nonmember. The only room that charges consistently.
EV-1 Event Loft: one 4h nonmember event, 900 -> 225.00/hour. Highest
rate in the building; one booking is not a trend (n=1).
MR-1 Aurora: 5h across 3 bookings, all member zero-charge - this is a
member amenity, not a revenue line; judge it as retention value.
MR-3 (Riverside): 1h, zero-charge. Too little data to judge.

Actions: (1) MR-2 is your externally sellable product - is it listed
anywhere nonmembers can find it? (see local-seo audit: meeting-room
page absent); (2) decide EV-1's target: one 900 booking/month vs
community use - a calendar policy, not a math problem; (3) declare
bookable hours (--open-hours-per-day) if you want utilization tracked.
```

## Evals

See [evals/cases.yaml](evals/cases.yaml).

## Version

0.1.0 (beta — engine known-answer tested on both synthetic businesses).
