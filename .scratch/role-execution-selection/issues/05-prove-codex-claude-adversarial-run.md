# Demonstrate a Codex-hosted Run with an independent Claude Code Critic

Type: issue
Status: done
Slice: `role-execution-selection#05`
Spec: `.scratch/role-execution-selection/spec.md`
Created: 2026-09-15

## Parent

`role-execution-selection`

## What to build

Exercise the completed flow in the real fixture and publish sanitized reproducible evidence plus operator instructions, demonstrating cross-harness execution and Antigravity interoperability via `agy`.

### Files to read

- `fixture/README.md`
- `PRD.md`
- `.agents/skills/gantry/SKILL.md`
- `.agents/skills/gantry/reference/round-workflow.md`

## Acceptance criteria

- [x] A live Codex-hosted fixture records a Claude Code Critic independently reading the exact delivery revision and executing acceptance and gates, with a schema-valid result.
- [x] Automated fixture and contract tests demonstrate Antigravity role dispatch and hook interception interoperability alongside the live proof.
- [x] Evidence identifies installed versions, selections, revision, verification outcomes and limitations without secrets; simulated tests are clearly distinguished from live proof.
- [x] A known unmet fixture criterion is refuted, and its corrected delivery is accepted only after independent verification.
- [x] Recovery demonstration shows explicit Issue-role replacement or retry with preserved work and budgets; local deterministic tests also cover parallel failure isolation.
- [x] Operator documentation covers discovery, tracked defaults, overrides, preflight failures and recovery; no unsupported support tier or improved-review-quality claim is made.

## Blocked by

- role-execution-selection#04

## Comments

Draft proposal only; implementation requires operator approval.
