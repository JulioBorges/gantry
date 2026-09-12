# GTP v1: task and result contracts

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 03, wave 0)
Source: `PRD.md` §5, §4.1
Created: 2026-09-11

## Problem Statement

An operator running agents through a harness has no reliable way to know what an agent actually did.
Today the only channel is free-form stdout and an exit code, so "the build passed" and "the agent
believes the build passed" are indistinguishable, an agent that silently stops looks identical to one
that finished, and a slice can be marked done while half its acceptance criteria were never touched.

`PRD.md` §5 fixes the policy: every invocation is a transaction with a validated envelope in and a
validated envelope out, a missing or malformed result is a Protocol Failure that preserves work
without advancing the workflow, exit code zero is never sufficient, an agent's completion claim is
never sufficient, and a result from a superseded assignment cannot advance anything. It then leaves
every mechanism open — "exact schemas and persistence details are implementation deliverables",
"the evidence format and criterion verification rules remain to be specified", "submission identity
fields, content comparison, receipts, and atomic acceptance mechanics remain to be specified".

Two failures follow from that gap. First, a builder result and a review result would validate against
the same loose shape, so a reviewer's output could satisfy a build assignment. Second, context usage
has no representation for "unknown", so an integration that cannot measure it would report zero and
the operator would read that as a healthy agent.

## Solution

GTP v1 defines a two-layer envelope. A common layer carries the identities every dispatch and result
must bind — protocol version, execution, assignment, ownership generation, role, and correlation — and
a role layer carries a discriminated payload whose shape is specific to that role. Both layers are
validated at the boundary before any state change is considered, and validation of the common layer
happens first, so an envelope that does not belong to the current assignment is rejected before its
content is interpreted.

Result envelopes carry a submission identity distinct from the task correlation, so a replay is
recognizable, a correction is a new linked attempt rather than an overwrite, and receipts describe
exactly what was accepted. Status is a small closed set with a fixed precedence, and completion is not
a status an agent can assert: a builder result claiming completion is a request to evaluate
completion, which Gantry grants only after every acceptance criterion of the assigned PBI is
accounted for and Gantry itself has verified the mandatory tests on the delivered revision.

Measurements that an integration cannot provide are represented as unknown rather than defaulted, so
the operator sees an absence of information instead of a false zero.

All traffic is hub-and-spoke through Gantry: envelopes are issued and accepted by the registrar, never
passed agent to agent.

## User Stories

