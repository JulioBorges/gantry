# Invocation host binding evidence

On 2026-09-30, this implementation ran the executable canonical round entry from
its actual Codex conversation, explicitly selecting `codex` against an isolated
repository with a saved `antigravity` preference. Reproduce the bounded proof:

```sh
python3 scripts/prove-host-entry.py --host codex
```

`live-entry.json` is sanitized output of that real invocation. The command uses
real `execution.py host`, the actual capability file and real Run-log lifecycle
commands in a temporary Git repository. It executes an empty round and forbids
role invocations. It proves stale-preference entry, capability binding, unchanged
policy/roles and sanitized Run metadata. It does not prove automatic host detection,
provider authentication, real external role execution or an implemented Issue.
The active checkout policy is never written by this proof.

`tests/test_workflow_host_binding.py` separately exercises both entry paths through
the canonical workflow smoke seam. Host resolution and Result Contract validation
are real subprocesses. Role agents and external dispatch results are simulated;
Codex-host/Claude-Code-Critic routing, custom model/effort, Issue precedence and
invalid external results are regression coverage, not live cross-harness proof.
Concurrent Run tests execute real lifecycle commands with distinct worktrees and
Run IDs. Existing execution-selection and preflight suites retain independent
role precedence, readiness and availability checks.
