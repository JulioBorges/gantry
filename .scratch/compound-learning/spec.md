# Compound learning: proposals from execution evidence

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 18, wave 5)
Source: `PRD.md` §9, §10 Phase 5, §7.5
Created: 2026-09-11

## Problem Statement

A factory that makes the same mistake on every slice is a factory that never improves. `PRD.md` assigns
the Compound Learner the job of extracting lessons from Ralph Loop errors and updating `AGENTS.md`, with
one invariant attached: it "submits learnings for formal operator approval via CLI".

Two things make this harder than "write what you learned into a file".

The evidence is deliberately thin. Spec 04 retains references, hashes, and redacted summaries rather than
raw conversation history, tool transcripts, or build logs — which is exactly the material a naive learner
would want to read. So learning has to be built on what is actually retained: gate findings, correction
attempts, protocol failures, handoff memos, integrity findings, and state transitions. That constraint is
a feature rather than an obstacle, because a lesson drawn from a resolvable reference is auditable while a
lesson drawn from a summary of a conversation is a plausible story.

The target matters more than it looks. `AGENTS.md` sits at governance precedence level 6; `CONSTITUTION.md`
is level 3 and applicable ADRs are level 4. A learner permitted to write to any of them could quietly
raise its own output's authority — proposing a rule as an ADR because agents follow ADRs more reliably. And
a change to the constitution or an ADR is a governance baseline transition under spec 15, with its own
manifest and approval, so routing a learning there must go through that path rather than around it.

There is also a smaller failure worth designing against: a learner that reproposes the same rejected
lesson after every PBI becomes noise the operator learns to dismiss, which costs the mechanism its value.

## Solution

`gantry learn-from-pbi` reads the retained evidence for a completed or failed PBI and produces learning
candidates. Each candidate names the observation, cites at least one resolvable evidence reference,
proposes a concrete rule, and names its target document. A candidate without resolvable evidence is not
produced — there is no path from an agent's impression to a proposal.

Targets are constrained by precedence. A candidate targeting the `AGENTS.md` Gantry section is an
operational proposal: it requires operator approval and nothing more. A candidate targeting
`CONSTITUTION.md` or an ADR is converted into a governance baseline transition proposal under spec 15,
which means it needs a manifest, comparative reasoning, and adoption — the learner cannot promote its own
output's authority by choosing a higher-precedence file.

Approval is operator-only and per candidate. An approved candidate is applied only inside the marked
`AGENTS.md` section from spec 06, never to content the operator wrote. A rejected candidate is retained
with its reason and a fingerprint, and an equivalent observation is not reproposed.

Learning never triggers cleanup. Producing proposals reads evidence and preserves artifacts; removing them
is the separate authorization in spec 01.

## User Stories

