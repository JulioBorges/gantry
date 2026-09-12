# Release engineering and progressive documentation

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 19, wave 5)
Source: `PRD.md` §12, §2.3, §14.1
Created: 2026-09-11

## Problem Statement

Gantry is an open-source npm package whose entire argument is that deterministic code should own the
guardrails. A project making that argument while shipping unverified tarballs from a maintainer's laptop
would be hard to take seriously, and `PRD.md` treats its own release engineering as non-negotiable: CI on
pull requests with lint, typecheck, test, and build as required checks; `main` protected with one
approving review, linear history, and no force-push; publish on tag with provenance and a guard asserting
the tag matches the package version.

Three things need deciding rather than restating.

Some of this project's test suites cannot run in ordinary CI. The harness conformance suite in spec 10
needs Codex and OpenCode installed; the provider conformance suite in spec 14 needs GitHub credentials
and a repository to mutate. Making them required checks would block every pull request on infrastructure
most contributors do not have; making them invisible would mean the support matrix is never actually
produced. And §14.1 leaves Windows "expected but unverified", with the instruction to "report platform
capability from tests rather than inferring it from Node.js portability" — which makes CI the place that
evidence comes from or does not exist.

The documentation requirement is likewise a real constraint rather than a formality. The PRD names setup
complexity as the top adoption blocker and commits to a three-command quickstart with a demo, then
cookbooks, then deep reference — with the PRD itself read last. A project whose entry point is a 94KB
requirements document has failed that commitment regardless of how good the document is.

And one boundary is easy to lose: this repository's own review requirement is its policy, not a workflow
every user repository must adopt. §7.6 says so explicitly.

## Solution

The package is published from tags by CI, never from a workstation. Pull requests run the checks that
work anywhere — lint, typecheck, unit and integration tests including the demo pipeline, and build — as
required checks on a protected `main`. Conformance suites that need real harnesses or credentials run in
separate jobs that record their results into a published support matrix and do not gate ordinary
contributions; a skipped conformance run records its reason and never counts as support.

Windows is a CI matrix entry rather than an assumption. The suites that can run cross-platform run there,
and the symlink fallback tests in spec 05 are the specific evidence that turns "expected" into "supported"
or "unsupported with a stated reason".

Publishing is a tag-triggered pipeline: verify, build, assert the tag matches the package version, publish
with provenance, create a GitHub Release. A local flow exists for bumping and tagging and for validating
the tarball, but not for publishing.

Documentation is layered so that the first thing a reader meets is three commands and a demo, and the PRD
is reachable but last.

## User Stories

