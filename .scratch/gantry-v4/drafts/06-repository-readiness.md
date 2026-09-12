## Spec 06 — repository-readiness

This spec owns the per-repository onboarding phase: `gantry init` as a read-only diagnosis that resolves the **Artifact Location Mapping**, merges Gantry's instruction section into an existing `AGENTS.md` without disturbing anything else, turns detected tooling into **Verification Command Approval** proposals, offers **Preparation Authorization** for missing tooling as a scoped proposal, collects dependency/**License Policy** and egress declarations, and forces an explicit treatment for a **Dirty Working Tree** before any PBI Worktree exists. Everything it produces is a report or a proposal — **Repository Readiness** is never an approval, and `afkEligible` is the only answer to whether governed execution may start. The risk sits in two places. Detection is the part most likely to be wrong in the field, because real repository conventions vary more than any detector set; the design absorbs that by showing the resolved mapping before persistence and making every category overridable, so a wrong guess costs one correction rather than a duplicate documentation tree. The second is preparation scope: package managers rewrite lockfiles and pull transitive dependencies, so the threshold at which application pauses with an amended proposal is the thing most likely to be either useless (pauses on every install) or hollow (never pauses).

### Slices

---

- **01 — Artifact Location Mapping and the readiness report skeleton**
- **What to build**: Category detectors for agent instructions, constitution, ADRs, specs, PBIs/issues and learnings, each declaring ordered signals — repository self-description first, then existing canonical content, then conventional directories, then the Gantry fallback — with first-satisfied-wins resolution and no cross-category interference. Detection is strictly read-only: it opens files, walks directories and reads manifests, and executes nothing. Resolution produces an `ArtifactLocationMapping` that is presented before persistence, is overridable per category through an operation, and is then captured in the Execution Rule Snapshot so authoring, linting, context loading, governance protection and execution all read one mapping for the life of an execution. This slice also lands the report skeleton it lives inside — `ReadinessItem`, `ReadinessReport`, the `afkEligible` computation, and a producer registry keyed by category so later slices and spec 14's `provider` items attach without editing the report — plus `gantry init` rendering the report and the temporary-repository fixture builder every later slice depends on.
- **Acceptance criteria**:
  - A fixture repository documenting its own conventions under `docs/agents/` resolves ADRs to `docs/adr/`, specs to `.scratch/<feature>/spec.md` and PBIs to `.scratch/<feature>/issues/`, and no `.gantry/specs/` or `.gantry/adrs/` directory is created.
  - A fixture with a populated `docs/adr/` and no self-description still resolves ADRs there; a fixture with no convention for exactly one category receives the Gantry fallback for that category only.
  - A per-category override is persisted, captured in the snapshot, and read back identically by a subsequent read operation.
  - Detection runs with a process runner fake that fails the test if invoked, proving nothing in the repository is executed.
  - The fixture repository's files are byte-identical before and after diagnosis apart from Gantry's own state, and nothing is moved, renamed or duplicated for a category resolved by any signal other than the fallback.
  - `afkEligible` is computed from item statuses and is false whenever any item is `missing`, `needs_approval`, `needs_decision` or `blocked`; the CLI has one parity test proving it delegates to the core.
- **Blocked by**: needs the shared operation core `invoke`, the operation request/receipt/rejection-code contract, and the operator-channel rule from `execution-core`; needs the ConfigStore layering and Execution Rule Snapshot capture from `config-and-snapshot`; needs the redaction sink enforcement interface from `data-handling` for persisted report evidence.
- **Parallelizable with**: none (this is the bootstrap slice)

---

- **02 — Instruction merging and constitution ensuring**
- **What to build**: Gantry owns a delimited section of the root `AGENTS.md` bounded by `<!-- gantry:begin -->` and `<!-- gantry:end -->` and writes only between those markers; content outside is never read for modification. Re-running init replaces the section's content in place, a missing marker pair appends the section, and a malformed or duplicated pair blocks with a `resolve_conflict` required action rather than guessing which pair is authoritative. When no `AGENTS.md` exists a minimal file containing only the marked section is created; when no `CONSTITUTION.md` exists one is created with the required structure and no invented architectural invariants. The readiness report names the required instruction sections explicitly — the ASDLC workflow summary, the Artifact Location Mapping reference, the approved verification commands reference, and the Governance Precedence pointer — as `instructions` and `governance` items with their own statuses.
- **Acceptance criteria**:
  - An existing `AGENTS.md` is byte-identical outside the markers after init, and a second init run replaces the section without duplicating it or accumulating whitespace.
  - Malformed markers and two marker pairs each produce a `blocked` item with a `resolve_conflict` action, and neither writes to the file.
  - A repository with no `AGENTS.md` gets a file containing only the marked section, at the location the mapping resolved.
  - A created `CONSTITUTION.md` contains the required structure and zero invariant statements, asserted against the generated content.
  - Each required instruction section appears as its own report item with a status, and a missing section leaves `afkEligible` false.
