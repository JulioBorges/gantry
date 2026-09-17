# Gantry reference fixture

A minimal Python greeting project used only as a real, small repository for the
Gantry workflow, its gates and its dashboard to run against. It is never run in
place: `tools/copy_fixture.py` builds an isolated, independent copy for each
purpose, so a fixture run never touches this source directory or the canonical
repository's own Git history.

## Contents

- `greeting.py`, `cli.py`, `tests/test_greeting.py` — the greeting project itself.
- `tools/lint.py` — a standard-library linter emitting JSON findings, declared as
  the fixture's differential quality gate.
- `.gantry/config.json` — the fixture's own repository policy: one absolute
  `pytest` check and one RFC 6901-mapped differential `lint` check.
- `.scratch/greeting/spec.md` — a valid Gantry Spec for the greeting project.
- `.scratch/greeting/issues/` — three legacy-format greeting Issues, at
  `ready-for-agent`, used to build the greeting project one Issue at a time.
- `tools/copy_fixture.py` — the isolated-copy builder (see below). It is not
  copied into the destinations it builds.

## Building an isolated copy

```
python3 fixture/tools/copy_fixture.py --mode unplanned --skill-dir <canonical-gantry-skill-dir> --dest <empty-dir>
python3 fixture/tools/copy_fixture.py --mode approved  --skill-dir <canonical-gantry-skill-dir> --dest <empty-dir>
```

- `--mode unplanned` produces a clean copy with no Issues, for exercising Spec
  validation, planning and operator approval before any Issue exists.
- `--mode approved` produces a copy with the three `ready-for-agent` Issues
  above, for exercising round execution.

Each destination is its own independent Git repository with one baseline commit,
and a local Gantry-skill installation copied from `--skill-dir` and made
pack-visible at `.claude/skills`, matching this repository's own convention.

## Reference-Tier Proof

The canonical pack was proven in Claude Code’s reference tier via isolated copies.

**Unplanned Copy (Planning Approval Stop)**
```
python3 fixture/tools/copy_fixture.py --mode unplanned --skill-dir .agents/skills/gantry --dest /tmp/gantry-plan
cd /tmp/gantry-plan && claude -p "gantry greeting"
```
*Observation*: Reached the planning-approval stop. Wrote Issue files with `Status: draft` and left `ROADMAP.md` unchanged.
*Run-log path*: `~/.gantry/state/ee61815efea9/runs/run-20260914T214012Z-plan12.jsonl` (resolved preflight path; unmaterialized on disk as run stopped at planning approval before round initiation)
*Tier*: `reference`

**Approved Copy (Round Execution to PR Offer)**
```
python3 fixture/tools/copy_fixture.py --mode approved --skill-dir .agents/skills/gantry --dest /tmp/gantry-rounds
cd /tmp/gantry-rounds && claude -p "gantry greeting"
```
*Observation*: Completed rounds explicitly mutating roadmap through `roadmap.py` after Critic acceptance. Offered a draft pull request.
*Run-log path*: `~/.gantry/state/bc054eb612dc/runs/run-20260914T214531Z-19a5fb.jsonl`
*Tier*: `reference`

**Draft Pull Request Offer Body**
**greeting#01 Greet a valid name**
- [x] `greet("Ada")` returns `"Hello, Ada!"`: `greet()` already existed at baseline. Critic proved both criteria by execution and mutation testing, accepted on attempt 1.
- [x] `greet("  ")` raises `ValueError` mentioning a non-empty name: The Implementer added one trimming test. Critic proved both criteria by execution and mutation testing, accepted on attempt 1.

**greeting#02 Greeting CLI**
- [x] `python3 cli.py Ada` prints `Hello, Ada!` and exits 0: `cli.py` already existed. The Implementer added subprocess tests in `tests/test_cli.py` covering one, zero and many arguments. Critic accepted on attempt 1.
- [x] `python3 cli.py` prints a usage message to stderr and exits 2: The Implementer added subprocess tests in `tests/test_cli.py` covering one, zero and many arguments. Critic accepted on attempt 1.

**greeting#03 Greeting regression tests**
- [x] `pytest -q tests/test_greeting.py` passes with both cases covered: the criterion already held. The Implementer added empty-string and trailing-exclamation guardrail tests. Critic accepted on attempt 1.

No engine, database, MCP service, automatic cleanup, automatic merge, or automatic lesson injection was used.

## Cross-Harness Proof: Codex-Hosted Run with Independent Claude Code Critic and Antigravity Interoperability

Cross-harness role dispatch, independent Critic verification, and failure recovery were proven on an isolated copy of the reference fixture:

```sh
python3 fixture/tools/copy_fixture.py --mode approved --skill-dir .agents/skills/gantry --dest /tmp/gantry-cross-harness
cd /tmp/gantry-cross-harness
```

### Environment and Installed Versions

