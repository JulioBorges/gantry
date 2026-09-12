# Eligibility conjunction, joint capacity accounting, and typed dispatch rejections

Type: issue
Status: ready-for-agent
Slice: pbi-execution-loop#02
Spec: [`../spec.md`](../spec.md) (spec 11, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/pbi-execution-loop/spec.md`](../spec.md)

## What to build

`pbi.schedule` answers the host harness with either a dispatch or a typed reason, and `pbi.dispatch` evaluates eligibility as a conjunction of five conditions: Dependency Readiness verified against Git, a recorded planning approval for the current plan version, capacity available at every applicable limit evaluated jointly, no competing current ownership, and check resources available. A failed condition produces a rejection naming that specific condition. The conjunction is the single point where five independent conditions must hold together; no code path may let one condition be evaluated in isolation, because that reintroduces the bypass this behavior exists to prevent.

Capacity is evaluated across global, repository, and driver limits together, and a repository or driver setting can never raise the global ceiling. Waiting states are persistent and distinct: `awaiting_dependency` for the dependency condition and `queued` for the capacity condition, with `awaiting_operator` reserved exclusively for an agent-reported `blocked` result, so an operator is never asked to answer a question nobody posed.

Condition five is consulted through an injected resource-availability port whose real implementation lands in `pbi-execution-loop#07`. For the duration of this slice the port is satisfied by a fake, which is why this slice does not block on `verification-adapters`; the shape of the conjunction is what this slice proves, and its rejection must still name the occupied resource. The scheduling operation gets one CLI and one MCP parity test.

## Acceptance criteria

- [ ] Dispatch is rejected with the specific unmet condition named, separately, for each of: unready dependency, missing or stale planning approval, exhausted capacity, competing ownership, occupied check resource.
- [ ] A repository capacity limit configured above the global limit yields effective capacity equal to the global limit.
- [ ] Under a global limit of two, a third eligible PBI stays `queued` and is dispatched when a slot frees, with no dispatch above the limit at any point.
- [ ] `awaiting_dependency`, `queued`, and `awaiting_operator` are distinguishable in the projection, and a PBI waiting on a prerequisite is never presented as needing an operator answer.
- [ ] Two concurrent start requests for one PBI resolve to exactly one owner; two concurrent start requests for distinct eligible PBIs both proceed.
- [ ] The CLI and MCP surfaces for scheduling delegate to `invoke` and return the same outcome as the in-process call.

## Blocked by

- `pbi-execution-loop#01` — the worktree and lease the dispatch success path creates.
- `execution-core#03` — `pbi.schedule`, `pbi.dispatch`, `pbi.claimOwnership`, ownership arbitration, and the `capacity_unavailable` / `dependency_not_ready` rejection codes.
- `execution-core#02` — the version-bound Planning Approval record and the `approval_required` rejection.
- `slicing-and-approval#05` — Dependency Readiness evaluated against Git.
- `slicing-and-approval#01` — plan version identity.
- `slicing-and-approval#06` — the Planning Approval binding that makes an approval stale when the plan version changes.
- `config-and-snapshot#01` — the global, repository, and driver capacity limit values and the rule that a narrower layer never raises the global ceiling.
