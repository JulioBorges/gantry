# Spec 19 — release-engineering

Type: slice proposal (draft)
Status: proposal — not published as issues
Spec: [`.scratch/release-engineering/spec.md`](../../release-engineering/spec.md)
Map: [`.scratch/gantry-v4/map.md`](../map.md) (spec 19, wave 5)
Created: 2026-09-12

---

This spec owns everything that turns the repository into a shippable npm package: the pull-request
required checks (lint, typecheck, test, build) on a protected `main`, the platform matrix that turns
§14.1's "Windows expected but unverified" into per-behavior evidence, the conformance jobs that cannot be
required checks and the support matrix they write into, publish-on-tag with provenance and a
tag-equals-version guard, the local bump/tag/dry-run flow, and the progressive documentation layers. Its
risk sits in three places. First, it is the only spec that can be built against an empty repository, so
its first slice is a hard blocking root for the other eighteen — every choice made there is inherited,
and two load-bearing choices (SQLite driver, package manager) are **not made by any spec**. Second,
several of its acceptance scenarios describe negative or configuration facts (no local publish path,
branch protection settings, required-check membership) that are verified by inspection rather than by a
test, and the spec says so — that honesty is correct but it means those items need an explicit review
step rather than a green job. Third, the six Windows divergence rows and both conformance suites are
*consumed* from other specs, so the machinery must ship able to record "unverified" and "skipped" long
before the suites exist, or slices 05 and 06 become blocked on half the project.

## Slices

---

### 01 — Repository bootstrap and the first required checks

**What to build**

Turn the empty repository into a Node/TypeScript project whose pull-request workflow actually runs green:
package manifest (`type: module`, `engines`, `bin`, `main`, `types`), TypeScript config, Vitest, ESLint
with typescript-eslint, a formatter, the directory layout (`src/`, `src/bin/`, `tests/`, `templates/`,
`docs/`, `.github/workflows/`), and `.github/workflows/pull-request.yml` invoking the same named scripts a
contributor runs locally (story 33). The tracer bullet is a real binary — `src/bin/gantry.ts` that builds
to `dist/bin/gantry.js` and prints its version — so lint, typecheck, test, and build each have real work
rather than an empty target.

The slice must also install and *prove* the engine dependencies the rest of the project assumes: a smoke
test opening a real temporary SQLite database in WAL mode, a smoke test parsing a source file with
tree-sitter, and a temporary-Git-repository helper.

**The existing `.gitignore` must be replaced.** It is the Visual Studio / .NET template, and
`git check-ignore -v --no-index` confirms line 51 (`**/[Bb]in/*`) matches both `src/bin/gantry.ts` and
`dist/bin/gantry.js` — the binary entry point would be created, build locally, and silently never be
committed. The file also fails to ignore `dist/`, `coverage/`, `*.tsbuildinfo`, and `.DS_Store`.

Finally, document `main` protection (one approving review, required status checks, linear history, no
force-push) as *this repository's* policy, with the §7.6 note that it is not imposed on user repositories.

**Acceptance criteria**

- A pull request runs a workflow with four jobs — lint, typecheck, test, build — and all four pass on a
  clean checkout using the same package scripts documented for local use.
- `git check-ignore src/bin/gantry.ts dist/bin/gantry.js` reports no match, and `dist/`, `coverage/`, and
  `*.tsbuildinfo` are ignored.
- `node dist/bin/gantry.js --version` prints the version from the package manifest after a clean build.
- A test opens a temporary SQLite database with WAL enabled, writes and reads a row, and deletes the file;
  a test parses a TypeScript and a Python source file with tree-sitter and reads a named symbol; a test
  creates, commits into, and removes a temporary Git repository.
- A test spawns a second OS process that opens the same temporary database file and observes a write from
  the first — proving the cross-process concurrency seam spec 01 requires is runnable.
- `docs/` states the branch-protection settings for `main` and states explicitly that they are this
  repository's policy, not a requirement Gantry places on a user's repository.

