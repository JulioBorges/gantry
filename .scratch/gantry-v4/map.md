# Gantry v4 — spec map

Type: map
Status: active
Source: `PRD.md` (v4.0.0)
Created: 2026-09-11

`PRD.md` is the product argument for all of Gantry v4, not a feature. It defers roughly forty
contracts with the phrase "remains to be specified" and instructs (§14) that they be resolved
"in local specs and issues under the repository's existing `.scratch/<feature>/` convention".

This map is that decomposition. Each row is one spec, living at `.scratch/<slug>/spec.md`, with its
implementation issues at `.scratch/<slug>/issues/NN-<slug>.md`. A spec **resolves** the PRD items it
owns; it never restates them as open questions.

## Shared testing seam

Every spec binds its tests to a single seam: the **shared operation core**, invoked in process
against a real temporary SQLite database and a real temporary Git repository, with harness drivers
and check adapters injected as fakes. CLI, MCP, and dashboard get one thin parity test each, proving
delegation rather than behavior. This follows §8.1: "no interface may bypass an invariant" — so the
invariants are tested below the transports, once. `execution-core` establishes this seam; later specs
extend it rather than adding new ones.

## Wave 0 — Foundation

Nothing runs without these. No real harness, no transport.

| # | Spec | Owns | PRD | Blocked by | Status |
|---|---|---|---|---|---|
| 01 | [`execution-core`](../execution-core/spec.md) | Shared operation core, Execution State Machine, SQLite record families, Repository Execution Unit identity, PBI Execution Ownership, Correction Budget and Infrastructure Retry accounting, operation intent/receipt/reconciliation, Execution Cancellation and Resumption, Cleanup Authorization, execution version compatibility | §8.1, §6.1, §5.4.6, §6.2 | — | drafted |
| 02 | [`config-and-snapshot`](../config-and-snapshot/spec.md) | ConfigStore layering, config validation, Execution Rule Snapshot capture and migration, Governance Precedence resolution, capacity and budget limit values | §6.2 | 01 | drafted |
| 03 | [`gtp-protocol`](../gtp-protocol/spec.md) | Role-specific task and result contracts, boundary validation with forward compatibility, Result Submission identity and receipts, Protocol Failure, status semantics and precedence, Implementation Completion rules | §5 | 01 | drafted |
| 04 | [`data-handling`](../data-handling/spec.md) | Output Redaction pipeline, Telemetry Retention, Data Egress Policy enforcement | §6.2 | 01 | drafted |

## Wave 1 — Entering a repository

| # | Spec | Owns | PRD | Blocked by | Status |
|---|---|---|---|---|---|
| 05 | [`machine-setup`](../machine-setup/spec.md) | `gantry setup`, `~/.gantry` factory, skills at `~/.agents/skills/gantry-*` and harness symlinks, harness compatibility matrix, presets | §6.3, §3.2, §7.1 | 02 | drafted |
| 06 | [`repository-readiness`](../repository-readiness/spec.md) | `gantry init`, Repository Readiness diagnosis, Artifact Location Mapping, Verification Command Approval, Preparation Authorization, Dirty Working Tree classification, dependency and license policy detection | §6.3, §8.1 | 02 | drafted |
| 07 | [`demo-mode`](../demo-mode/spec.md) | `gantry init --demo`, fixture project, stub agents, under-two-minute pipeline, explicit simulated-evidence marking | §7.1, §13.6, §8.2 | 01, 03 | drafted |

## Wave 2 — Planning

| # | Spec | Owns | PRD | Blocked by | Status |
|---|---|---|---|---|---|
| 08 | [`spec-validation`](../spec-validation/spec.md) | `gantry lint-spec`, Spec Structural Validation rules, Requirement Review, Spec Adaptation of existing canonical documents, structured authoring templates | §7.2 | 03, 06 | drafted |
| 09 | [`slicing-and-approval`](../slicing-and-approval/spec.md) | `gantry slice-spec`, `gantry lint-pbi`, Initial Context Budget estimation and uncertainty, PBI Dependency and Dependency Readiness, Planning Approval provenance, Plan Amendment | §4.2, §7.3, §7.2 | 08 | drafted |

## Wave 3 — Execution

