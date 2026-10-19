# Technical-community draft

DRAFT for one AI or open-source community whose current rules allow a project post. Not for r/coworking. Re-read the rules. Disclose that you built it.

Title: Vertical Agent Skills for coworking, with deterministic metrics and a 518-case router file

Body:

Most agent-skill repos are instructions with no calculator. I wanted a vertical set where the metric cannot quietly change.

OpenCoworking Skills is Apache-2.0. Skills follow the Agent Skills layout (`SKILL.md` in `.agents/skills/`). A stdlib Python CLI computes occupancy, leakage, pipeline hygiene, room yield, and a few other coworking-specific ratios. Known answers are checked against two synthetic operators. The suite collects 233 tests. Thirty-one command evals execute. A trigger file has 518 cases. An LLM judge scored an earlier 476-case slice 476/476. The 42 cases added for three new skills have not been judged. I am leaving that gap visible.

Privacy: exports are treated as data, not instructions. A health-check preflight refuses credential files and card numbers. Finalizing a report requires a reviewer name and an attestation string. There is no send command.

Install path that the skills CLI documents:

npx skills add QaliAI/open-coworking-skills --list

What I want from this community is routing and eval criticism, not a verdict on coworking. If a description activates the wrong skill, that is a bug.

I built it. Connectors for HubSpot and OfficeRnD are mock-tested read-only prototypes, not live clients.
