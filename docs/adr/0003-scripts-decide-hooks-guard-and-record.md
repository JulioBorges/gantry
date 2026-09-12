# Deterministic scripts decide; guard hooks only block shortcuts and record events

Gantry has two deterministic layers and a strict boundary between them. Workflow scripts (frontier, acceptance, gates, roadmap, spec, budget, result) are the sole authority on which work is ready, what a delivery must prove, whether the declared gates pass and when an issue becomes done. Guard hooks, wired into whichever harness supports hooks, exist only to block shortcuts around those decisions — editing an issue's `Status:` or the roadmap outside the roadmap script, force-pushing, skipping tests — and to record events into the run log. A hook never decides that something is ready or done, so the workflow is complete and identical in a harness without hooks; hooks add enforcement and observability, not semantics.

## Considered options

- **Scripts only, rules as prose.** Simplest and fully harness-neutral, but "the implementer must not tick the roadmap" stays a sentence the model obeys, and the run log depends on the model remembering to write it.
- **Depend on the harness-toolkit.** Its floor rules, rails and operator rules are exactly this kind of enforcement, but it supports Cursor and Claude Code only, needs Bun or Node 24 and is Elastic-licensed; Gantry would inherit all three. It stays a compatible companion, never a dependency.
- **Hooks that decide.** Letting a `Stop` hook mark work done would make the workflow differ per harness and would put authority in the layer the agent can least inspect.
