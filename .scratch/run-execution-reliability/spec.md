# Spec: Reliable Run execution and truthful timing

Type: spec
Status: ready-for-agent
Map: `ROADMAP.md` (spec 18)
Source: Operator request and revised Run audit of 2026-10-02
Created: 2026-10-03
Planning: Spec, testing seams and five-Issue breakdown approved on 2026-10-03

## Blueprint

### Context

Operators experience long Gantry Runs but cannot reliably distinguish useful work from execution failure, missing verification prerequisites, Host inactivity, machine suspension or a result awaiting integration. A local audit of 22 Runs found current harness adapter incompatibilities, a Host turn ending before its launched Critic completed, repeated external verification blockers and misleading phase clocks.

### Architecture

Gantry remains a harness-neutral skill pack. The Host Harness owns conversation, agent coordination and integration. Workflow scripts retain readiness, acceptance, gates and completion authority. Harness-specific execution stays at adapter boundaries. The machine-local Run log remains observational and the Dashboard remains read-only. This work strengthens existing role execution, preflight, round workflow, Run observation and presentation contracts.

### Constraints

Preserve explicit role selection, independent Critic verification, correction ceilings, Issue worktree isolation, serial integration, repository checks, and the existing approval boundaries. Additive observational metadata must not turn the Run log into completion authority. Legacy telemetry must remain readable without inventing missing facts. Support claims must be backed by the actual declared harness capability path.

## Problem Statement

As an operator, I cannot tell whether a Run that has been open for two hours is still making progress, waiting on a result, blocked by its execution environment or stopped because the Host ended its turn. I sometimes need to say “continue” after an agent has already completed. Other Runs spend time repairing custom execution wrappers or repeating verification against prerequisites that code changes cannot supply.

The audit establishes different causes that need different responses:

- A 124.1-minute Swagger Run included 96.75 minutes of recorded machine sleep. That is not model reasoning time.
- A 189.8-minute NestJS Run included a Host final response while its launched Critic was still running. The accepted result was not integrated until a later operator message.
- Current Codex dispatch generates a reasoning-effort argument rejected by the installed CLI, while existing fake-based tests pass.
- The injected command-runner path can lose version-probe stdout even when the default runner works.
- SaaS verification repeatedly encountered unavailable infrastructure and service entitlement alongside actionable code defects.
- The current Dashboard charges execution pauses to the Critic phase and infers operator waiting solely from Critic completion.

These observations do not establish a universal model bottleneck or a safe speedup percentage.

## Solution

Provide a reliable, bounded way to execute selected roles from a supported Host Harness, preserve Host responsibility until launched work reaches a real handoff boundary, and make Run progress explain what is known about execution and waiting.

Before work that depends on a verification capability starts, check the declared prerequisite through the supported boundary. Report unavailable verification distinctly from a code defect. When code work is actionable independently of an external blocker, preserve that distinction rather than repeatedly claiming that another correction can satisfy the external requirement.

During execution, retain the operator's approved choices, consume completed results promptly while the Host is active, and advance the existing acceptance and integration steps without an invented extra approval. On interruption or loss of capability, preserve work and present an honest resumption state.

Show elapsed Run time, recorded phase intervals, known pauses, results pending Host handling and unknown/stale periods with their provenance and limitations. Never equate a heartbeat with useful progress or a missing event with a known cause.

## User Stories

