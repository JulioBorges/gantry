## Spec 02 — config-and-snapshot

This spec owns the single `ConfigStore` that every transport reads and writes through, the whole-document validation that makes an invalid combination of layers unrepresentable, the Execution Rule Snapshot that freezes an execution's rules at start, its migration path, and Governance Precedence resolution. It is the value supplier for the whole system: spec 01 defines Correction Budget accounting but takes the number from here; specs 05, 06, and 17 all write through the store; every envelope, approval, finding, and Merge Authorization binds a snapshot identity. The risk sits in two places. First, **relational validation is the entire point** — each layer can look reasonable alone, so a slice that validates per layer instead of on the merged document has built the wrong thing, and the failure is silent. Second, **precedence assumes rules can be expressed as keyed assertions**, which holds for configuration and provider protections and does not hold for prose in a constitution or an ADR; the spec's position is that a prose-only document participates at its level with no machine-checkable keys, so it can block through conflict but never silently resolve one. A slice that tries to extract keys from prose has overreached.

### Slices

---

**01 — Configuration layering and the effective document**

**What to build**: The `ConfigStore` module and the configuration schema with all sections declared — host and role routing, context policy (Context Watermark, Initial Context Budget), capacity limits, budgets, Git Workflow Policy, Artifact Location Mapping, verification commands and declared Check Resources, data handling (Data Egress Policy matrix, Telemetry Retention level), and dashboard settings — carrying the approved defaults so a fresh install is already correct: global capacity two, Correction Budget five, Infrastructure Retry allowance three, Context Watermark forty percent, Initial Context Budget fifteen percent. Layer resolution runs built-in defaults, then the machine-wide file, then the repository override, with fixed merge semantics: objects merge key by key, arrays are replaced wholesale, an explicit `null` in a higher layer clears the inherited value, and an unknown key is a rejection rather than a preserved extension. The store's read surface returns one resolved immutable document plus per-field provenance naming the supplying layer, reached through a `config.read` operation registered in the shared operation core's catalog, with `gantry config show` as the reading transport. Sections whose semantics belong to other specs are declared and shaped here but not interpreted here.

**Acceptance criteria**
- With no files present on either layer, `config.read` returns every approved default and provenance reports the built-in layer for each.
- A sparse repository override inherits every unstated value; provenance names the repository layer for stated fields and the lower layer for the rest.
- An array-valued setting stated in the repository override replaces the inherited list rather than appending to it; an explicit `null` clears an inherited value rather than being treated as absent.
- An unknown configuration key at any layer is rejected, naming the key path and the layer that supplied it.
- Tests drive `config.read` through the operation core's `invoke` against layer files written into a temporary home and repository directory; `gantry config show` has one parity test proving delegation.

**Blocked by**: needs the operation core `invoke` entry point, the operation catalog registration mechanism, and the rejection-code vocabulary from `execution-core`. (Schema *sections* can be declared with placeholder inner shapes; see the consumed-contracts table for the section owners.)

**Parallelizable with**: nothing intra-spec — this is the bootstrap slice.

---

**02 — Whole-document validation and secret rejection**

**What to build**: Validation that runs on the merged document rather than per layer, because the constraints that matter are relational — a repository capacity limit cannot exceed the global one, a file-mutating role cannot be routed to a gateway, a check declaring a shared Check Resource must declare its serialization behavior. Validation returns every violation at once, each naming the field path and the layer that supplied the offending value, and surfaces through `config.read` so an invalid merged document is refused at read time with no write involved. Secret rejection is two layers: the schema has no field whose type admits a credential value (credentials are referenced by environment variable name only, and a name field whose content does not look like an environment variable name is rejected), plus a scan rejecting any string anywhere in the document that matches the configured secret detectors. The scan is a defense against accident, not a security boundary — the boundary is the absence of a field to put a secret in.

**Acceptance criteria**
- Two layers that are each individually valid but whose merged result violates a relational constraint are rejected, naming both the field path and the supplying layer.
- A document violating several constraints reports all of them in one rejection, not the first.
- A file-mutating role routed to a gateway is rejected; a check declaring a shared Check Resource without serialization behavior is rejected.
- A string matching a secret detector anywhere in the document is rejected, including in a field whose name gives no hint it holds one.
- A credential field populated with a value rather than an environment variable name is rejected; no schema field exists whose declared type accepts a credential value (provable at type level).

