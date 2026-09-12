# Gantry is a harness-neutral skill pack, not an npm engine

Gantry v4 was specified as a TypeScript/Node.js engine: SQLite execution state, a GTP envelope protocol, an MCP server, a dashboard with settings and capability tokens, merge authorization and provider reconciliation — 19 specs and 132 issues. Meanwhile the `asdlc` skill, written to build that engine, already delivered most of the intended workflow with five stdlib Python scripts and two workflow templates: a deterministic frontier, planning that stops for operator approval, TDD implementation, two-axis review, an adversarial critic with a bounded correction budget, serial integration with gates, and a roadmap that only a script can tick. We decided that Gantry *is* that skill pack, evolved, and abandoned the engine.

What the pack keeps from the engine's intent: agents + code over agents alone, structured results validated against schemas, vertical slices with an estimated context budget, differential quality gates, operator approval before autonomous work, and honest per-harness capability declarations. What it drops, deliberately: Gantry never merges into a target branch (it offers a draft pull request per run), keeps no database (issue `Status:` lines are the authority, a machine-level JSONL run log is observation), exposes no MCP server or settings screen (decisions are taken in the harness conversation), and does not attempt a context ceiling it cannot measure.

## Consequences

- The three deterministic homes are: skills in `.agents/skills/` (repository copy wins over the user copy), a sparse tracked `.gantry/config.json` per repository written only by the setup skill, and observational state under `~/.gantry/state/<repository-execution-unit>/` written only by scripts and hooks.
- Harness support is declared in tiers (reference: Claude Code; supported: OpenCode; compatible: Codex) and every run report states the tier it ran at.
- Session security (output redaction, shell floor rules) is out of scope; a harness policy layer such as the harness-toolkit covers it and Gantry stays compatible with one.
- The engine's decomposition was deleted rather than archived so that agents reading the repository do not treat it as current.
