# Vertical slicing, context budget, and planning approval

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 09, wave 2)
Source: `PRD.md` §4.2, §7.3, §7.2
Created: 2026-09-11

## Problem Statement

`PRD.md` names ineffective horizontal slicing as one of the five bottlenecks: splitting work
layer by layer forces the whole application into an agent's context and produces colossal diffs. The
answer is vertical slices, each delivering a narrow complete behavior with an estimated initial context
package under fifteen percent of the model's window.

Three things make that answer hard to implement honestly.

The budget is an estimate, and the PRD is insistent about not dressing it up: "record the estimation
method, assumed window, and uncertainty margin; distinguish estimates from observed usage", and "this
is a planning budget, not a claim of exact runtime measurement". A system reporting a clean fifteen
percent with no method and no margin would be fabricating precision. The mechanism — "token estimation
and uncertainty calculation remain to be specified" — is open.

Dependencies are stricter than they look. A dependent PBI cannot start until every prerequisite is
*integrated into the applicable target*, and the PRD spells out what does not count: "completed
implementation, green gates, or an open PR alone do not satisfy a dependency". Stacked branches and
stacked PRs are out of scope, so there is no mechanism to lean on. "Dependency schema and validation
rules remain to be specified."

And the whole plan needs a human yes. The PRD requires explicit operator approval of both spec and
breakdown before AFK execution, states that "passing automated checks does not replace this approval",
and requires that approval reference the concrete version reviewed — because an agent asserting
`approved: true` is not evidence. Changes afterwards need renewed approval, with internal
implementation choices excluded. "Approval commands and persistence schema" and "amendment
representation and impact tracking" are both deferred.

The failure mode if any of these is loose: a breakdown that lints clean, was never actually approved,
carries an unmeasured context estimate, and starts a dependent slice against a base that lacks its
prerequisite.

## Solution

`gantry slice-spec` proposes PBIs from a technically ready spec, each with a verifiable behavior,
identified acceptance criteria carried forward from the spec, explicit prerequisites, the user stories
it covers, and a context estimate. `gantry lint-pbi` evaluates declared rules against each PBI, with
file count as a warning that triggers decomposition review rather than an automatic rejection.

The context estimate is computed component by component with a declared tokenizer against the
configured model's nominal window, and it carries an uncertainty margin. The comparison against the
budget uses the upper bound, so a slice near the limit is reduced rather than optimistically accepted.
Estimates and observed usage are separate fields everywhere they appear, so one is never read as the
other.

Dependencies form a validated acyclic graph. Dependency Readiness is evaluated at dispatch against
actual integration state — the prerequisite's changes present in the dependent's starting base — not
against a status anyone recorded.

Planning approval is one operator decision over a plan version identified by the content of the spec
and the whole PBI set. Any later change is classified: behavioral changes produce an amendment
requiring renewed approval, and internal implementation choices proceed. An amendment retains the prior
version and invalidates the validations its changes affect.

## User Stories

