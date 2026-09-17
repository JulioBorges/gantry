# Build problem vs solution, skills pack, and harness compatibility sections

Type: issue
Status: done
Slice: `gantry-site#04`
Spec: `.scratch/gantry-site/spec.md`
Created: 2026-09-17

## Parent

`gantry-site`

## What to build

Implement the narrative and capability sections of the page: (1) Problem vs Solution contrasting autonomous agent pitfalls (context degradation, mock escapes, fake green tests, self-approval) against Gantry's deterministic guardrails ("Agents + code > agents alone"); (2) Three Skills Pack detailing `gantry`, `gantry-setup`, and `gantry-dashboard`; and (3) Harness Compatibility Matrix displaying verified support tiers (Claude Code, OpenCode, Codex, Antigravity, Cursor) with honest capabilities criteria.

### Files to read

- `.scratch/gantry-site/spec.md`
- `.scratch/gantry-site/issues/02-hero-install-widget-and-visual-rig.md`
- `PRD.md`
- `README.md`
- `docs/adr/0004-skill-pack-instead-of-an-engine.md`

## Acceptance criteria

- [x] Problem vs Solution section highlights failure modes vs Gantry principles with structured visual cards.
- [x] Skills section clearly delineates the roles of `gantry`, `gantry-setup`, and `gantry-dashboard`.
- [x] Harness matrix displays tier definitions, capabilities, and verification notes without fabricated claims.
- [x] Playwright test asserts section presence, correct heading hierarchy, link integrity, and responsive grid layouts.

## Blocked by

- gantry-site#02

## Comments

Approved vertical slice breakdown.
