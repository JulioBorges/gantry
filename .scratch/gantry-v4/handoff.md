# Handoff — Gantry v4 spec decomposition

Type: handoff
Status: superseded-in-part
Created: 2026-09-11
Updated: 2026-09-12
Map: [`map.md`](./map.md) · Slice index: [`slice-index.md`](./slice-index.md)

> **Update, 2026-09-12 — read this before the rest of the file.**
>
> This document records the state at the end of the *spec decomposition* phase. The **issue
> decomposition** phase has since run: all 19 specs were broken into **132 issues** at
> `.scratch/<slug>/issues/NN-<slug>.md`, every one `Status: ready-for-agent`, with cross-spec blockers
> written as `` `<spec-slug>#NN` `` references.
>
> **[`slice-index.md`](./slice-index.md) is now the authority** for resolving a cross-spec dependency,
> and it also records the operator decisions settled during that phase — the SQLite driver, the
> repository bootstrap owner, the test-seam boundary, and the wave 0 opening order. Those must not be
> re-litigated from this file.
>
> Fifteen contracts turned out to be needed by one spec and owned by none; all are now assigned in
> `slice-index.md`. The sections below on standing decisions, deliberate inconsistencies, and honest
> gaps remain accurate. The "What was not done" section is partly stale and is marked inline.

## Where things stand

`PRD.md` (v4.0.0) has been decomposed into **19 specs, all drafted**. Every spec is at
`.scratch/<slug>/spec.md` with `Status: ready-for-agent`, and [`map.md`](./map.md) is the index with
owns / PRD section / `Blocked by` / status per spec.

Nothing has been implemented. The repository still contains no `package.json` and no `src/`. These are
specifications, not code, and they have not been reviewed by the operator.

```
.scratch/
├── gantry-v4/map.md          ← the index; read this first
├── gantry-v4/handoff.md      ← this file
├── execution-core/spec.md              (01)  config-and-snapshot/spec.md      (02)
├── gtp-protocol/spec.md                (03)  data-handling/spec.md            (04)
├── machine-setup/spec.md               (05)  repository-readiness/spec.md     (06)
├── demo-mode/spec.md                   (07)  spec-validation/spec.md          (08)
├── slicing-and-approval/spec.md        (09)  harness-adapters/spec.md         (10)
├── pbi-execution-loop/spec.md          (11)  verification-adapters/spec.md    (12)
├── entropy-gate/spec.md                (13)  git-integration/spec.md          (14)
├── baseline-transitions/spec.md        (15)  mcp-server/spec.md               (16)
├── dashboard/spec.md                   (17)  compound-learning/spec.md        (18)
└── release-engineering/spec.md         (19)
```

The next phase is **issues**: each spec breaks into implementation tickets at
`.scratch/<slug>/issues/NN-<slug>.md`, per `docs/agents/issue-tracker.md`. None exist yet.

## Standing decisions — do not re-litigate these

These were decided once and applied across all 19 specs. A new session should treat them as settled
context, not as open questions.

1. **One testing seam.** Every spec binds its tests to the shared operation core's `invoke`, called in
   process, against a real temporary SQLite database (WAL) and a real temporary Git repository, with
   harness drivers and check adapters injected as fakes. CLI, MCP, and dashboard get one parity test each
   proving delegation — no behavior tests. Rationale: §8.1's "no interface may bypass an invariant" puts
   the invariants below the transports, so they are tested once.
   Two deliberate exceptions: spec 12's adapter parsers are tested against recorded tool output, and spec
   19's subject is the release pipeline, which lives outside the application.

2. **Two operator channels, and MCP is not one.** `actor.kind: "operator"` can only be asserted by an
   interactive CLI session or a dashboard request carrying a valid capability token. The MCP channel is
   always an agent. Operator-only operations return `operator_channel_required`. This is the mechanism
   that satisfies the PRD's "an agent's report of operator approval is insufficient" without adding a
   second approval stage.

3. **Documents are projections.** Canonical Markdown owns the plan; SQLite owns execution state. A status
   rendered in a document has no authority and is never read when deciding a transition.

4. **An absent capability beats a claimed one.** ADR-0001, applied structurally rather than by
   discipline: `ContextUsage` has an `unknown` variant, `StopOutcome` has `unsupported` and
   `requested_cooperatively`, capabilities require passing conformance probes, and harness presence is a
   separate type from harness capability with no derivation between them.

5. **Fail closed.** Incomplete comparison evidence leaves a gate unapproved; unconfident redaction
   withholds content and marks the operation blocked for review; an unknown operation outcome blocks
   rather than retrying; ambiguous egress authorization blocks dispatch.

6. **Budget accounting.** A correction attempt is consumed at correction *dispatch*, not at revalidation
   — so an interrupted cycle stays consumed and a resume continues the same attempt. Infrastructure
   retries are a separate allowance and never approve a gate. Neither resets on handoff, agent
   replacement, cancellation, or resumption.

7. **Rules enforced by shape, not by check.** Where a rule could be forgotten, the type makes it
   unrepresentable: the adversarial critic's payload has no field that can clear a deterministic finding;
   the dashboard projection has no single "done" value and no numeric context value when usage is
   unknown; configuration has no field that can hold a secret.

