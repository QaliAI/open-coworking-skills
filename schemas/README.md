# Schemas

[`coworking.schema.json`](coworking.schema.json) is a JSON Schema (2020-12)
document whose `$defs` hold one schema per entity in the vendor-neutral model.
Property names double as the canonical CSV headers of the generic CSV format
(see [`adapters/generic-csv/`](../adapters/generic-csv/README.md)).

Values are typed as strings because the canonical interchange format is CSV
export text; parsing rules (dates, money, booleans) live in
`src/opencoworking/normalize.py` and are described per-field in the schema
descriptions.

Prose documentation of the model: [`references/data-model/`](../references/data-model/README.md).
