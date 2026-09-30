# Role Execution and Cross-Harness Guide

Operate and configure multi-harness execution in Gantry runs.

## Architecture

- Host harness (Codex, Claude Code, OpenCode, Antigravity) retains operator interaction, scheduling, and serial integration.
- Bounded native CLI invocations execute roles (`plan`, `implement`, `review`, `critic`, `learner`).
- Every execution harness must satisfy the Result Contract (`result.py`).
- Critic independently inspects the delivery revision and executes acceptance criteria and differential gates.
- No automatic fallback between harnesses or models.
- Model diversity does not imply improved review quality (ADR-0006).
- No secrets or credentials in tracked repository policy or Run logs.

## Runtime Model Discovery

Query available executable models and supported reasoning effort levels before planning:

```sh
python3 .agents/skills/gantry/scripts/discovery.py <harness> --json
```

Supported harnesses:
- `codex`: invokes `codex models`
- `claude-code`: queries local Claude Code CLI capabilities
- `opencode`: invokes `opencode models`
- `antigravity`: invokes `agy models`

Unknown availability fails closed: do not guess models or fabricate effort levels.

## Tracked Repository Defaults

Set versioned role defaults under `execution.roles` in `.gantry/config.json`:

```json
{
  "execution": {
    "roles": {
      "implement": {"harness": "codex", "model": "gpt-5.6-terra"},
      "review": {"harness": "codex", "model": "gpt-5.6-astra"},
      "critic": {"harness": "claude-code", "model": "claude-sonnet-5"}
    }
  }
}
```

Configure defaults through the `gantry-setup` skill (recommended) by sending
this prompt in your coding harness:

```text
/gantry-setup
```

During setup, request role defaults for this repository and verify each selected
harness, model, and effort before approving the proposed policy.

For automation or low-level diagnostics, the equivalent config writer is
available through the Python CLI:

```sh
python3 .agents/skills/gantry/scripts/setup.py --harness codex --verify-auth
```

Direct script use does not provide the skill's conversational review and
approval flow. See [Using Gantry](usage.md) for the interface boundary.

Inheritance rules:
- `requirement-critic` and `plan-critic` inherit `critic` defaults unless overridden.
- `learner` inherits `critic` defaults unless overridden.
- `research` inherits `plan` defaults unless overridden.
- Omitted fields inherit the verified environment default.

## Role Overrides

Override roles for a Run or specific Issue without mutating tracked repository policy:

1. Run override: pass `args.models` or configure during preflight prompts.
2. Issue override: set `issueRoleReplacements` in workflow invocation or Issue frontmatter.
3. Effective resolution order: Issue override → Run override → repository policy (`.gantry/config.json`) → environment default.

## Preflight Validation and Failures

Preflight validates all role selections before implementation starts:
1. Verify CLI installation and minimum version.
2. Verify local authentication.
3. Validate model existence in discovered catalog.
4. Validate requested reasoning effort against supported levels.

When validation fails:
- Preflight aborts and starts no implementation work.
- Review reported error and adjust `.gantry/config.json` or CLI environment.

## Runtime Execution Failures and Operator Recovery

Differentiate failure types:
- **Critic Refutation**: normal adversarial rejection; increments `correctionsSpent`.
- **Protocol Failure**: invalid Result Contract schema; handled via `result.py`.
- **Runtime Execution Failure**: process crash, network error, or missing CLI.

Execution failure behavior:
1. Affected Issue pauses immediately (`issue.paused`).
2. Worktree and branch are preserved intact.
3. Independent Issues continue implementation, review, Critic verification, and serial integration.
4. Next round is blocked while unresolved failures exist.

Recover from execution failure:
1. Inspect paused Issue and failure reason in Run log or dashboard.
2. Specify explicit replacement via `issueRoleReplacements`:
   ```json
   {
     "issueRoleReplacements": {
       "<issue-ref>": {
         "critic": {"harness": "antigravity", "model": "gemini-3.1-pro-high", "effort": "high"}
       }
     }
   }
   ```
3. Resume Run from `priorRun`.
4. Gantry validates replacement (`validate_role_replacement`), logs `role.changed`, preserves spent correction budget, and retains repository defaults.

## Support Tiers

- **Reference Tier**: Claude Code (full-loop proven on reference fixture).
- **Supported Tier**: Codex CLI (hybrid runner via `codex exec`, independent Critic verification, defense-in-depth git hooks), Antigravity (`agy`), OpenCode (planned).
- **Compatible Tier**: Cursor.
- Do not claim unsupported tiers or automatic cross-harness parity.

## Codex Installation, Setup, and Supported Capabilities

### Installation Commands

Ensure the Codex CLI is installed and available on `PATH`:

```sh
npm install -g @openai/codex
```

Verify authentication and login status:

```sh
codex login
codex login status
```

Verify installed version meets the minimum requirement (`0.1.0`):

