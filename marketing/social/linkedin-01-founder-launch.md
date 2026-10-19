# LinkedIn 1 — founder launch

DRAFT. Post from your own account.

I open-sourced the coworking workflows I wanted when a generic AI assistant kept mixing up the numbers.

Office occupancy is not workstation occupancy. Neither of those is financial occupancy. A full room on the calendar is not a room that was used. A partner-billed virtual office is not an unbilled member. A won deal in the CRM is not someone who moved in.

OpenCoworking Skills is an Apache-2.0 library of agent skills plus a small Python calculator. You bring the AI host. You bring CSV exports from whatever system you already run. The calculations stay on your machine. Nothing in the tool emails a member or changes a contract.

The library has 24 stable skills and 13 beta skills. Beta means tested on synthetic data, not yet proven by an operator on real exports. I would rather say that than pretend otherwise.

If you run a space and you want to break it, start with one question: where are we losing money?

https://github.com/QaliAI/open-coworking-skills

Install, once the repo is public:

npx skills add QaliAI/open-coworking-skills --list
