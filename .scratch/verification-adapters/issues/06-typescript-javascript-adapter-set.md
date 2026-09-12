# TypeScript and JavaScript adapter set

Type: issue
Status: ready-for-agent
Slice: verification-adapters#06
Spec: [`../spec.md`](../spec.md) (spec 12, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/verification-adapters/spec.md`](../spec.md)

## What to build

Adapters for TypeScript compilation, ESLint with typescript-eslint, Vitest, dependency-cruiser, and the configured license check. Each translates its tool's native JSON into the normalized finding shape, declares what its tool actually examines, and carries its own severity mapping into blocker, major, minor, and info plus its own absolute-rule flagging. Adapters never derive problem identity themselves; they emit the normalized fields and identity derivation happens in the shared layer.

Approved commands must run unmodified under npm, pnpm, and yarn. Every adapter ships a conformance test against recorded real tool output rather than a live tool run — this spec holds a deliberate exception to the standing test seam for adapter parsers, and only for them. The behavioral assertions still go through the operation core, and the shared seam applies everywhere else.

## Acceptance criteria

- [ ] Each of the five adapters parses recorded real output into normalized findings and passes a conformance test against fixture files with no live tool invocation.
- [ ] Severity mapping from each tool's native levels is table-driven and covered by a test per tool.
- [ ] Every produced report carries a `declaredCoverage` string naming what its tool actually examines; generic tool support is nowhere presented as complete analysis coverage.
- [ ] The same approved command executes under npm, pnpm, and yarn without rewriting, proven for all three.
- [ ] A failing Vitest run yields findings plus its mandatory-test outcome; a crashed tool yields `adapter_failure` with a classification, never findings.
- [ ] Identities produced from two runs over the same fixture are identical.

## Blocked by

- `verification-adapters#01` — the `CheckAdapter` interface, the normalized finding shape, and the adapter failure outcome these parsers target.
- `repository-readiness#04` — the approved verification command reference and its declared coverage.
