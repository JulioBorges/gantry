# Repository bootstrap and the first required checks

Type: issue
Status: ready-for-agent
Slice: release-engineering#01
Spec: [`../spec.md`](../spec.md) (spec 19)
Created: 2026-09-12

## Parent

[`.scratch/release-engineering/spec.md`](../spec.md)

## What to build

This is the blocking root of the entire Gantry v4 project. It is the only work that can start against
the current empty repository, and all eighteen other specs inherit every choice made here. Nothing else
bootstraps the repository — `execution-core#01` consumes this toolchain and must not re-declare it.

Turn the empty repository into a Node/TypeScript project whose pull-request workflow actually runs green.
That means: a package manifest (`"type": "module"`, `engines`, `bin`, `main`, `types`), a TypeScript
configuration in strict mode emitting ESM into `dist/`, Vitest, ESLint with typescript-eslint, a formatter,
the directory layout, and `.github/workflows/pull-request.yml` with four jobs — lint, typecheck, test,
build. The tracer bullet is a real binary: `src/bin/gantry.ts` that builds to `dist/bin/gantry.js` and
prints its version, so each of the four jobs has real work rather than an empty target. A manifest and a
tsconfig that nothing runs is not a tracer bullet, which is why the bootstrap is deliberately not split
from the first CI workflow. It *is* split from the release pipeline proper: packaging (`#02`), publishing
(`#03`) and the local release flow (`#04`) are separate slices and nothing else waits on them.

**CI entry points.** Four named scripts — `lint`, `typecheck`, `test`, `build` — that CI invokes verbatim
and a contributor can run locally to reproduce a failure (story 33). CI must never inline a different
command than the script; the moment it does, "runnable locally with the same commands CI uses" becomes
false. `#02` adds `pack:check` and `#04` adds the bump and dry-run commands to the same set.

**Directory layout.** `src/` with `src/bin/` for the binary entry point, a top-level `tests/` directory
(tests do not live beside sources), `templates/` for the shipped fixture project and generated-file
templates, `docs/` for the documentation layers, and `.github/workflows/` for CI. `.scratch/` and `PRD.md`
stay out of the published package by virtue of the `files` allowlist that `#02` asserts. State in the
contributing documentation that any spec shipping an asset must place it under `dist/` or `templates/` or
it will not be published — that constraint is silent until someone packs.

**SQLite driver — settled, do not re-litigate.** The driver is **better-sqlite3**, keeping
`engines: { "node": ">=20" }`. It must be installed and *proven*, not merely declared: WAL mode on a real
file, immediate transactions (`BEGIN IMMEDIATE`) for the merge serialization lease, and correct locking
**across two OS processes** rather than only across async calls within one. Prebuilt binaries must be
available for Linux, macOS and Windows — a native module without prebuilds needs a compiler on the user's
machine, which breaks both the Windows job in `#05` and the `npx gantry` promise that the whole
documentation argument in `#07` rests on. Production uses `~/.gantry/gantry.sqlite`; tests use a temporary
path. The cross-process proof matters because an in-process mutex would pass a same-process test while
failing the actual requirement that `execution-core` places on lease and ownership contention.

**tree-sitter.** An engine dependency, not optional: finding identity derives `symbol` via tree-sitter
rather than taking it from the tool, which makes it load-bearing for `verification-adapters` and therefore
for `entropy-gate` and `baseline-transitions`. Install the runtime plus grammars for TypeScript,
JavaScript and Python — the adapter languages §14.1 approves — and prove a parse works.
`verification-adapters` owns the full grammar set. The same prebuild concern applies and has the same
consequence if missed: grammars that need compiling at install time make `npx gantry` fail on a clean
machine. The grammar packages must also end up inside the published dependency closure, which interacts
with the compiler-versus-bundler decision below.

