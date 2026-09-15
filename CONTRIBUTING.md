# Contributing to Gantry

Anyone can open a GitHub Issue and submit a pull request from a fork. GitHub
Issues are public reports and proposals; Gantry's delivery Issues remain local
Markdown under `.scratch/`. Discuss substantial scope changes with the maintainer
before implementation.

Read [AGENTS.md](AGENTS.md), [PRD.md](PRD.md), [CONTEXT.md](CONTEXT.md), and the
[ADRs](docs/adr/). Keep artifacts in English and preserve the skill pack boundary.

## Git workflow

1. Fork `JulioBorges/gantry`, clone your fork, and add the original as `upstream`.
2. Create `feat/<topic>`, `fix/<topic>`, or `docs/<topic>` from current upstream `main`.
3. Make focused commits and run the checks below.
4. Push your branch to your fork and open a PR targeting upstream `main`.
5. Address JulioBorges's review and resolve conversations. Update from upstream
   when the base moves; checks must pass against current `main`.
6. JulioBorges reviews and squash-merges. Contributors receive no upstream write
   access. No direct push, force push, or deletion of `main` is allowed, including
   for its owner. Automated dependency PRs use the same review process.

```bash
git remote add upstream https://github.com/JulioBorges/gantry.git
git fetch upstream
git switch -c feat/my-change upstream/main
npm ci --ignore-scripts
make test
npm run test:package
npm audit --audit-level=high
npm pack --dry-run --ignore-scripts
python3 .agents/skills/gantry/scripts/roadmap.py check
python3 .agents/skills/gantry/scripts/frontier.py --scope all
```

CI tests Python 3.10 and 3.14, the npm installer on Node 22.20.0 and 24,
package installation from a real tarball, dependency vulnerabilities, workflow
syntax, roadmap drift, and blocker graph validity. `CI gates` fails if any
required job fails, is cancelled, or is skipped. Workflow changes also require
`actionlint` 1.7.12. Frontend changes require Playwright evidence as specified in
AGENTS.md; this CI does not establish real harness support or replace the Critic.

Fork PRs run through `pull_request` with a read-only token, no repository secrets,
and no publishing permission. The maintainer may need to approve a contributor's
first workflow execution. Approval to run CI is separate from code review.

Only JulioBorges owns code review and merging. GitHub does not allow an author
to approve their own PR. The owner has a PR-only override for the review ruleset
for maintainer-authored PRs; it cannot bypass the separate PR, CI, linear history,
or branch preservation rules. Use this override only for your own PR after
reviewing the complete diff and passing gates. Review external PRs normally.

## Releases

A merged PR does not publish a version. Version changes and publication are
maintainer decisions. See the [release runbook](docs/maintainers/releases.md).