1. As an operator, I want slices that each deliver a complete narrow behavior, so that every merge is independently valuable.
2. As an operator, I want slicing to span the layers a feature actually touches, so that I get working behavior rather than a layer.
3. As an operator, I want no architecture imposed on my slices, so that a tooling change is not forced into a route-to-repository shape.
4. As an operator, I want each PBI to carry acceptance criteria with stable identifiers, so that later verification refers to specific criteria.
5. As an operator, I want criteria carried forward from the spec rather than reinvented, so that the plan and the spec cannot drift apart.
6. As an operator, I want each PBI to declare deterministic local verification, so that "done" has a command behind it.
7. As an operator, I want a PBI with no verification definition rejected, so that unverifiable work never enters the backlog.
8. As an operator, I want test duration never used to reject a slice, so that slow but correct verification is allowed.
9. As an operator, I want a PBI touching many files to trigger a decomposition review rather than automatic rejection, so that I am not forced into artificial splits.
10. As an operator, I want the file count threshold visible in the warning, so that I understand why review was triggered.
11. As an operator, I want each PBI's initial context package estimated, so that I know before dispatch whether a slice is too big.
12. As an operator, I want the estimate broken down by component, so that I can see what is consuming the budget.
13. As an operator, I want the tokenizer and assumed model window recorded, so that the estimate is reproducible.
14. As an operator, I want an uncertainty margin recorded, so that the estimate is honest about being an estimate.
15. As an operator, I want the budget compared against the upper bound of the estimate, so that a slice near the limit is reduced rather than optimistically accepted.
16. As an operator, I want an over-budget slice to require reduction and reassessment before approval, so that the budget has teeth.
17. As an operator, I want estimates and observed usage shown as separate values, so that I never read one as the other.
18. As an operator, I want the same budget applied to a replacement agent after a handoff, so that continuity work is bounded like any start.
19. As an operator, I want a package that cannot fit the budget without dropping mandatory content to pause for review, so that nothing required is silently omitted.
20. As an operator, I want each PBI to declare its prerequisites explicitly, so that order is stated rather than inferred.
21. As an operator, I want the dependency graph validated as acyclic, so that a cycle is caught at planning rather than at dispatch.
22. As an operator, I want a prerequisite referencing a nonexistent PBI rejected, so that the graph is always resolvable.
23. As an operator, I want a self-dependency rejected, so that an obvious mistake is caught immediately.
24. As an operator, I want dependency readiness to require actual integration into the applicable target, so that an open PR does not release dependent work.
25. As an operator, I want completed implementation and green gates alone not to satisfy a dependency, so that readiness means integrated.
26. As an operator, I want the dependent's starting base verified to include the prerequisite's integration, so that it does not start from a stale base.
27. As an operator, I want waiting on a prerequisite represented as a scheduling state, so that it is not confused with an agent being blocked.
28. As an operator, I want only dependency-ready PBIs eligible for parallel work, so that parallelism never violates order.
29. As an operator, I want to see the story coverage map, so that I can tell whether the breakdown covers what the spec promised.
30. As an operator, I want an uncovered user story flagged, so that a breakdown cannot quietly drop scope.
31. As an operator, I want a PBI covering no story flagged, so that work without a stated purpose is questioned.
32. As an operator, I want to approve the spec and the breakdown together in one explicit decision, so that consent covers the whole plan.
33. As an operator, I want approval to cover behavior, story coverage, granularity, and dependencies, so that I am approving the plan rather than a document's existence.
34. As an operator, I want approval bound to the exact plan version I reviewed, so that a later edit does not inherit my consent.
35. As an operator, I want an agent's claim of my approval rejected, so that approval means my decision.
36. As an operator, I want lint success unable to substitute for approval, so that automated checks never authorize execution.
37. As an operator, I want builder dispatch refused without a recorded approval, so that AFK work cannot start on an unapproved plan.
38. As an operator, I want a change to approved behavior, criteria, contracts, dependencies, or decomposition to require my renewed approval, so that scope cannot shift silently.
39. As an operator, I want internal implementation choices to proceed without asking me, so that I am not consulted about things that preserve the plan.
40. As an operator, I want the classification of a change into behavioral or internal to be explicit and recorded, so that the boundary is auditable rather than judgment I cannot see.
41. As an operator, I want an amendment proposed to me rather than applied, so that agents never edit the approved plan themselves.
42. As an operator, I want the prior plan version retained after an amendment, so that history shows what changed.
43. As an operator, I want an amendment to invalidate and rerun the validations its changes affect, so that approval is never carried across a change.
44. As an operator, I want unaffected work to continue during an amendment, so that one change does not stall everything.
45. As an operator, I want approval recorded with its snapshot, so that I know which rules governed the plan I approved.
46. As a host harness, I want the proposal, coverage map, estimates, and dependency graph as structured data, so that I can present them for approval without parsing text.
47. As a host harness, I want a dispatch rejection to name the unmet prerequisite, so that I report the real reason.
48. As an auditor, I want every dispatch traceable to an approved plan version, so that no work exists outside the plan.

## Implementation Decisions

### PBI shape

```ts
type ProposedPbi = {
  id: PbiId;
  behavior: string;                       // the complete narrow behavior delivered
  criteria: Array<{ id: string; text: string; specCriterionId: string }>;
  verification: Array<{ command: ApprovedCommandRef; expectedOutcome: string; coversCriteria: string[] }>;
  prerequisites: PbiId[];
  storyCoverage: string[];                // spec user story identifiers
  contextEstimate: ContextEstimate;
  scopeHint: { estimatedFiles: number; paths: string[] };
};
```

