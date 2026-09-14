# Reference fixture isolation foundation

Type: issue
Status: done
Slice: `gantry-migration#16`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

 Build the reusable `fixture/` repository and its deterministic isolated-copy builder, without running the full Gantry workflow. The fixture contains a minimal Python greeting project, a standard-library JSON linter, `.gantry/config.json` declaring its absolute and RFC 6901-mapped differential checks, and a valid greeting Spec. `fixture/tools/copy_fixture.py --skill-dir <canonical-gantry-skill-dir>` produces one clean no-Issue copy for plan and approval stopping and one clean approved-Issue copy with three `ready-for-agent` greeting Issues for round execution. Each destination is an independent Git repository with a baseline commit and a pack-visible local Gantry-skill installation. Feature-owner Issues keep their behavioral test seams beside their own scripts; this foundation owns only reusable fixture content and isolated-copy construction.

## Acceptance criteria

- [x] `python3 fixture/tools/copy_fixture.py --mode unplanned --skill-dir <canonical-gantry-skill-dir> --dest <empty-dir>` creates an isolated Git repository with a baseline commit, a pack-visible local Gantry-skill installation, no files under `.scratch/greeting/issues/`, a valid greeting Spec, and no inherited source Git or Run-log state.
- [x] `python3 fixture/tools/copy_fixture.py --mode approved --skill-dir <canonical-gantry-skill-dir> --dest <empty-dir>` creates an independent Git repository with a baseline commit, the same local Gantry-skill installation, and exactly three legacy-format greeting Issues at `ready-for-agent`, each preserving `Status:`, `Slice:`, `## Acceptance criteria`, and `## Blocked by`.
- [x] Both generated copies contain a runnable absolute pytest check and RFC 6901-mapped standard-library linter configuration, and copy-builder tests prove repository-relative paths, independent Git common directories and Run-log unit ids, installed skill visibility, and no source fixture files are modified.
- [x] The fixture foundation’s tests and documentation are English, do not invoke a harness workflow, and do not create an engine, database, MCP service, automatic cleanup, automatic merge, or lesson injection.
- [x] The Spec Changelog receives an English entry in the same merge, with the copy-builder test runnable from the repository.

## Blocked by

- `gantry-migration#03` — consumes effective-template Spec validation for the fixture Spec.
- `gantry-migration#07` — consumes the declared differential-gate mapping contract.

## Comments
