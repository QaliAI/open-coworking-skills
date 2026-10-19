# r/coworking draft

DRAFT. Re-read today's r/coworking rules before posting. Disclose that you built this. Do not cross-post this text.

Title: I open-sourced the coworking workflows I wanted when an AI assistant mixed up occupancy

Body:

I operate and market spaces, and I kept getting one confident occupancy percentage back from generic assistants. In a coworking building that number is at least three numbers: offices, workstations, and revenue against list price. They diverge when a suite is comped, discounted, or out of service.

I put the corrections into an open-source skill library and a small local calculator. It reads CSV exports. It does not log into your workspace system. It will not email members. A health-check report stays a draft until a human attests that they reviewed the checklist.

The interesting failures I want operators to test:

- Partner-billed virtual offices getting treated as unbilled members
- A won CRM deal with nobody in the workspace system
- Meeting-room revenue counted as profit when there is no cost column
- Notice date treated as the end date

There are 24 skills I would call stable and 13 that are beta, meaning tested on synthetic companies only. If you run a space and you have a redacted export, I would rather you tell me which sentence is wrong than hear that it "looks useful."

Repo, if links are allowed: https://github.com/QaliAI/open-coworking-skills

I built this. I am not a vendor, and OfficeRnD / Nexudus / HubSpot have not endorsed it.
