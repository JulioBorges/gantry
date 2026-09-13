---
name: asdlc
description: Agentic SDLC workflow for a repository. Implements specs, waves or single issues in rounds of parallel subagents — deterministic frontier (Python) → research + plan when unplanned → TDD implementer → two-axis code review → adversarial critic that verifies every acceptance criterion and every project gate → roadmap update. Asks up front which model runs Plan, Implement, Review and Critic. Use for "implement spec X", "run wave 0", "execute spec#01", "rodar o ASDLC", "implementa as issues", "executa a onda".
argument-hint: <spec-slug | spec#NN | wave:N | frontier | all | "free-text goal"> [--limit N] [--budget N]
---

# ASDLC — Agentic Software Development Life Cycle

A short, repeatable loop that turns approved issues into verified, roadmap-tracked deliveries. Code owns the
rails (Python scripts decide *what* is ready and *whether* it is done); agents own the cognition (how to
build it, how to review it, how to refute it). The same principle Gantry itself is built on.

```
preflight (offer worktree) → ask models → frontier.py ──planned──▶ round loop: [ implement(TDD) → review → critic ] × issues
                                     └─unplanned─▶ research → plan → critique → STOP for operator approval
round done → integrate serially → roadmap.py done → commit → next round
```

## Roles and models

| Role | Runs | Model | Skill it invokes |
|---|---|---|---|
| Orchestrator | the harness's main agent, inline | session model | — |
| Planner | plan workflow: research + issue drafting | **Plan** model | — |
| Implementer | one per issue, per fix pass | **Implement** model | `tdd` |
| Reviewer | one per issue, Standards + Spec axes | **Review** model | `code-review` |
| Critic | adversarial, one per verification attempt | **Critic** model | runs `acceptance.py` + `gates.py` |

The models are asked once at the start and passed into every `agent()` call through `args.models`.

## Deterministic scripts (`scripts/`, Python 3, stdlib only)

| Script | Decides | Used by |
|---|---|---|
| `common.py` | resolves sparse pack policy with the optional repository `.gantry/config.json` overlay and keeps the Markdown issue parser | orchestrator, every workflow |
| `frontier.py --scope … --json` | which issues are in scope, their dependency rounds, cycles, parked and externally blocked issues | orchestrator, plan critic |
| `acceptance.py <ref> --json` | the authoritative acceptance-criteria list of an issue; `--check` exits 1 unless done and fully ticked | critic, orchestrator |
| `gates.py --run --diff-base <ref> --cwd <dir> --json` | detects and runs the repo's real gates (package scripts, pytest, Makefile, pre-commit), lists CI jobs and hooks, flags dirty tree and frontend changes | implementer, critic, orchestrator after integration |
| `roadmap.py done <ref>` | the only way an issue becomes done: ticks criteria, sets `Status: done`, regenerates ROADMAP.md (checkbox, per-spec and per-wave counts, Progress). `check` reports drift; `waves` regenerates the wave layout after a blocker change; `status` / `comment` edit the issue only | orchestrator |

Run them with `python3 <skillDir>/scripts/<name>.py`. `<skillDir>` is this skill's absolute directory
(`<repo>/.agents/skills/asdlc`; harness-specific folders such as `.claude/skills/asdlc` are symlinks to it).
Resolve it once in preflight and pass it in `args.skillDir`.

## Step 0 — Preflight (inline)

1. Parse the arguments: scope tokens, `--limit N` (max issues per round, default 4), `--budget N`
   (correction budget per issue, default `policy.budget.corrections`). Derive `<scope-slug>` from the scope tokens
   (`spec-slug`, `wave-0`, `spec-slug-01`, …).
2. Resolve `policy` with `common.resolve_policy(repoRoot)`, before creating a worktree, so its Git policy
   selects the target and branch prefix.
3. `git status --short && git branch --show-current`. A dirty tree must be committed or stashed by the user
   first — report and stop.
4. **Offer a dedicated worktree — always, before anything is created.** An ASDLC run takes a long time and
   commits continuously; if it runs in the user's checkout, the user cannot work on anything else meanwhile.
   Ask one single-select question (put it in the same message as the scope question if the scope is
   missing):

   > Run this ASDLC session in its own git worktree so you can keep working here in parallel?
   > - **Yes, dedicated worktree (Recommended)** — `../<repo>-asdlc-<scope-slug>` on branch
   >   `<policy.git.prefix><scope-slug>`, created from `<policy.git.target>`. Your current checkout is untouched.
   > - **No, run here** — creates/switches to `<policy.git.prefix><scope-slug>` in this checkout; you should not edit
   >   files here until the run ends.

   - **Yes** → create it (Claude Code: `EnterWorktree`; elsewhere
     `git worktree add ../<repo>-asdlc-<scope-slug> -b <policy.git.prefix><scope-slug> <policy.git.target> && cd` into it). From here
     on `repoRoot` is the worktree path: every script, every `agent()` and every commit runs there, and the
     repository artifacts and `ROADMAP.md` edits land on the run branch.
   - **No** → refuse to run on the target branch: create or switch to `<policy.git.prefix><scope-slug>` in the current checkout.

   If the current checkout already uses the configured branch prefix (resumed run), skip the question and continue
   there.
