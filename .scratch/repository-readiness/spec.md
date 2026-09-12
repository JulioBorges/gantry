# Repository readiness and approved preparation

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 06, wave 1)
Source: `PRD.md` §6.3, §8.1, §7.1
Created: 2026-09-11

## Problem Statement

An operator points Gantry at a repository they already work in. That repository has its own
conventions: ADRs somewhere, specs somewhere else, an `AGENTS.md` written for other tools, a test
command that only works with a particular package manager. `PRD.md` is emphatic that Gantry must adapt
to this rather than impose a layout — "reuse canonical locations already established by the
repository, including conventions installed by other skills", "do not move or duplicate canonical
documents merely to match Gantry's fallback layout", and the example it gives is a repository using
`docs/adr/` with `.scratch/<feature>/spec.md`, which is precisely this repository.

Getting that wrong produces a specific failure: a duplicate documentation tree. Gantry writes specs to
`.gantry/specs/` while the operator keeps writing them in `.scratch/`, linting validates documents
nobody reads, and governance protection guards paths that hold nothing.

The second problem is verification. Gantry's entire quality argument rests on executing real checks and
comparing their evidence, so a repository without working checks cannot run governed execution at all.
But detecting a command is not permission to run it, and the PRD is explicit: "execution of a new or
changed command may not be implicit". Meanwhile a repository missing tooling needs that tooling
installed, which means Gantry proposing changes to someone's project — bounded by an approval that
"authorizes only the explicitly listed commands, files, dependency changes, and expected effects".

The third is smaller and nastier. Repositories have uncommitted changes. Silently including them in a
slice, using them as a comparison baseline, or discarding them are all wrong, and the PRD requires
explicit classification before a worktree is created.

Every policy above is decided. The mechanisms — "detection rules and mapping schema", "the readiness
report format, supported detectors, and exact required instruction sections", "preparation mechanics
and supported tool presets", "exact classification and recovery mechanics" — are all deferred.

## Solution

`gantry init` diagnoses rather than configures. It runs a set of declared detectors over the
repository, produces a structured readiness report where every item has a status and a required action,
and persists the effective Artifact Location Mapping it resolved. Detection prefers what the repository
already says about itself: when a repository documents its own conventions — as this one does under
`docs/agents/` — those documents are the primary detection source, ahead of directory heuristics.
Gantry creates a default location only for a category with no existing convention.

Instructions are merged, never overwritten. Gantry owns a clearly delimited section of the root
`AGENTS.md` and writes only inside it, leaving everything else untouched.

Verification is a two-step contract. Detection proposes commands; approval authorizes them. An approval
shows the exact command, working directory, environment variable references, declared effects, and
expected report, and binds the approved command to the execution rule snapshot, so a later change
invalidates the evidence the old version produced. Where tooling is missing, Gantry produces a
preparation proposal listing exactly what it will do, applies only that, and pauses with an amended
proposal if execution discovers anything outside it.

Uncommitted changes block until the operator classifies them. Readiness itself is a report, never an
approval: a repository can be fully ready and still have nothing authorized to run.

## User Stories

