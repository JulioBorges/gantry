# Roadmap

Delivery tracking for Gantry v4. One checkbox per implementation issue.

**Each issue's `Status:` line is authoritative for that issue.** This roadmap is the rolled-up view of
them, kept in step by hand. When the two disagree, the issue wins and this file is stale — fix the file.

- Specs: `.scratch/<slug>/spec.md`
- Issues: `.scratch/<slug>/issues/NN-<slug>.md`
- Cross-spec references and settled decisions: [`.scratch/gantry-v4/slice-index.md`](.scratch/gantry-v4/slice-index.md)

## How to update this file

When an issue is completed:

1. Set `Status: done` in the issue file itself.
2. Tick its checkbox here and bump the `done/total` count on its spec heading.
3. Update the **Progress** table below.

Do not tick an item here without setting `Status: done` in the issue, and do not tick an item whose
acceptance criteria are not all met. A partially delivered slice stays unticked — the whole point of a
vertical slice is that it is demonstrable on its own, so "mostly done" is not a state this file records.

## Progress

| | Count |
|---|---|
| Issues completed | **0 / 132** |
| Specs completed | **0 / 19** |
| Acceptance criteria | 754 |

## Where work can start

Only two issues have no blockers:

- **`release-engineering#01`** — the repository bootstrap. It is the blocking root of the whole project:
  there is no `package.json`, no `src/`, and no CI, and all 18 other specs inherit its toolchain choices.
- **`machine-setup#02`** — the harness compatibility matrix, delivered as validated data plus a detection
  function. Pulled forward out of wave 1 because five specs read it and it depends on nothing.

After those, the wave 0 order is `data-handling#01` (the redaction sink interface every writer consumes)
and then `execution-core#01` (the shared operation core seam).

## Open decisions

These are recorded inside their issues and still need an operator answer before those issues are finished:

- Package manager, compiler versus bundler, formatter, and changelog convention — `release-engineering#01`
- Whether the first publish is `4.0.0` — `release-engineering#03`
- Whether macOS and Windows jobs are required checks — `release-engineering#05`
- Whether a four-row conformance pass is a release gate — `release-engineering#06` / `harness-adapters#07`
- Whether the SSE feed endpoint is readable without a capability token — `dashboard#04`
- Where MCP host identification surfaces: `initialize` field or read tool — `mcp-server#04`

## Issues by wave

Waves come from [`.scratch/gantry-v4/map.md`](.scratch/gantry-v4/map.md). They describe how the specs
relate, not a strict execution order — the real order is the blocker graph below, and several issues in
later waves unblock earlier than their wave suggests.

<!-- BEGIN GENERATED: issue checklist -->

### Wave 0 — Foundation and bootstrap

#### 19 `release-engineering` — 0/7

- [ ] **`release-engineering#01`** — Repository bootstrap and the first required checks _(no blockers — can start immediately)_
- [ ] **`release-engineering#02`** — Package allowlist, tarball assertions, and installed-binary smoke test
  <br>↳ blocked by: release-engineering#01
- [ ] **`release-engineering#03`** — Publish on tag with provenance
  <br>↳ blocked by: release-engineering#02
- [ ] **`release-engineering#04`** — Local release flow: bump, tag, and dry run
  <br>↳ blocked by: release-engineering#02
- [ ] **`release-engineering#05`** — Platform matrix and per-row Windows status
  <br>↳ blocked by: release-engineering#01
- [ ] **`release-engineering#06`** — Conformance jobs and the published support matrix
  <br>↳ blocked by: release-engineering#01
- [ ] **`release-engineering#07`** — Progressive documentation, quickstart verification, and the demo as a required check
  <br>↳ blocked by: release-engineering#02

#### 04 `data-handling` — 0/7

- [ ] **`data-handling#01`** — Redaction sink boundary and normalized content hashing
  <br>↳ blocked by: release-engineering#01
