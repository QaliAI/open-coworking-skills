# Operator quickstart (no coding required)

You run a coworking or flex space. You have an AI assistant (Claude,
ChatGPT/Codex, Copilot, or another tool that supports Agent Skills). Here
is how to get value in your first session — without installing anything,
connecting anything, or handing over credentials.

## 1. Give your assistant the skills

If your assistant supports Agent Skills, install this collection (see
[platform installation](../platform-installation/) for your specific
tool). If you use GitHub CLI:

```
gh skill install QaliAI/open-coworking-skills --all
```

If you can't install skills at all, you can still open any skill file
(e.g. [.agents/skills/coworking-pipeline-health/SKILL.md](../../.agents/skills/coworking-pipeline-health/SKILL.md))
and paste it into your chat before your request — a skill is just precise
instructions.

## 2. Build your operator profile (10 minutes, once)

Say: **"Build my coworking operator profile."**

The assistant interviews you about locations, products, pricing, team,
and systems, and saves a profile file that every later analysis uses. It
will separate what you told it (facts) from what it guessed
(assumptions) — correct the assumptions.

## 3. Try a real analysis with your own export

Export something from your workspace software or CRM (a leads list, a
memberships list — CSV is ideal) and say:

**"Here's an export from our system — what can you do with it?"**

The export-analyzer skill identifies what the file contains, checks its
quality (duplicates, blanks, broken dates), and tells you honestly which
analyses it supports. Follow its recommendation — typical first wins:

- "**What's our occupancy?**" — three occupancy numbers with visible
  formulas, and the comped/discounted/out-of-service units distorting them
- "**Where are we losing money?**" — the leakage audit across whatever
  files you provide
- "**How fast do we respond to leads?**" — business-hours response times
  plus every lead nobody touched

## 4. Try it on fake data first (optional but smart)

The repository ships a complete fictional operator — Northstar Coworking
Demo — with realistic problems planted in the data. Point your assistant
at `examples/synthetic-space/data/` and ask the same questions; you'll
see exactly what the outputs look like with zero privacy risk. Expected
findings are listed in [the synthetic-space README](../../examples/synthetic-space/README.md).

## 5. Protect member data

Before pasting or uploading member data anywhere, say **"redact this
export first"** — the PII redactor replaces emails, phones, and names
with stable placeholders and lists what it couldn't catch. Rules of
thumb: analyses of your own data on your own machine are fine; anything
leaving your control gets redacted first; nothing in this project ever
needs your passwords or API keys.

## What these skills will not do

They will not send emails to members or prospects, change your CRM,
charge anyone, or promise Google rankings. Drafts are always handed to
you to review and send. Numbers always come with their formulas — if a
number surprises you, read its formula line first.
