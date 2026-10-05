# Operator harness preferences live in a machine profile outside tracked policy

ADR-0004 established three deterministic homes: skills under `.agents/skills/`, sparse tracked `.gantry/config.json` written only by setup, and observational Run state under `~/.gantry/state/<repository-execution-unit>/`. ADR-0006 versioned role defaults in tracked repository policy. When different operators collaborate on the same repository, however, each operator often works in a different host harness (Antigravity, Claude Code, Codex, or OpenCode). Storing `execution.hostHarness` in tracked repository policy caused Git diff churn and forced one operator's harness choice onto all collaborators.

We establish a fourth home: machine-local operator profiles at `~/.gantry/profiles/<unit-id>/execution.json`, keyed by the repository execution-unit id (`runlog.unit_id`).

## Consequences

- Machine-local operator profiles live at `~/.gantry/profiles/<unit-id>/execution.json`.
- The profile contains only operator `hostHarness` and optional `roles` overlays (with `harness`, `model`, and optional `effort`). Credentials, tokens, transcripts, commands, outputs, and environment variables are strictly forbidden from profiles.
- Host Harness resolution order: explicit `--host` outranks the profile `hostHarness`, which outranks a legacy tracked `execution.hostHarness`.
- Role resolution order: Issue-role override, Run-role override, operator profile overlay, repository role default (`policy["execution"]["roles"]`), then confirmed environment default.
- Personal switches (`setup.py --personal`) write only the machine profile and leave tracked `.gantry/config.json`, adapter files, and `AGENTS.md` byte-for-byte unchanged.
- Shared setup against an ignored `.gantry/config.json` continues to refuse setup with the tracked-policy migration proposal and writes no files.
- `AGENTS.md` generation is harness-neutral; host-specific instructions remain in the skill pack and bind from the resolved invocation host.