- [ ] **`data-handling#02`** — Detector sources and ruleset versioning
  <br>↳ blocked by: config-and-snapshot#01, data-handling#01, repository-readiness#03
- [ ] **`data-handling#03`** — Withheld output and blocked-for-review
  <br>↳ blocked by: config-and-snapshot#01, data-handling#01, execution-core#01, execution-core#05
- [ ] **`data-handling#04`** — Reference-first retention and replayable references
  <br>↳ blocked by: data-handling#01, execution-core#01, execution-core#06, execution-core#08, pbi-execution-loop#04
- [ ] **`data-handling#05`** — Detailed retention opt-in and evidence invalidation
  <br>↳ blocked by: config-and-snapshot#01, config-and-snapshot#04, config-and-snapshot#05, data-handling#04
- [ ] **`data-handling#06`** — Egress matrix resolution and dispatch enforcement
  <br>↳ blocked by: config-and-snapshot#01, data-handling#01, gtp-protocol#01, harness-adapters#01, repository-readiness#06
- [ ] **`data-handling#07`** — Egress audit trail and driver-change reauthorization
  <br>↳ blocked by: config-and-snapshot#04, data-handling#06, harness-adapters#06

#### 01 `execution-core` — 0/8

- [ ] **`execution-core#01`** — Operation core seam and Repository Execution Unit registration
  <br>↳ blocked by: data-handling#01, release-engineering#01
- [ ] **`execution-core#02`** — Execution lifecycle, operator channel provenance, and version-bound Planning Approval
  <br>↳ blocked by: config-and-snapshot#04, dashboard#02, data-handling#01, execution-core#01, slicing-and-approval#01
- [ ] **`execution-core#03`** — PBI Execution Ownership, dispatch, and capacity accounting
  <br>↳ blocked by: config-and-snapshot#01, execution-core#01, gtp-protocol#02, gtp-protocol#03
- [ ] **`execution-core#04`** — Result Submission identity, receipts, and stale assignment rejection
  <br>↳ blocked by: execution-core#03, gtp-protocol#01, gtp-protocol#02, gtp-protocol#04, gtp-protocol#05
- [ ] **`execution-core#05`** — Gate state, Correction Budget accounting, and operator grants
  <br>↳ blocked by: config-and-snapshot#01, execution-core#01, verification-adapters#01, verification-adapters#03
- [ ] **`execution-core#06`** — Operation intent, Operation Reconciliation, and Infrastructure Retry
  <br>↳ blocked by: config-and-snapshot#01, execution-core#01
- [ ] **`execution-core#07`** — Merge Authorization binding and serialized integration
  <br>↳ blocked by: execution-core#05, execution-core#06, git-integration#02, git-integration#06
- [ ] **`execution-core#08`** — Execution Cancellation, Resumption, Cleanup Authorization, and runtime compatibility
  <br>↳ blocked by: execution-core#02, execution-core#06

#### 02 `config-and-snapshot` — 0/7

- [ ] **`config-and-snapshot#01`** — Configuration layering and the effective document
  <br>↳ blocked by: execution-core#01
- [ ] **`config-and-snapshot#02`** — Whole-document validation and secret rejection
  <br>↳ blocked by: config-and-snapshot#01, data-handling#02
- [ ] **`config-and-snapshot#03`** — Validated writes with per-layer authorization
  <br>↳ blocked by: config-and-snapshot#02, data-handling#01
- [ ] **`config-and-snapshot#04`** — Execution Rule Snapshot capture and identity
  <br>↳ blocked by: config-and-snapshot#01, data-handling#01, execution-core#01, repository-readiness#01
- [ ] **`config-and-snapshot#05`** — Snapshot migration and approval invalidation
  <br>↳ blocked by: config-and-snapshot#04, execution-core#02, execution-core#05
- [ ] **`config-and-snapshot#06`** — Governance Precedence resolution and conflict blocking
  <br>↳ blocked by: config-and-snapshot#01, execution-core#07
