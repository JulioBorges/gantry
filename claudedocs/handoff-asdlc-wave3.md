# Handoff — ASDLC wave:3 (gantry-migration), round 3 in flight

Written 2026-09-14 because the operator needs to shut down the machine mid-run. The background
Workflow task (`wi95brm9r` / run `wf_ab1494ca-00b`) is a **local** process and will die with the
shutdown — its `resumeFromRunId` only works inside the same Claude Code session, so a new session
cannot resume it directly. This file has everything needed to pick the work back up by hand.

## What's already merged into `main` (safe, done, nothing to do)

`gantry-migration#04`, `#11`, `#13`, `#16` are `done` in ROADMAP.md and merged into `main` at commit
`6cbeecb` (`merge: integrate ASDLC wave 3 (gantry-migration#04, #11, #13, #16)`). Old merged
issue branches/worktrees (#03/#05/#06/#07/#08/#12 and the round-1/2 done branches) were already
cleaned up via `.agents/skills/gantry/scripts/cleanup.py`. `main` is 27+ commits ahead of
`origin/main` — **nothing has been pushed to the remote**.

## What's in flight right now: `#09` and `#14`, round 3 of retries

Both issues have been refuted twice already (round 1 and a round-2 retry both spent their full
2-correction budget). A round-3 retry was launched continuing in the SAME preserved worktrees,
after merging current `main` into each to pick up #04/#11/#13/#16 and resolving the resulting
conflicts by hand (mostly additive `.scratch/gantry-migration/spec.md` Changelog entries — union,
never drop content — plus one real logic conflict in
`.agents/skills/gantry/reference/round-workflow.md` between #14's `run.finished` gating and #13's
Learner `isLastRound` gating, resolved by gating both under the same `A.isLastRound` flag).

Both issues are currently `Status: ready-for-agent` in
`.scratch/gantry-migration/issues/09-guard-hooks-and-claude-wiring.md` and
`.scratch/gantry-migration/issues/14-resumable-round-execution.md` (reopened on `main` at commit
`d077811`).

### Worktrees (git-safe — check these first, they will NOT have been corrupted by the shutdown)

| Issue | Worktree path | Branch | Base ref for gates/critic |
|---|---|---|---|
| `gantry-migration#09` | `/Users/julioborges/src/personal/gantry/.claude/worktrees/wf_8d1cbc1a-f67-2` | `worktree-wf_8d1cbc1a-f67-2` | `6cbeecb46f60fe8a033f4d99fb1f0d94b4ad4d53` (= current `main`) |
| `gantry-migration#14` | `/Users/julioborges/src/personal/gantry/.claude/worktrees/wf_b0e31a60-8d6-1` | `worktree-wf_b0e31a60-8d6-1` | `6cbeecb46f60fe8a033f4d99fb1f0d94b4ad4d53` (= current `main`) |

As of the last check before shutdown, both worktrees were clean (`git status --porcelain` empty)
with these commits already made **during round 3** (these survive the shutdown — they're real git
objects):

- `#09` (`worktree-wf_8d1cbc1a-f67-2`): `c9a5013` fix(gantry): case-insensitive ROADMAP guard, bound
  commit-segment tokenising; `23b96de` fix(gantry): make guard.py Bash push/commit gating linear-time.
- `#14` (`worktree-wf_b0e31a60-8d6-1`): `d436eda` fix(gantry): gate run.started on
  args.isFirstRound so multi-round Runs record once; `6803c06` fix(gantry): project the recorded
  Critic verdict before appending it.

**What was interrupted:** for both issues, the round-3 critic's first verification attempt (`#1`)
had already come back `complete: false` (refuted), the implementer made one correction pass (the
second commit in each list above), and the critic's **second and final** verification attempt (the
last one allowed under the 2-correction budget) was still running when the machine was shut down.
So: the fix work for round 3 is committed and real, but it has **not yet been independently
verified**. Treat both issues as unverified, not as failed — the prior critic findings that
triggered this round were:

