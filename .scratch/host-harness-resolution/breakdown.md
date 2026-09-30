# Approved Issues: Host Harness resolution

Status: approved
Spec: `.scratch/host-harness-resolution/spec.md`
Created: 2026-09-30

The operator approved this Spec, testing seams and four-Issue breakdown on 2026-09-30. Four delivery Issues are published separately under `issues/`, with `ready-for-agent` status set through the roadmap tooling. Identifiers below are live local tracker references. Initial reading packages for Issues 02 and 04 were narrowed after budget audit; their Issue files retain focused follow-up references without changing behavior or acceptance criteria.

## 01 — Diagnose current Host Harness and stale preferences

Slice: `host-harness-resolution#01`
Blocked by: None
User stories covered: 1–9, 24

### What to build

Expose read-only structured host resolution through the existing execution CLI. Distinguish explicit invocation selection, trustworthy current-invocation evidence, weak installation/environment hints and saved preference. Report resolved, unknown, ambiguous or invalid identity, mismatch and recovery guidance. Ship usage documentation with reproducible diagnostic examples. Do not introduce a stand-alone refactor Issue: this behavior provides the shared resolution boundary needed by later slices while delivering an independently usable diagnosis.

### Files to read

- `.scratch/host-harness-resolution/spec.md`
- `.agents/skills/gantry/scripts/execution.py`
- `.agents/skills/gantry/scripts/common.py`
- `tests/test_role_execution_defaults.py`
- `docs/adr/0006-role-execution-can-use-another-harness.md`

### Acceptance criteria

- [ ] CLI subprocess tests demonstrate explicit supported selection, verified invocation evidence where available, stale saved preference, absent signals, conflicting signals and unsupported identifiers through structured output.
- [ ] Binary presence, common skill directories, inherited environment hints and saved preferences alone never produce an automatically resolved host. Document evidence provenance and the explicit-selection path for each supported identity.
- [ ] Diagnostics expose status, effective host when resolved, saved preference, mismatch and sanitized source identifiers without raw environment values or credentials.
- [ ] Policy bytes, adapter files and machine-level Run state remain unchanged during diagnosis; malformed policy is reported without overwrite or fallback.
- [ ] Public usage examples explain diagnostic exit behavior separately from blocking operational preflight and identify the limits of simulated evidence.

## 02 — Bind new workflows to a resolved Run host

Slice: `host-harness-resolution#02`
Blocked by: `host-harness-resolution#01`
User stories covered: 10–17, 22, 24

### What to build

Make planning and execution entry resolve the actual host before host-dependent initialization, worktree creation or role scheduling. Propagate the resolved host into capabilities, native/external dispatch and Run metadata while preserving role precedence and independent validations. Demonstrate an intentionally external Critic under a mismatched saved preference. Deliver workflow instructions and regression evidence with the behavior.

### Files to read

- `.scratch/host-harness-resolution/spec.md`
- `.agents/skills/gantry/scripts/execution.py`
- `.agents/skills/gantry/scripts/runlog.py`
- `.agents/skills/gantry/SKILL.md`
- `.agents/skills/gantry-plan/SKILL.md`
- `.agents/skills/gantry/reference/plan-workflow.md`
- `.agents/skills/gantry/reference/round-workflow.md`
- `tests/test_canonical_gantry_workflow.py`
- `tests/test_cross_harness_proof.py`

### Acceptance criteria

- [ ] Both entry paths reject unresolved or unsupported host identity before creating Run worktrees or invoking role agents; no implicit Claude Code or saved-policy fallback remains in the affected routing paths.
- [ ] A selected Claude Code host with a saved Antigravity preference uses Claude Code capability metadata, reports the mismatch and leaves repository policy unchanged.
- [ ] A resolved Codex host with a selected Claude Code Critic takes the existing external dispatch path, preserving model/effort and enforcing the Result Contract. A same-host selection takes the intended native path.
- [ ] All base and derived role selections, Issue/Run overrides, custom policy fields and independent readiness/availability checks retain their semantics.
- [ ] Concurrent new Runs retain separate resolved-host records; diagnostics and Run metadata contain only sanitized identity/provenance and no secrets.
- [ ] Existing workflow smoke/fixture seams exercise entry, routing and no-work-on-failure; include sanitized evidence of one real stale-preference invocation and distinguish it from mocked dispatch coverage.

## 03 — Apply an approved host-only setup and adapter repair

Slice: `host-harness-resolution#03`
Blocked by: `host-harness-resolution#01`
User stories covered: 17–21, 24

