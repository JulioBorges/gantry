# Status precedence, handoff continuity, and context usage

Type: issue
Status: ready-for-agent
Slice: gtp-protocol#04
Spec: [`../spec.md`](../spec.md) (spec 03, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/gtp-protocol/spec.md`](../spec.md)

## What to build

The closed status set `complete | failed | needs_handoff | blocked` with a fixed precedence — `blocked` outranks `needs_handoff`, which outranks any evaluation of completion — so one result can never be read two ways. `blocked` requires a non-empty list of questions for the operator; an empty list makes the result invalid rather than unblocked, and a valid one moves the PBI to `awaiting_operator`. `needs_handoff` requires a reason and continuity content and moves the PBI to `handoff_pending`. `complete` is a claim, not a transition.

Context usage lands here because it arrives on results. It is a three-variant union with no default, where an integration that cannot measure returns `unknown` with a reason, and self-reported usage is structurally distinct from measured usage and never establishes a watermark guarantee.

```ts
type ContextUsage =
  | { kind: "measured"; tokens: number; window: number; source: string }
  | { kind: "self_reported"; tokens: number; window?: number }
  | { kind: "unknown"; reason: string };
```

## Acceptance criteria

- [ ] A result carrying both `blocked` and completed criteria resolves as `blocked` and moves the PBI to `awaiting_operator`.
- [ ] `blocked` with an empty question list is invalid; the result does not advance anything and is not treated as unblocked.
- [ ] A result carrying both `needs_handoff` and completed criteria resolves as `needs_handoff`, retains the criteria progress, and moves the PBI to `handoff_pending`.
- [ ] `needs_handoff` without a reason or without continuity content is invalid.
- [ ] A result whose context usage is `unknown` is projected as unknown; no code path can render it as zero, and `self_reported` is never presented as a measurement.
- [ ] `complete` on its own produces no transition past implementation until the completion rule evaluates it.

## Blocked by

- `gtp-protocol#01` — provides the common envelope layer and the validation order that status and context usage are validated behind.
