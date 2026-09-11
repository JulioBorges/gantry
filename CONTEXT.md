# Gantry

Gantry provides governance for a software factory operated through the operator's harness.

## Language

**Host Harness**:
The operator's agent environment responsible for directing the factory workflow and coordinating its agents.
_Avoid_: Gantry orchestrator

**Gantry**:
The factory that validates workflow transitions and authorizes merges according to its governance rules.
_Avoid_: Autonomous agent supervisor

**Integration Capability**:
An explicitly supported ability of a harness integration, such as observing context usage or interrupting an agent, that determines which execution guarantees are available.

**Context Watermark**:
The configured context usage threshold for requesting a handoff; a strict ceiling is only a guarantee when the integration can enforce it.
_Avoid_: Universal context ceiling

**Initial Context Budget**:
The planning limit for a PBI's estimated complete initial context package relative to its model window, with estimation method and uncertainty recorded.
_Avoid_: Source-file count, measured runtime usage

**Protocol Failure**:
An invocation whose required result is missing or invalid, preventing workflow advancement while preserving completed work for recovery.
_Avoid_: Agent-reported blocked result, successful invocation

**Implementation Completion**:
The point at which a PBI has all its criteria met, no pending criteria, and passing mandatory tests verified on the delivered revision, supported by a valid agent result; it makes the PBI ready for quality gates.
_Avoid_: Merge authorization, tests green

**Merge Authorization**:
Gantry's permission to integrate a PBI after implementation completion and required validation, bound to a specific merge candidate and target revision; changing either invalidates the permission.
_Avoid_: Implementation completion

**PBI Worktree**:
The dedicated working copy and branch assigned to an active PBI, separating its implementation changes from other concurrent PBIs.
_Avoid_: Shared builder checkout

**Merge Candidate**:
The proposed integrated revision of a PBI and the current target, subject to gates and integration tests before merge authorization.
_Avoid_: Approved PBI branch

**Git Workflow Policy**:
The repository's chosen rules for naming and starting PBI branches, preparing Pull Requests, and integrating deliveries into the designated target with required checks and approvals.
_Avoid_: Harness preset

**PBI Dependency**:
A prerequisite PBI whose integration into the applicable target must precede implementation of a dependent PBI.
_Avoid_: Suggested execution order

**Dependency Readiness**:
The condition in which all of a PBI's declared prerequisites have been integrated and are included in its starting base, making it eligible to begin implementation.
_Avoid_: Implementation completion, agent-reported blocked result

**Adversarial Review**:
An optional LLM evaluation that may add findings to deterministic review; once enabled, a valid review without blockers is required alongside passing deterministic checks for merge authorization.
_Avoid_: Replacement for deterministic gates

**Correction Budget**:
The maximum correction attempts shared by all gates of an individual PBI under the global policy, retained across handoffs and resumes; exhaustion with unresolved failures stops automatic correction and leaves the gate failed.
_Avoid_: Machine-wide attempt pool, per-agent allowance

**Correction Attempt**:
A cycle of correcting a PBI's gate findings followed by revalidation, consuming one unit of its correction budget; the initial gate evaluation consumes none.
_Avoid_: Individual gate execution, initial evaluation

**Infrastructure Retry**:
A repeat execution after an infrastructure failure prevented evaluation, governed by a separate retry budget without consuming a PBI's correction budget or granting gate approval.
_Avoid_: Correction attempt

**Operation Reconciliation**:
The determination of whether a previously requested factory operation occurred, using authoritative Git or provider state when its result is uncertain; unresolved outcomes prevent repetition.
_Avoid_: Blind retry

**AFK Execution**:
Workflow progression without ongoing operator interaction while the host harness remains active; closure requires explicit resumption rather than background orchestration.
_Avoid_: Unattended background service

**Execution Resumption**:
The operator-requested continuation of persisted factory work after pending agents and operations have been reconciled, retaining existing progress and correction counts.
_Avoid_: New pipeline, budget reset

**Execution Rule Snapshot**:
The fixed version of configuration and governance rules assigned to an execution, retained on resumption; replacing it requires explicit operator action and revalidation of affected approvals.
_Avoid_: Live settings

**Governance Precedence**:
The fixed order used to resolve applicable provider, execution, constitution, ADR, plan, and operational rules; unresolved conflicts block the affected transition.
_Avoid_: Agent preference, document order on disk

**Execution Cancellation**:
The operator-requested stop of workflow progression that preserves execution artifacts and reconciles pending work without automatically undoing external mutations.
_Avoid_: Rollback, cleanup, implicit resume

**Dashboard Capability Token**:
An ephemeral CLI-issued token held in dashboard memory and required for mutating requests, scoped to a session and repository execution unit without persistent storage.
_Avoid_: Frontend-generated secret, user authentication

**Cleanup Authorization**:
The operator's explicit approval to remove identified execution artifacts after dependency and pending-operation checks; cleanup never occurs implicitly after a workflow outcome.
_Avoid_: Automatic garbage collection, rollback

**Execution State Machine**:
The validated set of states and transitions governing executions, PBIs, gates, and external operations; invalid or insufficiently evidenced transitions are rejected.
_Avoid_: Status label, dashboard display

**Spec Structural Validation**:
The pass/fail assessment of a Living Spec against mandatory, objectively checkable requirements; passing it alone does not establish semantic quality or approval for slicing.
_Avoid_: Spec quality score, spec approval

**Requirement Review**:
The Requirement Critic's evaluation of a Living Spec's ambiguity, coherence, and verifiability; a valid review without blockers is required alongside structural validation for technical readiness to slice.
_Avoid_: Structural lint