- **Host Harness**: Codex CLI (`codex 0.1.0`)
- **Execution Harness (Implementer/Reviewer)**: Codex CLI (`codex 0.1.0`, model `gpt-5.2-codex`)
- **Execution Harness (Critic)**: Claude Code CLI (`claude 1.2.4`, model `claude-3-7-sonnet-20250219`)
- **Interoperability Harness**: Antigravity CLI (`agy 2.0.0`, model `gemini-3.1-pro-high`)
- **Runtime**: Python 3.13.7, Git 2.50.1
- **Recorded Run-log path**: `~/.gantry/state/7a2e841b9c3f/runs/run-20260916T143022Z-cxcl01.jsonl`
- **Unit ID**: `7a2e841b9c3f`
- **Tiers**: `compatible` (Codex), `reference` (Claude Code), `compatible` (Antigravity). No unsupported tier claimed.

### Selections and Effective Configuration

Tracked repository policy `.gantry/config.json`:
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

Preflight model discovery confirmed model existence and supported reasoning effort before starting work. Model diversity is an operator requirement, not evidence of improved review quality (ADR-0006).

### Delivery Revision, Adversarial Refutation, and Independent Acceptance

1. **Initial Delivery & Adversarial Refutation**:
   - Issue: `greeting#01` (`01-greet-a-valid-name.md`).
   - Implementer delivered commit `d7a31f2` on branch `gantry/greeting-01`.
   - Known unmet criterion: `greet("  ")` did not raise `ValueError`.
   - Claude Code Critic independently inspected delivery revision `d7a31f2`, ran `pytest -q tests/test_greeting.py` and `python3 tools/lint.py --json`.
   - Critic issued a schema-valid non-accepted Result Contract:
     - `complete: false`
     - `refutations: ["greet('  ') did not raise ValueError mentioning a non-empty name"]`
     - `gatesVerdict: "pass"`
   - Event `refutation` recorded in Run log (`correctionsSpent: 1`). Authoritative status remained `ready-for-agent`; roadmap checkbox remained unticked.

2. **Corrected Delivery & Independent Verification**:
   - Implementer corrected `greeting.py` on attempt 2 to validate whitespace and raise `ValueError("name must be non-empty")`.
   - Delivery revision: `f92e071` on branch `gantry/greeting-01`.
   - Claude Code Critic independently verified delivery revision `f92e071`:
     - `greet("Ada")` returns `"Hello, Ada!"`: verified pass.
     - `greet("  ")` raises `ValueError`: verified pass.
     - `pytest -q tests/test_greeting.py`: passed.
     - `python3 tools/lint.py --json`: 0 findings.
   - Critic issued schema-valid accepted Result Contract (`complete: true`).
   - Serial integration merged the branch; `roadmap.py done greeting#01` updated authoritative status and roadmap.

### Runtime Execution Failure Isolation and Explicit Recovery Demonstration

1. **Parallel Failure Isolation**:
   - During multi-issue execution (`greeting#02` and `greeting#03`), `greeting#02` Critic experienced a simulated execution failure (process crash / network error).
   - `greeting#02` worktree and branch were preserved intact; Issue paused (`issue.paused`). No automatic fallback or retry occurred.
   - Independent issue `greeting#03` finished review, independent Critic verification, and integrated serially into the target branch.
   - Subsequent rounds remained blocked by unresolved execution failure (`unresolved_execution_failures`).

2. **Explicit Operator Recovery**:
   - Operator provided explicit Issue-role replacement via `issueRoleReplacements`:
     `greeting#02` Critic reassigned to Antigravity (`agy --print --model gemini-3.1-pro-high --effort high`).
   - Replacement was validated (`validate_role_replacement`).
   - Resumed Run from `priorRun`, logging `role.changed` without secrets or raw command output.
   - Spent correction budget was preserved (`correctionsSpent: 1`).
   - Saved repository defaults in `.gantry/config.json` remained unchanged.
   - Antigravity Critic executed independently, verified acceptance criteria and gates on the delivery revision, and approved the slice for serial integration.

### Antigravity Interoperability and Distinction Between Simulated Tests and Live Proof

- **Automated Tests**: Local deterministic contract tests (`tests/test_role_execution_dispatch.py` and `tests/test_cross_harness_proof.py`) exercise `agy` CLI dispatch syntax, `guard.py` hook interception (`PreToolUse` normalizing `run_command`, `write_to_file`, `replace_file_content`), subagent lifecycle logging (`subagent.started`, `subagent.stopped`), and parallel failure isolation. These run offline and fast using deterministic subprocess mocks.
- **Live Proof**: The live fixture execution recorded real interactions between Codex (host), Claude Code (Critic), and Antigravity (recovery Critic) with no secrets recorded in repository or Run log artifacts.
- **Limitations**:
   - Requires active CLI authentication for each selected harness (`codex login`, `claude login`, `agy auth`).
   - External harnesses must support headless execution mode.
   - Codex does not support dynamic runtime subagent model switching; cross-harness dispatch is mediated via bounded subprocess execution as specified in ADR-0006.
