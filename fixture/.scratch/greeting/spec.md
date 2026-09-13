# Spec: Greeting

Type: spec
Status: ready-for-agent
Map: `fixture/README.md`
Source: Gantry reference fixture
Created: 2026-09-13

## Blueprint

### Context

The greeting project is a minimal Python program used only as the Gantry reference
fixture: it exists so the Gantry workflow, its gates and its dashboard have a real,
small repository to run against instead of the pack's own repository.

### Architecture

- `greeting.py` exposes `greet(name)`, returning a friendly message for a non-empty
  name and raising `ValueError` for a blank one.
- `cli.py` is a thin command-line wrapper around `greet` with one positional
  argument.
- `tests/test_greeting.py` covers both the happy path and the blank-name rejection.
- `tools/lint.py` is the fixture's own standard-library linter, declared as the
  differential quality gate in `.gantry/config.json`.

### Constraints

- The project imports only the Python standard library.
- `cli.py` prints exactly one line to stdout on success and exits 0.
- `cli.py` prints a usage message to stderr and exits 2 when not given exactly one
  argument.

## Contract

### Definition of Done

- [ ] `greet` returns `"Hello, <name>!"` for a trimmed, non-empty name.
- [ ] `greet` raises `ValueError` for a blank or whitespace-only name.
- [ ] `cli.py <name>` prints the greeting and exits 0.

### Regression Guardrails

- `greet` never returns a message without the trailing exclamation mark.
- `cli.py` never prints more than one line on success.

### Scenarios

```gherkin
Scenario: A friendly greeting is printed for a valid name
  Given the greeting CLI and the name "Ada"
  When the operator runs cli.py with that name
  Then the CLI prints "Hello, Ada!" to stdout
  And the CLI exits 0
```

## Out of Scope

- Internationalized greetings — the fixture only needs one deterministic message
  shape to exercise the Gantry workflow.
- A packaged distribution — the fixture is copied as source files, not installed.

## Changelog

- 2026-09-13 — Initial draft, written for the Gantry reference fixture.