1. As an operator, I want Gantry to detect the conventions my repository already uses, so that I am not asked to adopt a second layout.
2. As an operator, I want my repository's own convention documents treated as the primary detection source, so that what I already wrote down is what Gantry follows.
3. As an operator, I want my existing ADR directory reused, so that Gantry reads and protects the decisions I actually maintain.
4. As an operator, I want my existing spec and issue convention reused, so that authored specs land where my team looks for them.
5. As an operator, I want conventions installed by other skills recognized, so that Gantry coexists with the tools I already run.
6. As an operator, I want default locations created only for categories I have no convention for, so that Gantry fills gaps instead of imposing structure.
7. As an operator, I want nothing moved, renamed, or duplicated to match a Gantry layout, so that adopting Gantry does not reorganize my repository.
8. As an operator, I want the resolved mapping shown to me before it is persisted, so that I can correct a wrong guess.
9. As an operator, I want to override a detected location, so that detection is a proposal rather than a verdict.
10. As an operator, I want the effective mapping persisted and used by authoring, linting, context loading, governance protection, and execution alike, so that no part of the system uses a different path than another.
11. As an operator, I want my existing `AGENTS.md` preserved, so that instructions I wrote for other tools survive.
12. As an operator, I want Gantry's additions confined to a clearly marked section, so that I can see exactly what it added and remove it cleanly.
13. As an operator, I want re-running init to update only that section, so that repeated runs do not accumulate duplicates or clobber my edits.
14. As an operator, I want a minimal `AGENTS.md` created when none exists, so that a fresh repository still carries the workflow guidance.
15. As an operator, I want a `CONSTITUTION.md` ensured without having its content invented for me, so that architectural invariants are mine to state.
16. As an operator, I want the required instruction sections named explicitly, so that I know what Gantry needs rather than guessing from a failure.
17. As an operator, I want my verification tooling detected, so that I do not have to enumerate commands manually.
18. As an operator, I want detection to cover my actual package manager, so that a proposed command works in my repository rather than in a generic one.
19. As an operator, I want to see the exact command, working directory, and environment variable references before anything runs, so that approval is informed.
20. As an operator, I want the declared effects and expected report shown, so that I know whether a command mutates anything and what evidence it will produce.
21. As an operator, I want no detected command executed before I approve it, so that diagnosis never runs arbitrary code from my repository.
22. As an operator, I want an approved command bound to the execution rule snapshot, so that evidence is attributable to a specific command version.
23. As an operator, I want changing an approved command to invalidate its prior evidence and require reapproval, so that a modified check cannot inherit old results.
24. As an operator, I want each check to record what it actually covers, so that I am not told security is handled when only secrets are scanned.
25. As an operator, I want a check that cannot produce valid evidence to prevent readiness, so that governed execution never starts on a broken tool.
26. As an operator, I want a broken tool distinguished from preexisting findings, so that existing debt does not look like a setup failure.
27. As an operator, I want missing tooling presented as a concrete proposal, so that I can evaluate what would change in my project.
28. As an operator, I want the proposal to list every command, file, and dependency change it will make, so that approval has a definite scope.
29. As an operator, I want only the listed items applied, so that approval cannot expand into unrelated changes.
30. As an operator, I want execution to pause with an amended proposal when it discovers anything outside the approved scope, so that scope creep requires a new decision.
31. As an operator, I want readiness re-verified after preparation is applied, so that completing a proposal is not confused with being ready.
32. As an operator, I want accepting a proposal to grant nothing beyond applying it, so that preparation is not planning approval or gate approval.
33. As an operator, I want AFK execution unavailable until required checks are installed, configured, and executable, so that autonomous work cannot start on an unverifiable repository.
34. As an operator, I want my dependency and license policy detected or asked for, so that license rules are part of readiness rather than an afterthought.
35. As an operator, I want existing license findings visible but not blocking, while a newly introduced violation blocks, so that the policy matches the differential rule used elsewhere.
36. As an operator, I want uncommitted changes detected at init, at planning approval, and at dispatch, so that they cannot slip in at any of the three moments.
37. As an operator, I want to choose whether uncommitted changes are excluded, recorded as an intentional base, or moved to a separate branch, so that the decision is mine and explicit.
38. As an operator, I want the governed workflow blocked until I classify them, so that they are never silently included, used as a baseline, or discarded.
39. As an operator, I want no worktree created before the classification is recorded, so that the baseline is definite before work starts.
40. As an operator, I want the readiness report to be structured and itemized, so that I can act on it rather than read prose.
41. As an operator, I want each unready item to state the action required, so that I know whether it needs my approval, my decision, or a tool installation.
42. As an operator, I want to re-run diagnosis cheaply and see only what changed, so that iterating toward readiness is quick.
43. As an operator, I want readiness to be a report rather than an authorization, so that being ready never implies anything was approved.
44. As an operator, I want init to work when run inside my harness conversationally, so that the running agent can walk me through it.
45. As a host harness, I want the readiness report available as structured data, so that I can present it and collect decisions without parsing text.
46. As a Gantry implementer, I want detectors declared per artifact category with ordered signals, so that adding a detector does not change how existing categories resolve.

## Implementation Decisions

### Detection and the effective mapping

Detection runs per artifact category: agent instructions, constitution, ADRs, specs, PBIs or issues,
and learnings. Each category declares ordered signals, and the first satisfied signal wins:

1. **Repository self-description.** A repository that documents its own conventions for agents — this
   repository's `docs/agents/issue-tracker.md` and `docs/agents/domain.md` are the reference case — is
   read first. What a repository says about itself outranks any heuristic.
2. **Existing canonical content.** An `AGENTS.md` at the root, a `CONSTITUTION.md`, a populated
   `docs/adr/`, a `.scratch/<feature>/spec.md` with a sibling `issues/` directory.
3. **Conventional directories.** Known layouts used by other tools, matched only when populated.
4. **Gantry fallback.** The `.gantry/` locations, used only for a category no earlier signal resolved.

