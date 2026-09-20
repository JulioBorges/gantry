# Implement CLI Lifecycle Commands and Shutdown HTTP Endpoint

Type: issue
Status: done
Slice: `dashboard-lifecycle#01`
Spec: `.scratch/dashboard-lifecycle/spec.md`
Created: 2026-09-19

## Parent

`dashboard-lifecycle`

## What to build

Add daemonized lifecycle management to `dashboard.py` and a graceful shutdown HTTP endpoint:
1. `status` subcommand: checks whether the dashboard is listening on loopback and whether an active process exists, inspecting `~/.gantry/state/dashboard.json`. Supports `--json` to output machine-readable status (`{"running": bool, "host": str, "port": int, "pid": int, "stateRoot": str}`). Cleans up stale PID metadata when inactive.
2. `start --daemon` subcommand: spawns the dashboard server in a detached background subprocess, waits up to 5 seconds to ensure the port responds, writes process metadata to `~/.gantry/state/dashboard.json`, and outputs connection details. Idempotently returns existing instance if already running Gantry dashboard. Exits with descriptive error if port is occupied by an alien process.
3. `stop` subcommand: sends `POST /api/shutdown` to the running dashboard, waits for process termination, cleans up `dashboard.json`, and reports successful shutdown.
4. `POST /api/shutdown` HTTP route: restricts requests to `127.0.0.1`, returns `200 {"status": "shutting_down"}`, and schedules graceful `server.shutdown()` on a separate thread.

### Files to read

- `.agents/skills/gantry/scripts/dashboard.py`
- `tests/test_dashboard.py`

## Acceptance criteria

- [x] `dashboard.py` provides `status`, `start --daemon`, and `stop` subcommands alongside existing `serve`.
- [x] `status` accurately reports running state, PID, port, and URL with `--json` support.
- [x] `start --daemon` spawns background server, verifies loopback readiness, and writes `~/.gantry/state/dashboard.json`.
- [x] `stop` invokes `POST /api/shutdown`, verifies socket closure and process termination, and cleans up metadata.
- [x] `POST /api/shutdown` rejects non-loopback requests with 403 and triggers asynchronous server shutdown.
- [x] Unit tests in `tests/test_dashboard.py` validate daemon start, status reporting, stopping, and port release using standard library only.

## Blocked by

None - can start immediately
