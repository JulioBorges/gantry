# Git Workflow Policy resolution and the integration operation surface

Type: issue
Status: ready-for-agent
Slice: git-integration#01
Spec: [`../spec.md`](../spec.md) (spec 14, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/git-integration/spec.md`](../spec.md)

## What to build

The `GitWorkflowPolicy` shape — branch naming template, starting branch, integration target, delivery mode, local check references, observed provider requirements — and its resolution from configuration through the Execution Rule Snapshot. Ship the three workflow presets `trunk-local` (target `main`, local merge), `trunk-pr` (target `main`, Pull Request) and `develop-pr` (target `develop`, Pull Request) as adjustable starting points rather than fixed bundles: every field of a preset-derived policy must remain editable.

A repository with no chosen Git Workflow Policy resolves to a `needs_decision` readiness item and cannot run governed execution. There is no silent default, because guessing how a team integrates code is not a recoverable error.

This slice also registers the `integration.*` operation namespace on the shared operation core together with its typed rejection codes, so the later slices in this spec add handlers rather than inventing a surface. Policy inspection is exposed through the CLI, which delegates to the core and reimplements no decision, with one parity assertion on the other transports.

## Acceptance criteria

- [ ] A unit whose configuration carries no Git Workflow Policy produces a `needs_decision` item, and every governed-execution operation is rejected with a typed code naming the missing policy.
- [ ] Each of the three presets resolves to a complete, valid policy, and a test mutates every field of a preset-derived policy and observes the change survive snapshot capture.
- [ ] A policy captured into the Execution Rule Snapshot is read from the snapshot, not from live configuration, for the lifetime of an execution.
- [ ] The `integration.*` operations are discoverable on the core with their rejection codes enumerated; the CLI surface delegates without reimplementing any decision.
- [ ] Local checks are required when the mode is `local_merge`, and their absence is a typed rejection.

## Blocked by

- `execution-core#01` — provides the shared operation core `invoke`, operation catalog registration, and typed rejection codes.
- `config-and-snapshot#04` — provides Execution Rule Snapshot capture and snapshot identity.
- `config-and-snapshot#02` — provides whole-document configuration schema validation.
- `repository-readiness#01` — provides the readiness item shape and the `needs_decision` classification.
