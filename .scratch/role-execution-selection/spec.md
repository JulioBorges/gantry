# Spec: Role execution selection

Type: spec
Status: approved
Map: `ROADMAP.md` (spec 12)
Source: `PRD.md` §6.1 and §12; `grilling.md`; ADR-0006
Created: 2026-09-15

## Blueprint

### Context

Operators cannot select the complete executable model catalog in Codex, use Antigravity (`agy`) as an execution or host harness, or assign another harness to a role. The shipped Codex declaration names only `gpt-5.2-codex`, `budget.py` rejects undeclared models, Antigravity tools and lifecycle hooks lack native `guard.py` handling, and round invocations carry a model without a role-specific harness. The operator needs cross-harness freedom (such as a Codex-hosted Run with a Claude Code Critic, or Antigravity-hosted Runs and Critic executions), backed by clean context isolation and guard rails.

### Architecture

The Host Harness retains the conversation, scheduling and serial integration. Bounded native harness invocations execute roles; no independent execution engine is introduced. Initial execution integrations cover Codex CLI, Claude Code, OpenCode and Antigravity (`agy`), subject to verified local capabilities; unsupported versions are reported explicitly rather than treated as supported.

For Antigravity, compatibility spans both Host Harness and Execution Harness roles. A static capability file `capabilities/antigravity.json` declares the harness identity, skills path, and supported hook events. `setup.py` detects Antigravity (via `.agents/` or the `agy` CLI) and generates or merges `.agents/hooks.json` to wire `PreToolUse` to `guard.py PreToolUse --json`. `guard.py` explicitly normalizes Antigravity tool calls (`run_command` via `CommandLine`, `write_to_file` and `replace_file_content` via `TargetFile`, `CodeContent` and `ReplacementContent`), enforcing protections on `ROADMAP.md`, `Status:` lines, checkbox lines, and git hook bypass attempts, returning JSON decisions (`allow`/`deny` with reason and exit code 0). Subagent lifecycles invoked via `invoke_subagent` are recorded into the Run log (`subagent.started` and `subagent.stopped`). When executing roles on Antigravity, strict context isolation is maintained by dispatching headless subprocess invocations (`agy --print --model <model> [--effort <effort>] --output-format json --dangerously-skip-permissions "<prompt>"`) whose outputs are validated against the Result Contract via `result.py`.

Separate runtime model discovery from static harness capability declarations. Discovery returns all executable model IDs exposed by the effective environment, supported reasoning effort values, evidence source and freshness. It handles pagination and environment/provider differences (including `agy models`). Unknown availability is not executable availability; if complete discovery cannot be established, report the limitation and block affected selection instead of presenting a static shortlist as complete. Do not infer capability from a model name or fabricate effort levels.

Persist sparse role defaults under `execution.roles` in tracked `.gantry/config.json`, written through `gantry-setup` and `setup.py`. Each selection contains `harness`, `model` and optional `effort`; omission means the harness's verified default. Preserve unrelated policy, including Caveman opt-in. Track only repository policy and intentional reusable templates; keep transient discovery and execution state outside tracked policy. Adjust the current root `.gantry/` ignore rule to allow canonical policy without broadly including local state.

Resolution order is Issue-role override, Run-role override, repository role default, then explicitly confirmed environment default. Cover Plan, Implement, Review and Critic and their derived roles (Requirement Critic, Plan Critic, research and Learner). Learner retains its existing Critic inheritance unless explicitly overridden. Display effective selections before work and validate every combination, authentication, working directory, tools and result handling. A failed preflight starts no implementation work. Relative model strength is advisory, never a guessed cross-family ranking.

External roles receive canonical Issue/Spec paths, the assigned working directory, delivery revision where applicable, role instructions and the existing Result Contract. Validate returned results with `result.py` even when the external harness supports structured output. Critic independently inspects that revision and executes acceptance and gates; a summary/diff is insufficient. Existing policies govern edits, command execution and approval; role dispatch must not silently bypass them. Native or configured fallback must not silently replace the selected model. Verify effective execution identity when the harness exposes it; an unverifiable identity cannot be claimed as confirmed.

Execution failures preserve the worktree and pause the affected Issue separately from Critic refutation or invalid-result protocol failures. Other Issues finish and accepted deliveries integrate, but no next round starts with unresolved failure. Retry or replacement requires an operator decision. An Issue-role replacement applies to the next invocation, is revalidated and logged, leaves running agents/defaults unchanged, and does not reset correction budgets. Run Log events identify requested/effective selection, Issue, role and changes without credentials or raw command output.

