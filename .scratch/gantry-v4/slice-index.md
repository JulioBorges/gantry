# Gantry v4 — slice index and contract ownership

Type: index
Status: active
Created: 2026-09-12
Map: [`map.md`](./map.md) · Handoff: [`handoff.md`](./handoff.md)

This is the authority for resolving a cross-spec dependency to a concrete issue reference.
Issues live at `.scratch/<slug>/issues/NN-<slug>.md`. A cross-spec blocker is written as
`` `<spec-slug>#NN` `` — for example `` `data-handling#01` ``.

Total: **132 issues across 19 specs**.

## Operator decisions already settled

These were decided on 2026-09-12 and must not be re-litigated in an issue.

| Decision | Value |
|---|---|
| SQLite driver | **better-sqlite3**, keeping `engines: { node: ">=20" }`. Must be proven for WAL, `BEGIN IMMEDIATE`, and cross-process locking, with prebuilt binaries for Linux, macOS and Windows. |
| Repository bootstrap owner | `release-engineering#01`. No other spec bootstraps the repository. |
| Test seam boundary | `release-engineering#01` proves the dependencies work (open a WAL database, parse with tree-sitter, create a temporary Git repository, spawn a second OS process against the same database file). `execution-core#01` builds the real fixture builders on top. |
| Wave 0 opening order | `release-engineering#01` → `data-handling#01` → `execution-core#01`. |
| Granularity | 132 slices: the 131 as drafted, plus `git-integration#09` added on 2026-09-12 to cover the provider conformance suite the spec requires at line 333 and the drafted breakdown omitted. Do not merge or split without operator approval. |
| Issue language | English, per §12.4 and the map's conventions. |

Still open, to be recorded in `release-engineering#01` as explicit choices rather than assumptions:
package manager for this repository, compiler versus bundler, formatter, changelog convention,
whether macOS and Windows jobs are required checks, and whether the first publish is `4.0.0`.

## Resolved contract ownership

Each row was needed by one spec and owned by none. The owner column is now binding.

| Contract | Owner | Consumers |
|---|---|---|
| Gate state `pending_review` | `execution-core#05` | `entropy-gate#05` |
| PBI state `awaiting_review` | `execution-core#03` | `pbi-execution-loop#06` |
| Operation `pbi.answer` (operator channel; returns `awaiting_operator` → `queued` carrying the answer as continuity input) | `execution-core#03` | `pbi-execution-loop#05` |
| Operation input schemas published as runtime data, keyed by operation name | `execution-core#01` | `mcp-server#02` |
| Collected mandatory-test identities including skip status, on the `mandatory_test` adapter report | `verification-adapters#01` | `entropy-gate#04` |
| Configuration section `gates.*` — blocking thresholds, absolute-rule flags, `gates.adversarial.mode` | `config-and-snapshot#01` | `entropy-gate#02`, `entropy-gate#05` |
| PBI file-count threshold under context policy | `config-and-snapshot#01` | `slicing-and-approval#02` |
| Baseline operations `baseline.declare` / `baseline.propose` / `baseline.adopt` / `baseline.abandon`, registered in the shared catalog | `baseline-transitions#01` | `execution-core` catalog |
| CLI surface `gantry config` | `config-and-snapshot#01`, `#03`, `#07` | — |
| CLI surface `gantry baseline …` | `baseline-transitions#06` | — |
| Production wiring of the merge candidate and current target revision pair | `git-integration#02` | `entropy-gate#06`, `verification-adapters#08` |
| Secret scanner rule source reference — scanner identity plus resolved rule-configuration location, distinct from the `ApprovedCommandProposal` that runs it | `repository-readiness#03` | `data-handling#02` (detector source 3) |
| Context usage read operation registered in the shared catalog, returning a `ContextUsage` value including the `unknown` variant — never a bare number | `pbi-execution-loop#03` | `mcp-server#04` |

## Resolved ownership collisions

- **Repository bootstrap** — `release-engineering#01` owns it. `execution-core#01` consumes it and must not
  re-declare the toolchain.
- **Merge Authorization** — `execution-core#07` owns the binding record and the invalidation rule.
  `git-integration#02` owns Merge Candidate preparation and the Git/provider mechanics, and **consumes**
  the invalidation predicate rather than redefining it.
- **Worktree activity marker** — `harness-adapters#01` defines the `ReconciliationResult.worktreeActivity`
  variant set and ships an injectable Git-state observer. `pbi-execution-loop#01` supersedes it with the
  lease-aware marker without reopening the interface.
- **Cross-mode boundary (demo)** — `execution-core#01` owns the immutable `mode` property on the
  Repository Execution Unit and the boundary predicate at the operation boundary, with its rejection code.
  `demo-mode#01` consumes it and owns only the projection field and the demo-specific tests.
