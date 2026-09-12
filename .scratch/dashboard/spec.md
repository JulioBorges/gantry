# Dashboard: monitor, settings, and capability token

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 17, wave 5)
Source: `PRD.md` §8.2, §8.3, §2.3
Created: 2026-09-11


## Problem Statement

An operator running an AFK pipeline needs to know what is happening without reading a database. `PRD.md`
specifies a local dashboard for that — swimlanes per pipeline, watermark bars, a live feed under a hundred
milliseconds — plus a Settings screen as "the visual fallback for users who prefer forms over
conversation", since setup complexity is named as the top adoption blocker.

Three problems make this harder than a read-only status page.

The dashboard mutates. Settings writes, approvals, resumptions, and cancellations are real operations, and
the operator is the one making them — which means the browser must be able to act as the operator, and the
browser is the least trustworthy thing in the system. `PRD.md` specifies an ephemeral capability token
issued by the CLI, held only in browser memory, sent on mutating requests, scoped to session and
repository execution unit, revoked when the session ends, and "never persisted in configuration, SQLite,
URLs, browser storage, logs, envelopes, or artifacts". It also states plainly what this is not: "a
lightweight loopback boundary, not strong browser attestation". The PRD review flags the delivery
mechanism as unresolved design work, including how global Settings scope fits.

The dashboard is where a dishonest guarantee would look most convincing. A watermark bar implies
measurement; a green badge implies verification. §8.3 requires that estimated and observed context be
distinguished, that unknown measurements "remain visibly unknown", and that "no badge should imply a
strict context guarantee unsupported by the integration". It also requires implementation completion to be
distinguished from integration, and technical readiness from operator approval — the exact conflations the
PRD review corrected elsewhere.

And a live view that polls could quietly become a second orchestrator. §8.3 forbids it: "polling and SSE
do not become an independent background orchestrator".

## Solution

The dashboard is a transport over the operation core, served on loopback only. Reads render state
projections; every mutation is a core operation with the `dashboard` channel. It holds no state, decides
nothing, and progresses nothing — the feed is a projection of transitions the core made, never a trigger
for one.

Mutating requests carry an ephemeral capability token. The CLI generates it, serves it once through a
single-use bootstrap response rather than in a URL, and the browser keeps it in a JavaScript variable —
not `localStorage`, not a cookie, not the address bar. The token is scoped to the dashboard session, to a
repository execution unit, and separately to whether global settings may be changed. It is revoked when
the session or the dashboard process ends. A request without a valid token is served read-only data or
rejected.

The projection is built to make honest reporting the default rather than a discipline. Estimated and
observed context are separate fields, observed is a union with an explicit unknown variant, and the
watermark indicator renders differently per declared monitoring granularity so it cannot imply enforcement
the integration does not provide. Completion, gate approval, and integration are separate states with
separate labels, as are technical readiness and operator approval.

Settings writes go through the same `ConfigStore` as every other interface, with a backup on save, a live
preview of each role's resolved command, a dead-configuration badge, and no field capable of holding a
secret.

## User Stories

