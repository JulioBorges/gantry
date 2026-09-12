## Spec 14 — git-integration

This spec owns the moment Gantry stops validating and starts mutating: it resolves the repository's Git Workflow Policy, prepares a Merge Candidate from the PBI branch and the current integration target, binds Merge Authorization to that exact candidate/target pair, serializes the integration, and drives the two delivery paths — local merge behind the Mutation Approval Boundary, and Pull Request delivery behind Provider Identity, Provider Protection Authority, and Pull Request Observation. It also owns what happens when a mutation's response is lost (Operation Reconciliation against authoritative Git or provider state) and when the world changes underneath it (requested changes, externally resolved Pull Requests). The risk sits in exactly two places: the window between validating a candidate and mutating the target, which is closed by the unit lease plus an in-section target re-check for same-unit processes but remains open for a shared remote in local mode; and external integration content matching, where Gantry can confirm the PBI criteria hold on the integrated target but cannot prove the exact candidate landed. Everything else in the spec is a consequence of the authorization binding and its invalidation rule, which is why that rule is settled in slice 02 and consumed everywhere after.

### Slices

- **01 — Git Workflow Policy resolution and the integration operation surface**
- **What to build**: The `GitWorkflowPolicy` shape (branch naming template, starting branch, integration target, delivery mode, local check references, observed provider requirements), its resolution from configuration through the Execution Rule Snapshot, and the three workflow presets `trunk-local`, `trunk-pr`, `develop-pr` as adjustable starting points rather than fixed bundles. A repository with no chosen policy resolves to a `needs_decision` readiness item and cannot run governed execution — there is no silent default, because guessing how a team integrates code is not a recoverable error. This slice also registers the `integration.*` operation namespace on the shared operation core with its typed rejection codes, so later slices add handlers rather than inventing a surface, and exposes policy inspection through the CLI with one parity assertion on the other transports.
- **Acceptance criteria**:
  - A unit whose configuration carries no Git Workflow Policy produces a `needs_decision` item and every governed-execution operation is rejected with a typed code naming the missing policy.
  - Each of the three presets resolves to a complete, valid policy, and a test mutates every field of a preset-derived policy and observes the change survive snapshot capture.
  - A policy captured into the Execution Rule Snapshot is read from the snapshot, not from live configuration, for the lifetime of an execution.
  - The `integration.*` operations are discoverable on the core with their rejection codes enumerated; the CLI surface delegates without reimplementing any decision.
  - Local checks are required when the mode is `local_merge` and their absence is a typed rejection.
- **Blocked by**: Contract `shared operation core invoke, operation catalog registration and typed rejection codes` (`execution-core`); contract `Execution Rule Snapshot capture and identity, config schema validation` (`config-and-snapshot`); contract `readiness item shape and needs_decision classification` (`repository-readiness`).
- **Parallelizable with**: none intra-spec (it is the bootstrap), but it is small and unblocks 02 and 05 together.

---

- **02 — Merge Candidate preparation and the Merge Authorization binding**
- **What to build**: Candidate preparation merges the current integration target revision into the PBI branch and records the resulting `candidateRevision`; merge, never rebase, because rebasing rewrites the micro-commits and save points that retained evidence points at. Optional history consolidation is a policy setting that produces a new candidate revision and therefore forces revalidation. The Merge Authorization record binds unit, PBI, target revision, candidate revision, snapshot, gate decision and optional provider evidence, and it is valid only while both revisions still hold — any movement in either invalidates it, returns the gate to `pending`, and requires a fresh candidate and fresh comparison. Gates and integration checks are driven against `candidateRevision`, not the pre-merge branch tip. This is the contract the rest of the spec is a consequence of, so it ships with its invalidation predicate as an explicit, separately testable rule.

  ```ts
  type MergeAuthorization = {
    unit: RepositoryExecutionUnitId; pbi: PbiId;
    targetRevision: string; candidateRevision: string;
    snapshot: SnapshotId; gateDecision: string;
    providerEvidence?: ProviderObservation; authorizedAt: string;
  };
  ```
