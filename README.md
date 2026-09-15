# Gantry

**Turn an approved Spec into verified software deliveries inside your coding
harness.**

[![CI](https://github.com/JulioBorges/gantry/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/JulioBorges/gantry/actions/workflows/ci.yml)
[![Release](https://github.com/JulioBorges/gantry/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/JulioBorges/gantry/actions/workflows/release.yml)
[![npm version](https://img.shields.io/npm/v/%40julioborges%2Fgantry)](https://www.npmjs.com/package/@julioborges/gantry)
[![GitHub release](https://img.shields.io/github/v/release/JulioBorges/gantry)](https://github.com/JulioBorges/gantry/releases)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#requirements)
[![Agent Skills](https://img.shields.io/badge/Agent-Skills-orange.svg)](#installation)
[![Status: early development](https://img.shields.io/badge/status-early%20development-yellow.svg)](#project-status)

Gantry is an open source, harness-neutral skill pack for agentic software
development. Deterministic scripts decide which Issues are ready and whether
checks pass. Fresh agents implement, review, and challenge each delivery. You
approve the plan and decide how the resulting Run is handed off.

[Get started](#quick-start) · [Greenfield example](#greenfield-build-a-new-project) ·
[Brownfield example](#brownfield-extend-an-existing-project) ·
[Contribute](#contributing)

## Why Gantry?

Agent-written code needs more than a passing test suite and a completion summary.
Gantry gives each delivery a repeatable path from requirements to independent
verification:

- **Plan before building.** Validate the Spec, create vertical-slice Issues, and
  critique the breakdown before asking for your approval.
- **Verify independently.** A fresh Critic runs acceptance checks and real
  repository gates, demanding evidence for every criterion.
- **Respect dependencies.** Scripts compute readiness from the blocker graph;
  accepted branches integrate serially with gates after every merge.
- **Track delivery in Git.** Markdown Issues and `ROADMAP.md` record completion;
  only the roadmap script updates authoritative status and checkboxes.
- **Keep decisions in your harness.** Review plans, proposed lessons, draft PRs,
  and cleanup without a separate execution service.

Named after the [gantry crane](https://en.wikipedia.org/wiki/Gantry_crane), the
pack provides the rails for the work. See [ADR-0004](docs/adr/0004-skill-pack-instead-of-an-engine.md)
for the product boundary.

## Project status

The canonical pack lives in `.agents/skills/`. Gantry is under active development.
Capability files declare harness tiers; fixture validation is required before
claiming support for a particular integration. See [PRD §13](PRD.md#13-harness-support)
for harness support and fixture requirements. A declared tier does not prove every harness version
has been exercised.

The npm installer is published as `@julioborges/gantry`. The npm badge above
shows the published version; new releases require maintainer authorization.

## Requirements

| Component | Requirement |
|---|---|
| Workflow | Python 3.10+ and Git |
| Agent environment | A coding harness that can load skills and run commands |
| npm installer | Node.js 22.20.0+ |
| Draft Run PR (optional) | `gh`, authenticated with access to the repository |
| Project checks | Your project's own toolchain and dependencies |

Gantry's workflow scripts use only the Python standard library. Your project's
checks can require additional tools. Keep the host harness open during a Run;
Gantry does not continue as a background service.

## Installation

Run this in the project where you want to use Gantry:

```bash
npx skills add JulioBorges/gantry
```

Select all three skills and your harness in the installer:

| Skill | Purpose |
|---|---|
| `gantry-setup` | Configure artifact locations, templates, checks, Git policy, and hooks |
| `gantry` | Plan and execute verified Issues |
| `gantry-dashboard` | Open the read-only kanban for recorded Runs |

You can also copy or symlink the three directories into
`<repo>/.agents/skills/` or `~/.agents/skills/`. The repository copy wins.

The npm package includes a bundled installer:

```bash
npx @julioborges/gantry add
npx @julioborges/gantry add --agent codex --yes
npx @julioborges/gantry add --global
npx @julioborges/gantry add --list
```

`add` delegates to a pinned version of the [skills CLI](https://github.com/vercel-labs/skills)
using the bundled files. Agent selection and global installation options pass
through unchanged. The npm command installs skills; it does not execute a Run.

## Quick start

After installation, open your coding harness in the repository and send:

```text
Use gantry-setup to configure this repository. Present the proposed artifact
locations, templates, check commands, Git target, and hook settings for approval
before applying the policy.
```

Approve the reviewed setup, prepare a Spec using the
[default template](.agents/skills/gantry/templates/spec.md) or your repository's
configured equivalent, and commit the setup and Spec. Start from a clean Git
working tree, then send:

```text
Use gantry for Spec delivery-api. Validate the Spec and prepare the Issue
breakdown. Stop for my planning approval before implementation.
```

Review the resulting Issues, criteria, dependencies, and plan critique. If you
accept that particular breakdown, send:

```text
I approve the delivery-api Spec and the Issue breakdown just presented.
Use gantry delivery-api --limit 4 --budget 2 to execute all approved Issues.
```

These are **prompts in your coding harness**, not terminal commands. Use its
skill invocation syntax when available, or explicitly name the skill in prose.
`delivery-api` identifies your Spec scope, normally
`.scratch/delivery-api/spec.md`; it is not a filename to copy verbatim.

## Complete execution examples

The examples below cover setup, Spec preparation, planning approval,
implementation, and handoff. Spec authoring happens before the Gantry Run;
Gantry reads and critiques the Spec rather than rewriting it.

### Greenfield: build a new project

Build a small Python CLI that adds and lists tasks in a local JSON file. Start
with an initial Git commit so the Run has a target branch to branch from:

```bash
mkdir task-cli
cd task-cli
git init -b main
printf '# Task CLI\n' > README.md
git add README.md
git commit -m "Initialize task CLI repository"
npx skills add JulioBorges/gantry
```

**1. Configure the repository.** Open your harness in `task-cli` and send:

```text
Use gantry-setup for this new Python project. Propose main as the Git target,
.scratch/<slug>/ for Specs and Issues, and unittest discovery as the test gate.
There is no test suite yet: identify the bootstrap requirement, and do not
accept no_gates or an empty test run as proof of completion. Present the full
policy and hook choices before writing them.
```

Review and approve the proposed policy. The bootstrap Issue must establish and
exercise meaningful tests before it can complete.

**2. Prepare the Spec outside the Run.** Create
`.scratch/task-cli/spec.md` from the effective template and fill every required
section. Define these outcomes and boundaries:

- `python3 -m task_cli add "Buy milk" --file tasks.json` creates a stored task
  with a unique ID and reports it to the user.
- `python3 -m task_cli list --file tasks.json` lists stored tasks; a missing file
  produces an empty list without an error.
- Tasks persist across separate CLI invocations. Empty titles and malformed JSON
  produce a clear error and a nonzero exit code without overwriting stored data.
- Tests exercise the CLI with temporary files. No network, accounts, task
  deletion, or UI is included.

Include observable Given/When/Then scenarios and regression guardrails in the
Spec. Commit the installation files, approved setup, and completed Spec before
starting the Run.

**3. Request and review the plan.** Send:

```text
Use gantry task-cli --limit 2 --budget 2. Validate the Spec and prepare vertical
slices covering every outcome, including bootstrap tests. Show the dependencies
and plan critique, then stop for my approval.
```

A possible breakdown is an add-and-persist slice with real tests, followed by a
list-and-error-handling slice. Review the actual generated plan rather than
assuming these example slices are authoritative. Amend the Spec if Requirement
Review finds a blocker, then request planning again.

**4. Approve the concrete plan and execute.** After reviewing the draft Issues:

```text
I approve the task-cli Spec and the exact Issue breakdown just presented.
Use gantry task-cli --limit 2 --budget 2 to execute the approved scope in a
dedicated Run worktree. Keep the bootstrap test gate meaningful.
```

Answer the preflight worktree and model choices. Gantry schedules ready Issues,
implements each with TDD, reviews it, runs independent Critic verification, and
integrates accepted work into the Run branch. Successful rounds advance until
the scope completes; a failed round stops with evidence and preserved work.

**5. Review the handoff.** Expect criterion evidence, integration gate results,
updated Issues and roadmap, the declared support tier, remaining frontier,
optional lesson candidates, and a cleanup plan. If you want the offered PR:

```text
Open the draft Run pull request from the reported Run branch to main using the
verified delivery evidence. Leave merging for my review.
```

If `gh` is unavailable, the Run branch is the handoff. Review the proposed
cleanup separately before authorizing removal of any branches or worktrees.

### Brownfield: extend an existing project

Add pagination to an existing `GET /orders` endpoint while preserving its
current behavior for clients that do not request pagination.

**1. Establish the baseline and install.** In your existing repository, review
`git status`, resolve uncommitted work, install project dependencies, and run the
current checks using the repository's documented commands. Then install Gantry:

```bash
npx skills add JulioBorges/gantry
```

**2. Adapt setup to existing conventions.** Open your harness and send:

```text
Use gantry-setup for this existing repository. Inspect AGENTS.md, the canonical
Specs and Issues, ADRs, test commands, and target branch. Reuse those locations
and templates; propose equivalent heading mappings where needed. Preserve
existing hooks and present any conflicts. Show the full proposed policy before
writing it. Keep tests absolute; offer differential checks only where real
structured output supports comparison.
```

Approve the concrete settings. Existing debt in a differential check remains
visible; new or aggravated findings block. An absolute check still has to pass.
Setup does not waive a failing baseline or approve the feature plan.

**3. Prepare or adapt the canonical Spec.** Use the agreed location and template
for the `orders-pagination` scope. Include these explicit behaviors:

- Requests without pagination parameters keep the existing response shape,
  ordering, and authorization behavior.
- Requests with `page` and `pageSize` return the agreed paginated contract,
  including stable ordering and the defined metadata.
- Invalid values return the repository's standard client error. Define default
  values, maximum page size, and out-of-range behavior in the Spec.
- Existing clients and access restrictions have regression scenarios. Tests use
  the repository's established integration fixtures and required real services.
- No schema migration, authorization redesign, or unrelated refactoring is
  included.

Replace every undecided detail with an agreed value before planning. If an
existing Spec is missing required content, review and amend it in its canonical
format. Commit the installation, approved setup, and Spec so preflight sees a
clean working tree.

**4. Plan, approve, and execute.** Send:

```text
Use gantry orders-pagination --limit 2 --budget 2. Validate the canonical Spec,
inspect existing endpoint and integration tests, and propose vertical slices
with compatibility criteria. Stop after the plan critique for my approval.
```

After reviewing that exact breakdown, send:

```text
I approve the orders-pagination Spec and the Issue breakdown just presented.
Use gantry orders-pagination --limit 2 --budget 2 in a dedicated Run worktree.
Execute the approved scope with the configured gates and regression checks.
```

Answer the worktree and model choices. Each accepted Issue integrates into the
Run branch serially; gates run after every merge. A red integration gate stops
the Run. Changes to approved behavior or dependencies require a plan amendment.

**5. Inspect results and resume when needed.** Review the same evidence-backed
handoff described in the greenfield example. To revisit an interrupted scope:

```text
Use gantry orders-pagination. Report remaining ready and blocked Issues and
any in-flight worktrees. Offer continuation in the preserved worktree before
starting new work, retaining correction attempts already spent.
```

Continuation is an operator choice, not an automatic budget reset. Once the
scope completes, explicitly authorize the offered draft Run PR if desired,
review it under the repository's normal process, and approve cleanup separately.

## How a Run works

```text
Preflight → Spec validation → Requirement Review → Plan → Plan critique
                                                        ↓
                                               Operator approval
                                                        ↓
Ready Issues → Implement (TDD) → Review → Critic → Serial integration
                   ↑                       │          + gates
                   └── bounded corrections ┘              ↓
                                                  Roadmap update
                                                        ↓
                              Next round or final report + PR offer
```

Already planned scopes skip planning. `--limit` caps Issues per round (default
4); `--budget` caps Critic correction attempts per Issue (default 2). The single
review fix pass is separate. These limits do not approve a plan or restrict a
Run to a single round.

| Scope | Meaning |
|---|---|
| `delivery-api` | One Spec's Issues |
| `delivery-api#01` | One Issue |
| `wave:1` | A roadmap wave |
| `frontier` | Currently ready work |
| `all` | All discovered Issues |
| `"free-text goal"` | Unplanned scope; draft planning stops for approval |

Workflow scripts own readiness (`frontier.py`), criteria (`acceptance.py`),
gates (`gates.py`), Spec structure (`spec.py`), context estimates (`budget.py`),
result validation (`result.py`), and status updates (`roadmap.py`). Guard hooks
block shortcuts and record events; they never grant completion.

Only Critic acceptance, passing gates, and a clean worktree permit completion.
Gantry offers one draft PR per Run after explicit approval. It never merges
into the target branch. Lessons stay proposals, and cleanup requires approval
of the printed plan.

## Harness capabilities

The current [capability files](.agents/skills/gantry/capabilities/) declare:

| Tier | Harness | Declared capabilities |
|---|---|---|
| Reference | Claude Code | Parallel rounds, native structured output, worktree isolation, per-role models, hooks |
| Supported | OpenCode | Per-role models and plugin hooks; script-validated results; manually managed isolation |
| Compatible | Codex | Manually driven chain and script-validated results; no hooks or native parallel rounds declared |

Use the host's available features without assuming parity. Every final Run
report states its declared tier. Gantry does not provide session security or
output redaction; apply your harness's policy layer for those concerns.

## Dashboard and artifacts

Ask your harness to `use gantry-dashboard` to open the read-only local kanban.
It displays recorded Runs and operator waits; decisions remain in the harness.

| Artifact | Default location |
|---|---|
| Spec | `.scratch/<slug>/spec.md` |
| Issues | `.scratch/<slug>/issues/` |
| Delivery roadmap | `ROADMAP.md` |
| Repository policy | `.gantry/config.json` |
| Custom templates | `.gantry/templates/` |
| Run logs | `~/.gantry/state/<unit-id>/runs/<run-id>.jsonl` |

Setup can map existing repository locations. Issue status and criteria are the
authority on delivery state; Run logs provide observation across a clone's
worktrees.

## Documentation

- [Product requirements](PRD.md): scope, workflow, and acceptance requirements.
- [Domain glossary](CONTEXT.md): canonical terms and product boundaries.
- [Architecture decisions](docs/adr/): standing decisions.
- [Agent contribution rules](AGENTS.md): repository instructions.
- [Delivery roadmap](ROADMAP.md): implementation progress and dependencies.
- [Workflow skill](.agents/skills/gantry/SKILL.md): execution protocol and references.

## Contributing

Bug reports, documentation improvements, and focused pull requests are welcome.
Use [GitHub Issues](https://github.com/JulioBorges/gantry/issues) to describe a
reproducible problem or propose a change. Delivery Issues used by Gantry itself
remain local Markdown artifacts.

All changes go through a PR; `main` requires passing CI and maintainer review.
Only [JulioBorges](https://github.com/JulioBorges) reviews and merges contributions.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the fork workflow, required gates,
and the documented self-review exception for maintainer PRs.

Before changing the pack, read `PRD.md`, `CONTEXT.md`, `docs/adr/`, and `AGENTS.md`.
Keep documentation and generated artifacts in English. Explain behavior changes
and include validation evidence in your pull request.

Run the Python suite from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
make test
```

For installer or packaging changes, also run:

```bash
npm ci
npm run test:package
npm pack --dry-run
```

Frontend changes require Playwright validation under `AGENTS.md`. Complete
roadmap Issues only when all criteria are met, using `roadmap.py done`, and
verify with `roadmap.py check`.

### Publishing to npm

Releases use the manually authorized [Release workflow](.github/workflows/release.yml).
A version bump goes through a PR, then JulioBorges dispatches publication from
`main` for the exact merged commit and approves the `npm-release` environment.
The workflow reruns gates, publishes the verified tarball using npm OIDC with
provenance, verifies registry integrity, and creates the immutable version tag
and GitHub Release. Merging a PR does not automatically publish.

See the [maintainer release runbook](docs/maintainers/releases.md) for versioning,
authorization, npm trusted publisher setup, and recovery after partial failures.
The package includes only the installer, three skill directories, README and
license; project Issues, fixtures, caches, local configuration and runtime state
are excluded. Local `make release` retains its npm account check, but GitHub
Actions is the normal publication path.

## License

Gantry is licensed under the [Apache License 2.0](LICENSE).