1. As an operator, I want to see all active pipelines at once, so that I understand the factory's state without querying anything.
2. As an operator, I want swimlanes per pipeline, so that parallel work is visually separable.
3. As an operator, I want to see the current PBI and its resolved driver, so that I know which harness is doing what.
4. As an operator, I want the repository and execution identified, so that I do not confuse two clones.
5. As an operator, I want a live feed of transitions, so that I can watch progress rather than refresh.
6. As an operator, I want the feed to be fast, so that it feels live rather than delayed.
7. As an operator, I want estimated and observed context shown as separate values, so that I never read one as the other.
8. As an operator, I want an unmeasurable context usage shown as unknown, so that I am not shown a reassuring zero.
9. As an operator, I want the watermark indicator to reflect my integration's actual monitoring granularity, so that it does not imply enforcement I do not have.
10. As an operator, I want no badge suggesting a strict context ceiling my integration cannot enforce, so that the display matches reality.
11. As an operator, I want implementation completion distinguished from integration, so that finished code is not shown as merged.
12. As an operator, I want gate approval distinguished from both, so that the three stages are legible.
13. As an operator, I want technical readiness distinguished from my approval, so that a lint pass does not look like consent.
14. As an operator, I want waiting, blocked, and failed shown as distinct states with reasons, so that I know whether I am the blocker.
15. As an operator, I want to see why something is waiting, so that I can act on the real cause.
16. As an operator, I want correction and infrastructure retry counts visible, so that I can see how close a slice is to its limit.
17. As an operator, I want local and provider evidence shown side by side, so that I can see which side is missing.
18. As an operator, I want a pending decision to show me the exact proposal and version, so that I approve what I actually read.
19. As an operator, I want to approve a plan from the dashboard, so that the form is a real alternative to the conversation.
20. As an operator, I want to confirm a local merge from the dashboard, with the target, candidate, and snapshot named, so that the confirmation is informed.
21. As an operator, I want to resume and cancel executions from the dashboard, so that lifecycle control is available visually.
22. As an operator, I want mutating actions to require a capability token, so that a random page cannot drive my factory.
23. As an operator, I want the token issued by my CLI, so that possessing it means the CLI gave it to me.
24. As an operator, I want the token never to appear in a URL, so that it does not land in history or a referrer.
25. As an operator, I want the token kept only in memory, so that closing the tab discards it.
26. As an operator, I want the token never written to configuration, the database, logs, envelopes, or artifacts, so that it cannot be recovered later.
27. As an operator, I want the token scoped to one repository execution unit, so that it cannot act on another.
28. As an operator, I want changing global settings to require its own scope, so that a repository-scoped session cannot alter my machine defaults.
29. As an operator, I want the token revoked when the session or dashboard ends, so that it does not outlive its use.
30. As an operator, I want an unauthenticated request served read-only or rejected, so that reading is easy and writing is not.
31. As an operator, I want a manual token entry fallback, so that a browser launch failure does not lock me out.
32. As an operator, I want the dashboard bound to loopback only, so that it is not reachable from my network.
33. As an operator, I want the binding non-configurable, so that it cannot be widened by a setting.
34. As an operator, I want to be told this is a loopback boundary rather than authentication, so that I do not overestimate it.
35. As an operator, I want Settings writes validated exactly like CLI writes, so that the form cannot produce an invalid configuration.
36. As an operator, I want a backup written on every save, so that a mistake is recoverable.
37. As an operator, I want a live preview of each role's resolved command, so that I can see what will run.
38. As an operator, I want roles that are never invoked badged, so that dead configuration is visible.
39. As an operator, I want no secret fields anywhere in Settings, so that I cannot accidentally paste a key into a file.
40. As an operator, I want environment variable names shown instead of values, so that the form is safe to screen-share.
41. As an operator, I want both global and repository configuration editable, so that I can manage layers where they belong.
42. As an operator, I want to see which layer supplies each value, so that I understand what I am overriding.
43. As an operator, I want to re-run the demo pipeline in one click, so that I can revisit the walkthrough.
44. As an operator, I want demo data marked persistently while I view it, so that a screenshot cannot mislead.
45. As an operator, I want the dashboard never to progress work on its own, so that it observes rather than orchestrates.
46. As an operator, I want polling and the live feed unable to trigger a transition, so that watching is passive.
47. As an auditor, I want dashboard mutations recorded with their channel and provenance, so that they are as traceable as CLI actions.

## Implementation Decisions

### Transport, not authority

Served at `http://127.0.0.1:4200`. The bind address is loopback and non-configurable; there is no setting
that widens it.

Reads render state projections from the core. Mutations construct `OperationRequest` values with
`channel: "dashboard"` and invoke the core. The server holds no execution state, caches no approval, and
contains no transition logic. The live feed publishes transitions the core has already made; nothing in
the dashboard path can cause one. That is the structural form of §8.3's rule against becoming a background
orchestrator — there is no code path from a timer or a connection to a mutation.

### The capability token

```ts
type CapabilityToken = {
  value: string;                   // high-entropy, never logged, never persisted
  sessionId: string;
  scope: {
    unit?: RepositoryExecutionUnitId;   // absent means no execution mutations
    globalSettings: boolean;            // machine-wide configuration writes
  };
  issuedAt: string;
  expiresAt: string;
};
```

Issuance and delivery:

