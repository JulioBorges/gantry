# Redaction sink boundary and normalized content hashing

Type: issue
Status: ready-for-agent
Slice: data-handling#01
Spec: [`../spec.md`](../spec.md) (spec 04, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/data-handling/spec.md`](../spec.md)

## What to build

One Output Redaction pipeline producing a three-way outcome (`clean` / `redacted` / `uncertain`) carrying metadata of detector identity, hit count, and ruleset version — and a sink signature that accepts *only* a pipeline result, so a raw string is not a valid argument to anything that persists or displays. Ship the normalized content hashing rule in the same slice: a single line-ending convention and a consistent trailing-newline rule. Every writer in the system consumes both of these, so they get one unblock point. Only enough built-in pattern detectors to prove the path; the detector catalog is slice `data-handling#02`.

This slice ships as an **interface package with no dependency on the shared operation core**. It is the second issue in the whole project's build order, ahead of `execution-core#01`, precisely so that no writer is ever added without the sink boundary already in place. Its behaviour is therefore proven against the thin sink and hashing helpers the repository bootstrap provides, not against a real record write. The end-to-end proof — a planted token surviving a real audit record write and coming back masked through the core's audit read — is carried by `execution-core#01` when it adopts this interface while building its audit record family.

This spec has **no transport surface of its own**: no `gantry` subcommand and no MCP tool belongs to data-handling, and its observable surfaces (the state projection, the audit read, rejection codes) are owned by `execution-core`. This slice therefore contributes no CLI/MCP/dashboard parity test, and that is by design rather than a gap.

The outcome shape encodes the decision that there is no partial-content variant:

```ts
type RedactionOutcome =
  | { confidence: "clean";     content: string; metadata: RedactionMetadata }
  | { confidence: "redacted";  content: string; metadata: RedactionMetadata }
  | { confidence: "uncertain"; content: null;   metadata: RedactionMetadata; reason: string };
```

## Acceptance criteria

- [ ] Output containing a planted bearer token, driven through the pipeline into the bootstrap's thin sink, is accepted with the token replaced by a marker, and reading it back from that sink returns the marker in place.
- [ ] Stored redaction metadata contains detector identity, hit count, and ruleset version, and contains no offset, length, prefix, or hash of matched content — asserted by schema shape, not by inspection.
- [ ] Passing a raw string to a sink fails to compile, and a runtime refusal exists for content arriving without a pipeline result across a dynamic boundary.
- [ ] The same content hashed with CRLF endings and with LF endings yields one identical hash; the trailing-newline rule produces one hash for both the present and absent case as declared.
- [ ] Redaction is applied on the error path: a scripted failure output carrying a planted secret reaches the thin sink masked, not raw and not dropped.

## Blocked by

- `release-engineering#01` — repository bootstrap, toolchain, and test runner, plus the thin sink and hashing helpers this slice proves itself against.
