# Screenshots still to capture

No image files are in this folder. Do not commit a mock UI.

Capture after the repository is public, from the rendered GitHub page and from a local run:

1. README hero and the skill table, showing stable and beta.
2. `npx skills add QaliAI/open-coworking-skills --list` with the skill count visible.
3. Northstar occupancy output with the three ratios.
4. Health-check `report.html` banner that says the report is a draft.
5. The finalize command failing when `--attest` is omitted, if you can crop it without a huge traceback. A one-line error is enough.
6. `docs/CHOOSE_A_PLAYBOOK.md` rendered on GitHub.

Social preview for GitHub: a simple card with the sentence "Generic AI knows business. OpenCoworking Skills teaches it coworking." and the three synthetic ratios labeled "Northstar demo, not a client." Generate it when you are at a machine with an image tool. Do not put "34 skills" on it. The installable count is 37, of which 13 are beta.

Architecture, if you draw it: exports in, skills choose a playbook, Python computes, a human attests, nothing is sent. Three modes underneath: interview, CSV, and connector prototypes that are mock-tested only.