1. The CLI generates the token in memory when it starts or explicitly opens the dashboard.
2. The CLI opens the browser at a single-use bootstrap path carrying a nonce — not the token.
3. The bootstrap request consumes the nonce and returns the token in the response body.
4. The page keeps it in a JavaScript variable. Not `localStorage`, not `sessionStorage`, not a cookie, not
   the URL.
5. A manual fallback exists: the CLI can print the token for the operator to paste, for when a browser
   launch fails.

The nonce is in the URL and the token is not, which is what keeps the token out of history, referrers, and
shell logs while still making the flow a single click.

Scope is two-dimensional because the PRD review flagged global Settings as an open question. A token issued
for a repository session carries that `unit` and `globalSettings: false`; a token issued for a global
Settings session carries no `unit` and `globalSettings: true`. A request outside its token's scope is
rejected, so a repository session cannot alter machine defaults and a global session cannot advance an
execution.

The token is revoked when the session ends or the dashboard process exits, and it expires on a short
interval — minutes, not hours — renewed while the page is active. A short lifetime is what keeps an
abandoned tab from remaining an open capability, and renewal is what keeps that from being an annoyance.
The token is never written to configuration, SQLite, URLs, browser storage, logs, envelopes, or artifacts
— and the redaction pipeline in spec 04 treats its value as a secret, so an accidental log line is
redacted.

Requests without a valid token receive read-only data or a rejection.

**Origin enforcement.** A token alone does not protect a loopback server, because a page on any origin can
reach `127.0.0.1`, and DNS rebinding lets an attacker-controlled hostname resolve there after the page has
loaded. Every request is therefore checked on three axes beyond the token:

- `Origin` must match the dashboard's own origin. A cross-origin or absent origin on a mutating request is
  rejected.
- `Sec-Fetch-Site` must be `same-origin`, rejecting requests initiated from another page.
- A required custom header must be present, which cannot be set by a simple cross-origin request and
  therefore forces a preflight the server refuses.
- The `Host` header must be a loopback literal. A request arriving with any other hostname is a rebinding
  attempt and is rejected before the token is even examined.

The token is carried in a header rather than a cookie, so the browser never attaches it automatically and
there is no cross-site request forgery surface to defend.

This hardening closes the remote-attacker path. What it does not close is stated plainly in the interface,
because an operator who overestimates the boundary might expose the port deliberately: this is a loopback
boundary, not authentication. Any process on the machine that can reach loopback and obtain a token can
act as the operator, and a browser extension with access to the page can read the token from memory.

### Operator actorhood

The `dashboard` channel may assert `actor.kind: "operator"` when the request carries a valid token in
scope. This is the second of the two operator channels from spec 01, and it is what makes the Settings
screen a genuine alternative to the conversational path: an operator who prefers forms can approve plans,
confirm local merges, authorize preparation, and classify findings.

The provenance recorded is the session identity and token reference — never the token value.

### Honest projection

The projection is shaped so that misrepresentation requires effort:

```ts
type PbiProjection = {
  pbi: PbiId;
  state: PbiState;                          // the state machine's own value, not a display label
  stageLabels: {
    implementation: "pending" | "in_progress" | "complete";
    gates: "pending" | "passed" | "failed" | "blocked";
    integration: "not_authorized" | "authorized" | "integrated" | "externally_integrated";
  };
  readiness: { technical: boolean; operatorApproved: boolean };   // separate fields, never merged
  context: {
    estimated: ContextEstimate;
    observed: ContextUsage;                 // includes the unknown variant
    monitoring: "per_tool_call" | "between_turns" | "self_reported" | "none";
  };
  budgets: { correctionUsed: number; correctionLimit: number; infrastructureRetries: number };
  waitingReason?: WaitingReason;
  blockedReason?: BlockedReason;
  evidence: { local: EvidenceRef[]; provider: EvidenceRef[] };
  mode: "live" | "demo";
};
```

Three deliberate consequences. `stageLabels` has three independent fields, so there is no single "done"
to render — implementation completion cannot be displayed as integration. `readiness` has two booleans, so
technical readiness cannot be shown as approval. And `context.observed` is the union from spec 03, so an
`unknown` variant has no numeric value to put in a bar.

