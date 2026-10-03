# Spec: Keep each operator's harness outside tracked policy

Type: spec
Status: draft
Map: `ROADMAP.md` (spec 19)
Source: Personal-project adoption, 2026-10-03; ADR-0004; ADR-0006; spec 17
Created: 2026-10-03

## Problem Statement

`.gantry/config.json` is the shared, tracked repository policy. The same file also stores `execution.hostHarness` and the harness, model and effort of each role. Setup refuses to write that file while Git ignores it, and a host change rewrites the tracked policy and the marked Gantry section of `AGENTS.md`.

Two operators on one repository then share one harness. The last approved setup becomes the committed preference. Spec 17 already treats the invocation host as separate from saved policy during a Run, and it forbids a second policy file inside the repository. It does not give each operator a durable harness of their own.

## Solution

Shared repository policy stays in tracked `.gantry/config.json`. Each operator's host preference and optional role overlays live in a machine profile under `~/.gantry/profiles/<unit-id>/execution.json`, keyed by the existing repository execution-unit id from `runlog.unit_id`. A personal harness switch writes only that profile. Explicit `--host` still selects the invocation and writes nothing. Team role defaults remain available in tracked policy as the shared baseline.

## User Stories

1. As an operator, I want my harness saved on this machine, so that the next Run in this repository starts from my choice.
2. As an operator, I want another clone of the same repository to keep its own harness, so that my switch does not become theirs.
3. As an operator, I want a personal switch to leave tracked policy and `AGENTS.md` unchanged, so that Git does not record my harness.
4. As an operator, I want an explicit `--host` for one Run, so that a single invocation can differ from my saved profile.
5. As an operator, I want team role defaults to remain in tracked policy, so that a repository can still publish a shared baseline.
6. As an operator, I want a personal role overlay to outrank that baseline on my machine only, so that my Critic harness stays local.
7. As an operator, I want a missing profile to remain valid, so that a fresh clone runs from explicit selection and tracked defaults.
8. As a maintainer, I want ignored tracked policy to keep the existing migration refusal, so that shared policy is not written into an untracked file.
9. As a maintainer, I want a legacy `execution.hostHarness` in tracked policy to remain readable, so that existing repositories keep working until an approved migration removes it.
10. As a maintainer, I want the profile free of credentials and transcripts, so that machine state stays as small as the selection itself.

## Blueprint

### Context

ADR-0004 names three homes: skills under `.agents/skills/`, sparse tracked `.gantry/config.json` written only by setup, and observational state under `~/.gantry/state/<unit-id>/`. ADR-0006 versions role defaults in that tracked policy and keeps credentials and transient state outside it. Spec 12 defines role precedence as Issue override, Run override, repository default, then confirmed environment default. Spec 17 resolves the invocation host from explicit selection, reports a mismatch with the saved preference, and leaves tracked policy unchanged. Spec 17 also rejects a repository-local override file.

This spec adds a fourth home beside observational state: the operator profile. It does not add a policy file inside the repository, and it does not move shared policy out of Git.

### Architecture

`runlog.unit_id` remains the repository identity. The profile path is `~/.gantry/profiles/<unit-id>/execution.json`. Its object contains optional `hostHarness` and optional `roles`, using the same role selection shape as `execution.roles` in tracked policy: `harness`, `model` and optional `effort`. Absence of the file, or of either member, is valid.

Resolution for one invocation:

1. Explicit `--host` selects the Host Harness for that invocation and writes no profile and no tracked policy.
2. Otherwise the profile `hostHarness` is the saved preference.
3. A legacy tracked `execution.hostHarness` applies only when the profile has no host. Setup reports it as legacy and offers an approved migration that copies it into the profile and removes it from tracked policy.

Role precedence becomes: Issue override, Run override, operator profile overlay, repository role default, confirmed environment default. The profile overlay replaces only the roles it names.

Personal switch is a setup path that previews the profile, asks approval, and writes the profile alone. Normal setup remains the only writer of `.gantry/config.json` and of the marked Gantry section in `AGENTS.md`. That section states the repository policy location and contains no host-specific orchestration block. Host-specific instructions stay in the skill pack and bind from the resolved invocation host.

`~/.gantry/state/` remains observational Run state. The profile directory is a sibling, not a Run log.

### Constraints

- Python standard library only. Setup remains the only writer of tracked repository policy.
- The profile lives under `~/.gantry/profiles/<unit-id>/` and is outside the repository worktree.
- A personal switch leaves `.gantry/config.json`, adapter files and `AGENTS.md` byte-for-byte unchanged.
- Ignored `.gantry/config.json` still stops a shared-policy write and still prints the tracked-policy migration proposal. Setup still does not edit ignore rules.
- The profile stores harness, model and effort selections only. Credentials, environment values, transcripts and command output stay out of it.
- Artifacts are English. A legacy tracked host remains readable until the operator approves its removal.

## Implementation Decisions