Criterion identifiers trace to the spec's criterion identifiers from spec 08 rather than being
reinvented, so plan and spec cannot drift. Every criterion must be covered by at least one verification
entry; a criterion with no covering command is a lint failure, because that is the gap where "all
criteria completed" becomes unverifiable.

### Lint rules

| Rule | Severity | Requirement |
|---|---|---|
| `PBI-BEHAVIOR` | blocker | A single complete verifiable behavior is stated |
| `PBI-CRITERIA-ID` | blocker | Every criterion has a stable identifier tracing to the spec |
| `PBI-VERIFICATION` | blocker | Deterministic local verification is defined |
| `PBI-CRITERIA-COVERED` | blocker | Every criterion is covered by at least one verification entry |
| `PBI-BUDGET` | blocker | The context estimate's upper bound is within the configured budget |
| `PBI-DEPS-RESOLVABLE` | blocker | Every prerequisite exists; no self-dependency; the graph is acyclic |
| `PBI-STORY-COVERAGE` | blocker | The PBI covers at least one user story |
| `PBI-FILE-COUNT` | warning | Estimated file count within the threshold |

`PBI-FILE-COUNT` is the only warning, and deliberately: exceeding five files triggers a decomposition
review without forcing an artificial split, per §7.3. Test duration is not a rule at all — there is no
ten-second limit, and the PRD removed it explicitly.

At the breakdown level, two further rules apply across all PBIs: every approved user story is covered by
at least one PBI, and the dependency graph is acyclic as a whole.

### Context estimation

```ts
type ContextEstimate = {
  tokenizer: { id: string; version: string };
  assumedWindow: { model: string; tokens: number };
  components: Array<{
    kind: "instructions" | "spec" | "pbi" | "contracts" | "governance" | "source_files" | "continuity" | "other";
    tokens: number;
    basis: "counted" | "sampled" | "declared";
  }>;
  totalTokens: number;
  uncertaintyMargin: number;              // fraction, e.g. 0.2
  upperBoundFraction: number;             // (totalTokens * (1 + margin)) / assumedWindow.tokens
  method: string;
};
```

Components are counted with the declared tokenizer where content is known — instructions, spec and PBI
text, contracts, governance documents — and `sampled` or `declared` where it is not, such as source
files the builder may open. The basis is recorded per component so an operator can see which parts are
counted and which are guessed.

`PBI-BUDGET` compares `upperBoundFraction` against the configured budget, defaulting to fifteen percent.
Using the upper bound rather than the point estimate is the decision that makes the margin meaningful
instead of decorative.

The same estimate and budget apply to a replacement agent's package after a handoff, including the
handoff memo, per §4.3. There is no separate smaller allowance for continuity. When a package cannot fit
the budget without dropping mandatory content — contracts, criteria, governance — the work pauses for
context or decomposition review rather than dropping anything.

Estimates are never presented as observed usage. The projection carries both fields, and the observed
field is `unknown` until an integration reports a measurement, per spec 03.

### Dependencies and readiness

Prerequisites are PBI identifiers within the same plan. The graph is validated at lint time for
resolvability, self-reference, and acyclicity.

Dependency Readiness is evaluated at dispatch, not recorded at planning:

- Every prerequisite's state is `integrated` or `externally_integrated`.
- The dependent's starting base actually contains each prerequisite's integrated changes, verified
  against Git rather than against a status field.

Both conditions are required. The second exists because the first can be true while the dependent's base
predates the integration, which is exactly the stale-base failure §4.2 warns about. An unmet
prerequisite produces `dependency_not_ready` and the PBI sits in `awaiting_dependency` — a scheduling
state, not `awaiting_operator`.

Stacked branches and stacked PRs are out of scope for v4, so a dependent always starts from an updated
base that includes its prerequisites, under the repository's Git workflow policy.

### Plan version and approval

```ts
type PlanVersion = {
  id: PlanVersionId;                      // hash over spec content hash + ordered PBI content hashes + dependency graph
  specContentHash: string;
  pbis: Array<{ id: PbiId; contentHash: string }>;
  dependencyGraph: Array<[PbiId, PbiId]>;
  storyCoverage: Record<string, PbiId[]>;
  supersedes?: PlanVersionId;
  snapshot: SnapshotId;
};
```