- `#09`: (1) a 1MB Bash/`git commit` payload took 236ms–8s to decide (limit 200ms) because
  `commit_uses_all_flag()`/`extract_git_add_targets()` ran `shlex.split` over the whole matched
  segment; (2) ROADMAP protection was bypassable on case-insensitive filesystems (basename compared
  case-sensitively).
- `#14`: (1) branch didn't cleanly integrate with the Learner's (`#13`) return shape in
  `round-workflow.md` (now resolved by the orchestrator's merge); (2) `run.started`/`run.finished`
  fired on every round instead of once per Run across multiple rounds; (3) a Changelog claim that
  `#16`'s fixture tree was "merged" was false at the time (also now true after the real merge).

## How to resume in a new session

1. `cd /Users/julioborges/src/personal/gantry && git status --short` — confirm main is clean and at
   `d077811` (or later, if you already touched it).
2. For each of the two worktrees above: `git -C <path> status --short` and `git -C <path> log
   --oneline -5` to confirm they're still clean and show the commits listed above (nothing lost).
3. Re-run the verification that got interrupted — either:
   - **Cheapest**: manually run, in each worktree, exactly what the critic prompt would have run:
     `python3 .agents/skills/asdlc/scripts/acceptance.py <repo>/<issue-path> --json`, then
     `python3 .agents/skills/asdlc/scripts/gates.py --run --diff-base
     6cbeecb46f60fe8a033f4d99fb1f0d94b4ad4d53 --cwd "$(pwd)" --json`, then judge each acceptance
     criterion against the current code/tests yourself (or with a fresh `Agent` call using the
     `criticPrompt` shape from the round-3 script — see below).
   - **Full re-run**: launch a fresh Workflow (a "round 4") using the same two-stage pattern as
     round 3 (implement-with-feedback → review → critic loop), but since both issues already have a
     correction committed, you can start straight at the critic stage instead of implement, to avoid
     burning correction budget on work that's already done. If the critic refutes again, you have a
     literal correction-budget question for the operator: this is the 3rd retry, each with its own
     2-correction budget already spent — consider whether to keep retrying or escalate to a human fix.
4. The exact round-3 script (implement/review/critic prompts, schemas) is saved at:
   `/Users/julioborges/.claude/projects/-Users-julioborges-src-personal-gantry/e5fbc431-4342-4b19-a383-5daf1d1fd24e/workflows/scripts/asdlc-retry-round-3-wf_ab1494ca-00b.js`
   — read it to reuse the exact prompts/schemas if launching a new Workflow by hand (the `resumeFromRunId` itself won't work in a new session, but the script file survives on disk and can be passed via `scriptPath` with a **new** run, i.e. omit `resumeFromRunId` or expect a full re-run of all agents).
5. Once a `complete` verdict is obtained for an issue, integrate exactly like every prior round:
   `git checkout main`, `git merge --no-ff <worktree-branch>` (resolve the additive
   `.scratch/gantry-migration/spec.md` Changelog conflict the same way — union both sides), run
   gates on `main`, `python3 .agents/skills/asdlc/scripts/roadmap.py done <ref>`,
   `git worktree remove <path> --force`, commit.
6. If refuted again, mark `blocked` via `roadmap.py status <ref> blocked` +
   `roadmap.py comment <ref> "..."`, keep the branch/worktree, and **ask the operator** before
   attempting a 4th retry — this is already the 3rd consecutive refutation for both issues, which is
   a signal worth surfacing rather than silently looping.

## Final state check (run this first in the new session to see if anything changed)

```
python3 .agents/skills/asdlc/scripts/roadmap.py check
python3 .agents/skills/asdlc/scripts/frontier.py --scope wave:3 --json
```

## Not done yet regardless of #09/#14's outcome

- `main` has not been pushed to `origin/main`. Ask the operator before pushing (branch-protection /
  PR conventions may apply — check `git-flow-woba` skill guidance if working under Woba's policy,
  though this repo's own `AGENTS.md`/ASDLC conventions govern here).