1. As an operator, I want the selected role invocation to be accepted by my installed harness CLI, so that execution does not fail on an unsupported argument.
2. As an operator, I want requested harness, model and reasoning effort to reach the actual invocation, so that approved settings are preserved.
3. As an operator, I want effective execution settings reported only when they are evidenced, so that requested settings are not mistaken for observed behavior.
4. As an operator, I want preflight to distinguish version, authentication, model availability and verification capability, so that a partial check is not reported as complete readiness.
5. As an operator, I want identical execution checks reused within their valid Run scope, so that preflight does not add unnecessary repeated work.
6. As an operator, I want checks invalidated after relevant execution settings change, so that stale readiness is not reused.
7. As a Host Harness integrator, I want one consistent runner contract for probes and role execution, so that output capture and errors behave consistently.
8. As a Host Harness integrator, I want the supported adapter to extract and validate role results, so that I do not need to invent a new temporary wrapper for each Run.
9. As an operator, I want schema or result transport failures identified separately from code findings, so that recovery addresses the correct problem.
10. As an operator, I want approved permission scope respected by child execution, so that missing access is detected without silent privilege expansion.
11. As an operator, I want the Host to remain responsible for roles it has launched, so that I do not need another message just to consume a completed result.
12. As an operator, I want a status question during an active Run answered without silently ending authorized work, so that checking progress does not stop delivery.
13. As an operator, I want accepted work to advance through existing integration gates while the Host remains active, so that a ready result is not left unattended.
14. As an operator, I want a clear handoff when I interrupt execution or the harness cannot continue, so that the Run does not falsely appear to be progressing.
15. As an operator, I want resumption to use the existing Run, worktree and correction accounting, so that interruptions do not restart completed work or reset limits.
16. As an operator, I want unavailable verification prerequisites identified before dependent work is scheduled, so that I do not spend correction attempts on impossible acceptance.
17. As an operator, I want actionable code defects distinguished from infrastructure blockers, so that useful corrections can proceed without hiding missing proof.
18. As an operator, I want an unchanged external blocker to pause repeated verification, so that the same missing dependency does not trigger another unproductive cycle.
19. As an operator, I want resumption to recheck the relevant prerequisite, so that merely saying “continue” is not treated as proof that the environment changed.
20. As an operator, I want a waiting state to identify the actual required decision, so that the Dashboard does not ask for approval where none is required.
21. As an operator, I want execution pauses excluded from phase-work clocks, so that a short Critic run does not appear to have spent its pause working.
22. As an operator, I want result-ready and awaiting-integration states distinguished from executing and awaiting-operator states, so that I understand the next responsible action.
23. As an operator, I want known machine or harness interruptions attributed only when supported by evidence, so that unexplained gaps remain honestly unknown.
24. As an operator, I want a long-running role to expose available liveness information, so that I can distinguish a live process from a stale observation without assuming useful progress.
25. As an operator, I want durations across parallel Issues calculated without double counting, so that total Run time remains meaningful.
26. As an operator, I want legacy logs with missing or out-of-order lifecycle events marked as incomplete, so that reports do not invent precise history.
27. As a maintainer, I want adapter tests to exercise the real supported invocation boundary, so that fake CLIs cannot certify incompatible command syntax.
28. As a maintainer, I want lifecycle tests to include delayed child results, interruption and resumption, so that premature Host completion becomes a visible regression.
29. As a maintainer, I want Dashboard changes verified through real browser interactions, so that displayed state and accessibility match the observable contract.
30. As an operator, I want independent Critic verification and integration gates retained, so that shorter Runs still establish complete delivery.
31. As an operator, I want a Run report to distinguish observed timing from estimated or unknown timing, so that I can prioritize improvements using trustworthy measurements.
32. As an operator, I want planning, execution recovery, PR and cleanup decisions to retain their existing boundaries, so that improved continuity does not imply new authorization.

## Implementation Decisions

