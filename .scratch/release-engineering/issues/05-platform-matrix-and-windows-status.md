# Platform matrix and per-row Windows status

Type: issue
Status: ready-for-agent
Slice: release-engineering#05
Spec: [`../spec.md`](../spec.md) (spec 19)
Created: 2026-09-12

## Parent

[`.scratch/release-engineering/spec.md`](../spec.md)

## What to build

Add macOS and Windows jobs to the pull-request workflow running the platform-independent suites, and build
the mechanism that derives documented platform status **per behavior row rather than from the job's
overall result**. §14.1 leaves Windows "expected but unverified" and instructs that platform capability be
reported from tests rather than inferred from Node.js portability, so a Windows job that passes everything
except one row is not evidence of support for that one.

Define a registry of the six divergent behaviors the spec names, each carrying an owning spec, a test tag,
and a derived status of `supported`, `unsupported (reason)`, or `unverified (no test yet)`. The derivation
step reads the per-tag results from the Windows job and writes the platform status into the reference
documentation; a hand-edited status is overwritten rather than preserved.

The six rows and the issues that will eventually supply their tagged tests:

| Row | Owning spec | Where the test will come from |
|---|---|---|
| Repository Execution Unit identity — case-insensitive paths, UNC versus mapped drive, 8.3 short names, path length | `execution-core` | `execution-core#01` |
| Skill installation — symlinks unavailable without developer mode, the copy fallback and its drift reporting | `machine-setup` | `machine-setup#03` (fallback), `machine-setup#04` (drift reporting) |
| Agent stop — no cooperative process signal; job objects or a declared `agentInterruption: "none"` | `harness-adapters` | `harness-adapters#02` (capability declaration), `harness-adapters#04` (process identity) |
| PBI Worktree freeze — read-only enforcement and open-file-cannot-be-deleted semantics during cleanup | `pbi-execution-loop` | `pbi-execution-loop#01` |
| Normalized content hashing under `core.autocrlf` divergence between working tree and blob | `data-handling` | `data-handling#01` |
| Check Resource ports and temporary directories under a different locking model | `verification-adapters` | `verification-adapters#05` |

**Ship the registry with all six rows present and `unverified`.** That is what keeps this slice startable
now rather than blocked behind six other specs, and it is also an accurate description of the project's
current evidence: no tagged test exists yet for any row. The derivation must never promote `unverified` to
`supported`; rows move only when a tagged test runs and passes. Shipping deliberately empty is the intent
here, not a shortcut.

Whether the macOS and Windows jobs are required checks or informational is an open operator choice recorded
in `release-engineering#01`. This slice documents the answer either way and does not decide it; Linux is
the required check and the documented required-check list states the standing of the other two.

## Acceptance criteria

- [ ] The pull-request workflow runs on Linux, macOS, and Windows; Linux is the required check and the other two are declared in the documented required-check list.
- [ ] The registry contains exactly the six rows the spec names, each naming its owning spec: Repository Execution Unit identity (`execution-core`), skill installation fallback (`machine-setup`), agent stop (`harness-adapters`), PBI Worktree freeze (`pbi-execution-loop`), normalized content hashing (`data-handling`), Check Resource isolation (`verification-adapters`).
- [ ] A Windows run where five rows pass and one fails produces documentation marking that one row unsupported with its reason, and does not mark the platform supported.
- [ ] A row with no tagged test produces `unverified`, and the derivation never promotes `unverified` to `supported`.
- [ ] The derived platform status is written into the reference documentation by CI, and a manually edited status is overwritten rather than preserved.

## Blocked by

- `release-engineering#01` — provides the pull-request workflow, the named CI scripts, and the cross-platform test seam the macOS and Windows jobs run.
