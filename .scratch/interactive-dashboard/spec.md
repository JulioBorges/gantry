# Spec: Interactive ASDLC Observability Dashboard and Human Gates

Type: spec
Status: ready-for-agent
Map: `ROADMAP.md` (spec 14)
Source: `/grill-me` session; PRD.md §3; ADR-0001, ADR-0003, ADR-0004
Created: 2026-09-18

## Blueprint

### Context

When operating agentic software development lifecycles across multiple projects and execution units, the existing dashboard provides only high-level card placement without actionable observability. The operator cannot observe live agent execution—such as active tool calls, model reasoning (thinking), or code alterations and diffs—directly from the board.

Furthermore, human checkpoints during delivery lack interactive integration: when a critical quality gate such as Critic verification finishes, the workflow either proceeds autonomously or halts in the terminal without a clear visual cue or actionable approval button in the dashboard. When tickets reach the Done column, their elapsed timers continue to count indefinitely instead of recording total cycle duration. Finally, tickets are fragmented across redundant per-directory swimlanes rather than aggregated into a cohesive, filterable kanban view where all active tickets can be monitored from a single pane of glass.

### Architecture

Transform the Gantry dashboard into an interactive, zero-dependency ASDLC observability board:
1. **Unified Kanban & Project Filtering:** A top project selector featuring a default "ALL" view that presents every ticket across all execution units in a single 8-column board with project badges, with the ability to filter down to any specific project.
2. **Live Agent Activity & Transcript Streaming:** Cards display real-time activity badges (`Thinking...`, `Tool: edit`, `Awaiting Operator`), and clicking a card opens an active modal displaying live tool calls, collapsible thinking blocks, and syntax-highlighted code diffs streamed from the harness transcript.
3. **Interactive Human Gates (Critic ➔ Integrate):** A mandatory human gate halts the ticket after Critic acceptance. The operator can approve the gate directly via a one-click dashboard action button or via the terminal harness conversation, coordinated through a local approval state marker and wait script.
4. **Structured Gate Verdicts & Detailed History:** The ticket detail modal provides dedicated tabs for reviewing the structured verdicts of each lifecycle gate (Plan, Implement, Critic, Integrate) as well as a full chronological execution history with a dedicated action to pop out into a separate browser window.
5. **Cycle Time Measurement & Delivery Completion:** Upon merge confirmation (following the repository's configured PR or branch merge delivery strategy), the ticket transitions to Done, freezing the elapsed timer and presenting a breakdown of time spent in each phase.

### Constraints

- Dependency-free implementation: server runs on Python 3.10+ standard library (`http.server.ThreadingHTTPServer`) and client uses vanilla HTML5/CSS3/ES6+ without npm or build steps.
- Strict loopback binding: server binds to `127.0.0.1` only and refuses all other hosts.
- Non-destructive execution: dashboard cannot mutate git repositories directly; approvals are signaled via local state markers in `~/.gantry/state/`.
- Playwright-tested frontend: all UI additions and interactions must be validated with automated browser tests.

## User Stories

1. As an operator, I want to see a project selector at the top of the dashboard with an "ALL" option selected by default, so that I can see all tickets from all active projects in a single view.
2. As an operator, I want the project selector dropdown to list all active repository execution units, so that I can switch the board focus to an individual project whenever I need.
3. As an operator, I want the "ALL" view to display a single unified 8-column Kanban board rather than duplicating separate boards per directory, so that screen space is maximized and cross-project status is obvious at a glance.
4. As an operator, I want each card on the unified board to display a project/repository badge, so that I immediately know which codebase the ticket belongs to.
5. As an operator, I want to see an active execution badge on the ticket card (such as `Thinking...`, `Tool: run_command`, or `Awaiting Operator`), so that I know what the agent is currently doing without opening logs.
6. As an operator, I want to click any ticket card to open a detail modal, so that I can inspect the execution in depth.
7. As an operator, I want the detail modal to display the agent's current step in real time, so that I can monitor progress as it happens.
8. As an operator, I want the agent's reasoning (thinking blocks) to be displayed in collapsible panels within the modal, so that I can understand its decision-making process without being overwhelmed by text.
9. As an operator, I want tool calls and their inputs/outputs to be clearly formatted and inspectable in the modal, so that I can verify which commands or edits were executed.
10. As an operator, I want file alterations and patches to be rendered with syntax highlighting in the modal, so that I can review code changes cleanly before integration.
11. As an operator, I want the ticket to automatically pause after the Critic successfully accepts a delivery, so that human verification is guaranteed before any code is integrated or PRs are merged.
12. As an operator, I want the dashboard to visually alert me when a ticket is awaiting operator approval, so that I can quickly take action.
13. As an operator, I want an interactive "Aprovar Gate" button on the card and inside the modal, so that I can approve the transition from Critic to Integrate with a single click in the browser.
14. As an operator, I want to be able to approve the gate directly in the terminal harness conversation as an alternative to the web UI, so that my existing terminal workflow remains fully functional.
15. As an operator, I want the harness process to unblock immediately upon approval in the dashboard, so that delivery proceeds without manual polling or terminal restarts.
16. As an operator, I want to view the structured verdict of the Plan gate inside the modal, so that I can inspect the requirements review, criteria coverage, and planned scope.
17. As an operator, I want to view the structured verdict of the Implement gate inside the modal, so that I can verify test suite outcomes, TDD red-green proofs, and modified files.
18. As an operator, I want to view the structured verdict of the Critic gate inside the modal, so that I can see the checklist of acceptance criteria, verification evidence, and quality gate results.
19. As an operator, I want to view the structured verdict of the Integrate gate inside the modal, so that I can inspect the integration branch, pull request details, and post-merge gate checks.
20. As an operator, I want a "Histórico Completo" tab inside the modal, so that I can review the entire chronological timeline of agent prompts, thoughts, and tool actions from start to finish.
21. As an operator, I want a button to open the full execution history in a dedicated browser tab or window, so that I can inspect large logs alongside the main Kanban board.
22. As an operator, I want the Integrate phase to follow the repository's configured delivery strategy (GitHub PR or direct branch merge), so that team-specific conventions are honored.
23. As an operator, I want Gantry setup to prompt for the repository delivery strategy if it has not been defined, so that the integration phase always has clear instructions.
24. As an operator, I want the ticket to move to the Done column only after the merge is verified, so that incomplete or failed integrations never show as completed.
25. As an operator, I want the elapsed timer badge to stop counting immediately when the ticket enters Done, so that the recorded time reflects actual delivery duration rather than continuing indefinitely.
26. As an operator, I want the Done card badge to display the total frozen cycle time formatted in human-readable units (e.g., `Total: 14m 20s`), so that I can evaluate throughput at a glance.
27. As an operator, I want the ticket modal to show a detailed duration breakdown of time spent in each phase (Plan, Implement, Review, Critic, Integrate), so that bottlenecks in the SDLC can be diagnosed.
28. As an operator, I want all dashboard capabilities to function locally without external npm or database dependencies, so that starting the dashboard remains lightweight and instant.

## Contract

### Definition of Done

- [ ] Top bar displays project dropdown selector defaulting to `ALL` with options for each execution unit.
- [ ] In `ALL` mode, cards from all projects render in a single unified 8-column board with project identifier badges.
- [ ] Selecting an individual project filters the 8-column board to show only cards from that project.
- [ ] Ticket cards display active execution badges (`Thinking...`, `Tool: <name>`, `Awaiting Operator`).
- [ ] Clicking a card opens a modal streaming live agent activity from the harness transcript (thoughts, tools, diffs).
- [ ] Critic-accepted tickets halt before Integrate with an `Awaiting Operator` gate state.
- [ ] Dashboard provides an interactive "Aprovar Gate" button on cards and modals via `POST /api/runs/<unit>/<run>/issues/<issue>/approve`.
- [ ] A `wait-gate` mechanism coordinates unblocking whether the approval is made in the dashboard or in the terminal harness conversation.
- [ ] Modal tabs display structured verdicts for Plan, Implement, Critic, and Integrate gates.
- [ ] Modal includes a "Histórico Completo" tab and an action button to open the execution timeline in a dedicated browser window.
- [ ] Tickets entering Done freeze their timer, displaying formatted total cycle time on the card and per-phase breakdowns in the modal.
- [ ] Integration phase honors the configured repository delivery strategy (PR or direct merge).
- [ ] Python unit tests in `tests/test_dashboard.py` and Playwright tests in `site/tests/dashboard.spec.ts` pass cleanly.

### Regression Guardrails

- Existing read-only routes (`GET /api/state`) remain backwards-compatible.
- Refusal to bind on any host other than `127.0.0.1` remains strictly enforced.
- Run log events and format remain intact without introducing unvalidated payloads.
- No Node/npm dependencies are introduced into the Python dashboard server.

### Scenarios

```gherkin
Scenario: Unified Kanban with Project Selector
  Given multiple execution units exist under ~/.gantry/state
  When the dashboard loads
  Then the project selector defaults to "ALL"
  And all tickets across all execution units appear in a single unified 8-column board
  And each card displays its originating project badge

Scenario: Filter by Specific Project
  Given the dashboard is displaying all projects
  When the operator selects a specific project from the dropdown
  Then only cards belonging to that project remain visible on the board

Scenario: Live Activity and Transcript Streaming
  Given an agent is actively executing a round for an issue
  When the operator clicks the issue card
  Then the detail modal opens showing current activity
  And model thinking and tool calls stream in real time from the harness transcript

Scenario: Mandatory Human Gate and Approval via Dashboard
  Given an issue passes Critic verification and enters Awaiting Operator
  When the operator clicks "Aprovar Gate" in the dashboard
  Then the dashboard records the state approval marker
  And the waiting harness unblocks and begins the Integrate phase

Scenario: Cycle Time Frozen on Done
  Given an issue completes the Integrate phase and merges
  When the issue transitions to Done
  Then the elapsed timer stops running
  And the card displays the frozen total cycle time
  And the modal displays the duration breakdown across Plan, Implement, Review, Critic, and Integrate
```

## Implementation Decisions

- **Unified Kanban Board & Project Selector:** The dashboard server aggregates runs and issues across all execution units under the state root. The client interface maintains an active project filter state (`ALL` by default). In `ALL` mode, cards from all active projects are placed into a single shared set of 8 columns with project identifier badges. Selecting an individual project filters cards to only those belonging to that project.
- **Loopback-Only Interactive Endpoints & State File Markers:** The HTTP server introduces controlled action endpoints (`POST /api/runs/<unit_id>/<run_id>/issues/<issue_ref>/approve`) bound strictly to `127.0.0.1`. Calling this endpoint writes an approval marker to `~/.gantry/state/<unit_id>/approvals/<issue_ref>.json` and records an approval event.
- **Harness Transcript Streaming & Adapter:** The server discovers and exposes the active harness transcript path associated with each run or worktree. An endpoint (`GET /api/runs/<unit_id>/<run_id>/issues/<issue_ref>/transcript`) streams incremental transcript steps (system thoughts, tool calls, results, diffs) to the frontend via polling or Server-Sent Events.
- **Mandatory Human Gate Coordination (`wait-gate`):** A gate waiting mechanism is introduced between the Critic and Integrate phases. The harness runner executes a gate wait check that suspends until either an approval marker is written by the dashboard or an explicit approval response is received in the harness conversation.
- **Structured Gate Verdict Persistence & Retrieval:** Each lifecycle phase (Plan, Implement, Critic, Integrate) records its structured outcome contract into the run log or dedicated issue artifact storage under `~/.gantry/state/<unit_id>/artifacts/<run>/<issue>/gate-<phase>.json`. The dashboard retrieves these artifacts on demand via `GET /api/runs/<unit_id>/<run_id>/issues/<issue_ref>/gates`.
- **Phase Duration & Total Time Calculation:** When issues transition between phases, phase start and end timestamps are recorded. When an issue enters `Done` (or `Blocked`), the final completion timestamp is fixed. The dashboard computes and renders both total duration and per-phase duration breakdowns.
- **Configurable Delivery Strategy Resolution:** The Integrate phase queries `.gantry/config.json` for repository delivery preferences (`delivery.strategy`: `pull-request` with `gh` CLI or `branch-merge`). When missing, repository setup or preflight prompts the operator to configure the default.
- **Zero-Dependency Vanilla Modern Architecture:** The server continues using Python standard library `ThreadingHTTPServer` without third-party packages. The frontend retains pure vanilla HTML5, modern CSS Grid/Flexbox, and ES6+ JavaScript, requiring no node modules or build steps to serve.

## Testing Decisions

A good test exercises external behavior through stable public seams—HTTP routes, JSON payloads, file state markers, and browser DOM interactions—without coupling to internal helper implementations.

- **HTTP API & State Management Seam (`tests/test_dashboard.py`):**
  - Verify loopback host enforcement (`127.0.0.1` only).
  - Verify `GET /api/state` returns aggregated runs, project metadata, and issue status across multiple execution units.
  - Verify `POST /api/runs/.../approve` writes the expected approval marker, returns 200, and rejects invalid run/issue identifiers.
  - Verify `GET /api/runs/.../gates` and `GET /api/runs/.../transcript` return accurate structured payloads and stream updates.
  - Verify timer freezing logic when an issue event stream contains `issue.done`.
  - Prior art: Existing test suite in `tests/test_dashboard.py`.

- **End-to-End User Experience & Browser Seam (`site/tests/dashboard.spec.ts`):**
  - Validate project selector dropdown switching between `ALL` and individual projects with corresponding card filtering.
  - Validate unified 8-column Kanban layout and project badges on cards.
  - Validate ticket card click opening the detail modal.
  - Validate live activity indicators, collapsible thinking blocks, and tool call rendering.
  - Validate structured gate verdict tab displays (Plan, Implement, Critic, Integrate).
  - Validate "Histórico Completo" tab and external window popout button.
  - Validate the "Aprovar Gate" interactive button action and visual transition to Integrate.
  - Validate frozen timer badge on Done cards and duration breakdown in modal.
  - Prior art: Existing Playwright tests in `site/tests/dashboard.spec.ts`.

## Out of Scope

- Exposing the dashboard server over non-loopback network interfaces or public hostnames.
- Introduction of external database systems (e.g., PostgreSQL, SQLite, Redis) or heavy ORMs.
- Direct automated push/merge to remote protected branches without operator or CI authorization.
- Replacing the lightweight Python standard library HTTP server with heavyweight web frameworks or requiring Node/npm build steps for dashboard execution.

## Changelog

- 2026-09-18 — Initial spec drafted from `/grill-me` alignment.

## Further Notes

This specification honors ADR-0001 (harness-first control boundary), ADR-0003 (deterministic scripts decide; guard hooks record), and ADR-0004 (Gantry as a lightweight, harness-neutral skill pack). The interactive approval capability provides a bridge between the browser UI and the harness without compromising harness autonomy or introducing unnecessary external dependencies.