- Keep role execution within the existing Host/adapter model and the standing skill-pack architecture. No independent scheduling engine is introduced.
- Establish a single consistent command-runner contract covering version/authentication probes, supported execution probes, bounded role invocation, captured results, timeout and cancellation outcomes.
- Translate generic role selections to the installed harness's supported argument/configuration interface at the adapter boundary. Preserve requested settings; expose unavailable or unverifiable selections without fallback.
- Validate result transport according to the capability actually used. A generic Result Contract is not automatically a valid native strict-output schema. Post-execution contract validation remains authoritative wherever the harness cannot enforce it directly.
- Distinguish cheap local preflight from an actual model execution probe. Deduplicate equivalent checks within a Run using non-secret execution identity and invalidate after relevant changes. Never label a model verified merely because a nonempty ID, CLI version or login check passed.
- Keep a launched invocation associated with its Run, Issue, role, attempt, assigned worktree and delivered revision when known. Record dispatch, result availability and result consumption separately when the supported harness exposes those observations.
- The Host's workflow contract must continue already-authorized work after a status response while it has the required execution capability. Ending an execution turn with a pending child requires an explicit interruption, real blocker, deliberate authorized handoff or declared harness limitation.
- Preserve deterministic acceptance, clean-tree requirements, independent Critic checks and serial integration before any Issue becomes done.
- Represent missing verification capability and operator decisions separately from code corrections. A pure external wait does not consume a code correction attempt; a mixed finding may still contain a legitimate correction. Existing spent budgets remain preserved.
- Discover readiness from declared Issue acceptance needs and repository checks. Do not invent provider readiness or amend approved scope. When satisfying a prerequisite requires an Issue split or changed acceptance, present a Plan Amendment.
- Define observational lifecycle states with explicit transition causes. A completed Critic alone does not imply operator approval is needed. Preserve any genuinely configured post-Critic human gate and its existing authorization; do not remove it as a timing optimization. A paused invocation does not continue accumulating phase-work duration.
- Keep elapsed wall time distinct from measured command durations and known waiting/suspension intervals. A report must state what each measure includes. Use monotonic elapsed measurements where appropriate for a live interval, while documenting suspend and cross-process limitations.
- Use additive, sanitized metadata and preserve legacy events. Do not persist prompts, command output, source diffs or credentials in the Run log. Missing evidence remains unknown.
- Expose these distinctions through the existing read-only reporting and Dashboard surfaces. Optional platform-specific suspension evidence belongs at an adapter boundary; absence of an OS signal must not prevent honest unknown-state reporting.
- Implement in vertical increments after the approved breakdown. Reliability comes before speculative gate caching, context compression or scheduling changes.

## Testing Decisions

The approved primary seam is the existing canonical Run workflow exercised in a temporary Git fixture through the supported Host execution boundary. Observe public outputs, Result Contract validation, Run events, branch/Issue state, and read-only reporting. Test accepted behavior and failure handling rather than private helpers or exact internal command arrays.

Two supporting seams are necessary because their contracts cannot be established by a simulated workflow alone:

- The actual installed harness CLI boundary: local help/parser checks for generated options and a bounded declared capability exercise for effective selection and result handling. Fakes remain useful for deterministic failures but cannot substitute for compatibility evidence.
- The existing read-only Dashboard interface: deterministic event replay through its public data surface, with Playwright verification of visible states, timing labels, keyboard behavior, responsive layout and accessibility when frontend code changes.

Prior art includes canonical workflow fixtures, role dispatch subprocess tests, recovery/lifecycle tests, Run-log tests and Dashboard HTTP tests. Strengthen those seams rather than adding a new service or a parallel testing architecture.

Required cases include delayed role completion without a new operator message; status questions during execution; explicit interruption; unsupported CLI syntax; unavailable model; missing/invalid result; runner capture failure; timeout; changed execution settings; missing Docker or other declared verification prerequisites; mixed code/external findings; unchanged blockers; same-Run resumption; accepted-result awaiting integration; real approval waits; nonoverlapping timing categories; parallel intervals; machine suspension when observable; and incomplete legacy logs.

The regression must demonstrate that the installed CLI accepts the emitted invocation shape while deliberate unsupported syntax fails. Do not replace the real CLI with a fake that accepts whatever the production command builder emits.

No unconditional speedup threshold is asserted from this historical sample. Acceptance proves removal of specific failure modes and truthful accounting. Subsequent performance comparisons must use comparable workloads, effective execution settings and the same verification requirements.

## Contract

### Definition of Done

- [ ] The supported role execution path passes actual CLI compatibility checks and preserves evidenced selected settings through validated results.
- [ ] Probe and execution runner calls preserve captured output, exit status and bounded failure behavior consistently.
- [ ] A delayed accepted role result proceeds to the existing completion steps without another operator message in a supported Host fixture.
- [ ] Explicit interruptions, real blockers and required approvals still stop execution correctly and preserve same-Run recovery state.
- [ ] Missing verification prerequisites cause a distinguishable pause and cannot be satisfied by an unchanged correction retry.
- [ ] Pauses, execution, operator decisions and result handling have distinct observable states and durations without overlapping attribution.
- [ ] Dashboard and report show incomplete or unknown observations honestly and handle legacy logs without rewriting them.
- [ ] Relevant existing gates and independent Critic verification pass; frontend changes carry real Playwright evidence.