- [ ] **`config-and-snapshot#07`** — Role routing resolution and dead configuration
  <br>↳ blocked by: config-and-snapshot#01, execution-core#03, machine-setup#02

#### 03 `gtp-protocol` — 0/7

- [ ] **`gtp-protocol#01`** — Envelope boundary, extensions, and Protocol Failure
  <br>↳ blocked by: config-and-snapshot#04, data-handling#01, execution-core#01, execution-core#03, execution-core#04, slicing-and-approval#01
- [ ] **`gtp-protocol#02`** — Builder task and result contract
  <br>↳ blocked by: config-and-snapshot#01, gtp-protocol#01, spec-validation#02
- [ ] **`gtp-protocol#03`** — Non-mutating role contracts
  <br>↳ blocked by: gtp-protocol#01, slicing-and-approval#01, slicing-and-approval#02, slicing-and-approval#03, spec-validation#02, verification-adapters#01
- [ ] **`gtp-protocol#04`** — Status precedence, handoff continuity, and context usage
  <br>↳ blocked by: gtp-protocol#01
- [ ] **`gtp-protocol#05`** — Criterion accounting and Implementation Completion
  <br>↳ blocked by: config-and-snapshot#01, gtp-protocol#02, gtp-protocol#04, spec-validation#02, verification-adapters#01
- [ ] **`gtp-protocol#06`** — Result submission identity, idempotency, and corrections
  <br>↳ blocked by: data-handling#01, execution-core#03, execution-core#04, gtp-protocol#01
- [ ] **`gtp-protocol#07`** — Allowed scope and governance-path protection
  <br>↳ blocked by: baseline-transitions#01, gtp-protocol#02, repository-readiness#01, verification-adapters#01

### Wave 1 — Entering a repository

#### 05 `machine-setup` — 0/7

- [ ] **`machine-setup#01`** — Machine factory provisioning
  <br>↳ blocked by: config-and-snapshot#01, data-handling#01, execution-core#01, execution-core#08
- [ ] **`machine-setup#02`** — Harness compatibility matrix and presence detection _(no blockers — can start immediately)_
- [ ] **`machine-setup#03`** — Skill installation into harness conventions
  <br>↳ blocked by: machine-setup#01, machine-setup#02
- [ ] **`machine-setup#04`** — Installation lifecycle: idempotent re-run, divergence reconciliation, and uninstall
  <br>↳ blocked by: machine-setup#01, machine-setup#03
- [ ] **`machine-setup#05`** — Integration Capability declaration validation
  <br>↳ blocked by: harness-adapters#02, machine-setup#01, machine-setup#02
- [ ] **`machine-setup#06`** — Routing presets
  <br>↳ blocked by: config-and-snapshot#01, machine-setup#01
- [ ] **`machine-setup#07`** — The conversational setup interview
  <br>↳ blocked by: execution-core#02, machine-setup#01, machine-setup#06

#### 06 `repository-readiness` — 0/7

- [ ] **`repository-readiness#01`** — Artifact Location Mapping and the readiness report skeleton
  <br>↳ blocked by: config-and-snapshot#01, config-and-snapshot#04, data-handling#01, execution-core#01, execution-core#02
- [ ] **`repository-readiness#02`** — Instruction merging and constitution ensuring
  <br>↳ blocked by: repository-readiness#01
- [ ] **`repository-readiness#03`** — Verification command detection and approval proposals
  <br>↳ blocked by: repository-readiness#01
- [ ] **`repository-readiness#04`** — Verification Command Approval, validation run and preexisting baseline
  <br>↳ blocked by: config-and-snapshot#04, config-and-snapshot#05, data-handling#01, execution-core#02, repository-readiness#03
- [ ] **`repository-readiness#05`** — Preparation proposal, authorization and scoped application
  <br>↳ blocked by: execution-core#02, repository-readiness#03