1. As an operator, I want every agent invocation to carry a validated task envelope, so that no agent ever works from an improvised prompt with no recorded contract.
2. As an operator, I want every agent to have official ways to say "done", "failed", "I need a fresh context", and "I am stuck and here are my questions", so that agents never have to improvise a channel.
3. As an operator, I want a missing result treated as a Protocol Failure rather than a completion, so that an agent that dies quietly does not look like one that succeeded.
4. As an operator, I want a malformed result to preserve the agent's work while refusing to advance the workflow, so that a schema problem costs me a retry and not the work.
5. As an operator, I want a Protocol Failure recorded as its own persistent condition, so that I can tell it apart from an agent that deliberately reported being blocked.
6. As an operator, I want a Protocol Failure not to require questions from the agent, so that recording the failure does not depend on the agent that failed to respond.
7. As an operator, I want exit code zero to count as verification evidence and nothing more, so that a process that exits cleanly without a result cannot advance my factory.
8. As an operator, I want a reviewer's output rejected when submitted against a build assignment, so that role confusion cannot satisfy the wrong contract.
9. As an operator, I want an envelope missing its required identities rejected before dispatch, so that untraceable work never starts.
10. As an operator, I want the common identity layer validated before the role payload, so that a result from a superseded assignment is refused without its content being acted on.
11. As an operator, I want unknown fields in an envelope preserved rather than stripped, so that a newer agent or adapter can add information without losing it on a round trip.
12. As an operator, I want the protocol version recorded on every envelope, so that a future change cannot silently reinterpret today's records.
13. As an operator, I want each acceptance criterion to have a stable identity, so that "completed" refers to a specific criterion rather than a count.
14. As an operator, I want a builder result to account for every criterion of its assigned PBI, so that silence about a criterion is not read as success.
15. As an operator, I want completion refused when any criterion remains pending, so that a green test run cannot finish an unfinished slice.
16. As an operator, I want completion refused when mandatory tests are missing or failing, so that completed criteria with no passing tests cannot finish a slice either.
17. As an operator, I want Gantry to verify the mandatory tests itself on the delivered revision, so that completion rests on an actual run rather than on the agent's report of one.
18. As an operator, I want completion to advance the PBI to quality gates and nothing further, so that finishing implementation never implies permission to merge.
19. As an operator, I want reported file changes checked against the assignment's allowed scope, so that a slice cannot quietly edit code it was not assigned.
20. As an operator, I want a result that reports changes to protected governance paths rejected, so that an ordinary assignment cannot rewrite the constitution or an ADR.
21. As an operator, I want an approved governance baseline transition to be the only way an assignment may touch those paths, so that the protection does not block the work that is supposed to change them.
22. As an operator, I want `blocked` to outrank `needs_handoff`, and both to outrank completion evaluation, so that a single result cannot be read two ways.
23. As an operator, I want a `blocked` result to require at least one question for me, so that "stuck" always comes with something I can answer.
24. As an operator, I want a `needs_handoff` result to carry its reason and continuity content, so that the replacement agent starts from evidence rather than from scratch.
25. As an operator, I want context usage representable as unknown, so that an integration that cannot measure it does not report zero.
26. As an operator, I want measured, self-reported, and unknown context usage distinguished in the record, so that I never mistake an agent's guess for a measurement.
27. As an operator, I want each result submission to have its own identity, distinct from the task correlation, so that a replay is recognizable as a replay.
28. As an operator, I want an identical resubmission to return the original receipt, so that a retried delivery does not duplicate transitions or downstream dispatch.
29. As an operator, I want altered content under the same submission identity rejected, so that a receipt always describes what was actually accepted.
30. As an operator, I want a corrected result recorded as a new submission linked to the previous one, so that the correction is visible in history rather than replacing it.
31. As an operator, I want a corrected submission still subject to ownership, role, and transition checks, so that correction is not a way around the rules.
32. As an operator, I want iteration N's envelopes never overwritten by iteration N+1, so that the record of what was asked and answered is append-only.
33. As an operator, I want every dispatch and every result also recorded as a telemetry event, so that the audit trail and the workflow cannot diverge.
34. As an operator, I want envelopes routed only through Gantry, so that two agents cannot agree on something the factory never saw.
35. As an operator, I want each dispatch bound to the approved plan version and rule snapshot, so that an agent cannot be working from rules I replaced.
36. As a host harness, I want to request the next task envelope for a role and receive either a complete envelope or a typed rejection, so that I never have to assemble a contract myself.
37. As a host harness, I want the required output contract stated inside the task envelope, so that the agent I spawn knows the exact shape it must return.
38. As a builder agent, I want to report partial progress honestly through criteria status rather than choosing between done and failed, so that a handoff preserves what I finished.
39. As a builder agent, I want to request a handoff before my context degrades, so that I am not forced to guess my way to the end of a slice.
40. As a reviewer agent, I want to return findings that can only add to the deterministic result, so that my role is clear and I cannot be blamed for clearing a static finding.
41. As a slicer agent, I want to return proposed PBIs with criteria, dependencies, story coverage, and context estimates as structured fields, so that the planning approval step has something checkable to show the operator.
42. As an auditor, I want every envelope stored with its protocol version, actor, driver, and rule snapshot, so that I can replay what governed each exchange.
43. As a Gantry implementer, I want role contracts as a discriminated union with one shared identity layer, so that adding a role does not weaken validation for existing ones.

## Implementation Decisions

### Two-layer envelope

Every envelope is a common identity layer plus a role-discriminated payload. The common layer is
identical for tasks and results; only the payload differs. Validation order is fixed: protocol version,
then common identities, then current-assignment check through the operation core, then role payload.

```ts
type GtpCommon = {
  gtpVersion: "1";                   // major; additive minor changes do not alter this value
  envelopeKind: "task" | "result";
  envelopeId: string;
  issuedAt: string;                  // RFC 3339
  execution: ExecutionId;
  unit: RepositoryExecutionUnitId;
  assignment: AssignmentId;
  ownershipGeneration: number;        // monotonic per PBI; a stale value is refused
  role: GtpRole;
  correlation: CorrelationId;         // stable across the task and all of its result submissions
  ruleSnapshot: SnapshotId;
  planVersion: PlanVersionId;
  extensions?: Record<string, unknown>;  // preserved verbatim, never interpreted
};

type GtpRole =
  | "builder"
  | "requirement_critic"
  | "adversarial_critic"
  | "slicer"
  | "spec_architect"
  | "architectural_sentinel"
  | "appsec_gatekeeper"
  | "merger"
  | "compound_learner";
```

Schemas are Zod at the boundary. Objects are permissive for unknown keys, but unknown keys are lifted
into `extensions` and persisted verbatim rather than left inline, so forward compatibility never means
an unvalidated field masquerading as a known one. A known field with the wrong type is always a
violation; permissiveness applies only to fields the schema has never heard of.