### Regression Guardrails

- Issue Status and criteria remain the authority on completion; observational events never grant acceptance.
- Requested harness/model/effort, existing correction counts and assigned worktrees are not silently replaced or reset.
- Unknown evidence remains incomplete; no test, verification requirement or approval boundary is weakened to reduce time.
- Repository policy changes remain subject to the existing setup workflow.
- No behavior assumes an agent or Host continues running after its harness closes.

### Scenarios

```gherkin
Scenario: A completed child is consumed without another operator message
  Given an authorized Run with a supported active Host and a delayed Critic invocation
  When the Critic returns an accepted Result Contract for the delivered revision
  Then the Host consumes that result and runs the existing integration checks
  And completion is recorded only after the checks and clean-tree requirements pass

Scenario: The real CLI rejects an unsupported generated argument
  Given a selected role and an installed supported harness CLI
  When the adapter validates the generated invocation shape
  Then unsupported syntax is reported before dependent implementation starts
  And a fake accepting that syntax cannot establish compatibility

Scenario: Verification depends on an unavailable external capability
  Given an Issue whose acceptance requires a declared capability that is unavailable
  When the workflow evaluates readiness or a result exposes that missing capability
  Then it records a verification pause with the required remedy
  And it does not spend a code correction attempt merely waiting for that remedy

Scenario: A pause does not inflate phase work time
  Given an invocation that pauses and later resumes
  When its durations are reported
  Then the known paused interval is separate from recorded phase work intervals
  And missing observations remain explicitly unknown

Scenario: Critic completion is not an invented operator approval
  Given accepted Critic evidence with no pending operator decision
  When the result awaits Host integration
  Then the read-only view identifies result handling as pending
  And it does not label the Issue as awaiting operator approval

Scenario: An interrupted Host resumes preserved work
  Given an operator-interrupted Run with an existing worktree and spent correction budget
  When the operator resumes through the validated recovery path
  Then the existing Run and worktree are reused with the preserved budget
  And the relevant execution and verification capabilities are rechecked
```

## Out of Scope

- An independent Gantry daemon, scheduling engine, database or mutating Dashboard.
- Preventing macOS lid-close suspension, silently changing power settings, or promising progress while the Host is unavailable.
- Removing or merging the Reviewer and Critic, weakening gates, or sharing acceptance authority with implementers.
- Automatically expanding permissions, changing models, repairing external infrastructure, purchasing service entitlements or publishing remote artifacts.
- Generic context compression, model benchmarking, broad gate caching, or a concurrency/scheduler rewrite.
- Changing approved Issue dependencies, decompositions or acceptance criteria without a Plan Amendment.
- Rewriting historical Run logs or claiming exact active time when observations do not support it.
- Implementing the underlying SaaS, proxy, architecture-gate or Middleware fixes used as diagnostic examples.

## Further Notes

The empirical audit is attached separately. Its examples justify the selected failure modes but are not a comparative benchmark across harnesses or models. A supported capability must be described at the level demonstrated by the fixture, including any limitation of conversational Host continuation.

On 2026-10-03 the operator accepted the proposed direction and testing seams and requested publication of the Spec, vertical Issues and roadmap update. The Spec is published with ready-for-agent triage. The operator subsequently approved the five-Issue breakdown and its dependencies through to-issues; the canonical Issues are ready for agent selection. Neither Spec triage nor breakdown approval starts an implementation Run.

See [audit evidence](evidence.md) and [proposed breakdown](breakdown.md) for the historical basis and delivery coverage.

## Changelog

- 2026-10-02 — Draft synthesized from the revised Run audit.
- 2026-10-03 — Spec and testing seams accepted; published to the local tracker, followed by approval of the five-Issue breakdown and its dependencies.
