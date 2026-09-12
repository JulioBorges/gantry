# Whole-document validation and secret rejection

Type: issue
Status: ready-for-agent
Slice: config-and-snapshot#02
Spec: [`../spec.md`](../spec.md) (spec 02, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/config-and-snapshot/spec.md`](../spec.md)

## What to build

Validation that runs on the merged document rather than per layer, because the constraints that matter are relational: a repository capacity limit cannot exceed the global one, a file-mutating role cannot be routed to a gateway, a check declaring a shared Check Resource must declare its serialization behavior. Validation returns every violation at once, each naming the field path and the layer that supplied the offending value, and surfaces through `config.read` so an invalid merged document is refused at read time with no write involved.

Secret rejection is two layers. The schema has no field whose type admits a credential value — credentials are referenced by environment variable name only, and a name field whose content does not look like an environment variable name is rejected. On top of that sits a scan rejecting any string anywhere in the document that matches the configured secret detectors. The scan is a defense against accident, not a security boundary; the boundary is the absence of a field to put a secret in.

## Acceptance criteria

- [ ] Two layers that are each individually valid but whose merged result violates a relational constraint are rejected, naming both the field path and the supplying layer.
- [ ] A document violating several constraints reports all of them in one rejection, not the first.
- [ ] A file-mutating role routed to a gateway is rejected; a check declaring a shared Check Resource without serialization behavior is rejected.
- [ ] A string matching a secret detector anywhere in the document is rejected, including in a field whose name gives no hint it holds one.
- [ ] A credential field populated with a value rather than an environment variable name is rejected; no schema field exists whose declared type accepts a credential value (provable at type level).

## Blocked by

- `config-and-snapshot#01` — the merged effective document and layer provenance that validation runs over.
- `data-handling#02` — the secret detector ruleset consumed by the document-wide scan; the schema-shape half of secret rejection depends on nothing and can proceed against a fixture detector set.
