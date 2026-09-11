# Isolate PBI implementation and serialize integration

Each active PBI uses a dedicated Git worktree and branch so parallel builders do not share a working directory. Gantry serializes merges per repository and validates each merge candidate against the current target, invalidating authorization whenever the candidate or target changes. This preserves parallel implementation while avoiding shared-checkout interference and stale approvals, at the cost of worktree lifecycle management and repeated validation as the target advances.