The watermark indicator renders by `monitoring`: a threshold marker for `per_tool_call`, a between-turns
marker with explicit granularity for `between_turns`, a clearly-labeled self-reported marker for
`self_reported`, and no indicator at all for `none`. No variant renders as an enforced ceiling.

`mode: "demo"` drives the persistent simulated-evidence indicator from spec 07.

### Live feed

Transitions are published over SSE as they are recorded. The feed carries projections, not commands, and
subscribing causes no work. The latency target is under a hundred milliseconds from transition to client
receipt, measured on demo traffic per spec 07 rather than asserted.

A disconnected client reconnects and re-reads the projection rather than replaying a queue, so the feed
never becomes a source of truth.

### Settings

Every write goes through the same `ConfigStore` and whole-document validation as spec 02, with the same
per-layer write authorization, the same `.bak` on save, and the same rejection of any document containing
a secret-shaped value. Sections follow §8.2: harness and host, roles, gates, Git workflow, context limits,
execution capacity, repository readiness, and data handling.

Form behavior that follows from the configuration rules rather than being decided here: field provenance
is displayed because the store exposes it; a repository override cannot raise a global limit because the
store rejects it; the resolved command per role is previewed because the store can resolve it; dead
configuration is badged because the store computes it.

No field accepts a secret value. Credential fields accept environment variable names, which is what makes
the screen safe to screen-share.

## Testing Decisions

**What makes a good test here.** Two layers, split by what each can actually prove.

Transport tests exercise the HTTP and SSE surface against an instrumented core and assert on token
enforcement, scope enforcement, channel assignment, projection contents, and that no mutation occurs
without an operation. These are the tests that matter, because every claim in this spec is about the
boundary rather than about rendering.

Projection-shape tests assert the honesty rules structurally: that `observed` has no numeric value when
unknown, that `stageLabels` cannot collapse, that `readiness` is two fields, and that the watermark
indicator variant is derived from `monitoring`. These are type-level and unit-level assertions on the
projection builder, deliberately — a rendering test would prove a rendering, while the requirement is that
a dishonest rendering has no data to draw from.

**The seam.** The same seam as spec 01 for everything behavioral, with the dashboard exercised through its
own HTTP surface. One parity test per mutating endpoint proves delegation, matching spec 16's pattern.

**Modules under test.** Loopback binding, token generation, bootstrap nonce consumption, token scope
enforcement, revocation and expiry, channel and provenance assignment, projection construction and its
honesty constraints, the watermark indicator derivation, SSE publication and reconnection, and Settings
write delegation.

**Scenarios that must exist**, from PRD §14.3 items 9 and 10:

- The server binds loopback only, and no configuration value widens it.
- A mutating request without a token is rejected; a read request without one succeeds.
- The bootstrap nonce works once; a replay is rejected.
- The token never appears in any URL, log line, configuration file, database row, envelope, or artifact, verified by scanning every persistence sink after a full session.
- The token value is treated as a secret by the redaction pipeline.
- A token scoped to one unit cannot mutate another unit's execution.
- A repository-scoped token cannot write global configuration; a global-settings token cannot advance an execution.
- A token is rejected after session end, after process exit, and after expiry; an active page renews before expiry and an idle one does not.
- A mutating request with a cross-origin `Origin`, an absent `Origin`, or a `Sec-Fetch-Site` other than `same-origin` is rejected even with a valid token.
- A request whose `Host` header is not a loopback literal is rejected before the token is examined.
- A request missing the required custom header is rejected, and the corresponding preflight is refused.
- The token is never accepted from a cookie, and no endpoint reads one.
- A dashboard request with a valid in-scope token may perform operator-only operations; the same request without one may not.
- Recorded provenance contains the session identity and a token reference, never the token value.
- The manual token entry fallback works when the browser launch is simulated as failing.
- Every mutating endpoint produces exactly one core invocation with `channel: "dashboard"`.
- No timer, connection, or SSE subscription produces a mutation, verified by an instrumented core over a session with no operator action.
- A PBI at implementation completion projects `implementation: "complete"` with `integration: "not_authorized"`.
- A technically ready spec with no approval projects `technical: true, operatorApproved: false`.
- An `unknown` observed usage projects with no numeric value available to a bar.
- Each `monitoring` value produces its designated indicator variant, and none produces an enforced-ceiling variant.
- Waiting, blocked, and failed project distinct states with their reasons.
- Correction and infrastructure counts project separately.
- Local and provider evidence project as separate lists, including when one is empty.
- A pending decision projects the exact proposal identity and version.
- A demo unit projects `mode: "demo"` on every record.
- A Settings write with any invalid field is rejected as a whole and writes no file; a valid write produces a `.bak`.
- A repository-layer write attempting to raise a global limit is rejected.
- No Settings field accepts a secret value; credential fields carry environment variable names.
- Field provenance, resolved role commands, and dead-configuration badges are present in the Settings projection.
- SSE latency is measured on demo traffic and reported as a demo measurement.
- A disconnected client reconnects and re-reads the projection rather than replaying a queue.

