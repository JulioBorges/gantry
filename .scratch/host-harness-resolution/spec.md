# Spec: Resolve the active Host Harness without replacing role selections

Type: spec
Status: approved
Map: `ROADMAP.md` (spec 17)
Source: Host Harness planning handoff, 2026-09-30; PRD; ADR-0004; ADR-0006
Created: 2026-09-30

## Problem Statement

An operator opens a repository in Claude Code while its saved Gantry configuration names Antigravity. Existing setup heuristics detect installed tools or repository directories rather than proving which harness owns the current conversation. Workflow routing also has a Claude Code default. The external project's switcher leaves existing mismatches unresolved and can replace every role with fixed presets when applying a host change. This risks incorrect adapter selection and loss of intentionally chosen harnesses, models and efforts.

## Solution

Gantry reports the current Host Harness separately from repository preferences and execution-role selections. Reliable current-invocation evidence resolves the host; inconclusive evidence requires an explicit operator choice. The resolved host controls Run coordination and capability-dependent adapters while independently validated roles retain their existing selections. Setup can propose a host-only policy or adapter repair, show its complete effects, and apply only the approved change.

## User Stories

1. As an operator, I want to inspect the current host without changing files, so that diagnosis is safe.
2. As an operator, I want the saved host preference shown separately, so that stale policy is visible.
3. As an operator, I want evidence sources and resolution status reported, so that I understand the decision.
4. As an operator, I want installed binaries and skill directories treated as hints, so that installation is not mistaken for the active host.
5. As an operator, I want inherited environment hints treated as insufficient proof, so that nested invocations do not misidentify the host.
6. As an operator, I want conflicting current signals reported, so that arbitrary ordering does not choose my host.
7. As an operator, I want missing evidence to require a choice, so that no fixed harness becomes an implicit fallback.
8. As an operator, I want an explicit Run host selection, so that I can proceed when automatic resolution is inconclusive.
9. As an operator, I want unsupported host identifiers rejected, so that capability claims stay accurate.
10. As an operator, I want a stale saved preference reconciled for the Run, so that the current host coordinates work.
11. As an operator, I want my Critic on a different harness preserved, so that intentional cross-harness review still works.
12. As an operator, I want custom models and efforts preserved, so that host reconciliation does not substitute role presets.
13. As an operator, I want Issue and Run role overrides to retain precedence, so that local decisions remain effective.
14. As an operator, I want unresolved host identity to stop workflow entry, so that work does not begin under a guessed adapter.
15. As an operator, I want native versus external role routing based on the resolved host, so that each role uses the intended execution path.
16. As an operator, I want actual host capabilities reported, so that unavailable hook guarantees are never advertised.
17. As an operator, I want missing repository setup reported independently, so that host resolution does not invent policy.
18. As an operator, I want a host-only setup preview, so that I can approve concrete changes.
19. As an operator, I want unrelated and custom policy fields preserved, so that setup does not discard my configuration.
20. As an operator, I want only the chosen host adapter updated, so that other tools' settings survive.
21. As an operator, I want setup cancellation and repetition to be safe, so that declined or repeated repair has predictable effects.
22. As an operator, I want Run identity scoped to its invocation and worktree, so that another Run cannot overwrite it.
23. As an operator, I want resumption under a different host to require an explicit transition, so that existing work and budgets survive.
24. As a maintainer, I want reproducible workflow and CLI evidence, so that simulated checks and live host proof are distinguishable.

## Blueprint

### Context

The existing policy resolver, role execution resolver, setup writer, capability declarations, Run Log and plan/round workflows supply the integration boundaries. Repository policy is tracked and sparse; the prototype's convention of ignoring the entire policy is incompatible with ADR-0004 and ADR-0006. The hook compatibility fix is separate work and is not included in this Spec.

### Architecture

