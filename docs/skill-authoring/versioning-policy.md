# Versioning, releases, and deprecation

## Version scheme

The repository releases as a whole under semantic versioning
(`MAJOR.MINOR.PATCH`), and each skill additionally carries its own
`opencoworking.version` in frontmatter.

- **Repository MAJOR**: breaking changes to the canonical schema, the
  mapping-file format, or CLI flags/output contracts.
- **Repository MINOR**: new skills, new adapters, new CLI commands,
  non-breaking schema additions.
- **Repository PATCH**: fixes, doc corrections, eval additions.
- **Skill versions** bump when the skill's workflow, output contract, or
  formulas change; a formula change is at least a skill-MINOR and is
  called out in the changelog because it changes reported numbers.

## Release checklist

A release may be tagged only when, from a clean checkout:

1. `python -m pip install -e ".[dev]"` succeeds on a supported Python
2. `python -m pytest` passes (unit + integration)
3. `python scripts/validate_skills.py`, `check_catalog.py`,
   `check_references.py`, `run_evals.py`, and
   `generate_readme_catalog.py --check` all pass
4. CHANGELOG has a dated section for the version
5. No unresolved placeholder scan hits; no secrets scan hits
6. The README quick start was executed as written

Tags are immutable once pushed; a bad release gets a new PATCH, not a
moved tag. Installation pinning: users can pin with
`gh skill install QaliAI/open-coworking-skills <skill> --pin <tag>`.

## Migration guidance

Breaking schema or CLI changes ship with a `docs/guides/migrating-<from>-<to>.md`
covering: what changed, why, mechanical steps, and how to verify outputs
match (or why they legitimately differ — formula changes list before/after
on the synthetic demo).

## Deprecation policy

- Skills: `deprecated` maturity + catalog note + replacement pointer;
  removed from `.agents/skills/` after two minor releases.
- CLI flags: warn for one minor release before removal.
- Schema fields: never silently repurposed; deprecated fields keep
  parsing for one major version.