`gtpVersion` is a major marker. Adding an optional field is a minor change that does not move it;
removing a field, narrowing a type, or changing a meaning requires a new major and a declared
compatibility range against persisted executions.

### Role contracts

Tasks and results are a discriminated union on `role`. Each role's task states its inputs and the
required output contract; each role's result states its evidence. A result whose payload does not
match its assignment's role is rejected before any interpretation.

| Role | Task payload | Result payload |
|---|---|---|
| `builder` | PBI reference and version, criteria with stable identities, approved verification commands, allowed scope, continuity context when resuming after handoff | Per-criterion status with evidence references, delivered revision, reported changed paths, verification attempt records, status |
| `requirement_critic` | Versioned spec subject, applicable rules, available structural findings | Findings with severity and location, review coverage statement, status |
| `adversarial_critic` | Versioned PBI and spec, constitution and ADR references, diff reference, deterministic findings already produced | Additional findings restricted to the four allowed classes, coverage statement, status |
| `slicer` | Technically ready spec, user stories, context budget and assumed model window | Proposed PBIs with criteria identities, dependencies, story coverage map, per-PBI context estimate with method and uncertainty, status |
| `spec_architect` | Problem context, existing canonical document reference when adapting | Proposed spec content or complements, mapped sections, status |
| `architectural_sentinel`, `appsec_gatekeeper` | Subject revisions, approved check configuration | Structured findings and coverage declaration, status |
| `merger` | Candidate and target revisions, approved plan constraints, conflict context | Resolution description, resulting candidate revision, changed paths, status |
| `compound_learner` | Execution history references, failure evidence | Proposed learning candidates with rationale, status |

`adversarial_critic` findings are restricted to `spec-deviation`, `adr-deviation`,
`semantic-conflict`, and `scope-creep`. The payload has no field capable of expressing approval,
clearance, or downgrade of an existing finding, so the "may only add" rule is enforced by the shape
rather than by a check that could be forgotten.

### Status and its precedence

```ts
type GtpStatus = "complete" | "failed" | "needs_handoff" | "blocked";
```

Precedence within one valid result is fixed: `blocked` outranks `needs_handoff`, which outranks any
evaluation of completion. `blocked` requires a non-empty `questionsForOperator`; an empty list makes
the result invalid rather than unblocked. `needs_handoff` requires a reason and continuity content.

`complete` is a claim, not a state change. For a builder it is a request to evaluate Implementation
Completion, which the core grants only under the rules below. For a non-mutating role it means the
role's own work finished and its evidence is present.

### Implementation Completion

Completion requires all of:

1. The result is valid and from the current assignment.
2. Every acceptance criterion identity declared by the assigned PBI appears in the result exactly once.
3. Every one of those criteria has status `completed`. Any `pending` criterion refuses completion.
4. Each completed criterion carries an evidence reference: the verification command that covers it and
   the revision it was observed on.
5. Gantry has verified the PBI's mandatory tests on the delivered revision.

Point 5 is a re-execution, not an acceptance of the agent's report. Gantry runs the approved mandatory
verification commands against the delivered revision through the check adapter and uses its own result.
The agent's verification records are retained as context and as a discrepancy signal — an agent
reporting a pass where Gantry observes a failure is recorded as a verification-integrity finding — but
they never establish completion. This implements §5.4's "actual check results and Git or provider state
take precedence over agent claims" without leaving a gap where the claim is the only evidence.

Criterion identities are stable strings assigned when the PBI is approved and never renumbered. A
result naming a criterion the PBI does not declare, or omitting one it does, is invalid.

Completion advances the PBI to `in_gates` and nothing further.

### Protocol Failure

A Protocol Failure is a persistent condition on the assignment, not a status an agent reports. Its
classes:

| Class | Cause |
|---|---|
| `missing_result` | The dispatch ended with no result submitted, including exit code zero |
| `malformed_result` | The envelope failed structural validation |
| `role_mismatch` | The payload is valid for a different role than the assignment's |
| `identity_mismatch` | Required identities absent, or referencing a different execution or plan version |
| `stale_generation` | The ownership generation is behind the current one |
| `criteria_mismatch` | Criterion identities do not correspond to the assigned PBI |

Every class preserves the agent's work and the raw submission for recovery, records the failure with
its class, and advances nothing. None requires `questionsForOperator`. `stale_generation` is stored and
rejected rather than discarded, so a late agent's output remains auditable. Protocol Failures are
classified as protocol, never as infrastructure, so they consume no infrastructure retry allowance.

