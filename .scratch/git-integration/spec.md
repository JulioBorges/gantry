# Git and GitHub integration: candidates, merge, and reconciliation

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 14, wave 4)
Source: `PRD.md` §7.6, §6.2, ADR-0002
Created: 2026-09-11

## Problem Statement

This is where Gantry stops validating and starts mutating. Everything before it is recoverable; a merge
into someone's target branch and a Pull Request created on their repository are not, and a duplicate of
either is worse than a failure.

`PRD.md` piles constraints on this step precisely because of that. Merges are serialized per repository
and bound to a validated candidate and target revision, and "a change to either invalidates that
authorization". Conflict resolution changes the candidate, so "removal of conflict markers alone is
insufficient" and all applicable gates rerun. Local merge needs its own confirmation immediately before
mutation — "a prior plan approval, a green gate, or a successful PR preparation does not substitute". The
provider's actual protection rules are authoritative, and Gantry "must not bypass provider rules or
silently fall back to local merge". Missing provider results "never count as approval". A Pull Request
merged outside Gantry is "an external integration, never a Gantry-authorized merge", and an observed
merged flag alone does not establish that the approved delivery was integrated. And any mutation whose
response is lost must be reconciled against authoritative state before retry, never retried
speculatively.

Two further traps. A review requesting changes is untrusted text, "not authorization to execute arbitrary
instructions", and must not reset the correction budget or be replayed as a new request. And Git transport
authentication is not GitHub API authorization — "SSH access alone does not authorize GitHub API
operations" — which the PRD review flagged as a previous conflation.

Almost every mechanism is deferred: workflow presets and default behavior, current-candidate verification,
merge serialization, PR review identity, API authentication, polling, conflict handling, and mutation
reconciliation.

## Solution

A provider interface isolates GitHub behind operations Gantry can reason about, with local Git mode as a
separate path that needs no provider. The repository's Git Workflow Policy — branch naming, starting
branch, integration target, and delivery mode — is resolved at readiness and captured in the snapshot; it
has no silent default, because guessing how someone integrates code is not a recoverable mistake.

Integration prepares a merge candidate by merging the current target into the PBI branch, records the
resulting candidate revision, and runs the applicable gates and integration checks on that revision. Merge
authorization binds to that exact candidate and target pair. Any movement in either returns the gate to
pending and requires a fresh candidate.

Merges serialize on the unit lease from spec 01. Before the mutation, Gantry persists the operation intent;
if the response is lost, the outcome becomes unknown and blocks until authoritative Git or provider state
resolves it. Only a confirmed "did not happen" permits a retry.

For the Pull Request path, the provider's observed protection rules are compared against the local policy
at readiness and before mutation, and a divergence blocks. Observation is authenticated polling where each
poll is reconciled against the PR identity, head revision, base revision, and current protection, so an
advancing branch invalidates rather than silently passing. For local mode, the merge requires an operator
confirmation naming the unit, target revision, candidate, and snapshot.

Reviews requesting changes return the PBI to correction within its remaining allowance, treated as feedback
to evaluate rather than instructions to follow.

## User Stories