Extend the existing execution CLI with read-only Host Harness resolution and consume the same result at workflow entry. Keep the resolved host in invocation arguments and, for an established Run, record sanitized observational metadata in the existing machine-level Run Log. Do not introduce a repository-local override file or a second configuration precedence hierarchy.

Use the setup writer for approved repository-policy and adapter changes. Preserve role resolution precedence: Issue override, Run override, repository role default, explicitly confirmed environment default. Host resolution never contributes role presets. Planning and round workflows use one resolved Host Harness for capability selection and native/external dispatch decisions.

### Constraints

- Python standard library workflow tooling; no engine, new service, database, or Node switcher dependency.
- Setup remains the only repository-policy writer.
- Host evidence must refer to the current invocation. Unproven environment variables, executable presence, skill directories and saved preferences are hints only.
- No new support tier or identity assurance without corresponding evidence.
- No credentials, environment values, transcripts or raw process output in host diagnostics or Run Log metadata.
- Artifacts are English; execution and release remain separately authorized.

## Implementation Decisions

- Add a structured host resolution result to the execution interface: status (`resolved`, `unknown`, `ambiguous`, or `invalid`), effective host when resolved, saved preference, mismatch flag, sanitized source identifiers, and actionable diagnostics. Read-only resolution does not create policy, hooks or Run state. Unresolved diagnostics may be inspected successfully; operational preflight must fail when unresolved.
- An explicit operator-confirmed invocation selection takes precedence over saved policy and weak hints. Conflicting trustworthy current-invocation evidence still blocks until the operator explicitly resolves the conflict. Unsupported selections and malformed policy return errors rather than resetting configuration.
- Current-invocation evidence adapters must document their source and validity boundary. If a harness offers no verifiable current-invocation marker, return unknown and use explicit selection; never promote a guessed marker. Initial identities remain the four supported execution integrations, subject to actual capability declarations.
- A reliably resolved current host may differ from the saved preference. Report the mismatch and use the current host for the Run without changing tracked policy. Updating the repository preference is a separate setup proposal.
- Each workflow entry resolves once before role scheduling, worktree creation or host-dependent initialization. Propagate the result into planning, rounds, capability selection and role routing; remove implicit host fallbacks along these paths. Resolution does not bypass readiness, role validation, Result Contracts, gates or approval.
- The Run host is immutable within an invocation. Resume revalidates the current host; a change requires operator approval before continuation and records old/new identity and confirmation source. Preserve Run identity, assigned worktrees, revisions, role selections and correction budgets. Concurrent Run host records remain isolated.
- Host-only setup proposals preserve every unrelated field, including custom execution fields, derived roles, model/effort selections, checks, artifacts and Caveman. On missing policy, guide the normal setup conversation rather than silently synthesizing defaults.
- Adapter repair targets the selected host and only Gantry-owned entries, retains unrelated settings and other harness adapters, honors approved hook decisions, and reports unsupported wiring honestly. Installed binaries and common skill directories cannot select an adapter automatically.
- Setup shows policy and adapter effects before mutation, supports decline without writes, and is idempotent. Use structured arguments or configuration-file input, never shell interpolation of JSON or synthetic overwrite confirmation.
- An existing policy ignored by an adopting repository is reported as a portability concern with a proposed tracked-policy migration; never silently edit ignore rules or relocate user state.

## Testing Decisions

- Proposed primary seam: public execution resolution/preflight CLI and setup CLI, exercised through the existing temporary-Git-repository subprocess pattern. Assert exit status, structured output, policy bytes, adapter settings and dispatch observations; avoid private helper structure.
- Extend the existing canonical plan/round workflow smoke seam only to prove that both workflow entry paths consume the same resolved host and stop before work when unresolved. This integration check is necessary because CLI success alone cannot prove workflow routing.
- Prior art includes role-default/setup transcript tests, policy preservation tests, canonical workflow smoke checks and cross-harness fixture proofs. Isolated environment fixtures cover absent, weak, inherited and conflicting signals without relying on the developer's machine.
- Cover a stale Antigravity preference with Claude Code selected, a Codex-hosted Run with a Claude Code Critic, custom and derived roles, all precedence levels, malformed policy, cancellation, repeated repair, structured input containing quotes and shell metacharacters, unsupported adapters, and concurrent/resumed Runs.
- Keep simulated resolver/dispatch evidence separate from sanitized live invocation evidence. Demonstrate one stale-preference workflow on a real host; for integrations without trustworthy detection, demonstrate the documented explicit-selection path instead of claiming automatic detection.

