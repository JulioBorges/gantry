# Live transition feed over SSE

Type: issue
Status: ready-for-agent
Slice: dashboard#04
Spec: [`../spec.md`](../spec.md) (spec 17, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/dashboard/spec.md`](../spec.md)

## What to build

Publish transitions the core has already recorded over SSE, carrying projections rather than commands. Subscribing causes no work, and there is no code path from a timer or a connection to a mutation — that structural absence is the form the rule against becoming a background orchestrator takes here, and the instrumented-core assertion is what proves it. A disconnected client reconnects and re-reads the projection rather than replaying a queue, so the feed is never a source of truth.

Latency from transition to client receipt is measured on demo traffic and reported as a demo measurement, never asserted as a product guarantee. This slice provides the measurement surface; `demo-mode#07` populates and labels it from the demo run, so the direction of the dependency between the two is this slice first.

**Open question for the operator, to be confirmed before this slice is implemented rather than decided inside it:** whether the SSE feed endpoint should be readable without a token. It is specified here as token-free, consistent with the spec's rule that reads are served to unauthenticated requests and that read operations are separated precisely so a transport can expose them without a credential. But an unauthenticated live feed of every transition is a materially broader read surface than a single projection fetch, and under the acknowledged local threat model that difference is worth a deliberate decision. The acceptance criterion below states the token-free reading; if the operator decides otherwise, that criterion changes and the token check from `dashboard#02` applies to the feed as well.

Test seam: dashboard-owned. Publication, reconnection semantics, and the no-mutation-from-subscription invariant are this spec's behavior. The instrumented-core assertion is the load-bearing test here.

## Acceptance criteria

- [ ] A transition recorded by the core reaches a subscribed client as a projection payload; the payload contains no command or action field.
- [ ] An instrumented core observes zero mutating invocations over a session with an open subscription, an elapsed timer interval, and no operator action.
- [ ] A client disconnected mid-session reconnects and receives a fresh full projection; no queued events are replayed.
- [ ] Latency is measured on demo traffic against the under-one-hundred-millisecond target and the result is reported with an explicit demo-measurement label.
- [ ] The feed endpoint is a read path and is served without a token.

## Blocked by

- `dashboard#01` — the loopback server and the `Host` guard the subscription request passes through.
- `dashboard#03` — the projection payload type the feed publishes.
- `execution-core#01` — the recorded transition primitive and its audit record, which is the stream this feed republishes.
- `demo-mode#05` — the scripted walkthrough that produces the demo traffic the latency measurement runs against; needed only for the latency criterion.
