# Operator profile template

Copy this structure into `operator-profile.md`. Every field belongs under
Facts, Assumptions, or Missing — never leave a guessed value looking like a
fact. Keep the operator's own words in Terminology.

```markdown
# Operator profile — <business name>
last_updated: YYYY-MM-DD
sources: <interview date, document names>

## Facts

### Identity
- Business name, brand names
- Currency

### Locations (one block per location)
- location_id (short slug), name, address, market
- Timezone (IANA), opening hours
- Opening date, operating status
- Sellable capacity: offices / workstations (state which)
- Non-sellable capacity (staff areas, comped show suites)

### Products
- List each sellable product with the operator's name and the canonical type
  (private office, team suite, managed office, dedicated desk, hot desk,
  community membership, day pass, meeting room, training room, event space,
  virtual office / business address, mailbox, phone answering, add-ons,
  enterprise agreements)

### Pricing
- List price ranges per product per location; discount policy; who approves

### Target customers
- Segments actually served (solo, 2-10 teams, enterprise, VO-only, ...)

### Team and roles
- Who owns: sales follow-up, tours, community, billing, marketing

### Sales process
- Lead definition ("what counts as a lead")
- Stage names in the CRM and what each means
- Tour booking flow; who hosts

### Membership lifecycle
- Notice period, renewal process, pause policy

### Systems
- WMS, CRM, accounting, payments, access control, marketing tools
- Which system is the source of truth for members / money / inventory

### Marketing channels
- Active channels and how sources are labeled in the CRM

### KPI definitions
- Occupancy definition managed to (unit / workstation / financial)
- Churn definition used in reporting
- Any custom formulas the owner already uses

### Approval requirements
- Actions requiring human sign-off (discounts, refunds, external emails)

### Terminology
- operator word -> canonical term

## Assumptions
- Each with reasoning and how to confirm

## Missing
- Ranked by impact on analyses
```
