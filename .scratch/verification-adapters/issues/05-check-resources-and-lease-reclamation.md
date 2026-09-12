# Check resources: scoped declaration, allocation, and lease reclamation

Type: issue
Status: ready-for-agent
Slice: verification-adapters#05
Spec: [`../spec.md`](../spec.md) (spec 12, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/verification-adapters/spec.md`](../spec.md)

## What to build

Check Resource declaration with kind, the real shared identity, sharing scope, and isolatability, plus the allocator that prefers isolation and falls back to serialization. When a resource is isolatable, a per-execution instance is provisioned and no lock is taken; otherwise a lease is acquired at the declared scope, with heartbeat and expiry, reclaimable only after the holder has been reconciled.

Machine scope is what makes two clones of the same repository serialize on one port — worktree separation never substitutes for it. Coordination applies identically to target validation and candidate validation of the same check. Expose the declarations as a projection the scheduler can consult for dispatch eligibility without knowing adapter internals.

The lease test must run two operating-system processes. A same-process test passes against an in-process mutex and proves nothing about a machine-scoped lock, so that criterion is not optional.

## Acceptance criteria

- [ ] Two checks in different repository execution units declaring the same machine-scoped port identity serialize; a worktree-scoped temporary directory takes no lock.
- [ ] An isolatable resource is provisioned per execution and takes no lock.
- [ ] Target validation and candidate validation of the same check serialize against each other on a shared resource.
- [ ] A lease whose holder crashed is reclaimed only after reconciliation, proven by a test running two operating-system processes — not an in-process mutex.
- [ ] A machine-scoped requirement is still serialized when the two runs come from distinct worktrees.
- [ ] The resource declaration projection is readable by a scheduler consumer and contains scope and identity without adapter-internal detail.

## Blocked by

- `verification-adapters#01` — the check-run input that carries allocated resources and the Repository Execution Unit subject.
- `execution-core#07` — the lease primitive with heartbeat, expiry, and reconciliation before reclamation.
- `release-engineering#01` — the proven ability to spawn a second operating-system process against shared state, which the lease test requires.