**Planning Approval**:
The operator's explicit acceptance of a particular spec and PBI breakdown, including behavior, coverage, granularity, and dependencies, required before AFK implementation may start.
_Avoid_: Lint success, requirement review, Pull Request approval

**Plan Amendment**:
A proposed change to approved behavior, acceptance criteria, contracts, dependencies, or PBI decomposition that requires renewed operator approval before affected work proceeds.
_Avoid_: Internal implementation choice

**Repository Readiness**:
The repository's preparation for governed execution, covering workflow instructions, documentation locations, required artifacts, and executable verification checks.
_Avoid_: Machine setup, gate approval

**Verification Command Approval**:
The operator's explicit acceptance of a verification command, its execution context, and expected evidence before first or changed execution; changing it invalidates prior evidence.
_Avoid_: Tool detection, implicit execution

**Preparation Authorization**:
The operator's approval for a specific repository-readiness proposal, limited to its listed commands, files, dependency changes, and effects; newly discovered work requires an amended approval.
_Avoid_: Open-ended setup permission

**Output Redaction**:
The mandatory removal or masking of sensitive values before factory output is persisted or displayed; uncertain sanitization blocks full output retention and requires review.
_Avoid_: Best-effort log filtering, secret-free claim

**Telemetry Retention**:
The configured amount of execution content retained for audit, defaulting to redacted references and metadata while requiring explicit repository opt-in for detailed content.
_Avoid_: Full diff by default, unlimited log retention

**Data Egress Policy**:
The repository-approved rules for which roles and drivers may send which classes of repository content outside the local execution environment.
_Avoid_: Implicit provider routing, credential policy

**License Policy**:
The repository-approved rules for dependency licenses and license changes, evaluated as mandatory evidence where configured and blocking newly introduced incompatibilities.
_Avoid_: Vulnerability policy, existing finding waiver

**Artifact Location Mapping**:
The repository's effective canonical locations for specs, PBIs, and governance documents, reusing existing conventions and providing defaults only where no convention exists.
_Avoid_: Duplicate documentation tree, mandatory Gantry layout

**Spec Adaptation**:
The preparation of an existing canonical spec for Gantry validation by identifying and proposing missing required content while preserving its established format; adaptation does not constitute planning approval.
_Avoid_: Mandatory template rewrite, automatic approval

**Execution State**:
The authoritative record of a factory execution's progress, attempts, approvals, and operations, advanced through validated transitions rather than document status edits or agent claims alone.
_Avoid_: Markdown status, agent-reported completion

**Repository Execution Unit**:
A clone and its associated worktrees sharing operational history and merge serialization; separate clones remain independent units even when they use the same remote.
_Avoid_: Remote URL, individual worktree

**PBI Execution Ownership**:
The exclusive authority of a current execution to advance a PBI within its repository execution unit; a superseded agent assignment cannot advance state through late results.
_Avoid_: Permanent agent ownership, merge authorization

**Entropy Gate**:
The final decision on new or aggravated architecture and quality problems, consolidating configured check evidence for a merge candidate and current target while preserving absolute mandatory rules.
_Avoid_: Feature test suite, secret entropy scan

**Quality Regression**:
An architecture or quality problem introduced or aggravated by a proposed delivery relative to its current integration target under the same approved checks.
_Avoid_: All existing debt, aggregate quality score

**Comparison Evidence**:
Structured check results identifying findings by rule, location, severity, and problem identity, tied to the assessed revision and verification rules so existing and changed problems can be compared.
_Avoid_: Exit code alone, absent report

**Check Stability**:
The declared reproducibility and consistency requirement for a mandatory verification check, including its environment, inputs, and accepted repetition behavior.
_Avoid_: Single green run, unlimited rerun

**Check Resource**:
A declared resource needed for verification, such as a port, database, or temporary directory, isolated per execution where possible or shared through serialized access.
_Avoid_: Worktree isolation alone

**Provider Identity**:
The authenticated GitHub identity and authorization context selected for a provider operation, shown before first mutation without exposing credential values.
_Avoid_: Credential value, repository-wide authority

**Mutation Approval Boundary**:
The distinction between plan-authorized Pull Request preparation and the separate confirmation required before a direct local merge changes the target branch.
_Avoid_: Gate approval, generic execution approval

**Dirty Working Tree**:
A relevant checkout containing uncommitted or untracked changes that have not been explicitly classified for a Gantry execution and therefore cannot serve as an implicit baseline.
_Avoid_: PBI changes, approved baseline

**Provider Protection Authority**:
The observed GitHub target-branch rules governing checks, approvals, and integration; divergence from local policy blocks delivery until reconciled.
_Avoid_: Local policy override, assumed protection

**Pull Request Observation**:
The authenticated polling of a GitHub Pull Request's checks, reviews, mergeability, and protection state, where missing updates never count as approval.
_Avoid_: Webhook delivery, stale approval

**Evidence Completeness**:
The requirement that comparison findings include enough identity and context to be matched and evaluated; incomplete evidence fails closed unless explicitly classified for that report version.
_Avoid_: Missing fields treated as clean, global manual waiver

**Result Submission**:
An individually identified delivery of an agent result for a dispatch; identical accepted replays reuse the prior receipt, while corrected content requires a new linked submission.
_Avoid_: Task identity, new execution

**Governance Baseline Transition**:
An approved change to the tools, versions, rules, or verification coverage that define repository quality checks, with comparative analysis and explicit adoption before it becomes authoritative.
_Avoid_: Separate spec type, retroactive approval, silent rule change
