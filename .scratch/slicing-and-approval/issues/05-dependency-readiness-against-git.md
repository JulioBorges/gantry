# Dependency Readiness evaluated against Git

Type: issue
Status: ready-for-agent
Slice: slicing-and-approval#05
Spec: [`../spec.md`](../spec.md) (spec 09, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/slicing-and-approval/spec.md`](../spec.md)

## What to build

Implement the Dependency Readiness predicate consumed at dispatch. A PBI is dependency-ready only when every prerequisite's state is `integrated` or `externally_integrated` **and** the dependent's starting base actually contains each prerequisite's integrated changes, verified against the real Git repository rather than against a recorded status field. The stale-base failure is invisible to a status field, which is why the second condition must be evaluated independently.

An unmet prerequisite produces `dependency_not_ready` naming the specific prerequisite and which of the two conditions failed, and the PBI rests in `awaiting_dependency` — a scheduling state distinct from `awaiting_operator`. Expose the predicate through the operation core so the execution loop calls it rather than reimplementing it.

Tests need a real temporary Git repository with actual integration history; readiness is never read from a persisted field.

## Acceptance criteria

- [ ] Dispatch of a dependent whose prerequisite is `implementation_complete` is rejected `dependency_not_ready`; so is one whose prerequisite has passing gates and an open Pull Request.
- [ ] Dispatch of a dependent whose prerequisite is `integrated` but whose starting base predates the integration is rejected, proving the second condition is evaluated independently of the first.
- [ ] Dispatch succeeds once the prerequisite is integrated and the base contains it; until then the PBI is `awaiting_dependency` and never `awaiting_operator`.
- [ ] The rejection names the unmet prerequisite and the failing condition.
- [ ] Two dependency-ready PBIs are both eligible concurrently; a dependent of an unintegrated PBI is not.
- [ ] Readiness is computed at evaluation time and never read from a persisted readiness field.

## Blocked by

- `slicing-and-approval#01` — provides the persisted plan proposal and declared prerequisites the predicate evaluates.
- `git-integration#01` — provides "the applicable target" and starting-base resolution under the Git Workflow Policy.
- `execution-core#03` — provides the PBI integration states (`integrated`, `externally_integrated`) and the `awaiting_dependency` scheduling state in the Execution State Machine.