The resolved mapping is presented before persistence and is overridable per category. Once persisted it
is captured in the execution rule snapshot, so authoring, linting, context loading, governance
protection, and execution all read one mapping for the life of an execution. A category resolved by
signal 1, 2, or 3 is never moved, renamed, or duplicated.

Detection is read-only. It opens files, walks directories, and reads manifests. It executes nothing.

### Instruction merging

Gantry owns a delimited section of the root `AGENTS.md`, bounded by `<!-- gantry:begin -->` and
`<!-- gantry:end -->`, and writes only between those markers. Content outside is never read for
modification. Re-running init replaces the section's content in place; a missing pair of markers means
the section is appended; a malformed or duplicated pair blocks and asks the operator to resolve it
rather than guessing which one is authoritative.

When no `AGENTS.md` exists, a minimal file is created containing only the marked section. When no
`CONSTITUTION.md` exists, one is created with the required structure and no invented invariants —
architectural invariants are the operator's to state, and a generated constitution full of plausible
rules would be worse than an empty one, since it would be treated as governance at precedence level 3.

Required instruction sections are named explicitly in the readiness report: the ASDLC workflow summary,
the artifact location mapping reference, the approved verification commands reference, and the
governance precedence pointer.

### The readiness report

A structured, itemized document rather than prose:

```ts
type ReadinessItem = {
  category:
    | "artifact_mapping" | "instructions" | "governance"
    | "verification" | "dependency_policy" | "working_tree" | "provider";
  key: string;
  status: "satisfied" | "missing" | "needs_approval" | "needs_decision" | "blocked";
  evidence: string[];              // what was observed, as references
  requiredAction?:
    | { kind: "approve_command"; command: ApprovedCommandProposal }
    | { kind: "authorize_preparation"; proposal: PreparationProposal }
    | { kind: "classify_working_tree"; changes: WorkingTreeChangeSet }
    | { kind: "operator_input"; question: string }
    | { kind: "resolve_conflict"; detail: string };
};

type ReadinessReport = {
  unit: RepositoryExecutionUnitId;
  mapping: ArtifactLocationMapping;
  items: ReadinessItem[];
  afkEligible: boolean;            // true only when no item blocks governed execution
};
```

`afkEligible` is the single answer to "can autonomous implementation start", and it is false while any
required check is missing, unapproved, or unable to produce valid evidence. The report is data, so a
harness can present it and collect decisions without parsing text. Re-running diagnosis is cheap and
reports item-level differences against the previous report.

Readiness is never an approval. A report with `afkEligible: true` means the repository can support
governed execution; it says nothing about whether a plan was approved or a gate passed.

### Verification command detection and approval

Detection identifies the package manager and the tools present, from the approved initial adapter set
in §14.1: npm, pnpm, or yarn with TypeScript, ESLint with typescript-eslint, Vitest, and
dependency-cruiser; uv or pip with Ruff, pytest, Import Linter, and pip-audit; Gitleaks and license
checks where configured. Detection reads manifests, lockfiles, and configuration files. It does not run
the tools.

Each detected or proposed command becomes an approval proposal:

```ts
type ApprovedCommandProposal = {
  purpose: "mandatory_test" | "architecture" | "security" | "dependency" | "license";
  command: string[];               // argv, not a shell string
  workingDirectory: string;
  environmentReferences: string[]; // variable names only, never values
  declaredEffects: "read_only" | "writes_workspace" | "writes_network";
  expectedReport: { format: string; location: string };
  declaredCoverage: string;        // what this check actually covers
  resources: CheckResourceDeclaration[];
  stabilityCriterion: string;
};
```

Commands are argv arrays rather than shell strings, so approval describes exactly what executes with no
shell interpretation between approval and execution. Approval is operator-only, binds the proposal to
the execution rule snapshot, and is invalidated by any change to the command, working directory,
environment references, or declared effects — which in turn invalidates evidence the previous version
produced, per spec 02.

`declaredCoverage` is required and free-form, and it is surfaced wherever the check's evidence appears.
This is what prevents a Gitleaks-only configuration from being presented as security coverage, which the
PRD review flagged as an earlier overstatement.

After approval, each command is executed once to validate that it runs and produces its expected report.
A command that runs but emits no parseable report is `blocked`, not `satisfied` — and this is
distinguished from the command running and reporting findings, which is `satisfied` with preexisting
findings recorded for the differential policy in spec 13.

### Missing tooling and preparation authorization

A missing required check produces a proposal:

```ts
type PreparationProposal = {
  proposalId: string;
  rationale: string;
  commands: string[][];            // argv, executed in order
  fileChanges: Array<{ path: string; change: "create" | "modify"; summary: string }>;
  dependencyChanges: Array<{ manager: string; package: string; version: string; scope: string }>;
  expectedEffects: string[];
  resultingChecks: ApprovedCommandProposal[];
};
```

