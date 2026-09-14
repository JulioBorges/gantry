# Guard hooks and Claude Code wiring

Type: issue
Status: ready-for-agent
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
