# Spec: Invoke Gantry Runs from a repository command

Type: spec
Status: approved
Map: `ROADMAP.md` (spec 21)
Source: Operator-approved design from the 2026-10-17 grilling conversation
Created: 2026-10-17
Planning: Behavior confirmed; testing seam and six-Issue breakdown approved for publication by the operator on 2026-10-17

## Blueprint

### Context

Gantry executes a Run through a skill inside an agent. The operator opens that agent, invokes the skill, and types the request. The gantry-harness needs to load a repository that already has the pack, show Issues and Specs, and conduct the Run by calling a command, stopping for a person only when the command asks. The pack has deterministic scripts and role configuration, and no `gantry` command that reserves an Issue, opens its worktree, calls each role, and publishes the closing commit.

### Architecture

The pack exposes `gantry` as an executable inside the consumer repository. It reads Issues, Specs and the frontier. `execute` walks one Run in that Issue's worktree. A separate approval command writes the closing commit, pushes, and opens the pull request. The harness, or a person at a terminal, is the parent process: it reads one JSON object per line and writes the answer on that process's stdin.

Each role's harness and model come from `execution.roles`. Project policy overrides the global policy. `execute` opens the named harness without a window. The test seam is that command, replaced by a double. The card phase and the Run record stay outside the repository.

### Constraints

- One Run is one Issue. Parallel Runs use separate worktrees.
- A Spec is not executable. A Spec with no Issue receives exactly one Issue during plan.
- Plan and implement create micro commits and do not push. Review and Critic read the branch diff against `git.target`.
- Review and Critic share `budget.corrections`. A dirty plan tree does not spend a correction.
- The approval command is the only push. The target stays unchanged until the pull request merges.
- Python standard library only. No engine, database, or global binary.

## Problem Statement

An operator who wants the harness to run Gantry still has to open an agent and type the skill request. The repository command that would validate setup, isolate the Issue, call each role, and publish one pull request does not exist.

## Solution

`gantry` in the installed pack becomes the command the harness invokes. It reports the board, executes one Issue through its roles, and approves a finished Run by opening a pull request whose last new commit already marks the Issue and the roadmap done.

## User Stories

1. As an operator, I want to list Issues, so that I can choose what to execute.
2. As an operator, I want to list Specs, so that I can read the supporting document for an Issue.
3. As an operator, I want to see which Issues the frontier blocks, so that I do not start a Run the frontier refuses.
4. As an operator, I want to execute an Issue that already has a Spec, so that implement, checks, review and Critic run without a chat.
5. As an operator, I want setup validated before a branch exists, so that a setup failure leaves no branch and no worktree.
6. As an operator, I want an Issue with an open blocker refused, so that the Run does not start outside the frontier.
7. As an operator, I want one worktree per Run, so that several Issues can proceed without mixing files.
8. As an operator, I want micro commits from plan and implement, so that review and Critic read the diff against the target.
9. As an operator, I want review and Critic to end with pass or fail, so that execute can advance or repeat.
10. As an operator, I want a review fail to skip Critic, so that the correction returns to implement.
11. As an operator, I want a Critic fail to run review and Critic again after implement, so that both roles see the correction.
12. As an operator, I want project checks between implement and review, so that a red check does not spend a review role.
13. As an operator, I want a red check and a dirty implement tree to spend the same correction budget, so that one limit covers both.
14. As an operator, I want a pause when the budget is zero, so that I can grant one more correction or stop without merging.
15. As an operator, I want stop-without-merge to keep the worktree, so that I can resume the unfinished role.
16. As an operator, I want resume at zero budget to reopen the pause, so that implement does not run unseen.
17. As an operator, I want to discard an interrupted Run, so that its local worktree and branch are removed.
18. As an operator, I want to plan work that has no Spec and no Issue, so that execute reserves the slug and number and creates the branch under the Issue name.
19. As an operator, I want to approve the plan in the same worktree, so that implementation continues without another pull request.
20. As an operator, I want to reject the plan, so that the worktree and branch disappear and no card remains.
21. As an operator, I want a Spec or Issue delta during plan to be committed before approval, so that the pause does not happen on a dirty tree.
22. As an operator, I want a plan that stays dirty after one retry to pause, so that I can retry or reject without spending a correction.
23. As an operator, I want execute to finish when review and Critic pass, so that approval is a separate command.
24. As an operator, I want approval to record the Issue and roadmap as done, push, and open the pull request, so that a second pull request is not required for the roadmap.
25. As an operator, I want a repeated approval, when that closing commit is already on the branch, only to open the pull request, so that the commit is not duplicated.
26. As an operator, I want the Issue to be done on the target only after the pull request merges, so that opening the pull request does not mark it done.
27. As a harness, I want to be the parent of execute, so that I can show a pause and return the answer on the same stdin.
28. As a harness, I want each role's harness and model to come from configuration, so that execute opens that role headlessly.
29. As an operator in another agent, I want the pack to remain in the repository, so that I can use Gantry without the gantry-harness.

