# Installation lifecycle: idempotent re-run, divergence reconciliation, and uninstall

Type: issue
Status: ready-for-agent
Slice: machine-setup#04
Spec: [`../spec.md`](../spec.md) (spec 05, wave 1)
Created: 2026-09-12

## Parent

[`.scratch/machine-setup/spec.md`](../spec.md)

## What to build

A second `gantry setup` run inventories everything the first one produced — factory items and skill installations alike — and classifies each as present, missing, or divergent. A copy whose source version has advanced is divergent; a symlink never is. The run changes nothing without operator authorization, and any authorized overwrite of a configuration file writes a `.bak` first.

Re-sync of a divergent copy happens only on request, never silently, because an operator may have modified a copy deliberately.

Uninstall is the inverse operation: it removes every link and copy from every harness directory, leaving none broken, and leaves the factory and database intact unless the operator explicitly asks for those too. Broken links left behind in directories Gantry does not own are the failure mode this slice exists to rule out.

## Acceptance criteria

- [ ] A second run over an intact installation reports every item present and writes nothing, asserted by comparing the tree before and after.
- [ ] A run against an installation with a deleted asset and a stale copy reports one missing and one divergent item and still changes nothing without authorization.
- [ ] An authorized reconciliation of a configuration file writes a `.bak` containing the prior content before overwriting.
- [ ] A copy whose source version advances is reported divergent on every subsequent run until re-sync is requested; after re-sync its installed version matches the source.
- [ ] A symlinked installation is never reported divergent, including after the source version advances.
- [ ] Uninstall leaves no link or copy in any harness directory and no broken symlink, verified by resolving every path under the fixture harness directories; the factory and database survive unless explicitly included.

## Blocked by

- `machine-setup#01` — the factory items the re-run inventories and the announced-path contract it classifies against.
- `machine-setup#03` — the `SkillInstallation` record and the symlink/copy mechanisms whose divergence and removal this slice governs.
