# Greeting regression tests

Type: issue
Status: ready-for-agent
Slice: `greeting#03`
Spec: `.scratch/greeting/spec.md`
Created: 2026-09-13

## Parent

`greeting`

## What to build

Add `tests/test_greeting.py` covering `greet`'s happy path and its blank-name
rejection, runnable with `pytest -q` from the repository root.

## Acceptance criteria

- [ ] `pytest -q tests/test_greeting.py` passes with both cases covered.

## Blocked by

- `greeting#01`

## Comments
