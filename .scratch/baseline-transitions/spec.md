# Governance baseline transitions

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 15, wave 4)
Source: `PRD.md` §7.5, §6.2, §5.4
Created: 2026-09-11

## Problem Statement

Gantry's quality argument rests on comparing a delivery against its target under identical rules and tool
versions. That works until the delivery's purpose is to change the rules — add a linter, tighten an ADR,
upgrade a tool, extend license policy — at which point the comparison has no common basis and the
governance protection that keeps agents out of `CONSTITUTION.md` and `docs/adr/` blocks exactly the work
that is supposed to touch them.

`PRD.md` identifies both failure modes it must avoid. An unconditional path prohibition would mean
approved governance work can never be done: "an unconditional path prohibition must not prevent the
approved transition". And self-approval would mean a delivery introducing a rule change could use it to
erase its own findings: "do not use the proposed rule change to erase historical findings or
retroactively approve the delivery that introduced it".

Between those, the PRD sets requirements that need a mechanism. A transition must "identify the old and
proposed configurations, compare their evidence where both can run, explain coverage and finding changes,
and receive the applicable operator and gate approvals before the new baseline becomes authoritative".
Where no prior check exists, "record the absence as part of the baseline transition and validate the new
check against representative repository state". Subsequent PBIs use the new baseline while "prior
evidence remains bound to the old one", and in-flight executions require "explicit snapshot migration".
And a spec is not a separate type merely because it changes the baseline — the transition is a property of
work, declared during planning.

Everything mechanical is deferred: "the transition manifest and comparison rules remain to be specified".

## Solution

A baseline transition is a declared property of a PBI, made during planning and approved with the plan. A
PBI carrying it receives an explicit governance-path permission naming the files it may change, which is
what lets the protection in spec 03 stay strict for ordinary assignments while permitting approved
governance work.

The transition produces a manifest: the old configuration, the proposed configuration, a comparison mode
stating whether both, one, or neither of the check versions can run against the repository, and the
evidence obtained under each. Where both run, their findings are compared and the coverage and finding
differences are explained. Where only the new one can run — the common case of adding a check that did not
exist — the absence of a prior check is recorded as part of the transition, and the new check is validated
against representative repository state rather than against a nonexistent baseline.

The delivery that introduces the transition is evaluated under the old rules plus the transition evidence.
It never benefits from the rules it proposes. Once adopted, the new baseline governs subsequent
executions; existing evidence keeps its original binding, and in-flight executions move only through
explicit snapshot migration.

## User Stories

1. As an operator, I want to improve my repository's checks through Gantry, so that quality tooling evolves rather than freezing at adoption.
2. As an operator, I want a rule change declared during planning, so that I know before work starts that governance is being modified.
3. As an operator, I want to approve the transition together with the plan, so that I am not asked twice about the same reviewed proposal.
4. As an operator, I want the PBI doing governance work to be allowed to change those files, so that an unconditional prohibition does not block approved work.
5. As an operator, I want that permission to name the specific files, so that a governance PBI cannot edit arbitrary governance.
6. As an operator, I want ordinary PBIs still unable to touch governance, so that the protection remains meaningful.
7. As an operator, I want the old and proposed configurations both identified, so that I can see exactly what changes.
8. As an operator, I want a comparison of both versions' evidence where both can run, so that I understand the practical effect before adopting.
9. As an operator, I want the coverage difference explained, so that I know what the new check examines that the old one did not.
10. As an operator, I want the finding difference explained, so that I know how many problems the change surfaces or hides.
11. As an operator, I want a check being newly added handled explicitly, so that the absence of a baseline is recorded rather than treated as clean.
12. As an operator, I want a newly added check validated against representative repository state, so that I know it works before it becomes mandatory.
13. As an operator, I want a change that reduces coverage flagged clearly, so that a weakening is visible rather than presented as an improvement.
14. As an operator, I want the transition's own evidence gathered before adoption, so that approval is informed by results rather than intent.
15. As an operator, I want the transition to be able to run the proposed checks before they are authoritative, so that gathering that evidence is possible.
16. As an operator, I want the delivery introducing the change evaluated under the old rules, so that it cannot approve itself.
17. As an operator, I want the change unable to erase historical findings, so that adopting a new rule does not rewrite the past.
18. As an operator, I want prior evidence to keep its original version binding, so that an audit of an old merge still makes sense.
19. As an operator, I want subsequent work to use the new baseline automatically, so that adoption actually takes effect.
20. As an operator, I want in-flight executions unaffected until I migrate them, so that adopting a rule does not change what running work is judged against.
21. As an operator, I want migrating an in-flight execution to be an explicit decision, so that it never happens as a side effect.
22. As an operator, I want a migration to invalidate affected approvals and evidence, so that nothing carries across the rule change unexamined.
23. As an operator, I want a tool version upgrade treated as a baseline transition, so that a silent upgrade cannot invalidate comparisons unnoticed.
24. As an operator, I want a license policy change treated the same way, so that dependency rules evolve under the same discipline.
25. As an operator, I want an ADR change treated the same way, so that architectural rules cannot shift informally.
26. As an operator, I want a transition rejected when its evidence is incomplete, so that adoption requires real results.
27. As an operator, I want a transition that fails its own proposed checks to be blocked, so that a broken new rule is not adopted.
28. As an operator, I want the transition recorded with its approvals and evidence, so that I can explain later why a rule changed.
29. As an operator, I want to abandon a transition without adopting it, so that exploring a change is safe.
30. As an operator, I want an abandoned transition to leave the old baseline authoritative, so that nothing half-applies.
31. As an operator, I want no separate spec type required for governance work, so that a rule change is planned like any other work.
32. As a host harness, I want the manifest and comparison as structured data, so that I can present the decision without parsing text.
33. As an auditor, I want every adoption traceable to its manifest, evidence, and approval, so that a rule's provenance is recoverable.