`plan.approve` is operator-only through the channel rules in spec 01, references a specific
`PlanVersionId`, and records the actor provenance, channel, and snapshot. An agent-supplied approval
claim is rejected with `operator_channel_required`; a stale version is rejected with
`approval_version_mismatch`. Builder dispatch requires a recorded approval for the current plan version,
so lint success alone never authorizes work.

Approval covers behavior, story coverage, granularity, and dependencies — the four things §7.2 names —
and the approval record stores the proposal as presented, so an audit can show what the operator saw.

### Amendments

A proposed change is classified before anything happens:

```ts
type PlanChange =
  | { kind: "behavioral"; affects: Array<"behavior" | "criteria" | "contracts" | "dependencies" | "decomposition">; affectedPbis: PbiId[] }
  | { kind: "internal"; rationale: string; preserves: PlanInvariants };
```

`behavioral` requires `plan.amend`, operator-only, producing a new plan version with `supersedes` set.
The prior version is retained. Validations affected by the change are invalidated and rerun: readiness
for a changed spec, lint for changed PBIs, gate results for PBIs whose criteria or contracts changed.
Unaffected PBIs continue, so one amendment does not stall the execution.

`internal` proceeds automatically only when it preserves approved behavior, contracts, criteria,
dependencies, and decomposition, and complies with the execution's governance rules. The classification
is recorded with its rationale, so the boundary is auditable rather than an invisible judgment. An agent
proposes; it never edits the approved plan directly.

## Testing Decisions

**What makes a good test here.** Tests drive slicing, linting, approval, dispatch, and amendment through
the core against real temporary repositories, and assert on failed rule identities, estimate fields,
rejection codes, plan version identities, and which validations were invalidated. Estimates are asserted
structurally — that components, tokenizer, window, margin, and upper bound are present and that the
budget comparison uses the upper bound — rather than on exact token counts, which would make the tests a
tokenizer snapshot.

**The seam.** The same seam as spec 01, with a fake harness driver scripted to return slicer results,
including proposals that are over budget, cyclic, self-referential, missing verification, and leaving a
story uncovered. A deterministic stub tokenizer is injected so estimate assertions are stable.

**Modules under test.** PBI shape validation, each lint rule, breakdown-level coverage and graph rules,
context estimation and its budget comparison, dependency graph validation, dependency readiness
evaluation at dispatch, plan version identity, approval channel and version binding, dispatch gating on
approval, and change classification and amendment effects.

**Scenarios that must exist**, from PRD §14.3 items 3 and 4:

- A PBI whose criteria do not trace to spec criterion identifiers fails `PBI-CRITERIA-ID`.
- A criterion with no covering verification entry fails `PBI-CRITERIA-COVERED`.
- A PBI with no verification definition fails `PBI-VERIFICATION`.
- A PBI with slow but defined verification passes; no rule references test duration.
- A PBI touching seven files produces the `PBI-FILE-COUNT` warning, passes lint, and can be approved.
- An estimate whose point value is under budget but whose upper bound exceeds it fails `PBI-BUDGET`.
- An estimate records tokenizer, window, per-component basis, margin, and method; a component without a basis is invalid.
- A handoff package including the memo is evaluated against the same budget, with no separate allowance.
- A package that cannot fit without dropping contracts, criteria, or governance pauses for review rather than dropping them.
- The projection shows estimated and observed context as separate fields, with observed `unknown` before any measurement.
- A cyclic graph, a self-dependency, and a prerequisite referencing a nonexistent PBI each fail `PBI-DEPS-RESOLVABLE`.
- A breakdown leaving an approved user story uncovered fails the breakdown-level coverage rule; a PBI covering no story fails `PBI-STORY-COVERAGE`.
- Dispatch of a dependent whose prerequisite is `implementation_complete` is rejected `dependency_not_ready`.
- Dispatch of a dependent whose prerequisite has passing gates and an open PR is rejected.
- Dispatch of a dependent whose prerequisite is `integrated` but whose starting base predates the integration is rejected.
- Dispatch succeeds once the prerequisite is integrated and the base contains it; the PBI waits in `awaiting_dependency` until then, never in `awaiting_operator`.
- Two dependency-ready PBIs can run in parallel; a dependent cannot.
- `plan.approve` from an MCP channel is rejected `operator_channel_required`.
- An agent result asserting approval does not create an approval record.
- Approving a stale plan version is rejected `approval_version_mismatch`.
- Builder dispatch without a recorded approval for the current plan version is rejected; passing lint does not satisfy it.
- Editing a PBI's criteria after approval produces a new plan version identity and invalidates the approval.
- A behavioral change requires `plan.amend`, retains the prior version, invalidates and reruns affected validations, and leaves unaffected PBIs running.
- An internal change proceeds automatically and records its classification and rationale.
- An agent attempting to edit the approved plan directly is rejected; only a proposal is accepted.