### What to build

Let setup consume host diagnosis and propose a targeted repository preference and/or host adapter repair without role presets. Preview concrete policy and adapter effects, apply only operator-approved changes and preserve unrelated configuration. Missing or ignored policy receives normal setup or portability guidance rather than an automatic overwrite. Deliver usage documentation and CLI transcript evidence as part of this behavior.

### Files to read

- `.scratch/host-harness-resolution/spec.md`
- `.agents/skills/gantry/scripts/setup.py`
- `.agents/skills/gantry/scripts/common.py`
- `.agents/skills/gantry-setup/SKILL.md`
- `tests/test_gantry_setup.py`
- `tests/test_guard_hook_wiring.py`
- `tests/test_role_execution_defaults.py`

### Acceptance criteria

- [ ] Setup CLI previews host-only policy and selected adapter effects before writes; decline, EOF and invalid identity leave files unchanged.
- [ ] Host-only application preserves all base/derived roles, custom model/effort selections, execution extensions, gates, artifacts, Caveman and unknown unrelated fields; malformed policy cannot be silently replaced.
- [ ] Only the selected host's Gantry-owned adapter entries change according to approved hook policy. Unrelated settings and other adapters remain intact; repetition produces no duplicates or further changes.
- [ ] Installed binaries and common directories do not independently choose adapters. A host without verified hook support receives honest manual guidance without fabricated enforcement.
- [ ] Configuration with quotes and shell metacharacters passes through structured arguments or configuration-file input with no shell execution; no synthetic overwrite approval is supplied.
- [ ] Missing policy requires normal setup approval; ignored existing policy yields a concrete tracked-policy migration proposal without editing ignore rules automatically.
- [ ] Setup transcript and preservation tests verify the complete path, and operator docs explain why host repair leaves role choices independent.

## 04 — Resume an existing Run with an approved host transition

Slice: `host-harness-resolution#04`
Blocked by: `host-harness-resolution#02`
User stories covered: 22–24

### What to build

On resumption, resolve the current invocation again and compare it with the prior Run host. Require a concrete operator decision for a host transition, record it, and continue through the existing workflow in the same Run and assigned worktrees. Preserve role overrides and spent correction budgets. Document and prove the resumption path rather than treating resumption as a new Run.

### Files to read

- `.scratch/host-harness-resolution/spec.md`
- `.agents/skills/gantry/scripts/execution.py`
- `.agents/skills/gantry/scripts/runlog.py`
- `.agents/skills/gantry/SKILL.md`
- `.agents/skills/gantry/reference/round-workflow.md`
- `tests/test_cross_harness_proof.py`
- `tests/test_round_workflow_lifecycle_hooks.py`
- `tests/test_runlog.py`

### Acceptance criteria

- [ ] Resumption with unknown, conflicting or unsupported host identity performs no new role work; another Run's host record cannot resolve the ambiguity.
- [ ] An unchanged resolved host resumes through the normal existing recovery path. A changed host presents old/new identity and requested effects before continuation.
- [ ] Declining a host transition leaves worktrees, revisions, role overrides and correction counts unchanged; no new Run or worktree silently substitutes for the existing one.
- [ ] Approving the transition records sanitized old/new host and confirmation provenance under the same Run and uses the newly resolved host for capabilities and role routing.
- [ ] Resumed workflow fixture evidence demonstrates existing Issue worktrees and spent correction attempts survive the transition; missing older host metadata requires explicit establishment rather than a guessed fallback.
- [ ] Concurrent worktree/Run tests prove transition metadata isolation; documentation and final verification receipts identify simulated coverage and any live resumption evidence separately.

## Dependency and coverage review

The graph is 01 → 02 → 04 and 01 → 03. Issues 02 and 03 may proceed independently after diagnosis exists; Run binding never requires a policy repair. Slice 04 handles existing Runs, not a separate test-only delivery.

All 24 User Stories are covered above. No existing Issue is a new blocker: the role-execution and standalone-planning foundations are already delivered on the planning branch's base. The unrelated hook compatibility fix remains separate; implementation must use the compatible adapter available at its eventual base revision rather than expanding that fix here.

Generated roadmap waves: 27 = 01; 28 = 02 + 03; 29 = 04. Historical completed-wave placement was preserved by the roadmap script.

## Approval record

On 2026-09-30 the operator answered "aprovado" to the presented Spec, public CLI/workflow test seams and four-slice breakdown. This approval covers publication to the local Markdown tracker and roadmap scheduling. Implementation, target-branch integration and release remain outside this planning task.