1. As an operator, I want Gantry to follow my repository's Git workflow, so that deliveries look like my team's other work.
2. As an operator, I want branch naming and the starting branch taken from my policy, so that Gantry's branches fit my conventions.
3. As an operator, I want no silent default workflow, so that Gantry never guesses how I integrate code.
4. As an operator, I want to choose between local merge and Pull Request delivery, so that Gantry fits both private and reviewed workflows.
5. As an operator, I want workflow presets available, so that a common arrangement takes one choice.
6. As an operator, I want the merge candidate prepared against the current target, so that validation reflects what integration will produce.
7. As an operator, I want the candidate revision recorded, so that evidence and authorization are attributable to it.
8. As an operator, I want all applicable gates and integration checks run on the candidate, so that the merged result is what was validated.
9. As an operator, I want merge authorization bound to a specific candidate and target, so that it cannot outlive either.
10. As an operator, I want an advancing target to invalidate authorization, so that a stale approval never merges.
11. As an operator, I want a changed candidate to invalidate authorization, so that any edit is revalidated.
12. As an operator, I want merges serialized per repository, so that two Gantry processes cannot integrate at once.
13. As an operator, I want the target update rejected when the target changed, so that integration never proceeds on stale approval.
14. As an operator, I want conflict resolution attempted within my approved plan, so that mechanical conflicts do not always need me.
15. As an operator, I want a resolution that requires deciding behavior to come to me instead, so that agents do not invent contracts.
16. As an operator, I want any resolution to invalidate prior validation and rerun the gates, so that removing markers is never enough.
17. As an operator, I want resolution attempts to consume my correction allowance, so that conflict loops are bounded like everything else.
18. As an operator, I want no conflict classified as mechanical to skip validation, so that there is no exemption path.
19. As an operator, I want a local merge to require my confirmation immediately before it happens, so that mutating my target is always a conscious act.
20. As an operator, I want that confirmation to name the repository, target revision, candidate, and rule snapshot, so that I know exactly what I am approving.
21. As an operator, I want any change to those to invalidate the confirmation, so that it cannot be reused.
22. As an operator, I want plan approval to authorize Pull Request preparation but not a local merge, so that the two mutation classes stay distinct.
23. As an operator, I want my provider's actual protection rules treated as authoritative, so that local configuration cannot weaken them.
24. As an operator, I want a divergence between my local policy and observed protection to block, so that I reconcile rather than discover it later.
25. As an operator, I want Gantry never to bypass provider rules, so that my branch protection means something.
26. As an operator, I want no silent fallback to local merge when a Pull Request cannot proceed, so that a blocked review is not routed around.
27. As an operator, I want Pull Request checks, reviews, mergeability, and protection polled with my credentials, so that observation reflects reality.
28. As an operator, I want each observation reconciled against the Pull Request identity and revisions, so that an advancing branch invalidates rather than passing.
29. As an operator, I want polling intervals, backoff, and a budget configurable and recorded, so that observation is bounded and auditable.
30. As an operator, I want a reached observation budget to leave the execution waiting, so that it stops rather than polls forever.
31. As an operator, I want a missing update, a timeout, or an unavailable provider never counted as approval, so that silence is never success.
32. As an operator, I want both my local gates and the provider's required checks to pass, so that neither substitutes for the other.
33. As an operator, I want conflicting local and provider results to block until reconciled, so that the disagreement is resolved rather than picked.
34. As an operator, I want pending, missing, or stale provider results treated as not successful, so that timing cannot produce a merge.
35. As an operator, I want my existing authenticated provider credentials used, so that I do not configure a separate key.
36. As an operator, I want Git transport authentication distinguished from API authorization, so that SSH access is not mistaken for permission to call the API.
37. As an operator, I want no credential value stored anywhere by Gantry, so that my configuration and database hold nothing worth stealing.
38. As an operator, I want the identity and authorization scope shown before the first mutation, so that I know which account will act.
39. As an operator, I want to approve that identity before it mutates anything, so that the wrong account cannot act on my behalf.
40. As an operator, I want missing, ambiguous, expired, or insufficient credentials to block, so that a permission problem is explicit.
41. As an operator, I want a review requesting changes to return the slice to correction within its remaining allowance, so that feedback is actionable without resetting anything.
42. As an operator, I want review text treated as feedback to evaluate rather than instructions to execute, so that a comment cannot direct arbitrary work.
43. As an operator, I want a review requesting a behavior change to require a plan amendment, so that scope does not shift through review comments.
44. As an operator, I want a review reconciled against current Pull Request state before acting, so that a superseded review is not replayed.
45. As an operator, I want changes from a review to invalidate prior evidence and rerun both local gates and provider checks, so that the final state is validated.
46. As an operator, I want a Pull Request merged outside Gantry recorded as an external integration, so that the audit trail does not claim Gantry authorized it.
47. As an operator, I want the actually integrated changes reconciled rather than trusting a merged flag, so that dependent work is released only when the delivery is really in.
48. As an operator, I want criteria and dependency readiness verified before dependents are released after an external merge, so that order holds.
49. As an operator, I want a Pull Request closed without merge to pause the slice and preserve its work, so that nothing is discarded or repeated automatically.
50. As an operator, I want the intent of every mutation persisted before it is requested, so that a lost response is recoverable.
51. As an operator, I want an uncertain outcome to block until I or Gantry can consult authoritative state, so that no speculative retry occurs.
52. As an operator, I want a confirmed-completed mutation recorded rather than repeated, so that reconciliation never duplicates a Pull Request or a merge.
53. As an operator, I want release orchestration and branch promotion left alone, so that Gantry integrates without taking over my release process.
54. As a host harness, I want integration exposed as operations with typed rejections, so that I report the real blocking reason.
55. As an auditor, I want every merge traceable to its candidate, target, gates, approvals, and provider evidence, so that any integration is explainable.