- **Blocked by**: 01
- **Parallelizable with**: 03, 06, 07

---

- **03 — Verification command detection and approval proposals**
- **What to build**: Detect the repository's package manager and present tooling by reading manifests, lockfiles and configuration files — npm, pnpm or yarn with TypeScript, ESLint with typescript-eslint, Vitest and dependency-cruiser; uv or pip with Ruff, pytest, Import Linter and pip-audit; plus Gitleaks and license checks where configured — and turn each detection into an `ApprovedCommandProposal` carrying argv (never a shell string), working directory, environment variable *names* only, declared effects, expected report format and location, `declaredCoverage`, Check Resource declarations and a Check Stability criterion. Each proposal becomes a `verification` report item with status `needs_approval`. Detection reads; it does not run the tools, and a repository missing a required check produces a `missing` item that points at slice 05's proposal rather than inventing one here.
- **Acceptance criteria**:
  - A fixture for each supported package manager yields a proposed command that is correct for that manager, asserted on argv rather than a rendered string.
  - Proposals carry environment variable names and no values anywhere in the persisted record.
  - `declaredCoverage` is required: a proposal constructed without it is rejected at the boundary.
  - No detected command executes during detection, proven by a check-adapter fake that fails the test if invoked.
  - Every proposal appears as a `verification` item with `needs_approval` and `afkEligible` is false while any required check is unapproved.
- **Blocked by**: 01
- **Parallelizable with**: 02, 06, 07

---

- **04 — Verification Command Approval, validation run and preexisting baseline**
- **What to build**: An operator-only approval operation that accepts an `ApprovedCommandProposal`, binds it to the Execution Rule Snapshot, and yields an `ApprovedCommandRef` that spec 12 and spec 13 later cite as the provenance of evidence. Any change to the command argv, working directory, environment references or declared effects invalidates the approval, invalidates the evidence the previous version produced, and requires reapproval. After approval each command is executed exactly once through an injected check adapter to validate that it runs and emits its expected report: a command that runs but emits no parseable report is `blocked`, while a command that runs and reports findings is `satisfied` with those findings recorded as the preexisting finding baseline for the differential policy. `declaredCoverage` travels with the ref and is surfaced wherever the check's evidence appears.
- **Acceptance criteria**:
  - Approval from a non-operator channel is rejected with `operator_channel_required`; the MCP channel can read proposals but never approve.
  - The approved ref records the snapshot identity, and mutating any of the four bound fields invalidates prior evidence and returns the item to `needs_approval`.
  - A fake adapter emitting no parseable report yields a `blocked` item; a fake adapter emitting findings yields `satisfied` plus a persisted preexisting baseline distinguishable from a setup failure.
  - `afkEligible` flips to true only on a fresh report where every required check is `satisfied`.
  - `declaredCoverage` is present alongside the check's evidence in the state projection, asserted through a read operation.
- **Blocked by**: 03; needs the snapshot-bound evidence invalidation rule from `config-and-snapshot`; needs the redaction sink enforcement interface and normalized content hashing from `data-handling` for validation-run output.
- **Parallelizable with**: 05, 06, 07

---

