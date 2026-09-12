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

`ROADMAP.md` at the repository root tracks delivery: one checkbox per implementation issue, grouped by
wave, with each issue's blockers listed. It also records where work can start and which decisions are
still open.

**Whenever you complete something that appears in the roadmap, update the roadmap in the same change.**
That means all three of these, not just the first:

1. Set `Status: done` in the issue file at `.scratch/<slug>/issues/NN-<slug>.md`.
2. Tick the item's checkbox in `ROADMAP.md` and bump the `done/total` count on its spec heading.
3. Update the **Progress** table at the top of `ROADMAP.md`.

Rules that keep the roadmap trustworthy:

- **Only tick an item whose acceptance criteria are all met.** A vertical slice is demonstrable on its
  own, so a partially delivered one stays unticked. There is no "in progress" mark — that state lives in
  the issue, not here.
- **The issue's `Status:` line wins.** If the roadmap and an issue disagree, the issue is authoritative
  and the roadmap is stale; fix the roadmap.
- **Never tick an item on another agent's behalf** or because a report claims it is done. Verify the
  acceptance criteria against the delivered revision first.
- If work reveals that an issue needs to be split, merged, or added, say so rather than silently editing
  the roadmap — the breakdown was approved by the operator, and changing it needs the same approval.
