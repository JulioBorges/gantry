# Old-baseline evaluation of the introducing delivery

Type: issue
Status: ready-for-agent
Slice: baseline-transitions#04
Spec: [`../spec.md`](../spec.md) (spec 15, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/baseline-transitions/spec.md`](../spec.md)

## What to build

Make the Entropy Gate decision for a transition PBI use the configuration in force when the PBI started, while still permitting the proposed checks to run as manifest evidence. This is the structural answer to self-approval, and it must be enforced structurally rather than by convention, because the distinction is easy to collapse into one code path and impossible to detect once collapsed.

Three rules. The gate's baseline selection resolves to the execution's captured snapshot for a transition PBI, regardless of any proposed configuration in scope. Findings produced only by the proposed configuration are excluded from Quality Regression classification for that delivery and are recorded instead as the preexisting baseline the new check will carry forward once adopted. And the proposed configuration cannot clear, downgrade, or reclassify a finding the old configuration produces against the delivery.

Publish the baseline-selection contract the Entropy Gate consumes. Note the seam deliberately: this spec owns **which** baseline judges a delivery, and `entropy-gate#01` owns **how** the chosen baseline decides. If `entropy-gate`'s issues already define baseline selection by the time this slice is picked up, this slice shrinks to consuming that definition rather than publishing one.

## Acceptance criteria

- [ ] A transition PBI's gate decision records the old snapshot identity as its governing configuration, even when a proposed configuration is present in the manifest.
- [ ] A finding surfaced only by the proposed check does not appear as introduced or aggravated in the transition PBI's gate decision and does not block it.
- [ ] A finding produced by the old configuration against the transition PBI still blocks when at or above the blocking severity; a proposed rule that would exempt it has no effect on the outcome.
- [ ] Findings surfaced by a `new_only` check are recorded as the preexisting baseline for that check and are not attributed as regressions to the PBI that added it.
- [ ] The proposed configuration's reports are retained as manifest evidence even though they did not participate in the gate decision, and are distinguishable from gate evidence by role.
- [ ] An absolute mandatory rule in the old configuration still blocks, and the transition provides no path to waive it.

## Blocked by

- `baseline-transitions#01` — the transition record and declaration that marks a PBI as a transition PBI for baseline selection.
- `entropy-gate#01` — the gate decision record, its Execution Rule Snapshot binding, and the introduced / aggravated / preexisting classification semantics this slice constrains.
- `entropy-gate#02` — the absolute mandatory rules that must keep blocking through a transition.
