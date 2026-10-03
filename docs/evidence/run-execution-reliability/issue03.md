# Issue 03 — Active Host result continuation evidence

The canonical workflow remains the authority for role consumption and serial integration. The
Host adapter owns conversation/transport lifetime. There is no additional scheduler or daemon.

## Deterministic simulated Host coverage

`tests/test_result_continuation.py` exercises the public canonical workflow with real temporary Git
repositories, Result Contract validation, Run append/query commands, acceptance extraction, gates,
serial branch integration and `roadmap.py done`. Model roles and conversational status steering are
simulated. The post-Critic approval case runs the actual approval wait and marker writer.

Coverage includes deliberately delayed completion and status steering without another message;
completed Issue and merged branch state; refutation, malformed contracts, execution unavailability
and a red integration gate; configured approval with the Issue still unfinished during the wait;
explicit interruption and same-Run result reconciliation; stale revision refusal; rejection of a
late result after Run closure; and explicit unknown availability for legacy absent observations.

Existing canonical correction/resume tests continue to prove spent-budget accounting. Result reuse
never overrides those counts or treats observational logs as completion authority.

## Bounded live role trace

The opt-in `python3 tests/manual/result_continuation_trace.py` runs the actual installed Codex CLI
via the shipped bounded `execution.py dispatch` boundary, selected `gpt-6.1-sol`, effort `medium`.
It then returns the role result through the canonical Node Host driver. Only the Critic invocation
is live; Implement/Review and conversational status steering remain fixtures.

- `issue03-bounded-trace.json`: the first 90-second invocation timed out. The workflow paused,
  preserved the ready-for-agent Issue and clean branch, and emitted no completed-delivery claim.
- `issue03-bounded-trace-second.json`: the 180-second invocation returned a valid Critic refutation.
  The same invocation automatically observed and consumed it, recorded the refutation and respected
  its zero correction ceiling. No further operator message was needed. The Issue remained unfinished.

The live trace establishes bounded transport/result consumption while the Host remains active.
It does not establish accepted live code delivery, server-side model identity or conversational
continuation after closing a Host. Accepted delivery/integration is established by the separate
real-Git simulated-role cases. Event-only traces omit prompts, process streams, source diffs and
credentials; model progress remains unknown.