## Out of Scope

- **Operations, state machine, channels, ownership, budgets** (spec 01) and **snapshot and limit values** (spec 02).
- **Envelope contracts** (spec 03): the slicer role's payload shape and result validation. This spec defines what the payload must contain semantically.
- **Spec structural validation and requirement review** (spec 08): technical readiness is this spec's precondition, and criterion identifiers originate there.
- **Worktree creation, scheduling, capacity, and the build loop** (spec 11): this spec decides eligibility; spec 11 acts on it.
- **Check execution and approved command definitions** (spec 12): this spec references approved commands; spec 12 runs them.
- **Gate decisions and correction** (spec 13): this spec's amendments invalidate gate results; the gate logic is elsewhere.
- **Git workflow policy, branch bases, and integration** (spec 14): "the applicable target" and how a base is updated are resolved there; this spec consumes the result when evaluating readiness.
- **Dashboard presentation of proposals and approvals** (spec 17).

Out of scope by product decision:

- Stacked branches and stacked Pull Requests. Explicitly deferred in §4.2.
- A mandatory layer sequence for slices. §4.2 calls route-to-repository an example, not a requirement.
- A file count ceiling that rejects. §7.3 makes it a warning.
- A test duration limit. §4.2 removed the ten-second rule explicitly.
- Claiming measured context usage from an estimate. §13.2 forbids reporting estimates as observed runtime usage.

## Further Notes

**Binding decisions.** ADR-0002 is why dependency readiness is evaluated against Git rather than status:
with serialized integration and no stacked branches, the only honest question is whether the
prerequisite's changes are actually in the dependent's base.

**Glossary alignment.** Initial Context Budget, PBI Dependency, Dependency Readiness, Planning Approval,
and Plan Amendment follow `CONTEXT.md`, including the terms it marks to avoid: the budget is not a
source-file count and not measured runtime usage; a dependency is not a suggested execution order;
readiness is not implementation completion and not an agent-reported blocked result; planning approval is
not lint success, requirement review, or Pull Request approval; an amendment is not an internal
implementation choice.

**Glossary gap for `/domain-modeling`.** Plan version, story coverage map, and change classification are
introduced here without entries and should get them.

**Where the risk actually sits.** The behavioral-versus-internal classification is the judgment this spec
cannot fully mechanize. The rule stated above — internal only when behavior, contracts, criteria,
dependencies, and decomposition are all preserved — is checkable for contracts, criteria, dependencies,
and decomposition, since those are recorded and hashable. "Preserves behavior" is not. The mitigation is
that the classification is recorded with a rationale and visible to the operator, so a wrong
classification is discoverable rather than invisible, and the asymmetry is deliberate: misclassifying a
behavioral change as internal is the harmful direction, so anything touching a recorded artifact is
behavioral by default and only genuinely internal work qualifies.

The second risk is estimation accuracy for `source_files`, the one component whose content is unknown at
planning time. It is `sampled` or `declared` rather than counted, which means the margin is doing real
work there. Calibrating the default margin against observed usage once spec 10 can report measurements is
the follow-up that makes the budget trustworthy rather than merely honest.

**Sequencing note.** This spec depends on spec 08 for criterion identifiers and on spec 14's notion of
"the applicable target" for readiness evaluation. Approval and plan version identity are what spec 11
gates dispatch on, so the plan version hash definition is the piece to settle first.