- **Acceptance criteria**:
  - Against a real temporary Git repository, preparation produces a merge commit whose parents are the PBI branch tip and the target revision; the recorded `candidateRevision` equals that commit, and every micro-commit and save point revision remains reachable from it.
  - The injected check adapters observe the candidate revision as their subject; a test asserts they are never invoked against the pre-merge branch tip.
  - Enabling history consolidation yields a different `candidateRevision` and an authorization that was valid before consolidation is invalid after.
  - Advancing the target after authorization invalidates it and the gate record transitions to `pending`; a commit on the PBI branch after authorization does the same.
  - The invalidation predicate is exercised directly with a table of (target moved, candidate moved, snapshot replaced) combinations and is total — no combination leaves authorization valid except all-unchanged.
  - A conflicting merge during preparation yields a typed `candidate_conflicted` outcome and records no authorization.
- **Blocked by**: 01; contract `gate decision record identity and the pending transition` (`entropy-gate`); contract `PBI branch and worktree lifecycle, micro-commits and save points` (`pbi-execution-loop`); contract `check execution on a named revision` (`verification-adapters`).
- **Parallelizable with**: 05

---

- **03 — Serialized target update, the Mutation Approval Boundary, and local-merge Operation Reconciliation**
- **What to build**: The local-merge delivery path end to end. Integration acquires the unit-scoped merge lease, re-verifies the target revision inside the serialized section, and only then updates the target — a target that moved is rejected rather than integrated on stale approval. `merge.confirmLocal` is operator-only, carries unit, target revision, candidate revision and snapshot identity, and must immediately precede the mutation; a green gate, a prior plan approval, and a successful Pull Request preparation each fail to substitute for it. The mutation persists its operation intent before the request, and a lost or uncertain response — including across a process restart — leaves the operation `unknown`, which blocks; resolution consults authoritative Git state for that specific operation, records a confirmed completion without repeating it, and permits a retry only on a confirmed non-occurrence.
- **Acceptance criteria**:
  - Two in-process integrations against one unit serialize; the loser is rejected `lock_unavailable` or revalidates, and the target advances exactly once in real Git.
  - A target moved between authorization and the serialized section is rejected with a typed code and the target commit is unchanged.
  - Local merge without a preceding `merge.confirmLocal` is rejected; three separate tests show a passing gate, a plan approval, and a successful Pull Request preparation each failing to authorize it.
  - A confirmation naming a stale target revision, candidate revision, or snapshot is rejected; a confirmation from the MCP channel is rejected `operator_channel_required`.
  - A merge whose response is lost leaves an `unknown` operation that blocks; reconciliation against real Git state to "completed" records the outcome with no second merge commit, and to "not performed" permits exactly one retry that still requires valid authorization.
  - A test asserts no branch other than the configured integration target is written — no promotion between long-lived branches, no hotfix automation.
- **Blocked by**: 02; contract `repository-execution-unit merge lease` (`execution-core`); contract `operation intent record, receipt, and unknown-outcome blocking` (`execution-core`); contract `operator channel assertion and operator_channel_required rejection` (`execution-core`).
- **Parallelizable with**: 04, 05, 06

---

- **04 — Conflict resolution within candidate preparation**
- **What to build**: When candidate preparation conflicts, the merger role may attempt resolution within the approved plan and governance rules, dispatched through the role envelope contract. Each attempt consumes one unit of the PBI's Correction Budget at dispatch. Any resolution produces a new candidate revision, which by slice 02's rule invalidates prior validation and requires all applicable gates and integration checks to rerun — removing conflict markers establishes nothing, and no classification of a conflict as mechanical grants an exemption path. A resolution that would require deciding behavior or changing approved contracts, criteria, dependencies or scope pauses and raises a Plan Amendment proposal instead of resolving.
- **Acceptance criteria**:
  - A conflicted preparation dispatches the merger role once and consumes exactly one correction attempt at dispatch, not at revalidation; an interrupted attempt stays consumed.
  - A successful resolution yields a new `candidateRevision` and the applicable gates are re-invoked against it; a test asserts no code path marks a resolution as validated without a rerun.
  - A resolution result that clears markers but leaves criteria unmet does not produce authorization.
  - A merger result flagged as requiring a behavioral decision produces a Plan Amendment proposal and leaves the PBI paused with its work preserved.
  - Exhausting the Correction Budget during conflict resolution leaves the gate failed and stops automatic resolution; the budget is not reset by anything in this path.
