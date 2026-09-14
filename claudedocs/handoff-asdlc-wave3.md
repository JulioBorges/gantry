# ASDLC wave:3 (gantry-migration) — closeout

Updated 2026-09-14. The round-3 retry described in earlier versions of this file has finished; nothing
is in flight. Authoritative state lives in `ROADMAP.md` and each Issue's `## Comments` — this note only
points at it.

## Outcome

| Issue | Result | Where |
|---|---|---|
| `#04` `#11` `#13` `#16` | done (round 1–2) | merged into `main` at `6cbeecb` |
| `#14` Resumable and recorded round execution | **done (round 3)** | merged into `main` at `2b128fd`; roadmap `929a5d3` |
| `#09` Guard hooks and Claude Code wiring | **blocked** after 3 refutations | branch `worktree-wf_8d1cbc1a-f67-2`, worktree `.claude/worktrees/wf_8d1cbc1a-f67-2` @ `d344f14` (clean, 166 tests green) |

`roadmap.py check` is clean (13/18; wave 3 at 5/6). `frontier.py --scope wave:3` returns no runnable
work — only `#09` parked.

## `#09` — decision taken, implementation to be pulled in a new session

The round-3 critic (full text in the Issue's Comments, commit `3064fae`) proved the guard's regex-based
Bash parsing is both quadratic on 1 MB payloads and bypassable through quoting, pathspecs, combined short
flags, quoted refspecs, `--mirror`, token literals and absolute `git` paths. The operator ruled on
2026-09-14: enforcement of no-force-push / no-test-skip-commit moves to the repository's own git hooks —
**`docs/adr/0005-git-hooks-enforce-git-rules.md`**. `#09`'s *What to build* and AC4 were amended to match
(operator-approved breakdown change); the spec's *Hook wiring* bullet names the new `hooks/git/` layer.
`#09` stays `blocked` until the next run flips it to `ready-for-agent`.

To pull it: `roadmap.py status gantry-migration#09 ready-for-agent`, then run the round on the preserved
worktree `.claude/worktrees/wf_8d1cbc1a-f67-2` (branch `worktree-wf_8d1cbc1a-f67-2`, HEAD `d344f14`, clean,
166 tests green) — merge `main` into it first so ADR-0005 and the amendment are present. The implementer
must add `hooks/git/pre-commit` + `pre-push`, delete guard.py's Bash-parsing machinery (segment/force
regexes, `_bounded_tokens`, `commit_uses_all_flag`, `extract_git_add_targets`, `tracked_worktree_skip_match`
and their tests) in favour of the single linear substring rule, keep Edit/Write/MultiEdit protection and
`hook.degraded` handling, and prove the hooks in temporary git repos with `core.hooksPath` set by the test.
Writing `core.hooksPath` into the operator's repository belongs to `#10`; its hook criteria should gain that
line — a breakdown change that still needs operator approval and was deliberately not made here.

## Not done regardless

- `main` has not been pushed to `origin/main` (~35 commits ahead). Ask the operator before pushing.
- `#14`'s critic left five non-blocking design observations in its `decisionsForOperator` (Learner
  running after `run.cancelled`; a `learn#00` card appearing on the dashboard; `runlog.py corrections`
  extending #08's script from #14; no committed test for the skipped-Learner negative case; `runlog.py`
  accepting events after a terminal one). None blocks `#14`; each is a candidate follow-up or spec
  amendment.