8. **Everything is written in English**, including generated user files (§12.4), and uses `CONTEXT.md`'s
   vocabulary while avoiding the synonyms it marks `_Avoid_`.

## Deliberate inconsistencies — do not "fix" these

Two places look like contradictions and are intentional. Both are stated in the specs, but a reviewer
skimming will want to reconcile them.

- **Unknown keys.** Configuration (spec 02) **rejects** unknown keys; GTP envelopes (spec 03)
  **preserve** them in `extensions`. Configuration is not an extensibility surface; the protocol is.
- **Cleanup authorization.** Live units require a two-step propose-then-authorize manifest (spec 01);
  `demo.reset` (spec 07) is exempt, narrowly, because a demo unit has no remote, no provider objects, and
  no dependents. The exemption is enforced by rejecting `demo.reset` against a live unit, not by
  loosening cleanup.

## Cross-spec decisions to lock before writing issues

Each spec ends with a "Sequencing note" naming the one thing worth settling before its issues are
written. Consolidated, because most of them are shared contracts:

| Decision | Owner | Read by |
|---|---|---|
| `extensions` lifting rule (unknown keys into a side field) | 03 | 01 persistence shape, every 03 schema |
| Artifact Location Mapping schema | 06 | 08, 09, 12 |
| Criterion identity rule (required, never generated, stable) | 08 | 03, 09, 13 |
| Plan version hash definition | 09 | 11 dispatch gating, 15 |
| Adapter interface — `StopOutcome`, `ReconciliationResult` variants | 10 | 11's entire control flow |
| Handoff sequence ordering — save point → compile → stop → reconcile → dispatch | 11 | proves work is never lost or duplicated |
| Normalized finding shape, content anchor, tree-sitter symbol derivation | 12 | every adapter parser, all of 13, 15 |
| Normalized content hashing (line endings) | 04 | 12 content anchors, 02 snapshot hashes, every retained record |
| "Aggravated" classification rules | 13 | 13's integrity comparison and correction loop |
| Merge authorization binding and its invalidation rule | 14 | every other decision in 14 |
| Governance-path permission in a transition declaration | 15 | 03's protection rule |
| Redaction sink enforcement interface | 04 | **every writer in the system** |
| MCP schema derivation from operation schemas | 16 | prevents catalog drift |
| Harness compatibility matrix as data | 05 | 08, 09, 11, 13, 14 each ship a skill |

**The one to build first regardless of spec order:** spec 04's redaction sink interface. Retrofitting it
means auditing every writer, and spec 04's own sequencing note says so.

## Recommended issue-writing order

Not the same as the map's build order. Issues should be written where the contracts are shared, so later
specs inherit settled shapes:

1. **01 `execution-core`** — largest and most structuring; everything references its catalog and state
   machine.
2. **03 `gtp-protocol`** — mutually referential with 01; expect the issues to interleave, and expect 03
   to propose small additions to 01's catalog rather than a parallel one.
3. **04 `data-handling`** — the sink interface blocks every other writer.
4. **02 `config-and-snapshot`** — 05, 06, and 17 all write through it.
5. **12 `verification-adapters`** then **13 `entropy-gate`** — the finding shape is the widest shared
   contract after the operation catalog.
6. **06 `repository-readiness`** → **08** → **09** — the mapping and criterion identity chain.
7. **10** → **11** — adapter primitives before the loop that orchestrates them.
8. **14**, then **07 `demo-mode`** — the demo's scripted scenario should be written once the real state
   sequences are settled.
9. **19 `release-engineering`** at any point; it depends on nothing and should be *implemented* first.
10. **05**, **15**, **16**, **17**, **18** last.

## Glossary gaps for `/domain-modeling`

Every spec flagged the domain terms it introduced without a `CONTEXT.md` entry. Consolidated, since
several are shared and should be defined once:

| Spec | Terms |
|---|---|
| 01 | shared operation core, operation intent record, rejection code (as a contractual value) |
| 02 | rule assertion, source level, field provenance |
| 03 | criterion identity, scope violation |
| 04 | payload class, replayable reference, redaction confidence |
| 05 | harness presence, skill installation mechanism, installation divergence |
| 06 | readiness item, declared coverage, working tree treatment |
| 07 | demo mode (as a unit property), simulated evidence (as a projection property) |
| 08 | normalized spec model, canonical section, spec complement |
| 09 | plan version, story coverage map, change classification |
| 10 | conformance probe, support matrix, result path |
| 11 | worktree lease, activity marker, save point, micro-commit |
| 12 | problem identity, message fingerprint, resource scope |
| 13 | absolute mandatory rule, integrity finding, blocking reason |
| 14 | candidate preparation, observation budget, external integration |
| 15 | transition manifest, comparison mode, coverage change |
| 16, 17, 01 | transport adapter, channel |
| 17 | bootstrap nonce, token scope, stage label |
| 18 | learning candidate, observation fingerprint, occurrence count |
| 10, 14, 19 | support matrix (shared — define once) |

## Honest gaps recorded in the specs