- Add the profile reader and writer next to the existing policy resolver. `resolve_policy` continues to overlay tracked `.gantry/config.json` on pack defaults. A separate resolver overlays the profile onto execution selection and never merges the profile back into the tracked document.
- Personal switch preview prints the resolved unit id, the profile path and the resulting host and role overlay. Decline, EOF and an unsupported host write nothing. Repetition of the same approved profile is a no-op.
- Normal setup of shared policy omits `execution.hostHarness` from newly written policy. It preserves an existing legacy host unless the operator approves the migration in the same proposal.
- Host-only repair from spec 17 continues to preview tracked changes when the operator asks to change tracked policy. A personal switch is a different command path and cannot be satisfied by rewriting `execution.hostHarness`.
- Workflow entry keeps spec 17's rule: the invocation host is the operator-confirmed selection, and a mismatch with the saved preference does not rewrite policy. The saved preference compared there is the profile host, then the legacy tracked host.
- `AGENTS.md` generation for a non-Codex and a Codex repository policy uses one harness-neutral marked section. Codex orchestration text is selected from the skill at invocation time.
- Tests use a temporary home directory and a temporary Git repository. They do not read the developer's `~/.gantry`.

## Testing Decisions

- Public seams are the setup CLI and the execution host CLI, plus `resolve_policy` remaining independent from the profile. Assert exit status, profile bytes, tracked policy bytes and `AGENTS.md` bytes.
- Cover two profiles for one unit, a missing profile, explicit `--host` with no writes, decline, unsupported host, legacy tracked host below the profile, approved legacy removal, and an ignored tracked policy that still refuses shared setup.
- Cover role precedence with a tracked Critic default and a profile Critic overlay, including an Issue override above both.
- A personal switch fixture asserts the tracked policy hash and the marked `AGENTS.md` section are unchanged, including when the previous marked section contains the Codex guardrails.

## Contract

### Definition of Done

- [ ] An approved personal switch writes `~/.gantry/profiles/<unit-id>/execution.json` and leaves tracked policy, adapters and `AGENTS.md` unchanged.
- [ ] Two profiles for the same execution unit resolve two different hosts from the same tracked policy.
- [ ] Explicit `--host` selects the invocation, writes nothing, and outranks the profile and any legacy tracked host.
- [ ] Role resolution applies Issue, Run, profile overlay, repository default, then confirmed environment default.
- [ ] Ignored tracked policy still refuses a shared-policy write and still prints the migration proposal without editing ignore rules.
- [ ] An approved legacy migration removes `execution.hostHarness` from tracked policy after copying it into the profile. Until then, readers honor the legacy key only when the profile has no host.
- [ ] CLI transcripts in a temporary home demonstrate the contract, and an ADR records the profile home beside ADR-0004 and ADR-0006.

### Regression Guardrails

- Tracked `.gantry/config.json` remains the shared repository policy and setup remains its only writer.
- `~/.gantry/state/` remains observational and receives no harness preference.
- Spec 17 invocation binding still refuses to treat installed binaries or environment hints as proof of the current host.
- Repository readiness, role availability and host identity stay separate checks.
- A personal switch grants no roadmap completion and edits no issue status.

### Scenarios

```gherkin
Scenario: Two operators keep different hosts
  Given one tracked policy with no execution.hostHarness
  And operator A has an Antigravity profile for this execution unit
  And operator B has a Codex profile for the same execution unit
  When each operator resolves the saved preference
  Then A resolves Antigravity and B resolves Codex
  And the tracked policy bytes are identical

Scenario: Personal switch does not touch Git
  Given tracked policy and AGENTS.md exist
  When the operator approves a personal switch to Antigravity
  Then the profile records Antigravity
  And tracked policy, adapter files and AGENTS.md are byte-for-byte unchanged

Scenario: One invocation overrides the profile
  Given the profile host is Antigravity
  When the operator passes --host claude-code
  Then this invocation resolves Claude Code
  And the profile and tracked policy are unchanged

Scenario: Profile role outranks the team default
  Given tracked policy selects a Codex Critic
  And the profile selects a Claude Code Critic
  When role resolution runs without an Issue or Run override
  Then the effective Critic is the Claude Code selection
  And another operator without that profile still receives the Codex default

Scenario: Ignored shared policy still refuses setup
  Given .gantry/config.json is ignored by the repository
  When the operator runs shared setup
  Then setup exits with the tracked-policy migration proposal
  And no ignore rule or policy file is written
```

## Out of Scope

- Changes to an adopting repository, its ignore rules, or its installed skill copy.
- A second policy file inside the repository worktree, including a gitignored `.gantry/execution.json`.
- Detecting the current harness from installed binaries, skill directories or inherited environment variables.
- A settings screen, dashboard editor or credential store.
- Changing spec 17's resume transition, adapter ownership or hook compatibility.
- Removing team role defaults from tracked policy. Personal overlays sit above them; the shared baseline stays.

## Further Notes

Proposed as spec 19, ordered after spec 17. Planning approval is still required before any issue moves to `ready-for-agent`. This revises the spec 17 decision that saved host preference lives in tracked policy, and it records that revision in a new ADR rather than by rewriting ADR-0004 or ADR-0006 in place.

## Changelog

- 2026-10-03 — Draft from a personal-project adoption: setup refused an Antigravity switch while `.gantry/config.json` was ignored, then rewrote shared policy once the file became trackable.