- **`git-integration` dependency on `entropy-gate`** — the map blocks 14 on 13 wholesale; only
  `git-integration#02`, `#04` and `#07` actually need the gate decision. `#01`, `#05` and `#06` may start
  before spec 13 exists.
- **`machine-setup#02`** (harness compatibility matrix) has no blockers and five specs read it. It is
  pulled forward into wave 0, delivered as validated data plus a detection function, with its
  operation-core surfacing deferred.

## Slice index

### 01 `execution-core`
| # | Title |
|---|---|
| 01 | Operation core seam and Repository Execution Unit registration |
| 02 | Execution lifecycle, operator channel provenance, and version-bound Planning Approval |
| 03 | PBI Execution Ownership, dispatch, and capacity accounting |
| 04 | Result Submission identity, receipts, and stale assignment rejection |
| 05 | Gate state, Correction Budget accounting, and operator grants |
| 06 | Operation intent, Operation Reconciliation, and Infrastructure Retry |
| 07 | Merge Authorization binding and serialized integration |
| 08 | Execution Cancellation, Resumption, Cleanup Authorization, and runtime compatibility |

### 02 `config-and-snapshot`
| # | Title |
|---|---|
| 01 | Configuration layering and the effective document |
| 02 | Whole-document validation and secret rejection |
| 03 | Validated writes with per-layer authorization |
| 04 | Execution Rule Snapshot capture and identity |
| 05 | Snapshot migration and approval invalidation |
| 06 | Governance Precedence resolution and conflict blocking |
| 07 | Role routing resolution and dead configuration |

### 03 `gtp-protocol`
| # | Title |
|---|---|
| 01 | Envelope boundary, extensions, and Protocol Failure |
| 02 | Builder task and result contract |
| 03 | Non-mutating role contracts |
| 04 | Status precedence, handoff continuity, and context usage |
| 05 | Criterion accounting and Implementation Completion |
| 06 | Result submission identity, idempotency, and corrections |
| 07 | Allowed scope and governance-path protection |

### 04 `data-handling`
| # | Title |
|---|---|
| 01 | Redaction sink boundary and normalized content hashing |
| 02 | Detector sources and ruleset versioning |
| 03 | Withheld output and blocked-for-review |
| 04 | Reference-first retention and replayable references |
| 05 | Detailed retention opt-in and evidence invalidation |
| 06 | Egress matrix resolution and dispatch enforcement |
| 07 | Egress audit trail and driver-change reauthorization |

### 05 `machine-setup`
| # | Title |
|---|---|
| 01 | Machine factory provisioning |
| 02 | Harness compatibility matrix and presence detection |
| 03 | Skill installation into harness conventions |
| 04 | Installation lifecycle: idempotent re-run, divergence reconciliation, and uninstall |
| 05 | Integration Capability declaration validation |
| 06 | Routing presets |
| 07 | The conversational setup interview |

### 06 `repository-readiness`
| # | Title |
|---|---|
| 01 | Artifact Location Mapping and the readiness report skeleton |
| 02 | Instruction merging and constitution ensuring |
| 03 | Verification command detection and approval proposals |
| 04 | Verification Command Approval, validation run and preexisting baseline |
| 05 | Preparation proposal, authorization and scoped application |
| 06 | Repository policy readiness: dependency, License Policy and egress declarations |
| 07 | Dirty Working Tree detection and treatment |

### 07 `demo-mode`
| # | Title |
|---|---|
| 01 | Demo mode marker and the cross-mode boundary |
| 02 | Demo fixture lifecycle: `gantry init --demo` and `demo.reset` |
| 03 | Stub harness drivers and scripted result envelopes |
| 04 | Stub check adapters and scripted Comparison Evidence |
| 05 | Scripted walkthrough: clean delivery, Protocol Failure, and the dependency wait |
| 06 | Scripted walkthrough: Correction Attempt and the entropy regression block |
| 07 | Demo measurement and the pipeline regression check |

### 08 `spec-validation`
| # | Title |
|---|---|
| 01 | `gantry lint-spec` tracer with the normalized spec model and content-presence rules |
| 02 | Criterion identity and Given-When-Then scenario rules |
| 03 | Declared contract validation per format |
| 04 | Spec format detection, mapping override, and canonical location |
| 05 | Requirement Review and technical readiness |
| 06 | Spec Adaptation by proposed complements |
| 07 | Structured spec authoring |

### 09 `slicing-and-approval`
| # | Title |
|---|---|
| 01 | Plan proposal and plan version identity |
| 02 | PBI lint rules and breakdown coverage |
| 03 | Context estimation and the upper-bound budget |
| 04 | Dependency graph validation at planning |
| 05 | Dependency Readiness evaluated against Git |
| 06 | Planning Approval and dispatch gating |
| 07 | Change classification and Plan Amendment |

