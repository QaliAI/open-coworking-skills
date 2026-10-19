# Show HN

DRAFT. Post only if you still believe the technical substance is the point. HN readers punish a marketing voice. Do not post the LinkedIn text here.

## Title

Show HN: OpenCoworking Skills – open-source AI agent workflows for coworking operators

## Text

OpenCoworking Skills is an Apache-2.0 library of Agent Skills (SKILL.md) plus a stdlib Python CLI for coworking operators.

The domain problems are specific. Office occupancy, workstation occupancy, and financial occupancy are different ratios. A CRM "won" deal is a different object from a workspace membership. Meeting-room hours booked are not hours used. Virtual-office clients billed by a partner are not automatically unbilled. The CLI refuses to sum leakage classes that do not share a base.

What is tested: 233 pytest items, 31 command evals with hand-computed fixtures on two synthetic operators (Northstar and Harbor Works), skill schema checks, and a 518-case trigger file. An LLM judge scored an earlier 476-case run 476/476. Forty-two cases added later have not been judged.

What is deliberately weak: 13 skills are beta because no outside operator has run them. HubSpot and OfficeRnD connectors are read-only and mock-tested, not exercised against a live or sandbox tenant. The tool has no network calls and no telemetry. A health-check report cannot be marked reviewed without a reviewer name and an attestation string. There is no send path.

Install (skills CLI, Node 22.20+):

npx skills add QaliAI/open-coworking-skills --list

Repo: https://github.com/QaliAI/open-coworking-skills

I built it. I am interested in routing failures, formula mistakes, and cases where the canonical columns do not match a real export.
