# Dependency graph validation at planning

Type: issue
Status: ready-for-agent
Slice: slicing-and-approval#04
Spec: [`../spec.md`](../spec.md) (spec 09, wave 2)
Created: 2026-09-12

## Parent

[`.scratch/slicing-and-approval/spec.md`](../spec.md)

## What to build

Implement `PBI-DEPS-RESOLVABLE` and the breakdown-level acyclicity rule over the persisted prerequisites. Every prerequisite must resolve to a PBI in the same plan, self-dependency is rejected, and the whole graph is validated acyclic with the offending cycle named in the finding.

The validated graph is the same structure that feeds the plan version hash defined in `slicing-and-approval#01`, so a graph edit changes the plan identity. The output is a resolved graph projection that the dashboard and the execution loop can read without re-deriving it.

Validation here is purely structural: this slice touches no Git and consults no PBI status, which is what keeps it independent of the Git-backed readiness work in `slicing-and-approval#05`.

## Acceptance criteria

- [ ] A cyclic graph, a self-dependency, and a prerequisite referencing a nonexistent PBI each fail `PBI-DEPS-RESOLVABLE`.
- [ ] A cycle finding names the participating PBI identifiers, not just the fact of a cycle.
- [ ] A valid graph produces a persisted resolved-graph projection; adding or removing an edge produces a different `PlanVersionId`.
- [ ] No dependency rule consults integration state or any PBI status — validation is purely structural at this stage.

## Blocked by

- `slicing-and-approval#01` — provides the persisted prerequisites, the plan proposal record, and the plan version hash the graph feeds into.
