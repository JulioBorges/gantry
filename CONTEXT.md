# Gantry

Gantry is a skill pack that runs an agentic software development life cycle inside the operator's harness.

## Language

**Host Harness**:
The operator's agent environment in which Gantry runs: it hosts the skills, spawns the subagents, runs the guard hooks it supports and holds the operator conversation where decisions are taken. Gantry declares each harness's capabilities in the pack and never assumes one it did not declare.
_Avoid_: Gantry orchestrator, engine, external service

**Gantry**:
A harness-neutral skill pack that runs an agentic software development life cycle: deterministic scripts decide which work is ready and whether a delivery is done; agents do the planning, building, reviewing and refuting. It is installed as a directory of skills, either inside a repository or in the user's agent directory.
_Avoid_: Engine, orchestrator, autonomous supervisor, npm application

**Support Tier**:
The declared level at which Gantry runs in a harness, derived from its capability file and exercised on the fixture before it is announced: reference (parallel rounds, native structured output, native worktree isolation, guard hooks), supported (skills, per-role subagents, hooks through the harness's plugin mechanism, results validated by the workflow script) or compatible (skills and a manually driven chain, with whatever the version supports). A run report states the tier it ran at.
_Avoid_: Assumed parity, "works everywhere", unverified support

**Issue**:
The unit of work Gantry plans, implements and verifies: one Markdown file under the repository's issue location, with a `Status:` line, a `## Blocked by` list and a `## Acceptance criteria` checklist, referenced as `<spec-slug>#NN`. Every issue must be a vertical slice: a narrow, complete behaviour demonstrable on its own.
_Avoid_: PBI, ticket, task, story, layer

**Spec**:
The parent document of a set of issues, written in the repository's effective template, describing the problem, the behaviour, the non-goals and the scenarios that the issues must cover. It is the operator's document; agents read and critique it, they do not rewrite it.
_Avoid_: Living Spec, PRD (the product-level document a spec may be derived from), requirements dump

**Integration Capability**:
An explicitly supported ability of a harness, such as running guard hooks on tool events, spawning a subagent with a chosen model, or isolating a subagent in its own worktree, that determines which Gantry guarantees hold in that harness.
_Avoid_: Assumed support, universal guarantee

**Workflow Script**:
A deterministic, dependency-free script that is the sole authority on a workflow question: which work is ready, what a delivery must prove, whether the repository's gates pass, and when an issue becomes done. Agents call it; they never re-decide what it decided.
_Avoid_: Helper, suggestion, LLM judgement

**Guard Hook**:
A harness event handler shipped by Gantry that blocks shortcuts around the workflow rules and records events for observation. It never decides whether work is ready or done; that authority stays with the workflow scripts. Available only where the harness supports hooks. Two rules live one layer lower instead, in the repository's own tracked `pre-push`/`pre-commit` git hooks (`docs/adr/0005`): no force-push and no test-skip commit are enforced there, where the actual ref update or staged diff is visible, because no Bash-command parsing can reliably recognise them.
_Avoid_: Gate, orchestrator, source of truth

**Context Watermark**:
Not a Gantry guarantee: no harness reports context usage to a hook, so Gantry never promises a context ceiling. What it does record is that a compaction happened, in which phase of which issue, as a signal in the run log and dashboard.
_Avoid_: Enforced ceiling, self-reported usage, handoff trigger

**Initial Context Budget**:
The planning limit, 15% of the chosen model's window by default, for an issue's estimated initial package: the issue, its spec and the files it tells the implementer to read, measured deterministically by a workflow script. An issue over budget is refuted by the plan critic with the number.
_Avoid_: Source-file count, measured runtime usage, agent self-estimate

**Result Contract**:
The versioned JSON Schema, shipped in the pack per role (requirement critic, planner, plan critic, implementer, reviewer, critic, learner), that every agent result must satisfy. Harnesses that can enforce structured output load it directly; everywhere else the orchestrator validates the result with the workflow script before accepting it.
_Avoid_: Inline schema, task envelope, free-text report

**Protocol Failure**:
A missing or invalid agent result, judged against the role's result contract by a workflow script. It never advances the workflow: the work stays in the worktree, the agent is asked once more, and then the issue is reported as failed for that phase.
_Avoid_: Agent-reported blocked result, successful invocation, silent acceptance

**Implementation Completion**:
The point at which the Critic has accepted an issue with evidence for every acceptance criterion, the declared gates pass, and the worktree is clean; only then does the orchestrator integrate the branch and let the roadmap script mark the issue done.
_Avoid_: Tests green, implementer summary, merge

**Issue Worktree**:
The dedicated Git worktree and branch an implementer works in when a round has more than one issue, so concurrent implementers never share a working directory; a single-issue round works directly on the run branch. Created by the orchestrator, kept after refutation for inspection, removed only through cleanup authorization.
_Avoid_: Shared checkout, the run worktree

**Run Pull Request**:
The draft Pull Request Gantry offers to open from a run's branch to the configured target when the run ends, one per run, carrying each issue's critic evidence. Opening it requires the operator's explicit yes in the conversation; merging it is never Gantry's to do.
_Avoid_: Merge, per-issue PR, stacked PR

**Git Workflow Policy**:
The two Git settings in the repository policy: the target branch the run pull request is opened against and the prefix used for run and issue branches. Everything else about integration is the repository's own protection rules on the provider.
_Avoid_: Harness preset, merge policy, release lifecycle

**Issue Dependency**:
A prerequisite listed in an issue's `## Blocked by` section, by `<spec-slug>#NN` reference; the blocker graph must stay acyclic and the frontier script refuses a graph with a cycle or a dangling reference.
_Avoid_: Suggested order, soft hint

**Dependency Readiness**:
The condition in which every issue in an issue's `## Blocked by` list has `Status: done`, which within a run means integrated into the run branch with gates green; only then does the frontier schedule the issue into a round.
_Avoid_: Implementation completion of the blocker, open branch, agent claim

**Adversarial Review**:
The mandatory verification of every delivery by the Critic, a fresh agent whose job is to refute completion: it runs the acceptance and gates scripts itself, demands evidence per criterion, and defaults to not complete when uncertain. It can only refute; it never marks anything done, and its acceptance is the only thing that lets the roadmap script do so.
_Avoid_: Optional LLM review, replacement for deterministic gates, implementer self-report

**Correction Budget**:
The maximum number of critic-driven correction attempts for one issue in a run, two by default, set in the repository policy or per run; it is a ceiling that is never raised silently. Exhausting it leaves the issue blocked for the operator. The single fix pass after code review is separate and fixed.
_Avoid_: Machine-wide pool, per-gate allowance, retry on agent failure

**Correction Attempt**:
One cycle of a fresh implementer addressing the critic's required fixes in the issue's existing worktree, followed by a new critic verification; it consumes one unit of the issue's correction budget. The first verification consumes none.
_Avoid_: Individual gate execution, review fix pass

**Execution Resumption**:
Running Gantry again over the same scope: the frontier is recomputed from the issues' status lines, and the run log's in-flight record lets the orchestrator offer to continue an issue in its existing worktree instead of starting over. The operator chooses; budgets already spent are not reset.
_Avoid_: New run from scratch, budget reset, automatic takeover

**Lesson Candidate**:
A proposed standing rule drafted by the Learner phase from refutations and review findings recorded in the run log, kept only when the same problem recurred across issues or attempts, and carrying its evidence and its proposed target (the Gantry section of AGENTS.md, CONTEXT.md or an effective template). It stays a draft until the operator accepts it; nothing is injected automatically.
_Avoid_: Auto-injected lesson, single-occurrence note, agent-written rule

**Run**:
One invocation of the Gantry workflow over a scope, executed on its own branch and usually in its own worktree, made of one or more rounds, and progressing only while the host harness stays open. Stopping the harness stops the run and undoes nothing.
_Avoid_: Pipeline, session, background job

**Round**:
The set of in-scope issues whose blockers are all done, implemented concurrently and then integrated one at a time; a run advances round by round.
_Avoid_: Wave (the roadmap's static projection of rounds), batch

**Dashboard**:
A read-only kanban that shows, across runs and harness sessions, which issues are in which phase and which are waiting for the operator. It reads the recorded events and never changes an issue's status or makes a decision; decisions are taken in the harness conversation.
_Avoid_: Control panel, settings screen, approval surface

**Cleanup Authorization**:
The operator's explicit acceptance of a printed cleanup plan listing exactly which worktrees and branches of done, already-merged issues will be removed; Gantry never removes anything outside that plan or without it.
_Avoid_: Automatic garbage collection, rollback

**Effective Template**:
The spec, PRD or issue template in force for a repository: the repository's own copy under its Gantry templates directory when present, otherwise the pack's default. Structural validation derives its required sections from it and the planner writes issues in it, so changing the template is changing the check.
_Avoid_: Hardcoded section list, mandatory rewrite of existing documents

**Spec Structural Validation**:
The workflow script's pass/fail assessment of a spec against mandatory, objectively checkable requirements, accepting equivalent sections under different headings; passing it alone does not establish semantic quality or approval for slicing.
_Avoid_: Spec quality score, spec approval

**Requirement Review**:
The Requirement Critic's evaluation of a spec's ambiguity, coherence, verifiability and non-goal coverage, run after structural validation and before slicing. A blocking finding stops the run; the operator amends the spec, the critic never does.
_Avoid_: Structural lint, automatic spec revision

**Planning Approval**:
The operator's explicit acceptance of a particular spec and issue breakdown, including behavior, coverage, granularity, and dependencies, required before AFK implementation may start.
_Avoid_: Lint success, requirement review, Pull Request approval

**Plan Amendment**:
A proposed change to approved behavior, acceptance criteria, contracts, dependencies, or issue decomposition that requires renewed operator approval before affected work proceeds.
_Avoid_: Internal implementation choice

**Repository Readiness**:
The state produced by the setup skill: a repository policy exists, the artifact locations and effective templates are known, the declared checks run, and AGENTS.md carries the marked Gantry section. Setup is conversational, item by item with trade-offs, idempotent, and enables nothing the operator did not accept.
_Avoid_: Machine setup, gate approval, generic template dump

**Verification Command Approval**:
The operator's explicit acceptance, during setup, of each declared check command, whether it is absolute or differential, and its comparison-evidence mapping; a check Gantry runs is always one the operator declared.
_Avoid_: Tool detection alone, implicit execution

**Artifact Location Mapping**:
The repository's effective canonical locations for specs, issues, and governance documents, reusing existing conventions and providing defaults only where no convention exists.
_Avoid_: Duplicate documentation tree, mandatory Gantry layout

**Spec Adaptation**:
The preparation of an existing canonical spec for Gantry validation by identifying and proposing missing required content while preserving its established format; adaptation does not constitute planning approval.
_Avoid_: Mandatory template rewrite, automatic approval

**Execution State**:
The issue's `Status:` line and acceptance checkboxes, written only by the roadmap script, are the authority on where work stands; the run log records how it got there and what is in flight, and is never consulted to decide whether something is done.
_Avoid_: Run log as source of truth, agent-reported completion, dashboard display

**Repository Execution Unit**:
A clone and its associated worktrees, identified by their shared Git common directory; it keys the machine-level state so every worktree of one clone reports into the same run log. Separate clones remain independent units even when they use the same remote.
_Avoid_: Remote URL, individual worktree

**Repository Policy**:
The repository's tracked, sparse Gantry configuration: the artifact location mapping, gate overrides and which guard hooks are enabled. Anything it does not set falls back to Gantry's defaults; it never holds execution state or secrets.
_Avoid_: State, machine settings, prose in AGENTS.md

**Run Log**:
The append-only record of a run's events (rounds, phases, subagent start and stop, hook decisions), written only by workflow scripts and guard hooks into machine-level state keyed by repository execution unit. It is the dashboard's sole source and is never the authority on an issue's status.
_Avoid_: Telemetry database, source of truth, audit ledger

**Entropy Gate**:
The differential mode of a declared check: the workflow script runs the same command on the round's base and on the delivery, matches findings by rule, file and problem identity, and blocks new or aggravated findings while leaving preexisting ones visible. Checks declared absolute (tests, secrets) stay pass/fail.
_Avoid_: Feature test suite, aggregate quality score, LLM opinion

**Quality Regression**:
A finding present in the delivery and absent from, or less severe in, the round's base under the same declared check.
_Avoid_: All existing debt, any failing check

**Comparison Evidence**:
A check's structured output, declared in the repository policy with a generic mapping of where rule, file, line and message live, that lets the entropy gate compare base and delivery. A check without it is pass/fail only.
_Avoid_: Exit code alone, tool-specific adapter

**Dirty Working Tree**:
A relevant checkout containing uncommitted or untracked changes that have not been explicitly classified for a Gantry execution and therefore cannot serve as an implicit baseline.
_Avoid_: issue changes, approved baseline