**Blocked by**: None. This slice can start against the current empty repository.

**Parallelizable with**: Nothing in this spec — it is the root. It unblocks 02, 05, and 06 simultaneously.

---

### 02 — Package allowlist, tarball assertions, and installed-binary smoke test

**What to build**

Make the published artifact provable. `files` is an allowlist (`["dist", "templates"]`), never an ignore
list, so a new top-level directory is excluded by default. Add an expected-tarball manifest and a
`pack:check` script that builds, packs, and asserts the manifest: `dist` and `templates` present, binary
entry point present with a shebang and the executable bit, no test files, no build intermediates, no
`.scratch`. Then install the packed tarball into a temporary directory and run the binary's version
command — the assertion that catches the class of failure where the build works and the package does not.

**Flag**: story 24 ("the declared Node version is enforced") cannot be satisfied by `engines` alone —
npm's `engine-strict` defaults to false, so a mismatched Node produces an `EBADENGINE` warning, not a
refusal. The refusal must be a runtime guard in the binary entry point, and the test must assert the
guard, not the manifest field.

**Acceptance criteria**

- `pack:check` fails when a test file, a `.tsbuildinfo`, or a `.scratch` path appears in the tarball.
- Adding a new top-level directory containing a file changes nothing about the tarball, with no edit to
  any configuration.
- Installing the tarball into a temporary directory and running the binary's version command exits zero
  and prints the manifest version.
- Running the installed binary under a Node version below the declared engine exits non-zero with a
  message naming the required version.
- The packed binary entry point has a shebang and is executable after installation on Linux and macOS.
- `pack:check` runs as part of the build required check.

**Blocked by**: 01.

**Parallelizable with**: 05, 06.

---

### 03 — Publish on tag with provenance

**What to build**

A workflow triggered by a `v*.*.*` tag that reruns lint, typecheck, test, and build rather than trusting
the branch, asserts the tag equals the manifest version and fails before publishing on mismatch, reruns
the tarball assertions from slice 02, publishes with `npm publish --provenance` under the workflow's OIDC
identity, and creates a GitHub Release carrying the changelog entry for that version. Publishing
credentials exist only in the workflow. Verify the happy path with a publish dry run rather than a real
publish, so the pipeline is provable before there is anything to release.

**Flag**: "publishing is impossible from a workstation" is a negative claim that no test fully
establishes — anyone holding an npm token can publish. What is checkable is that no package script and no
documented procedure publishes, and that the registry token is configured only as a workflow secret; that
is what the test and the documentation should say, rather than claiming impossibility.

**Acceptance criteria**

- A tag whose version differs from the manifest fails the pipeline at the guard step, before any publish
  or release step runs.
- A matching tag proceeds through verify, build, tarball assertions, publish dry run, and release
  creation, with the dry run reporting the expected file list.
- The publish step is unreachable except from the tag workflow — no package script invokes a publish, and
  a test asserts this over the manifest.
- The created GitHub Release body is the changelog section for that exact version; a missing section fails
  the pipeline.
- The workflow declares the `id-token` permission required for provenance and no broader write permission
  than it needs.

**Blocked by**: 02 (reuses the tarball assertions and the manifest).

**Parallelizable with**: 04, 05, 06, 07.

---

### 04 — Local release flow: bump, tag, and dry run

**What to build**

The commands a maintainer runs before a tag exists. A bump-and-tag command per version level that updates
the package manifest and `CHANGELOG.md` and creates the annotated tag — and deliberately does not push,
since pushing with tags stays manual. A dry-run command that builds, packs, and runs slice 02's tarball
assertions locally so a packaging change is validated before tagging. A tarball testing guide in the
release documentation covering both.

**Flag**: the spec does not choose a changelog convention or tooling; see the open-choices list.

**Acceptance criteria**

- Running the bump command for each of patch, minor, and major updates the manifest version, inserts a
  dated changelog section for that version, and creates a matching annotated tag in one step.
