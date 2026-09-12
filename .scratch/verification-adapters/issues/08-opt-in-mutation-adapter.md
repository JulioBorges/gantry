# Opt-in mutation adapter

Type: issue
Status: ready-for-agent
Slice: verification-adapters#08
Spec: [`../spec.md`](../spec.md) (spec 12, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/verification-adapters/spec.md`](../spec.md)

## What to build

An adapter, off by default, that measures verification strength rather than finding source defects — the one deterministic signal for an assertion weakened in place. Stryker for TypeScript and JavaScript, mutmut for Python, both run incrementally and scoped strictly to code the PBI's diff touched and to code covered by tests the diff modified; a whole-repository run must not be reachable. Only a transition from killed-by-assertion to survived produces a finding; a mutant killed by the clock is recorded and displayed but never contributes to the decision.

The per-mutant bound is derived from the unmutated suite's own measured duration times a declared factor, never a wall-clock constant, and the check itself has no elapsed-time cap — its duration is recorded, not enforced. Comparability comes from declaring a machine-scoped check resource so target and candidate runs serialize, rather than from a tolerance threshold. Surviving mutants are emitted as ordinary normalized findings under a `mutation:<operator>` rule namespace with the standard identity derivation, so the entropy gate needs no special case.

The operator should expect a cost when enabling this: the machine-scoped resource serializes mutation runs machine-wide, so on a machine running several repositories mutation checks queue behind each other and observed parallelism drops. That is the trade for comparable evidence, and it is why the adapter is opt-in. Parser conformance is proven against recorded tool output, this spec's deliberate exception to the standing test seam; the shared seam applies to everything else here.

## Acceptance criteria

- [ ] The adapter runs only under explicit opt-in; a default check set invokes no mutation run.
- [ ] Mutants are generated only for diff-touched code and code covered by tests the diff modified; a whole-repository run is not reachable through any configuration.
- [ ] A test weakened from an equality assertion to a presence assertion produces surviving mutants that were previously killed by assertion, emitted as normalized findings under the `mutation:<operator>` rule namespace with standard identity derivation.
- [ ] A mutant transitioning from killed-by-assertion to killed-by-timeout is recorded and displayed, produces no finding, and does not block.
- [ ] The per-mutant bound scales numerically when the fixture suite is made slower, proving derivation from measured duration rather than a constant; the check records its own duration and enforces no wall-clock limit on itself.
- [ ] Two mutation runs serialize on the machine-scoped resource, including a target run against a candidate run of the same check.

## Blocked by

- `verification-adapters#01` — the normalized finding shape and identity derivation that surviving mutants are emitted through.
- `verification-adapters#05` — the machine-scoped check resource declaration and its scoped allocation.
- `git-integration#02` — the merge candidate and current target revision pair with its touched-path diff, which scopes mutant generation.
- `config-and-snapshot#04` — the mutation opt-in configuration value bound to the Execution Rule Snapshot.