### Constraints

- Dependency-free workflow scripts and native harness facilities preserve ADR-0004's skill-pack boundary.
- No authentication material is stored in Git, model catalogs, prompts or Run Log events.
- Static capability files alone cannot prove current account availability or model strength.
- `budget.py` uses verified model context metadata; absent metadata blocks planning with an actionable error rather than inventing a window or weakening the budget gate.
- Setup remains the sole repository-policy writer; no settings UI or mutating dashboard is added.
- Report runtime evidence separately from local fixture coverage. Do not promote harness support tiers without the required full-loop proof.

## Contract

### Definition of Done

- [ ] Complete available-model and supported-effort selection replaces static shortlists, including actionable discovery failure handling across Codex, Claude Code, OpenCode and Antigravity.
- [ ] Antigravity capability declaration (`capabilities/antigravity.json`), `guard.py` hook payload normalization for Antigravity tools, and `.agents/hooks.json` setup generation establish host and execution foundation.
- [ ] Versioned defaults survive cloning and setup merges, with validated Run and Issue overrides and no credentials.
- [ ] Every role can select a supported execution harness (including Antigravity CLI) independently of the Host Harness and satisfy its Result Contract in an isolated context.
- [ ] A real Codex-hosted delivery is independently inspected by a Claude Code Critic that executes acceptance and gates on the exact revision, with interoperability verified for Antigravity.
- [ ] A runtime failure isolates the affected Issue, preserves its work, requires explicit recovery and blocks the next round while unresolved.
- [ ] Local regression coverage and sanitized live evidence demonstrate the contract without changing completion authority or correction budgets.

### Regression Guardrails

- Existing repositories without execution policy remain usable through explicit environment-default confirmation.
- Existing result validation, bounded corrections, serial integration and post-merge gates retain their semantics.
- Only roadmap scripts write authoritative Issue status and completion checkboxes.
- Caveman settings, hook decisions and unrelated repository policy survive setup updates.
- Existing Invalid Result protocol handling remains separate from execution unavailability.

### Scenarios

```gherkin
Scenario: Complete Codex selection
  Given an effective Codex environment exposes several executable models and effort levels
  When the operator selects a role execution
  Then every exposed executable model and its supported effort levels is offered
  And unsupported effort values are rejected

Scenario: Antigravity model discovery and role execution
  Given an effective Antigravity environment exposes executable Gemini models and effort levels via agy
  When the operator selects a role execution for Antigravity
  Then every exposed executable model and its supported effort levels is offered
  And the role executes headlessly in an isolated subprocess with strict Result Contract validation

Scenario: Invalid saved selection
  Given a clone contains saved role defaults unavailable to the current account
  When preflight validates the selections
  Then no implementation starts
  And the operator receives the failing selection and recovery options

Scenario: Independent external Critic
  Given Codex hosts the Run and Claude Code is selected for Critic
  When an Issue reaches adversarial review
  Then Claude Code inspects the exact delivered revision and canonical Issue and Spec
  And executes acceptance and gates independently
  And a validated Critic result controls subsequent integration eligibility

Scenario: Execution failure during a round
  Given two independent Issues are running
  When one Issue's selected harness fails to execute its Critic
  Then that Issue's work is preserved and paused without automatic fallback
  And the other Issue may finish and integrate after approval by its Critic
  And the next round cannot begin while the execution failure remains unresolved

Scenario: Explicit Issue-role replacement
  Given an Issue is paused and has already spent one correction attempt
  When the operator selects and validates another Critic execution for that Issue
  Then the next invocation uses the replacement and records the change
  And the spent correction count, running agents and repository defaults are unchanged
```

## Out of Scope

- Independent engines, databases, persistent execution supervisors, credential management and automatic fallback.
- Automated claims that a different model improves adversarial quality; execution proof does not establish comparative effectiveness.
- Automatic target-branch merges, cleanup, model-strength rankings or universal harness parity.
- Frontend changes; any later UI scope amendment requires approval and Playwright validation.

## Changelog

- 2026-09-16 — Updated with operator-confirmed Antigravity compatibility: Host Harness hook integration, capability declaration, model discovery and headless role execution via `agy`.
- 2026-09-15 — Draft based on the operator-confirmed interview; Spec and five-Issue breakdown approved by the operator.
- 2026-09-15 — Operator approved the Spec and five-Issue breakdown; implementation remains pending.
