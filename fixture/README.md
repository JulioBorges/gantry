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
*Observation*: Reached the planning-approval stop. Wrote Issue files with `Status: draft` and left `ROADMAP.md` unchanged. No Run-log was created since it stopped before rounds started (state isolated/empty).
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
- **greeting#01 Greet a valid name**: `greet()` already existed at baseline. The Implementer added one trimming test. Critic proved both criteria by execution and mutation testing, accepted on attempt 1.
- **greeting#02 Greeting CLI**: `cli.py` already existed. The Implementer added subprocess tests in `tests/test_cli.py` covering one, zero and many arguments. Critic accepted on attempt 1.
- **greeting#03 Greeting regression tests**: the criterion already held. The Implementer added empty-string and trailing-exclamation guardrail tests. Critic accepted on attempt 1.

No engine, database, MCP service, automatic cleanup, automatic merge, or automatic lesson injection was used.
