# Implement tracer-bullet vertical slicing engine with automated gates and operator quizzing

Type: issue
Status: done
Slice: `gantry-plan#03`
Spec: `.scratch/gantry-plan/spec.md`
Created: 2026-09-19

## Parent

`gantry-plan`

## What to build

Implement the vertical slicing engine that breaks an approved spec down into tracer-bullet implementation issues adhering to `to-issues` principles and Gantry issue structure.

When invoked with a spec:
1. Validates the spec structurally (`spec.py --check`) and via `Requirement Critic`.
2. Slices the requirements into thin vertical tracer bullets cutting end-to-end across layers, placing prefactoring requirements into the earliest issue.
3. Generates issue files under `.scratch/<slug>/issues/NN-<slug>.md` with `Status: draft`, Gantry metadata headers, `### Files to read` under `## What to build`, observable checkbox criteria, and explicit `## Blocked by` lines.
4. Executes deterministic context budget validation using `budget.py --json` and runs adversarial `Plan Critic` to audit granularity, coverage, and DAG validity (`frontier.py --scope <slug> --include-parked`).
5. Quizzes the operator on granularity, dependency order, and split/merge preferences before persisting.

### Files to read

- `.agents/skills/gantry/templates/issue.md`
- `.agents/skills/gantry/scripts/budget.py`
- `.agents/skills/gantry/scripts/frontier.py`
- `.agents/skills/gantry/reference/plan-workflow.md`

## Acceptance criteria

- [x] Slicing engine validates the input spec with `spec.py --check` before decomposing.
- [x] Decomposes requirements into vertical tracer bullets with prefactoring identified in the earliest slice.
- [x] Draft issues are written to `.scratch/<slug>/issues/NN-<slug>.md` with valid Gantry headers, `### Files to read`, criteria, and acyclic `## Blocked by`.
- [x] Context budget is measured for each issue with `budget.py` and flagged if over budget.
- [x] Plan Critic audits the draft issues and reports actionable findings.
- [x] Slicing presents a quiz to the operator covering granularity, dependencies, and split/merges.
- [x] Unit tests in `tests/test_gantry_plan.py` verify tracer-bullet generation, budget validation, and DAG acyclicity.

## Blocked by

- `gantry-plan#01`
