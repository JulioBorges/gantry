# Dashboard Capability Token and the mutation boundary

Type: issue
Status: ready-for-agent
Slice: dashboard#02
Spec: [`../spec.md`](../spec.md) (spec 17, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/dashboard/spec.md`](../spec.md)

## What to build

The full Dashboard Capability Token flow plus the first mutating endpoint, so the boundary is proven by a real operation rather than a stub. The CLI generates the token in memory, opens the browser at a single-use bootstrap path carrying a nonce — not the token — the bootstrap request consumes the nonce and returns the token in the response body, and the page holds it in a JavaScript variable. Putting the nonce in the URL and the token in the body is what keeps the token out of history, referrers, and shell logs while the flow stays a single click.

Mutating requests carry the token in a header — never a cookie, never a URL — so the browser never attaches it automatically and there is no cross-site request forgery surface to defend. The server enforces the remaining three origin axes before evaluating scope: `Origin` must match the dashboard's own origin, `Sec-Fetch-Site` must be `same-origin`, and a required custom header must be present, which a simple cross-origin request cannot set and which therefore forces a preflight the server refuses. The `Host` loopback-literal axis already guards every request from `dashboard#01`.

Scope is two-dimensional and enforced in both directions: `unit` names the Repository Execution Unit whose executions may be mutated, and its absence means no execution mutations at all; `globalSettings` is a separate boolean governing machine-wide configuration writes. One mutating endpoint — `execution.cancel` — is wired through to the core with `channel: "dashboard"`, `actor.kind: "operator"`, and provenance carrying the session identity and a token reference, never the token value.

**Parity-test granularity, stated so the divergence is visible.** The project handoff says the dashboard gets *one* parity test proving delegation; this spec says one parity test per mutating endpoint. This issue and the rest of the spec follow the spec's stricter reading, and that reading is approved: a single parity test spread across roughly a dozen mutating endpoints proves delegation for one endpoint and nothing about the others. The handoff's wording was about not writing behavior tests for delegated semantics, not about the count.

Test seam: dashboard-owned for everything except the one `execution.cancel` parity test, which proves delegation only. Token generation, nonce consumption, scope enforcement, and all four origin axes are this spec's own behavior and get real tests.

## Acceptance criteria

- [ ] A mutating request without a token is rejected; the same request with a valid in-scope token produces exactly one core invocation with `channel: "dashboard"`.
- [ ] The bootstrap nonce succeeds once and a replay is rejected; the token appears in no URL on any path.
- [ ] A mutating request with a cross-origin `Origin`, an absent `Origin`, a `Sec-Fetch-Site` other than `same-origin`, or a missing custom header is rejected even when the token is valid; the preflight for the custom header is refused.
- [ ] A token whose scope names unit A cannot mutate unit B; a token with `globalSettings: false` cannot write global configuration; a token with no `unit` cannot advance an execution.
- [ ] No endpoint reads a token from a cookie, asserted by a test that sends the token only as a cookie and observes rejection.
- [ ] The recorded provenance for the cancel operation contains the session identity and a token reference and does not contain the token value.

## Blocked by

- `dashboard#01` — the loopback server, the `Host` guard every request passes through first, and the application shell that holds the token.
- `execution-core#02` — the dashboard operator-channel rule that lets a token-bearing request assert `actor.kind: "operator"`, and the `ActorProvenance` shape recorded with it.
- `execution-core#08` — the `execution.cancel` operation this slice delegates to.
