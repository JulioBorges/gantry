# Validated writes with per-layer authorization

Type: issue
Status: ready-for-agent
Slice: config-and-snapshot#03
Spec: [`../spec.md`](../spec.md) (spec 02, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/config-and-snapshot/spec.md`](../spec.md)

## What to build

The `config.write` operation, whole-document and transactional from the caller's perspective: the merged result is validated before anything is written, the target layer's previous file is copied to a backup sibling, and the write either fully lands or leaves the original in place.

Write authorization is per layer. A repository override attempting to set or raise a global capacity limit is rejected with the field path, because a single repository must not consume more of the machine than the operator allowed. The writing transport is `gantry config set`, with one parity test proving delegation.

This slice is what guarantees the dashboard Settings screen and the setup interview cannot reach configuration by any other path.

## Acceptance criteria

- [ ] A write whose merged result fails validation in any field leaves the previous file byte-identical on disk and returns every violation.
- [ ] A successful write produces a backup of the previous file at the target layer.
- [ ] A repository-layer write attempting to raise the global capacity limit is rejected naming the field path, while the same value written at the machine layer is accepted.
- [ ] A write interrupted partway leaves either the complete new document or the untouched original, never a half-applied one.
- [ ] `gantry config set` has one parity test proving it delegates to `config.write`; no test asserts on file formatting or key order.

## Blocked by

- `config-and-snapshot#02` — the whole-document validator that validate-before-write runs.
- `data-handling#01` — the redaction sink enforcement interface that writes must traverse.
