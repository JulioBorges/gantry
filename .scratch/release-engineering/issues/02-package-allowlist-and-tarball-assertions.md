# Package allowlist, tarball assertions, and installed-binary smoke test

Type: issue
Status: ready-for-agent
Slice: release-engineering#02
Spec: [`../spec.md`](../spec.md) (spec 19)
Created: 2026-09-12

## Parent

[`.scratch/release-engineering/spec.md`](../spec.md)

## What to build

Make the published artifact provable. `files` is an allowlist — `["dist", "templates"]` — never an ignore
list, so a new top-level directory is excluded by default and nobody has to remember to exclude it. Add an
expected-tarball manifest and a `pack:check` script that builds, packs, and asserts that manifest:
`dist/` and `templates/` present, the binary entry point `dist/bin/gantry.js` present with a shebang and
the executable bit, no test files, no build intermediates such as `*.tsbuildinfo`, and no `.scratch` path.
Wire `pack:check` into the build required check so a packaging regression fails a pull request.

Then install the packed tarball into a temporary directory and run the binary's version command. That is
the assertion that catches the class of failure where the build works and the package does not — the one
failure mode a green `build` job cannot see. `templates/` ships the fixture project and the generated-file
templates that other specs author; this slice asserts the directory is present in the tarball and does not
own its contents.

**Reframed acceptance item.** Story 24 ("the declared Node version is enforced") cannot be satisfied by
the `engines` field alone: npm's `engine-strict` defaults to false, so a mismatched Node produces an
`EBADENGINE` warning rather than a refusal. The enforcement must be a runtime guard in the binary entry
point that exits non-zero with a message naming the required version, and the test must assert that guard
rather than the manifest field. The spec's wording ("installation under a Node version below the declared
engine is refused") is kept as intent; the mechanism is the runtime guard.

## Acceptance criteria

- [ ] `pack:check` fails when a test file, a `.tsbuildinfo`, or a `.scratch` path appears in the tarball.
- [ ] Adding a new top-level directory containing a file changes nothing about the tarball, with no edit to any configuration.
- [ ] Installing the tarball into a temporary directory and running the binary's version command exits zero and prints the manifest version.
- [ ] Running the installed binary under a Node version below the declared engine exits non-zero with a message naming the required version.
- [ ] The packed binary entry point has a shebang and is executable after installation on Linux and macOS.
- [ ] `pack:check` runs as part of the build required check.

## Blocked by

- `release-engineering#01` — provides the package manifest, the build producing `dist/bin/gantry.js`, and the named CI scripts that `pack:check` joins.
