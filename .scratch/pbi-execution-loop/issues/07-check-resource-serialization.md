# Check Resource serialization in scheduling

Type: issue
Status: ready-for-agent
Slice: pbi-execution-loop#07
Spec: [`../spec.md`](../spec.md) (spec 11, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/pbi-execution-loop/spec.md`](../spec.md)

## What to build

Replace the injected resource-availability port of `pbi-execution-loop#02` with a real consultation of the declared Check Resources for a PBI's verification. A resource declared `isolatable` is provisioned per execution and imposes no constraint. A resource shared at unit or machine scope makes a PBI ineligible while another PBI holds it, keeping it `queued` with a rejection naming the resource.

This is why observed parallelism can be lower than the configured capacity limit: separate worktrees do not isolate a port or a database, so two PBIs whose checks need the same shared resource serialize regardless of available capacity. A capacity limit is a ceiling, not a target.

The verification spec owns the declarations and the locks. This slice consults them for eligibility and never takes, holds, or releases a lock of its own; the lock lifecycle stays with the check runner.

## Acceptance criteria

- [ ] Two PBIs whose verification declares the same machine-scoped resource never run concurrently, even with two capacity slots free, and the second's rejection names the resource.
- [ ] Two PBIs whose verification declares only `isolatable` resources run concurrently under sufficient capacity.
- [ ] Machine-scoped serialization holds across two Repository Execution Units in the same test, proving the scope is not unit-local.
- [ ] Releasing the resource makes the waiting PBI eligible without operator intervention.
- [ ] The scheduler consults declarations and does not acquire or release a resource lock itself; the lock lifecycle remains with the check runner.
- [ ] Effective parallelism reported in the projection reflects resource-bound serialization rather than the configured limit.

## Blocked by

- `pbi-execution-loop#02` — the eligibility conjunction and the injected resource-availability port this slice replaces.
- `verification-adapters#05` — `CheckResourceDeclaration` with its sharing scope (`machine` / `unit` / `isolatable`) and the resource lease and lock lifecycle.
