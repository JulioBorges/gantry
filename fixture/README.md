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
