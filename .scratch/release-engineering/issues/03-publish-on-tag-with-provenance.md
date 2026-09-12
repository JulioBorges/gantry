# Publish on tag with provenance

Type: issue
Status: ready-for-agent
Slice: release-engineering#03
Spec: [`../spec.md`](../spec.md) (spec 19)
Created: 2026-09-12

## Parent

[`.scratch/release-engineering/spec.md`](../spec.md)

## What to build

A workflow triggered by a `v*.*.*` tag that reruns lint, typecheck, test and build rather than trusting
the branch, asserts the tag equals the manifest version and fails before publishing on a mismatch, reruns
the tarball assertions from `release-engineering#02`, publishes with `npm publish --provenance` under the
workflow's OIDC identity, and creates a GitHub Release carrying the `CHANGELOG.md` section for that exact
version. The workflow declares the `id-token` permission provenance requires and no broader write
permission than it needs. Publishing credentials exist only in the workflow.

Verify the happy path with a publish dry run rather than a real publish, so the pipeline is provable
before there is anything to release.

**Reframed acceptance item.** "Publishing is impossible from a workstation" is a negative claim no test
fully establishes — anyone holding a registry token can publish, and claiming otherwise would be exactly
the overclaiming ADR-0001 forbids. What is checkable, and what the test and the documentation should
therefore say, is that no package script publishes, that no documented procedure publishes, and that the
registry token is configured only as a workflow secret.

**Open question for operator review — do not resolve in this issue.** The package shape in the spec fixes
the first version at `4.0.0`. Publishing `4.0.0` as the first-ever release of a package that has no 1, 2
or 3 is a product decision rather than a technical one, and `0.x` or a prerelease tag until the pipeline
has shipped something real may serve better. Record it as an open question and leave the version as the
spec states it.

## Acceptance criteria

- [ ] A tag whose version differs from the manifest fails the pipeline at the guard step, before any publish or release step runs.
- [ ] A matching tag proceeds through verify, build, tarball assertions, publish dry run, and release creation, with the dry run reporting the expected file list.
- [ ] The publish step is unreachable except from the tag workflow — no package script invokes a publish, and a test asserts this over the manifest.
- [ ] The created GitHub Release body is the changelog section for that exact version; a missing section fails the pipeline.
- [ ] The workflow declares the `id-token` permission required for provenance and no broader write permission than it needs.

## Blocked by

- `release-engineering#02` — provides the tarball manifest and the `pack:check` assertions the tag workflow reruns before publishing.
