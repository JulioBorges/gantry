# Retire ASDLC after canonical proof

Type: issue
Status: ready-for-agent
Slice: `gantry-migration#18`
Spec: `.scratch/gantry-migration/spec.md`
Created: 2026-09-13

## Parent

`gantry-migration`

## What to build

After the canonical pack has passed the Claude Code reference-tier proof, remove `.agents/skills/asdlc/` and replace the existing harness skill links under `.claude/skills`, `.cursor/skills`, `.opencode/skills`, and `.gemini/skills` so they resolve to `.agents/skills/gantry`, `.agents/skills/gantry-setup`, and `.agents/skills/gantry-dashboard`. Remove migration-only references to `asdlc` while preserving the canonical pack, policy defaults, Issue parser compatibility, and all workflow guarantees.

## Acceptance criteria

- [ ] `.agents/skills/asdlc/` no longer exists, each of `.agents/skills/gantry/`, `.agents/skills/gantry-setup/`, and `.agents/skills/gantry-dashboard/` contains accepted `SKILL.md` frontmatter, and `ls .claude/skills .cursor/skills .opencode/skills .gemini/skills` lists all three resolving skill directories.
- [ ] `grep -r "gantry-v4\|slice-index\|the Gantry repository" .agents/skills/gantry*` returns no matches, and a no-policy smoke test runs the canonical workflow’s portable policy/default path on this repository.
- [ ] The final fixture proof and feature-owner test suites pass after removal, including roadmap authority, unchanged legacy Issue parsing, no-hooks semantics, serialized integration, and the offered draft-pull-request behavior.
- [ ] The Spec Changelog receives an English entry in the same merge, and the final migration report explicitly confirms no engine, database, MCP service, auto-cleanup, auto-merge, or auto-lesson injection was introduced.

## Blocked by

- `gantry-migration#17` — retires the legacy skill only after the canonical pack is proven in the reference tier.

## Comments