### Submission identity and idempotency

A submission identity is distinct from the correlation identity:

```ts
type ResultSubmission = {
  correlation: CorrelationId;       // shared by the task and every submission answering it
  submissionId: string;             // unique per submission attempt
  supersedes?: string;              // the submissionId this correction replaces
  contentHash: string;              // over the canonicalized payload
};
```

Canonicalization for the hash is deterministic: sorted keys, no insignificant whitespace, `extensions`
included. An identical `submissionId` with an identical `contentHash` returns the original receipt with
no repeated transition, counter change, acceptance event, or downstream dispatch. An identical
`submissionId` with a different `contentHash` is rejected. A correction uses a new `submissionId` with
`supersedes` set, retains the prior submission, and passes the full ownership, role, and transition
checks again.

Submission identity maps onto the operation core's `requestId` for `pbi.submitResult`, so idempotency
is enforced in one place rather than two.

### Scope and governance protection

Every mutating task declares an allowed scope as path patterns. A result reporting changes outside it
is a scope violation: the result is retained, the PBI does not complete, and the violation is recorded
as a finding rather than silently accepted. Protected governance paths come from the repository's
effective Artifact Location Mapping, not from hardcoded directory names.

An ordinary assignment cannot report changes to protected paths. An assignment issued under an approved
Governance Baseline Transition carries an explicit permission naming those paths, so the protection does
not block the work whose whole purpose is to change them. Absent that permission, a governance-path
change is a violation.

### Append-only storage and routing

Envelopes are stored under their assignment and iteration and never overwritten. Every dispatch and
every result also writes a telemetry event, in the same transaction as the transition it evidences.

Task envelopes are produced only by Gantry's registrar, through the CLI or MCP transports, and results
are accepted only by it. There is no agent-to-agent envelope path. A result submitted for an assignment
that was never dispatched is an identity mismatch.

Retained representation follows spec 04: the dispatch payload may contain the full approved context,
while the retained record holds references, hashes, and redacted summaries plus enough information to
locate the versioned content again.

### Context usage

```ts
type ContextUsage =
  | { kind: "measured"; tokens: number; window: number; source: string }
  | { kind: "self_reported"; tokens: number; window?: number }
  | { kind: "unknown"; reason: string };
```

There is no default. An integration that cannot measure usage returns `unknown` with a reason, and the
projection renders it as unknown. `self_reported` is never presented as a measurement and never
establishes a watermark guarantee, per ADR-0001.

## Testing Decisions

**What makes a good test here.** Tests build envelopes as data, submit them through the operation core,
and assert on the returned receipt or rejection code and the resulting state projection. They never
assert on Zod internals, schema object identity, error message text, or storage layout. A test should
survive a schema refactor and fail if a contract rule is relaxed.

**The seam.** The same single seam as spec 01: `core.invoke` for `pbi.dispatch` and `pbi.submitResult`,
against a real temporary SQLite database and a real temporary Git repository, with a fake harness driver
returning scripted envelopes and a fake check adapter returning scripted verification results. Envelope
validation is never tested by calling a validator directly — that would test an implementation detail and
would not prove the boundary actually runs it.

**Modules under test.** The envelope schemas and their validation order, the role contract union, status
precedence, the Implementation Completion rule, Protocol Failure classification, submission identity and
idempotency, scope and governance protection, append-only envelope storage, and context usage
representation — all through `invoke`.

**Fixtures.** A scripted driver that can be told to return: a valid builder result, a result with one
pending criterion, a result whose criteria do not match the PBI, a reviewer payload under a builder
assignment, an envelope with unknown extra fields, an envelope with a known field of the wrong type, an
envelope with a stale ownership generation, no result at all with exit code zero, and a result claiming
a pass where the check adapter is scripted to fail.

**Scenarios that must exist**, from PRD §14.3 items 3 and 4:

- A valid builder result with all criteria completed and Gantry-verified tests completes the PBI and
  leaves it in `in_gates`, not merge-authorized.
- One pending criterion refuses completion even when the test run is green.
- All criteria completed but Gantry's own test run failing refuses completion.
- An agent reporting a pass where Gantry observes a failure refuses completion and records a
  verification-integrity finding.
- A criterion identity absent from the result, and one not declared by the PBI, are both
  `criteria_mismatch`.
- A reviewer payload submitted under a builder assignment is `role_mismatch`.
- An adversarial critic result cannot express clearing a deterministic finding, demonstrated by the
  absence of any such field rather than by a runtime check.