- The bump command leaves the remote unchanged — no push occurs, verified against a temporary bare remote.
- The bump command refuses to run on a dirty working tree.
- The dry-run command reports the same manifest and the same failures as CI for a deliberately broken
  packaging change.
- The release documentation walks through bump, dry run, inspect, tag push, and observe the publish
  workflow, and is linked from the reference layer.

**Blocked by**: 02.

**Parallelizable with**: 03, 05, 06, 07.

---

### 05 — Platform matrix and per-row Windows status

**What to build**

Add macOS and Windows jobs to the pull-request workflow running the platform-independent suites, and build
the mechanism that derives documented platform status **per behavior row rather than from the job's
overall result**. Define a registry of the six divergent behaviors named by the spec, each with an owning
spec, a test tag, and a derived status of `supported`, `unsupported (reason)`, or
`unverified (no test yet)`. The derivation step reads the per-tag results from the Windows job and writes
the platform status into the reference documentation. Ship the registry with all six rows present and
`unverified` — that is what keeps this slice from being blocked on six other specs, and it is also the
honest state today.

**Acceptance criteria**

- The pull-request workflow runs on Linux, macOS, and Windows; Linux is the required check and the other
  two are declared in the documented required-check list.
- The registry contains exactly the six rows the spec names, each naming its owning spec: Repository
  Execution Unit identity (01), skill installation fallback (05), agent stop (10), PBI Worktree freeze
  (11), normalized content hashing (04), Check Resource isolation (12).
- A Windows run where five rows pass and one fails produces documentation marking that one row unsupported
  with its reason, and does not mark the platform supported.
- A row with no tagged test produces `unverified`, and the derivation never promotes `unverified` to
  `supported`.
- The derived platform status is written into the reference documentation by CI, and a manually edited
  status is overwritten rather than preserved.

**Blocked by**: 01. The six row *contents* are consumed contracts (see table) but are not blockers — rows
ship `unverified`.

**Parallelizable with**: 02, 03, 04, 06, 07.

---

### 06 — Conformance jobs and the published support matrix

**What to build**

