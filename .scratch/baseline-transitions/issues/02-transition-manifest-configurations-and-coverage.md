# Transition manifest: configurations, comparison mode, and coverage change

Type: issue
Status: ready-for-agent
Slice: baseline-transitions#02
Spec: [`../spec.md`](../spec.md) (spec 15, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/baseline-transitions/spec.md`](../spec.md)

## What to build

Build the manifest for a declared transition, produced through `baseline.propose`. Identify the old configuration from the execution's captured Execution Rule Snapshot and the proposed configuration from the transition PBI's changes — commands, tool versions, rule sets, coverage declarations.

Determine the comparison mode by actually attempting both configurations against one representative subject revision, never by inspecting the declaration. `both_run` applies when both execute and produce parseable Comparison Evidence. `new_only` applies when no prior check existed, and carries a non-empty `absenceReason`, recorded as an explicit absence and never as a zero-finding report. `old_only` applies when the proposed configuration cannot execute, and carries its `reason`. `neither` applies when neither can execute. Record both report identities and the single `subjectRevision` they share.

Compute the coverage change — added, removed, unchanged — from the declared coverage of both configurations. Derive `reducesCoverage` from the removed set rather than accepting an assertion on input, and surface a reducing transition distinctly in the manifest, since a weakening presented as an improvement is the failure mode this guards against.

## Acceptance criteria

- [ ] `both_run` produces a manifest whose old and new reports share one `subjectRevision`, with both report identities recorded.
- [ ] `new_only` records a non-empty absence reason and leaves the old report identity unset; no report with zero findings is synthesized for the missing prior check.
- [ ] A proposed check that executes but emits unparseable evidence yields a manifest marked as not adoptable, distinct from a check that does not execute at all.
- [ ] `old_only` and `neither` are recorded with their reason and mark the manifest not adoptable.
- [ ] A transition removing a coverage declaration computes `reducesCoverage: true` with the removed entries listed; a transition adding coverage computes `reducesCoverage: false`. The flag is never taken from input.
- [ ] A manifest is refused when the two reports were produced against different subject revisions.

## Blocked by

- `baseline-transitions#01` — the transition record, its lifecycle, and the operation catalog family the propose operation joins.
- `verification-adapters#01` — the structured report binding carrying `subjectRevision`, `toolVersion`, `ruleSetVersion`, `declaredCoverage` and the command reference.
- `verification-adapters#04` — the adapter failure classification that distinguishes a check which cannot execute from one that executes and emits unparseable evidence.
- `config-and-snapshot#04` — the baseline configuration content captured in an Execution Rule Snapshot: approved commands, observed tool versions, and rule sets.
