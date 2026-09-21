# Implement Socratic Gate planning engine for free-text goals

Type: issue
Status: done
Slice: `gantry-plan#02`
Spec: `.scratch/gantry-plan/spec.md`
Created: 2026-09-19

## Parent

`gantry-plan`

## What to build

Implement the Socratic Gate engine that guides an operator from a free-text goal to a fully validated `.scratch/<slug>/spec.md`.

The engine surveys repository context in the background (reading `CONTEXT.md`, `PRD.md`, `docs/adr/`, existing modules and seams), logs `phase.started` for `<slug>#00` with `operatorWaiting: true`, and walks down the design tree across four structured phases:
1. Problem Statement & Context
2. Architectural Boundaries & Seams
3. Scope & Non-Goals
4. Verifiable Criteria & Scenarios

For each question, the engine recommends a vetted default answer based on codebase exploration. Once the interview is complete, it synthesizes `.scratch/<slug>/spec.md` according to Gantry's spec template and validates it with `spec.py --check`.

### Files to read

- `.agents/skills/gantry/templates/spec.md`
- `.agents/skills/gantry/scripts/spec.py`
- `.agents/skills/gantry/reference/plan-workflow.md`
- `tests/test_spec_validation.py`

## Acceptance criteria

- [x] Socratic Gate engine accepts a free-text goal and generates a slug for the feature.
- [x] Engine explores codebase context and structures questions across Problem, Architecture, Scope, and Criteria phases with recommended answers.
- [x] Run log events mark `<slug>#00` with `phase: "Plan"` and `data.operatorWaiting: true` during interview pauses.
- [x] Spec synthesizer outputs `.scratch/<slug>/spec.md` with Blueprint, Contract (DoD, guardrails, scenarios), Out of Scope, and Changelog.
- [x] `python3 .agents/skills/gantry/scripts/spec.py --check <specPath>` passes on the generated spec.
- [x] Unit tests in `tests/test_gantry_plan.py` verify the Socratic gate lifecycle and spec generation.

## Blocked by

- `gantry-plan#01`
