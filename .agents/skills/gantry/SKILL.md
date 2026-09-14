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
                         └→ spec.py --check → Requirement Critic → research → draft plan → critique
                            → STOP for operator approval
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
  Preflight also resolves `unitId` (`runlog.py unit-id --cwd <repoRoot> --json`) and a fresh `runId`, then
  queries `runlog.py inflight <unitId> --json`. Every match names an Issue still `ready-for-agent`, its
  phase and its preserved worktree; preflight offers the operator continuation there before doing anything
  else. `runlog.py inflight` reports only `run`, `issue`, `phase`, `worktree`, `repositoryRoot`,
  `policyHash`, `tier` and `staleAfterSeconds` — it does not report `correctionsSpent` or `branch`, so
  preflight derives them before building `args.priorRun` by invoking the shipped query
  `runlog.py corrections <unitId> <match.run> <match.issue> --json`, which reads the match's own Run log
  (`~/.gantry/state/<unitId>/runs/<match.run>.jsonl`, or `--state-root` when overridden) and returns
  `correctionsSpent` as the sum of two counts: (1) the `run.resumed.data.correctionsSpent` recorded in
  that same Run log, but only when that same `run.resumed` event's `data.issue` also equals `match.issue`
  — `0` when the log has no `run.resumed` event, or when its `run.resumed` names a different Issue, since
  the base is per-Issue and must never be lent to another Issue that happens to share the Run log; plus
  (2) the number of `refutation` events in that log whose `issue` equals `match.issue` and that are each
  followed, later in the log, by a `phase.started` event for `Implement` on that same Issue — i.e. only
  refutations whose correction pass actually started count toward the spent budget. Neither this
  derivation rule nor `correctionsSpent` itself is ever computed by prose or by test code: this shipped
  command is the single implementation, and it fails closed (`runlog error: no Run log for <runId>`,
  exit 1) when no Run log exists for the requested Run ID, rather than silently reporting `0`.
  `branch` is optional: when omitted, `reference/round-workflow.md` derives it itself from
  `common.issue_branch` and verifies it with `git branch --show-current` in the preserved worktree
  (see `implementationLocation`). Only explicit acceptance carries the derived match forward as
  `args.priorRun` (`run`, `worktree`, `issue`, `correctionsSpent`, `policyHash`, and `branch` when known)
  into `reference/round-workflow.md`, which appends `run.resumed` naming the prior Run and worktree
  instead of starting a fresh worktree, and resumes the spent correction count instead of resetting it.
  When the prior Run's `policyHash` differs from the effective policy resolved for this Run,
  `reference/round-workflow.md` appends `policy.changed` with the new hash so the drift is recorded
  before any Issue work resumes. The Run log is read only to offer that continuation and to derive
  `correctionsSpent`; it never decides readiness or completion — `frontier.py`, Issue `Status:` lines
  and `roadmap.py` do.
- `reference/round-workflow.md` appends every recorded-Run lifecycle event through `runlog.py append
  <unitId> <runId>` when the caller supplies both. A Run spans one or more rounds, each a separate
  invocation of this workflow sharing the same `runId`/`unitId`: only the first round (`args.isFirstRound`
  not explicitly `false`) appends `run.started` (with the repository root, a policy hash, the harness
  tier and the effective `staleAfterSeconds` in `data`) and, when resuming, `run.resumed` and
  `policy.changed`; every subsequent round of the same Run passes `args.isFirstRound = false` so these
  three events are never appended again — a Run log accepts only one `run.started` and rejects a
  duplicate. Every round, first or not, then appends `round.started`, one `phase.started` /
  `phase.finished` pair per Implement, Review and Critic phase, one
  `subagent.started` / `subagent.stopped` pair per fresh agent carrying its validated role result,
  `review.finding` after the Reviewer returns, `refutation` on every non-accepted Critic verdict,
  `issue.blocked` when the correction ceiling is spent without acceptance, `issue.done` on successful
  integration, `run.cancelled` on the first red post-merge gate, and `round.finished`. Only the last round
  of a Run (`args.isLastRound = true`) appends `run.finished`, once, after that round's `round.finished`.
  `issue.blocked` records only a Run-log fact: the Issue's `Status:` line stays `ready-for-agent` so
  `frontier.py` keeps offering it, and only `roadmap.py done` after Critic acceptance ever changes an
  Issue's authoritative status. Omitting `runId` or `unitId` disables recording entirely and leaves the
  round behaviorally identical, so a harness with no resolved Run log keeps working.
- Use `frontier.py --scope <scope> --json` as the only authority for dependency rounds. Exit 1 for a
  cyclic or dangling blocker graph. Parked `draft`, `blocked`, and `needs-operator` Issues are reported
  and skipped.
- Before slicing, `spec.py --check` validates the Spec's structure and then the read-only Requirement
  Critic (Critic model) assesses ambiguity, coherence, verifiability and non-goal coverage. A blocking
  finding stops the run, quotes the finding, and tells the operator to amend the Spec; the Critic never
  edits it. Neither structural validation nor Requirement Review approves planning — only explicit
  operator approval does.
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
  into `AGENTS.md`, `CONTEXT.md`, a template or policy on its own. Pass `args.isLastRound = true` and
  `args.learnerRunLogs` only for that final frontier round; `learnerRunLogs` is the current Run's own
  Run-log path(s), normally `~/.gantry/state/<unit-id>/runs/<run-id>.jsonl`.

## Harness-neutral execution

Use the host harness to ask the operator and spawn agents. Where native workflow scripts, structured
outputs, parallel agents or worktree isolation are available, use them. Otherwise execute the same
prompts from the reference files manually and validate their JSON-shaped results before advancing.
The deterministic scripts and workflow semantics stay identical in every harness.

## References

- `reference/plan-workflow.md` — structural validation, Requirement Critic, research, draft, plan
  critic and mandatory operator stop.
- `reference/round-workflow.md` — TDD implementation, two-axis review, adversarial Critic and serial
  integration contract.
- `templates/` — default Spec, PRD and Issue structures.
