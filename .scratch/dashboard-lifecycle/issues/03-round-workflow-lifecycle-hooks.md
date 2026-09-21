# Integrate Round Workflow Lifecycle Hooks and Skill Automation

Type: issue
Status: done
Slice: `dashboard-lifecycle#03`
Spec: `.scratch/dashboard-lifecycle/spec.md`
Created: 2026-09-19

## Parent

`dashboard-lifecycle`

## What to build

Automate dashboard lifecycle prompts and execution across Gantry's round workflow:
1. Pre-implementation hook: At the beginning of each ASDLC round (before the `Implement` phase begins), query `dashboard.py status --json`. If inactive, ask the operator whether they wish to start the dashboard. If approved, start the dashboard via `dashboard.py start --daemon` and display the connection URL. If already active, log the URL without prompting.
2. Post-integration hook: At the end of each round (immediately after the `Integrate` step completes), query `dashboard.py status --json`. If active, prompt the operator asking whether they want to shut down the dashboard. If approved, terminate the dashboard with `dashboard.py stop`.
3. Skill documentation: Update `.agents/skills/gantry/SKILL.md`, `.agents/skills/gantry/reference/round-workflow.md`, and `.agents/skills/gantry-dashboard/SKILL.md` to document the daemon subcommands and round lifecycle hooks.

### Files to read

- `.agents/skills/gantry/SKILL.md`
- `.agents/skills/gantry/reference/round-workflow.md`
- `.agents/skills/gantry-dashboard/SKILL.md`
- `.agents/skills/gantry/scripts/dashboard.py`

## Acceptance criteria

- [x] `reference/round-workflow.md` specifies pre-implementation check: if inactive, prompt operator to start dashboard via `dashboard.py start --daemon`.
- [x] `reference/round-workflow.md` specifies post-integration check: if active, prompt operator to stop dashboard via `dashboard.py stop`.
- [x] Inactive dashboard at round start does not prompt if operator declines, proceeding with execution.
- [x] Already active dashboard at round start displays the URL without prompting.
- [x] Documentation in `SKILL.md` and `gantry-dashboard/SKILL.md` reflects daemon subcommands (`start --daemon`, `status`, `stop`) and round hooks.

## Blocked by

- dashboard-lifecycle#01
