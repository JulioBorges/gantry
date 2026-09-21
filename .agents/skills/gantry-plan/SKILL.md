---
name: gantry-plan
description: Socratic Gate planning and tracer-bullet vertical slicing. Guides interactive goal discovery, challenges architectural assumptions, decomposes specs into thin vertical slices, audits token budgets, and validates through Plan Critic.
argument-hint: <spec-slug | spec-path | "free-text goal">
---

# Gantry Plan

A harness-neutral planning skill that unifies Socratic interviewing and tracer-bullet
vertical slicing (`to-issues` pattern). It turns unrefined goals or raw specs into
verifiable, end-to-end demonstrable Issues scheduled into execution waves.

```
Goal or Spec → [Socratic Gate / Spec Validation] → Tracer-Bullet Slicing
             → Budget Audit → Plan Critic → Operator Quiz → Approval Transition
             → Execution Handoff
```

## Dual Entry Modes

### 1. Free-Text Goal

When invoked with a free-text prompt or goal (e.g. `/gantry-plan "add webhook support"`):
1. **Context Exploration**: Explore repository context in the background:
   - Glossary: `CONTEXT.md`
   - Requirements: `PRD.md`
   - Standing decisions: `docs/adr/`
   - Existing modules under `scripts/` and `.agents/skills/`.
2. **Telemetry Initiation**: Emit a `phase.started` event in the Run log for milestone
   `<slug>#00` with `phase: "Plan"` and `data.operatorWaiting: true`. The Gantry Kanban
   dashboard displays an *"Awaiting Operator"* badge in the `Plan` column.
3. **Socratic Gate Interview**: Guide the operator across 4 structured phases:
   - **Problem Statement & Context**: Pain point, concrete use case, user personas.
   - **Architectural Boundaries & Seams**: Seam locations, CLI/API contracts, dependencies.
   - **Scope & Non-Goals**: Strictly in-scope capabilities vs explicit out-of-scope boundaries.
   - **Verifiable Criteria & Scenarios**: Acceptance criteria and primary Gherkin scenarios.
   Each question presents a concise recommended answer based on repository conventions.
4. **Operator Response Logging**: When the operator answers, record `operator.approved`
   in the Run log for `<slug>#00`.
5. **Spec Synthesis**: Generate `.scratch/<slug>/spec.md` conforming to the Gantry spec template
   (`Blueprint`, `Contract`, `Definition of Done`, `Regression Guardrails`, `Scenarios`,
   `Out of Scope`, `Changelog`).
6. **Spec Verification**: Verify the synthesized spec passes `python3 <skillDir>/../gantry/scripts/spec.py --check <spec-path>`.

### 2. Spec-Provided

When invoked with an existing spec path or slug (e.g. `/gantry-plan .scratch/auth/spec.md` or `/gantry-plan auth`):
1. Validate the spec structurally via `python3 <skillDir>/../gantry/scripts/spec.py --check <spec-path>`.
2. Run read-only Requirement Critic evaluation (checking for ambiguity, coherence, verifiability, and non-goals).

## Tracer-Bullet Vertical Slicing

Decompose the approved spec into end-to-end demonstrable vertical slices:
1. **Prefactoring First**: Isolate prefactoring into `<slug>#01` ("Make the change easy, then make the easy change").
   Slice 01 has no implementation blockers. Subsequent slices depend on Slice 01 (`Blocked by: <slug>#01`).
2. **Vertical Slices**: Every slice cuts across all necessary layers (CLI/API, domain logic, tests) rather than
   horizontal layers (no "database-only" or "frontend-only" issues).
3. **Issue Metadata**: Maintain standard Gantry issue headers:
   - `Type: issue`
   - `Status: draft`
   - `Slice: <slug>#NN`
   - `Spec: .scratch/<slug>/spec.md`
   - `### Files to read`
   - `## Acceptance criteria` (with `- [ ]` checkboxes)
   - `## Blocked by`
4. **Context Budget Audit**: Verify each issue fits within model token windows via `budget.py`.
5. **Plan Critic**: Verify that:
   - Blocker graph forms a valid directed acyclic graph (DAG) without cycles.
   - Every issue has observable acceptance criteria.
   - No horizontal slicing smells are present.
6. **Operator Quiz**: Quiz the operator on:
   - Granularity (are slices sized for single-round TDD deliveries?).
   - Dependency sequence (is prefactoring prioritized?).
   - Split / merge preferences.
7. **Persist Issues**: Write issues to `.scratch/<slug>/issues/NN-<slug>.md`.

## Planning Approval Transition

Upon operator approval of the issue breakdown:
1. **Update Issue Status**: Set status of generated issues to `ready-for-agent`:
   ```bash
   python3 <skillDir>/../gantry/scripts/roadmap.py status <ref> ready-for-agent
   ```
2. **Recompute Waves**: Update `ROADMAP.md` wave layout:
   ```bash
   python3 <skillDir>/../gantry/scripts/roadmap.py waves
   ```
3. **Verify Integrity**: Ensure zero drift:
   ```bash
   python3 <skillDir>/../gantry/scripts/roadmap.py check
   ```
4. **Complete Planning Milestone**: Record milestone completion in the Run log:
   - Append `issue.done` for milestone `<slug>#00` with `phase: "Plan"`.
   (Alternatively, use `python3 <skillDir>/../gantry/scripts/plan.py --approve <slug>`).

## Execution Handoff

- **Standalone Invocation (`/gantry-plan`)**:
  Present the computed execution waves and prompt the operator:
  > Planning approved and scheduled into Wave N. Would you like to launch execution now with `/gantry`?
  Wait for explicit confirmation before launching `gantry`.
- **Delegated Invocation (from `/gantry`)**:
  When delegated from `/gantry`, automatically proceed directly into Gantry's TDD
  implementation round loop without additional prompting.