1. As an operator, I want lessons extracted from what actually went wrong, so that my instructions improve instead of staying static.
2. As an operator, I want each lesson to cite the evidence it came from, so that I can check it rather than trust it.
3. As an operator, I want a lesson with no resolvable evidence not proposed at all, so that I am never shown an agent's impression as a finding.
4. As an operator, I want lessons drawn from gate findings, so that recurring quality problems become instructions.
5. As an operator, I want lessons drawn from correction attempts, so that a slice that took four tries teaches something.
6. As an operator, I want lessons drawn from protocol failures, so that a recurring contract mistake is fixed at the instruction level.
7. As an operator, I want lessons drawn from handoff patterns, so that slices that always need a handoff prompt a decomposition change.
8. As an operator, I want lessons drawn from integrity findings, so that attempts to weaken verification inform my rules.
9. As an operator, I want each proposal to state a concrete rule rather than an observation, so that approving it changes behavior.
10. As an operator, I want each proposal to name its target document, so that I know what I am changing.
11. As an operator, I want a proposal for my operational instructions handled as an ordinary approval, so that small improvements are cheap.
12. As an operator, I want a proposal touching my constitution or an ADR routed through a baseline transition, so that architectural rules do not change casually.
13. As an operator, I want the learner unable to raise its own output's authority by choosing a higher-precedence file, so that precedence means something.
14. As an operator, I want to approve or reject each candidate individually, so that one good lesson is not bundled with three bad ones.
15. As an operator, I want approval to be mine alone, so that an agent cannot record its own lesson as accepted.
16. As an operator, I want an approved change applied only inside the marked section, so that my own instructions are never rewritten.
17. As an operator, I want a rejected candidate retained with my reason, so that the record shows what was considered.
18. As an operator, I want an equivalent observation not reproposed after a rejection, so that the mechanism does not become noise.
19. As an operator, I want to see how often a pattern recurred before it was proposed, so that I can weigh a one-off against a trend.
20. As an operator, I want patterns aggregated across PBIs, so that a problem appearing three times is proposed once with three citations.
21. As an operator, I want learning to read evidence without changing execution state, so that running it is always safe.
22. As an operator, I want learning never to trigger cleanup, so that generating proposals cannot remove anything.
23. As an operator, I want learning to work on a failed PBI as well as a successful one, so that the most instructive runs are not skipped.
24. As an operator, I want proposals to respect redaction, so that a lesson does not quote something that should not have been stored.
25. As an operator, I want the applied section to stay readable, so that accumulated learnings do not become an unusable pile.
26. As an operator, I want to see when a learning was applied and from which PBI, so that I can trace any instruction back to its cause.
27. As an operator, I want to remove a previously applied learning, so that a rule that turned out to be wrong is reversible.
28. As a host harness, I want candidates as structured data, so that I can present them for approval without parsing text.
29. As an auditor, I want every applied learning traceable to its evidence and approval, so that instruction changes are explainable.

## Implementation Decisions

### Candidate shape and evidence requirement

```ts
type LearningCandidate = {
  candidateId: string;
  observation: string;                    // what recurred
  occurrences: Array<{ pbi: PbiId; evidence: EvidenceRef }>;   // at least one, each resolvable
  proposedRule: string;                   // an instruction, not a description
  target:
    | { kind: "agents_section" }          // operational, precedence level 6
    | { kind: "constitution" }            // requires a baseline transition
    | { kind: "adr"; adrPath: string };   // requires a baseline transition
  observationFingerprint: string;         // for deduplication against prior rejections
  sourceKinds: Array<"gate_finding" | "correction_attempt" | "protocol_failure" | "handoff" | "integrity_finding" | "state_transition">;
};
```

`occurrences` must be non-empty and every `EvidenceRef` must resolve under spec 04's replayable reference
rules at the time the candidate is produced. An unresolvable reference disqualifies the occurrence; a
candidate left with none is not produced. This is what keeps proposals grounded in retained evidence
rather than in a narrative.

`proposedRule` is required to be an instruction. A candidate whose proposed rule merely restates the
observation is not useful to approve, so the distinction is enforced as a validation rather than left to
the learner's discretion.

Aggregation happens across PBIs within an execution and, where the repository retains them, across
executions: three occurrences of one observation produce one candidate with three citations rather than
three candidates. `occurrences.length` is shown, because a pattern that happened once and a pattern that
happened five times deserve different scrutiny.

### Target constraint by precedence

The target determines the approval path, and the learner cannot choose freely:

| Target | Path |
|---|---|
| `agents_section` | Operator approval, then applied inside the marked section |
| `constitution` | Converted to a baseline transition proposal under spec 15 |
| `adr` | Converted to a baseline transition proposal under spec 15 |

The conversion is mandatory rather than advisory. A candidate targeting a level 3 or level 4 document
never has a direct application path, so the learner cannot promote its output's authority by choosing a
higher-precedence file. The transition's manifest, comparative reasoning, and adoption apply, which is
considerably more work — appropriately, since it is changing an architectural rule on the basis of
observed execution evidence.

### Approval and application

`learning.approve` and `learning.reject` are operator-only per spec 01's channel rules, and act on one
candidate at a time. An agent-supplied claim of approval is rejected with `operator_channel_required`.

