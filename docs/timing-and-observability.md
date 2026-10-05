# Attributable Run State and Truthful Timing

Gantry provides honest, attributable Run state and non-overlapping timing across the CLI, Run logs, read-only data endpoints, and Dashboard.

## Core Principles

1. **Active Phase Work vs. Wall Time**:
   - `phaseDurations` records strictly the active execution intervals spent within each phase (`Plan`, `Implement`, `Review`, `Critic`, `Integrate`).
   - `pausedSeconds` records intervals where an Issue was explicitly paused (`issue.paused`) awaiting external verification prerequisites or operator intervention.
   - `wallClockSeconds` / `totalCycleSeconds` records total elapsed wall-clock time from initial phase start to completion or present observation, without attributing paused or waiting intervals to model reasoning or phase execution.

2. **Truthful Waiting Causes**:
   - **Verification Pauses** (`verification-paused`): Triggered by missing declared external verification capabilities (e.g. Docker, network auth, hardware probes). The phase work interval freezes and does not consume a code correction attempt.
   - **Decision Required** (`decision-required`): Triggered strictly when an operator decision is explicitly configured and awaited (`operator.waiting`). Critic completion alone never creates an operator decision or approval state.
   - **Result Pending Integration** (`result-pending-integration`): Indicates that an accepted Critic result or role result is ready (`role.result.ready`) and awaiting Host handling or integration (`role.result.consumed`). It confers no operator approval requirement.

3. **Non-Overlapping and Non-Inflated Timing**:
   - Parallel Issue intervals in multi-issue rounds do not sum into an inflated Run duration. Run-level duration reflects the real elapsed wall-clock span of the Run itself.
   - Correction, retry, interrupted, and resumed intervals retain attribution to their respective phases without double-counting.
   - Legacy logs lacking result-ready or paused observations remain readable without modification, and missing result intervals remain explicitly unknown rather than backfilled from completion.

4. **Incomplete Evidence**:
   - Duplicate phase starts, missing finishes, out-of-order timestamps, or post-finish records flag `timingEvidence: "incomplete"` in the reduced state and Dashboard cards, presenting visible incomplete evidence rather than invented precision.
   - Event gaps without harness-declared provenance remain `unknown/stale`. Heartbeat or keepalive events are never labelled as model reasoning or useful progress.

## Dashboard Visualization

- **Lifecycle Badges**:
  - `AWAITING OPERATOR` (Amber, pulsing) — Explicit operator decision required.
  - `PAUSED (VERIFICATION)` (Sky blue) — Verification prerequisite unavailable; displays remedy in execution modal.
  - `RESULT PENDING INTEGRATION` (Yellow) — Role result ready, awaiting Host handoff.
  - `TIMING: INCOMPLETE` (Red) — Malformed or missing lifecycle telemetry observed.
- **Duration Breakdown**:
  - Modal displays active phase work breakdown (`Plan`, `Implement`, `Review`, `Critic`, `Integrate`), `Paused` duration, and `Total` wall time with accessible labels.
- **Keyboard Navigation**:
  - Full keyboard accessibility: Tab navigation across cards, Enter/Space to open details, and Escape to dismiss modals.
