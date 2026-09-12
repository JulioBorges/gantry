# Loopback transport shell and read-only monitor

Type: issue
Status: ready-for-agent
Slice: dashboard#01
Spec: [`../spec.md`](../spec.md) (spec 17, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/dashboard/spec.md`](../spec.md)

## What to build

Stand up the dashboard server at `http://127.0.0.1:4200` with a binding that no configuration value can widen, plus the browser application shell it serves. One read path works end to end: the browser requests current state, the server calls the core's `state.project` read operation for a Repository Execution Unit, and the shell renders an identified repository and execution with a placeholder swimlane list. A request guard rejects any request whose `Host` header is not a loopback literal, before anything else is examined — a non-loopback `Host` is a DNS-rebinding attempt and never reaches a handler. The remaining three origin axes (`Origin`, `Sec-Fetch-Site`, the required custom header) arrive with the mutation boundary in `dashboard#02`; this slice owns only the `Host` axis, because it is the one a read path needs too.

The interface carries the standing statement that this is a loopback boundary rather than authentication. This wording is load-bearing, not decoration: any process on the machine that reaches loopback and obtains a token acts as the operator, and a browser extension with access to the page can read the token out of memory. That residual risk is acknowledged as irreducible at v4 scope, so the interface's job is to state the boundary rather than to overclaim it — nothing rendered may describe the session as logged in or authenticated.

**This slice makes and records the frontend framework and build-tool decision**, as an explicit written decision in the delivered work rather than a silent choice, because `machine-setup#03` installs the built assets and `release-engineering#02` packages them. The choice is constrained rather than free, and the constraints must be named alongside it: the capability token lives in a plain JavaScript variable, so no framework whose session model assumes a cookie or a server-side session is usable; the assets must build into a bundle another spec installs and a third packages, so the output layout is a published contract; and SSE plus an in-memory-only credential argue for a thin client over a full application framework. Record the built-asset layout and the build output location as part of the decision.

Test seam: dashboard-owned. Loopback binding, the `Host` guard, and asset serving are this spec's own behavior and get real tests. The single read path gets one delegation assertion, not a behavior test of projection contents.

## Acceptance criteria

- [ ] The server listens only on a loopback address; a test asserts no bind to a non-loopback interface and that no configuration key exists that changes the bind address.
- [ ] A request with a non-loopback-literal `Host` is rejected without the request reaching any handler.
- [ ] A read request with no token returns projection data; the read path invokes `state.project` exactly once per request.
- [ ] The shell renders repository and execution identity sourced from the projection, not from the URL or a client-side guess.
- [ ] The rendered interface contains the loopback-boundary statement and contains no text describing the session as authenticated or logged in.
- [ ] A build command produces the servable asset bundle at a documented location.

## Blocked by

- `execution-core#01` — the operation core `invoke` entry point, the `state.project` read operation and `StateProjection` shape, and Repository Execution Unit identity and registration.
- `data-handling#01` — the redaction sink enforcement interface that server logging must traverse.