- **Blocked by**: 02; contract `merger role task and result envelope` (`gtp-protocol`); contract `Correction Budget accounting consumed at correction dispatch` (`execution-core`); contract `Plan Amendment proposal` (`slicing-and-approval`).
- **Parallelizable with**: 03, 05, 06

---

- **05 — Provider Identity, the provider interface, and the scripted provider fake**
- **What to build**: The GitHub provider interface — identity and access inspection, protection observation, Pull Request creation, update, observation and merge — as the single seam all provider behavior sits behind, plus a scriptable fake implementing it that can return protection variants, check and review states, mergeability, lost responses and externally changed state. Authentication uses what the environment already has: an authenticated `gh` installation or a token referenced by an approved environment variable for API operations, and existing SSH or HTTPS credentials for Git transport — these are distinct, and transport access proves nothing about API authorization. The resolved `ProviderIdentity` (login, mechanism, variable *name* only, observed scopes, repository access) is shown and approved before the first mutating provider operation. No credential value is ever written to configuration, the database, envelopes, projections, or repository artifacts.
- **Acceptance criteria**:
  - The first mutating provider operation is rejected until the identity has been approved; the approval records the observed scopes and repository access.
  - A unit with working SSH transport but no API authorization is rejected with a typed code on an API operation, and the rejection names API authorization rather than transport.
  - Missing, ambiguous, expired, and insufficient credentials each produce a distinct typed rejection and zero retry attempts.
  - A test scans the configuration store, the SQLite database, emitted envelopes and every projection for the fake's token value and finds no occurrence; the environment-variable name is present, the value is not.
  - The provider fake implements the full interface and can script a lost response and an externally changed remote state.
  - A conformance suite against real GitHub.com and GitHub Enterprise exists, records its rows in the support matrix, and skips with an explicit stated reason when credentials are absent.
- **Blocked by**: 01; contract `redaction sink enforcement interface` (`data-handling`).
- **Parallelizable with**: 02, 03, 04

---

- **06 — Provider Protection Authority and divergence blocking**
- **What to build**: The target branch's actual protection rules, required checks and required approvals are observed through the provider interface and treated as authoritative. Observation happens at readiness and again immediately before any mutation, and the result is compared against the local Git Workflow Policy captured in the snapshot. A missing, weaker, or otherwise divergent protection blocks until the operator adjusts either the policy or the provider configuration, after which affected validations rerun. Local configuration can never compensate for weaker provider protection, Gantry never bypasses a provider rule, and there is no fallback to local merge when the Pull Request path is blocked.
- **Acceptance criteria**:
  - Observed protection requiring fewer approvals or fewer checks than the local policy blocks with a typed divergence rejection naming the specific divergent fields.
  - Adjusting the policy to match observed protection reruns the affected validations rather than silently accepting prior evidence.
  - Protection that changes between the readiness observation and the pre-mutation observation blocks until reconciled, and the mutation does not occur.
  - With the Pull Request path blocked for any reason, no operation in the spec performs a local merge; a test enumerates the blocked reasons and asserts the target commit is unchanged in every one.
  - The observed protection record is produced in a shape readiness can report without re-observing.
- **Blocked by**: 05; contract `Governance Precedence resolution for conflicting rule sources` (`config-and-snapshot`).
- **Parallelizable with**: 02, 03, 04

---

- **07 — Pull Request preparation, Pull Request Observation, and the local-plus-provider conjunction**
- **What to build**: Pull Request creation and update under plan approval (which authorizes this class of mutation and only this class), then authenticated polling with a configurable and recorded interval, backoff and observation budget. Each observation is reconciled against the Pull Request identity: a `headRevision` no longer equal to the candidate means the candidate changed and invalidates authorization, a `baseRevision` no longer equal to the target means the target advanced and does the same, and changed protection reruns slice 06's comparison. Merge requires both the applicable local gates and the provider's required checks to pass for the relevant revisions — neither substitutes for the other and a conflict between them blocks. Provider mutations persist intent before the request and resolve an `unknown` outcome against authoritative provider state, never by speculative repetition. Webhooks and hosted callbacks are deferred; silence is never success.
- **Acceptance criteria**:
  - Plan approval alone authorizes Pull Request creation and update, and a test confirms it does not authorize a local merge.
  - An observation whose `headRevision` differs from the candidate invalidates authorization; one whose `baseRevision` differs from the target does the same; both return the gate to `pending`.
  - A `pending` required check, a missing check, a poll timeout, and an unavailable provider each fail to authorize the merge, in four separate assertions.
  - Reaching the observation budget leaves the execution waiting for resumption — not failed, not approved — and the interval, backoff and budget used are readable from the recorded observations.
  - Passing local gates with a failing provider check does not merge; the reverse does not merge; a direct conflict between the two blocks with a typed code.
  - A Pull Request creation or merge whose response is lost produces an `unknown` operation that blocks, and reconciliation against scripted provider state records a confirmed completion without creating a duplicate Pull Request or a second merge.
