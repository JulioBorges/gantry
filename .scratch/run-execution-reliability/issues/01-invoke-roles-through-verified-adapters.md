# Invoke selected roles through a verified harness adapter

Type: issue
Status: ready-for-agent
Slice: `run-execution-reliability#01`
Spec: `.scratch/run-execution-reliability/spec.md`
Created: 2026-10-03
User stories covered: 1, 2, 3, 7, 8, 9, 10, 27, 30, 32

## Parent

`run-execution-reliability` — [Spec](../spec.md)

## What to build

Deliver a complete bounded role invocation through the existing public execution interface and canonical workflow routing. The supported adapter translates the approved harness/model/effort selection into a command accepted by the installed CLI, captures the final role result, validates its Result Contract and returns attributable success or failure. Refactor the inconsistent probe/execution runner calls inside this slice before extending the adapter; do not introduce a standalone refactor Issue. Remove the need for a Run-specific wrapper to repair argument syntax, output capture or result extraction. Keep harness-specific syntax and transport at the adapter boundary and retain the independent Host identity.

### Files to read

- `.agents/skills/gantry/scripts/execution.py`
- `docs/role-execution.md`
- `tests/test_cross_harness_proof.py`

### Focused follow-up exploration

Use focused searches for dispatch contract tests, model discovery, canonical native/external routing, Result Contract schemas and installed CLI help. Read only the relevant sections; do not preload the full canonical workflow test module. Keep effective selection provenance independent of model-written claims.

## Acceptance criteria

- [ ] The public role dispatch path, reached by a canonical workflow fixture, preserves explicit harness/model/effort selection and Issue/Run override precedence; same-host and external routing retain the resolved Host Harness and do not silently replace roles.
- [ ] A probe and a role invocation through the same subprocess-compatible runner preserve stdout, stderr, return code and cwd. A real version command succeeds through both default and injected runners; failed probes, process-start errors and timeouts produce bounded, actionable failures.
- [ ] The installed Codex CLI accepts the generated invocation syntax including the selected reasoning effort. A parser-only negative control rejects an intentionally unsupported argument. Existing fake-only tests are corrected so they no longer certify incompatible syntax by reproducing it.
- [ ] A bounded real supported role invocation in a disposable worktree produces a valid Result Contract through the declared transport, with CLI version and requested/observed selection evidence identified separately. Strict native schemas are used only where supported; generic schemas are not blindly supplied as native strict-output schemas.
- [ ] Malformed, missing or truncated final results and nonzero execution exits cannot advance acceptance or integration. Any allowed protocol-result retry is distinguishable from a code correction and remains bounded by the existing retry contract.
- [ ] Cancellation and timeout preserve the assigned worktree and code; the adapter reports what stopped and any process-cleanup limitation rather than claiming termination it cannot establish. Permission scope is preserved without silent expansion or automatic model fallback.
- [ ] Sanitized invocation/result metadata is attributable to Run, Issue, role and attempt when invoked within a Run. Prompts, raw command output, credentials and source diffs do not enter the Run log.
- [ ] Existing supported harness regression fixtures retain their contracts. Operator instructions demonstrate the supported dispatch path and distinguish actual CLI/role evidence from simulated failure coverage; green unit tests alone do not establish harness compatibility.

## Blocked by

None - can start immediately after planning approval.

## Comments

- 2026-10-03 — Prepared through to-issues as a complete vertical slice. The operator approved all five slices, story coverage and dependency relationships in conversation. Planning approval does not authorize implementation.
