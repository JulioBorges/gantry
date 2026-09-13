# Conversational repository setup

Type: issue
Status: ready-for-agent
Slice: `gantry-migration#10`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

Create `.agents/skills/gantry-setup/SKILL.md` as the sole conversational writer of repository policy and its marked `AGENTS.md` section. It presents each artifact, template, check, Git, and hook decision with benefit, trade-off, default, and confirmation; renders the full proposed `.gantry/config.json` before writing; supports merge, overwrite, and abort for an existing policy; preserves pack defaults when skipped. Implement idempotent merging of the shipped Claude Code hook fragment into `.claude/settings.json` and write only the `<!-- gantry:begin -->` through `<!-- gantry:end -->` region in `AGENTS.md`.

## Acceptance criteria

- [ ] A setup transcript test proves `.gantry/config.json` is shown in full and is not written before confirmation, and an existing policy offers merge, overwrite, or abort with the chosen outcome observable on disk.
- [ ] Running accepted setup twice produces byte-identical `.claude/settings.json`, preserves every unrelated key byte for byte, and installs the `hooks/claude-code.settings.json` entries exactly once.
- [ ] Setup adds or replaces only the marked Gantry section in `AGENTS.md`; a byte-comparison test proves all content outside `<!-- gantry:begin -->` and `<!-- gantry:end -->` is unchanged.
- [ ] The skill reads capability declarations to offer only supported hook choices, enables recording by default, asks before denial hooks, and creates no engine, database, MCP service, or automatic cleanup.
- [ ] The Spec Changelog receives an English entry in the same merge, and setup-generated policy, prompts, and marked content are English.

## Blocked by

- `gantry-migration#09` — consumes the shipped hook fragments and capability-aware guard contract.

## Comments
