# Harness compatibility matrix and presence detection

Type: issue
Status: ready-for-agent
Slice: machine-setup#02
Spec: [`../spec.md`](../spec.md) (spec 05, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/machine-setup/spec.md`](../spec.md)

## What to build

Declare the compatibility matrix as validated data mapping a harness identity to its skill directory convention, its skill format, and the evidence kinds that establish presence. Build detection over a temporary `HOME` containing fixture harness installations, producing a `HarnessPresence` record per harness with its evidence and path. Classify each detected harness against the matrix as supported or unsupported, and surface the whole inventory through a core operation and a CLI report.

Detection writes no Integration Capability claim of any kind. That is the load-bearing property of this slice, not a side note: presence and capability stay two types with no derivation path between them.

This slice is scheduled ahead of the rest of spec 05 — five other specs read the matrix and it has no blockers. It may therefore be delivered **before the operation core seam exists**, as validated data plus a detection function; in that case ship those two first and defer the core operation and CLI report to a follow-up once `execution-core#01` has landed. The matrix data and the detection function are the part other specs are waiting on.

```ts
type HarnessPresence = {
  harness: string;
  evidence: Array<{ kind: "directory" | "binary" | "manifest"; path: string }>;
};
```

## Acceptance criteria

- [ ] The matrix is data with its own schema validation; adding a fixture harness entry requires no change outside the data file, proven by a test that adds one and sees it detected and classified.
- [ ] A fixture `HOME` with three harness installations produces one presence record each, carrying the evidence kind and path that established it.
- [ ] A harness present on disk but absent from the matrix is classified unsupported and appears as such in the report.
- [ ] The detection result contains no capability field, and a test asserts the configuration written after detection alone holds no capability claims.
- [ ] `GANTRY_HOST_COMMAND` and a spoofed parent process name change the detection output in no way.

## Blocked by

None - can start immediately