## Implementation Decisions

### Git Workflow Policy

```ts
type GitWorkflowPolicy = {
  branchNaming: string;                 // template, e.g. "pbi/{id}" — an example, not a requirement
  startingBranch: string;               // where PBI branches are created from
  integrationTarget: string;            // target branch / PR base
  mode: "local_merge" | "pull_request";
  localChecks?: ApprovedCommandRef[];   // required for local_merge
  providerRequirements?: {              // observed, not declared — see protection authority
    requiredChecks: string[];
    requiredApprovals: number;
  };
};
```

Presets offered at readiness: `trunk-local` (target `main`, local merge), `trunk-pr` (target `main`, Pull
Request), and `develop-pr` (target `develop`, Pull Request). A preset is a starting point and every field
remains adjustable.

There is no silent default. A repository whose operator has not chosen a policy produces a
`needs_decision` readiness item and cannot run governed execution. Guessing whether someone merges locally
or through review is not a recoverable error, so it is the one place where blocking on a question is
better than a sensible default.

### Merge candidate preparation

The candidate is produced by merging the current target revision into the PBI branch, and the resulting
revision is recorded as `candidateRevision`. Merge rather than rebase: rebasing rewrites the micro-commits
and save points that handoff memos and evidence reference, which would invalidate replayable references
from spec 04 for no gain.

History consolidation — squashing the work-in-progress and micro-commit history — is an optional policy
setting rather than a default. When enabled it produces a new `candidateRevision`, which by the
invalidation rule below requires revalidation, so consolidation is never a way to skip a gate.

Gates and integration checks run on `candidateRevision`, not on the PBI branch tip before the merge,
because the merged result is what integration will produce.

### Authorization binding and invalidation

```ts
type MergeAuthorization = {
  unit: RepositoryExecutionUnitId;
  pbi: PbiId;
  targetRevision: string;
  candidateRevision: string;
  snapshot: SnapshotId;
  gateDecision: string;                 // the specific passing decision
  providerEvidence?: ProviderObservation;
  authorizedAt: string;
};
```

Authorization is valid only while `targetRevision` and `candidateRevision` both still hold. A change to
either invalidates it, returns the gate to `pending` per spec 01, and requires a fresh candidate and a
fresh comparison. The target update itself rejects a changed target rather than integrating with stale
approval — checked inside the serialized section, so the window between validation and mutation is closed
by the lease rather than by hope.

Serialization uses the unit-scoped merge lease from spec 01, including across separate Gantry processes.
Its scope is stated: one unit on one machine, not a distributed lock. Changes arriving at a shared remote
from another clone are handled by current-target verification and operation reconciliation, not by the
lease.

### Mutation approval boundary

Plan approval authorizes preparing, creating, and updating Pull Requests under the approved workflow,
subject to provider protection and current validation. It does not authorize a local merge.

`merge.confirmLocal` is operator-only, immediately precedes the mutation, and carries the unit, target
revision, candidate revision, and snapshot identity. Any change to those invalidates it. A green gate, a
prior plan approval, and a successful PR preparation each fail to substitute for it.

### Provider interface and authentication

GitHub is the only provider. All provider behavior sits behind an interface with operations for identity
and access inspection, protection observation, Pull Request creation and update, observation, and merge, so
another provider can be added later without touching the rest of the system. Local mode is a separate
implementation of the integration path that performs no provider operation.

Authentication uses what the environment already has: an authenticated `gh` installation or a token
referenced by an approved environment variable for API operations, and existing SSH or HTTPS credentials
for Git transport. These are distinct: transport access proves nothing about API authorization, and SSH
alone never authorizes an API operation.