5. Render its artifact patterns for the current
   scope into `paths`: `specPath`, `issueDir`, `exemplarIssue`, `decisions`, `issueTracker`, `context` and `adrs`.
   `common.resolve_workflow_paths(repoRoot, scopeSlug)` renders the default policy and optional overlay. `policy`
   keeps the effective values; `paths` contains only the corresponding repository paths. Pass both to every
   workflow invocation — no workflow assumes an artifact location.
5. `python3 --version` (3.10+) and `python3 <skillDir>/scripts/roadmap.py check` inside `repoRoot`. Drift
   between the roadmap and the issues is fixed with the user before anything else runs.

## Step 1 — Ask the models

Ask the user four single-select questions in one message — `Plan`, `Implement`, `Review`, `Critic` — using
the harness's question tool if it has one (Claude Code: `AskUserQuestion`), otherwise a plain message and
wait for the reply. Options for each: `fable`, `opus`, `sonnet`, `haiku`, or any model id the harness
accepts (the user may type one).
Recommend `fable` for Critic and Plan, `opus` for Implement, `sonnet` for Review, and say why in the
descriptions (the critic's job is to refute, so it should be at least as strong as the implementer). Store
the answers as `models = { plan, implement, review, critic }`.

The scope, when missing from the arguments, is asked together with the worktree question in Step 0, so
this call only ever carries the four model questions.

## Step 2 — Resolve the scope deterministically

```
python3 <skillDir>/scripts/frontier.py --scope <token> [--scope <token>…] --limit <N> --json
```

- **Exit 1** — the graph has errors (cycle, dangling ref). Print them verbatim and stop. The breakdown was
  approved by the operator; per AGENTS.md you do not edit it silently. Propose the fix and wait.
- **`externally_blocked`** non-empty — list them; they are skipped this run, not failed.
- **`parked`** non-empty — issues already `blocked` / `needs-operator` / `draft`; list them, skip them.
- **Unplanned** — any of: the scope names a spec whose `issues/` directory is missing or empty; an
  in-scope issue has `criteria_total: 0`; the scope is free text `frontier.py` rejects. Go to Step 3 for
  that target, then come back here.
- Otherwise `rounds` is the plan. Continue to Step 4. With `wave:N` the plan is always exactly one
  round: `ROADMAP.md` waves are generated from the blocker graph so that wave N depends only on waves
  below N (`roadmap.py waves` regenerates them; `roadmap.py check` must be clean before starting).

## Step 3 — Unplanned work: research → plan → critique → stop

Run the plan workflow described in `reference/plan-workflow.md` with `args.models = { plan, critic }` (see
**Harness notes** for how to run it). It writes issue files in `Status: draft`, never touches `ROADMAP.md`,
and returns the critique.

Present the drafts, the critique and the proposed roadmap lines. **Stop here.** Changing the breakdown needs
operator approval (AGENTS.md). When approved, flip the issues to `ready-for-agent` with
`roadmap.py status <ref> ready-for-agent`, add the roadmap lines in the file's exact format, run
`roadmap.py check`, commit, and re-run Step 2.

## Step 4 — Round loop

For each round `k` in `rounds`:

1. `baseRef = git rev-parse HEAD` on the round branch. `isolate = round.length > 1`.
2. Run the round workflow described in `reference/round-workflow.md` (see **Harness notes**) with
   `args = { round: k, issues, models, branch, baseRef, isolate, correctionBudget, skillDir, repoRoot, policy, paths, date }`
   where `issues[i] = { ref, path, title, specPath }` comes from the `frontier.py` output and `date` is
   today's ISO date. Scale nothing down: every issue in the round runs its full chain.
3. Read the result. Per issue:
   - **`complete`** → if isolated, integrate serially: `git merge --no-ff <branch>` into the round branch,
     then `gates.py --run --diff-base <baseRef>` on the merged tree; a red gate after a merge means the
     merge — not the slice — is at fault: stop and report, do not "fix forward" inside the orchestrator.
     Conflicts: use the `resolving-merge-conflicts` skill; never resolve by discarding one side. After a green
     integration run `python3 <skillDir>/scripts/roadmap.py done <ref>`, then `git worktree remove <path>`
     if isolated, and commit the roadmap/issue change with a message naming the slice
     (`chore(roadmap): spec-slug#01 done`).
   - **`refuted`** → `roadmap.py status <ref> blocked` and `roadmap.py comment <ref> "<critic's top
     refutations + branch/worktree>"`. Keep the branch and worktree. The roadmap stays unticked.
   - **`implementer_failed` / `critic_failed`** → record it; do not retry inside the loop.
4. If every issue in the round is `complete`, continue to round `k+1` without asking. If any issue is
   refuted or failed, stop after this round and report: later rounds may depend on it, and the operator
   decides whether to continue, re-plan or split.
5. After the last round: `roadmap.py check` must be clean; `frontier.py --scope <same tokens>` shows what
   is left.

## Step 5 — Report

Lead with the outcome per issue (complete / refuted / skipped and why), then the operator decisions the
agents surfaced (`decisions`, `decisionsForOperator`, `openDecisions`), then gate results after
integration, then the next frontier. Quote the critic's evidence for anything marked done — the roadmap
checkbox must be traceable to it.

If the run used a dedicated worktree, end with how to bring the work back: the branch `<policy.git.prefix><scope-slug>`
and its worktree path, the command to open a pull request from it (or `git merge --no-ff` into `<policy.git.target>` if the
user prefers), and `git worktree remove <path>` once merged. Do not merge into `main` or remove the worktree
yourself — that is the user's call. Leave the worktree in place if anything was refuted: the blocked
issue's branch or worktree is referenced from its `## Comments` and the user may want to inspect it.

## Harness notes

The skill lives at `.agents/skills/asdlc/` so any harness can use it; only the orchestration mechanics differ.
The prompts, schemas, scripts and rules are the same everywhere.

| Need | Claude Code | Other harnesses (Codex, OpenCode, …) |
|---|---|---|
| Offer a dedicated worktree for the run | `AskUserQuestion`, then `EnterWorktree` (and `ExitWorktree` only if the user asks to leave it) | ask in a plain message; create the branch from the rendered `policy.git.prefix` and `policy.git.target`, then run everything from that directory |
| Ask the four models | `AskUserQuestion` | one message with the four questions; wait for the answer |
| Run a workflow template | `Workflow` tool with the JavaScript from `reference/*.md` passed inline and the `args` object | execute the same chain by hand: for each issue in the round spawn the harness's subagent for implementer → reviewer → critic using the prompt functions in the template as the prompt text, with `model` set per role. Run issues of one round concurrently if the harness supports it, otherwise sequentially; the order inside one issue never changes |
| Structured output | `schema` on `agent()` | ask the subagent to answer with a single JSON object matching the schema; re-ask once on invalid JSON |
| Worktree per implementer | `isolation: 'worktree'` | `git worktree add ../<repo>-<slug>-NN -b <policy.git.prefix><slug>-NN <baseRef>` before spawning; pass the path in the prompt |
| Invoke `tdd` / `code-review` | Skill tool | if the harness has the skill installed, invoke it; otherwise the prompts already carry the fallback ("run the same two-axis review yourself and say so"; red → green → refactor per behaviour) |

Everything deterministic — frontier, acceptance, gates, roadmap — is a Python script and needs nothing
from the harness beyond `python3` and `git`.

## Hard rules

- **Never tick the roadmap by hand.** Only `roadmap.py done`, only after `outcome === 'complete'`.
- **Fail closed.** Uncertain critic → not complete. `no_gates` → not complete unless the issue *is* the gates
  and the critic ran them. Dirty tree → not complete.
- **Never skip, weaken or delete a test to get green**, and never accept a delivery that did.
- **Correction budget is a ceiling, not a target.** When it is spent, the issue is blocked and the operator
  hears about it. Do not raise it silently.
- **Settled decisions stay settled.** Read them from the repository path passed in `args.paths.decisions`;
  an agent that reopens one has produced a blocking finding.
- **Breakdown changes need approval.** Splitting, merging or adding issues, and moving drafts to
  `ready-for-agent`, only after the operator says so.
- **Frontend changes need Playwright evidence** before they count (AGENTS.md).
- **One integration at a time.** Isolated branches merge serially with gates run between merges.
- **Never occupy the user's checkout without asking.** The dedicated-worktree offer in Step 0 is not
  optional; the user's main checkout stays free for parallel work unless they explicitly choose otherwise.
- **Artifacts are English**, issue comments included, regardless of the conversation language.
