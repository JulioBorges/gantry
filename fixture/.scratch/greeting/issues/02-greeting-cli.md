# Greeting CLI

Type: issue
Status: ready-for-agent
Slice: `greeting#02`
Spec: `.scratch/greeting/spec.md`
Created: 2026-09-13

## Parent

`greeting`

## What to build

Implement `cli.py`: given exactly one positional argument, print the greeting for
that name and exit 0; given any other number of arguments, print a usage message
to stderr and exit 2.

## Acceptance criteria

- [ ] `python3 cli.py Ada` prints `Hello, Ada!` and exits 0.
- [ ] `python3 cli.py` prints a usage message to stderr and exits 2.

## Blocked by

- `greeting#01`

## Comments