```ts
type ProviderIdentity = {
  account: string;                      // login, not a credential
  authMechanism: "gh_cli" | "token_env_ref";
  tokenEnvRef?: string;                 // variable name only
  observedScopes: string[];
  repositoryAccess: "admin" | "write" | "read" | "none";
  observedAt: string;
};
```

No credential value is written to configuration, the database, envelopes, dashboard output, or repository
artifacts. The identity and its scopes are shown and approved before the first mutating provider
operation. Missing, ambiguous, expired, or insufficient credentials block with a typed rejection rather
than being retried.

### Provider protection authority

The target branch's actual protection rules and required checks and approvals are authoritative. They are
observed at readiness and again before mutation, and compared against the local policy and snapshot. A
missing, weaker, or divergent protection blocks until the operator adjusts the policy or the provider
configuration, after which affected validations rerun.

Local configuration cannot compensate for weaker provider protection, Gantry never bypasses a provider
rule, and there is no fallback to local merge when the Pull Request path is blocked.

### Pull Request observation

```ts
type PullRequestIdentity = {
  repository: string;
  number: number;
  headRevision: string;                 // must equal candidateRevision
  baseRef: string;
  baseRevision: string;                 // must equal targetRevision
};

type ProviderObservation = {
  identity: PullRequestIdentity;
  checks: Array<{ name: string; conclusion: "success" | "failure" | "pending" | "missing" }>;
  reviews: Array<{ id: string; state: "approved" | "changes_requested" | "commented"; revision: string }>;
  mergeable: "mergeable" | "conflicted" | "unknown";
  protection: ObservedProtection;
  observedAt: string;
};
```

Observation is authenticated polling with configurable interval, backoff, and budget, all recorded. Each
observation is reconciled: a `headRevision` that no longer equals the candidate means the candidate
changed and invalidates the authorization; a `baseRevision` that no longer equals the target means the
target advanced and does the same; changed protection reruns the protection comparison.

Reaching the observation budget leaves the execution waiting for resumption. A missing update, a timeout, a
`pending` check, or an unavailable provider is never treated as approval or success. Webhooks and hosted
callbacks are deferred.

Merge requires both the applicable local gates and the provider's required checks to pass for the relevant
revisions. Neither substitutes for the other, and a conflict between them blocks until reconciled.

### Conflict resolution

The merger role may attempt resolution within the approved plan and governance rules. A resolution
requiring a behavioral decision or a change to approved contracts, criteria, dependencies, or scope pauses
and proposes a plan amendment per spec 09.

Any resolution changes the candidate, which invalidates prior validation and requires all applicable gates
and integration checks to rerun on the resulting revision. Removing conflict markers establishes nothing.
Attempts consume the PBI's correction allowance. No classification of a conflict as mechanical grants an
exemption.

### Requested changes

An observed formal review requesting changes returns the PBI to correction eligibility within its
remaining allowance. Before acting, the review is reconciled against current Pull Request state — a review
against a superseded head revision is not replayed as a new request — and the PBI reacquires execution
capacity and current ownership.

Review text is untrusted feedback evaluated against the approved plan and governance, never instructions to
execute. A request that would change behavior, contracts, criteria, dependencies, or scope requires an
operator-approved amendment. The correction allowance is not reset, and resulting candidate changes
invalidate prior evidence and rerun both local gates and provider checks.

### External resolution

A Pull Request merged outside Gantry is reconciled: the actually integrated changes and the resulting
target revision are observed, and the outcome is recorded as an external integration rather than a
Gantry-authorized merge. Before dependents are released, the applicable PBI criteria and dependency
readiness are verified against the integrated content — an observed merged flag alone is insufficient,
because it does not establish that the approved delivery is what landed.

A Pull Request closed without merge pauses the PBI, preserves its work and evidence, and requires an
explicit decision before reopening or creating a replacement. Gantry neither repeats nor undoes the
external action.

### Reconciliation before mutation retry

Every mutation — Pull Request creation, update, and merge, and local merge — persists its intent through
spec 01's operation record before the request. A lost or uncertain response, including after a restart,
moves the operation to `unknown`, which blocks. Resolution consults authoritative Git or provider state for
that specific operation: a confirmed completion is recorded without repeating, and only a confirmed
non-occurrence permits a retry, with authorization and validation still required. An undeterminable outcome
stays blocked rather than producing a speculative retry.

