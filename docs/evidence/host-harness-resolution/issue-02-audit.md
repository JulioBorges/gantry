# Issue #02 independent implementation audit

This audit was performed on 2026-09-30 in the approved
`feat/host-harness-resolution` worktree. The Run baseline was
`0728e480d590f011d949819ec7579916d4a3b1cd`. Existing delivery commits
`de8d47b`, `a9f130f` and `ca1bcd7` supply workflow binding, base Plan selection
preservation and Research selection preservation respectively. This audit does
not establish Critic acceptance or change Issue execution state.

## Acceptance criterion evidence

1. Both canonical entries call the real public host CLI before other commands or
   agents. `test_both_entries_stop_before_commands_or_agents_when_host_unresolved`
   exercises missing and unsupported identities for both entries and observes no
   work commands or agent calls. Host resolution occurs once per entry.
2. `test_selected_host_capabilities_win_over_stale_policy_without_writes`
   selects Claude Code against a saved Antigravity preference, checks the actual
   capability metadata and byte-for-byte unchanged policy. Both entries return
   the mismatch; their instructions also report it to the operator.
3. The planning and round routing tests in `test_workflow_host_binding.py`
   exercise native Codex selection and external Claude Code Critic dispatch,
   preserve model and effort, and reject invalid external Result Contracts.
   External dispatch results in this seam are simulated, not live provider proof.
4. The role defaults and dispatch suites retain base/derived role choices,
   Issue-over-Run-over-policy precedence, availability/authentication failures
   and explicit replacements. Host binding tests independently cover Research
   inheritance, Research override, external Research text, planner selection and
   round Issue override. Existing policy tests retain sparse defaults and custom
   policy fields. Resolving a host does not alter these independent checks.
5. Concurrent host-binding tests use real lifecycle commands with separate
   worktrees and Run IDs. They verify separate host records, actual capability
   tiers and sanitized provenance. Public host CLI tests exercise inherited hints
   and malformed/unsupported input without disclosing raw values.
6. Canonical workflow coverage includes both entries and failure before work.
   `python3 scripts/prove-host-entry.py --host codex` was rerun successfully from
   the actual Codex conversation. Its sanitized output matches `live-entry.json`:
   Codex effective host, Antigravity saved preference, mismatch, supported tier,
   unchanged policy and roles, zero role invocations and four lifecycle events.
   This real empty-round proof does not establish live external role execution.

## Current validation and regression repair

The approved public CLI and canonical workflow smoke seams remain unchanged.
These independently executed suites passed:

```sh
python3 -m unittest tests.test_workflow_host_binding tests.test_cross_harness_proof tests.test_role_execution_dispatch -q
# Ran 35 tests; OK.
python3 -m unittest tests.test_role_execution_defaults tests.test_host_resolution_cli tests.test_common_policy tests.test_canonical_gantry_workflow -q
# Ran 66 tests; OK.
```

Tracking the already approved repository policy exposed a fixture assumption:
the no-policy legacy smoke test expected `git archive HEAD` to omit
`.gantry/config.json`. The existing test failed before the repair with
`AssertionError: True is not false`. Commit `fd3947d` removes the policy only from
the extracted temporary repository, then retains all absence, default mapping,
frontier and canonical workflow assertions. The source repository policy is
untouched. The same test passed after the repair:

```sh
python3 -m unittest tests.test_legacy_workflow_smoke.LegacyWorkflowSmokeTests.test_no_policy_smoke_runs_canonical_workflow_on_tracked_repository_copy -v
# Ran 1 test; OK.
```

No frontend code changed. Full gate execution uses the approved Run baseline;
its result belongs to the Implementer Result Contract and remains subject to
independent Reviewer and Critic verification:

```sh
python3 .agents/skills/gantry/scripts/gates.py --run --diff-base 0728e480d590f011d949819ec7579916d4a3b1cd --json
```
