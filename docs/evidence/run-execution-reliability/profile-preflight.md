# Selected-profile preflight evidence

Date: 2026-10-03. Delivery: `run-execution-reliability#02`.

## Real receipt

The public `execution.py preflight --selection` path was executed in the Issue
worktree with Codex, requested model `gpt-6.1-sol`, effort `medium`, explicit
`read-only` sandbox and `--authorize-probe`. It returned exit 0, `valid=true`,
`status=verified`, and all five dimensions verified. The selected-profile probe
returned the exact expected marker in a completed Codex JSONL final agent message.
No role, repository edit, approval expansion or model fallback was requested.
The later parser-only enhancement was verified using the installed CLI's `--help`
path and the complete receipt was rerun after that enhancement.

This proves an executed profile with the requested CLI arguments. It does not
prove observed effective model/effort identity; the result explicitly labels them
unobserved. Authentication was confirmed by bounded login status, and permission
scope was an operator selection. No account capability was inferred from a model
name, capability declaration or static catalog. Raw streams and credentials are
excluded from this document and reusable evidence.

## Simulated workflow traces

`tests/test_profile_preflight.py` runs the canonical JavaScript workflow fixture
at both planning and round entry seams. Ready responses in general workflow
fixtures are explicitly labeled `simulated-workflow-fixture`; they are routing
proof, never live account availability. Refused readiness stops both native and
external agents before invocation. The fake subprocess tests separately exercise
unsupported syntax, failed auth, malformed JSONL, timeout, nonzero refusal and
fallback. These negative cases are simulated, and successful live availability
comes only from the real receipt above.

Within one Run, eight roles using an identical profile issue one set of cheap
checks and one selected-profile probe. A repeated unchanged attempt issues none.
A second Run or changed auth identity requires a new set. Model, effort,
transport, sandbox, cwd, policy, CLI and configuration identity mutations are
covered independently; missing auth identity cannot generate a cache hit.

The tests also preserve Issue > Run > repository > environment precedence;
preflight operates on the selected effective role and never changes the Host.
Issue status and roadmap are intentionally unchanged pending independent Critic
acceptance and serial integration.
