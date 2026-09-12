# Progressive documentation, quickstart verification, and the demo as a required check

Type: issue
Status: ready-for-agent
Slice: release-engineering#07
Spec: [`../spec.md`](../spec.md) (spec 19)
Created: 2026-09-12

## Parent

[`.scratch/release-engineering/spec.md`](../spec.md)

## What to build

The reader-facing layers, in the order the spec sets and in the order a reader meets them. `README.md`:
what Gantry is, the three commands to the demo, and a recording of the demo pipeline — nothing else
competing for attention. Quickstart: the demo first, then a real repository, with Repository Readiness and
Planning Approval stated as steps rather than glossed, since §13.6 makes the ten-minute real pipeline
conditional on readiness and approvals. Cookbooks, one per workflow: authoring a spec, slicing, running a
PBI, gates, merging, cross-harness routing, dashboard settings. Reference: the operation catalog, the
configuration schema, the GTP contracts, and the support matrix. `PRD.md` last, reachable only from the
reference layer.

Add the CI job that runs the documented quickstart commands against the **installed tarball** rather than
the working tree, so documented behavior and shipped behavior cannot drift. Extracting the commands from
the quickstart must be automated, so adding a command to the documentation without it working fails the
job. Assert that every file under `templates/` is in English, including generated `AGENTS.md` sections,
`CONSTITUTION.md`, and the spec and PBI templates. Include the §7.6 statement that this repository's branch
protection and review requirement are its own policy and not a requirement on the reader's repository.

Build additively against the commands that exist rather than waiting: the demo recording, the
`gantry init --demo` path and the demo-pipeline-as-required-check need `demo-mode#02` (demo fixture
lifecycle) and `demo-mode#07` (the demo pipeline regression check); the real-repository path needs
`machine-setup#07` (`gantry setup`) and `repository-readiness#01`. Start from `--version`, `--help` and
whatever setup surface has landed, and extend the quickstart and the required-check list as those commands
arrive. The required-check set grows over time, so the pull-request workflow stays additive and the
required-check list stays an inspection-verified documentation item.

**The quickstart-drift gap is not closed by this slice, and the documentation should say so.** Verifying
that the documented commands succeed proves they run; it does not prove the demo shows what the readme
claims it shows. That gap is closed by review rather than by a test, so add an explicit review step to the
release documentation instead of implying a job covers it. A quickstart that runs cleanly while describing
something else is the most expensive documentation failure this project could have — it costs the reader
exactly the trust the demo exists to earn.

## Acceptance criteria

- [ ] The documentation tree has the five layers in order, with the readme linking forward and `PRD.md` reachable only from the reference layer.
- [ ] A CI job installs the packed tarball into a temporary directory and executes every command shown in the quickstart, failing if any exits non-zero or if a command shown in the documentation does not exist in the installed binary.
- [ ] Extracting the commands from the quickstart is automated, so adding a command to the documentation without it working fails the job.
- [ ] Every file under `templates/` passes the English assertion, including generated `AGENTS.md` sections, `CONSTITUTION.md`, and spec and PBI templates.
- [ ] The readme states that this repository's branch protection and review requirement are its own policy and not a requirement on the reader's repository.
- [ ] The demo pipeline runs as a required check and the required-check list in the protection documentation names it.
- [ ] The release documentation carries a review step for confirming the demo shows what the readme claims, stated as a review rather than as a test.

## Blocked by

- `release-engineering#02` — provides the installable tarball and the `pack:check` harness the quickstart verification job runs against.
