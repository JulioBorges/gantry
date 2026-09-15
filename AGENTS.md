## Product documents

Read before working on Gantry itself: [`PRD.md`](PRD.md) (what the skill pack is and does), [`CONTEXT.md`](CONTEXT.md)
(the glossary — use its terms: Issue not PBI, Spec not Living Spec, Run not pipeline) and [`docs/adr/`](docs/adr/)
(standing decisions; ADR-0004 explains why Gantry is a skill pack and not an engine). The Gantry pack provides the workflow skills in `.agents/skills/` (`gantry`, `gantry-setup`, `gantry-dashboard`).

## Agent skills

### Issue tracker

Issues and specs live as local Markdown files under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context documentation uses `CONTEXT.md` at the repository root and `docs/adr/`. See `docs/agents/domain.md`.

## Frontend Implementation Testing

**Mandatory Rule**: Any changes to frontend code MUST be validated with Playwright before marking work complete.

**When to apply**:
- Modified or created UI components, pages, or layouts
- Updated styling, responsive design, or CSS
- Changed form interactions, validation, or user flows
- Added or modified interactive elements
- Updated accessibility features or ARIA attributes

**What to verify**:
- Component renders without errors
- User interactions work as specified
- Responsive behavior on multiple screen sizes
- Form submissions and validation flow
- Accessibility compliance (keyboard navigation, screen reader compat)
- Visual consistency with design specs

**How to report**:
- Include Playwright test results in commit message or PR description
- Document any visual changes with screenshots if needed
- Flag any regressions or unexpected behaviors discovered during testing

**Exception**: Purely non-visual changes (utility functions, business logic without UI impact) don't require Playwright testing.

## Roadmap

`ROADMAP.md` at the repository root, when it exists (it is regenerated once the repository has issues), tracks delivery: one checkbox per implementation issue, grouped into
**execution waves** computed from the blocker graph (wave N only depends on waves below N, so each wave is
one round of parallel implementation). It also records where work can start and which decisions are still
open.

**Whenever you complete something that appears in the roadmap, update the roadmap in the same change** by
running

```
python3 .agents/skills/gantry/scripts/roadmap.py done <spec-slug>#NN
```

which does all three required edits at once — and nothing else does them:

1. Sets `Status: done` and ticks the acceptance criteria in the issue file at `.scratch/<slug>/issues/NN-<slug>.md`.
2. Ticks the item's checkbox in `ROADMAP.md` and refreshes the per-spec and per-wave counts.
3. Updates the **Progress** table at the top of `ROADMAP.md`.

`roadmap.py check` must report no drift afterwards. When a blocker line changes or an issue is added, run
`roadmap.py waves` to recompute the wave layout; it refuses a graph with a cycle.

Rules that keep the roadmap trustworthy:

- **Only tick an item whose acceptance criteria are all met.** A vertical slice is demonstrable on its
  own, so a partially delivered one stays unticked. There is no "in progress" mark — that state lives in
  the issue, not here.
- **The issue's `Status:` line wins.** If the roadmap and an issue disagree, the issue is authoritative
  and the roadmap is stale; regenerate the roadmap.
- **Never tick an item on another agent's behalf** or because a report claims it is done. Verify the
  acceptance criteria against the delivered revision first.
- **The blocker graph must stay a DAG.** `python3 .agents/skills/gantry/scripts/frontier.py --scope all`
  must report zero errors; a new `Blocked by` line that closes a cycle is a defect in the breakdown, not a
  scheduling problem.
- If work reveals that an issue needs to be split, merged, or added, say so rather than silently editing
  the roadmap — the breakdown was approved by the operator, and changing it needs the same approval.