**Blocked by**: 01. The detector scan needs the secret detector ruleset from `data-handling`; the schema-shape half of secret rejection depends on nothing and the slice can start against a fixture detector set.

**Parallelizable with**: 04, 06.

---

**03 — Validated writes with per-layer authorization**

**What to build**: The `config.write` operation, whole-document and transactional from the caller's perspective: the merged result is validated before anything is written, the target layer's previous file is copied to a backup sibling, and the write either fully lands or leaves the original in place. Write authorization is per layer — a repository override attempting to set or raise a global capacity limit is rejected with the field path, because a single repository must not consume more of the machine than the operator allowed. The writing transport is `gantry config set`, with one parity test proving delegation. This slice is what guarantees the dashboard Settings screen and the setup interview cannot reach configuration by any other path.

**Acceptance criteria**
- A write whose merged result fails validation in any field leaves the previous file byte-identical on disk and returns every violation.
- A successful write produces a backup of the previous file at the target layer.
- A repository-layer write attempting to raise the global capacity limit is rejected naming the field path, while the same value written at the machine layer is accepted.
- A write interrupted partway leaves either the complete new document or the untouched original, never a half-applied one.
- `gantry config set` has one parity test proving it delegates to `config.write`; no test asserts on file formatting or key order.

**Blocked by**: 02 (validate-before-write needs the validator). Writes must traverse the redaction sink enforcement interface from `data-handling`.

**Parallelizable with**: 04, 05, 06.

---

**04 — Execution Rule Snapshot capture and identity**

**What to build**: Capture of the Execution Rule Snapshot by the core at execution start, before the Planning Approval transition, stored immutably. Contents are the resolved effective configuration document, content hashes and resolved paths of the governance documents in effect (constitution, applicable ADRs, root `AGENTS.md`, approved spec and PBI artifacts), the approved verification commands each with working directory, environment variable references, declared effects, declared Check Resources and Check Stability criterion, the observed versions of the tools those commands invoke, the effective Artifact Location Mapping, and the engine and protocol versions. Identity is a hash over canonicalized snapshot content, so identical rules yield one identity and any change yields a new one. Governance document content is hashed rather than copied, with the resolved location retained so versioned content is recoverable from Git; a hash whose content cannot be recovered is a missing-source condition to reconcile, not a reason to proceed. Every dispatch, approval, finding, gate result, and Merge Authorization records its governing snapshot identity, and a record whose snapshot is unavailable blocks rather than being silently reinterpreted.

**Acceptance criteria**
- An execution started under one configuration continues under it after a subsequent edit to configuration, the constitution, or an ADR; a new execution started after the edit captures a different snapshot identity.
- Two executions whose captured inputs are identical share one snapshot identity; changing any single captured input — a config field, a governance document's content, an approved verification command, a tool version — produces a different one.
- A decision record carries its snapshot identity, and a record whose snapshot is missing blocks with a reconciliation-required rejection rather than resolving against current configuration.
- A snapshot does not grant permission for something its own captured rules forbid, and does not justify using a stale target revision — current-target verification still applies at integration.
- Snapshots are never removed while any record references them.
- Content hashes are computed over normalized content, not over bytes on disk.

**Blocked by**: 01. Needs the normalized content hashing rule (line endings) from `data-handling`, the Artifact Location Mapping schema from `repository-readiness`, and the atomic transition-plus-audit persistence from `execution-core`.

**Parallelizable with**: 02, 03, 06.

---

**05 — Snapshot migration and approval invalidation**

**What to build**: `execution.migrateRuntime` and its rule-change counterpart as operator-only operations that move an in-flight execution to a new snapshot. A migration records the old and new snapshot identities and the operator's stated reason, then classifies every existing record: approvals whose governing rules changed are invalidated, gate results whose rules or commands changed return to `pending`, and unaffected records keep their original binding. Affected work is revalidated before it advances. Two specific invalidation rules ship with this slice: a changed Verification Command Approval invalidates Comparison Evidence produced by its previous version, and a recorded tool version change invalidates comparison evidence that depended on it. The normal path for a rule change remains simply the next execution, which always captures a fresh snapshot — migration exists so that moving running work is a decision the operator makes, never a side effect of an edit.

