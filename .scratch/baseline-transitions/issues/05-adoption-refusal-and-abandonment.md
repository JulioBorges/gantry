# Adoption, refusal, and abandonment

Type: issue
Status: ready-for-agent
Slice: baseline-transitions#05
Spec: [`../spec.md`](../spec.md) (spec 15, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/baseline-transitions/spec.md`](../spec.md)

## What to build

Add the operator-only `baseline.adopt` operation, referencing a specific manifest. Adoption is refused when the comparison mode blocks, when required evidence is incomplete, when the proposed configuration failed to execute or produced unparseable evidence, when the manifest's transition PBI has not reached Implementation Completion, or when the request arrives on a non-operator channel. A successful adoption records the approving actor and time, produces a new Execution Rule Snapshot from the proposed configuration, and marks the transition adopted.

`baseline.abandon` is the symmetric terminal decision: it retains the manifest and all its evidence as a record of what was evaluated, leaves the old configuration authoritative, and is itself irreversible for that manifest. Neither operation rewrites, reclassifies, or removes any existing finding or evidence record.

**The Implementation Completion precondition is an inferred rule, not one the spec states.** The spec refuses adoption for a blocking mode, incomplete evidence, or a proposed configuration that failed to execute, and is silent on whether a transition can be adopted before its PBI is integrated. The precondition is kept here because adopting a configuration whose defining files are not yet on the target would make the new snapshot reference content that does not exist there. A reviewer should be able to challenge it rather than assume the spec said it. Note also the chain-shortening option recorded during breakdown: the chain `01 → 02 → 05 → 06` is four deep for a six-slice spec, and these adoption preconditions can instead be built against a manifest fixture in parallel with `baseline-transitions#02`, at the cost of a later integration step.

## Acceptance criteria

- [ ] Adoption of a manifest whose mode is `old_only` or `neither` is refused with a typed rejection code naming the mode.
- [ ] Adoption with a missing or unparseable required report is refused; the refusal is distinguishable from a refusal for blocked mode.
- [ ] Adoption from an agent channel is refused with `operator_channel_required`; the same request from an operator channel succeeds.
- [ ] A successful adoption produces a new snapshot identity distinct from the old one and records it on the manifest alongside the approving actor's provenance.
- [ ] Findings, reports, approvals, and Merge Authorizations recorded before adoption are byte-identical afterward and remain bound to their original snapshot identity.
- [ ] An abandoned manifest retains its configurations, comparison mode, and evidence; a later adoption attempt against it is refused; the old configuration remains the authoritative baseline.

## Blocked by

- `baseline-transitions#02` — the manifest, its comparison mode and its evidence completeness, which the adoption preconditions read.
- `config-and-snapshot#04` — snapshot identity and immutable snapshot creation from a supplied configuration.
- `execution-core#02` — operator-only channel enforcement and the `operator_channel_required` rejection code.
- `gtp-protocol#05` — the Implementation Completion definition the inferred adoption precondition reads.
