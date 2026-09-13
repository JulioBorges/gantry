# Canonical round workflow

One round contains only Issues selected by `frontier.py` whose dependency readiness is satisfied. The
caller supplies `args.round`, `args.issues`, `args.models`, `args.branch`, `args.baseRef`,
`args.isolate`, `args.correctionBudget`, `args.skillDir`, `args.repoRoot`, effective `args.policy` and
rendered `args.paths`.

```
implement (TDD) → review (standards + Spec) → one review fix pass
→ adversarial Critic → correction implementer ⇄ Critic (at most correctionBudget)
```

## Per-Issue roles

**Implementer:** a fresh agent reads the complete Issue, parent Spec, settled decisions, context and ADRs.
It follows red → green TDD at the approved CLI, script-interface and template-file seams, makes small
commits, runs `gates.py --run --diff-base <baseRef> --cwd "$(pwd)"`, and leaves a clean tree. It does not
edit `ROADMAP.md`, Issue statuses or criteria checkboxes.

**Reviewer:** a fresh agent reviews the delivery against two independent axes:

- standards: documented repository rules, context and ADRs;
- Spec: every Issue acceptance criterion and its `What to build` contract.

It reports blocking and non-blocking findings. Exactly one fresh Implementer pass addresses blocking review
findings in the same worktree.

**Critic:** a fresh adversarial Critic defaults to refutation. It runs `acceptance.py <issue> --json` and
`gates.py --run --diff-base <baseRef> --cwd "$(pwd)" --json`, verifies evidence per criterion, checks the
tree and diff for weakened tests, placeholders and scope creep, and returns `complete` only with proof.
Refutations generate ordered required fixes and consume one correction attempt; budget exhaustion leaves
the Issue refuted and its worktree retained.

## Isolation and integration

When `args.isolate` is true, each Implementer uses its own worktree and branch from `args.baseRef`; agents
in the round may run concurrently. The host harness waits for accepted deliveries and integrates branches
one at a time with `git merge --no-ff`. Run the declared gates after every merge. A failing merge gate stops
the Run rather than fixing forward.

Only a Critic-complete, gate-green and clean delivery may be integrated. Then, and only then, the
orchestrator calls `roadmap.py done <ref>` and commits the resulting authoritative projection. Refuted,
failed, parked and externally blocked Issues remain unticked.
