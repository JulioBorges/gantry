## Spec 17 — dashboard

This spec owns a loopback HTTP/SSE transport over the shared operation core: a Monitor that renders state projections, a Settings screen that writes through `ConfigStore`, and the Dashboard Capability Token that lets a browser request assert `actor.kind: "operator"`. It adds no behavior — every mutation is a core operation with `channel: "dashboard"` — but it owns three things nobody else does, and that is where the risk sits. First, the token: issuance, the single-use bootstrap nonce, two-dimensional scope (`unit` vs `globalSettings`), short expiry with renewal, revocation, and the four-axis origin enforcement (`Origin`, `Sec-Fetch-Site`, required custom header, loopback-literal `Host`) that closes the DNS-rebinding path a token alone leaves open. Second, the projection shape, which is deliberately built so a dishonest rendering has no data to draw from — three independent stage labels instead of one "done", two readiness booleans instead of one, an `observed` context union with an `unknown` variant carrying no number, and a watermark indicator derived from declared monitoring granularity rather than from a threshold. Third, the structural guarantee that no timer, connection, or SSE subscription can reach a mutation. The residual risk is local and acknowledged as irreducible at v4 scope: any process that reaches loopback and obtains a token acts as the operator — so the interface must never describe itself as authenticated.

### Slices

---

**01 — Loopback transport shell and read-only monitor**

- **What to build**: Stand up the dashboard server bound to `127.0.0.1:4200` with a binding that no configuration value can widen, plus the browser application shell that it serves. One read path works end to end: the browser requests current state, the server calls the core's `state.project` read operation for a Repository Execution Unit, and the shell renders an identified repository and execution with a placeholder swimlane list. A request guard rejects any request whose `Host` header is not a loopback literal, before anything else is examined. The interface carries the standing statement that this is a loopback boundary rather than authentication. This slice also makes and records the frontend framework and build-tool decision, and the built-asset layout that `machine-setup` will install and `release-engineering` will package.
- **Acceptance criteria**:
  - The server listens only on a loopback address; a test asserts no bind to a non-loopback interface and that no configuration key exists that changes the bind address.
  - A request with a non-loopback-literal `Host` is rejected without the request reaching any handler.
  - A read request with no token returns projection data; the read path invokes `state.project` exactly once per request.
  - The shell renders repository and execution identity sourced from the projection, not from the URL or a client-side guess.
  - The rendered interface contains the loopback-boundary statement and contains no text describing the session as authenticated or logged in.
  - A build command produces the servable asset bundle at a documented location.
- **Blocked by**: needs the operation core `invoke` entry point and the `state.project` read operation plus `StateProjection` from `execution-core`; needs Repository Execution Unit identity from `execution-core`.
- **Parallelizable with**: nothing intra-spec — this is the bootstrap slice.
- **Test seam**: dashboard-owned. Loopback binding, the `Host` guard, and asset serving are this spec's behavior. The single read path gets one delegation assertion, not a behavior test of projection contents.

---

**02 — Dashboard Capability Token and the mutation boundary**

- **What to build**: The full token flow plus the first mutating endpoint, so the boundary is proven by a real operation rather than a stub. The CLI generates a token in memory, opens the browser at a single-use bootstrap path carrying a nonce, the bootstrap request consumes the nonce and returns the token in the response body, and the page holds it in a JavaScript variable. Mutating requests carry the token in a header — never a cookie, never a URL — and the server enforces the remaining three axes (`Origin` matches own origin, `Sec-Fetch-Site` is `same-origin`, the required custom header is present, with the corresponding preflight refused) before evaluating scope. Scope is two-dimensional and enforced both ways.

  ```ts
  scope: {
    unit?: RepositoryExecutionUnitId;   // absent means no execution mutations
    globalSettings: boolean;            // machine-wide configuration writes
  }
  ```

  One mutating endpoint — `execution.cancel` — is wired through to the core with `channel: "dashboard"`, `actor.kind: "operator"`, and provenance carrying the session identity and a token reference, never the token value.