## Implementation Decisions

### Declaration during planning

A PBI declares a baseline transition as part of the plan:

```ts
type BaselineTransitionDeclaration = {
  pbi: PbiId;
  affects: Array<"check_command" | "tool_version" | "rule_set" | "adr" | "constitution" | "license_policy" | "coverage">;
  governancePaths: string[];            // exactly the files this PBI may change
  rationale: string;
};
```

Declaring it is part of the plan the operator approves in spec 09, so approving the plan approves the
intent to change governance. It does not approve adoption — that is a separate decision after evidence
exists, and the distinction is between "you may attempt this change and show me the results" and "this
change is now authoritative".

The declared `governancePaths` become an explicit permission on assignments for that PBI, which is what
spec 03's governance protection honors. An ordinary assignment carries no such permission, and a
governance PBI's permission is limited to the declared paths — so a transition changing one ADR cannot
edit the constitution.

### The manifest

```ts
type ComparisonMode =
  | { kind: "both_run" }                      // old and new versions both executable against the repository
  | { kind: "new_only"; absenceReason: string }  // the check did not previously exist
  | { kind: "old_only"; reason: string }      // the new version cannot yet run; blocks adoption
  | { kind: "neither" };                      // blocks adoption

type BaselineTransitionManifest = {
  transitionId: string;
  pbi: PbiId;
  oldConfiguration: BaselineConfiguration;    // commands, tool versions, rule sets, coverage declarations
  proposedConfiguration: BaselineConfiguration;
  comparisonMode: ComparisonMode;
  evidence: {
    oldReport?: string;                       // report identity under the old configuration
    newReport?: string;                       // report identity under the proposed configuration
    subjectRevision: string;                  // the representative state both were run against
  };
  coverageChange: {
    added: string[];
    removed: string[];
    unchanged: string[];
    reducesCoverage: boolean;
  };
  findingChange: {
    newlySurfaced: number;
    noLongerSurfaced: number;
    ruleMappings: Array<{ oldRule: string; newRule: string; source: "adapter" | "operator" }>;
    perRuleCounts: Array<{ rule: string; path: string; oldCount: number; newCount: number }>;
  };
  adoption?: { approvedBy: ActorProvenance; adoptedAt: string; newSnapshot: SnapshotId };
};
```

`reducesCoverage` is computed rather than asserted, from the `removed` list and the coverage declarations
of both configurations. A transition that reduces coverage is not forbidden — sometimes a check is wrong —
but it is surfaced prominently, because a weakening presented as an improvement is the failure mode worth
guarding against.

`ruleMappings` handles the one thing a tool upgrade can still break. Since spec 12 derives problem identity
from rule, path, derived symbol, and content anchor — with the message deliberately excluded — a version
that rewords its output no longer disturbs identity at all. What a version *can* change is a rule
identifier: a linter that renames or splits a rule produces findings that look entirely new. That is a
short, enumerable list rather than a per-finding problem, so the adapter supplies the mapping where it
knows one and the operator supplies it otherwise, with the source recorded either way.