Eight limitations were identified after the first draft and worked through with the operator on
2026-09-12. Five were reduced or resolved and the specs updated; three remain, narrower than before. Each
spec's "Where the risk actually sits" section carries the current state.

### Resolved

- **Finding identity** (12, 15) — identity is now `rule` + `path` + `symbol` + `contentAnchor`, with the
  message excluded. `symbol` is derived by Gantry via tree-sitter rather than taken from the tool, and
  `contentAnchor` hashes the normalized reported line plus neighbours. This fixed two limitations at
  once: count-based matching fell back to the narrow no-location case, and a tool upgrade rewording
  messages no longer invalidates every identity. Spec 15's per-finding `identityMappings` became
  `ruleMappings` plus a per-rule count fallback. **Tree-sitter is now an engine dependency.**
- **Result channel** (10, 16) — `resultChannel` is `"file" | "mcp" | "both"` determined by conformance
  probe instead of assumed. An integration where file writing is unreliable is discovered at probe time;
  duplicate submission is already covered by submission idempotency.

### Reduced

- **Assertion weakening** (13) — three layers now: assertion-shape comparison as an always-on warning
  (syntactic, evadable); automatic adversarial-critic escalation when the candidate touches test files
  covering approved criteria, overriding a global `static` mode; and an opt-in mutation adapter (12)
  whose surviving mutants arrive as ordinary findings. Only the third is deterministic. With it disabled,
  the gap is a heuristic plus a reviewer opinion — better than open, not the same as covered.
- **Concurrent worktree writes** (11) — the activity marker now derives from observed Git state (index
  hash plus `git status --porcelain` fingerprint) rather than file timestamps, and the worktree is frozen
  read-only during the handoff reconciliation window. The dangerous window is closed. Outside a handoff
  it remains detection, and the freeze is advisory against a sufficiently privileged process.
- **Dashboard token** (17) — origin enforcement added: `Origin`, `Sec-Fetch-Site`, a required custom
  header, and a loopback-literal `Host` check, which closes the DNS-rebinding path a token alone does not
  defend. Token lifetime shortened with renewal while the page is active. An out-of-band confirmation
  code for irreversible mutations was considered and declined — it adds friction to the path the Settings
  screen exists to smooth, and a local attacker can usually read the code too.

### Still open

- **The local threat model for the dashboard** (17). Any process reaching loopback with a token acts as
  the operator; a browser extension reads it from page memory. Irreducible at v4 scope, and the interface
  must not describe itself as authenticated.
- **Windows** (§14.1). Now concrete rather than vague: spec 19 names six platform-divergent behaviors
  with owning specs, and the documented status is derived per row rather than from a job result. Two
  divergences were discovered during this pass and are new to the specs — **Windows has no cooperative
  process signal**, so `requestStop` needs job objects or declares `agentInterruption: "none"` (10); and
  **`core.autocrlf` makes filesystem-byte hashes platform-dependent**, so all content hashing is now
  specified over normalized content (04).
- **Compound learning's value** (18). Unprovable in advance. Rejection-rate backoff per source and a
  section size limit with mandatory consolidation were added to make it self-limiting. The signal to
  watch is whether the size limit ever gets raised.

## What was not done

- **No operator review.** All 19 specs are drafted and unreviewed. The `ready-for-agent` status reflects
  that they are complete enough to slice, not that anyone has approved them.
- ~~**No issues.**~~ **Superseded on 2026-09-12** — see "Update" at the top of this file. All 19 specs
  were decomposed into 132 issues under `.scratch/<slug>/issues/`.
- **No code, no `package.json`, no CI.** Spec 19 argues CI should exist from the first commit; it does
  not yet. `release-engineering#01` is the issue that changes this and is the project's blocking root.
- **No `CONTEXT.md` updates.** Every gap above is recorded in its spec and nowhere else.
- **No cross-spec consistency pass.** The specs were written in dependency order and cross-reference each
  other by number, but nothing verified that every `Out of Scope` pointer has a matching owner on the
  other side. That is the cheapest useful review to run next.
- **Verification performed:** file existence, line counts, `Status` lines, relative link resolution
  between `map.md` and the specs. Nothing beyond that — these are documents, so there is nothing to
  execute.

## Starting a new session

```
Read .scratch/gantry-v4/slice-index.md first — it is the authority for settled
decisions and for resolving any `<spec-slug>#NN` reference.
Then .scratch/gantry-v4/map.md for how the specs relate, and this handoff for
the standing decisions behind them.
Then read .scratch/<slug>/issues/NN-<slug>.md for the issue you are picking up,
and .scratch/<slug>/spec.md when the issue's context is not enough.
CONTEXT.md and docs/adr/ are binding on all of them.
```

Two issues have no blockers and are the only places work can start: `release-engineering#01` (the
repository bootstrap every other spec inherits) and `machine-setup#02` (the harness compatibility matrix,
pulled forward because five specs read it and it depends on nothing).

The specs assume the reader has not read `PRD.md`. Each states the problem from its own scope and cites
the PRD sections it resolves, so a session can work on one spec without loading the 94KB document. Load
`PRD.md` only when a spec's citation needs checking.
