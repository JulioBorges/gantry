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

Normal setup actions proposed for approval:
1. Uses the explicit `--harness codex` selection; binaries and directories do not choose adapters.
2. Previews `execution.hostHarness: "codex"` and legacy default role mappings (`gpt-5.2-codex`) in `.gantry/config.json`.
3. Checks Codex discovery and provides authentication guidance; discovery does not prove invocation identity.
4. Updates only the marked Gantry section in `AGENTS.md` with Codex orchestration and defense-in-depth instructions after policy approval. It does not install native Codex hooks.

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
preflight acceptance. Both canonical workflow entries now require a resolved host
before initialization or scheduling through `host --require-resolved --json`,
adding `--host <host>` only after operator confirmation. This operational variant
exits **1** for unknown or ambiguous identity and includes the actual capability
declaration on success. The local resolved identity controls native/external
routing and capability metadata; new recorded Runs include sanitized identity
and confirmation provenance. A mismatch never writes policy or replaces roles.
Existing role preflight validates role availability separately and does not
itself prove Host Harness identity. See
[`docs/evidence/host-harness-resolution/README.md`](evidence/host-harness-resolution/README.md)
for bounded live entry evidence and separately labeled simulated dispatch coverage.

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


## Repair the saved Host Harness without changing roles

Run host identity and repository preference are separate. Selecting Claude Code for the current Run
while policy still names Antigravity does not overwrite a Codex Implementer or a custom Claude Code Critic.
Use the read-only diagnosis and setup preview before choosing a repository change:

```bash
python3 .agents/skills/gantry/scripts/execution.py host --host claude-code --json
python3 .agents/skills/gantry/scripts/setup.py --host-only --host claude-code
python3 .agents/skills/gantry/scripts/setup.py --host-only --host claude-code --apply
```

`--host` represents the operator's confirmed invocation selection. `--apply` asks a separate `y/N`
question after showing the actual proposed policy and adapter payload. It does not grant overwrite
approval. Decline and EOF preserve every file. Only `execution.hostHarness` and Gantry-owned entries in
that selected adapter can change; all role selections and other policy fields survive. Existing
`hooks.record` and `hooks.deny` event arrays determine wiring. `PreToolUse` needs denial opt-in because
its current guard cannot operate in a recording-only mode. Setup leaves `AGENTS.md` and other adapters
untouched during host-only repair and repeated approved repair produces no further changes.

Missing policy requires normal setup approval. For a full setup proposal, save reviewed JSON in a file
and invoke `setup.py --config-file /absolute/path/to/proposed-policy.json` through structured arguments.
Never construct shell commands by interpolating policy JSON or feed synthetic overwrite confirmation.
The legacy normal `--harness codex` path may initialize roles when explicitly requested; host-only repair
has no role preset path. A malformed policy or selected adapter stops before writes, including when
normal setup was asked to overwrite policy.

An ignored policy is a portability concern: setup prints a proposed tracked-policy migration and stops.
Review effective ignore rules, apply the shown exceptions intentionally, verify policy is trackable and
stage `.gantry/config.json`. Setup never changes `.gitignore`, global ignore rules or Git's local excludes.
Codex and adapters without verified automatic setup wiring receive manual workflow and independent
Critic guidance. Adapter preview and tests prove setup behavior, not live hook enforcement. Reproduce
these paths using the [CLI transcript](evidence/host-harness-resolution/setup-repair.md).