- [ ] **`repository-readiness#06`** — Repository policy readiness: dependency, License Policy and egress declarations
  <br>↳ blocked by: config-and-snapshot#01, data-handling#04, data-handling#06, entropy-gate#01, repository-readiness#01, repository-readiness#03
- [ ] **`repository-readiness#07`** — Dirty Working Tree detection and treatment
  <br>↳ blocked by: execution-core#02, repository-readiness#01

#### 07 `demo-mode` — 0/7

- [ ] **`demo-mode#01`** — Demo mode on the state projection and the cross-mode boundary tests
  <br>↳ blocked by: execution-core#01, execution-core#02
- [ ] **`demo-mode#02`** — Demo fixture lifecycle: `gantry init --demo` and `demo.reset`
  <br>↳ blocked by: config-and-snapshot#01, config-and-snapshot#04, data-handling#01, demo-mode#01, execution-core#01, execution-core#02, execution-core#08, machine-setup#01
- [ ] **`demo-mode#03`** — Stub harness drivers and scripted result envelopes
  <br>↳ blocked by: gtp-protocol#01, gtp-protocol#02, gtp-protocol#03, gtp-protocol#04, gtp-protocol#06, harness-adapters#01, harness-adapters#02
- [ ] **`demo-mode#04`** — Stub check adapters and scripted Comparison Evidence
  <br>↳ blocked by: verification-adapters#01, verification-adapters#03, verification-adapters#04, verification-adapters#05
- [ ] **`demo-mode#05`** — Scripted walkthrough: clean delivery, Protocol Failure, and the dependency wait
  <br>↳ blocked by: demo-mode#02, demo-mode#03, demo-mode#04, execution-core#02, git-integration#01, git-integration#03, gtp-protocol#01, gtp-protocol#05, pbi-execution-loop#01, pbi-execution-loop#02, pbi-execution-loop#05
- [ ] **`demo-mode#06`** — Scripted walkthrough: Correction Attempt and the entropy regression block
  <br>↳ blocked by: demo-mode#02, demo-mode#03, demo-mode#04, entropy-gate#01, entropy-gate#06, execution-core#05, git-integration#03, pbi-execution-loop#02, pbi-execution-loop#05, verification-adapters#01
- [ ] **`demo-mode#07`** — Demo measurement and the pipeline regression check
  <br>↳ blocked by: dashboard#04, demo-mode#05, demo-mode#06, release-engineering#01

### Wave 2 — Planning

#### 08 `spec-validation` — 0/7

- [ ] **`spec-validation#01`** — `gantry lint-spec` tracer with the normalized spec model and content-presence rules
  <br>↳ blocked by: data-handling#01, execution-core#01
- [ ] **`spec-validation#02`** — Criterion identity and Given-When-Then scenario rules
  <br>↳ blocked by: spec-validation#01
- [ ] **`spec-validation#03`** — Declared contract validation per format
  <br>↳ blocked by: spec-validation#01
- [ ] **`spec-validation#04`** — Spec format detection, mapping override, and canonical location
  <br>↳ blocked by: repository-readiness#01, spec-validation#01
- [ ] **`spec-validation#05`** — Requirement Review and technical readiness
  <br>↳ blocked by: config-and-snapshot#04, data-handling#01, execution-core#06, gtp-protocol#01, gtp-protocol#04, gtp-protocol#06, spec-validation#01
- [ ] **`spec-validation#06`** — Spec Adaptation by proposed complements
  <br>↳ blocked by: spec-validation#01, spec-validation#02
- [ ] **`spec-validation#07`** — Structured spec authoring
  <br>↳ blocked by: machine-setup#03, spec-validation#04

#### 09 `slicing-and-approval` — 0/7

- [ ] **`slicing-and-approval#01`** — Plan proposal and plan version identity
  <br>↳ blocked by: data-handling#01, execution-core#01, gtp-protocol#03, repository-readiness#01, spec-validation#01, spec-validation#02
