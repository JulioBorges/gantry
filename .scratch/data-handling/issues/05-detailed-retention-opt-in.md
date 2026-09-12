# Detailed retention opt-in and evidence invalidation

Type: issue
Status: ready-for-agent
Slice: data-handling#05
Spec: [`../spec.md`](../spec.md) (spec 04, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/data-handling/spec.md`](../spec.md)

## What to build

The per-repository opt-in that trades storage for depth, and the invalidation that keeps it honest. Detailed retention stores fuller content, still through the pipeline and still subject to `uncertain` withholding, so opting in never opts out of Output Redaction.

The retention level in effect for a record is the one captured in its Execution Rule Snapshot, not the current setting, so changing it does not retroactively alter a running execution's records. Turning detailed retention off invalidates evidence that depended on content no longer kept: affected gate results return to pending and the invalidation is recorded, following the snapshot-migration classification.

## Acceptance criteria

- [ ] With detailed retention enabled, a record stores fuller content and that content is still redacted by the pipeline.
- [ ] A record written under a snapshot capturing the default level keeps default-level content even after the current setting is raised.
- [ ] Disabling detailed retention returns gate results that depended on the dropped content to pending, and records an invalidation naming the cause.
- [ ] Gate results that did not depend on the dropped content keep their original binding and are not invalidated.
- [ ] Detailed retention with an `uncertain` outcome still stores no content and still marks the operation or check blocked for review.

## Blocked by

- `data-handling#04` — the default Telemetry Retention record shape this slice extends with fuller content.
- `config-and-snapshot#01` — the retention level field in the data-handling configuration section.
- `config-and-snapshot#04` — the Execution Rule Snapshot capture that binds a record to the retention level in force when it was written.
- `config-and-snapshot#05` — the snapshot migration record classification the invalidation follows.
