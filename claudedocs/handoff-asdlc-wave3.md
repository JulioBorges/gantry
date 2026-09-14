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

## `#09` needs an operator decision before any retry

The round-3 critic (full text in the Issue's Comments, commit `3064fae`) proved the guard's regex-based
Bash parsing is both quadratic on 1 MB payloads and bypassable through quoting, pathspecs, combined short
flags, quoted refspecs, `--mirror`, token literals and absolute `git` paths, and concluded that
regex/whitespace parsing of shell is not a defensible enforcement boundary. It recommends either full
`shlex` tokenisation plus git-side `pre-commit`/`pre-push` hooks, or narrowing the spec guarantee to
best-effort detection of listed shapes. Decide that first; a fourth blind retry would repeat the pattern.

## Not done regardless

- `main` has not been pushed to `origin/main` (~35 commits ahead). Ask the operator before pushing.
- `#14`'s critic left five non-blocking design observations in its `decisionsForOperator` (Learner
  running after `run.cancelled`; a `learn#00` card appearing on the dashboard; `runlog.py corrections`
  extending #08's script from #14; no committed test for the skipped-Learner negative case; `runlog.py`
  accepting events after a terminal one). None blocks `#14`; each is a candidate follow-up or spec
  amendment.