- [ ] **`slicing-and-approval#02`** — PBI lint rules and breakdown coverage
  <br>↳ blocked by: config-and-snapshot#01, repository-readiness#04, slicing-and-approval#01
- [ ] **`slicing-and-approval#03`** — Context estimation and the upper-bound budget
  <br>↳ blocked by: config-and-snapshot#01, slicing-and-approval#01
- [ ] **`slicing-and-approval#04`** — Dependency graph validation at planning
  <br>↳ blocked by: slicing-and-approval#01
- [ ] **`slicing-and-approval#05`** — Dependency Readiness evaluated against Git
  <br>↳ blocked by: execution-core#03, git-integration#01, slicing-and-approval#01
- [ ] **`slicing-and-approval#06`** — Planning Approval and dispatch gating
  <br>↳ blocked by: config-and-snapshot#04, execution-core#02, mcp-server#02, repository-readiness#07, slicing-and-approval#01
- [ ] **`slicing-and-approval#07`** — Change classification and Plan Amendment
  <br>↳ blocked by: config-and-snapshot#05, entropy-gate#03, slicing-and-approval#06

### Wave 3 — Execution

#### 10 `harness-adapters` — 0/7

- [ ] **`harness-adapters#01`** — Adapter interface, driver resolution, and dispatch provenance
  <br>↳ blocked by: config-and-snapshot#04, config-and-snapshot#07, data-handling#01, execution-core#01, execution-core#03, gtp-protocol#01, gtp-protocol#02, gtp-protocol#04
- [ ] **`harness-adapters#02`** — Integration Capability declaration and conformance probes
  <br>↳ blocked by: harness-adapters#01, machine-setup#02, mcp-server#03
- [ ] **`harness-adapters#03`** — Native subagent adapter
  <br>↳ blocked by: gtp-protocol#01, harness-adapters#01, mcp-server#03
- [ ] **`harness-adapters#04`** — Detached CLI adapter, result path, and process identity
  <br>↳ blocked by: data-handling#01, gtp-protocol#01, gtp-protocol#04, harness-adapters#01
- [ ] **`harness-adapters#05`** — Gateway adapter and the file-mutating role restriction
  <br>↳ blocked by: config-and-snapshot#02, config-and-snapshot#07, data-handling#06, gtp-protocol#01, harness-adapters#01
- [ ] **`harness-adapters#06`** — Driver unavailability, Infrastructure Retry, and explicit replacement
  <br>↳ blocked by: config-and-snapshot#05, data-handling#07, execution-core#06, harness-adapters#01
- [ ] **`harness-adapters#07`** — Cross-harness conformance suite and the support matrix
  <br>↳ blocked by: gtp-protocol#06, harness-adapters#02, harness-adapters#03, harness-adapters#04, harness-adapters#05, machine-setup#02, mcp-server#03

#### 11 `pbi-execution-loop` — 0/7

- [ ] **`pbi-execution-loop#01`** — PBI Worktree lifecycle and worktree lease
  <br>↳ blocked by: execution-core#01, execution-core#03, execution-core#08, git-integration#01, harness-adapters#01, repository-readiness#07
- [ ] **`pbi-execution-loop#02`** — Eligibility conjunction, joint capacity accounting, and typed dispatch rejections
  <br>↳ blocked by: config-and-snapshot#01, execution-core#02, execution-core#03, pbi-execution-loop#01, slicing-and-approval#01, slicing-and-approval#05, slicing-and-approval#06
- [ ] **`pbi-execution-loop#03`** — Context Watermark observation per declared granularity
  <br>↳ blocked by: config-and-snapshot#01, config-and-snapshot#04, gtp-protocol#04, harness-adapters#01, harness-adapters#02, pbi-execution-loop#01
