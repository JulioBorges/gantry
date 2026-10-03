# Pause on unavailable verification prerequisites and resume preserved work

Type: issue
Status: ready-for-agent
Slice: `run-execution-reliability#04`
Spec: `.scratch/run-execution-reliability/spec.md`
Created: 2026-10-03
User stories covered: 4, 16, 17, 18, 19, 20, 28, 30, 32

## Parent

`run-execution-reliability` — [Spec](../spec.md)

## What to build

Give an Issue whose acceptance depends on a declared external verification capability a complete readiness, pause and recovery path. Consume operator-approved repository checks and explicit Issue acceptance needs; run only declared approved probes. Report available, unavailable or unknown capability with a stable prerequisite identity and a remedy. Preserve actionable code findings separately from unavailable proof, and avoid repeating the same acceptance cycle against an unchanged external blocker. Any declaration/configuration additions must follow the existing setup approval writer rather than letting the workflow silently rewrite policy.

### Files to read

- `.agents/skills/gantry/scripts/execution.py`
- `.agents/skills/gantry/scripts/runlog.py`
- `.agents/skills/gantry/schemas/critic.json`

### Focused follow-up exploration

Inspect readiness/frontier boundaries, approved check configuration, setup policy preservation, correction derivation and the canonical recovery fixtures on demand. Dependencies remain authoritative in Issue files; a capability observation does not rewrite the blocker graph. Dashboard rendering of the typed pause is delivered by Issue 05.

## Acceptance criteria

- [ ] An operator-approved prerequisite declaration is consumed through the public readiness path and associated with the affected Issue and acceptance need. Missing, malformed or inconclusive capability evidence yields unavailable/unknown with a remedy; no probe command is invented from arbitrary repository text.
- [ ] A canonical Run with an unavailable declared prerequisite pauses before dependent role work is scheduled, records an attributable verification blocker, and leaves authoritative Issue completion criteria unticked. Independent eligible work retains the existing scheduling and recovery rules.
- [ ] When verification capability disappears after implementation, the returned failure is classified separately from a substantive code refutation. The assigned worktree, branch, delivered revision and last valid evidence remain preserved.
- [ ] A pure external verification pause consumes no code correction attempt and cannot become an unbounded retry loop. Mixed findings retain genuine required code fixes; each actual correction is counted once under the existing budget, without resetting or retrospectively refunding spent attempts.
- [ ] Resumption requires the existing authorized recovery path and fresh verification of the blocked capability. A repeated continue request with unchanged unavailable evidence does not rerun dependent acceptance or mark the Issue done.
- [ ] A changed capability can resume the same Run and worktree with the preserved role selection and budget. Before acceptance, the independent Critic still verifies the delivered revision and every required gate; a prerequisite probe never substitutes for that proof.
- [ ] Disposable canonical fixtures cover unavailable and restored Docker-like capability, a missing external entitlement, inconclusive evidence, and a mixed code/external finding. They demonstrate absence of dependent invocations during the unchanged pause and normal completion after verified restoration.
- [ ] Operator guidance states the exact required remedy and distinguishes verification readiness from dependency readiness. No automatic infrastructure repair, privilege expansion, entitlement purchase, provider write, scope change or Issue split occurs; any necessary Plan Amendment remains an operator decision.

## Blocked by

- `run-execution-reliability#02`

## Comments

- 2026-10-03 — Prepared through to-issues as a complete vertical slice. The operator approved all five slices, story coverage and dependency relationships in conversation. Planning approval does not authorize implementation.