Authorization is operator-only and scoped to that proposal identity. Application executes only the listed
commands and expects only the listed file and dependency changes. Anything outside — an additional
transitive requirement, a file the tool rewrites that was not listed, a command that fails and needs a
different approach — pauses application and produces an amended proposal referencing the original.
Application never expands implicitly.

After application, readiness is re-verified from scratch. Completing a proposal is not readiness, and
accepting one is not planning approval or gate approval. AFK execution stays unavailable until
`afkEligible` is true on a fresh report.

### Dependency and license policy

Detected from existing configuration where present and asked for otherwise. Approved license checks
become mandatory checks with structured evidence. Existing findings are recorded as the preexisting
baseline and remain visible without blocking; a newly introduced dependency, license, or license change
violating the policy blocks the delivery under the differential rule. A change to the license policy
itself is a governance baseline transition and belongs to spec 15.

### Dirty working tree

Detected at three moments: `gantry init`, planning approval, and PBI dispatch. Detection covers both
uncommitted modifications and untracked files in the relevant base checkout.

```ts
type WorkingTreeTreatment =
  | { kind: "excluded"; acknowledgedPaths: string[] }
  | { kind: "intentional_base"; revision: string; note: string }
  | { kind: "moved_to_branch"; branch: string; revision: string };
```

Until a treatment is recorded, the governed workflow is blocked. No worktree is created and no baseline
is captured before the treatment exists, so the comparison base is definite before any work starts.
Gantry never discards changes: `excluded` leaves them in place and records that they are outside the
execution; `intentional_base` requires them committed first, so the recorded revision is real;
`moved_to_branch` requires an explicit branch that Gantry creates and records. A treatment is bound to
the revision it was recorded against, and new changes appearing later require a new classification
rather than inheriting the old one.

## Testing Decisions

**What makes a good test here.** Tests build real temporary repositories with specific conventions,
run diagnosis and the approval and preparation operations through the core, and assert on the resolved
mapping, the report items and their statuses, `afkEligible`, rejection codes, and the actual file state
of the repository afterwards. Assertions on file content are limited to what is contractual: the
presence and boundaries of the marked section, and that content outside it is byte-identical.

**The seam.** The same seam as spec 01, with real temporary repositories as the primary fixture
variation. Repository shape is the input under test here, so the fixture builder is the most important
piece of test infrastructure this spec adds: it must construct repositories that document their own
conventions, repositories with an existing `AGENTS.md`, repositories with populated `docs/adr/` and
`.scratch/`, bare repositories, repositories with each supported package manager, and repositories with
uncommitted and untracked changes.

Tool detection is tested against fixture manifests and configuration files, not against installed
tools. Command validation execution is tested with a fake check adapter, so no test depends on ESLint or
pytest being present.

**Modules under test.** Category detectors and their signal ordering, mapping resolution and override,
mapping persistence into the snapshot, instruction section merging, constitution ensuring, report
construction and `afkEligible` computation, command proposal construction and approval binding,
coverage declaration propagation, preparation proposal application and scope enforcement, dependency and
license policy detection, and working tree detection and treatment recording.

**Scenarios that must exist**, from PRD §14.3 item 2:

- A repository documenting its conventions under `docs/agents/` resolves ADRs to `docs/adr/` and specs to `.scratch/<feature>/spec.md` with issues under `.scratch/<feature>/issues/`, and creates no `.gantry/specs/` or `.gantry/adrs/`.
- The same repository's files are byte-identical afterwards except for the marked `AGENTS.md` section.
- A repository with a populated `docs/adr/` but no self-description still resolves ADRs there.
- A repository with no convention for a category gets the Gantry fallback for that category only.
- An operator override of a detected location is persisted and used by a subsequent lint operation.
- An existing `AGENTS.md` retains all content outside the markers; re-running init replaces only the section and does not duplicate it.
- Malformed or duplicated markers block with a resolve-conflict action.
- A repository with no `AGENTS.md` gets a minimal one containing only the section.
- A created `CONSTITUTION.md` contains no invented invariants.
- Each supported package manager fixture yields a working proposed command for that manager.
- No detected command executes before approval, verified by a fake adapter that fails the test if invoked.
- An approved command's evidence is invalidated when the command, working directory, environment references, or declared effects change, and reapproval is required.
- A check that runs but emits no parseable report is `blocked`; a check that runs and reports findings is `satisfied` with the findings recorded as the preexisting baseline.
- `declaredCoverage` is required and appears alongside the check's evidence in the projection.
- `afkEligible` is false while any required check is missing, unapproved, or blocked, and becomes true only after a fresh report with all of them satisfied.
- Preparation applies only the listed commands and expected changes; a discovered dependency outside the proposal pauses application and produces an amended proposal referencing the original.
- Authorizing a proposal does not mark the repository ready, and does not approve a plan or a gate.
- Approval and authorization are rejected from a non-operator channel.
- An existing license violation is recorded without blocking; a newly introduced one blocks the delivery.
- Uncommitted and untracked changes are detected at init, at planning approval, and at dispatch.
- The workflow is blocked until a treatment is recorded, and no worktree is created before it.
- `excluded` leaves files in place; `intentional_base` refuses until changes are committed; `moved_to_branch` creates and records the branch.
- New changes after a recorded treatment require a new classification.
- Re-running diagnosis reports item-level differences against the previous report.