- [ ] **`pbi-execution-loop#04`** — The handoff sequence and the State Compaction memo
  <br>↳ blocked by: config-and-snapshot#04, data-handling#01, data-handling#04, execution-core#03, execution-core#04, gtp-protocol#01, gtp-protocol#04, gtp-protocol#05, harness-adapters#01, pbi-execution-loop#01, pbi-execution-loop#03, slicing-and-approval#03
- [ ] **`pbi-execution-loop#05`** — Result handling, micro-commits, and correction dispatch
  <br>↳ blocked by: config-and-snapshot#01, entropy-gate#06, execution-core#03, execution-core#05, gtp-protocol#04, gtp-protocol#05, gtp-protocol#06, pbi-execution-loop#01, verification-adapters#01
- [ ] **`pbi-execution-loop#06`** — Slot release during review, reacquisition, and resumption
  <br>↳ blocked by: execution-core#03, execution-core#06, execution-core#08, pbi-execution-loop#01, pbi-execution-loop#02
- [ ] **`pbi-execution-loop#07`** — Check Resource serialization in scheduling
  <br>↳ blocked by: pbi-execution-loop#02, verification-adapters#05

#### 12 `verification-adapters` — 0/8

- [ ] **`verification-adapters#01`** — Check adapter seam and normalized finding shape
  <br>↳ blocked by: data-handling#01, execution-core#01, repository-readiness#04
- [ ] **`verification-adapters#02`** — Enclosing-symbol derivation and the fallback ladder
  <br>↳ blocked by: release-engineering#01, verification-adapters#01
- [ ] **`verification-adapters#03`** — Evidence validity: completeness, operator classification, and report reuse
  <br>↳ blocked by: execution-core#02, verification-adapters#01
- [ ] **`verification-adapters#04`** — Check stability and adapter failure classification
  <br>↳ blocked by: config-and-snapshot#04, execution-core#06, verification-adapters#01
- [ ] **`verification-adapters#05`** — Check resources: scoped declaration, allocation, and lease reclamation
  <br>↳ blocked by: execution-core#07, release-engineering#01, verification-adapters#01
- [ ] **`verification-adapters#06`** — TypeScript and JavaScript adapter set
  <br>↳ blocked by: repository-readiness#04, verification-adapters#01
- [ ] **`verification-adapters#07`** — Python adapter set
  <br>↳ blocked by: repository-readiness#04, verification-adapters#01
- [ ] **`verification-adapters#08`** — Opt-in mutation adapter
  <br>↳ blocked by: config-and-snapshot#04, git-integration#02, verification-adapters#01, verification-adapters#05

### Wave 4 — Delivery

#### 13 `entropy-gate` — 0/6

- [ ] **`entropy-gate#01`** — Gate decision record and differential classification
  <br>↳ blocked by: config-and-snapshot#04, data-handling#01, execution-core#01, execution-core#05, verification-adapters#01, verification-adapters#02
- [ ] **`entropy-gate#02`** — Absolute mandatory rules and fail-closed evidence handling
  <br>↳ blocked by: config-and-snapshot#01, entropy-gate#01, verification-adapters#03
- [ ] **`entropy-gate#03`** — Evidence consolidation: reuse, target currency, and invalidation
  <br>↳ blocked by: config-and-snapshot#04, entropy-gate#01, repository-readiness#04, verification-adapters#01, verification-adapters#03
- [ ] **`entropy-gate#04`** — Verification integrity comparison, assertion-shape warning, and operator approval
  <br>↳ blocked by: entropy-gate#01, entropy-gate#05, execution-core#02, repository-readiness#04, slicing-and-approval#01, spec-validation#02, verification-adapters#01, verification-adapters#08
- [ ] **`entropy-gate#05`** — Adversarial review: ordering, add-only, and failure behavior
  <br>↳ blocked by: config-and-snapshot#01, entropy-gate#01, entropy-gate#04, execution-core#05, execution-core#06, gtp-protocol#01, gtp-protocol#03
