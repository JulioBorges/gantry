# Guard hooks and Claude Code wiring

Type: issue
Status: blocked
Slice: `gantry-migration#09`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Add `.agents/skills/gantry/scripts/guard.py`, `.agents/skills/gantry/hooks/claude-code.settings.json`, `.agents/skills/gantry/hooks/opencode.plugin.js`, and `.agents/skills/gantry/hooks/codex.hooks.json`. Implement Claude Code payload handling for allow, deny, and context decisions; wire each hook entry to invoke `guard.py <event>` with stdin payload. Deny edits to `ROADMAP.md`, Issue `Status:` lines, and Issue criteria checkboxes outside the roadmap script; deny force pushes and test-skip commits; record hook and subagent events through the Run log. Unknown payload shapes must degrade to recording, never grant workflow authority.

## Acceptance criteria

- [ ] A Claude Code `PreToolUse` payload for editing `ROADMAP.md` or an Issue `Status:` line returns one denial line naming its rule and refused path, logs `hook.denied`, and a `Read` payload returns allow.
- [ ] A Claude Code `PreToolUse` payload changing an Issue acceptance-criteria checkbox returns one denial line naming its rule and refused path, and appends a `hook.denied` event for that edit.
- [ ] A `SubagentStop` payload appends `subagent.stopped`; malformed or capability-incomplete payloads produce a recorded degradation rather than a false completion or a denial without enough fields.
- [ ] Tests prove `git push --force` and committed test-skip patterns are denied, while `guard.py` answers a 1 MB payload in under 200 ms and all hook entries invoke the script with their event and stdin payload.
- [ ] The guard implementation only protects and records: status and checkbox authority stays with `roadmap.py`, and the no-hooks workflow prompts still state and Critic-check every protected rule.
- [ ] The Spec Changelog receives an English entry in the same merge, and `guard.py` passes the standard-library-only import test and its runnable test command.

## Blocked by

- `gantry-migration#08` — consumes the append-only Run log event contract.
- `gantry-migration#05` — consumes harness capability fields and support tiers.

## Comments
- 2026-09-13 — ASDLC round 1 critic refuted after 2/2 correction budget spent. Top refutations: (1) Spec/code drift — guard.py:348 emits hook.degraded but spec.md:25 Blueprint event list omits it (only mentioned in Changelog); (2) undecodable/non-object stdin with a resolvable Run ID (--run-id or GANTRY_RUN_ID) records nothing, contradicting the criterion that malformed payloads produce a recorded degradation. Branch: worktree-wf_8d1cbc1a-f67-2, worktree: /Users/julioborges/src/personal/gantry/.claude/worktrees/wf_8d1cbc1a-f67-2 (kept for operator inspection).
- 2026-09-13 — ASDLC retry round 2: critic refuted again after 2/2 correction budget spent. Remaining gaps: (1) perf constraint violated on the Bash/git-commit decision path — 1MB payload takes ~236ms-8s (limit 200ms) because commit_uses_all_flag()/extract_git_add_targets() run shlex.split over the whole matched segment; (2) ROADMAP protection is bypassable on case-insensitive filesystems (macOS/Windows) — guard.py:403 compares the basename case-sensitively, so roadmap.md/Roadmap.md payloads are allowed and unlogged. Branch: worktree-wf_8d1cbc1a-f67-2, worktree: /Users/julioborges/src/personal/gantry/.claude/worktrees/wf_8d1cbc1a-f67-2 (kept for operator inspection).
- 2026-09-14 — ASDLC round 3 (2026-09-14): refuted a third time after the 2/2 correction budget was spent (corrections 23b96de, d344f14). Critic verdict at d344f14: AC1-3, AC5-6 met; AC4 NOT met. (1) PERF: spec.md:36 200 ms constraint violated — 1 MB Bash payloads 'git commit -m "<1 MB of git tokens>"' (with/without -a) and a heredoc single 1 MB line of 'git ' tokens all exceeded a 60 s timeout; cause GIT_ADD_SEGMENT_RE (guard.py:99) retried from every 'git' occurrence via extract_git_add_targets (guard.py:370, called :519) — the same quadratic pattern 23b96de removed for push/commit but left for add; isolated 25KB=488ms, 50KB=2028ms, 100KB=7780ms. (2) SECURITY, test-skip bypass: quoted separators in -m cut the segment before the trailing -a (COMMIT_SEGMENT_RE :98, COMMAND_SEGMENT_SPLIT_RE :94): 'git commit -m "fix; cleanup" -a', -m 'a|b' -a, -m 'a & b' -a, -m 'l1\nl2' -a all ALLOW with an unstaged @unittest.skip and the skip really lands in HEAD. (3) test-skip bypass via pathspec/include: 'git commit -m x app_test.py', '-- app_test.py', '-i/--include/-o app_test.py' commit the worktree version unstaged — ALLOW. (4) 'git stage f && git commit' ALLOW (stage == add). (5) force-push bypass: combined short flags -uf/-fu/-qf (FORCE_FLAG_RE :85 needs -f\b), quoted refspecs '+main:main' / "+main" (FORCE_REFSPEC_RE :86 needs whitespace before +), and --mirror — all proven '(forced update)' against a diverged bare remote. (6) token-literal bypasses: git 'push' --force, git 'commit', /usr/bin/git ..., git -c k=v push --force, sh -c 'git push --force'. REQUIRED FIXES (critic, ordered): a) delete GIT_ADD_SEGMENT_RE/COMMIT_SEGMENT_RE, walk _bounded_tokens once per segment; b) tokenise the whole Bash command with shlex.shlex(punctuation_chars=True, whitespace_split=True) and split on separator tokens only; c) treat -i/--include/-o/--only, '--', or non-flag pathspecs after commit as worktree commits -> tracked_worktree_skip_match; accept 'stage' as 'add'; d) replace FORCE_* regexes with a token check on the push segment (--force, --force-with-lease[=x], --force-if-includes, --mirror, ^-[A-Za-z]*f[A-Za-z]*$, token starting with '+'); e) match program by Path(token).name == 'git'; Write-branch Status/checkbox compare for existing Issues; f) perf tests with 1 MB 'git ' token payloads <0.2 s; Changelog entry. OPERATOR DECISIONS (critic): regex/whitespace parsing of Bash is NOT a defensible enforcement boundary — every round closed one shape and opened another; recommend full shlex tokenisation PLUS git-side pre-commit (index/worktree diff scan) and pre-push (reject non-FF and '+' refspecs) hooks, OR narrow the spec guarantee to best-effort detection of listed shapes. Also: Bash-level writes to ROADMAP.md/Issue files (sed -i, echo >>) are unguarded and roadmap.py itself runs via Bash — decide scope/exemption; decide whether guard.py should carry a 200 ms time budget failing open with hook.degraded; decide whether 'git push --delete' is a protected rewrite. Branch worktree-wf_8d1cbc1a-f67-2, worktree /Users/julioborges/src/personal/gantry/.claude/worktrees/wf_8d1cbc1a-f67-2 (clean at d344f14, 166 tests green) kept for inspection. Do not retry blindly: the critic's design question needs an operator answer first.
