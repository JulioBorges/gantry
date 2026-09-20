# Spec: Dashboard Lifecycle Controls and ASDLC Round Automation

Type: spec
Status: ready-for-agent
Map: `ROADMAP.md` (spec 15)
Source: `/grill-me` session; PRD.md §3; ADR-0004
Created: 2026-09-19

## Blueprint

### Context

Currently, the Gantry dashboard server must be manually started and terminated by the operator in a terminal via `dashboard.py serve`. When an agent or operator starts an ASDLC execution round using the `gantry` skill, the dashboard is not automatically offered, leading to lack of visual telemetry unless the operator remembers to run the dashboard command in a separate terminal. Furthermore, at the end of the round (after the integration step), there is no prompt or mechanism to terminate the dashboard. Lastly, the dashboard web UI itself lacks an interactive shutdown control, forcing the operator to switch back to terminal sessions and hunt for background process IDs or send SIGINT signals.

### Architecture

Integrate full daemonized lifecycle control and round hooks into Gantry:
1. **Daemon & Process Lifecycle CLI:** Extend `dashboard.py` with `status`, `start --daemon`, and `stop` subcommands. `status` checks if the dashboard is running (querying loopback `/api/state` and checking PID/port metadata in `~/.gantry/state/dashboard.json`). `start --daemon` launches the server in a detached background process on port 4600 (or configured port), verifies readiness, and writes metadata. `stop` sends a graceful shutdown command to the active server and cleans up metadata.
2. **Graceful Shutdown HTTP Endpoint:** Expose `POST /api/shutdown` restricted strictly to loopback (`127.0.0.1`). When invoked, the server responds with `200 {"status": "shutting_down"}` and asynchronously initiates `server.shutdown()` on a background thread to close the socket and terminate cleanly.
3. **Web UI Shutdown Control:** In `index.html` and `app.js`, add an industrial-styled "SHUTDOWN" button in the rig header. Clicking the button opens an explicit confirmation dialog. Upon confirmation, the UI sends `POST /api/shutdown`, stops state polling, and renders a clear visual overlay: `SERVER STOPPED`.
4. **Round Workflow Integration Hooks:** In `SKILL.md` and `reference/round-workflow.md`:
   - At the beginning of each round (prior to `Implement`): the workflow checks `dashboard.py status`. If not running, it asks the operator whether to launch the dashboard. If approved, it runs `dashboard.py start --daemon` and outputs the URL. If already active, it logs the active URL without prompting.
   - At the end of each round (immediately after `Integrate`): the workflow checks `dashboard.py status`. If active, it asks the operator whether to shut down the dashboard. If approved, it calls `dashboard.py stop`.

### Constraints

- Dependency-free implementation: `dashboard.py` server and CLI commands must only use Python 3.10+ standard library (`argparse`, `http.server`, `json`, `pathlib`, `subprocess`, `sys`, `threading`, `time`, `urllib`).
- Strict loopback binding: server binds to `127.0.0.1` only; `POST /api/shutdown` rejects non-loopback requests with 403.
- Playwright-tested frontend: all web UI changes (shutdown button, confirmation modal, stopped state transition) must be covered with Playwright automated tests.
- Non-destructive execution: stopping the dashboard does not alter Git repository state, Run logs, or issue statuses.

## User Stories

1. As an operator running an ASDLC round, I want the Gantry skill to check if the dashboard is already running before implementation begins, so that I don't have to check manually.
2. As an operator, I want to be prompted at the start of a round if the dashboard is inactive, so that I can choose whether to open it for live visual telemetry.
3. As an operator, I want the dashboard to start in background daemon mode automatically upon my approval, so that my terminal conversation is not blocked by a foreground server.
4. As an operator, I want Gantry to display the dashboard URL when started or detected, so that I can click and view it in my browser immediately.
5. As an operator, I want Gantry to skip asking to start the dashboard if it is already running, so that I am not asked redundant questions.
6. As an operator, I want to query `python3 <skillDir>/scripts/dashboard.py status --json`, so that scripts and tools can deterministically check whether the dashboard is active.
7. As an operator, I want to start the daemonized dashboard with `python3 <skillDir>/scripts/dashboard.py start --daemon`, so that I have a reliable CLI command to launch it.
8. As an operator, I want `start --daemon` to reuse an already running Gantry dashboard instance without crashing, so that duplicate startup requests are idempotent.
9. As an operator, I want `start --daemon` to fail with a clear error message if port 4600 is occupied by a non-Gantry process, so that I can resolve the port collision.
10. As an operator, I want to terminate the running dashboard using `python3 <skillDir>/scripts/dashboard.py stop`, so that I can stop it cleanly from the command line.
11. As an operator, I want an interactive "SHUTDOWN" button in the dashboard web UI header, so that I can stop the server without switching to a terminal.
12. As an operator, I want a confirmation dialog before the dashboard shuts down, so that accidental clicks do not interrupt my monitoring session.
13. As an operator, I want the web UI to stop polling `/api/state` immediately after shutdown is triggered, so that the browser does not flood the console with network failure errors.
14. As an operator, I want the web UI to display a prominent "SERVER STOPPED" indicator after shutdown, so that I know the server has terminated.
15. As an operator completing an ASDLC round, I want Gantry to ask whether I want to close the dashboard after integration completes, so that background processes are not left running unnecessarily.
16. As an operator, I want Gantry to cleanly stop the dashboard if I confirm closure at the end of the round, so that system resources and port 4600 are released.
17. As an operator, I want Gantry to leave the dashboard running if I decline closure at the end of the round, so that I can continue reviewing completed issues and execution history.