- Exit code zero with no result is `missing_result`, the work is preserved, and nothing advances.
- A malformed envelope is `malformed_result` with the raw submission retained.
- A stale ownership generation is `stale_generation`: stored, rejected, state unchanged.
- No Protocol Failure class requires `questionsForOperator`, and none consumes infrastructure retries.
- `blocked` with an empty question list is invalid; with questions it moves to `awaiting_operator`.
- A result carrying both `blocked` and completed criteria resolves as `blocked`.
- A result carrying both `needs_handoff` and completed criteria resolves as `needs_handoff`.
- An identical resubmission returns the original receipt with no second transition or dispatch.
- The same `submissionId` with altered content is rejected; a new `submissionId` with `supersedes`
  is accepted and both submissions remain readable.
- Unknown fields survive a store-and-read round trip inside `extensions`; a known field with a wrong
  type is rejected.
- A result reporting a change outside the allowed scope refuses completion and records a violation.
- A result touching a protected governance path is a violation under an ordinary assignment and
  accepted under an assignment carrying explicit baseline-transition permission.
- Iteration N+1 envelopes do not overwrite iteration N; both remain retrievable.
- An integration returning `unknown` context usage is projected as unknown, never as zero.

## Out of Scope

- **Transitions, ownership, budgets, receipts, persistence** (spec 01): this spec defines envelope content and the completion rule; the state machine, ownership arbitration, idempotency storage, and atomic acceptance are the core's.
- **Config and snapshot** (spec 02): which verification commands are approved, what the rule snapshot contains, and how it is captured. This spec binds `ruleSnapshot` on every envelope; it does not define it.
- **Redaction, retention, egress** (spec 04): what may be persisted from a dispatch payload or an agent output, and whether a payload class may leave the machine. This spec says the retained record must locate versioned content; spec 04 defines safe retention.
- **Real harness invocation** (spec 10): how Codex or OpenCode is actually launched, how usage is extracted, and how an agent is interrupted. This spec's driver is a fake, and the `ContextUsage` union is the contract adapters must satisfy.
- **Watermark policy and handoff memo construction** (spec 11): when a handoff is triggered and what the memo contains. This spec defines the `needs_handoff` result and its continuity fields.
- **Criterion authoring and PBI approval** (specs 08, 09): how criteria are written, linted, given identities, and approved. This spec requires stable identities and consumes them.
- **Check execution and finding normalization** (spec 12): how mandatory tests are run and how findings are structured. This spec requires that Gantry, not the agent, produces the completion evidence.
- **Gate decisions** (spec 13): what findings block. This spec records findings; it does not decide gates.
- **Governance baseline transition approval** (spec 15): how the permission naming protected paths is granted. This spec honors it.
- **Transports** (specs 16, 17): the MCP tools that carry dispatch and result submission.

Out of scope by product decision:

- Agent-to-agent envelope exchange. Traffic is hub-and-spoke through Gantry (§5).
- Harness-specific conversation continuation as a cost optimization, explicitly deferred in §6.2. Identifying and reconciling current assignments is not deferred and belongs to spec 01.
- A universal envelope shape shared by all roles. The PRD review explicitly rejected presenting a builder-shaped sample as the universal schema.

## Further Notes

**Binding decisions.** ADR-0001 is why `ContextUsage` has an `unknown` variant and why
`self_reported` is structurally distinct from `measured`: a guarantee an integration cannot enforce must
not be advertised, and the type system is the cheapest place to hold that line.

**Glossary alignment.** Protocol Failure, Implementation Completion, Result Submission, and PBI
Execution Ownership follow `CONTEXT.md`. Note the two the glossary explicitly warns about: a Protocol
Failure is not an agent-reported blocked result and not a successful invocation; Implementation
Completion is not Merge Authorization and not merely "tests green".

**Glossary gap for `/domain-modeling`.** Criterion identity and scope violation are used here without
glossary entries and should get them.

**Where the risk actually sits.** The strongest decision in this spec is that Gantry re-executes the
mandatory tests rather than trusting the agent's evidence. It closes the completion gap the PRD worries
about, at the cost of one extra verification run per completion attempt and a dependency on spec 12
being able to run those commands cheaply against a delivered revision. If that cost proves unacceptable,
the fallback is not to trust the agent but to make the re-execution incremental — the rule that
completion rests on Gantry's own observation should survive any optimization.

**Sequencing note.** This spec and spec 01 are mutually referential by design: 01 owns the transition
`pbi.submitResult` performs, 03 owns what makes the submission valid. Expect the issues to interleave.
The `extensions` lifting rule is the one detail worth settling before either starts, because it affects
the persistence shape in 01 and every schema in 03.
