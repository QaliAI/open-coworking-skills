# Customize for your location

The skills are vendor-neutral and definition-flexible by design. Here is
where your specifics plug in.

## Your operator profile carries your definitions

Build it once (`coworking-context-builder`) and keep it updated. The
fields that change analysis behavior:

- **Occupancy definition you manage to** — count, workstation, or
  financial; reports lead with yours and show the others.
- **Lead definition and stage names** — your CRM's stages map to the
  canonical set; the mapping lives in your data-dictionary file, not in
  edited skills.
- **Business hours and time zones per location** — speed-to-lead is
  computed in YOUR hours (`--open-hour/--close-hour` flags).
- **Terminology** — if you call offices "studios", record it; briefs and
  reports should speak your language while the data stays canonical.
- **Approval requirements** — who may approve discounts and refunds;
  skills route those decisions to the named human.

## Your thresholds

Defaults are visible and adjustable, not hidden: stale-deal threshold
(`--stale-days`, default 21), discount flag (`--discount-flag-pct`,
default 25), the leakage audit's 45-day invoice window (annual-prepaid
members: see the skill's edge cases). Change the flag, not the code.

## Your source labels

Extend the lead-source normalizer with your local reality — the brokers
you use, your partner names — as `extra_rules` proposed and confirmed in
the skill's workflow. Unmapped labels are never silently bucketed.

## Your systems

Map once with `coworking-data-dictionary`; save the mapping file; reuse
it every export. If your platform has no guide yet in
[adapters/](../../adapters/README.md), the generic CSV path always works,
and the `coworking-system-adapter-builder` skill shows how to contribute
the guide.

## What NOT to customize

Don't edit the formulas inside the shared package per location — that
forks the meaning of your own reports. If you genuinely use a different
formula, define it in your profile, have reports state both, and
consider a PR making the variant configurable for everyone.

## Multi-location operators

Keep one profile with per-location overrides (hours, time zones,
definitions where they truly differ). Run analyses per location AND
consolidated; never mix definitions across locations without the report
saying so.
