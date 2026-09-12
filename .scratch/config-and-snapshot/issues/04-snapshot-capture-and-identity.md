# Execution Rule Snapshot capture and identity

Type: issue
Status: ready-for-agent
Slice: config-and-snapshot#04
Spec: [`../spec.md`](../spec.md) (spec 02, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/config-and-snapshot/spec.md`](../spec.md)

## What to build

Capture of the Execution Rule Snapshot by the core at execution start, before the Planning Approval transition, stored immutably. Its contents are the resolved effective configuration document, content hashes and resolved paths of the governance documents in effect (constitution, applicable ADRs, root `AGENTS.md`, approved spec and PBI artifacts), the approved verification commands each with working directory, environment variable references, declared effects, declared Check Resources and Check Stability criterion, the observed versions of the tools those commands invoke, the effective Artifact Location Mapping, and the engine and protocol versions.

Identity is a hash over canonicalized snapshot content, so identical rules yield one identity and any change yields a new one. Governance document content is hashed rather than copied, with the resolved location retained so versioned content is recoverable from Git; a hash whose content cannot be recovered is a missing-source condition to reconcile, not a reason to proceed.

Every dispatch, approval, finding, gate result, and Merge Authorization records its governing snapshot identity, and a record whose snapshot is unavailable blocks rather than being silently reinterpreted.

## Acceptance criteria

- [ ] An execution started under one configuration continues under it after a subsequent edit to configuration, the constitution, or an ADR; a new execution started after the edit captures a different snapshot identity.
- [ ] Two executions whose captured inputs are identical share one snapshot identity; changing any single captured input — a config field, a governance document's content, an approved verification command, a tool version — produces a different one.
- [ ] A decision record carries its snapshot identity, and a record whose snapshot is missing blocks with a reconciliation-required rejection rather than resolving against current configuration.
- [ ] A snapshot does not grant permission for something its own captured rules forbid, and does not justify using a stale target revision — current-target verification still applies at integration.
- [ ] Snapshots are never removed while any record references them.
- [ ] Content hashes are computed over normalized content, not over bytes on disk.

## Blocked by

- `config-and-snapshot#01` — the resolved effective configuration document that the snapshot captures.
- `data-handling#01` — the normalized content hashing rule (line endings) used for governance document hashes.
- `execution-core#01` — the atomic transition-plus-audit persistence the snapshot record is written through.

## Notes

- 2026-09-12 — Dependency on `repository-readiness#01` removed to break a cycle in the blocker graph. The snapshot captures registered sections through a section registry declared here (name, schema version, canonical serialization); repository-readiness#01 registers the Artifact Location Mapping section. The capture is tested with a fixture section. Recorded in `.scratch/gantry-v4/slice-index.md`, *Dependency graph repair*.
