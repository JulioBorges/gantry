# Operation core seam and Repository Execution Unit registration

Type: issue
Status: ready-for-agent
Slice: execution-core#01
Spec: [`../spec.md`](../spec.md) (spec 01, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/execution-core/spec.md`](../spec.md)

## What to build

Stand up the operation core's single `invoke` entry point with the `OperationRequest` / `OperationOutcome` / `Rejection` shapes as a contract, including the full rejection code vocabulary even though most codes are unreachable until later slices. Publish the operation input schemas as runtime data keyed by operation name, so a transport can derive its own surface from the catalog without a parallel hand-maintained list. This slice does **not** bootstrap the repository: the toolchain, the TypeScript and Vitest configuration, the test layout, the SQLite WAL driver, the tree-sitter dependency and the ability to spawn a second operating-system process against one database file all arrive from `release-engineering#01` and must be consumed, not re-declared.

Open a real WAL SQLite database with a forward-only schema version check that refuses to open an unknown version, and implement the atomic transition primitive — state change, receipt, audit record, and any counter change written in one transaction — plus `requestId` idempotency so an accepted request replayed with identical content returns its original receipt without repeating anything. Prove all of it end-to-end with the first two real operations, `unit.register` and `audit.query`, and a minimal `state.project`. The Repository Execution Unit also carries an immutable `mode` property fixed at registration, and the operation boundary enforces the cross-mode predicate that refuses a request whose referenced records do not all belong to one mode, with its own rejection code; this is the enforcement point, and `demo-mode#01` only consumes it.

Unit identity derives from the canonical Git common directory resolved through its real path, with case-normalization where the filesystem is case-insensitive and exact comparison where it is not, UNC and mapped-drive and 8.3 forms resolved to a canonical form, a resolved path over the platform length limit blocking at registration, a matching fingerprint with a changed path recorded as relocation preserving the unit identifier, and a matching path with a changed fingerprint blocking for operator classification. Windows is an unvalidated platform for this project, so the Windows-specific criteria below are proven by tests driving a path-resolution seam with the platform behaviour injected — the real-Windows evidence for them is the platform matrix row owned by `release-engineering#05`, not this slice. Finally, ship the shared fixture kit this spec and every later spec binds to: temporary WAL database, temporary real Git repository with worktree and clone helpers, injected clock, named fake harness driver, named fake check adapter, and state builders that place a unit, execution, PBI or gate at a named state.

## Acceptance criteria

- [ ] Two worktrees of one clone resolve to one Repository Execution Unit; two clones of the same remote resolve to two, and a remote URL is never an identity input.
- [ ] A relocated clone keeps its unit identifier and prior history; a changed fingerprint at the same path is rejected rather than merged.
- [ ] Paths differing only in case resolve to one unit on a case-insensitive filesystem and to two on a case-sensitive one; a path exceeding the platform limit is rejected at registration with a message naming the limit.
- [ ] Replaying an accepted `unit.register` with the same `requestId` and identical content returns the original receipt and produces no second audit record; different content under the same `requestId` returns `duplicate_conflict`.
- [ ] A process killed mid-transition leaves either the complete transition with its audit record or neither, never a state change without its explanation.
- [ ] Opening a database whose schema version is unknown to the running engine fails with a distinct error instead of proceeding.
- [ ] The input schema for every registered operation is readable at runtime keyed by operation name, and a newly registered operation appears in that data without any additional declaration.
- [ ] A Repository Execution Unit's `mode` is fixed at registration and cannot be changed by any operation; a request whose referenced records span more than one mode is rejected with the cross-mode boundary rejection code and changes nothing.
- [ ] No test asserts on SQL, table names, column names, or module layout; every assertion is on a receipt, a rejection code, or a state projection.

## Blocked by

- `release-engineering#01` — repository bootstrap: toolchain, TypeScript and Vitest configuration, test layout, the SQLite WAL driver proven for `BEGIN IMMEDIATE` and cross-process locking, and the ability to spawn a second process against one database file.
- `data-handling#01` — redaction sink enforcement interface for audit references and normalized content hashing; build against the declared interface and integrate when it lands.
