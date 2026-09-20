---
name: gantry-dashboard
description: Opens a read-only, loopback-only kanban dashboard that shows every Gantry Run across every execution unit of the current Git clone — one swimlane per Run, Issues placed in Ready, Plan, Implement, Review, Critic, Integrate, Done and Blocked columns. Use for "open the dashboard", "show me the runs", "is anything stuck", "which run is stale".
---

# Gantry Dashboard

A local HTTP server that renders the Run log `runlog.py` already writes. It never decides
anything and never writes anything: every route is a `GET`, and the page polls
`GET /api/state` to redraw itself. No Issue, policy, Run log, branch or worktree can be
changed from the dashboard.

## Open the dashboard

### Foreground server
```
python3 <skillDir>/../gantry/scripts/dashboard.py serve
```

### Background daemon
```
python3 <skillDir>/../gantry/scripts/dashboard.py start --daemon
```

- Binds `127.0.0.1` only; the script refuses any other `--host` value and exits non-zero
  before opening a socket. There is no way to expose the dashboard beyond the local machine.
- Defaults to port `4600`; pass `--port 0` for an OS-assigned ephemeral port (the script
  prints the resolved `host`/`port`/`stateRoot` as one JSON line before it starts serving).
- Reads Run logs from `~/.gantry/state/<unit-id>/runs/*.jsonl` by default (every worktree of
  one clone shares that state root); pass `--state-root` to point at a different one, for
  example when inspecting a fixture.
- Open `http://127.0.0.1:<port>/` in a browser once the server is listening.

## Daemon subcommands and status

- Query status: `python3 <skillDir>/../gantry/scripts/dashboard.py status [--json]`
- Terminate daemon: `python3 <skillDir>/../gantry/scripts/dashboard.py stop`

## Round lifecycle hooks

Gantry's round workflow automates dashboard lifecycle checks:
- **Pre-implementation hook**: Prior to starting the `Implement` phase, the workflow checks `dashboard.py status --json`. If inactive, it asks the operator whether to launch the dashboard with `dashboard.py start --daemon`. If approved, it launches the daemon and displays the URL. If the operator declines, it proceeds without prompting again. If already active, it logs the active URL without prompting.
- **Post-integration hook**: After completing `Integrate`, if `dashboard.py status --json` reports active, it asks the operator whether to terminate the dashboard with `dashboard.py stop`. If approved, it cleanly stops the daemon.

## What you see

- One swimlane per Run (`<repositoryRoot> — <run> [tier: …]`), across every execution unit
  under the state root — a Run started from one clone shows next to a Run from another.
- Each Issue card sits in the column matching its most recent `phase.started` phase, or
  `Done`/`Blocked` once `issue.done`/`issue.blocked` is logged.
- Card badges: branch or worktree, per-role models, correction budget (used/ceiling), elapsed
  time in the current phase, and whether the Run is waiting on the operator.
- A swimlane is marked stale when its last non-`policy.changed` event is older than the
  `staleAfterSeconds` value recorded on that Run's own `run.started` event — the snapshot
  taken when the Run started, never the repository's current policy and never a later
  `policy.changed` event.

## Verify it without a browser

```
python3 -m unittest tests/test_dashboard.py -v
```

The test module and `dashboard.py` both import only the Python standard library (`argparse`,
`datetime`, `http.server`, `json`, `pathlib`, `threading`, `time`, `urllib`, plus the pack's
own `runlog` module) — no third-party dependency is required to run either the server or its
tests.

## Stopping the server

- For the foreground server: `Ctrl-C` in the terminal running `dashboard.py serve`.
- For the daemon: `python3 <skillDir>/../gantry/scripts/dashboard.py stop`.
- From the browser: click the **SHUTDOWN** button in the dashboard rig header and confirm in the dialog.

