# Greet a valid name

Type: issue
Status: ready-for-agent
Slice: `greeting#01`
Spec: `.scratch/greeting/spec.md`
Created: 2026-09-13

## Parent

`greeting`

## What to build

Implement `greet(name)` in `greeting.py`: it trims the given name and returns
`"Hello, <name>!"` for a non-empty result, and raises `ValueError` naming the
requirement for a blank or whitespace-only name.

## Acceptance criteria

- [ ] `greet("Ada")` returns `"Hello, Ada!"`.
- [ ] `greet("  ")` raises `ValueError` mentioning a non-empty name.

## Blocked by

- None

## Comments
