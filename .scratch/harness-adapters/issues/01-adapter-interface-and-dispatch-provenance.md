# Adapter interface, driver resolution, and dispatch provenance

Type: issue
Status: ready-for-agent
Slice: harness-adapters#01
Spec: [`../spec.md`](../spec.md) (spec 10, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/harness-adapters/spec.md`](../spec.md)

## What to build

Define the single `HarnessAdapter` interface that every implementation satisfies — `dispatch`, `observe`, `requestStop`, `reconcile` — together with its variant-bearing types. Those variant sets are the contract, not an implementation detail, because spec 11's entire control flow is shaped around which variants a caller must handle: `StopOutcome` is exactly `stopped` | `requested_cooperatively` | `unsupported`; `AgentObservation.liveness` is exactly `running` | `exited` | `unknown`; `ReconciliationResult` carries that same liveness set plus `result` as `present_valid` | `present_invalid` | `absent` and `worktreeActivity` as `quiescent` | `active` | `unknown`; and `DispatchIo` carries the result path, the working directory and the diagnostic sink. The absent-capability variants exist so that a caller cannot write logic assuming a stop succeeded, which is ADR-0001 expressed as a type.

Wire the interface into the shared operation core as an injected port, so that `pbi.dispatch` resolves a driver from the Execution Rule Snapshot, invokes the adapter, and records the resolved driver, command, model and processing destination on the dispatch record. Ship one scripted in-process adapter that satisfies the real interface and can be instructed to return every variant, so later slices and other specs test against variants rather than against success.

Ship the adapter-independent worktree activity observer that `reconcile` reports: a Git index hash plus a `git status --porcelain` fingerprint of the working directory, compared across observations. This observer must be injectable. The variant set stays in this interface permanently, but `pbi-execution-loop#01` supersedes the observer itself with a lease-aware marker, and it must be able to do so by substituting the injected observer rather than by reopening this interface. Finally, expose a CLI preview that prints the resolved invocation for a role without running anything.

## Acceptance criteria

- [ ] `core.invoke` on `pbi.dispatch` routes through the injected adapter port; an accepted dispatch record carries resolved driver, command, model and destination, queryable through `state.project`.
- [ ] The scripted adapter can return each `StopOutcome` and each liveness variant, and a test asserts a caller cannot treat `requested_cooperatively` or `unsupported` as a stop.
- [ ] Reconciliation reports `worktreeActivity` as `quiescent`, `active` or `unknown` from observed Git state, and takeover is refused while it is `active` or `unknown`.
- [ ] The worktree activity observer is injected rather than called directly by `reconcile`, and a test substitutes an alternative observer that changes the reported `worktreeActivity` without any change to the `HarnessAdapter` or `ReconciliationResult` types.
- [ ] The CLI preview for a configured role prints the invocation and exits without dispatching; a role with no resolvable driver fails the preview with a named rejection code.
- [ ] One CLI parity test proves the preview delegates to the operation core.

## Blocked by

- `execution-core#01` — the operation catalog, the `invoke` surface and the rejection code vocabulary this slice registers its port and preview against.
- `execution-core#03` — the `pbi.dispatch` operation and PBI Execution Ownership that the adapter port is invoked from.
- `gtp-protocol#01` — envelope boundary validation and the Protocol Failure classes a missing or invalid result maps to.
- `gtp-protocol#02` — the task and result envelope contract that `dispatch` carries and `reconcile` validates.
- `gtp-protocol#04` — the `ContextUsage` variants carried on `AgentObservation`.
- `config-and-snapshot#04` — the Execution Rule Snapshot the driver is resolved from.
- `config-and-snapshot#07` — role routing resolution, which determines which driver a role resolves to and when none does.
- `data-handling#01` — the redaction sink enforcement interface backing `DispatchIo.diagnosticSink`; build against the declared interface and integrate when it lands.
