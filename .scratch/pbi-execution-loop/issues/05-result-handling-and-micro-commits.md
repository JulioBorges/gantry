# Result handling, micro-commits, and correction dispatch

Type: issue
Status: ready-for-agent
Slice: pbi-execution-loop#05
Spec: [`../spec.md`](../spec.md) (spec 11, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/pbi-execution-loop/spec.md`](../spec.md)

## What to build

A submitted result drives the loop according to the fixed status precedence the GTP protocol defines. `blocked` stops the loop, moves the PBI to `awaiting_operator`, surfaces `questionsForOperator`, and releases the slot. The operator answers through `pbi.answer`, which returns the PBI from `awaiting_operator` to `queued` carrying the answer as continuity input, and this slice carries that answer into the redispatch so that answering is sufficient to continue. `complete` triggers Implementation Completion evaluation and, on success, advances toward gates. `failed` records evidence and schedules a correction attempt only within the PBI's remaining allowance, with exhaustion stopping automatic work rather than spawning another agent.

A micro-commit is made only when Gantry's own execution of the PBI's mandatory verification passes — never on an agent's reported pass — with a deterministic message identifying the PBI and the verification that passed. Nothing is ever pushed by the loop; integration is separately authorized and belongs elsewhere. An exit code with no submitted result advances nothing and produces no commit, because the loop never interprets an exit code as a status.

The `needs_handoff` path is not this slice's: it belongs to `pbi-execution-loop#04`. This slice owns the rest of result handling and touches the handoff only at the boundary where precedence resolves a result to `needs_handoff` and enters that sequence.

## Acceptance criteria

- [ ] A `blocked` result moves the PBI to `awaiting_operator`, surfaces the questions, releases the slot, and lets another queued PBI start; recording an answer resumes the loop for that PBI.
- [ ] A result carrying both `blocked` and completed criteria resolves as `blocked`; one carrying `needs_handoff` and completed criteria resolves as `needs_handoff` and enters the handoff sequence.
- [ ] A micro-commit appears on the PBI branch after Gantry runs the mandatory verification and it passes, and no commit appears when the agent reports a pass that Gantry's run contradicts.
- [ ] No push occurs at any point in the loop, asserted against the real temporary repository's remote refs.
- [ ] Correction attempts are consumed at correction dispatch; exhausting the allowance leaves the gate failed, dispatches no further agent, and produces `correction_budget_exhausted`.
- [ ] A process exit with status zero and no submitted result produces no micro-commit and no state advancement.
- [ ] The MCP result-submission surface gets one parity test proving delegation to `invoke`.

## Blocked by

- `pbi-execution-loop#01` — the PBI worktree and branch that micro-commits and save points land on.
- `gtp-protocol#04` — `GtpStatus` precedence and the `questionsForOperator` requirement on a `blocked` result.
- `gtp-protocol#05` — the Implementation Completion rule and criterion identity.
- `gtp-protocol#06` — Result Submission identity and idempotency.
- `execution-core#03` — the operator-channel operation `pbi.answer`, which returns a PBI from `awaiting_operator` to `queued` carrying the operator's answer as continuity input.
- `execution-core#05` — Correction Budget accounting and the dispatch-time consumption rule.
- `config-and-snapshot#01` — the correction budget value.
- `verification-adapters#01` — the check execution interface that runs a declared mandatory check and returns a pass or fail with evidence.
- `entropy-gate#06` — the correction dispatch entry point that decides what to correct; this slice only dispatches within the allowance.