`perRuleCounts` is the fallback when no mapping is available for a renamed rule. Comparing counts per
rule and path is weaker than identity matching — it cannot attribute a specific occurrence — but it is a
real signal about whether a change surfaces more or fewer problems, and it is far better than declaring
the comparison void. A transition relying on it says so in the manifest.

### Comparison modes

`both_run` is the strongest case: run both configurations against the same representative revision, compare
findings, and explain the differences.

`new_only` is the common case of adding a check. The absence of a prior check is recorded explicitly — not
as zero findings, which is the trap §7.5 warns about — and the new check is validated against
representative repository state: it must execute, produce parseable evidence, and its findings must be
reviewable before adoption. Whatever it surfaces becomes the preexisting baseline for the differential
policy going forward, not a set of regressions attributed to the PBI that added the check.

`old_only` and `neither` block adoption. A proposed configuration that cannot run against the repository is
not ready to become authoritative.

### Evaluating the introducing delivery

The PBI that introduces a transition is evaluated under the old configuration plus the transition evidence.
Specifically:

- Its own gate decision uses the old baseline. The proposed rules do not judge it.
- The findings its proposed check surfaces do not count as regressions introduced by it.
- The proposed rules cannot clear or reclassify a finding the old rules produce against it.

This is the structural answer to self-approval. The transition may run the proposed checks as evidence
before adoption — which is what makes gathering the evidence possible at all — while the delivery's own
approval remains governed by the rules in force when it started.

### Adoption and effect

Adoption is an operator-only operation referencing a specific manifest, refused when the comparison mode
blocks, when required evidence is incomplete, or when the proposed configuration failed to execute. It
produces a new snapshot per spec 02.

Effect is scoped deliberately:

- New executions capture the new snapshot and use the new baseline.
- Existing evidence keeps its original snapshot binding. An old merge remains explicable under the rules
  that authorized it.
- In-flight executions continue under their captured snapshot and move only through the explicit snapshot
  migration in spec 02, which invalidates affected approvals and returns affected gates to pending.

Historical findings are never rewritten or erased. A rule that no longer exists still explains a decision
that was made under it.

A transition may be abandoned without adoption: the manifest and its evidence are retained as a record of
what was evaluated, and the old baseline remains authoritative.

### Not a separate spec type

Governance work is planned, sliced, approved, implemented, gated, and integrated like any other work. The
transition is a declaration attached to a PBI and a manifest produced during its execution — not a
different document type, a different workflow, or a bypass. The only differences are the governance-path
permission, the manifest requirement, and the evaluation rule above.

## Testing Decisions

**What makes a good test here.** Tests drive a transition end to end through the core — declaration in a
plan, approval, assignment with governance permission, manifest production, adoption or refusal — and
assert on the manifest contents, the permission's scope, which configuration judged the introducing
delivery, and the snapshot binding of evidence before and after adoption.

**The seam.** Unchanged: `core.invoke`. A scripted check adapter provides old and new configuration
reports, including a configuration that fails to execute and one whose identities cannot be mapped.

**Modules under test.** Declaration validation and permission scoping, manifest construction, comparison
mode determination, coverage change computation, finding change and identity mapping, the
old-rules evaluation of the introducing delivery, adoption preconditions and refusals, snapshot effects,
and abandonment.

**Scenarios that must exist**, from PRD §14.3 item 5:

- An ordinary assignment reporting a change to a governance path is a violation; an assignment under a declared transition naming that path is accepted.
- A transition declaring one ADR path cannot change the constitution.
- Approving the plan approves the declaration but not adoption; adoption is a separate operator decision.
- `both_run` produces a comparison against one representative revision with coverage and finding differences.
- `new_only` records the absence of a prior check explicitly and does not treat it as zero findings.
- A newly added check's findings become the preexisting baseline and are not attributed as regressions to the PBI that added it.
- A newly added check that cannot execute or produces unparseable evidence blocks adoption.
- `old_only` and `neither` block adoption.
- A transition that removes coverage computes `reducesCoverage: true` and surfaces it.
- A tool version that rewords its messages without renaming rules produces a full identity-level comparison, with no mapping needed.
- A renamed rule with an adapter-supplied mapping produces a full comparison; the mapping's source is recorded.
- A renamed rule with an operator-supplied mapping does the same, recorded with its source.
- A renamed rule with no mapping falls back to per-rule counts, and the manifest states that it relied on the fallback.
- The introducing delivery's gate decision uses the old configuration.
- Findings surfaced only by the proposed check do not block the introducing delivery.
- The proposed rules cannot clear a finding the old rules produce against the introducing delivery.
- Adoption with incomplete evidence is refused.
- Adoption from a non-operator channel is refused.
- After adoption, a new execution captures the new snapshot; an existing execution continues under its own.
- Evidence produced before adoption retains its original snapshot binding after adoption.
- Migrating an in-flight execution invalidates affected approvals and returns affected gates to pending.
- Historical findings are unchanged by adoption.
- An abandoned transition retains its manifest and leaves the old baseline authoritative.
- No separate spec type or workflow is required: the transition PBI passes through the same states as any other.

## Out of Scope

- **Snapshot capture, identity, and migration mechanics** (spec 02): this spec triggers a new snapshot and an optional migration; spec 02 implements both.
- **Governance path protection enforcement** (spec 03): this spec issues the permission; spec 03 honors it.
- **Operations, approvals, channels, state machine** (spec 01).
- **Check execution, evidence production, identity derivation** (spec 12): this spec compares reports; spec 12 produces them, and the identity instability across tool versions originates there.
- **The differential gate decision** (spec 13): this spec determines which baseline judges a delivery; spec 13 applies it.
- **Plan declaration, approval, and amendment mechanics** (spec 09).
- **Verification command approval and initial tooling preparation** (spec 06): adding a check at onboarding is readiness; changing an adopted one is a transition, and the boundary is adoption.
- **Governance precedence resolution** (spec 02): this spec changes the documents; precedence decides how they interact.
- **Dashboard presentation of manifests** (spec 17).

Out of scope by product decision:

- A separate spec type for governance-changing work. §7.5 states a spec is not a different type merely because it changes the baseline.
- Retroactive application of a new baseline to completed work. §7.5 forbids using a rule change to erase historical findings or retroactively approve a delivery.
- Automatic migration of in-flight executions on adoption. §6.2 requires explicit snapshot migration.
- An unconditional prohibition on changing governance files. §5.4 requires the approved transition path to exist.
- Self-approval of a transition by the delivery that introduces it.

## Further Notes

**Binding decisions.** Nothing here contradicts either ADR, but this spec is the mechanism by which an ADR
can change under discipline. An ADR modified through a transition retains its precedence level 2 through
6 position from spec 02; what the transition governs is whether the change becomes authoritative, not
whether it outranks anything.

**Glossary alignment.** Governance Baseline Transition, Comparison Evidence, and Execution Rule Snapshot
follow `CONTEXT.md`, including what the glossary marks to avoid for the transition: it is not a separate
spec type, not retroactive approval, and not a silent rule change.

**Glossary gap for `/domain-modeling`.** Transition manifest, comparison mode, and coverage change are
introduced here without entries and should get them.

**Where the risk actually sits.** Rule renames are now the only identity hazard a tool upgrade presents,
and the mapping for them is supplied by an adapter or an operator rather than derived. Both sources can be
wrong in the same direction: a plausible-looking mapping between two rules that are not actually the same
check would silently carry a preexisting finding across as though nothing changed, hiding a real coverage
difference. The manifest records the mapping's source, which makes a wrong mapping reviewable, but nothing
validates that two rules are semantically equivalent — and nothing could, short of comparing their
behaviour on representative code, which is what the `both_run` comparison already does at the report level.
Treat an operator-supplied mapping as the weaker of the two.

The second risk is the `new_only` case becoming the norm. Most transitions will add checks rather than
change them, so most transitions will have no baseline to compare against, and the discipline reduces to
"the new check runs and here is what it finds". That is genuinely weaker than a comparison, and the spec
does not dress it up — but recording the absence explicitly is what keeps the resulting findings from
being attributed to the wrong delivery, which is the concrete harm.

**Sequencing note.** This spec depends on spec 13 for the gate and spec 12 for evidence, and it is the
least urgent of wave 4: a repository can run governed execution for a long time without changing its
baseline. The piece worth settling early, though, is the governance-path permission in the declaration,
because spec 03's protection rule references it and would otherwise have to be written twice.