1. As a maintainer, I want every pull request checked automatically, so that review is about design rather than mechanics.
2. As a maintainer, I want lint, typecheck, test, and build as required checks, so that `main` stays green.
3. As a maintainer, I want `main` protected with a required review, so that nothing lands unreviewed.
4. As a maintainer, I want linear history and no force-push on `main`, so that history stays auditable.
5. As a maintainer, I want the demo pipeline run in CI, so that the end-to-end path cannot rot unnoticed.
6. As a maintainer, I want conformance suites that need real harnesses kept out of the required checks, so that contributors without them can still contribute.
7. As a maintainer, I want those suites still run somewhere on a schedule, so that the support claims stay current.
8. As a maintainer, I want a skipped conformance run to record its reason, so that absence is visible rather than silent.
9. As a maintainer, I want a skipped run never counted as support, so that the matrix does not overstate.
10. As a maintainer, I want the support matrix published, so that users can see what is actually validated.
11. As a maintainer, I want tested harness and tool versions recorded in the matrix, so that a support claim has a basis.
12. As a maintainer, I want Windows in the CI matrix, so that platform support is evidence rather than inference.
13. As a maintainer, I want the symlink fallback path exercised on Windows, so that the documented fallback is real.
14. As a maintainer, I want platform support reported honestly, so that "expected but unverified" is stated where it applies.
15. As a maintainer, I want publishing triggered by a version tag, so that releases are deliberate.
16. As a maintainer, I want the pipeline to refuse a tag that does not match the package version, so that a mistagged release cannot ship.
17. As a maintainer, I want lint, test, and build to run again before publishing, so that the published artifact is verified.
18. As a maintainer, I want the package published with provenance, so that users can verify where it came from.
19. As a maintainer, I want a GitHub Release created alongside the publish, so that the changelog and the artifact stay together.
20. As a maintainer, I want publishing impossible from a workstation, so that credentials live only in CI.
21. As a maintainer, I want a local command to bump and tag, so that starting a release is one step.
22. As a maintainer, I want a local dry run that validates the tarball, so that packaging problems are caught before tagging.
23. As a maintainer, I want the tarball's contents asserted, so that a build artifact or a stray file is never shipped.
24. As a maintainer, I want the declared Node version enforced, so that the package does not install where it cannot run.
25. As a maintainer, I want the binary entry point smoke-tested from the built tarball, so that `npx gantry` works as published rather than as built.
26. As a user, I want three commands to a working demo, so that evaluating Gantry costs minutes.
27. As a user, I want a demo recording in the readme, so that I can see the pipeline before installing anything.
28. As a user, I want cookbooks per workflow, so that I can accomplish a task without reading the reference.
29. As a user, I want the deep reference available but last, so that I am not handed a requirements document as an introduction.
30. As a user, I want all documentation in English, including files Gantry generates, so that the artifacts are consistent.
31. As a user, I want the documented quickstart to match the shipped behavior, so that the first commands I run actually work.
32. As a user, I want to know that this repository's review policy is its own, so that I do not think Gantry requires it of my repository.
33. As a contributor, I want the checks runnable locally with the same commands CI uses, so that I can reproduce a failure.
34. As a contributor, I want a tarball testing guide, so that I can verify a packaging change.

## Implementation Decisions

### Package shape

```jsonc
{
  "name": "gantry",
  "version": "4.0.0",
  "type": "module",
  "bin": { "gantry": "./dist/bin/gantry.js" },
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "files": ["dist", "templates"],
  "engines": { "node": ">=20" }
}
```

`files` is an allowlist rather than an ignore list, so a new directory is excluded by default. `templates`
ships the fixture project from spec 07 and the generated-file templates from spec 06.

The published library surface is deliberately minimal. `main` and `types` exist because the operation core
is a library, but the supported interface is the CLI and the MCP server; exporting the core publicly would
make every internal contract a semver commitment, which is the wrong trade at this stage.

### Pull request checks

Required checks on every pull request, all runnable without credentials, a harness, or network access
beyond package installation:

| Check | Scope |
|---|---|
| Lint | ESLint with typescript-eslint over the repository |
| Typecheck | TypeScript with no emit |
| Test | Vitest: unit, integration at the operation-core seam, and the demo pipeline from spec 07 |
| Build | Production build, plus the packaging assertions below |

The demo pipeline is a required check because it is the only test that exercises every wave end to end.
Spec 07 made it deterministic for this reason.

`main` is protected: one approving review, required status checks, linear history, no force-push. This is
this repository's policy. §7.6 is explicit that it is not a workflow imposed on user repositories, and the
documentation states that where a reader might infer otherwise.

Platform matrix: Linux as the primary, plus macOS and Windows. The Windows job is where the §14.1 claim is
either earned or has to remain "unverified", and it is not a generic "run the suite elsewhere" job — six
specific behaviors differ on Windows and each has a named owner:

| Behavior | Spec | What differs |
|---|---|---|
| Repository Execution Unit identity | 01 | Case-insensitive paths, UNC versus mapped drive, 8.3 short names, path length limits |
| Skill installation | 05 | Symlinks unavailable without developer mode; the copy fallback and its drift reporting |
| Agent stop | 10 | No cooperative process signal; job objects or a declared `agentInterruption: "none"` |
| Worktree freeze | 11 | Read-only enforcement and the "open file cannot be deleted" semantics during cleanup |
| Content hashing | 04 | `core.autocrlf` divergence between working tree and blob |
| Check resources | 12 | Port and temporary-directory behavior under a different locking model |