## Contract

### Definition of Done

- [ ] `dashboard.py status [--json]` accurately reports running status, PID, port, and URL.
- [ ] `dashboard.py start --daemon` spawns a background server, writes state metadata, and waits until responsive.
- [ ] `dashboard.py stop` issues a graceful shutdown request, waits for process exit, and clears state metadata.
- [ ] `POST /api/shutdown` endpoint terminates the server asynchronously and frees TCP port 4600.
- [ ] Web UI displays a shutdown button, prompts for confirmation, triggers shutdown, and presents "SERVER STOPPED".
- [ ] Gantry round workflow prompts for dashboard start before `Implement` if inactive, and prompts for shutdown after `Integrate` if active.
- [ ] All Python unit tests pass in `tests/test_dashboard.py` and Playwright tests pass in `site/tests/dashboard.spec.ts`.

### Regression Guardrails

- Existing foreground `dashboard.py serve` continues to function unchanged.
- All dashboard endpoints remain strictly loopback-only (`127.0.0.1`).
- The dashboard never mutates Git repositories, Run logs, or issue statuses during lifecycle transitions.

### Scenarios

```gherkin
Scenario: Query dashboard status when inactive
  Given no dashboard server is running on port 4600
  When the operator executes dashboard.py status --json
  Then the command exits with code 0
  And the output contains running false

Scenario: Launch dashboard daemon
  Given no dashboard server is running on port 4600
  When the operator executes dashboard.py start --daemon
  Then the command exits with code 0
  And the server is listening on port 4600
  And dashboard.py status reports running true

Scenario: Terminate dashboard via CLI
  Given a dashboard daemon is running on port 4600
  When the operator executes dashboard.py stop
  Then the command exits with code 0
  And port 4600 is released
  And dashboard.py status reports running false

Scenario: Terminate dashboard via Web UI
  Given the operator opens the dashboard in a browser
  When the operator clicks the shutdown button and confirms
  Then a POST request is sent to /api/shutdown
  And the browser displays SERVER STOPPED
  And state polling is stopped
```

## Implementation Decisions

- **Daemon Metadata Storage:** Store daemon metadata in `~/.gantry/state/dashboard.json` containing `{ "pid": <int>, "port": <int>, "host": "127.0.0.1", "stateRoot": <str>, "startedAt": <iso_ts> }`.
- **Graceful Shutdown Endpoint:** Implement `POST /api/shutdown` in `DashboardRequestHandler`. It validates loopback origin, writes response `{"status": "shutting_down"}`, and schedules `server.shutdown()` on a new thread with a small delay (50ms) to ensure HTTP response transmission completes.
- **CLI Commands:**
  - `serve`: remains standard foreground server.
  - `start --daemon`: uses `subprocess.Popen` with detached process flags (`start_new_session=True` on POSIX), checks socket availability within 5 seconds, writes `dashboard.json`.
  - `status`: checks if process is alive and `/api/state` responds; if stale PID exists, cleans up `dashboard.json`.
  - `stop`: sends `POST /api/shutdown` with fallback to `SIGTERM` if unresponsive after 3 seconds, cleans `dashboard.json`.
- **UI Shutdown Button:** Positioned in `index.html` `.rig-header .header-status` or `.header-controls`. Styled with accent alert border. Opens a modal or confirm dialog before dispatching `POST /api/shutdown`.
- **Skill Round Workflow Integration:**
  - `SKILL.md` documents pre-implement check (`dashboard.py status`) and post-integrate shutdown prompt.
  - `reference/round-workflow.md` specifies lifecycle hooks around round implementation and round finalization.

## Testing Decisions

- **Test Seams:**
  1. CLI Seam (`dashboard.py` subprocess execution: `status`, `start --daemon`, `stop`).
  2. HTTP Seam (`urllib.request` against `/api/shutdown`).
  3. Browser Seam (Playwright automated test in `site/tests/dashboard.spec.ts`).
- **Standard Library Only:** Backend tests use Python's built-in `unittest` without external test dependencies.
- **Prior Art:** Matches patterns in `tests/test_dashboard.py` and `site/tests/dashboard.spec.ts`.

## Out of Scope

- Remote or multi-tenant dashboard hosting (must remain loopback only).
- Automatic browser window opening via `webbrowser.open` (URLs are printed for operator click).
- Killing arbitrary third-party processes occupying port 4600.

## Changelog

- 2026-09-19 — Initial spec draft created from `/grill-me` session.

## Further Notes

- The Gantry pack philosophy mandates zero-telemetry leaks and deterministic operator control. Adding daemon lifecycle and web shutdown respects the operator's control over background execution.
