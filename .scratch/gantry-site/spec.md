# Spec: Gantry marketing and showcase site

Type: spec
Status: approved
Map: `ROADMAP.md` (spec 13)
Source: Product requirements, grilling session 2026-09-17, `PRD.md`, `README.md`, ADR-0004
Created: 2026-09-17

## Blueprint

### Context

Gantry is a harness-neutral agentic SDLC skill pack that turns an approved Spec into verified software deliveries inside the operator's coding harness. While the repository provides documentation and npm package distribution, it lacks a public-facing landing page and showcase portal to introduce developers to Gantry's capabilities, core philosophy ("Agents + code > agents alone"), and deterministic workflow scripts.

Developers seeking reliable agentic workflows need an authentic, high-precision introduction that clearly explains how Gantry prevents typical agent failure modes (context bloat, mocked tests, hallucinated completions, unearned self-approval) without resorting to generic "AI-slop" aesthetics.

### Architecture

The site will be developed as a standalone static site located in `site/` within this repository, built with Astro and Tailwind CSS. The output deploys automatically to GitHub Pages at `https://julioborges.github.io/gantry/` via a GitHub Actions workflow using `actions/deploy-pages`.

The visual language adheres to an industrial precision theme directly inspired by the official artwork (`assets/gantry.png`), utilizing deep obsidian/slate backgrounds (`#0a0d14`, `#101622`), glowing amber/orange accents (`#ff9900`, `#f59e0b`), technical monospace typography, and crisp structural borders.

Interactive elements are isolated to lightweight React or Preact islands:
1. An Interactive Pipeline Simulator allowing visitors to click through the stages of Gantry (Spec & Requirement Critic, Planning & Token Budget, TDD Implementer, Two-Axis Reviewer, Adversarial Critic, and Serial Integration Gates) and observe the deterministic script rules, agent roles, and simulated terminal outputs.
2. A language toggle switching content between English (default) and Portuguese (PT-BR).

Per repository rules, all frontend components and flows will be covered and validated by a Playwright test suite verifying visual rendering, responsive design across mobile/desktop, interactive simulator transitions, and accessibility compliance.

### Constraints

- Zero "AI-slop": no generic purple/cyan gradient meshes, no meaningless floating spheres, and no hyperbolic marketing claims.
- Pure static HTML generation for the majority of the page, with lightweight client-side islands only where stateful interaction is required.
- Astro configuration must support `base: '/gantry/'` for correct asset paths on GitHub Pages.
- Deployment must run through standard GitHub Pages Actions without external server dependencies.
- Frontend implementation testing with Playwright is mandatory before marking delivery complete.

## Contract

### Definition of Done

- [ ] Astro static site project created in `site/` with Tailwind CSS and base path configured for GitHub Pages.
- [ ] Industrial aesthetic implemented with dark obsidian theme, glowing amber accents, and technical typography matching `assets/gantry.png`.
- [ ] Hero section showcasing value proposition, crane visual motif, and multi-harness quick-install snippet with copy functionality.
- [ ] Problem vs Solution section explaining why raw agents fail and how deterministic scripts and adversarial critics enforce rigor.
- [ ] Interactive Pipeline Simulator island allowing users to step through Spec, Planning, TDD, Review, Critic, and Integration phases with live terminal feedback.
- [ ] Language toggle enabling seamless switching between English and Portuguese (PT-BR).
- [ ] Three Skills Pack section detailing `gantry`, `gantry-setup`, and `gantry-dashboard`.
- [ ] Harness compatibility matrix presenting honest support tiers across Claude Code, OpenCode, Codex, Antigravity, and Cursor.
- [ ] GitHub Actions workflow in `.github/workflows/deploy-pages.yml` configured to build and deploy to GitHub Pages on pushes to `main` affecting `site/**`.
- [ ] Comprehensive Playwright test suite validating rendering, mobile responsiveness, interactions, and accessibility.

### Regression Guardrails

- Existing repository pack files (`.agents/skills/`, `bin/`, `scripts/`, `tests/`) remain intact and unaltered.
- Existing npm build and test targets continue passing without failure or dependency contamination.
- The site directory remains self-contained with its own dependencies and scripts.

### Scenarios

```gherkin
Scenario: Visitor views the Gantry landing page
  Given a visitor navigates to the Gantry site on GitHub Pages
  When the page loads
  Then the hero displays the core value proposition and industrial crane visual
  And the quick install snippet provides copyable installation commands for supported harnesses

Scenario: Visitor explores the interactive pipeline simulator
  Given a visitor is viewing the pipeline simulator section
  When the visitor selects the Adversarial Critic phase
  Then the simulator displays the critic's verification role, evidence requirements, and budget limits
  And the simulated terminal output shows acceptance checks and gate verification results

Scenario: Visitor switches language to Portuguese
  Given the site is displayed in English
  When the visitor toggles the language selector to Portuguese
  Then all section headings, descriptions, and simulator labels translate to Portuguese
  And the layout preserves structural styling and responsiveness

Scenario: Automated build and deployment to GitHub Pages
  Given changes are pushed to the main branch affecting files in site
  When the deploy-pages workflow triggers
  Then the Astro site builds successfully with base path /gantry/
  And the resulting artifact deploys to GitHub Pages
```

## Out of Scope

- Hosting external execution backends, databases, or web-based command runners.
- Mutating web dashboard for live repository state (dashboard remains local loopback via `gantry-dashboard`).
- Custom apex domain DNS management (standard GitHub Pages URL used initially).

## Changelog

- 2026-09-17 — Initial draft approved following design grilling interview.
