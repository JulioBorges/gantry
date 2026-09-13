# Resumable and recorded round execution

Type: issue
Status: ready-for-agent
Slice: `gantry-migration#14`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Complete the canonical `.agents/skills/gantry/SKILL.md` and `reference/round-workflow.md` lifecycle around recorded Runs. This Issue exclusively wires workflow preflight, round, phase, subagent, result, completion, cancellation, policy-change, Issue, review, and refutation events through `runlog.py`; it does not alter event serialization or validation. Preflight creates `run.started`, computes the frontier from authoritative Issue statuses, records every phase and validated subagent result, integrates completed parallel Issue branches serially, and invokes `roadmap.py done` only after Critic acceptance and green integration gates. On rerun, query the Run log only to offer continuation of an in-flight Issue in its preserved worktree; retain correction attempts and keep status authority in Issue files.

## Acceptance criteria

- [ ] A simulated interrupted fixture Run in which `greeting#02` is in Implement phase in worktree `W` causes the next `gantry greeting` invocation to offer continuation in `W`; choosing it appends `run.resumed` with the prior Run id and `W`, retains spent correction attempts, and keeps `greeting#02` at `ready-for-agent` until Critic acceptance.
- [ ] Workflow integration tests prove preflight emits `run.started`; an accepted continuation emits `run.resumed` with the prior Run and preserved worktree references; and each round, phase, subagent start or stop, validated role result, review finding, refutation, Issue outcome, policy change, cancellation, and final completion emits its required `runlog.py` event. The tests assert the event sequence and payload references rather than re-testing run-log serialization.
- [ ] An isolated multi-Issue round test proves branches integrate one at a time with `--no-ff`, gates run after each integration, and a red post-merge gate stops the Run without fixing forward or marking any additional Issue done.
- [ ] Tests prove a Critic refutation records evidence, leaves the Issue blocked with its worktree preserved after the fixed correction ceiling is spent, and only a complete Critic result followed by integration can call `roadmap.py done`.
- [ ] A no-hooks execution test proves protected rules remain in prompts and Critic verification, and a hand-ticked roadmap drift is reported by `roadmap.py check` rather than repaired by reading the Run log.
- [ ] The Spec Changelog receives an English entry in the same merge, with lifecycle tests runnable from the repository.

## Blocked by

- `gantry-migration#06` — consumes validated role results and protocol-failure behavior.
- `gantry-migration#07` — consumes post-integration absolute and differential gate verdicts.
- `gantry-migration#08` — consumes Run lifecycle events and in-flight queries.

## Comments