- [ ] **`entropy-gate#06`** — Correction loop: subject derivation, attempt accounting, and exhaustion
  <br>↳ blocked by: entropy-gate#01, execution-core#05, git-integration#02

#### 14 `git-integration` — 0/9

- [ ] **`git-integration#01`** — Git Workflow Policy resolution and the integration operation surface
  <br>↳ blocked by: config-and-snapshot#02, config-and-snapshot#04, execution-core#01, repository-readiness#01
- [ ] **`git-integration#02`** — Merge Candidate preparation and the Merge Authorization binding
  <br>↳ blocked by: config-and-snapshot#04, entropy-gate#01, entropy-gate#03, execution-core#07, git-integration#01, pbi-execution-loop#01, pbi-execution-loop#05, verification-adapters#01
- [ ] **`git-integration#03`** — Serialized target update, the Mutation Approval Boundary, and local-merge Operation Reconciliation
  <br>↳ blocked by: execution-core#02, execution-core#06, execution-core#07, git-integration#02
- [ ] **`git-integration#04`** — Conflict resolution within candidate preparation
  <br>↳ blocked by: entropy-gate#01, entropy-gate#03, execution-core#05, git-integration#02, gtp-protocol#03, slicing-and-approval#07
- [ ] **`git-integration#05`** — Provider Identity, the provider interface, and the scripted provider fake
  <br>↳ blocked by: data-handling#01, git-integration#01
- [ ] **`git-integration#06`** — Provider Protection Authority and divergence blocking
  <br>↳ blocked by: config-and-snapshot#06, git-integration#05
- [ ] **`git-integration#07`** — Pull Request preparation, Pull Request Observation, and the local-plus-provider conjunction
  <br>↳ blocked by: entropy-gate#01, execution-core#06, git-integration#02, git-integration#05
- [ ] **`git-integration#08`** — Requested changes, external integration, and Pull Requests closed without merge
  <br>↳ blocked by: execution-core#03, execution-core#05, git-integration#07, slicing-and-approval#05, slicing-and-approval#07
- [ ] **`git-integration#09`** — Provider conformance suite and support matrix rows
  <br>↳ blocked by: git-integration#05, git-integration#06, git-integration#07, harness-adapters#07, release-engineering#06

#### 15 `baseline-transitions` — 0/6

- [ ] **`baseline-transitions#01`** — Transition declaration and governance-path permission
  <br>↳ blocked by: data-handling#01, execution-core#01, execution-core#02, gtp-protocol#07, slicing-and-approval#01, slicing-and-approval#06
- [ ] **`baseline-transitions#02`** — Transition manifest: configurations, comparison mode, and coverage change
  <br>↳ blocked by: baseline-transitions#01, config-and-snapshot#04, verification-adapters#01, verification-adapters#04
- [ ] **`baseline-transitions#03`** — Finding change across configurations: rule mappings and the count fallback
  <br>↳ blocked by: baseline-transitions#02, execution-core#02, verification-adapters#01, verification-adapters#02
- [ ] **`baseline-transitions#04`** — Old-baseline evaluation of the introducing delivery
  <br>↳ blocked by: baseline-transitions#01, entropy-gate#01, entropy-gate#02
- [ ] **`baseline-transitions#05`** — Adoption, refusal, and abandonment
  <br>↳ blocked by: baseline-transitions#02, config-and-snapshot#04, execution-core#02, gtp-protocol#05
- [ ] **`baseline-transitions#06`** — Post-adoption effect, in-flight migration, and transport surface
  <br>↳ blocked by: baseline-transitions#05, config-and-snapshot#05, mcp-server#01, mcp-server#02

### Wave 5 — Surfaces and operation

#### 16 `mcp-server` — 0/5

- [ ] **`mcp-server#01`** — MCP transport adapter bootstrap
  <br>↳ blocked by: data-handling#01, execution-core#01