- **Acceptance criteria**:
  - A mutating request without a token is rejected; the same request with a valid in-scope token produces exactly one core invocation with `channel: "dashboard"`.
  - The bootstrap nonce succeeds once and a replay is rejected; the token appears in no URL on any path.
  - A mutating request with a cross-origin `Origin`, an absent `Origin`, a `Sec-Fetch-Site` other than `same-origin`, or a missing custom header is rejected even when the token is valid; the preflight for the custom header is refused.
  - A token whose scope names unit A cannot mutate unit B; a token with `globalSettings: false` cannot write global configuration; a token with no `unit` cannot advance an execution.
  - No endpoint reads a token from a cookie, asserted by a test that sends the token only as a cookie and observes rejection.
  - The recorded provenance for the cancel operation contains the session identity and a token reference and does not contain the token value.
- **Blocked by**: 01. Cross-spec: needs the dashboard operator-channel rule and `ActorProvenance` shape from `execution-core`; needs the `execution.cancel` operation from `execution-core`.
- **Parallelizable with**: 03 (03 touches only read paths).
- **Test seam**: dashboard-owned for everything except the one `execution.cancel` parity test, which proves delegation only. Token generation, nonce consumption, scope enforcement, and all four origin axes are this spec's own behavior and get real tests.

---

**03 — Honest PBI projection and Monitor swimlanes**

- **What to build**: The projection builder and the Monitor screen that renders it, one swimlane per pipeline. This is the slice that makes misrepresentation require effort. `stageLabels` carries three independent fields so there is no single value to render as "done"; `readiness` carries two booleans so technical readiness cannot be displayed as operator approval; `context` carries `estimated` and `observed` separately with `observed` as the union including `unknown`; `budgets` carries correction and infrastructure counts separately; waiting, blocked, and failed project as distinct states with their reasons; local and provider evidence project as separate lists. The watermark indicator variant is derived from `monitoring`, not from a threshold value: a threshold marker for `per_tool_call`, a between-turns marker with explicit granularity for `between_turns`, a clearly-labeled self-reported marker for `self_reported`, and no indicator at all for `none`. The projection also carries `mode`, and a `demo` unit renders the persistent simulated-evidence indicator on every record while it is on screen.
- **Acceptance criteria**:
  - A PBI at implementation completion projects `implementation: "complete"` with `integration: "not_authorized"`; no code path produces a single aggregate status value for a PBI.
  - A technically ready spec with no operator approval projects `technical: true, operatorApproved: false` as two fields.
  - An `unknown` observed usage projects with no numeric value reachable by the bar renderer, asserted structurally rather than by inspecting rendered output.
  - Each of the four `monitoring` values produces its designated indicator variant, and no value produces an enforced-ceiling variant.
  - Waiting, blocked, and failed project as distinct states each carrying its reason; correction and infrastructure retry counts project as separate fields; local and provider evidence project as separate lists including when one is empty.
  - A demo unit projects `mode: "demo"` on every record and the Monitor shows the simulated-evidence indicator persistently, verified on a screenshot-equivalent render of a scrolled view.
- **Blocked by**: 01. Cross-spec: needs the `ContextUsage` union including its `unknown` variant from `gtp-protocol`; needs the `contextMonitoring` granularity value from the Integration Capability declaration in `harness-adapters`; needs `WaitingReason`/`BlockedReason` and the correction and infrastructure budget counters from `execution-core`; needs the demo mode marker on the unit from `demo-mode`; needs the local and provider evidence reference shapes from `verification-adapters` and `git-integration`.
- **Parallelizable with**: 02, 06, 07.
- **Test seam**: dashboard-owned. The projection shape and its honesty constraints are this spec's behavior, tested as type-level and unit-level assertions on the builder. No rendering tests beyond the demo-marker persistence check, because a rendering test proves a rendering while the requirement is that a dishonest rendering has no data.

---

**04 — Live transition feed over SSE**