```sh
codex --version
```

### Setup via skill (recommended)

In the Codex conversation, send:

```text
/gantry-setup
```

Select Codex as the Host Harness, verify authentication and model discovery,
then review the complete policy before approving it.

### Setup via Python CLI (advanced/manual)

Configure repository execution policy for Codex:

```sh
python3 .agents/skills/gantry/scripts/setup.py --harness codex --verify-auth
```

The npm command below installs the skills; it does not run repository setup:

```sh
npx @julioborges/gantry add --agent codex --yes
```

Setup actions executed:
1. Detects `codex` CLI on `PATH` or `.codex` directory.
2. Writes `execution.hostHarness: "codex"` and default role mappings (`gpt-5.2-codex`) to `.gantry/config.json`.
3. Verifies model discovery via `python3 .agents/skills/gantry/scripts/discovery.py codex`.
4. Injects Codex host orchestration rules and defense-in-depth git hooks into `AGENTS.md`.

### Supported Capabilities

- **Tier**: Supported.
- **Process Runner**: Hybrid subprocess runner executing bounded CLI invocations (`codex exec <prompt> --model <model>`) with timeout and error capture.
- **Per-Role Models**: Supports role-specific models (`gpt-5.2-codex`, `gpt-5-codex`) and reasoning effort levels (`low`, `medium`, `high`).
- **Independent Verification**: Works with independent Critic models across harnesses (ADR-0006) to verify acceptance criteria and quality gates (`acceptance.py`, `gates.py`).
- **Defense in Depth**: Protects repository branches and `ROADMAP.md` via tracked git hooks (`pre-commit`, `pre-push`) and adversarial Critic refutation.

## Read-only Host Harness diagnosis

The Host Harness owns the operator conversation and Run coordination. It is
separate from saved `execution.hostHarness` preferences and role selections.
Inspect it without changing policy, adapters or machine-level Run state:

```sh
python3 .agents/skills/gantry/scripts/execution.py host --cwd /absolute/repository --json
python3 .agents/skills/gantry/scripts/execution.py host --cwd /absolute/repository --host claude-code --json
```

`--host` is the operator-confirmed selection for this invocation. Supported
identifiers are `antigravity`, `claude-code`, `codex` and `opencode`; each uses
this same explicit-selection path. Passing the flag is an assertion by the
caller, not verification that that program owns the conversation. Select the
harness actually hosting the conversation, independently of the role defaults.
A saved Antigravity preference with `--host claude-code` reports
`status: resolved`, `effectiveHost: claude-code`, `savedPreference: antigravity`
and `mismatch: true`. It leaves the preference and all roles unchanged. Updating
the saved preference requires a separate setup proposal.

The structured result exposes `status`, `effectiveHost`, `savedPreference`,
`mismatch`, `sources` and `diagnostics`. Source entries contain fixed identifiers,
a kind (`explicit`, `preference` or `hint`) and a supported host or null. Raw
environment values, binary paths, process output and policy contents are not
included. `mismatch` is true only when a resolved host differs from a saved one.

No verified current-invocation evidence adapter is available for these four
integrations in this delivery. There are no `verified` source entries and no
automatic `resolved` result. Binary presence, common repository skill directories,
saved policy and inherited environment hints cannot prove the current host.
Environment hints inspected by presence are `CODEX_THREAD_ID`, `CODEX_HOME`,
`CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`, `OPENCODE_SESSION_ID` and
`ANTIGRAVITY_SESSION_ID`. These can survive nested invocations; they are always
hints. Common directories are also hints and never identify a host. Missing or
single-host hints return `unknown`; hints identifying multiple hosts return
`ambiguous`. The latter is a conflict between hints, not conflicting verified
invocation evidence. An explicit supported choice resolves either result.

Diagnostic exits differ from operational blocking: inspection exits **0** for
`resolved`, `unknown` and `ambiguous`, allowing operators to inspect inconclusive
results. Unsupported explicit or saved identifiers and malformed/unreadable
policy return `invalid` and exit **1**, without overwrite or fallback. Invalid
policy diagnostics intentionally omit parser details that could expose values.
The diagnostic command neither launches roles nor establishes operational
preflight acceptance. Operational workflow entry must require a resolved host;
that integration is a subsequent delivery. Existing role preflight validates
role availability separately and does not itself prove Host Harness identity.

To reproduce isolated hints rather than accidentally using the developer's
environment, run the subprocess tests:

```sh
python3 -m unittest tests.test_host_resolution_cli -v
```

Tests use temporary Git repositories, an isolated environment, a fixture binary
and simulated inherited hints. They verify explicit selection, inconclusive and
conflicting hints, stale preferences, invalid input, sanitized provenance and
byte preservation of policy, adapters and state. They establish CLI behavior,
not live automatic host detection. Real-host evidence must state that explicit
selection was used when no trustworthy adapter exists.
