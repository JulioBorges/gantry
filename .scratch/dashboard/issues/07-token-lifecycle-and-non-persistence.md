# Token lifecycle, non-persistence proof, and manual entry fallback

Type: issue
Status: ready-for-agent
Slice: dashboard#07
Spec: [`../spec.md`](../spec.md) (spec 17, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/dashboard/spec.md`](../spec.md)

## What to build

Close the capability token's life cycle and prove the non-persistence claim rather than asserting it. The token expires on a short interval measured in minutes; an active page renews before expiry and an idle one does not, which is what keeps an abandoned tab from remaining an open capability without making renewal an annoyance. The token is revoked when the session ends and when the dashboard process exits. Its value is registered with the redaction pipeline as a secret, so an accidental log line is redacted.

A manual entry fallback lets the operator paste a token the CLI printed, for when the browser launch fails — a failed launch must not lock the operator out of their own machine.

The proof is a sweep, and it has to be real: after a full session exercising every endpoint, every persistence sink is scanned for the token value — URLs, log lines, configuration files, database rows, envelopes, and artifacts — which means the session runs against a temporary database and a temporary Git repository so there are actual sinks to scan. Browser storage is asserted separately against real storage state.

Test seam: dashboard-owned, except the redaction behavior itself, which belongs to `data-handling`. This slice proves the registration and the sink wiring, not the detector — the redaction criterion is therefore exercised through a sink rather than by calling the pipeline directly.

## Acceptance criteria

- [ ] A token is rejected after session end, after process exit, and after expiry; a test with an active page observes renewal before expiry and a test with an idle page observes none.
- [ ] After a full session, a scan of every URL, log line, configuration file, database row, envelope, and artifact finds no occurrence of the token value.
- [ ] A log line deliberately containing the token value is redacted by the pipeline, proven through a sink rather than by calling the pipeline directly.
- [ ] The token is absent from `localStorage`, `sessionStorage`, and cookies after a full session, asserted against browser storage state.
- [ ] The manual entry path yields a working session when the browser launch is simulated as failing.

## Blocked by

- `dashboard#02` — token issuance, the bootstrap nonce flow, and scope enforcement, whose life cycle this slice closes.
- `data-handling#01` — the redaction sink enforcement interface that every output traverses and that the sweep scans behind.
- `data-handling#02` — the detector source registration that makes the token value a recognized secret.
