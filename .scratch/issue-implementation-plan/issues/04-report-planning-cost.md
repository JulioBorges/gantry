# Report attributable technical-planning cost and correction outcomes

Type: issue
Status: ready-for-agent
Slice: `issue-implementation-plan#04`
Spec: `.scratch/issue-implementation-plan/spec.md`
Created: 2026-10-06
User stories covered: 11, 18–20, 21–22

## Parent

`issue-implementation-plan` — Spec in the local Markdown tracker.

## What to build

Deliver the observation path from Technical Plan and implementation invocation through sanitized phase events and public read-only Run reporting. Report separate durations, available provider token usage, total attributable usage, plan reuse/replanning, Review fix passes and Critic correction attempts. Carry measurement provenance and missing-data limitations. Preserve the existing observational Run log and keep plan bodies/source excerpts in separate execution artifacts. This is a report/data behavior, with no Dashboard UI change.

## Acceptance criteria

- [ ] An end-to-end workflow fixture and public Run report distinguish Technical Plan from implementation and attribute their completed phase durations.
- [ ] Provider-supplied usage is reported with provenance; unavailable token measurements remain unknown and estimates are explicitly distinguished from actual usage.
- [ ] Totals count original planning, targeted replanning, implementation and correction calls once; reused plan artifacts do not count as new invocations or usage.
- [ ] Review fix passes and Critic correction attempts are distinct report fields and agree with authoritative correction counting.
- [ ] Run-log validation accepts sanitized phase/identity/measurement projections and refuses prompts, source excerpts, plan bodies and sensitive raw outputs.
- [ ] Legacy Runs without Technical Plan or usage events remain readable without fabricating a checkpoint, zero usage or completion evidence.
- [ ] Reports provide evidence for future comparisons without asserting token savings, faster delivery or fewer corrections from incomparable Runs.
- [ ] Existing public report/data seams demonstrate the behavior without UI changes or weakening Review/Critic/gate completion authority.

## Blocked by

- issue-implementation-plan#02
- issue-implementation-plan#03

## Comments

Testing seams, four-Issue breakdown and dependencies approved for publication when the operator requested a PR to main on 2026-10-06. Implementation remains separately authorized; no criterion is complete.