## Out of Scope

- **Operations, approvals, snapshots, blocking states** (spec 01, spec 02): this spec defines what readiness means and what its approvals contain; the core records and enforces them, and spec 02 captures them.
- **Machine-level installation** (spec 05): `gantry setup`, the `~/.gantry` factory, skill installation and harness symlinks. This spec assumes the machine factory exists and covers only the per-repository phase.
- **Presets and demo** (specs 05, 07): routing presets and `init --demo`. This spec covers `init` against a real repository.
- **Spec and PBI content validation** (specs 08, 09): lint rules, Requirement Review, slicing. This spec resolves where those documents live.
- **Check execution, evidence normalization, stability, resource locking** (spec 12): this spec produces approved command declarations; spec 12 runs them and normalizes their output.
- **The differential gate decision** (spec 13): this spec records the preexisting finding baseline; spec 13 decides what blocks.
- **Governance baseline transitions** (spec 15): changing an approved check, tool version, or license policy after adoption.
- **Git workflow policy resolution and provider identity** (spec 14): the `provider` readiness category's content — observed protection rules, authenticated identity, and repository access — is produced there and consumed here as report items.
- **Egress and retention declaration semantics** (spec 04): this spec collects the declarations during onboarding; spec 04 defines their meaning and enforcement.

Out of scope by product decision:

- A mandatory Gantry documentation layout. The glossary marks it as a term to avoid, and §6.3 forbids duplicating canonical documents.
- Generating architectural invariants on the operator's behalf. A plausible invented constitution would carry precedence level 3 without anyone having decided it.
- Open-ended setup permission. Preparation authorization is scoped to a specific proposal (§6.3).
- Automatic remediation of preexisting findings. Existing debt is recorded, not fixed, per the differential policy.

## Further Notes

**Binding decisions.** Nothing here contradicts either ADR. The read-only nature of detection is the
practical expression of ADR-0001's boundary: diagnosing a repository is not a license to execute its
code.

**Glossary alignment.** Repository Readiness, Artifact Location Mapping, Verification Command Approval,
Preparation Authorization, Dirty Working Tree, and License Policy follow `CONTEXT.md`, including the
terms it marks to avoid: readiness is not machine setup and not gate approval; mapping is not a
duplicate documentation tree; command approval is not tool detection; preparation authorization is not
open-ended permission; a dirty working tree is not an approved baseline.

**Glossary gap for `/domain-modeling`.** Readiness item, declared coverage, and working tree treatment
are introduced here without entries and should get them.

**Where the risk actually sits.** Detection is the part most likely to be wrong in the field, because
repository conventions are more varied than any detector set. The design absorbs that in two ways: the
resolved mapping is always shown and overridable before persistence, so a wrong guess costs one
correction rather than a duplicate tree; and signal 1 means a repository can make detection correct by
documenting itself, which is a better outcome than Gantry guessing better. The residual risk is a
repository whose convention is implicit and unusual, which will land on the fallback and require an
override — acceptable, and visible in the report rather than silent.

The second risk is preparation scope. Package managers routinely rewrite lockfiles and add transitive
dependencies, so a strict reading of "only the listed changes" would pause on nearly every real
installation. The proposal therefore lists dependency changes at the level the operator cares about and
declares lockfile modification as an expected effect; anything beyond that pauses. Getting that
threshold right is the main thing to validate against real repositories.

**Sequencing note.** This spec depends on spec 02 for the snapshot and on spec 01 for approvals, and
specs 08, 09, and 12 all depend on the mapping it produces. The mapping schema is therefore the piece
to settle first — ahead of detectors, report format, or preparation — because three later specs read it
and changing it later touches all of them.
