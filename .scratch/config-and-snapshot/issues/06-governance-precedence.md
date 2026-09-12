# Governance Precedence resolution and conflict blocking

Type: issue
Status: ready-for-agent
Slice: config-and-snapshot#06
Spec: [`../spec.md`](../spec.md) (spec 02, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/config-and-snapshot/spec.md`](../spec.md)

## What to build

Resolution of the rules bearing on a decision into typed assertions, each tagged with its source level, and selection of the highest-precedence assertion per rule key. The level order and the resolution outcome shape are the decision-rich part:

```ts
type SourceLevel =
  | 1 // provider protections and absolute security requirements
  | 2 // the approved Execution Rule Snapshot
  | 3 // CONSTITUTION.md
  | 4 // applicable ADRs
  | 5 // approved spec and PBIs
  | 6 // AGENTS.md and operational configuration

type Resolution =
  | { resolved: true; value: unknown; level: SourceLevel; overridden: RuleAssertion[] }
  | { resolved: false; conflict: RuleAssertion[] };   // same level, incompatible values
```

Overridden assertions are retained in the resolution so an audit can show what was outranked. A lower level attempting to weaken a higher-level invariant is rejected as an override attempt rather than quietly losing. Two incompatible assertions at the same level are unresolvable: the affected transition blocks and the core surfaces a concrete proposed governance or plan amendment naming both sources and the conflicting key. Resolution must be consulted by at least one real transition in the core and recorded alongside the decision it informed — a resolver nobody consults is not a governance mechanism, so tests drive the transition, not the resolver.

Two boundaries hold here. **Level 2 arrives later**: the snapshot identity that backs level-2 assertions is defined by `config-and-snapshot#04`, so this slice carries a stub level-2 source and proves the resolution and conflict machinery against levels 1 and 3-6; whoever picks this up should expect to swap the stub for the real snapshot source once slice 04 lands. And **prose stays prose**: the resolver does not attempt to extract machine-checkable keys from prose in a constitution or an ADR. A prose-only document participates at its level and contributes no machine-checkable keys, so it can block through conflict but never silently resolve one. This is deliberate, not a gap — `entropy-gate` owns executable ADR rules. Expect the set of recognized rule keys to grow; do not expect the mechanism to change.

## Acceptance criteria

- [ ] A level-6 assertion loses to a level-3 one, and the recorded resolution names what was overridden and from where.
- [ ] A level-6 assertion that would weaken a level-3 invariant is rejected as an override attempt, distinguishable in the outcome from merely being outranked.
- [ ] Two incompatible assertions at the same level block the affected transition and produce a proposed amendment naming both sources and the conflicting key.
- [ ] A provider protection at level 1 wins over every local setting, including the snapshot.
- [ ] Every decision informed by a resolution records which source level and which document version supplied the governing rule.
- [ ] Changing the precedence order itself is treated as a level-3 change requiring explicit governance approval.

## Blocked by

- `config-and-snapshot#01` — the effective configuration document that supplies level-6 assertions.
- `execution-core#07` — a real transition (Merge Authorization) that consults a governance rule key, so the resolution has a consumer to be driven through.
