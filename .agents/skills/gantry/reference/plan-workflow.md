# Canonical planning workflow

Use this workflow only for an unplanned Spec, an Issue with no criteria, or an approved free-text goal.
The caller resolves and supplies `args.skillDir`, `args.repoRoot`, effective `args.policy`, rendered
`args.paths`, and `args.models.plan` / `args.models.critic`; this file assumes no repository location.

## Roles and sequence

1. Run research in parallel: repository conventions, the Spec and settled decisions, and an exemplar Issue.
2. The Planner writes vertical-slice Issues in the effective issue template, each with `Status: draft`,
   observable acceptance criteria and real non-cyclic blockers.
3. The Plan Critic attempts to refute granularity, coverage, criterion observability, contract ownership,
   format and `frontier.py --scope <slug> --include-parked`.
4. Allow exactly one Planner revision when refuted, then present the result and **stop for explicit operator
   approval**.

## Planner contract

The Planner returns `filesWritten`, `issues` (`ref`, `path`, `title`, `criteriaCount`, `blockedBy`),
`roadmapAdditions` and `openDecisions`. It must:

- write only draft Issue files under `args.paths.issueDir`;
- use `args.paths.specPath`, `decisions`, `context`, `adrs`, `issueTracker` and `exemplarIssue` rather
  than inferred paths;
- never write `ROADMAP.md`, set an Issue to `ready-for-agent`, or implement any issue;
- use English for every artifact.

## Approval transition

After, and only after, an operator approves the exact breakdown, the host harness calls:

```sh
python3 "$skillDir/scripts/roadmap.py" status <ref> ready-for-agent
python3 "$skillDir/scripts/roadmap.py" waves
python3 "$skillDir/scripts/roadmap.py" check
```

The last command must exit 0 before the Run recomputes the frontier. Planning approval does not permit
silent issue additions, splits, merges or dependency changes.