- **What to build**: Publish transitions the core has already recorded over SSE, carrying projections rather than commands. Subscribing causes no work and there is no code path from a timer or a connection to a mutation — this is the structural form of the rule against becoming a background orchestrator. A disconnected client reconnects and re-reads the projection rather than replaying a queue, so the feed is never a source of truth. Latency from transition to client receipt is measured on demo traffic and reported as a demo measurement, not asserted as a product guarantee.
- **Acceptance criteria**:
  - A transition recorded by the core reaches a subscribed client as a projection payload; the payload contains no command or action field.
  - An instrumented core observes zero mutating invocations over a session with an open subscription, an elapsed timer interval, and no operator action.
  - A client disconnected mid-session reconnects and receives a fresh full projection; no queued events are replayed.
  - Latency is measured on demo traffic against the under-one-hundred-millisecond target and the result is reported with an explicit demo-measurement label.
  - The feed endpoint is a read path and is served without a token.
- **Blocked by**: 01, 03 (needs the projection payload type). Cross-spec: needs the transition record stream from `execution-core`; needs the demo pipeline from `demo-mode` for the latency measurement.
- **Parallelizable with**: 05, 06, 07.
- **Test seam**: dashboard-owned. Publication, reconnection semantics, and the no-mutation-from-subscription invariant are this spec's behavior. The instrumented-core assertion is the load-bearing test here.

---

**05 — Operator decision surface**

- **What to build**: The screen where the operator acts, with every action a core operation carried by an in-scope token. A pending decision displays the exact proposal identity and version so the operator approves what they actually read. Plan approval, local merge confirmation with the target, candidate, and snapshot named on the confirmation itself, and execution resume and cancel all become mutating endpoints. The one-click demo pipeline re-run control lives here as well, since it is an operator mutation like the others. Each endpoint constructs an `OperationRequest` with a stable `requestId` and delegates; the server caches no approval and holds no decision state.
- **Acceptance criteria**:
  - Each mutating endpoint produces exactly one core invocation with `channel: "dashboard"` and `actor.kind: "operator"`, proven by one parity test per endpoint.
  - A pending decision renders the proposal identity and version taken from the projection; approving a proposal whose content changed since it was rendered surfaces the core's `approval_version_mismatch` rejection rather than succeeding.
  - The local merge confirmation displays the target revision, the merge candidate, and the governing rule snapshot before the confirming control is enabled.
  - The same requests without a valid in-scope token are rejected and produce no core invocation.
  - The demo re-run control is offered only on a unit projecting `mode: "demo"`.
  - Core rejection codes are surfaced to the operator by code, not translated into a generic failure message.
- **Blocked by**: 02, 03. Cross-spec: needs the plan version hash and proposal identity from `slicing-and-approval`; needs the merge candidate and target revision identity for `merge.confirmLocal` from `git-integration`; needs `execution.resume` and `execution.cancel` from `execution-core`; needs the demo run operation from `demo-mode`.
- **Parallelizable with**: 04, 06, 07.
- **Test seam**: almost entirely the delegated side. One parity test per mutating endpoint and nothing more; the semantics of approval, merge confirmation, and resumption belong to their owning specs and are tested at the core. The dashboard-owned part is narrow: that the proposal identity and version reach the screen, and that the token check gates each endpoint.

---

**06 — Settings screen**

- **What to build**: Both configuration layers editable from forms, written through the same `ConfigStore` and whole-document validation every other interface uses. The screen displays which layer supplies each effective value, previews each role's resolved command live, and badges roles that are never invoked as dead configuration — all read from the store rather than recomputed here. No field accepts a secret value; credential fields accept environment variable names so the screen is safe to screen-share. Sections follow the specified set: harness and host, roles, gates, Git workflow, context limits, execution capacity, repository readiness, and data handling. A global-layer write requires a token with `globalSettings: true`.
- **Acceptance criteria**:
  - A write with any invalid field is rejected as a whole and no file is written; a valid write produces a `.bak` sibling of the target layer's previous file.
  - A repository-layer write attempting to raise a global limit is rejected with the store's rejection code, surfaced by code.
  - Field provenance, resolved role commands, and dead-configuration badges all appear in the Settings projection and are sourced from the store.
  - No form field accepts a secret-shaped value; credential inputs are validated as environment variable names and never as values.
  - A repository-scoped token cannot write the global layer; a `globalSettings` token cannot advance an execution.
  - Each write endpoint produces exactly one core invocation, proven by one parity test.
