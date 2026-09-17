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
- **Supported Tier**: OpenCode (planned).
- **Compatible Tier**: Codex CLI, Antigravity (`agy`).
- Do not claim unsupported tiers or automatic cross-harness parity.
