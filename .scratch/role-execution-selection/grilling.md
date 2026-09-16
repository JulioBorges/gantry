# Role execution selection — decision ledger

Status: approved

## Confirmed decisions

1. Before role selection, present the complete set of models the current execution environment can actually run, with supported reasoning effort levels.
2. The operator may independently select the harness, model and supported reasoning effort for every role. Cross-harness execution is not restricted to the Critic.
3. The Host Harness retains the Run's operator conversation, decisions and integration. For example, Codex may host the Run while Claude Code executes its Critic.
4. When a selected execution cannot proceed, preserve delivered work and pause the affected phase. Retry or a replacement execution selection requires an explicit operator decision; there is no automatic fallback.
5. A Critic running in another harness must inspect the exact delivered revision, Issue and Spec directly and be able to execute the declared gates independently. A text summary and diff alone are insufficient substitutes for this verification.
6. Before work starts, validate every selected harness/model/effort combination, including authentication and the ability to execute its role. An invalid selection prevents the Run from starting until corrected. This check proves execution capability, not review quality.
7. Persist role execution defaults in the repository's `.gantry/` directory. Present and validate those defaults for each Run; a Run-specific override does not change the saved defaults.
8. Saved role execution defaults are versioned in Git. They contain harness, model and reasoning effort choices, never credentials; each execution environment validates their availability before starting work.
9. During a Run, the operator may change execution selection for a specific role on a specific Issue. Validate the replacement before its next attempt and record the change in the Run Log; running agents and saved repository defaults remain unaffected.
10. A runtime execution failure pauses only the affected Issue. Other Issues in the current round may finish and approved deliveries may be integrated; the Run stops at the round boundary while the execution failure remains unresolved.
11. Replace the PRD's mandatory relative-strength restriction for Plan and Critic versus Implement with advisory guidance. Do not block selections using an assumed cross-family ranking; the operator retains the final choice and execution capability validation remains mandatory.

## Observed current limitations

- The shipped Codex capability declaration lists only `gpt-5.2-codex` and sets `per_role_model` to false.
- `budget.py` accepts only model IDs in the shipped capability declarations.
- The round workflow passes a model to the host-provided agent invocation but does not express a per-role harness selection.
- These observations do not establish the runtime model catalog or prove cross-harness execution support.

## Remaining confirmation

- The operator confirmed shared understanding and authorized preparation of the Spec and proposed Issues. The operator approved the Spec and five-Issue breakdown. After approval, create a branch, push it to the remote and open a PR targeting main; do not merge it.

## Investigation required for implementation planning

- Discover and verify actual model and effort availability for each supported execution environment without treating the shipped shortlist as authoritative.
- Identify native cross-harness execution mechanisms and their authentication, working-directory, result-contract and independent-gate support.
- Define how execution selections are represented in repository policy and Run Log events while retaining `gantry-setup` as the sole repository-policy writer.
- Validate the design against ADR-0004's skill-pack boundary; cross-harness role execution must not silently introduce an independent engine.

The Spec and five-Issue breakdown are approved. Issues are ready-for-agent; no implementation completion is claimed.
