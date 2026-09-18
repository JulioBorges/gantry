# Enforce Post-Critic Human Gate and Interactive Approval

Type: issue
Status: ready-for-agent
Slice: `interactive-dashboard#03`
Spec: `.scratch/interactive-dashboard/spec.md`
Created: 2026-09-18

## Parent

`interactive-dashboard`

## What to build

Enforce a mandatory human checkpoint after Critic verification completes successfully and before the Integrate phase begins. Introduce a local interactive approval endpoint (`POST /api/runs/<unit>/<run>/issues/<issue>/approve`) and approval marker synchronization, enabling operator approval via either a single-click dashboard button or the terminal harness conversation.

### Files to read

- `.agents/skills/gantry/scripts/dashboard.py`
- `.agents/skills/gantry/scripts/runlog.py`
- `.agents/skills/gantry/reference/round-workflow.md`
- `tests/test_dashboard.py`
- `site/tests/dashboard.spec.ts`

## Acceptance criteria

- [ ] When Critic verification succeeds, the ticket halts in an `Awaiting Operator` state before starting Integrate.
- [ ] Ticket cards and the detail modal display prominent `Awaiting Operator` alerts and an active "Aprovar Gate" button.
- [ ] `POST /api/runs/<unit>/<run>/issues/<issue>/approve` records an approval marker in `~/.gantry/state/<unit>/approvals/<issue>.json` and appends an `operator.approved` event into the Run log.
- [ ] A `wait-gate` script detects the approval marker (or explicit terminal input) and immediately unblocks the harness process to begin Integrate.
- [ ] Server unit tests verify approval marker creation and loopback host restrictions; Playwright tests verify UI button interaction.

## Blocked by

- interactive-dashboard#01
- interactive-dashboard#02

## Comments

Draft proposal only; implementation requires operator approval.