- **05 — Preparation proposal, authorization and scoped application**
- **What to build**: A missing required check produces a `PreparationProposal` with a proposal identity, rationale, ordered argv commands, file changes, dependency changes at the level the operator cares about, expected effects (lockfile modification declared explicitly), and the `ApprovedCommandProposal`s it would result in. Authorization is operator-only and scoped to that proposal identity. Application executes only the listed commands and tolerates only the listed file and dependency changes; anything outside — an additional direct dependency, an unlisted file rewrite, a command that fails and needs a different approach — pauses application and emits an amended proposal referencing the original, requiring a fresh authorization. After application, readiness is re-diagnosed from scratch: completing a proposal is not readiness, and authorizing one is neither Planning Approval nor gate approval.
- **Acceptance criteria**:
  - Authorization from a non-operator channel is rejected; authorization of a proposal identity that has since changed is rejected.
  - Application runs exactly the listed commands in order, verified by a recording fake, and runs none on authorization failure.
  - A fixture where application pulls a change outside the proposal leaves the repository in the paused state with an amended proposal linked to the original, and no further command runs.
  - Declared lockfile modification does not pause application; an unlisted direct dependency does.
  - A successful application leaves `afkEligible` false until a fresh diagnosis is run, and grants no planning or gate approval anywhere in the state projection.
- **Blocked by**: 03 (for the `ApprovedCommandProposal` shape in `resultingChecks`)
- **Parallelizable with**: 04, 06, 07

---

- **06 — Repository policy readiness: dependency, License Policy and egress declarations**
- **What to build**: Detect the repository's dependency and License Policy from existing configuration where present, and produce an `operator_input` item asking for it where absent. An approved license check becomes a mandatory check with structured evidence, reusing the approval machinery. Existing license findings are recorded as the preexisting baseline and stay visible without blocking, while a newly introduced dependency, license or license change violating the policy blocks the delivery under the same differential rule the Entropy Gate applies. This slice also collects the repository's Data Egress Policy and Telemetry Retention declarations during onboarding as report items — collection only; their meaning and enforcement belong to `data-handling`.
- **Acceptance criteria**:
  - A fixture with an existing license configuration resolves the policy without asking; a fixture without one produces an `operator_input` item and leaves `afkEligible` false.
  - An existing license violation is recorded in the preexisting baseline and does not block, asserted through the projection.
  - A newly introduced violation against the recorded baseline blocks, using the same differential comparison the gate consumes.
  - Egress and retention declarations are persisted through the readiness operation and readable by the owning spec's enforcement path, with no policy semantics implemented here.
  - Changing the License Policy after adoption is rejected here with a pointer to the Governance Baseline Transition path rather than silently re-detected.
- **Blocked by**: 01; 03 (for the `ApprovedCommandProposal` shape used by the license check); needs the egress/retention declaration schema from `data-handling`.
- **Parallelizable with**: 02, 04, 05, 07

---

- **07 — Dirty Working Tree detection and treatment**
- **What to build**: Detect uncommitted modifications and untracked files in the relevant base checkout and expose that detection as a precondition callable at all three moments — `gantry init`, Planning Approval and PBI dispatch — with this slice wiring the init call site and publishing the predicate the other two specs call. Until a treatment is recorded the governed workflow is blocked, no PBI Worktree is created and no comparison baseline is captured.

  ```ts
  type WorkingTreeTreatment =
    | { kind: "excluded"; acknowledgedPaths: string[] }
    | { kind: "intentional_base"; revision: string; note: string }
    | { kind: "moved_to_branch"; branch: string; revision: string };
  ```

  Gantry never discards changes: `excluded` leaves files in place and records them as outside the execution, `intentional_base` refuses until the changes are committed so the recorded revision is real, and `moved_to_branch` creates and records an explicit branch. A treatment is bound to the revision it was recorded against, so changes appearing afterwards require a new classification rather than inheriting the old one.
- **Acceptance criteria**:
  - Fixtures with uncommitted modifications and with untracked files both produce a `working_tree` item with a `classify_working_tree` action and `afkEligible` false.
  - Recording a treatment is operator-only; an agent channel is rejected.
  - `excluded` leaves every file on disk unchanged; `intentional_base` against an uncommitted tree is rejected; `moved_to_branch` creates the branch and records its revision, verified against real Git state.
  - No worktree creation is attempted before a treatment exists, proven by a fake that fails the test if called.
  - Mutating the tree after a treatment is recorded invalidates it and returns the item to `needs_decision` against the new revision.
- **Blocked by**: 01
- **Parallelizable with**: 02, 03, 06

---

### Contracts this spec CONSUMES from other specs