## Out of Scope

- **Operations, state machine, channels, provenance rules** (spec 01). The dashboard adds no behavior.
- **Configuration schema, validation, layering, provenance, dead-configuration computation** (spec 02): this spec displays and delegates.
- **Redaction** (spec 04): this spec routes output through it and registers the token as a secret.
- **Demo fixture and pipeline** (spec 07): this spec renders the mode marker and provides the re-run control.
- **Capability declaration** (spec 10): the `monitoring` value comes from there.
- **Every operation's semantics**: owned by the spec that defines it.
- **MCP transport** (spec 16): a different channel with a different authority model.
- **Dashboard asset installation** (spec 05) and **packaging** (spec 19).

Out of scope by product decision:

- User authentication, multi-user authorization, and remote access. Explicitly out of scope for v4 (§8.2).
- Strong browser attestation. The PRD calls this a lightweight loopback boundary, and the interface says so (§8.2).
- A configurable bind address. Non-configurable by §8.2.
- Any background progression from the dashboard. Forbidden by §8.3.
- Persisting the token anywhere, including browser storage. Forbidden by §8.2.
- A single aggregate status for a PBI. §8.3 requires the stages to be distinguishable.

## Further Notes

**Binding decisions.** ADR-0001 shapes the projection more than anything else here. The watermark
indicator is the single place in the product where an unenforced guarantee would be most persuasive, so the
indicator variant is derived from the declared capability rather than from a threshold value, and the
`none` case renders nothing rather than an empty bar.

**Glossary alignment.** Dashboard Capability Token, Context Watermark, Implementation Completion, Merge
Authorization, and Execution State follow `CONTEXT.md`, including the terms it marks to avoid: the token is
not a frontend-generated secret and not user authentication; execution state is not a status label or a
dashboard display.

**Glossary gap for `/domain-modeling`.** Bootstrap nonce, token scope, and stage label are introduced here
without entries and should get them.

**Where the risk actually sits.** Origin enforcement closes the remote path, which was the one an attacker
could reach without already being on the machine. What remains is local and irreducible at v4 scope: any
process that can reach loopback and obtain a token acts as the operator, and a browser extension with
access to the page reads the token from memory. The PRD accepts this explicitly, and the interface's job is
to state the boundary rather than to close it. What matters is not overclaiming — the dashboard should not
describe itself as authenticated, and the token should not be presented as a credential, because an
operator who believes it is one might expose the port deliberately.

Worth noting what was considered and rejected: requiring a short code printed by the CLI before an
irreversible mutation would tie the action to terminal access rather than to browser access. It was
declined because it adds friction to exactly the path the Settings screen exists to make friction-free, and
because the local attacker it would stop can generally read the code too. If the local threat model ever
changes, that is the first mitigation to revisit.

The second risk is the honesty constraints eroding under design pressure. A designer will want one
progress bar and one status chip per slice, and the projection deliberately makes that hard by refusing to
provide a single value. Expect the request; the answer is that the three stages and the two readiness
booleans are a product requirement from §8.3 rather than a data-modeling preference.

**Sequencing note.** This spec depends on specs 01 and 02 and can be built early as a read-only monitor,
with mutations added once the token flow exists. Building the projection first is worth it regardless: it
is the artifact that forces every other spec's states to be nameable, and a state nobody can render
honestly is usually a state that was modeled wrong.
