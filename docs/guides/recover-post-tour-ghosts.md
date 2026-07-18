# Recover post-tour ghosts

Prospects who toured and went silent are recoverable — if you re-engage
with value instead of nagging.

## Find them

```bash
python -m opencoworking.cli leakage --tours tours.csv --deals deals.csv --as-of 2026-07-01
```

`completed_tours_without_next_action` is your ghost list;
`stale_open_deals_30d` catches the ones that stalled after a proposal.

## The sequence rules (from `coworking-post-tour-ghost-recovery`)

1. **History first.** List every prior attempt. Two value-less nudges
   already sent? The sequence shortens — the next message changes the
   game or starts the goodbye.
2. **≤4 touches over ~3 weeks, each a different type:**
   - *New information* — something actually changed (availability,
     a comparable unit opening)
   - *Useful artifact* — helpful regardless of reply (cost-comparison
     sheet, day-pass invite to work a real day in the space)
   - *Direct question* — "Still looking, or did the plan change? Either
     answer helps me stop bothering you."
   - *Close the loop* — assume plans changed, door stays open, pricing
     sheet attached, warm stop.
3. **Urgency only when real.** A hold expiry you actually set is
   urgency. "Others are interested" when they aren't is a lie your
   market is small enough to catch.
4. **A stop rule, stated.** After close-the-loop: silence. Re-entry only
   if they reply or something genuinely changes months later.
5. **Consent limits.** No newsletter-drip conscription; replies on their
   inquiry thread only unless they opted into marketing.

## What the assistant produces

Per prospect: attempt history, the dated touch drafts, urgency evidence
notes, CRM log lines. **You send the messages** — nothing in this
project sends anything.

## Measure it

Ghost recovery is a funnel too: track touched → replied → re-engaged →
closed for the sequence, and feed the results into next month's pipeline
review. If nobody ever replies to touch 1, the tour itself (or the
follow-up before it) is the real problem — see
[audit-your-sales-pipeline.md](audit-your-sales-pipeline.md).
