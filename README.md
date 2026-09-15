# Gantry

**A harness-neutral skill pack that runs an agentic software development life cycle — deterministic scripts decide, agents build and refute, the operator approves.**

Gantry turns an approved spec into verified, roadmap-tracked deliveries from inside your coding harness (Claude Code, OpenCode, Codex). A run slices the spec into vertical-slice issues and stops for your approval; then, round by round, a fresh implementer builds each issue with TDD, a reviewer checks standards and spec, and an adversarial critic tries to refute completion by running the acceptance criteria and the repository's real gates itself. Only the critic's acceptance lets a script mark an issue done. The run ends with a draft pull request and a report you can trace back to evidence.

Named after the [gantry crane](https://en.wikipedia.org/wiki/Gantry_crane): it does not lift the cargo itself — it provides the rails so every piece lands in the right place.

> **Project status:** canonical pack implemented in `.agents/skills/gantry/` (`gantry`, `gantry-setup`, `gantry-dashboard`). Support for a harness is announced only after the fixture exercises it; see [`PRD.md`](./PRD.md) §13.

---

## The idea

Prose in `AGENTS.md` is probabilistic; a script is not. Gantry puts every decision that must not be improvised into a dependency-free Python script and leaves the cognition to agents:

| Decision | Who makes it |
|---|---|
| Which issues are ready, in which order | `frontier.py` — the blocker graph, never the model |
| What a delivery must prove | `acceptance.py` — the issue's criteria, read by the critic |
| Whether the repository's gates pass, and whether a delivery added findings | `gates.py` — pass/fail or differential against the round's base |
| When an issue becomes done | `roadmap.py done` — the only writer of `Status:` and checkboxes |
| Whether the spec is fit to slice | `spec.py` against the repository's template, then a Requirement Critic |
| Whether an agent's result is acceptable | `result.py` against the role's JSON Schema |

Guard hooks, where the harness supports them, block shortcuts around those scripts and record events; they never grant completion ([ADR-0003](docs/adr/0003-scripts-decide-hooks-guard-and-record.md)). A read-only dashboard shows every run on the machine, issue by issue, phase by phase.

## What a run looks like

```
gantry <spec | spec#NN | wave:N | frontier | "goal">
  preflight   dirty tree refused · dedicated worktree offered · models chosen per role
  readiness   spec.py structural check → Requirement Critic (blockers stop; you fix the spec)
  plan        research → issues in your template → context budget ≤ 15% → plan critic → STOP for approval
  rounds      implement (TDD) → review (1 fix) → critic (≤ 2 corrections) → integrate serially, gates between merges → roadmap.py done
  finish      Learner drafts recurring lessons → draft PR offered → report with evidence, support tier, cleanup plan
```

## The pack

```
.agents/skills/
├── gantry/            the workflow: scripts, result schemas, templates, capability files, hook wiring
├── gantry-setup/      conversational setup; the only writer of .gantry/config.json
└── gantry-dashboard/  the read-only kanban
```

Install by copying or symlinking the three directories into `<repo>/.agents/skills/` or `~/.agents/skills/`; the repository copy wins. Requirements: `python3` ≥ 3.10 and `git`; `gh` for the draft pull request.

## Harness support

| Tier | Harness | Notes |
|---|---|---|
| Reference | Claude Code | parallel rounds via the Workflow tool, native structured output and worktree isolation, guard hooks |
| Supported | OpenCode | native skills and per-role subagents, hooks through a plugin, results validated by script |
| Compatible | Codex CLI | native skills, hooks when enabled, chain driven by hand |

Every run report states the tier it ran at. Gantry is not a session security layer; for output redaction and shell floor rules use a harness policy layer such as the [harness-toolkit](https://github.com/tech-leads-club/harness-toolkit) — Gantry stays compatible with one.

## Documents

- [`PRD.md`](./PRD.md) — requirements, workflow, gates, hooks, dashboard, setup, lifecycle, harness tiers, acceptance criteria
- [`CONTEXT.md`](./CONTEXT.md) — the glossary; use its terms (Issue, Spec, Run, Round, Guard Hook, Run Log…)
- [`docs/adr/`](./docs/adr/) — decisions, including why Gantry is a skill pack and not an engine ([ADR-0004](docs/adr/0004-skill-pack-instead-of-an-engine.md))
- [`AGENTS.md`](./AGENTS.md) — rules for agents working in this repository

## License

[Apache License 2.0](./LICENSE)