An approved `agents_section` candidate is applied only between the `<!-- gantry:begin -->` and
`<!-- gantry:end -->` markers from spec 06. Content the operator wrote outside those markers is never
touched. Each applied learning carries its provenance — originating PBIs, evidence references, approval
timestamp — so any instruction in the section can be traced to its cause.

Applied learnings can be removed by the operator, with the removal recorded. A rule that seemed right
after one failure and proved wrong later should be reversible without editing around Gantry.

To keep the section usable, applied learnings are grouped and each carries its provenance compactly.
Accumulation without organization would make the section long enough that agents stop reading it
carefully, which would defeat the purpose.

### Deduplication of rejections

A rejection records the operator's reason and the `observationFingerprint`. A later candidate whose
fingerprint matches a rejected one is not produced. The fingerprint is computed over the normalized
observation and the proposed rule's semantic content rather than its wording, so rephrasing does not
bypass the suppression.

A rejected fingerprint can be reconsidered explicitly by the operator — a lesson rejected after one
occurrence may be worth revisiting after ten — but not silently by the learner.

### Backoff and section size

Two self-limiting rules, because the failure mode here is volume rather than error.

**Rejection backoff per source kind.** Acceptance rate is tracked per `sourceKinds` entry. When a source's
rejection rate exceeds a configured threshold over a minimum sample, candidate production from that source
is throttled — fewer occurrences required to propose becomes more, and eventually the source proposes only
on strong recurrence. The throttle is visible and resettable. A mechanism the operator has rejected
fifteen times out of sixteen is producing noise, and continuing to propose from it at full rate trains the
operator to dismiss everything, including the one useful candidate.

**Section size limit.** The marked `AGENTS.md` section has a configured maximum. On reaching it, new
approvals require consolidation first: the operator is shown the existing learnings grouped by theme and
asked to merge or remove before adding. An instructions file long enough that agents skim it is worse than
a short one, so unbounded growth would make this mechanism actively harmful rather than merely unhelpful.

### Read-only with respect to execution

Producing candidates reads retained evidence and writes only candidate records. It changes no execution
state, consumes no budget, and never triggers cleanup. `gantry learn-from-pbi` is therefore safe to run at
any time, including on a failed PBI, which is often the most instructive case and must not be skipped
because it did not integrate.

Candidate text passes through the redaction pipeline like any other output, so a lesson cannot quote
something that should not have been retained.

## Testing Decisions

**What makes a good test here.** Tests seed an execution's retained evidence — findings, correction
records, protocol failures, handoff memos — drive candidate production, approval, and rejection through the
core, and assert on the candidates produced, the approval path taken per target, the resulting
`AGENTS.md` bytes, and the suppression of reproposals. File assertions are limited to the marked section's
content and the byte-identity of everything outside it.

**The seam.** The same seam as spec 01, with a real temporary repository containing an `AGENTS.md` that has
operator-written content outside the markers.

**Modules under test.** Candidate production from each source kind, evidence resolvability enforcement,
aggregation across PBIs, the instruction-versus-observation validation, target routing by precedence,
approval channel enforcement, marked-section application and provenance recording, removal, fingerprinting
and rejection suppression, and read-only behavior.

**Scenarios that must exist:**

- Candidates are produced from gate findings, correction attempts, protocol failures, handoff patterns, and integrity findings, one scenario each.
- A candidate whose only evidence reference no longer resolves is not produced.
- A candidate whose proposed rule merely restates its observation is rejected as invalid.
- Three occurrences of one observation across three PBIs produce one candidate with three citations and an occurrence count of three.
- An `agents_section` candidate is approved and applied between the markers; content outside them is byte-identical afterwards.
- An applied learning records its originating PBIs, evidence references, and approval timestamp.
- A `constitution` candidate has no direct application path and is converted to a baseline transition proposal.
- An `adr` candidate is converted the same way and cannot be applied by approval alone.
- Approval and rejection from a non-operator channel are rejected `operator_channel_required`.
- An agent result asserting approval creates no approval record.
- A rejected candidate is retained with its reason and fingerprint.
- A later candidate with the same fingerprint is not produced; a rephrased version of the same observation is also suppressed.
- An operator can explicitly reconsider a suppressed fingerprint.
- A source kind whose rejection rate passes the threshold over the minimum sample is throttled; the throttle is visible and resettable.
- Throttling raises the occurrence count required to propose rather than silencing the source entirely.
- Reaching the section size limit blocks new approvals until the operator consolidates, and consolidation then permits them.
- An applied learning can be removed, and the removal is recorded.
- Running learning on a failed PBI produces candidates.
- Running learning changes no execution state, consumes no budget, and triggers no cleanup, verified against the projection and an instrumented core.
- Candidate text is redacted.