- [ ] **`mcp-server#02`** — Derived tool catalog and drift guard
  <br>↳ blocked by: execution-core#01, execution-core#02, mcp-server#01
- [ ] **`mcp-server#03`** — Result Submission over the MCP channel
  <br>↳ blocked by: gtp-protocol#02, gtp-protocol#06, harness-adapters#02, mcp-server#02
- [ ] **`mcp-server#04`** — Honest host identification and capability-gated tools
  <br>↳ blocked by: gtp-protocol#04, harness-adapters#02, mcp-server#01, pbi-execution-loop#03
- [ ] **`mcp-server#05`** — Harness conformance for the MCP surface
  <br>↳ blocked by: harness-adapters#02, harness-adapters#07, machine-setup#03, mcp-server#02, mcp-server#03, mcp-server#04

#### 17 `dashboard` — 0/7

- [ ] **`dashboard#01`** — Loopback transport shell and read-only monitor
  <br>↳ blocked by: data-handling#01, execution-core#01
- [ ] **`dashboard#02`** — Dashboard Capability Token and the mutation boundary
  <br>↳ blocked by: dashboard#01, execution-core#02, execution-core#08
- [ ] **`dashboard#03`** — Honest PBI projection and Monitor swimlanes
  <br>↳ blocked by: dashboard#01, demo-mode#01, execution-core#03, execution-core#05, execution-core#06, git-integration#07, gtp-protocol#04, harness-adapters#02, verification-adapters#01
- [ ] **`dashboard#04`** — Live transition feed over SSE
  <br>↳ blocked by: dashboard#01, dashboard#03, demo-mode#05, execution-core#01
- [ ] **`dashboard#05`** — Operator decision surface
  <br>↳ blocked by: dashboard#02, dashboard#03, demo-mode#02, execution-core#08, git-integration#02, git-integration#03, slicing-and-approval#01
- [ ] **`dashboard#06`** — Settings screen
  <br>↳ blocked by: config-and-snapshot#01, config-and-snapshot#02, config-and-snapshot#03, config-and-snapshot#07, dashboard#02
- [ ] **`dashboard#07`** — Token lifecycle, non-persistence proof, and manual entry fallback
  <br>↳ blocked by: dashboard#02, data-handling#01, data-handling#02

#### 18 `compound-learning` — 0/6

- [ ] **`compound-learning#01`** — Learning candidate from Entropy Gate findings, approved into the marked section
  <br>↳ blocked by: data-handling#01, data-handling#04, entropy-gate#01, execution-core#01, execution-core#02, repository-readiness#01, repository-readiness#02, verification-adapters#01
- [ ] **`compound-learning#02`** — Candidates from Correction Attempts, Protocol Failures, and state transitions
  <br>↳ blocked by: compound-learning#01, entropy-gate#06, execution-core#01, execution-core#05, gtp-protocol#01
- [ ] **`compound-learning#03`** — Candidates from handoff patterns and integrity findings
  <br>↳ blocked by: compound-learning#01, entropy-gate#04, pbi-execution-loop#04
- [ ] **`compound-learning#04`** — Rejection, observation fingerprint suppression, and per-source backoff
  <br>↳ blocked by: compound-learning#01, config-and-snapshot#01, config-and-snapshot#04, data-handling#01, execution-core#01
- [ ] **`compound-learning#05`** — Applied-section stewardship: grouping, removal, size limit, and consolidation
  <br>↳ blocked by: compound-learning#01, config-and-snapshot#01, config-and-snapshot#04, execution-core#01, repository-readiness#01, repository-readiness#02
- [ ] **`compound-learning#06`** — Target routing by Governance Precedence and conversion to a Governance Baseline Transition
  <br>↳ blocked by: baseline-transitions#01, compound-learning#01, config-and-snapshot#06

<!-- END GENERATED: issue checklist -->