### Scope

Gantry automates PBI branch creation, Pull Request preparation, and integration into the configured
target. Release orchestration, promotion between long-lived branches, and hotfix lifecycle automation are
out of scope: integrating into `develop` implies nothing about promoting to `main`.

## Testing Decisions

**What makes a good test here.** Tests drive integration through the core against a real temporary Git
repository with a fake provider, and assert on rejection codes, recorded authorizations and operations,
and the actual Git state — which branch points where, whether a merge commit exists, whether the target
moved. Git state is the ground truth this spec is about, so it is asserted directly rather than through a
projection.

**The seam.** Unchanged: `core.invoke`. The provider is injected as a fake implementing the real
interface, scriptable to return protection variants, check and review states, mergeability, lost
responses, and externally changed state. Local mode uses real Git with no provider.

The fake provider is essential rather than incidental: the cases that matter — a lost merge response, a
base revision advancing between observation and merge, a review against a superseded head — cannot be
produced reliably against a real GitHub, and provoking them against a real repository would mean mutating
one.

Provider conformance against real GitHub.com and GitHub Enterprise is a separate suite like spec 10's,
recorded in the support matrix, skipped with an explicit reason when credentials are absent.

**Modules under test.** Policy resolution and presets, candidate preparation and revision recording,
authorization binding and invalidation, serialized integration under the lease, the mutation approval
boundary, provider identity and scope inspection, protection observation and divergence blocking,
observation reconciliation and budget behavior, local-and-provider validation conjunction, conflict
resolution effects, requested-changes handling, external resolution reconciliation, and mutation intent
and reconciliation.

**Scenarios that must exist**, from PRD §14.3 items 7 and 8:

- A repository with no chosen workflow policy produces `needs_decision` and cannot run governed execution.
- Each preset resolves to a valid policy, and every field remains adjustable.
- A candidate is produced by merging the current target into the PBI branch, and its revision is recorded; micro-commits and save points remain reachable.
- Gates run on the candidate revision, not on the pre-merge branch tip.
- Enabling history consolidation produces a new candidate revision and requires revalidation.
- A target advancing after authorization invalidates it and returns the gate to `pending`.
- A candidate edit after authorization invalidates it.
- The target update inside the serialized section rejects a changed target rather than integrating.
- Two processes attempting integration in one unit serialize; the loser is rejected `lock_unavailable` or revalidates.
- `merge.confirmLocal` is required immediately before a local merge; a green gate, a plan approval, and a successful PR preparation each fail to substitute.
- A confirmation naming a stale target revision, candidate, or snapshot is rejected.
- `merge.confirmLocal` from a non-operator channel is rejected.
- Plan approval alone authorizes Pull Request creation and update but not a local merge.
- Provider identity and scopes are shown and approved before the first mutating operation; an unapproved identity blocks it.
- SSH transport access alone does not authorize an API operation.
- No credential value appears in configuration, the database, envelopes, or projections.
- Missing, expired, and insufficient credentials each block with a typed rejection and no retry.
- Observed protection weaker than the local policy blocks; adjusting the policy reruns affected validations.
- A protection change observed before mutation blocks until reconciled.
- No path falls back to local merge when the Pull Request path is blocked.
- An observation whose `headRevision` differs from the candidate invalidates authorization; one whose `baseRevision` differs from the target does the same.
- A `pending` required check, a missing check, a timeout, and an unavailable provider each fail to authorize merge.
- Reaching the observation budget leaves the execution waiting, not failed or approved.
- Local gates passing with a failing provider check does not merge, and the reverse does not either; conflicting results block.
- Conflict resolution changes the candidate, invalidates prior validation, and reruns all applicable gates; removing markers alone does not authorize.
- A resolution attempt consumes one correction attempt; a resolution requiring a behavioral decision proposes an amendment instead.
- A review requesting changes returns the PBI to correction within the remaining allowance without resetting it.
- A review against a superseded head revision is not replayed as a new correction request.
- Review text requesting a behavior change produces an amendment requirement rather than direct work.
- Changes from a review invalidate prior evidence and rerun local gates and provider checks.
- A Pull Request merged externally is recorded as an external integration, and dependents are released only after criteria and dependency readiness are verified against the integrated content.
- A merged flag with content that does not match the approved delivery does not release dependents.
- A Pull Request closed without merge pauses the PBI, preserves its work, and requires an explicit decision.
- A lost merge response produces an `unknown` operation that blocks; reconciliation to completed records the outcome without repeating, and to not-performed permits exactly one retry.
- A restart between intent and response leaves a reconcilable intent.
- No release promotion or hotfix automation is attempted.