A Windows job that passes everything except one of these is not evidence of support for that one. The
documented platform status is derived from which of these rows pass, per row, rather than from the job's
overall result.

### Conformance suites

Two suites cannot be required checks:

- Harness conformance (spec 10): the four Codex and OpenCode combinations, needing both harnesses
  installed and authenticated.
- Provider conformance (spec 14): GitHub.com and GitHub Enterprise operations, needing credentials and a
  disposable repository.

They run as separate scheduled and manually dispatchable jobs, and on demand for a pull request that
touches an adapter. Each run writes into a published support matrix recording the combination, the tested
versions, the observed capabilities, and the limitations.

A run that cannot execute records an explicit skip reason and leaves the corresponding matrix rows
unsupported. A skip is never support, and a stale matrix row is marked with its age rather than presented
as current.

### Publish on tag

Triggered by a `v*.*.*` tag:

1. Lint, typecheck, test, build — the same checks as a pull request, rerun rather than trusted from the
   branch.
2. Assert the tag equals the `package.json` version. A mismatch fails the pipeline before anything is
   published.
3. Assert the tarball contents against an expected manifest.
4. `npm publish --provenance`, which requires the workflow's OIDC identity and therefore cannot be
   reproduced from a workstation.
5. Create a GitHub Release with the changelog entry for that version.

Publishing credentials exist only in the workflow. There is no local publish path, which is the point: the
guard asserting tag-equals-version is only meaningful if no route bypasses it.

Tarball assertions: the binary entry point is present and executable, `dist` and `templates` are present,
no test files or build intermediates are included, the declared Node engine is enforced, and installing
the tarball into a temporary directory and running the binary's version command succeeds. That last one
catches the class of failure where the build works and the package does not.

### Local release flow

- A bump-and-tag command for each version level, updating `package.json` and the changelog and creating the
  tag. It does not push; pushing with tags is deliberate and manual.
- A dry-run command that builds, packs, and runs the tarball assertions locally, so a packaging change can
  be validated before tagging.
- A tarball testing guide in the release documentation covering both.

### Documentation layers

Progressive disclosure, in the order a reader meets them:

1. Readme: what Gantry is, the three commands to the demo, and a recording of the demo pipeline. Nothing
   else competes for attention here.
2. Quickstart: the demo, then a real repository, with the readiness and approval steps stated as steps
   rather than glossed — §13.6 makes the ten-minute real pipeline conditional on readiness and approvals,
   and the quickstart should not imply otherwise.
3. Cookbooks: one per workflow — authoring a spec, slicing, running a PBI, gates, merging, cross-harness
   routing, dashboard settings.
4. Reference: the operation catalog, configuration schema, GTP contracts, and the support matrix.
5. `PRD.md`: the product argument, read last.

All documentation is in English, including the files Gantry generates into a user's repository —
`AGENTS.md` sections, `CONSTITUTION.md`, and spec and PBI templates.

The quickstart's commands are verified in CI against the built package, so documented behavior and shipped
behavior cannot drift.

## Testing Decisions

**What makes a good test here.** This spec's subject is the pipeline, so its tests are mostly assertions
about artifacts and workflow configuration rather than about Gantry's behavior. They assert what is
checkable: the tarball's contents and its installability, the tag-version guard's rejection of a mismatch,
the `files` allowlist's exclusions, the support matrix's handling of skips, and the quickstart commands
running against the built package.

**What is not tested here.** Branch protection and required-check configuration are provider settings, not
code. They are documented and verified by inspection during release preparation rather than by a test that
would only assert a configuration file exists.

**The seam.** This spec is the one exception to the shared operation-core seam, because its subject is
outside the application. Packaging assertions run against a real built tarball installed into a temporary
directory; the quickstart verification runs the documented commands against that installation.

**Modules under test.** Tarball manifest assertions, binary smoke test from an installed tarball, the
tag-version guard, `files` allowlist behavior, engine enforcement, support matrix construction and skip
handling, and quickstart command verification.