**Test seam boundary with `execution-core` — settled.** This slice **proves the dependencies work** and
ships thin helpers: open a WAL database at a temporary path, parse a TypeScript and a Python file with
tree-sitter, create and tear down a temporary Git repository, and spawn a second OS process that observes a
write from the first. `execution-core#01` builds the real fixture builders on top — seeded state, the
injected clock, and the named fake harness drivers and check adapters. State this boundary explicitly in
the contributing documentation so the two specs do not collide. Conventions the bootstrap configuration
must make available for those builders: fake timers (there are no test sleeps anywhere in this project; an
injected clock drives backoff, heartbeats and lease expiry), a real temporary database per test deleted
afterwards, a real temporary Git repository per test, and a supported way to execute project TypeScript in
a spawned child process — either a runtime loader or a build-then-spawn step — **which must work on
Windows**, since `#05` runs the suite there.

**The `.gitignore` defect was already fixed — verify it, do not redo it.** The repository originally
carried the Visual Studio / .NET template, whose line 51 (`**/[Bb]in/*`) matched `src/bin/gantry.ts`. The
binary entry point — the single most important file in the package — was ignored, so an author would have
created it, built it, run it locally, pushed a branch without it, and watched CI fail on a file visibly
present on their disk. The template also failed to ignore `dist/`, `coverage/`, `*.tsbuildinfo` and
`.DS_Store`.

The file was replaced wholesale with a Node/TypeScript ignore set on 2026-09-12, before this issue was
picked up. This slice only has to confirm the resulting behaviour through the acceptance criterion below,
and extend the set if a tooling choice made here introduces new output paths — a bundler's cache
directory, for example. Note that `dist/` **is** ignored as build output; only the TypeScript source under
`src/bin/` must remain committable.

**Branch protection.** Document `main` protection — one approving review, required status checks, linear
history, no force-push — as *this repository's* policy, with the §7.6 note that it is not a requirement
Gantry places on a user's repository. The required-check set grows as jobs land (the demo pipeline as a
required check needs `demo-mode`), so keep the pull-request workflow additive and treat the required-check
list as an inspection-verified documentation item updated over time rather than a one-time configuration.

**Open choices the implementer decides and documents.** These are explicit decisions to be recorded in the
repository, not assumptions to be left implicit, because eighteen specs inherit them: (1) the **package
manager** for this repository — §14.1's npm/pnpm/yarn list describes *target* repositories that Gantry's
verification adapters must support, not this one; the choice determines the committed lockfile, the CI
install step and its cache key, and the `packageManager` field; (2) **compiler versus bundler** — a bundler
makes `dist` smaller and the install faster but complicates shipping `templates/` and resolving the native
better-sqlite3 binding and the tree-sitter grammars, while plain `tsc` keeps resolution simple at the cost
of a larger `dist`; whichever is chosen must emit a shebang on the binary entry point, preserve or set the
executable bit, and leave `templates/` shippable as data rather than compiled; (3) the **formatter**
(Prettier, Biome or ESLint stylistic rules), and whether format is a fifth job or folded into lint — the
local command and the CI command must be the same command either way; (4) the **changelog convention and
tooling**, with `CHANGELOG.md` created here because `#03` extracts the section for a version to build the
GitHub Release body and fails the pipeline when it is missing, and `#04` writes into it.

## Acceptance criteria

- [ ] A pull request runs a workflow with four jobs — lint, typecheck, test, build — and all four pass on a clean checkout using the same package scripts documented for local use.
- [ ] `git check-ignore src/bin/gantry.ts` reports no match, so the binary entry point is committable; `dist/`, `coverage/`, `*.tsbuildinfo` and `.DS_Store` are ignored as build and environment output.
- [ ] `node dist/bin/gantry.js --version` prints the version from the package manifest after a clean build.
- [ ] A test opens a temporary SQLite database with WAL enabled, writes and reads a row, and deletes the file; a test parses a TypeScript and a Python source file with tree-sitter and reads a named symbol; a test creates, commits into, and removes a temporary Git repository.
- [ ] A test spawns a second OS process that opens the same temporary database file and observes a write from the first — proving the cross-process concurrency seam `execution-core` requires is runnable.
- [ ] `docs/` states the branch-protection settings for `main` and states explicitly that they are this repository's policy, not a requirement Gantry places on a user's repository.
- [ ] The four open choices — package manager, compiler versus bundler, formatter, and changelog convention — are each recorded in the repository as a stated decision with its reason, and `CHANGELOG.md` exists.

## Blocked by

None - can start immediately
