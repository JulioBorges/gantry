# Learning candidate from Entropy Gate findings, approved into the marked section

Type: issue
Status: ready-for-agent
Slice: compound-learning#01
Spec: [`../spec.md`](../spec.md) (spec 18, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/compound-learning/spec.md`](../spec.md)

## What to build

The spine, end to end. Add the learning record families — candidates, occurrences, applied learnings — to the unit-scoped store; register `learning.produce`, `learning.approve` and `learning.list` in the shared operation core's catalog; wire `gantry learn-from-pbi` and an approve command onto them so the CLI delegates to `invoke` rather than carrying its own logic. Production reads the retained gate-finding records for a named PBI and groups them into one candidate per distinct observation, each carrying its occurrence list and its occurrence count. Aggregation across PBIs within an execution — and across executions where the repository retains them — is the same grouping over a wider query, so three occurrences of one observation produce one candidate with three citations rather than three candidates.

```ts
type LearningCandidate = {
  candidateId: string;
  observation: string;                    // what recurred
  occurrences: Array<{ pbi: PbiId; evidence: EvidenceRef }>;   // at least one, each resolvable
  proposedRule: string;                   // an instruction, not a description
  target:
    | { kind: "agents_section" }          // operational, precedence level 6
    | { kind: "constitution" }            // requires a Governance Baseline Transition
    | { kind: "adr"; adrPath: string };   // requires a Governance Baseline Transition
  observationFingerprint: string;         // for deduplication against prior rejections
  sourceKinds: Array<"gate_finding" | "correction_attempt" | "protocol_failure" | "handoff" | "integrity_finding" | "state_transition">;
};
```

Two validations run at production, and both exist because the retained evidence is deliberately thin — references, hashes and redacted summaries rather than conversation history, tool transcripts or build logs. Every occurrence must carry an evidence reference that resolves under the replayable-reference rules **at production time**: an occurrence whose reference does not resolve is dropped, and a candidate left with no occurrences is not produced at all. And `proposedRule` must be an instruction rather than a restatement of the observation, enforced as a validation rather than left to the producer's discretion. All candidate text passes the redaction pipeline before persistence.

`learning.approve` is operator-only and renders the approved rule — with its originating PBIs, evidence references and approval timestamp — inside the `<!-- gantry:begin -->` / `<!-- gantry:end -->` markers. The structural decision to preserve: **the marked section is rendered from the persisted record set, never appended to in place.** `repository-readiness` owns the marker contract and its rule is that re-running init replaces the section's content in place; if approved learnings accumulate as free text in that region, `gantry init` silently erases them. Rendering both init's standard content and the applied learnings from one record set makes init and learning application the same operation over a shared source of truth, so any writer re-renders rather than overwrites. Production itself is read-only with respect to execution: it writes candidate records and nothing else.

## Acceptance criteria

- [ ] `gantry learn-from-pbi` against a seeded PBI with repeated gate findings produces at least one candidate carrying a non-empty occurrence list, each occurrence with a resolvable evidence reference.
- [ ] A candidate whose only evidence reference no longer resolves is not produced; a candidate whose `proposedRule` restates its observation is refused as invalid at production.
- [ ] An approved candidate appears between the markers; every byte of `AGENTS.md` outside the markers is identical before and after, and the applied record names its originating PBIs, evidence references and approval timestamp.
- [ ] `learning.approve` over the MCP channel is rejected `operator_channel_required`, and an agent result asserting approval creates no applied-learning record.
- [ ] Running production changes no execution state, consumes no Correction Budget or Infrastructure Retry allowance, and triggers no cleanup — asserted against the state projection and an instrumented core.
- [ ] One CLI parity test proves delegation to `invoke`; candidate text with a secret-shaped value is redacted in the persisted record.

## Blocked by

- `execution-core#01` — the `invoke` request/outcome shape, operation catalog registration, the record-family and unit-scoped store conventions, and the audit record written with each transition.
- `execution-core#02` — operator channel derivation and the `operator_channel_required` rule that makes `learning.approve` operator-only and refuses an agent-asserted approval.
- `data-handling#01` — the redaction sink enforcement interface every candidate write passes through.
- `data-handling#04` — replayable reference resolution and the missing-source condition that decides whether an occurrence's evidence reference resolves at production time.
- `verification-adapters#01` — the normalized finding shape (rule, path, symbol, content anchor, problem identity) that distinct observations are grouped by.
- `entropy-gate#01` — the gate decision record and its finding evidence records, the source family this slice reads.
- `repository-readiness#01` — the Artifact Location Mapping entry for agent instructions, which locates the marked section.
- `repository-readiness#02` — ownership of the `<!-- gantry:begin -->` / `<!-- gantry:end -->` marker contract and its in-place replacement rule, which this slice must turn into a render from persisted records.
