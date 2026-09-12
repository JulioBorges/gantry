# Finding change across configurations: rule mappings and the count fallback

Type: issue
Status: ready-for-agent
Slice: baseline-transitions#03
Spec: [`../spec.md`](../spec.md) (spec 15, wave 4)
Created: 2026-09-12

## Parent

[`.scratch/baseline-transitions/spec.md`](../spec.md)

## What to build

Compute the finding difference between the old and new reports in a `both_run` manifest. Findings match on problem identity directly wherever the rule identifier is unchanged, because identity already excludes the message and derives the enclosing symbol through tree-sitter rather than taking it from the tool — so a version that merely rewords its output does not disturb identity at all.

What a version *can* change is a rule identifier. A linter that renames or splits a rule produces findings that look entirely new, and that is a short enumerable list rather than a per-finding problem, which is why the bridge here is `ruleMappings` plus a per-rule count fallback rather than a per-finding identity mapping. A mapping bridges the old and new identifiers; the adapter supplies it where it knows one, and an operator supplies it through an operator-only operation otherwise, with the `source` recorded on every mapping either way. Treat an operator-supplied mapping as the weaker of the two — nothing validates that two rules are semantically equivalent.

Where a rule changed identifier and no mapping exists, fall back to comparing counts per rule and path, and mark on the manifest that the comparison relied on the fallback, so a reader knows the difference is not attributable to individual occurrences. Report `newlySurfaced` and `noLongerSurfaced` counts derived from the matched set.

## Acceptance criteria

- [ ] A proposed configuration that rewords messages without renaming rules produces a full identity-level comparison with no mappings recorded and no fallback flag.
- [ ] A renamed rule with an adapter-supplied mapping produces a full comparison, with the mapping recorded and `source: "adapter"`.
- [ ] A renamed rule with an operator-supplied mapping produces the same comparison with `source: "operator"`; the mapping operation is refused from a non-operator channel.
- [ ] A renamed rule with no mapping produces per-rule, per-path counts and sets the manifest's fallback indicator; `newlySurfaced` is derived from the count delta and no occurrence is attributed.
- [ ] A mapping naming a rule absent from either configuration is rejected rather than silently ignored.
- [ ] `newlySurfaced` and `noLongerSurfaced` are recomputed from evidence on every manifest read and never persisted as independently mutable values.

## Blocked by

- `baseline-transitions#02` — the manifest and its comparison mode, which this slice fills in for the `both_run` case.
- `verification-adapters#01` — the normalized finding shape, the problem identity tuple with the message excluded, and the documented no-location count fallback.
- `verification-adapters#01` — optional adapter-supplied rule mapping declaring known rule renames between two tool versions, consumed as `source: "adapter"`.
- `verification-adapters#02` — the tree-sitter enclosing-symbol derivation that completes the identity tuple this comparison is written against.
- `execution-core#02` — operator-only channel enforcement for the operator-supplied mapping operation.
