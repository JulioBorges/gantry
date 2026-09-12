# Skill installation into harness conventions

Type: issue
Status: ready-for-agent
Slice: machine-setup#03
Spec: [`../spec.md`](../spec.md) (spec 05, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/machine-setup/spec.md`](../spec.md)

## What to build

Establish the skill sources at `~/.agents/skills/gantry-*` as the single source of truth, versioned with the package so an installed skill's version is always identifiable. For each detected, supported harness, select the installation mechanism and install: a symlink where linking works, a copy where it does not, and nothing where the matrix has no format mapping. Persist a `SkillInstallation` record per harness in telemetry-free local machine state.

The setup report carries an explicit, prominent notice for each unsupported harness stating that it has CLI and MCP access only.

Link failure is proven by a fixture that forces it, not by running on a platform where linking fails. This slice claims no Windows support, and the forced-failure fixture is the evidence path `release-engineering#05`'s Windows platform row consumes.

```ts
type SkillInstallation = {
  harness: string;
  targetPath: string;
  mechanism: "symlink" | "copy" | "unsupported";
  sourceVersion: string;
  installedVersion?: string;   // copies only; equals sourceVersion when in sync
  divergent: boolean;
};
```

## Acceptance criteria

- [ ] A supported harness on a linking-capable fixture receives a symlink, recorded with `mechanism: "symlink"` and `divergent: false`.
- [ ] A fixture that makes linking fail receives a copy, recorded with `mechanism: "copy"` and an `installedVersion` equal to the source version — the test forces link failure rather than skipping on platforms where linking works.
- [ ] A harness with no matrix format mapping has no skill written into its directory and produces the CLI-and-MCP-only notice in the setup report.
- [ ] Every installed skill's version is readable from the installation record and matches the package version.
- [ ] Installation records are written to local machine state and appear in no telemetry or execution record.

## Blocked by

- `machine-setup#01` — the `~/.gantry` factory and the local machine state the installation records are written into.
- `machine-setup#02` — the compatibility matrix data and presence detection that say which harnesses are supported and where their skill directories are.