**Acceptance criteria**
- A migration invalidates approvals whose governing rules changed, returns affected gates to `pending`, and leaves unaffected records bound to their original snapshot.
- A migration requested from the MCP channel is refused with `operator_channel_required`; the same request from an interactive CLI session or a dashboard request carrying a valid Dashboard Capability Token is accepted.
- A changed verification command invalidates evidence produced by the previous version of that command; unrelated evidence is untouched.
- A tool version change recorded in the new snapshot invalidates the comparison evidence that depended on that tool.
- The migration record names both snapshot identities and the reason, and is queryable afterwards.
- Affected work cannot advance until it has been revalidated under the new snapshot.

**Blocked by**: 04. Needs operator-channel derivation and the approval/gate record families from `execution-core`.

**Parallelizable with**: 02, 03, 06, 07.

---

**06 — Governance Precedence resolution and conflict blocking**

**What to build**: Resolution of the rules bearing on a decision into typed assertions, each tagged with its source level, and selection of the highest-precedence assertion per rule key. The level order and the resolution outcome shape are the decision-rich part:

```ts
type SourceLevel =
  | 1 // provider protections and absolute security requirements
  | 2 // the approved Execution Rule Snapshot
  | 3 // CONSTITUTION.md
  | 4 // applicable ADRs
  | 5 // approved spec and PBIs
  | 6 // AGENTS.md and operational configuration

type Resolution =
  | { resolved: true; value: unknown; level: SourceLevel; overridden: RuleAssertion[] }
  | { resolved: false; conflict: RuleAssertion[] };   // same level, incompatible values
```

Overridden assertions are retained in the resolution so an audit can show what was outranked. A lower level attempting to weaken a higher-level invariant is rejected as an override attempt rather than quietly losing. Two incompatible assertions at the same level are unresolvable: the affected transition blocks and the core surfaces a concrete proposed governance or plan amendment naming both sources and the conflicting key. A prose-only document participates at its level and contributes no machine-checkable keys. Resolution must be consulted by at least one real transition in the core and recorded alongside the decision it informed — a resolver nobody consults is not a governance mechanism, so tests drive the transition, not the resolver.

**Acceptance criteria**
- A level-6 assertion loses to a level-3 one, and the recorded resolution names what was overridden and from where.
- A level-6 assertion that would weaken a level-3 invariant is rejected as an override attempt, distinguishable in the outcome from merely being outranked.
- Two incompatible assertions at the same level block the affected transition and produce a proposed amendment naming both sources and the conflicting key.
- A provider protection at level 1 wins over every local setting, including the snapshot.
- Every decision informed by a resolution records which source level and which document version supplied the governing rule.
- Changing the precedence order itself is treated as a level-3 change requiring explicit governance approval.

**Blocked by**: 01. Needs a transition declaration in `execution-core` that consults a governance rule key, so the resolution has a real consumer to be driven through. Level-2 assertions bind the snapshot identity defined in slice 04; the resolution and conflict machinery can be built and proven against levels 1 and 3-6 without it.

**Parallelizable with**: 02, 03, 04, 05.

---

**07 — Role routing resolution and dead configuration**

**What to build**: Resolution of each configured role to the concrete command that will actually run, previewable before anything is dispatched, plus refusal of a dispatch whose role routing cannot be resolved — returning setup guidance so the host harness reports a fixable problem instead of failing obscurely. Alongside it, the store computes from execution history which configured roles have never been invoked and which verification commands have never produced evidence, and exposes that on its read surface. Dead-configuration reporting is advisory and never blocks anything; it exists because a role configured with a typo is silent until the moment it matters. This is the slice that makes configuration observable rather than merely stored.

**Acceptance criteria**
- The resolved command for each configured role is returned by a read operation and rendered by the CLI before any dispatch occurs.
- A dispatch whose role routing cannot be resolved is refused with a typed rejection carrying setup guidance naming the unresolved role.
- A role configured but never invoked, and a verification command that has never produced evidence, both appear in the dead-configuration report.
- The dead-configuration report never causes a rejection, a blocked state, or a refused transition in any test.
- The report is derived from execution history rather than from static configuration inspection alone.

**Blocked by**: 01. Needs the dispatch operation from `execution-core` to attach the refusal to, and the harness compatibility matrix as data from `machine-setup` to resolve a role to a driver.

