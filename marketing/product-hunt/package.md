# Product Hunt

Use this for AI and developer visibility. It is not the main way to reach coworking operators. Do not buy a boost.

## Name

OpenCoworking Skills

## Tagline

Open-source coworking skills for the AI agent you already use.

## Description

Generic AI knows business. OpenCoworking Skills teaches it coworking.

Install tested skills for occupancy, revenue leakage, sales hygiene, virtual offices, and a local health check. You bring the host and the CSV exports. The calculator runs on your machine and does not send member data anywhere.

24 stable skills, 13 beta. Beta means complete on synthetic data, not yet proven by an outside operator. HubSpot and OfficeRnD connectors are read-only prototypes tested against mocks, not live accounts.

Apache-2.0. https://github.com/QaliAI/open-coworking-skills

## Maker comment

I built this because assistants kept returning one occupancy percentage for a business that has three. The arithmetic is in Python with known-answer tests. The judgment — who to call, what to charge, what to send — stays with the operator. A reviewed health-check banner requires a person's name and an attestation. I will not mark beta skills stable to make the launch look larger.

## FAQ

**Does it replace OfficeRnD or Nexudus?** No. It reads exports. It does not write back.

**Which AI do I need?** Any host that can load Agent Skills. Codex, Claude Code, Copilot, and Cursor are the ones the install docs name. The skills CLI also targets other agents. Host behavior still differs.

**Is the demo a real space?** No. Northstar and Harbor Works are synthetic.

**Do you collect usage data?** The Python package does not. The third-party skills CLI can. Set DISABLE_TELEMETRY=1.

## Gallery

Capture after publication: README on GitHub, `--list` output, Northstar occupancy JSON, health-check draft banner. Concepts only until those shots exist. See [../screenshots/README.md](../screenshots/README.md).

## Launch-day checklist

- Public repo and a working `--list` against GitHub, not only a local path.
- First comment is the maker comment above.
- Reply to technical questions with the limitation, not a bigger claim.
- Do not argue with coworking operators about their own definitions. File an issue.

## Follow-up comment, day 2

Post the synthetic three-ratio example and the link to CHOOSE_A_PLAYBOOK.md. Invite routing bugs.
