# Trigger and collision evaluation report

Audit session 2026-07-18, branch `expert-audit-wave-2`.

## The suite

[`tests/evals/trigger_cases.yaml`](../../tests/evals/trigger_cases.yaml):
per installable skill, 4 direct positives, 3 indirect positives in natural
operator language ("We look full but the revenue is terrible", "Which
cancellations should I call today?"), 3 negatives (each naming the skill
that SHOULD activate, or `none`), 2 ambiguous (acceptable-set), and 2
collision prompts with explicit unacceptable activations.

- Run 1 scope: 24 stable skills, **336 cases**
- Run 2 scope (after Wave 2): 34 skills, **476 cases**

Runner: [`scripts/run_trigger_evals.py`](../../scripts/run_trigger_evals.py)
— structural validation, a deterministic lexical proxy, manifest export,
and grading of host-produced routing results.

## What was actually executed (vs prepared)

| Layer | Status | Result |
|---|---|---|
| Structural validation | **executed** (CI-ready, deterministic) | 476 cases valid |
| Lexical proxy (IDF token overlap vs descriptions) | **executed** (deterministic; a lower bound, NOT host behavior) | direct 117/136 top-1; indirect 42/102 top-1 (expected: lexical matching cannot read intent) |
| LLM-judged routing run 1 (2026-07-18, Claude subagent `claude-fable-5` as activation judge, 24 skills) | **executed** | 326/336 (97.0%); raw results: [trigger-results-run1.json](trigger-results-run1.json) |
| LLM-judged routing run 2 (same judge setup, 34 skills incl. Wave 2) | **executed** | **476/476 after eval-spec corrections** (472/476 = 99.2% before them); raw: [trigger-results-run2.json](trigger-results-run2.json) |
| Routing inside a shipped host product (Claude Code CLI headless, Codex, Copilot) | **prepared, NOT executed** | Manifest export exists (`--export-manifest`); Claude CLI headless auth was revoked in the audit shell (401); Codex not installed. Do not cite host-product numbers — none exist. |

The LLM-judged runs used only the prompts plus the 34 name+description
pairs — the same information a spec-compliant host's activation layer
sees — but a production host's prompt framing may differ; treat 476/476
as strong evidence for description quality, not a guarantee of any
specific host's behavior.

## What run 1 found (and what was fixed)

- **2 description defects, fixed**: `coworking-lead-source-normalizer`
  overclaimed "asks which marketing channels work", capturing ad-ROI
  questions it cannot answer (2 wrong activations); its description now
  explicitly excludes channel-worth judgments.
  `coworking-renewal-preparation` lacked "member just gave notice / save
  conversation" phrasing its own example covers; added.
- **5 misses validated Wave 2 priorities**: prompts like "Which failed
  payments should we chase first?" and "What should I work on today?"
  had no correct destination among the 24 stable skills — the judge
  chose `none` or the nearest neighbor. All 5 route correctly in run 2
  once the Wave 2 skills exist.

## What run 2 found

Zero hard fails (no unacceptable activations anywhere). The 4 residual
misses were **eval-spec errors, not description errors** — cases where
the judge out-reasoned the original expectation:

1. "My HubSpot contacts don't line up with OfficeRnD" → judge chose the
   new `crm-wms-reconciliation` (better than the originally-expected
   data-dictionary once it exists); acceptable set widened.
2. "Is Google Ads worth the spend?" → judge chose `none` (ad-spend ROI
   is genuinely uncovered); expectation corrected to `none`.
3. "Which tours have no recorded next step?" → judge chose
   `revenue-leakage-audit`, which literally implements that check; the
   original expectation (pipeline-health) was wrong.
4. "What's the market rate for offices around here?" → judge chose
   `none`, respecting the pricing skill's own no-market-claims boundary;
   `none` added as acceptable.

Each correction is annotated inline in the YAML.

## Collision-risk map (from the suite's design + results)

Deliberately overlapping territories, all resolving correctly in run 2:

- occupancy-dashboard ↔ leakage ↔ forecast (present/leak/future money)
- churn-risk ↔ renewal-scan ↔ renewal-preparation (portfolio → member)
- data-dictionary ↔ wms-export-analyzer ↔ crm-wms-reconciliation
  (columns → files → systems)
- collections ↔ leakage ↔ vo-reconciliation (known debt → missing
  billing → partner billing)
- tour-preparation ↔ tour-follow-up ↔ ghost-recovery (time-ordered)

## How to re-run

```bash
python scripts/run_trigger_evals.py                       # structure + proxy (CI)
python scripts/run_trigger_evals.py --export-manifest m.json
# route m.json through your host/judge -> results.json ({case_id: skill})
python scripts/run_trigger_evals.py --grade results.json
```

Grading a real host product (Claude Code, Codex, Copilot) remains open
work; the manifest/grade interface is the contract for it.
