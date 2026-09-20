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
      "implement": {"harness": "codex", "model": "gpt-5.2-codex"},
      "review": {"harness": "codex", "model": "gpt-5.2-codex"},
      "critic": {"harness": "claude-code", "model": "claude-3-7-sonnet-20250219"}
    }
  }
}
```

Configure defaults via `gantry-setup`:

```sh
python3 .agents/skills/gantry/scripts/setup.py
```

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

### Setup Options

Configure repository execution policy for Codex:

```sh
# Automated setup specifying Codex harness
python3 .agents/skills/gantry/scripts/setup.py --harness codex

# Or via npm installer
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