- **Blocked by**: 02. Cross-spec: needs the `ConfigStore` layering, whole-document validation, per-layer write authorization, `.bak` on save, field provenance, resolved command, and dead-configuration computation from `config-and-snapshot`; needs `config.read` and `config.write` from `execution-core`'s catalog.
- **Parallelizable with**: 03, 04, 05, 07.
- **Test seam**: validation, layering, backup, secret rejection, and dead-configuration computation are `config-and-snapshot`'s behavior and are tested there — this slice gets one parity test per write endpoint. Dashboard-owned: scope enforcement on the global layer, and that the form cannot construct a request carrying a secret value.

---

**07 — Token lifecycle, non-persistence proof, and manual entry fallback**

- **What to build**: Close the token's life cycle and prove the non-persistence claim rather than asserting it. The token expires on a short interval measured in minutes; an active page renews before expiry and an idle one does not. The token is revoked when the session ends and when the dashboard process exits. Its value is registered with the redaction pipeline as a secret, so an accidental log line is redacted. A manual entry fallback lets the operator paste a token the CLI printed, for when the browser launch fails. The proof is a sweep: after a full session exercising every endpoint, every persistence sink is scanned for the token value.
- **Acceptance criteria**:
  - A token is rejected after session end, after process exit, and after expiry; a test with an active page observes renewal before expiry and a test with an idle page observes none.
  - After a full session, a scan of every URL, log line, configuration file, database row, envelope, and artifact finds no occurrence of the token value.
  - A log line deliberately containing the token value is redacted by the pipeline, proven through a sink rather than by calling the pipeline directly.
  - The token is absent from `localStorage`, `sessionStorage`, and cookies after a full session, asserted against browser storage state.
  - The manual entry path yields a working session when the browser launch is simulated as failing.
- **Blocked by**: 02. Cross-spec: needs the redaction sink enforcement interface and secret registration from `data-handling`.
- **Parallelizable with**: 03, 04, 05, 06.
- **Test seam**: dashboard-owned, except the redaction behavior itself, which is `data-handling`'s — this slice proves the registration and the sink wiring, not the detector. The sweep test is the one that has to be real: it needs a session against a temporary SQLite database and a temporary Git repository so there are actual sinks to scan.

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Operation core `invoke`, `OperationRequest`/`OperationOutcome`, `Rejection` codes | `execution-core` | 01, 02, 05, 06 |
| `state.project` read operation and `StateProjection` | `execution-core` | 01, 03, 04 |
| Dashboard operator-channel rule (token permits `actor.kind: "operator"`) and `ActorProvenance` | `execution-core` | 02, 05 |
| Repository Execution Unit identity | `execution-core` | 01, 02 |
| Transition record stream (what SSE publishes) | `execution-core` | 04 |
| `WaitingReason` / `BlockedReason`, correction and infrastructure budget counters | `execution-core` | 03 |
| `execution.cancel`, `execution.resume` operations | `execution-core` | 02, 05 |
| `config.read` / `config.write` operations | `execution-core` | 06 |
| ConfigStore layering, whole-document validation, per-layer write authorization, `.bak` on save, field provenance, resolved role command, dead-configuration computation | `config-and-snapshot` | 06 |
| `ContextUsage` union including the `unknown` variant | `gtp-protocol` | 03 |
| Redaction sink enforcement interface and secret registration | `data-handling` | 07, and 01 for server logging |
| Demo mode marker on the unit and its propagation to projections; demo run operation | `demo-mode` | 03, 05 |
| Demo pipeline as the latency measurement subject | `demo-mode` | 04 |
| `contextMonitoring` granularity from the Integration Capability declaration | `harness-adapters` | 03 |
| Local evidence reference shape | `verification-adapters` | 03 |
| Provider evidence reference shape; merge candidate and target revision identity for `merge.confirmLocal` | `git-integration` | 05, 03 |
| Plan version hash and proposal identity | `slicing-and-approval` | 05 |
| Dashboard asset installation location | `machine-setup` | 01 |
| Asset packaging in the published artifact | `release-engineering` | 01 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| Dashboard asset layout and build output location | 01 | `machine-setup` (installation), `release-engineering` (packaging) |
| `CapabilityToken` shape, two-dimensional scope, and bootstrap nonce flow | 02 | `execution-core` (the token reference stored in provenance), `machine-setup` (the CLI command that generates, opens, and prints it) |
| Dashboard request guard (`Host` loopback literal, `Origin`, `Sec-Fetch-Site`, required custom header) | 01 for `Host`, 02 for the rest | none blocking; `release-engineering` documents it |
| `PbiProjection` with `stageLabels`, `readiness`, `context`, `budgets`, `evidence`, `mode` | 03 | `demo-mode` (mode marker rendering); every spec whose states must be nameable reads it as the honesty contract |
| Watermark indicator derivation from `monitoring` | 03 | `harness-adapters` (the granularity value has a rendering consequence) |
| SSE transition feed contract and reconnection semantics | 04 | `demo-mode` (latency measured on demo traffic) |
| Token value registered as a secret with the redaction pipeline | 07 | `data-handling` (a named detector source) |
| Settings projection (provenance, resolved commands, dead-configuration badges) | 06 | `config-and-snapshot` (confirms the store exposes what the form needs) |