## Contract

### Definition of Done

- [ ] Read-only diagnostics distinguish current host, saved preference and unresolved evidence without writes.
- [ ] Planning and execution require a resolved host and use it for capabilities and role routing.
- [ ] Host reconciliation preserves role selections and unrelated policy, including cross-harness roles.
- [ ] Approved host-only setup and adapter repair preserve user settings, cancel cleanly and are idempotent.
- [ ] Resumption revalidates the host and preserves Run/worktree identity and correction budgets through an approved transition.
- [ ] CLI/workflow regressions and bounded live evidence demonstrate the contract; documentation explains setup, mismatch handling and explicit selection.

### Regression Guardrails

- Repository readiness, role availability and host identity remain separate validations.
- Unknown or unsupported host identity never triggers a saved-policy or fixed-harness fallback.
- No workflow detection path changes repository policy, role defaults or hook wiring.
- Roadmap scripts retain exclusive completion authority; host changes do not grant acceptance.
- Existing hooks, Result Contracts, integration gates and Issue recovery remain enforced.

### Scenarios

```gherkin
Scenario: Saved preference differs from current host
  Given the saved preference is Antigravity and the operator selects Claude Code for this invocation
  When workflow preflight resolves the host
  Then Claude Code coordinates the Run and the mismatch is visible
  And repository policy and all role selections remain unchanged

Scenario: Ambiguous inherited hints
  Given only conflicting environment hints are available
  When workflow preflight runs without an explicit selection
  Then it requires an operator host choice before creating work or invoking roles

Scenario: Intentional external Critic
  Given Codex is the resolved host and Claude Code is selected for Critic
  When the workflow routes the Critic invocation
  Then the existing external execution path uses the selected model and effort
  And the Result Contract remains required

Scenario: Cancel a host-only repair
  Given existing policy contains custom fields and independent role selections
  When the operator declines the shown setup repair
  Then policy and adapter files remain byte-for-byte unchanged

Scenario: Repeat an approved adapter repair
  Given a selected host adapter contains unrelated user settings
  When the operator applies the same approved host-only repair twice
  Then the second application adds no duplicate Gantry entries
  And unrelated settings and other adapters remain unchanged

Scenario: Resume on another host
  Given a Run has existing Issue worktrees and a spent correction attempt
  When the operator approves resumption with a different resolved host
  Then the Run records the transition and resumes in its existing worktrees
  And role selections and the spent correction budget remain unchanged
```

## Out of Scope

- Feature implementation during this planning task; release, merge, tag or npm publication.
- Replacing all role selections when a host changes; automatic recovery or model fallback.
- Importing or executing the external prototype's mutating switch commands.
- Editing the middleware project, its ignore rules or its local Gantry installation.
- A new engine, credential store, local policy hierarchy, settings UI or dashboard redesign.
- Expanding harness support guarantees or folding the separate hook compatibility fix into this feature.

## Further Notes

The operator approved this Spec, its public CLI/workflow test seams and the four-Issue breakdown on 2026-09-30. Delivery Issues are published locally with status managed by the roadmap scripts. Planning Approval does not authorize implementation or release. Keep planning on its dedicated branch based on current main.

## Changelog

- 2026-09-30 — Review draft synthesized from the handoff and verified repository integration surfaces.
- 2026-09-30 — Operator approved the Spec, testing seams, granularity and dependencies; four delivery Issues published locally.
