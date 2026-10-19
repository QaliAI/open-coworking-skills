# Sales conversion

Question: "Why aren't our leads converting?"

## Order

1. `coworking-wms-export-analyzer` and `coworking-data-dictionary` on leads, tours, and deals.
2. `coworking-speed-to-lead-auditor` before any judgment about ad spend.
3. `coworking-pipeline-health` for stale deals, missing next steps, and unassigned records.
4. `coworking-lead-source-normalizer` before any source ranking.
5. `coworking-lead-to-tour-diagnostic` to name the failing checkpoint.
6. `coworking-tour-follow-up` only for a specific completed tour with notes.
7. `coworking-post-tour-ghost-recovery` only after the follow-up history is reviewed.

## Minimum files

Leads with created time and first human response time. Tours and deals sharpen the diagnosis. Without response timestamps, say speed-to-lead is not measurable.

## Stop rules

Do not blame marketing volume until contact rate, speed, tour ask, and show rate have been separated. Do not draft a message that pretends a tour conversation you were not given.