### Risks / judgement calls

**The frontend stack needs a decision before slice 01 can start, and slice 01 is where it should be made.** The repo has no `package.json`, so this is a greenfield call, and it is constrained rather than free: the token must live in a plain JavaScript variable, which disqualifies any framework whose session model assumes a cookie or server-side session; the assets must build into a bundle that `machine-setup` installs and `release-engineering` packages; and SSE plus an in-memory-only credential argue for a thin client over a full application framework. I treated this as slice 01's responsibility rather than a blocking prerequisite, because the constraints above narrow it enough that an agent can decide it inside the slice. If the operator wants the choice made centrally — it affects `machine-setup` and `release-engineering` too — it should be settled before 01 is picked up.

**Parity-test granularity contradicts the handoff, and I followed the spec.** The standing decision says the dashboard gets *one* parity test proving delegation. This spec says "one parity test per mutating endpoint, matching spec 16's pattern." I wrote the slices to the spec's reading, because a single parity test across roughly a dozen mutating endpoints proves delegation for one of them and nothing about the rest. This is the stricter reading, so it should not surprise anyone, but it is a divergence from the handoff's literal wording and the operator should confirm it.

**I distributed the demo-mode surface instead of giving it a slice.** The mode marker landed in 03, the re-run control in 05, and the latency measurement in 04. A standalone demo slice would have been blocked by 02, 03, *and* 04 — the worst blocking profile in the set — for work that is three small additions to slices that already own the relevant layer. The cost is that no single issue owns "the demo looks right end to end," so if the operator wants that guarantee as one demoable thing, it should be added back as slice 08 with those three blockers accepted.

**Slice 02 is the biggest and I was tempted to split it.** Issuance plus nonce plus scope plus four origin axes plus one live mutation is a lot for one PBI. I kept it whole because splitting it produces a slice that can issue a token nobody checks, or a slice that checks a token nobody issues — neither is independently demoable, and the boundary is exactly the thing this spec exists to get right. If it proves too large in practice, the clean cut is origin enforcement as its own slice, since the four axes are independent of the token's life cycle.

**The chain 01 → 03 → 04 is the only depth-three path** and I am moderately confident in it. Slice 04 could start alongside 03 if the `PbiProjection` type is frozen first — which is cheap, and the spec's own sequencing note argues for building the projection first regardless. If the operator wants maximum parallelism, extracting "freeze the projection type" out of 03 into slice 01 would flatten this, at the cost of making slice 01 a partly-horizontal type-definition slice, which is the thing these rules are trying to avoid.

**One thing I could not resolve from the spec:** whether the SSE feed endpoint should be readable without a token. I specified it as a read path served without one, consistent with the spec's rule that reads are served to unauthenticated requests and that read operations are separated precisely so a transport can expose them token-free. But an unauthenticated live feed of every transition is a broader read surface than a single projection fetch, and given the acknowledged local threat model it is worth the operator confirming that reads really are meant to be free at that granularity.