### 10 `harness-adapters`
| # | Title |
|---|---|
| 01 | Adapter interface, driver resolution, and dispatch provenance |
| 02 | Integration Capability declaration and conformance probes |
| 03 | Native subagent adapter |
| 04 | Detached CLI adapter, result path, and process identity |
| 05 | Gateway adapter and the file-mutating role restriction |
| 06 | Driver unavailability, Infrastructure Retry, and explicit replacement |
| 07 | Cross-harness conformance suite and the support matrix |

### 11 `pbi-execution-loop`
| # | Title |
|---|---|
| 01 | PBI Worktree lifecycle and worktree lease |
| 02 | Eligibility conjunction, joint capacity accounting, and typed dispatch rejections |
| 03 | Context Watermark observation per declared granularity |
| 04 | The handoff sequence and the State Compaction memo |
| 05 | Result handling, micro-commits, and correction dispatch |
| 06 | Slot release during review, reacquisition, and resumption |
| 07 | Check Resource serialization in scheduling |

### 12 `verification-adapters`
| # | Title |
|---|---|
| 01 | Check adapter seam and normalized finding shape |
| 02 | Enclosing-symbol derivation and the fallback ladder |
| 03 | Evidence validity: completeness, operator classification, and report reuse |
| 04 | Check stability and adapter failure classification |
| 05 | Check resources: scoped declaration, allocation, and lease reclamation |
| 06 | TypeScript and JavaScript adapter set |
| 07 | Python adapter set |
| 08 | Opt-in mutation adapter |

### 13 `entropy-gate`
| # | Title |
|---|---|
| 01 | Gate decision record and differential classification |
| 02 | Absolute mandatory rules and fail-closed evidence handling |
| 03 | Evidence consolidation: reuse, target currency, and invalidation |
| 04 | Verification integrity comparison, assertion-shape warning, and operator approval |
| 05 | Adversarial review: ordering, add-only, and failure behavior |
| 06 | Correction loop: subject derivation, attempt accounting, and exhaustion |

### 14 `git-integration`
| # | Title |
|---|---|
| 01 | Git Workflow Policy resolution and the integration operation surface |
| 02 | Merge Candidate preparation and the Merge Authorization binding |
| 03 | Serialized target update, the Mutation Approval Boundary, and local-merge Operation Reconciliation |
| 04 | Conflict resolution within candidate preparation |
| 05 | Provider Identity, the provider interface, and the scripted provider fake |
| 06 | Provider Protection Authority and divergence blocking |
| 07 | Pull Request preparation, Pull Request Observation, and the local-plus-provider conjunction |
| 08 | Requested changes, external integration, and Pull Requests closed without merge |
| 09 | Provider conformance suite and support matrix rows |

### 15 `baseline-transitions`
| # | Title |
|---|---|
| 01 | Transition declaration and governance-path permission |
| 02 | Transition manifest: configurations, comparison mode, and coverage change |
| 03 | Finding change across configurations: rule mappings and the count fallback |
| 04 | Old-baseline evaluation of the introducing delivery |
| 05 | Adoption, refusal, and abandonment |
| 06 | Post-adoption effect, in-flight migration, and transport surface |

### 16 `mcp-server`
| # | Title |
|---|---|
| 01 | MCP transport adapter bootstrap |
| 02 | Derived tool catalog and drift guard |
| 03 | Result Submission over the MCP channel |
| 04 | Honest host identification and capability-gated tools |
| 05 | Harness conformance for the MCP surface |

### 17 `dashboard`
| # | Title |
|---|---|
| 01 | Loopback transport shell and read-only monitor |
| 02 | Dashboard Capability Token and the mutation boundary |
| 03 | Honest PBI projection and Monitor swimlanes |
| 04 | Live transition feed over SSE |
| 05 | Operator decision surface |
| 06 | Settings screen |
| 07 | Token lifecycle, non-persistence proof, and manual entry fallback |

### 18 `compound-learning`
| # | Title |
|---|---|
| 01 | Learning candidate from Entropy Gate findings, approved into the marked section |
| 02 | Candidates from Correction Attempts, Protocol Failures, and state transitions |
| 03 | Candidates from handoff patterns and integrity findings |
| 04 | Rejection, observation fingerprint suppression, and per-source backoff |
| 05 | Applied-section stewardship: grouping, removal, size limit, and consolidation |
| 06 | Target routing by Governance Precedence and conversion to a Governance Baseline Transition |

### 19 `release-engineering`
| # | Title |
|---|---|
| 01 | Repository bootstrap and the first required checks |
| 02 | Package allowlist, tarball assertions, and installed-binary smoke test |
| 03 | Publish on tag with provenance |
| 04 | Local release flow: bump, tag, and dry run |
| 05 | Platform matrix and per-row Windows status |
| 06 | Conformance jobs and the published support matrix |
| 07 | Progressive documentation, quickstart verification, and the demo as a required check |
