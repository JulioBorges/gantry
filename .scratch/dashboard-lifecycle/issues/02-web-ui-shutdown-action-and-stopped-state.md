# Add Web UI Shutdown Action and Stopped State

Type: issue
Status: done
Slice: `dashboard-lifecycle#02`
Spec: `.scratch/dashboard-lifecycle/spec.md`
Created: 2026-09-19

## Parent

`dashboard-lifecycle`

## What to build

Provide an in-browser shutdown button in the dashboard rig header:
1. Header shutdown control: Render a styled shutdown button in `index.html` within the rig header controls with clear industrial aesthetics matching Gantry design.
2. Confirmation dialog: Clicking the button triggers an explicit modal/confirmation warning the operator that the server will be terminated.
3. Shutdown dispatch & state transition: On confirmation, `app.js` posts to `/api/shutdown`, immediately cancels active interval timers / polling to `/api/state`, and transitions the UI to a `SERVER STOPPED` banner / overlay indicating that the server is offline.
4. Playwright test suite: Add tests in `site/tests/dashboard.spec.ts` ensuring the button renders, confirmation modal works, and the shutdown transition occurs without client errors.

### Files to read

- `.agents/skills/gantry/dashboard/static/index.html`
- `.agents/skills/gantry/dashboard/static/app.js`
- `.agents/skills/gantry/dashboard/static/style.css`
- `site/tests/dashboard.spec.ts`

## Acceptance criteria

- [x] The dashboard rig header displays a prominent shutdown button.
- [x] Clicking the shutdown button presents an explicit confirmation dialog.
- [x] Confirming shutdown sends a `POST` request to `/api/shutdown`.
- [x] Upon shutdown confirmation, frontend polling of `/api/state` stops immediately.
- [x] An overlay or status banner displays "SERVER STOPPED" and indicates disconnected state.
- [x] Playwright E2E tests in `site/tests/dashboard.spec.ts` validate button display, confirmation, and state transition.

## Blocked by

- dashboard-lifecycle#01