- **Blocked by**: 02, 05; contract `operation intent record, receipt, and unknown-outcome blocking` (`execution-core`).
- **Parallelizable with**: 03, 04, 06

---

- **08 — Requested changes, external integration, and Pull Requests closed without merge**
- **What to build**: An observed formal review requesting changes returns the PBI to correction eligibility within its *remaining* allowance, after being reconciled against current Pull Request state so a review against a superseded head revision is not replayed as a new request. Review text is untrusted feedback evaluated against the approved plan and governance, never instructions to execute; a request that would change behavior, contracts, criteria, dependencies or scope requires an operator-approved Plan Amendment. Separately, a Pull Request merged outside Gantry is reconciled: the actually integrated changes and resulting target revision are observed and recorded as an external integration rather than a Gantry-authorized merge, and dependents are released only after the applicable PBI criteria and Dependency Readiness are verified against the integrated content — a merged flag alone establishes nothing. A Pull Request closed without merge pauses the PBI, preserves its work and evidence, and requires an explicit decision.
- **Acceptance criteria**:
  - A `changes_requested` review returns the PBI to correction with the budget decremented per attempt and never reset; a test asserts the remaining allowance before and after.
  - A review whose recorded revision is not the current head is not replayed and produces no correction dispatch.
  - A review whose text requests a behavior change produces a Plan Amendment requirement and dispatches no implementation work.
  - Candidate changes originating from a review invalidate prior evidence and rerun both the local gates and the provider checks before any merge.
  - An externally merged Pull Request is recorded with an outcome kind distinguishable from a Gantry-authorized merge; dependents are released only after criteria and Dependency Readiness verify against the integrated target, and a scripted merge whose integrated content fails the criteria releases nothing.
  - A Pull Request closed without merge leaves the PBI paused with its worktree and evidence intact, and no reopen or replacement happens without an explicit operation.
- **Blocked by**: 07; contract `Dependency Readiness definition and the dependents-release signal` (`slicing-and-approval`); contract `Plan Amendment proposal` (`slicing-and-approval`); contract `PBI Execution Ownership and capacity reacquisition` (`execution-core`).
- **Parallelizable with**: 03, 04, 06

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of my slices needs it |
|---|---|---|
| Shared operation core `invoke`, operation catalog registration, typed rejection codes | `execution-core` | 01 (all downstream) |
| Operation intent record, receipt, and unknown-outcome blocking | `execution-core` | 03, 07 |
| Repository-execution-unit merge lease | `execution-core` | 03 |
| Operator channel assertion and `operator_channel_required` rejection | `execution-core` | 03 |
| Correction Budget accounting (consumed at correction dispatch) | `execution-core` | 04, 08 |
| PBI Execution Ownership and capacity reacquisition | `execution-core` | 08 |
| Execution Rule Snapshot capture and identity; config schema validation | `config-and-snapshot` | 01, 02 |
| Governance Precedence resolution for conflicting rule sources | `config-and-snapshot` | 06 |
| Merger role task and result envelope | `gtp-protocol` | 04 |
| Redaction sink enforcement interface | `data-handling` | 05 (all provider/Git output) |
| Readiness item shape and `needs_decision` classification | `repository-readiness` | 01 |
| Plan Amendment proposal | `slicing-and-approval` | 04, 08 |
| Dependency Readiness definition and the dependents-release signal | `slicing-and-approval` | 08 |
| PBI branch and worktree lifecycle, micro-commits, save points | `pbi-execution-loop` | 02 |
| Check execution on a named revision | `verification-adapters` | 02 |
| Gate decision record identity and the `pending` transition | `entropy-gate` | 02, 04, 07 |
| Support matrix as data (shared shape) | `machine-setup` / `harness-adapters` | 05 |

