# Demo script

Run from a clean checkout after `python -m pip install -e .`

```bash
python -m opencoworking.cli demo
```

That command finds the Northstar export shipped in the repo, writes a draft health check to a new temporary folder, and prints the path. It does not finalize. It does not send.

Say these sentences while the draft is on screen:

- This operator is fictional.
- Office occupancy, workstation occupancy, and financial occupancy are printed separately.
- Unbilled membership amount, overdue invoices, and idle list price are separate findings.
- The page says draft. A reviewed file needs a person's name and an attestation.

Optional second command, the occupancy JSON:

```bash
python -m opencoworking.cli occupancy --inventory examples/synthetic-space/data/inventory.csv --memberships examples/synthetic-space/data/memberships.csv --as-of 2026-07-01 --format json
```

Expected values include 0.7143, 0.5758, and 0.6370.

A wizard that interviews a non-technical operator is not in 0.1.0. `demo` is the one-command path. A wizard can wait for 0.2.0.