**Parallelizable with**: 02, 03, 04, 05, 06.

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Operation core `invoke`, catalog registration, rejection-code vocabulary | `execution-core` | 01 (then all) |
| Operator-channel derivation (`operator_channel_required`) | `execution-core` | 05 |
| Atomic transition-plus-audit persistence and record families | `execution-core` | 04, 05 |
| A transition declaration that consults a governance rule key | `execution-core` | 06 |
| Dispatch operation to attach a routing refusal to | `execution-core` | 07 |
| Normalized content hashing (line endings) | `data-handling` | 04 |
| Redaction sink enforcement interface | `data-handling` | 03, 04 |
| Secret detector ruleset reference | `data-handling` | 02 |
| Data Egress Policy matrix and Telemetry Retention level shapes | `data-handling` | 01 (section shape), 02 (constraints) |
| Artifact Location Mapping schema | `repository-readiness` | 01 (section shape), 04 (captured) |
| Verification Command Approval record shape (command, working directory, environment references, declared effects) | `repository-readiness` | 04, 05 |
| Check Stability criterion and Check Resource declaration shapes | `verification-adapters` | 02 (relational constraint), 04 (captured) |
| Git Workflow Policy schema shape | `git-integration` | 01 (section shape) |
| Harness compatibility matrix as data | `machine-setup` | 07 |
| Governance-path permission in a transition declaration | `baseline-transitions` | 06 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| Effective configuration document, per-field provenance, `config.read` | 01 | `machine-setup`, `repository-readiness`, `dashboard`, `mcp-server`, `demo-mode` |
| Approved default limit values (capacity, Correction Budget, Infrastructure Retry, Context Watermark, Initial Context Budget) | 01 | `execution-core`, `pbi-execution-loop`, `entropy-gate`, `harness-adapters` |
| Whole-document validation and rejection reporting (field path plus supplying layer) | 02 | `machine-setup`, `dashboard` |
| `config.write`, per-layer write authorization, backup on save | 03 | `machine-setup`, `dashboard`, `mcp-server` |
| Execution Rule Snapshot content, identity hash, and the binding recorded on every decision | 04 | `gtp-protocol` (`ruleSnapshot` on every envelope), `execution-core`, `spec-validation`, `slicing-and-approval`, `harness-adapters`, `verification-adapters`, `entropy-gate`, `git-integration`, `baseline-transitions` |
| Snapshot migration and its invalidation classification | 05 | `baseline-transitions`, `execution-core` |
| `SourceLevel` / `RuleAssertion` / `Resolution` and same-level conflict blocking | 06 | `entropy-gate`, `baseline-transitions`, `compound-learning`, `git-integration` |
| Role routing resolution, resolved-command preview, dead-configuration report | 07 | `harness-adapters`, `dashboard` |

### Risks / judgement calls

**The CLI surface is invented, narrowly.** No spec claims a `gantry config` command — spec 16 says "the CLI is the other transport and gets its own parity test" and defers semantics to each operation's spec. I gave slices 01, 03, and 07 a minimal `config show` / `config set` / role-preview CLI as this spec's transport surface, because without one there is nothing to write a parity test against and the slices stop being tracer bullets. If the operator would rather the CLI surface live entirely in `machine-setup` or `release-engineering`, slices 01/03/07 lose one acceptance criterion each and nothing else changes.

**I merged validation and secret rejection, and split write off.** The tempting split was validation-and-write as one slice. I kept them apart because write authorization per layer, backup, and atomicity are a genuinely separate body of work from relational constraint checking, and because validation is observable through `config.read` alone — which keeps slice 02 a real tracer with no write path. The cost is a three-deep chain 01 → 02 → 03. If you want to shorten it, merging 02 and 03 is the safe merge; merging 01 and 02 is not, because the merged slice would be the largest in the spec.

**Precedence is not blocked on snapshot capture, and I am least sure about this one.** Level 2 of the precedence order is the Execution Rule Snapshot, defined in slice 04. I declared slice 06 blocked only by 01 so the two biggest independent pieces can run concurrently, on the reasoning that the resolution and conflict machinery is provable against levels 1 and 3-6. If the agents picking these up would rather not carry a stub level-2 source, make 06 blocked by 04 and accept the serialization.

**Slice 07 bundles three small things.** Resolved-command preview, unresolved-routing dispatch refusal, and dead-configuration reporting are three separate user stories. Alone, each is too thin to be a PBI; together they form a coherent "make configuration observable" slice. It is also the only slice reaching into `machine-setup`'s compatibility matrix, so it is the most likely to stall on a cross-spec contract — it is last for that reason, not because it is least valuable.

**What I deliberately did not slice.** The precedence resolver does not attempt to extract machine-checkable keys from prose in a constitution or an ADR. The spec's own risk section takes this position and `entropy-gate` owns executable ADR rules. Expect the set of recognized rule keys to grow; do not expect the mechanism to change.
