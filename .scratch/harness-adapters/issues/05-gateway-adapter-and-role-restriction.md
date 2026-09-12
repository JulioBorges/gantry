# Gateway adapter and the file-mutating role restriction

Type: issue
Status: ready-for-agent
Slice: harness-adapters#05
Spec: [`../spec.md`](../spec.md) (spec 10, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/harness-adapters/spec.md`](../spec.md)

## What to build

Implement the single-shot OpenAI-compatible HTTP adapter for router and proxy setups: no working directory, no file mutation, no process lifecycle. Its capability declaration is honest about that shape — `agentInterruption: "none"`, because a single-shot request can be abandoned but not interrupted, so `requestStop` returns the `unsupported` variant, and `contextMonitoring` takes whatever the response reports, typically `self_reported`. Reported usage renders as `self_reported` and never as `measured`.

Enforce that a file-mutating role cannot route to a gateway, twice: once at configuration validation, and again independently at dispatch, so that a configuration written before the rule existed does not slip through. Each rejection carries its own named rejection code.

Classify every gateway dispatch's processing destination as `remote`, and have it evaluated against the egress allowance matrix before any payload is assembled, so that a disallowed destination stops the dispatch rather than being recorded after content has already been built.

## Acceptance criteria

- [ ] A gateway dispatch for a non-mutating role completes and its result is read from the response through the same envelope validation as the other adapters.
- [ ] `requestStop` returns `unsupported`; no caller path treats an abandoned request as a stop.
- [ ] A file-mutating role configured to a gateway is rejected at configuration validation and independently rejected at dispatch, each with a named rejection code.
- [ ] Every gateway dispatch records `destination: "remote"` and is evaluated against the egress allowance matrix before payload assembly.
- [ ] Usage reported by the response renders as `self_reported` and never as `measured`.

## Blocked by

- `harness-adapters#01` — the `HarnessAdapter` interface, the `StopOutcome` variant set, and the dispatch provenance record that carries the processing destination.
- `data-handling#06` — the egress allowance matrix resolution and destination classification evaluated at dispatch.
- `config-and-snapshot#02` — whole-document configuration validation, where the file-mutating-role rejection is raised.
- `config-and-snapshot#07` — role routing resolution, which determines that a role resolves to a gateway driver.
- `gtp-protocol#01` — envelope boundary validation applied to the response-carried result.
