# Target routing by Governance Precedence and conversion to a Governance Baseline Transition

Type: issue
Status: ready-for-agent
Slice: compound-learning#06
Spec: [`../spec.md`](../spec.md) (spec 18, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/compound-learning/spec.md`](../spec.md)

## What to build

Make the precedence constraint structural rather than a policy. `AGENTS.md` sits at Governance Precedence level 6, `CONSTITUTION.md` at level 3 and applicable ADRs at level 4; a learner able to target the higher two would be promoting its own output's authority past the ordering — proposing a rule as an ADR because agents follow ADRs more reliably. So a candidate's target determines its path and the producer cannot choose freely.

An `agents_section` target is an operational proposal handled by slices `compound-learning#01` and `compound-learning#05`. A `constitution` or `adr` target has **no direct application path at all** and is instead converted into a governance change declaration that enters the Governance Baseline Transition path — the legitimate route, with its manifest, comparative reasoning and adoption — carrying the candidate's originating occurrences and evidence references across as the transition's justification. `learning.approve` against a candidate with either higher-precedence target is refused with a routing condition rather than applying anything, so no sequence of learning operations can write to a level 3 or level 4 document.

The refusal half depends on nothing beyond slice 01 and is the part that actually protects the precedence ordering; the conversion half is what waits on the transition declaration intake.

## Acceptance criteria

- [ ] A candidate targeting `CONSTITUTION.md` produces a governance change declaration and no applied-learning record; the same holds for a candidate targeting an ADR path.
- [ ] `learning.approve` against a `constitution` or `adr` candidate is refused, and the marked section is byte-identical afterwards.
- [ ] The produced declaration carries the candidate's occurrences and evidence references, so the transition's justification is traceable to the same evidence the candidate cited.
- [ ] No operation in the learning catalog can write to any document above precedence level 6, demonstrated by attempting each learning operation against a higher-precedence target.
- [ ] The source level assigned to an applied learning is level 6, and a resolution that pits it against a higher-level assertion records the applied learning as overridden.

## Blocked by

- `compound-learning#01` — the candidate target field, the approve path the routing condition refuses, and the applied-learning record.
- `config-and-snapshot#06` — the `SourceLevel` definition and precedence resolution, including the recording of overridden assertions.
- `baseline-transitions#01` — Governance Baseline Transition declaration intake and governance-path permission, the destination for a converted candidate.