**Scenarios that must exist**, from PRD §14.3 items 1 and 10:

- A tarball built from a clean checkout contains `dist` and `templates`, an executable binary entry point, and no test files or build intermediates.
- A new top-level directory is excluded from the tarball without any change to configuration.
- Installing the tarball into a temporary directory and running the binary's version command succeeds.
- Installation under a Node version below the declared engine is refused.
- A tag not matching `package.json` fails the publish pipeline before publishing.
- A matching tag proceeds through verification, build, publish, and release creation, verified against a publish dry run.
- No local command path can publish.
- A conformance run that cannot execute records a skip reason and leaves its matrix rows unsupported.
- A matrix row from an older run is marked with its age rather than presented as current.
- The support matrix distinguishes the four harness combinations and each provider deployment separately.
- The Windows job runs the platform-independent suites and each of the six named platform-divergent behaviors, and the documented Windows status is derived per row rather than from the job's overall result.
- A Windows job passing five of the six rows documents the sixth as unsupported rather than the platform as supported.
- The documented quickstart commands succeed against the installed package.
- The demo pipeline runs as a required check and fails the build when any wave's behavior changes incompatibly.
- Every generated template file is in English.

## Out of Scope

- **Everything Gantry does**: specs 01 through 18. This spec ships them.
- **The demo fixture and its determinism** (spec 07): this spec runs it as a required check.
- **Harness conformance content** (spec 10) and **provider conformance content** (spec 14): this spec schedules them and publishes their matrix.
- **Skill content and installation behavior** (spec 05): this spec runs its tests on Windows.
- **Generated file content** (spec 06): this spec ships the templates and asserts they are in English.
- **Gantry's Git workflow features** (spec 14): this repository's own branch protection is its policy, not a product feature, and §7.6 separates the two explicitly.

Out of scope by product decision:

- Publishing from a workstation. The tag-version guard is only meaningful without a bypass.
- Making conformance suites required checks. They need infrastructure contributors do not have.
- Claiming Windows support without CI evidence. §14.1 requires reporting platform capability from tests.
- Exporting the operation core as a supported public library API. It would make internal contracts semver commitments.
- Imposing this repository's review policy on user repositories (§7.6).
- Release orchestration features for user repositories. Separate from this spec and out of product scope (§6.2).

## Further Notes

**Binding decisions.** Nothing here contradicts either ADR. The refusal to claim Windows support without a
passing job is the same discipline ADR-0001 applies to integration capabilities, extended to platforms:
a guarantee nobody tested is not a guarantee.

**Glossary alignment.** No new domain terms. The support matrix is the artifact that records Integration
Capability per validated combination, as `CONTEXT.md` defines it.

**Glossary gap for `/domain-modeling`.** Support matrix is referenced by specs 10, 14, and this one without
a glossary entry and should get one.

**Where the risk actually sits.** Conformance suites outside the required checks will rot. That is the
predictable outcome of any job that does not block a merge, and the honest question is not whether it
happens but how it is detected. Two things reduce the damage: matrix rows carry their age, so a stale claim
is visibly stale rather than quietly wrong; and a pull request touching an adapter dispatches the relevant
suite, which catches the changes most likely to break it. What remains uncovered is a harness updating
underneath a matrix row that nothing touched, which the scheduled run exists for and which will be the
first thing to be disabled when it becomes noisy. Worth watching.

The second risk is the quickstart drifting from reality in a way CI cannot catch. Verifying that the
documented commands succeed proves they run; it does not prove the demo shows what the readme claims it
shows. That gap is closed by review rather than by tests, and it is worth naming because a quickstart that
runs cleanly while describing something else is the most expensive documentation failure this project could
have — it costs the reader exactly the trust the demo exists to earn.

**Sequencing note.** This spec has no dependency on any other and should be built first in practice,
despite sitting last in the map. A repository with CI, branch protection, and a publishable package from
the first commit is the difference between a project that accumulates a release process and one that fights
for it later. The pieces worth having on day one are the pull request checks and the `files` allowlist;
publishing can wait until there is something to publish.
