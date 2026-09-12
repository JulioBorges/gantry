# Local release flow: bump, tag, and dry run

Type: issue
Status: ready-for-agent
Slice: release-engineering#04
Spec: [`../spec.md`](../spec.md) (spec 19)
Created: 2026-09-12

## Parent

[`.scratch/release-engineering/spec.md`](../spec.md)

## What to build

The commands a maintainer runs before a tag exists. A bump-and-tag command per version level — patch,
minor, major — that updates the package manifest and `CHANGELOG.md` and creates the annotated tag in one
step, and deliberately **does not push**: pushing with tags stays manual, because the push is the moment
the release becomes real. The command refuses to run on a dirty working tree.

A dry-run command that builds, packs and runs `release-engineering#02`'s tarball assertions locally, so a
packaging change is validated before tagging rather than discovered by the tag workflow.

A tarball testing guide in the release documentation covering both, walking through bump, dry run,
inspect, tag push, and observing the publish workflow, linked from the reference documentation layer.

The changelog convention and tooling are chosen and recorded in `release-engineering#01`; this slice
writes into `CHANGELOG.md` according to that convention rather than choosing one.

## Acceptance criteria

- [ ] Running the bump command for each of patch, minor, and major updates the manifest version, inserts a dated changelog section for that version, and creates a matching annotated tag in one step.
- [ ] The bump command leaves the remote unchanged — no push occurs, verified against a temporary bare remote.
- [ ] The bump command refuses to run on a dirty working tree.
- [ ] The dry-run command reports the same manifest and the same failures as CI for a deliberately broken packaging change.
- [ ] The release documentation walks through bump, dry run, inspect, tag push, and observe the publish workflow, and is linked from the reference layer.

## Blocked by

- `release-engineering#02` — provides the tarball manifest and the `pack:check` assertions the dry-run command runs locally.
