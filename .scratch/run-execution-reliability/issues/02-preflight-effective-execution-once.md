# Preflight effective execution with honest reusable evidence

Type: issue
Status: ready-for-agent
Slice: `run-execution-reliability#02`
Spec: `.scratch/run-execution-reliability/spec.md`
Created: 2026-10-03
User stories covered: 4, 5, 6, 9, 10, 27, 32

## Parent

`run-execution-reliability` — [Spec](../spec.md)

## What to build

Make an operator-selected execution profile travel from effective role resolution through preflight to a clear readiness outcome before dependent role work starts. Distinguish local CLI compatibility, authentication, model/effort availability, result transport and approved permissions. Reuse equivalent checks only within their valid Run scope, and revalidate after relevant changes. Explain unsupported or unknown capability in the public preflight result and Host handoff instead of presenting version/login success as proof of executable model availability.

### Files to read

- `.agents/skills/gantry/scripts/execution.py`
- `.agents/skills/gantry/scripts/discovery.py`
- `tests/test_role_execution_defaults.py`

### Focused follow-up exploration

Inspect only the affected setup selection, capability, canonical preflight and discovery tests. Consult the adapter contract delivered by Issue 01. Native discovery evidence and bounded live probes are different sources; preserve their provenance.

## Acceptance criteria

- [ ] The public preflight result separates the checked dimensions and distinguishes verified, unavailable and unknown execution capability. A nonempty model ID, successful version probe or login check alone cannot mark a selected model/effort profile executable.
- [ ] Canonical planning and execution entry consume that result before dependent role invocation. Unsupported syntax, unavailable model/effort, invalid transport or missing approved access stops the affected selection with a remedy while preserving policy, worktree and role defaults.
- [ ] Where discovery cannot establish availability, the supported path uses an operator-authorized bounded non-editing execution probe or reports unknown and pauses. A real selected-profile receipt is identified separately from simulated negative cases; no unverified account capability is fabricated.
- [ ] Repeated roles sharing an identical effective profile reuse applicable checks within that Run; test observations demonstrate that unchanged reusable probes are not reissued for every role or attempt. No cross-Run cache is implicitly trusted.
- [ ] Changing CLI/adapter identity, model, effort, result transport, approved permissions, relevant cwd/policy context or available authentication identity invalidates affected evidence. Unverifiable identity is not treated as a cache hit; no credential value is persisted in a key or log.
- [ ] Cheap read-only probes and actual role execution probes have separate bounded behavior. A timeout, invalid probe result or failed authentication cannot accidentally become successful reusable evidence.
- [ ] Existing Issue override, Run override, repository default and confirmed environment-default precedence remains intact. Native and external roles use their own validated selection; an external role never changes the Host Harness.
- [ ] Public documentation and workflow fixture traces show both a ready path and a refused path, including when the operator must select a replacement. No policy change, permission expansion or model fallback occurs as an automatic preflight repair.

## Blocked by

- `run-execution-reliability#01`

## Comments

- 2026-10-03 — Prepared through to-issues as a complete vertical slice. The operator approved all five slices, story coverage and dependency relationships in conversation. Planning approval does not authorize implementation.