| Contract name | Owning spec slug | Which of your slices needs it |
|---|---|---|
| Shared operation core `invoke`, request/receipt/rejection-code shape | `execution-core` | 01 (then all) |
| Operator-channel assertion and `operator_channel_required` rejection | `execution-core` | 01, 04, 05, 06, 07 |
| Blocked-state and approval record families | `execution-core` | 04, 05, 07 |
| ConfigStore layering | `config-and-snapshot` | 01, 06 |
| Execution Rule Snapshot capture and identity | `config-and-snapshot` | 01, 04 |
| Snapshot-bound evidence invalidation rule | `config-and-snapshot` | 04 |
| Redaction sink enforcement interface | `data-handling` | 01, 04 |
| Normalized content hashing | `data-handling` | 04 |
| Egress and retention declaration schema | `data-handling` | 06 |
| Provider Identity and Provider Protection Authority observations | `git-integration` | 01 (registry extension point for the `provider` category; items produced there) |

### Contracts this spec PUBLISHES for other specs

| Contract name | Your slice | Which specs wait on it |
|---|---|---|
| **Artifact Location Mapping schema** and its snapshot capture | 01 | 08, 09, 12 (also read by 14/15 for governance path protection) |
| `ReadinessReport` / `ReadinessItem` / `afkEligible` and the category producer registry | 01 | 14 (registers `provider` items), 17 (projection), 07 (asserts readiness never derives from demo records) |
| Gantry marker section contract for `AGENTS.md` and required instruction sections | 02 | 18 (approved `AGENTS.md` updates write through the same section) |
| `ApprovedCommandProposal` including `declaredCoverage`, Check Resource and Check Stability declarations | 03 | 12, 13 |
| `ApprovedCommandRef` and its snapshot binding / invalidation rule | 04 | 12, 13, 14 (`localChecks`), 09 (`verification` in the PBI), 15 |
| Preexisting finding baseline record | 04 | 13, 15 |
| License Policy record and its differential rule input | 06 | 13, 15 |
| `WorkingTreeTreatment` and the pre-dispatch precondition predicate | 07 | 09 (Planning Approval), 11 (dispatch, worktree creation) |

### Risks / judgement calls

**Slice 01 is deliberately the largest.** I folded the readiness report skeleton into the Artifact Location Mapping slice rather than giving it its own slice, because the mapping is a field of the report and `artifact_mapping` is itself a report category — splitting them would have produced two half-slices that neither demo independently. The cost is that 01 is a wide first PBI and everything blocks on it. The benefit is that slices 02–07 are all genuinely parallel afterwards, and the contract three other specs wait on ships first. If 01 looks too big in practice, the clean cut is to pull the temporary-repository fixture builder out as a shared test-infrastructure prerequisite — but that would be a horizontal slice, so I left it inside 01.

**03/04 split.** I was tempted to make detection, approval and the validation run one slice, since the spec presents them as a single two-step contract. I split them because the detector matrix alone (three JS package managers, two Python ones, nine tools) is a full PBI, and because the approval-binding and evidence-invalidation rules are the part other specs actually cite. The seam is the `ApprovedCommandProposal` shape, which makes 03 a hub that 04, 05 and 06 all wait on. An alternative worth considering is splitting 03 by ecosystem (JS, then Python) and letting 04 start against the JS half — that trades a cleaner contract for more parallelism.

**Where working-tree enforcement lives.** Slice 07 implements detection, the treatment operation and the `init` call site, and publishes a precondition predicate. Enforcement at Planning Approval and at dispatch is invoked by `slicing-and-approval` and `pbi-execution-loop` respectively. I judged that calling those sites from here would reach into two other specs' control flow; the risk is that "detected at three moments" ends up proven at only one unless those specs' slices carry the test. Worth stating explicitly in their issues.

**License differential boundary.** Slice 06 records the preexisting baseline and decides that a newly introduced violation blocks. The general differential decision belongs to `entropy-gate`. I kept the license-specific rule here because the spec states it here, but if 13's differential machinery turns out to be reusable, 06 should consume it rather than reimplement the comparison.

**Preparation scope threshold (slice 05).** The spec itself flags this as the thing to validate against real repositories: declaring lockfile modification as an expected effect while pausing on an unlisted direct dependency is a guess at the right line. The acceptance criteria pin the guess, so if it proves wrong in the field the change is visible as a test edit rather than a silent loosening.

**Ordering I am least sure of.** Slice 06 depends on both 01 and 03, which makes it the last thing to unblock despite being conceptually independent. If that becomes the critical path, the egress/retention collection half can be split off and run against 01 alone.
