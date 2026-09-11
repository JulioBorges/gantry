# Issue tracker: Local Markdown

Issues and specs (you may know a spec as a PRD) for this repo live as markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` — never a single combined tickets file
- Triage state is recorded as a `Status:` line near the top of each issue file
- Comments and conversation history append to the bottom of the file under a `## Comments` heading

## When a skill says "publish to the issue tracker"

Create a new file under `.scratch/<feature-slug>/` (creating the directory if needed).

## When a skill says "fetch the relevant ticket"

Read the file at the referenced path. The user will normally pass the path or the issue number directly.

## Wayfinding operations

Used by `/wayfinder`. The map is `.scratch/<effort>/map.md`; child tickets live under `.scratch/<effort>/issues/`, one file per ticket, numbered from `01`.

- A child ticket has `Type:` and `Status:` lines.
- Blocking is recorded with `Blocked by: NN, NN`.
- The frontier consists of open, unblocked, unclaimed tickets, with the lowest number first.
- Claim by setting `Status: claimed`.
- Resolve by appending `## Answer`, setting `Status: resolved`, and adding a context pointer to `map.md`.