## Out of Scope

- **Operations, channels, approvals, cleanup authorization** (spec 01).
- **Governance precedence definition** (spec 02): this spec routes by precedence level; spec 02 defines the levels.
- **Baseline transition manifests and adoption** (spec 15): this spec converts a candidate into a transition proposal; spec 15 owns everything after.
- **Marked section mechanics and `AGENTS.md` merging** (spec 06): this spec writes inside the section spec 06 established.
- **Retention and redaction rules** (spec 04): this spec is constrained by what is retained and routes its output through redaction.
- **Finding production, gate decisions, correction accounting** (specs 12, 13): this spec reads their records.
- **Handoff memo construction** (spec 11).
- **Envelope contracts for the compound learner role** (spec 03).
- **Dashboard presentation of candidates** (spec 17).

Out of scope by product decision:

- Self-applying learnings. §9 requires formal operator approval.
- Learning from raw conversation history. Spec 04 does not retain it, and a lesson from an unretained summary is unauditable.
- Direct modification of the constitution or an ADR through the learning path. Those are baseline transitions (§7.5).
- Modifying operator-written content in `AGENTS.md`. §6.3 requires preserving it.
- Cross-repository learning. Learnings are scoped to the repository that produced the evidence.
- Automatic reconsideration of rejected candidates.

## Further Notes

**Binding decisions.** Nothing here contradicts either ADR. The precedence-based target constraint is the
practical consequence of spec 02's ordering: a mechanism that can write to a document also inherits that
document's authority, so limiting where an automated proposal can land is how the ordering stays
meaningful.

**Glossary alignment.** Governance Precedence, Governance Baseline Transition, and Telemetry Retention
follow `CONTEXT.md`. The Compound Learner's responsibility in §9 — "submits learnings for formal operator
approval via CLI" — is implemented as the operator channel rule rather than as a convention.

**Glossary gap for `/domain-modeling`.** Learning candidate, observation fingerprint, and occurrence count
are introduced here without entries and should get them.

**Where the risk actually sits.** The value of this mechanism is unproven, and the spec should say so
rather than assume it. Learning from structured evidence produces reliable but shallow lessons — "this
PBI needed four corrections for the same lint rule" is true and auditable, and the useful instruction it
implies may not follow from the evidence alone. The deep lessons live in the conversation history that is
deliberately not retained. So the honest expectation is that this produces a small number of genuinely
useful operational rules and a larger number of candidates the operator rejects, which is why rejection
suppression matters more than candidate volume.

The second risk was section bloat, and the size limit above converts it from an open-ended problem into a
bounded one — but it relocates the cost rather than removing it. Consolidation is work the operator has to
do at the least convenient moment, when they are trying to approve something else. If that proves
annoying enough, the realistic outcome is the limit being raised rather than consolidation happening,
which returns the original problem. The honest signal to watch is whether the limit is ever raised: if it
is, the mechanism is producing more rules than the operator finds worth organizing, and the answer is
fewer proposals rather than a bigger file.

**Sequencing note.** This spec depends on spec 14 for a completed PBI's full evidence and on spec 15 for
the transition path, making it genuinely last in the pipeline. It is also the most deferrable thing in the
map: the product works without it, and the evidence it reads accumulates whether or not it is built, so
delaying it costs nothing that cannot be recovered later.