| # | Spec | Owns | PRD | Blocked by | Status |
|---|---|---|---|---|---|
| 10 | [`harness-adapters`](../harness-adapters/spec.md) | Native subagent, Detached CLI, and Gateway invocation adapters; Integration Capability declaration; context usage extraction; agent interruption and ownership reconciliation; the four Codex/OpenCode native and cross-harness combinations | §6.1, §14.2 | 03, 04 | drafted |
| 11 | [`pbi-execution-loop`](../pbi-execution-loop/spec.md) | PBI Worktree lifecycle, dispatch scheduling and capacity accounting, Context Watermark observation, State Compaction Protocol handoff memos, `blocked` handling, micro-commits, review waiting | §7.4, §4.1, §4.3, §6.2 | 09, 10 | drafted |
| 12 | [`verification-adapters`](../verification-adapters/spec.md) | TypeScript/JavaScript and Python check adapters, Comparison Evidence normalization, Evidence Completeness, Check Stability, Check Resource coordination | §7.5, §14.1 | 06 | drafted |

## Wave 4 — Delivery

| # | Spec | Owns | PRD | Blocked by | Status |
|---|---|---|---|---|---|
| 13 | [`entropy-gate`](../entropy-gate/spec.md) | Quality Regression differential decision, absolute mandatory rules, evidence consolidation, Correction Attempt loop, optional Adversarial Review semantics, verification integrity | §7.5 | 12 | drafted |
| 14 | [`git-integration`](../git-integration/spec.md) | Git Workflow Policy, worktree and branch operations, serialized merge, Merge Candidate versus current target revalidation, Merge Authorization, Pull Request preparation and observation, requested changes, externally resolved Pull Requests, Mutation Approval Boundary, Provider Identity, Provider Protection Authority, mutation reconciliation | §7.6, §6.2, ADR-0002 | 13 | drafted |
| 15 | [`baseline-transitions`](../baseline-transitions/spec.md) | Governance Baseline Transition manifest, comparative transition evidence, snapshot migration for in-flight executions | §7.5, §6.2 | 13 | drafted |

## Wave 5 — Surfaces and operation

| # | Spec | Owns | PRD | Blocked by | Status |
|---|---|---|---|---|---|
| 16 | [`mcp-server`](../mcp-server/spec.md) | `gantry mcp`, tool catalog mapped onto the operation core, transport parity | §11 | 01 | drafted |
| 17 | [`dashboard`](../dashboard/spec.md) | Monitor with SSE, Settings screen, Dashboard Capability Token issuance and scoping, state projections | §8.2, §8.3 | 01, 02 | drafted |
| 18 | [`compound-learning`](../compound-learning/spec.md) | `gantry learn-from-pbi`, learning candidates, approved `AGENTS.md` updates | §9, §10 Phase 5 | 14 | drafted |
| 19 | [`release-engineering`](../release-engineering/spec.md) | CI required checks, publish on tag with provenance, release flow, progressive documentation | §12 | — | drafted |

## Suggested order of attack

`01 execution-core` → `03 gtp-protocol` → `02 config-and-snapshot` → `04 data-handling` →
`07 demo-mode` (first visible artifact, runs on stubs) → `06 repository-readiness` →
`08 spec-validation` → `09 slicing-and-approval` → `10 harness-adapters` →
`11 pbi-execution-loop` → `12 verification-adapters` → `13 entropy-gate` →
`14 git-integration` → remainder.

## Conventions

- All specs and generated user-facing documents are written in English (§12.4).
- Domain terms follow `CONTEXT.md`; avoid the synonyms it marks with `_Avoid_`.
- ADR-0001 (harness-first control boundary) and ADR-0002 (worktree isolation and serialized
  integration) are binding on every spec in this map.
- A spec that contradicts an ADR must say so explicitly rather than overriding it silently.

## Boundaries worth restating

Two PRD boundaries are easy to lose during decomposition, so every spec inherits them:

1. A native harness can act outside Gantry's APIs. Gantry guarantees the transitions it accepts, not
   operating-system isolation of arbitrary harness actions (§14.2).
2. Integration limitations are documented, never filled in with a stronger guarantee. A capability
   that an integration does not expose must not be advertised (ADR-0001, §13.1).