## Out of Scope

- **Operations, leases, intent records, reconciliation mechanics, cleanup** (spec 01) and **policy schema validation and snapshot capture** (spec 02).
- **Envelope contracts and the merger role payload** (spec 03).
- **Redaction of provider output** (spec 04).
- **Policy collection at readiness and provider readiness items** (spec 06): this spec produces the provider observations that readiness reports.
- **Dependency readiness definition, plan amendments** (spec 09): this spec triggers amendments and consumes readiness.
- **Worktree and branch creation, micro-commits, save points** (spec 11): this spec consumes the branch and decides how its history becomes a candidate.
- **Check execution** (spec 12) and **the gate decision** (spec 13): a passing gate is a precondition here.
- **Baseline transitions** (spec 15).
- **Dashboard presentation of review state and confirmations** (spec 17).

Out of scope by product decision:

- Providers other than GitHub. GitLab, Bitbucket, and Azure DevOps are deferred (§6.2), and unsupported providers must not be presented as operational choices.
- Webhooks and externally hosted callbacks. Deferred in favor of authenticated polling (§6.2).
- Release orchestration, promotion between long-lived branches, and hotfix lifecycle automation (§6.2).
- Stacked branches and stacked Pull Requests (§4.2).
- A distributed merge lock across clones or machines. Serialization is unit-scoped (§8.1, ADR-0002).
- Rebasing to produce a candidate. It would rewrite revisions that retained evidence references.

## Further Notes

**Binding decisions.** ADR-0002 is implemented here: serialized integration, candidate validation against
the current target, and invalidation whenever the candidate or target changes. The ADR's stated cost —
repeated validation as the target advances — is accepted rather than optimized away, and the merge-not-rebase
decision follows from it, since the candidate must be a revision that evidence can point at.

**Glossary alignment.** Merge Candidate, Merge Authorization, Git Workflow Policy, Provider Identity,
Provider Protection Authority, Pull Request Observation, Mutation Approval Boundary, and Operation
Reconciliation follow `CONTEXT.md`, including the terms it marks to avoid: a merge candidate is not an
approved PBI branch; merge authorization is not implementation completion; provider identity is not a
credential value or repository-wide authority; protection authority is not a local policy override or
assumed protection; observation is not webhook delivery or stale approval; the approval boundary is not
generic execution approval; reconciliation is not a blind retry.

**Glossary gap for `/domain-modeling`.** Candidate preparation, observation budget, and external
integration are introduced here without entries and should get them.

**Where the risk actually sits.** The window between validating a candidate and mutating the target is the
one place where correctness depends on timing rather than structure. The lease closes it for other Gantry
processes in the same unit, and the in-section target check closes it for changes that arrive before the
mutation. What remains open is a change arriving at a shared remote from another clone or another person
between the last observation and the merge — which the provider itself rejects for a Pull Request through
its own mergeability and protection enforcement, but which local mode can only detect by re-verifying the
target immediately before the merge. That re-verification is required above, and the residual race is
stated rather than claimed closed: local mode against a shared remote is inherently weaker than the Pull
Request path, and operators choosing it should know that.

The second risk is external integration content matching. Verifying that "the approved delivery is what
landed" means comparing integrated content against the candidate, and a squash merge or an
administrator's edit changes the revision while preserving the intent. The rule above requires verifying
criteria and dependency readiness rather than revision equality, which is the honest version: Gantry can
confirm that the criteria hold on the integrated target, not that the exact candidate was merged.

**Sequencing note.** This spec depends on spec 13 for the gate and on spec 11 for the branch, and it is
the last piece of the core pipeline. The authorization binding and its invalidation rule are the piece to
settle first, because every other decision in this spec is a consequence of it.