### Contracts this spec PUBLISHES for other specs

| Contract name | My slice that defines it | Which specs wait on it |
|---|---|---|
| **Merge Authorization binding and its invalidation rule** | 02 | 13 (`entropy-gate` — the `pending` return), 11 (`pbi-execution-loop`), 15 (`baseline-transitions`), 17 (`dashboard`) |
| Git Workflow Policy schema and workflow preset catalog | 01 | 02 (`config-and-snapshot` snapshot fields), 06 (`repository-readiness` collection), 11 (branch naming, starting branch) |
| `integration.*` operation catalog and typed rejection codes | 01 | 16 (`mcp-server` catalog derivation), 17 (`dashboard`) |
| Merge Candidate preparation outcome and `candidateRevision` | 02 | 12/13 (evidence attribution to a revision), 15, 18 (`compound-learning`) |
| Mutation Approval Boundary (`merge.confirmLocal` shape) | 03 | 17 (`dashboard` confirmation surface), 16 (rejected as operator-only) |
| Provider interface and Provider Identity record | 05 | 06 (`repository-readiness` provider items), 17 (identity display), 19 (conformance suite rows) |
| Provider conformance rows in the support matrix | 05 | 19 (`release-engineering`), 10 (`harness-adapters` — shared support-matrix shape) |
| Provider Protection Authority observation record | 06 | 06 (`repository-readiness`), 17 |
| Pull Request Observation record and observation budget settings | 07 | 17 (`dashboard` review state), 02 (`config-and-snapshot` limit values) |
| External integration outcome record | 08 | 18 (`compound-learning` post-merge trigger), 11, 09 (dependents release) |

### Risks / judgement calls

**The authorization binding is in slice 02, not slice 01.** The handoff says the binding and its invalidation rule govern every other decision here and should be settled first. I put it in 02 rather than 01 because a slice that defines only the binding type would be a horizontal type slice with nothing to demo. Slice 02 delivers it as a working, testable predicate alongside the candidate preparation that produces the revisions it binds to. If the operator wants it settled even earlier, the cheapest fix is to require slice 02 to open with the invalidation predicate and its table test before the Git work — not to split it out.

**Two mutation-reconciliation implementations.** Slice 03 writes the Git-side resolver (consult real Git state) and slice 07 writes the provider-side resolver (consult provider state), and I deliberately did not block 07 on 03 so the local and provider tracks stay parallel. The cost is that two agents will design against spec 01's reconciliation contract independently and may diverge in shape. I judged the parallelism worth it because the authoritative sources genuinely differ, but if spec 01's contract turns out to be thin, these two will need a reconciling pass.

**Slice 07 is the biggest.** Pull Request preparation, polling with budget and backoff, observation reconciliation, the local-and-provider conjunction, *and* provider mutation reconciliation is a lot for one PBI. I was tempted to split observation reconciliation from preparation-and-merge, but the invalidation checks are the whole point of observing, and a preparation slice with no observation cannot demonstrate that a Pull Request ever merges. If it needs splitting during execution, the clean cut is preparation + create/update mutations in one, and polling + conjunction + merge in the other, with the second blocked on the first.

**Conflict resolution (04) could fold into 02.** It is arguably one behavior — preparing a candidate, including when that is hard. I kept it separate because it pulls in the merger role envelope, the Correction Budget, and Plan Amendment, which are three cross-spec contracts that 02 otherwise does not touch, and because a conflicted preparation returning a typed outcome is a clean handoff point between them.

**Slice 08 bundles two loosely related behaviors.** Requested changes and external resolution share only "the Pull Request changed state without us doing it" and a dependency on observation. They could be two slices. I bundled them to stay inside eight and because both are pure consumers of slice 07's observation record, so the shared context is real.

**Dependency on entropy-gate is heavier than the map suggests.** The map blocks 14 on 13 wholesale, but only slices 02, 04 and 07 actually need the gate decision. Slices 01, 05 and 06 can start before spec 13 exists at all, which is the main source of parallelism available here — worth confirming that reading is acceptable before agents are assigned.
