# Diagnose current Host Harness and stale preferences

Type: issue
Status: done
Slice: `host-harness-resolution#01`
Spec: `.scratch/host-harness-resolution/spec.md`
Created: 2026-09-30
User stories covered: 1–9, 24

## Parent

`host-harness-resolution`

## What to build

Expose read-only structured host resolution through the existing execution CLI. Distinguish explicit invocation selection, trustworthy current-invocation evidence, weak installation/environment hints and saved preference. Report resolved, unknown, ambiguous or invalid identity, mismatch and recovery guidance. Ship usage documentation with reproducible diagnostic examples. Do not introduce a stand-alone refactor Issue: this behavior provides the shared resolution boundary needed by later slices while delivering an independently usable diagnosis.

### Files to read

- `.scratch/host-harness-resolution/spec.md`
- `.agents/skills/gantry/scripts/execution.py`
- `.agents/skills/gantry/scripts/common.py`
- `tests/test_role_execution_defaults.py`
- `docs/adr/0006-role-execution-can-use-another-harness.md`

## Acceptance criteria

- [x] CLI subprocess tests demonstrate explicit supported selection, verified invocation evidence where available, stale saved preference, absent signals, conflicting signals and unsupported identifiers through structured output.
- [x] Binary presence, common skill directories, inherited environment hints and saved preferences alone never produce an automatically resolved host. Document evidence provenance and the explicit-selection path for each supported identity.
- [x] Diagnostics expose status, effective host when resolved, saved preference, mismatch and sanitized source identifiers without raw environment values or credentials.
- [x] Policy bytes, adapter files and machine-level Run state remain unchanged during diagnosis; malformed policy is reported without overwrite or fallback.
- [x] Public usage examples explain diagnostic exit behavior separately from blocking operational preflight and identify the limits of simulated evidence.

## Blocked by

- None

## Comments

- 2026-09-30 — Operator approved the Spec, test seams and four-Issue breakdown in conversation. Planning approval does not authorize implementation.
