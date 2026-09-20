# Spec: Gantry Plan Socratic Gating and Vertical Slicing

Type: spec
Status: ready-for-agent
Map: `ROADMAP.md` (spec 16)
Source: `/grill-me` session; PRD.md §2; ADR-0001, ADR-0004
Created: 2026-09-19

## Blueprint

### Context

When working in an agentic SDLC with Gantry, users often start with either an unrefined free-text goal or an existing spec that has not yet been decomposed into actionable tasks. Currently, Gantry's default planning reference workflow drafts issues in one pass without conversational probing or interactive design tree exploration. When a user provides a free-text goal, the agent creates a draft spec and issues without testing assumptions, challenging scope boundaries, or resolving architectural ambiguities with the operator.

Furthermore, when breaking specs down into implementation issues, agents often produce horizontal layers (e.g. database first, then backend API, then UI) rather than end-to-end verifiable tracer bullets with prefactoring identified upfront. Finally, during the planning phase, the Gantry Kanban dashboard lacks live visibility into the planning lifecycle: there is no clear card representation in the `Plan` column showing when the agent is interviewing the operator or awaiting approval on draft slices.

### Architecture

Introduce `gantry-plan` as a dedicated, first-class skill in `.agents/skills/gantry-plan/SKILL.md` (and integrated into the main `gantry` workflow) that unifies Socratic interviewing and tracer-bullet vertical slicing:

1. **Dual Entry Modes:**
   - **Free-Text Goal:** When invoked with a free-text prompt or goal, `gantry-plan` initiates a Socratic Gate interview (modeled after Matt Pocock's `grilling` and `grill-me`). It explores the codebase, glossary (`CONTEXT.md`), and ADRs in the background, maps the design tree of decisions, and interviews the operator across structured phases (Problem & Context, Architecture & Seams, Scope & Non-Goals, Verifiable Criteria & Scenarios) to synthesize a comprehensive `.scratch/<slug>/spec.md`.
   - **Spec-Provided:** When invoked with an existing spec (path or inline), it validates the spec structurally (`spec.py --check`) and qualitatively (`Requirement Critic`), skipping the initial interview and proceeding directly to tracer-bullet slicing.

2. **Tracer-Bullet Vertical Slicing (`to-issues` pattern):**
   - Decomposes the approved spec into thin, end-to-end vertical slices that cut across all layers (schema, business logic, CLI/API, UI, and automated tests) rather than horizontal slices.
   - Identifies and schedules prefactoring slices first ("Make the change easy, then make the easy change").
   - Preserves Gantry issue headers (`Type: issue`, `Status: draft`, `Slice`, `Spec`, `### Files to read`) with executable, verifiable checkbox acceptance criteria.
   - Runs automated validation via `budget.py` (context window checks) and `Plan Critic` (adversarial refutation of granularity, contract ownership, and DAG acyclicity).
   - Quizzes the operator on granularity, dependencies, and split/merge preferences before persisting issues to `.scratch/<slug>/issues/NN-<slug>.md`.

3. **Kanban & Telemetry Integration (`Plan` column):**
   - Emits Run log lifecycle events using a spec milestone identifier (`<slug>#00`) to represent the planning phase in `runlog.py`.
   - Emits `phase.started` with `phase: "Plan"` and `data.operatorWaiting: true` whenever the interview or approval is awaiting user input, rendering an *"Awaiting Operator"* badge in the dashboard's `Plan` column.
   - Records `operator.approved` when the operator responds or approves the plan, and transitions `<slug>#00` to `issue.done` upon plan finalization.

4. **Workflow Transition & Execution Handoff:**
   - Upon operator approval of the issue breakdown, marks issues `ready-for-agent` via `roadmap.py status`, recomputes waves via `roadmap.py waves`, and verifies integrity via `roadmap.py check`.
   - If invoked directly as `gantry-plan`, presents the wave breakdown and prompts the user whether to start execution via `gantry` immediately.
   - If delegated from `gantry`, automatically proceeds into Gantry's TDD implementation loop for the ready frontier issues.

### Constraints

- Zero external dependencies: All scripts and workflows execute using Python standard library and standard markdown files.
- Spec and Issue conformance: All generated specs must pass `spec.py --check` and all issues must conform to `frontier.py` DAG constraints and `budget.py` context limits.
- Harness neutrality: The skill must operate cleanly in conversational CLI harnesses (Antigravity `agy`, Claude Code, OpenCode, Codex).
- Telemetry safety: Run log events must strictly conform to `runlog.py` envelope schemas and reject prohibited tokens (`command`, `output`, `diff`).

## User Stories

1. As an operator, I want to invoke `gantry-plan` with a free-text goal (e.g. `/gantry-plan "add export to CSV"`), so that I can explore and define a new feature interactively without manually drafting a spec first.
2. As an operator, I want `gantry-plan` to explore the codebase, `CONTEXT.md`, and ADRs in the background, so that its questions are grounded in real project context rather than generic templates.
3. As an operator, I want to be interviewed in structured Socratic phases (Problem, Architecture, Scope, Scenarios), so that ambiguity is eliminated before any code is written.
4. As an operator, I want the agent to provide recommended answers for each question during the interview, so that I can validate or steer decisions quickly.
5. As an operator, I want the Socratic interview to synthesize a valid `.scratch/<slug>/spec.md` conforming to Gantry's spec template, so that the requirements are formally recorded.
6. As an operator, I want to invoke `gantry-plan` with an existing spec file (e.g. `/gantry-plan .scratch/auth/spec.md`), so that I can slice a pre-written spec into issues.
7. As an operator, I want the spec to be validated by `spec.py --check` and the Requirement Critic before slicing, so that flawed specs are caught early.
8. As an operator, I want the feature to be sliced into tracer-bullet vertical slices cutting across all layers, so that each issue delivers a demoable, independently verifiable outcome.
9. As an operator, I want prefactoring work to be isolated into the earliest slices, so that subsequent feature implementation is clean and low-risk.
10. As an operator, I want generated issues to preserve Gantry metadata headers (`Type: issue`, `Status: draft`, `Slice`, `Spec`, `### Files to read`), so that all downstream Gantry tooling functions seamlessly.
11. As an operator, I want context window usage of each issue to be evaluated by `budget.py`, so that issues do not exceed token thresholds.
12. As an operator, I want the Plan Critic to refute non-vertical slices, unobservable criteria, and cyclic dependencies, so that issue quality is rigorously audited.
13. As an operator, I want to be quizzed on the proposed issue breakdown (granularity, dependencies, splits/merges), so that I retain full control over the execution plan.
14. As an operator, I want a card representing the spec (`<slug>#00`) to appear in the `Plan` column of the Gantry Kanban dashboard during planning, so that team members can see planning in progress.
15. As an operator, I want the dashboard card to display an "Awaiting Operator" badge during interview questions and plan approval, so that it is visually obvious when the agent is waiting on human input.
16. As an operator, I want `operator.approved` events to be recorded in the Run log when I answer questions or approve the plan, so that the audit trail is complete.
17. As an operator, I want approved issues to be transitioned to `ready-for-agent` and scheduled into waves via `roadmap.py`, so that the roadmap is immediately updated.
18. As an operator, I want `gantry-plan` to ask if I wish to proceed immediately to implementation after approval, so that I can seamlessly transition to coding.
19. As an operator, I want invoking `gantry` with a free-text goal or unplanned spec to automatically delegate to `gantry-plan`, so that I have a unified entry point for both planning and implementation.
20. As an operator, I want all generated artifacts (specs, issues, commit messages, and reports) to be in English, ensuring repository consistency.

## Contract

### Definition of Done

- [ ] `.agents/skills/gantry-plan/SKILL.md` is created with full instructions for both free-text Socratic Gate planning and spec-to-issues vertical slicing.
- [ ] `.agents/skills/gantry/SKILL.md` delegates free-text goals and unplanned specs to `gantry-plan`.
- [ ] Socratic Gate engine interviews the operator across Problem, Architecture, Scope, and Criteria phases and writes `.scratch/<slug>/spec.md`.
- [ ] Spec synthesis conforms to Gantry's spec template and passes `spec.py --check`.
- [ ] Vertical slicing generates tracer-bullet issues adhering to `to-issues` rules with Gantry headers and `### Files to read`.
- [ ] Slicing pipeline runs `spec.py --check`, Requirement Critic, `budget.py`, and Plan Critic before operator quiz.
- [ ] Run log events using milestone identifier `<slug>#00` track planning in the `Plan` column with `data.operatorWaiting: true` during user gates.
- [ ] Approval transition runs `roadmap.py status ready-for-agent`, `roadmap.py waves`, and `roadmap.py check`.
- [ ] Unit and workflow tests validate `gantry-plan` invocation, telemetry recording, spec validation, and issue breakdown.

### Regression Guardrails

- Existing `gantry` implementation and round workflows (`reference/round-workflow.md`) remain untouched and backward-compatible.
- `spec.py --check` validation rules and required headings remain strictly enforced.
- `frontier.py` DAG validation and cycle detection remain invariant.
- `runlog.py` event validation rules and prohibited token restrictions remain inviolate.
- Direct commits to `main` remain prohibited.

### Scenarios

```gherkin
Scenario: Socratic Gate Planning from Free-Text Goal
  Given the operator invokes gantry-plan with a free-text goal "add webhook support"
  When the agent explores the codebase and begins the Socratic Gate interview
  Then a Run log event records phase.started for "webhook#00" in phase "Plan" with operatorWaiting true
  And the agent interviews the operator through Problem, Architecture, Scope, and Criteria phases
  And upon completion synthesizes .scratch/webhook/spec.md
  And spec.py --check validates the synthesized spec as valid

Scenario: Tracer-Bullet Slicing from Existing Spec
  Given a valid spec exists at .scratch/webhook/spec.md
  When gantry-plan slices the spec into issues
  Then each generated issue in .scratch/webhook/issues/ is a vertical slice covering end-to-end behavior
  And prefactoring requirements are placed in the earliest issue
  And each issue includes the Gantry header, Files to read, observable criteria, and Blocked by
  And Plan Critic and budget.py validate the draft issues

Scenario: Operator Approval and Roadmap Update
  Given draft issues have been validated and quizzed with the operator
  When the operator approves the breakdown
  Then gantry-plan records operator.approved and completes the "webhook#00" milestone
  And roadmap.py updates the issues to ready-for-agent and recomputes waves
  And roadmap.py check passes with zero drift
```

## Implementation Decisions

1. **Skill Packaging:** Implement `gantry-plan` as a distinct skill folder in `.agents/skills/gantry-plan/` with `SKILL.md` declaring argument hints for free-text goals, spec paths, and issue paths.
2. **Telemetry Milestone Key:** Use `<slug>#00` as the authoritative Issue reference for planning telemetry. This satisfies `runlog.ISSUE_RE` (`^[a-z0-9][a-z0-9-]*#\d{2,}$`) while cleanly identifying the overarching spec milestone on the Kanban board.
3. **Socratic Gate Phasing:** Structure the interview into four discrete gates: (1) Problem Statement & Context, (2) Architectural Boundaries & Seams, (3) Scope Limitations & Non-Goals, and (4) Observable Criteria & Gherkin Scenarios. Each gate asks targeted questions with recommended answers and explores codebase seams in the background.
4. **Tracer-Bullet Breakdown Protocol:** Enforce tracer-bullet slicing: each issue must slice through API/CLI, business logic, persistence/state, and tests. Horizontal slicing (e.g. "Create database tables" or "Add frontend styles only") is actively rejected by the Plan Critic prompt. Prefactoring is isolated into an explicit prerequisite issue.
5. **Issue Metadata Preservation:** Retain `Type: issue`, `Status: draft`, `Slice: <slug>#NN`, `Spec: <spec-path>`, `## Parent`, `## What to build`, `### Files to read`, `## Acceptance criteria`, and `## Blocked by` to ensure 100% interoperability with `budget.py`, `frontier.py`, `acceptance.py`, and `roadmap.py`.
6. **Roadmap Integration:** On approval, execute `roadmap.py status <ref> ready-for-agent` for every generated issue, followed by `roadmap.py waves` to calculate execution waves and `roadmap.py check` to verify consistency.

## Testing Decisions

- **Seams Tested:**
  1. CLI/Module seam: Python tests verifying `spec.py --check` on synthesized specs and `runlog.py` telemetry handling `<slug>#00` milestone events.
  2. Roadmap seam: Integration tests verifying that `roadmap.py` correctly calculates waves and updates progress when `<slug>` issues are approved.
  3. Workflow execution: Unit tests in `tests/test_gantry_plan.py` simulating free-text and spec-provided planning workflows, validating generated artifact schemas.

## Out of Scope

- Automated direct execution of implementation rounds within `gantry-plan` (implementation remains the responsibility of `gantry`).
- Custom web UI editors for specs in the dashboard (editing remains in standard Markdown files).
- Modifying the underlying git commit signing or branch creation rules.

## Changelog

- 2026-09-19 — Initial draft synthesized from `/grill-me` session and `/to-spec` invocation.
