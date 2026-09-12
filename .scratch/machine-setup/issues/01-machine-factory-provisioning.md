# Machine factory provisioning

Type: issue
Status: ready-for-agent
Slice: machine-setup#01
Spec: [`../spec.md`](../spec.md) (spec 05, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/machine-setup/spec.md`](../spec.md)

## What to build

`gantry setup` run against a fresh temporary `HOME` creates the `~/.gantry` factory end-to-end: the SQLite database opened at the current schema version, the global configuration document written through the ConfigStore with the approved defaults, and the CLI, MCP, and dashboard assets placed. Every path is announced before it is created, and setup creates nothing outside `~/.gantry` and `~/.agents/skills/gantry-*`.

The same code path handles an existing database. A database at an older schema version refuses to proceed without an explicit migration, and that migration records the prior version's provenance; a database at a newer version refuses to open at all, with a rejection distinct from the older-version case. Setup runs no harness, no model, and no repository tooling, needs no credential, and behaves identically whether entered through `npx` or a global install.

One bootstrap constraint must be verified against `execution-core#01` rather than solved here: setup operations are registered in the shared operation catalog, but `gantry setup` runs *before* the factory and database exist, so the catalog and its `invoke` seam have to be constructible against a not-yet-provisioned factory. Confirm that the seam as built supports this ordering; if it does not, raise it against `execution-core#01` instead of introducing a local second entry point.

## Acceptance criteria

- [ ] A first run creates exactly the announced paths and nothing outside the two declared trees, asserted by walking the temporary `HOME`.
- [ ] Injected harness drivers, model clients, and network access are fakes that fail the test if invoked; the run completes without touching any of them.
- [ ] A fixture database one schema version behind refuses to proceed and reports that an explicit migration is required; after migration the prior version is recorded as provenance.
- [ ] A fixture database one schema version ahead refuses to open, with a distinct rejection from the older-version case.
- [ ] No file written by setup contains a credential value; credentials appear only as environment variable names.
- [ ] Factory state produced through the `npx` entry point and through the global entry point compares equal.

## Blocked by

- `execution-core#01` — the operation core `invoke` seam, operation catalog registration, and the schema-version-checked database open.
- `execution-core#08` — the execution version compatibility rules (older requires explicit migration, newer refuses) and migration provenance.
- `config-and-snapshot#01` — ConfigStore layering and the approved defaults written into the global configuration document.
- `data-handling#01` — the redaction sink enforcement interface the setup report's display path must traverse.