## Implementation Decisions

- `gantry` is the pack executable inside the consumer repository. There is no global install.
- Project `execution.roles` overrides the global map. Each role names a harness and a model. Execute opens that harness without a window.
- A Run targets one Issue. The branch is created with its final name from `git.issueBranch` and `git.target`.
- Plan runs only when the Spec and Issue are absent. Execute reserves the supplied slug and the next free number before the agent writes. The agent uses those paths and does not choose another number.
- Execute order is setup, worktree, plan when required, implement, checks, review, Critic. Review and Critic share `budget.corrections`.
- Plan and implement record micro commits and do not push. A role finishes only with a clean worktree. Review and Critic receive the diff of the branch against the target.
- A dirty plan tree returns to plan and does not spend a correction. A second return that is still dirty pauses: try again or reject. Reject deletes the worktree and branch.
- A dirty implement tree, a failed check, and a review or Critic fail spend one correction and return to implement. A review fail does not call Critic. A Critic fail runs review and Critic again.
- At zero budget, execute pauses. Continue grants one more correction for that Run only. Stop does not merge.
- Execute exits when review and Critic pass, without pushing. Approval is another command in the same worktree. Without the closing commit, it marks the Issue and roadmap done, pushes, and opens the pull request. With that commit already on the branch, it only opens the pull request.
- Card phase and the Run record stay outside the repository. The command reports the result. The parent shows ready to agent, interrupted, or ready for approval.
- The test seam is the `gantry` process against a temporary Git repository. The role harness is a configured command the test replaces.

## Testing Decisions

- A good test observes the process from the outside: exit code, JSON, branch, worktree, commits, and the absence of a push.
- The test does not open Antigravity, Claude Code, Codex, or Cursor. The role command is a double that commits, dirties the tree, or returns pass, fail, or a request for input.
- The same double covers the happy path, corrections, plan, and approval.
- The diff base is the fixture's configured target, not a branch name hardcoded through the tests.
- Existing temporary-repository subprocess tests are the prior art.

## Contract

### Definition of Done

- [ ] `gantry` lists Issues, Specs and frontier blockers from a fixture repository without creating a branch.
- [ ] `gantry execute` takes an existing Issue through setup, an isolated worktree, micro commits, checks, review and Critic, and exits ready without pushing.
- [ ] Failures spend `budget.corrections` as specified and pause on stdin when the budget is zero.
- [ ] Plan reserves the Issue on the execution branch, pauses for approval, and deletes that branch on rejection.
- [ ] The approval command publishes the closing commit and opens the pull request, and a repeat only opens the pull request.
- [ ] An interrupted Run resumes in the same worktree or is discarded, and a ready Run does not call an agent again.

### Regression Guardrails

- The pack remains a skill pack installed in the consumer repository.
- Role configuration in project policy still overrides the global map.
- Antigravity hook installation and the Claude Code events other than the skipped project `PreToolUse` stay as they are.
- Review and Critic do not choose the next role. Execute does.

### Scenarios

```gherkin
Scenario: an existing Issue finishes review without a push
  Given a repository whose Issue has a Spec and no open blocker
  When gantry execute runs that Issue with a role double that commits and passes
  Then the worktree exists on the Issue branch
  And the branch has micro commits
  And origin was not pushed
  And the process exits ready for approval
```

```gherkin
Scenario: a zero budget pauses instead of calling implement
  Given a Run whose correction budget is zero after a review fail
  When the operator resumes it
  Then the process emits a pause
  And implement is not called until the operator grants one more correction
```

```gherkin
Scenario: approval does not duplicate the closing commit
  Given a branch that already contains the Issue and roadmap closing commit
  When the approval command runs
  Then no new commit is created
  And a pull request is opened against the target
```

## Out of Scope

- The harness screen, card phases, and watching a pull request after it is opened.
- Deleting the local worktree and branch after the pull request merges. The harness observes the merge.
- Installing the pack outside the consumer repository.
- Requiring Claude Code or Codex in order to run the command.
- A second pull request whose only change is the roadmap.

## Further Notes

- The initial card phase is ready to agent. That phase lives in the harness, not in the Issue file.
- A pull request closed without a merge does not mark the Issue done. Reopening it repeats approval.
- The harness product requirements live in the gantry-harness repository, not in this Spec.

## Changelog

- 2026-10-17 — Operator approved the behavior, the single CLI test seam, and the six-Issue breakdown.
