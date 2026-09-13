---
name: gantry
description: Harness-neutral agentic SDLC workflow. Resolves ready Issues deterministically, plans only to operator approval, implements with TDD, reviews against standards and Spec, and accepts delivery only after adversarial verification.
argument-hint: <spec-slug | spec#NN | wave:N | frontier | all | "free-text goal"> [--limit N] [--budget N]
---

# Gantry

Gantry is a harness-neutral skill pack, not an execution engine. Workflow scripts decide readiness,
acceptance, gates and roadmap state; agents plan, implement, review and refute; the operator makes
approval decisions in the host harness.

```
preflight → models → frontier.py → planned round loop
                         └→ research → draft plan → critique → STOP for operator approval
round: implement (TDD) → review (standards + Spec) → Critic → serial integration → roadmap.py done
```

## Resolve the portable runtime

Before a Run, resolve these values once and pass them as `args` to every reference workflow:

1. `skillDir` is this `gantry` directory as an absolute real path. A harness-specific symlink resolves
   through `realpath`; never assume a fixed installation directory.
2. `repoRoot` is the enclosing Git repository or worktree (`common.repo_root()`).
3. `policy` is `common.resolve_policy(repoRoot)`: Gantry's sparse defaults overlaid by
   `<repoRoot>/.gantry/config.json` when present. A missing repository policy is valid.
4. `paths` comes from `common.resolve_workflow_paths(repoRoot, scopeSlug)`. Prompts receive paths, not
   repository-specific literals.

Run the standard-library workflow scripts as `python3 <skillDir>/scripts/<script>.py`. `common.py` provides
the shared Markdown parser and policy resolution; its `--json` path prints the resolved portable runtime.
Every script provides `--help`, and data-producing paths support `--json`.

## Workflow rules

- Preflight refuses a dirty worktree, offers a dedicated Run worktree before creating anything, resolves
  the effective policy, checks `roadmap.py check`, and asks models for Plan, Implement, Review and Critic.
- Use `frontier.py --scope <scope> --json` as the only authority for dependency rounds. Exit 1 for a
  cyclic or dangling blocker graph. Parked `draft`, `blocked`, and `needs-operator` Issues are reported
  and skipped.
- Planning creates draft Issues and never edits `ROADMAP.md`. Present drafts and the critic verdict, then
  stop. Only explicit operator approval permits `roadmap.py status <ref> ready-for-agent`, followed by
  `roadmap.py waves` and `roadmap.py check`.
- Each Issue follows `reference/round-workflow.md`: a fresh TDD implementer, a reviewer on both standards
  and Spec axes, one review fix pass, then a fresh adversarial Critic. The Critic alone can establish a
  complete delivery. Its refutation consumes at most the correction budget.
- A multi-Issue round uses one isolated worktree and branch per implementer. Integrate accepted branches
  serially, run gates after every merge, and stop on a failed integration gate. Create and identify each
  Issue branch through the `git.issueBranch` policy template (default
  `{prefix}{spec}-{number:02d}`), rendered by `common.issue_branch(policy, issue)`.
- Only after Critic acceptance, green gates and a clean worktree may the orchestrator run
  `roadmap.py done <ref>`. Never hand-edit Issue status, criteria checkboxes or the roadmap.
- At the end of a Run, execute `python3 <skillDir>/scripts/cleanup.py --plan --json` from the Run worktree
  and present its JSON output as the actual, read-only cleanup plan for the operator's authorization.
  Only after explicit Cleanup Authorization may the workflow pass that unchanged JSON to
  `cleanup.py --yes --plan-file <authorized-plan.json>`; it revalidates the plan against the repository
  state and refuses any divergence. The workflow never executes `cleanup.py --yes` automatically.
- After the last round, the optional Learner (`reference/round-workflow.md`) reads only the refutation
  and review-finding events already recorded in the Run log and drafts a lesson candidate for each
  problem that recurred across Issues or attempts. The final Run report lists every lesson candidate,
  with its evidence and proposed target, as an operator decision: the workflow never writes a candidate
  into `AGENTS.md`, `CONTEXT.md`, a template or policy on its own.

## Harness-neutral execution

Use the host harness to ask the operator and spawn agents. Where native workflow scripts, structured
outputs, parallel agents or worktree isolation are available, use them. Otherwise execute the same
prompts from the reference files manually and validate their JSON-shaped results before advancing.
The deterministic scripts and workflow semantics stay identical in every harness.

## References

- `reference/plan-workflow.md` — research, draft, plan critic and mandatory operator stop.
- `reference/round-workflow.md` — TDD implementation, two-axis review, adversarial Critic and serial
  integration contract.
- `templates/` — default Spec, PRD and Issue structures.