Two jobs that are deliberately not required checks — harness conformance (spec 10's four Codex and
OpenCode combinations) and provider conformance (spec 14's GitHub.com and GitHub Enterprise operations) —
runnable on a schedule, by manual dispatch, and automatically for a pull request touching an adapter path.
Each run writes rows into a published support matrix recording the combination, the tested harness and
tool versions, the observed Integration Capabilities, and the stated limitations. A run that cannot
execute records an explicit skip reason and leaves its rows unsupported; a skip is never support. Rows
carry the age of the run that produced them and are presented as stale rather than current when old.
Publish the matrix into the reference documentation layer. Like slice 05, this ships with an entry-point
contract so the jobs run and record honest skips before either suite exists.

**Acceptance criteria**

- A scheduled run, a manual dispatch, and a pull request touching an adapter path each trigger the correct
  job; an ordinary pull request triggers neither and is not gated by them.
- A run with the harness absent records a skip reason and leaves the affected rows unsupported — no row
  moves to supported.
- The matrix lists the four harness combinations separately and each provider deployment separately; a
  native-only pass leaves cross-harness rows unsupported.
- Each row carries the timestamp and versions of the run that produced it, and a row older than the
  configured threshold renders with its age rather than as current.
- The published matrix is reachable from the reference documentation and is regenerated by CI rather than
  hand-edited.
- With both suites absent, the workflow still runs to completion and publishes a matrix in which every row
  is unsupported with a stated reason.

**Blocked by**: 01.

**Parallelizable with**: 02, 03, 04, 05, 07.

---

### 07 — Progressive documentation, quickstart verification, and the demo as a required check

**What to build**

The reader-facing layers in the order the spec sets: readme (what Gantry is, the three commands, the demo
recording, nothing competing for attention), quickstart (the demo first, then a real repository with
Repository Readiness and Planning Approval stated as steps rather than glossed), cookbooks one per
workflow, reference (operation catalog, configuration schema, GTP contracts, support matrix), and
`PRD.md` last. Add the CI job that runs the documented quickstart commands against the *installed tarball*
rather than the working tree, so documented behavior and shipped behavior cannot drift, and add the spec
07 demo pipeline to the required checks once it exists. Assert every shipped template file is in English.
Include the §7.6 statement that this repository's review policy is its own.

**Flag**: the quickstart verification proves the commands run; it does not prove the demo shows what the
readme claims. The spec names this gap and closes it by review — the slice should add that review step to
the release documentation rather than pretend a test covers it.

**Acceptance criteria**

- The documentation tree has the five layers in order, with the readme linking forward and `PRD.md`
  reachable only from the reference layer.
- A CI job installs the packed tarball into a temporary directory and executes every command shown in the
  quickstart, failing if any exits non-zero or if a command shown in the documentation does not exist in
  the installed binary.
- Extracting the commands from the quickstart is automated, so adding a command to the documentation
  without it working fails the job.
- Every file under `templates/` passes the English assertion, including generated `AGENTS.md` sections,
  `CONSTITUTION.md`, and spec and PBI templates.
- The readme states that this repository's branch protection and review requirement are its own policy and
  not a requirement on the reader's repository.
- The demo pipeline runs as a required check and the required-check list in the protection documentation
  names it.

**Blocked by**: 02 (needs an installable tarball). The demo-as-required-check and the demo recording need
the **demo pipeline entry point** (`demo-mode`); build the slice against the commands that exist
(`--version`, `--help`, `setup`) and extend as they land, rather than waiting.

**Parallelizable with**: 03, 04, 05, 06.

---

## What the bootstrap slice must provide to the other 18 specs

Slice 01 is the only work in the entire project that can start today, and every other spec inherits its
choices. This section is deliberately exhaustive. Items marked **OPERATOR DECISION** are choices the spec
does not make and that should be settled before slice 01 begins, not during it.

### Summary table

| Concern | What slice 01 fixes | Status |
|---|---|---|
| **Runtime** | Node, ESM (`"type": "module"`) | `engines: ">=20"` from the spec — **but the floor interacts with the SQLite driver choice below; may need to move to 22.5+** |
| **Package manager** | The lockfile and the CI install step | **OPERATOR DECISION.** §14.1's npm/pnpm/yarn list describes *target repositories*, not this one. |
| **Language / build config** | TypeScript, strict, ESM output to `dist/`, `bin: dist/bin/gantry.js`, `main`, `types` | Shape fixed by the spec; **compiler/bundler is an OPERATOR DECISION** (`tsc` vs `tsup`/`esbuild`) |
| **Test runner** | Vitest, tests under top-level `tests/`, no `sleep` (injected clock), ability to spawn a second OS process against the same database file | Vitest named by spec 19 and spec 01 |
| **SQLite driver** | A driver proven to open WAL, run `BEGIN IMMEDIATE`, and hold a lock across two OS processes | **OPERATOR DECISION — load-bearing.** See detail below. |
| **tree-sitter** | Runtime plus grammars for TypeScript, JavaScript, and Python, installed and proven to parse | Engine dependency per the handoff; spec 12 owns which grammars |
| **Lint / format** | ESLint with typescript-eslint | ESLint named by the spec. **Formatter is an OPERATOR DECISION.** |
| **Directory layout** | `src/`, `src/bin/`, `tests/`, `templates/`, `docs/`, `.github/workflows/`; `.scratch/` and `PRD.md` stay out of the package | Derived from `files: ["dist", "templates"]` |
| **`.gitignore`** | Replace the Visual Studio template entirely | **Confirmed defect** — see detail below |
| **CI entry points** | Named scripts `lint`, `typecheck`, `test`, `build` (plus `pack:check` from 02) invoked identically by CI and contributors | Required by story 33 |
| **Changelog** | `CHANGELOG.md`, consumed by slices 03 and 04 | **OPERATOR DECISION** (Keep a Changelog by hand vs Changesets vs conventional commits) |
| **Test fixtures** | Toolchain-level helpers only: temp WAL database, temp Git repository, tree-sitter parse | **Boundary call** with spec 01 — see detail below |

### Detail

**Runtime.** Node with ESM throughout (`"type": "module"`). The spec's package shape declares
`engines: { "node": ">=20" }`. This floor is not independent of the SQLite driver decision: if the driver
is Node's built-in `node:sqlite`, the floor must move to 22.5+ (or 24 for a non-experimental surface),
which contradicts the spec's stated `>=20`. Whichever is chosen, the declared engine must be enforced at
runtime by the binary (see slice 02), not only declared in the manifest.

**Package manager.** Not chosen anywhere. PRD §14.1 lists npm, pnpm, and yarn as *target repository*
package managers that Gantry's verification adapters must support — that is a statement about other
people's repositories, not about this one. The choice determines the lockfile committed, the CI install
step and its cache key, and the `packageManager` field. It is cheap to decide and expensive to change once
eighteen specs have branches open.

**Language and build config.** TypeScript in strict mode, ESM output into `dist/`, producing
`dist/bin/gantry.js` (the `bin` target), `dist/index.js` (`main`), and `dist/index.d.ts` (`types`). The
compiler-versus-bundler choice is open and has consequences: a bundler makes `dist` smaller and the
install faster but complicates shipping `templates/` and native-module resolution for the SQLite driver
and tree-sitter grammars; plain `tsc` keeps resolution simple at the cost of a larger `dist`. Whatever is
chosen must (a) emit a shebang on the binary entry point, (b) preserve the executable bit or set it during
packaging, and (c) leave `templates/` shippable as data rather than compiled.

**Test runner.** Vitest, named by both this spec's required-check table and spec 01's "prior art" note.
Constraints inherited from the rest of the project that the bootstrap configuration must satisfy:

- Tests live under a **top-level `tests/` directory**, not beside sources (spec 01 establishes this).
- **No test sleeps.** An injected clock drives backoff, heartbeats, and lease expiry (spec 01). The
  bootstrap should make fake timers available and the convention documented.
- **Real temporary SQLite database per test**, WAL enabled, deleted afterwards.
- **Real temporary Git repository per test.**
- **Two separate OS processes against the same database file.** Spec 01 is explicit that lease and
  ownership contention must be tested across processes, because an in-process mutex would pass a
  same-process test while failing the actual requirement. This means the bootstrap needs a supported way
  to execute project TypeScript in a spawned child process — either a runtime loader or a build-then-spawn
  step — **and it must work on Windows**, since slice 05 runs the suite there.
- Harness drivers and check adapters are injected as **fakes**; nothing in the shared seam may reach a real
  harness or a real network.

**SQLite driver — the decision that matters most.** No spec in the project names one. The requirements it
must satisfy, collected from spec 01 and spec 19:

- WAL mode on a real file at `~/.gantry/gantry.sqlite` in production and a temp path in tests.
- Immediate transactions (`BEGIN IMMEDIATE`) for the merge serialization lease.
- Correct locking **across OS processes**, not just across async calls.
- Prebuilt binaries available for Linux, macOS, and Windows — otherwise the Windows job in slice 05 needs a
  toolchain, and, more seriously, `npx gantry` requires a compiler on the user's machine, which breaks the
  three-commands-to-a-demo promise that the entire documentation argument in slice 07 rests on.

The two realistic candidates trade off differently: a native driver with prebuilds (better-sqlite3 and
similar) keeps the `>=20` floor but adds an install-time native artifact; the built-in `node:sqlite`
removes the native dependency entirely but raises the engine floor and contradicts the spec's stated
`>=20`. **This is the one choice that should be made before slice 01 starts.**

**tree-sitter.** An engine dependency, not optional — the handoff records that finding identity now
derives `symbol` via tree-sitter rather than taking it from the tool, which makes it load-bearing for spec
12 and therefore for spec 13 and spec 15. The bootstrap must install the runtime and prove a parse works;
spec 12 owns the grammar set. For the bootstrap smoke test, TypeScript, JavaScript, and Python are the
right minimum, since those are the adapter languages §14.1 approves. Same prebuild concern as the SQLite
driver, and the same consequence if it is missed: grammars that need compiling at install time make
`npx gantry` fail on a clean machine. The grammar packages must also end up inside the published
dependency closure, which interacts with the bundler choice above.

**Lint and format.** ESLint with typescript-eslint is named by the spec's required-check table. The
formatter is not chosen; Prettier, Biome, and ESLint stylistic rules are all defensible, and the decision
mainly affects whether format is a fifth job or folded into lint. Whichever is picked, the local command
and the CI command must be the same command (story 33).

**Directory layout.** `src/` with `src/bin/` for the binary entry point, `tests/` at the top level,
`templates/` for the shipped fixture project (spec 07) and generated-file templates (spec 06), `docs/` for
the documentation layers, `.github/workflows/` for CI. `.scratch/` and `PRD.md` stay out of the package by
virtue of the `files` allowlist, which is the point of an allowlist. Any spec shipping an asset must place
it under `dist/` or `templates/` or it will not be published — that constraint is worth stating in the
contributing documentation, because it is silent otherwise until someone packs.

**`.gitignore` — confirmed defect.** The repository currently carries the Visual Studio / .NET template.
Verified with `git check-ignore -v --no-index`:

```
.gitignore:51:**/[Bb]in/*	src/bin/gantry.ts
.gitignore:51:**/[Bb]in/*	dist/bin/gantry.js
```

The binary entry point — the single most important file in the package — is ignored. An author would
create it, build it, run it locally, and push a branch without it, and CI would fail on a file visibly
present on their disk. Beyond that, the file does not ignore `dist/`, `coverage/`, `*.tsbuildinfo`, or
`.DS_Store`, and it ignores `*.log` and `[Ll]og/` broadly enough to swallow test output someone may want
to commit as a fixture. Replace it wholesale with a Node/TypeScript ignore set rather than patching it.

**CI entry points.** Four named scripts that CI invokes verbatim and a contributor can run locally to
reproduce a failure (story 33): `lint`, `typecheck`, `test`, `build`. Slice 02 adds `pack:check`, slice 04
adds the bump and dry-run commands. CI must not inline a different command than the script — the moment it
does, "runnable locally with the same commands CI uses" becomes false.

**Changelog.** `CHANGELOG.md` must exist, because slice 03 extracts the section for a version to build the
GitHub Release body and fails the pipeline when it is missing, and slice 04 writes into it. The convention
is not chosen.

**Test fixtures — boundary call with spec 01.** Spec 01's testing section claims "fixture builders for the
temporary repository and database" as a convention *it* establishes, while slice 01 here cannot demonstrate
its own test job without the same dependencies working. Proposed boundary: **the bootstrap proves the
dependency and ships a thin helper** (open a WAL database at a temp path, initialize and tear down a temp
Git repository, parse a file with tree-sitter); **spec 01 builds the real fixture builders on top**, with
the seeded state, the injected clock, and the named fake drivers. This needs operator confirmation,
because the alternative — spec 01 owning the whole seam — leaves slice 01 with nothing testable.

### Consolidated list of open choices

1. **SQLite driver** — and therefore the real `engines` floor. Highest impact; decide first.
2. **Package manager** for this repository (not the §14.1 target-repository list).
3. **Compiler versus bundler** for the build, given native modules and shipped `templates/`.
4. **Formatter** (Prettier / Biome / ESLint stylistic), and whether format is its own check.
5. **Changelog convention and tooling**, consumed by slices 03 and 04.
6. **Exact `engines` minimum**, if the driver decision forces it above the spec's stated `>=20`.
7. **Whether macOS and Windows jobs are required checks or informational**, which slice 05 documents either
   way but cannot decide.
8. **Whether the published version really starts at `4.0.0`** (see risk 9).
9. **The test-fixture boundary with spec 01** described above.

---

## Contracts this spec CONSUMES from other specs

| Contract | Owning spec slug | My slice |
|---|---|---|
| Demo pipeline entry point and its deterministic scenario | `demo-mode` | 07 (required check, readme recording, quickstart) |
| Generated template set shipped under `templates/` | `repository-readiness`, `demo-mode` | 02 (tarball manifest), 07 (English assertion) |
| Harness conformance suite entry point and result shape | `harness-adapters` | 06 |
| Provider conformance suite entry point and result shape | `git-integration` | 06 |
| Support matrix row schema (combination, versions, Integration Capabilities, limitations) | `harness-adapters` | 06 |
| Windows row — Repository Execution Unit identity (case-insensitive paths, UNC vs mapped drive, 8.3 names, path length) | `execution-core` | 05 |
| Windows row — skill installation symlink unavailability, copy fallback, drift reporting | `machine-setup` | 05 |
| Windows row — agent stop with no cooperative process signal; job objects or `agentInterruption: "none"` | `harness-adapters` | 05 |
| Windows row — PBI Worktree freeze and open-file-cannot-be-deleted semantics during cleanup | `pbi-execution-loop` | 05 |
| Windows row — normalized content hashing under `core.autocrlf` | `data-handling` | 05 |
| Windows row — Check Resource ports and temporary directories under a different locking model | `verification-adapters` | 05 |
| Operation core `invoke` and its test fixture builders | `execution-core` | 01 (boundary only — bootstrap supplies the toolchain, not the builders) |
| Quickstart command set (`gantry setup`, `gantry init --demo`, and the real-repository path) | `machine-setup`, `repository-readiness`, `demo-mode` | 07 |

---

## Contracts this spec PUBLISHES for other specs

| Contract | My slice | Who waits on it |
|---|---|---|
| Repository toolchain and CI entry points (`lint`, `typecheck`, `test`, `build`) | 01 | All 18 |
| Test seam baseline: Vitest, `tests/` layout, WAL SQLite driver, tree-sitter runtime and grammars, temp-repo helper, cross-process test capability | 01 | `execution-core` first, then all; `verification-adapters` for tree-sitter specifically |
| Directory layout and the `files` allowlist — anything a spec ships must land in `dist/` or `templates/` | 01, 02 | `machine-setup`, `repository-readiness`, `demo-mode`, and every spec shipping a skill or template |
| Tarball manifest and installed-binary smoke harness | 02 | Any spec adding shipped assets |
| Support matrix artifact, skip-is-not-support rule, and row age semantics | 06 | `harness-adapters`, `git-integration` (shared "support matrix" concept — still has no `CONTEXT.md` entry) |
| Platform divergence row registry: test tag → row → derived per-row status | 05 | `execution-core`, `data-handling`, `machine-setup`, `harness-adapters`, `pbi-execution-loop`, `verification-adapters` |
| Documentation layer layout and the cookbook slot per workflow | 07 | Every spec that ships a cookbook page or a reference section |
| Release procedure (bump, dry run, tag, observe) | 03, 04 | Maintainers only |

---

## Risks / judgement calls

1. **Slice 01 is a hard blocking root, and I did not try to hide that.** Splitting it further would produce
   slices that deliver a config file rather than a running pipeline, which is not a tracer bullet. I kept
   it minimal-but-runnable (a real binary, a green four-job workflow, proven engine dependencies) and
   everything else fans out from it in parallel.

2. **Bootstrap should NOT be split from the first CI workflow, but SHOULD be split from the release
   pipeline proper.** The team lead asked directly. A manifest and a tsconfig that nothing runs is exactly
   the deliverable the tracer-bullet rule exists to forbid; the bootstrap is only demonstrably correct when
   a pull request goes green. But packaging (02), publishing (03), and the local release flow (04) are
   separable and nothing else waits on them — so they are their own slices.

3. **Three toolchain choices are unmade and one of them is load-bearing.** Package manager, formatter, and
   changelog convention are close to cosmetic. The **SQLite driver is not**: it determines the `engines`
   floor (`node:sqlite` needs 22.5+, which contradicts the spec's `>=20`), and a native module without
   prebuilt binaries for all three platforms breaks both the Windows job and the "three commands to a demo"
   promise the whole documentation argument rests on. Decide before slice 01 starts, not during it.

4. **Overlap with `execution-core` on the test seam.** Spec 01 explicitly claims Vitest, `tests/`, and
   fixture builders as conventions *it* establishes. Slice 01 here has to install and prove those same
   dependencies or nothing can run. I drew the line at "bootstrap proves the dependency works,
   execution-core builds the fixtures on top" — please confirm, because the alternative (execution-core
   owns the whole seam) makes this spec's slice 01 unable to demonstrate its own test job.

5. **The `.gitignore` defect is real and silent.** `git check-ignore -v --no-index` confirms
   `.gitignore:51 **/[Bb]in/*` matches `src/bin/gantry.ts`. If slice 01 does not replace the file, the
   binary entry point is created, builds locally, and never gets committed — and CI fails on a file the
   author can see on disk.

6. **The required-check set grows over time, which branch protection does not model well.** The spec wants
   the demo pipeline as a required check, but the demo needs specs 01, 03, and 07. I made the pull-request
   workflow additive and put the required-check list in documentation as an inspection-verified item,
   updated as jobs land. Treat the protection settings as a living operator task, not a one-time
   configuration.

7. **Two acceptance items are not testable as written, and I reframed them.** "No local command path can
   publish" became "no package script and no documented procedure publishes, and the registry token exists
   only as a workflow secret" — anyone with a token can always publish, and claiming otherwise would be
   exactly the overclaiming ADR-0001 forbids. "Installation under a Node version below the declared engine
   is refused" became a runtime guard in the binary, because npm's `engine-strict` defaults to false and
   `engines` alone only warns.

8. **Slices 05 and 06 ship deliberately empty.** The platform registry ships with all six rows `unverified`
   and the conformance jobs ship recording honest skips. This is what makes them startable today instead of
   blocked behind six other specs — and it is also an accurate description of the project's current
   evidence. If the operator would rather these slices wait until there is something real to record, they
   move to the back and slice 01 is the only thing runnable now.

9. **Version `4.0.0` at first publish.** The spec's package shape fixes it. Publishing a `4.0.0` as the
   first-ever release of a package with no 1, 2, or 3 is a product decision rather than a technical one,
   and `0.x` or a prerelease tag until the pipeline has shipped something real may serve better. I did not
   change it — flagging for review.

10. **The quickstart-drift gap the spec names is not closed by this proposal either.** Verifying that the
    documented commands succeed proves they run; it does not prove the demo shows what the readme claims.
    Slice 07 adds a review step to the release documentation rather than a test, which matches what the
    spec says is possible, but it means this remains a discipline item rather than a gate.

---

## Files referenced

- `/Users/julioborges/src/personal/gantry/.scratch/release-engineering/spec.md` — the spec, read in full
- `/Users/julioborges/src/personal/gantry/.gitignore` — line 51, the `**/[Bb]in/*` defect
- `/Users/julioborges/src/personal/gantry/.scratch/execution-core/spec.md` — lines 392–415, the test seam
  conventions that overlap slice 01
- `/Users/julioborges/src/personal/gantry/CONTEXT.md` — domain vocabulary
- `/Users/julioborges/src/personal/gantry/docs/adr/0001-harness-first-control-boundary.md`,
  `/Users/julioborges/src/personal/gantry/docs/adr/0002-worktree-isolation-and-serialized-integration.md`
