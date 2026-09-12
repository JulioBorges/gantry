# Python adapter set

Type: issue
Status: ready-for-agent
Slice: verification-adapters#07
Spec: [`../spec.md`](../spec.md) (spec 12, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/verification-adapters/spec.md`](../spec.md)

## What to build

Adapters for Ruff, pytest, Import Linter, pip-audit, and the configured license check, on the same terms as the TypeScript and JavaScript set: native output translated into the normalized finding shape, per-adapter declared coverage, severity mapping, and absolute-rule flagging. Approved commands must run under both uv and pip.

The same conformance-test discipline applies — each adapter is proven against recorded real tool output rather than a live tool run. That is this spec's deliberate exception to the standing test seam, scoped to adapter parsers only; the behavioral assertions still go through the operation core and the shared seam holds everywhere else.

## Acceptance criteria

- [ ] Each of the five adapters parses recorded real output into normalized findings and passes a conformance test against fixture files with no live tool invocation.
- [ ] Severity mapping from each tool's native levels is table-driven and covered by a test per tool.
- [ ] Every produced report carries a `declaredCoverage` string naming what its tool actually examines.
- [ ] The same approved command executes under both uv and pip without rewriting, proven for both.
- [ ] A failing pytest run yields findings plus its mandatory-test outcome; a crashed tool yields `adapter_failure` with a classification, never findings.
- [ ] Identities produced from two runs over the same fixture are identical.

## Blocked by

- `verification-adapters#01` — the `CheckAdapter` interface, the normalized finding shape, and the adapter failure outcome these parsers target.
- `repository-readiness#04` — the approved verification command reference and its declared coverage.
