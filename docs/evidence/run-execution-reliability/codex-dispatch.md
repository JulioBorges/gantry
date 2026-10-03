# Codex adapter compatibility — 2026-10-03

Installed CLI: Codex 0.160.0. Requested selection: Codex, `gpt-6.1-sol`, `medium`.
Observed model and effort: unknown; the CLI JSONL stream used here did not expose
execution identity. The result establishes successful requested invocation and
contract transport only. It does not prove useful implementation or Critic acceptance.

## Actual parser evidence

`test_execution_reliability.py` calls the actual binary on PATH, without a fake:

```python
cmd = execution.build_dispatch_command('codex', 'gpt-6.1-sol', 'parser check', effort='medium')
subprocess.run(cmd + ['--help'], capture_output=True, text=True, timeout=15)
subprocess.run(cmd + ['--gantry-unsupported-option'], capture_output=True, text=True, timeout=15)
```

Before correction, the generated `--effort medium` invocation exited 2 with
`error: unexpected argument '--effort' found`. After correction, generated syntax
with `--config 'model_reasoning_effort="medium"'` accepted `--help` with exit 0.
The deliberate `--gantry-unsupported-option` control returned nonzero and named the
unsupported argument. A successful help parser is syntax evidence, not model execution.

## Actual bounded role evidence

A temporary repository received an empty commit, then `git worktree add -b proof-role`
created a disposable assigned worktree. This public call ran with no wrapper or
native strict schema, with no protocol retry:

```python
execution.dispatch_role(
    'review',
    'Return a reviewer Result Contract: summary "adapter proof", blocking [], nonBlocking []. Do not invoke tools or inspect files.',
    worktree,
    selection={'harness':'codex', 'model':'gpt-6.1-sol', 'effort':'medium', 'sandbox':'read-only'},
    timeout=90,
    retry_on_invalid=False,
)
```

Returned and post-validated result:

```json
{"blocking": [], "nonBlocking": [], "summary": "adapter proof"}
```

The CLI returned exit 0 and completed the JSONL final agent-message transport.
`validate_harness_version('codex')` and an injected `subprocess.run` wrapper both
captured version `0.160.0`. These checks were run locally; environments without
Codex skip the two explicitly local parser/probe tests and establish no compatibility.

## Simulated regression boundaries

Canonical round fixtures establish Host independence, same-host bounded dispatch,
Issue-over-Run override precedence and failure preservation. Injected subprocess
fixtures establish truncated transport rejection, bounded protocol-result retry,
attributable attempt metadata and exclusion of raw results/prompts from logs.
Existing supported harness fixtures remain regression evidence, not new live
compatibility claims. Independent review, Critic and integration remain required.
