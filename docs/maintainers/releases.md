# Maintainer release runbook

Only `JulioBorges` reviews, merges, and authorizes publication. Releases are
manually dispatched from `main`; the workflow checks both the initiating and
rerunning actor, revalidates an exact merged commit, and uses the protected
`npm-release` environment. No release runs on fork PRs, PR closure, or tag pushes.

## Prepare a version through a PR

```bash
git fetch origin
git switch -c release/0.1.1 origin/main
npm version 0.1.1 --no-git-tag-version
# Update user-facing documentation and describe the changes in the PR.
npm ci --ignore-scripts
make test
npm run test:package
npm audit --audit-level=high
git add package.json package-lock.json README.md
git commit -m "Prepare release 0.1.1"
git push -u origin release/0.1.1
gh pr create --base main --title "Prepare release 0.1.1" --body "Version bump and release notes; see CI validation."
```

Use semantic versioning: patch for compatible fixes, minor for compatible new
behavior, major for breaking changes. This workflow publishes stable `x.y.z`
versions only. Do not create the version tag locally. Review and squash-merge
the PR after `CI gates` passes, using the documented owner review override for
your own PR. There is no override for mandatory CI or direct pushes.

## Authorize publication

After merging, copy the full SHA of the merged commit from GitHub. Review its
CI results and dispatch the release with that exact SHA:

```bash
gh workflow run release.yml --ref main -f version=0.1.1 -f commit=<full-merged-commit-sha>
gh run list --workflow release.yml
```

Approve the `npm-release` deployment as JulioBorges in GitHub Actions. The
environment permits only `main`, requires your review, and disallows admin
bypass. Self-review is permitted because you are the sole maintainer; manual
dispatch plus environment approval are the publication authorization.

The workflow verifies version/lockfile agreement, ancestry in `main`, tag
identity, tests, the real tarball installer, audit, roadmap, DAG, and clean
source. It packs that commit and publishes the tarball with npm OIDC provenance.
It then verifies registry SHA-512 integrity before creating `v<version>` and the
GitHub Release with generated notes and the tarball asset. Version tags cannot
be updated or deleted. CI and Release actions are pinned to commit SHAs;
Dependabot proposes updates for manual review.

Publication uses `npm publish <verified-tarball> --ignore-scripts`: the workflow
has already executed the test gates explicitly, and OIDC identifies the trusted
workflow rather than an npm user session. This avoids the local `npm whoami`
hook, which is retained for manual `make release` and source publication.
Do not use local publication for the normal release process.

## Recovery

npm publication and GitHub Releases are not an atomic transaction. If publication
succeeds but tag/release creation fails, rerun the same workflow with the same
version and commit. The registry check accepts an existing version only when
its integrity exactly matches the newly packed tarball. It refuses mismatched
bytes, authentication errors, outages, or a tag pointing at another commit.
Never bump a version merely to conceal a failed GitHub Release step; investigate
and recover the matching release first. Do not overwrite existing versions.

## One-time remote settings

Repository rulesets are tracked under `.github/rulesets/` and must also be applied
through GitHub's API/settings; committed JSON alone provides no enforcement.
Required check: `CI gates`, emitted by GitHub Actions. Keep mandatory gates in
the ruleset with **no bypass actors**. The separate review/merge ruleset allows
only JulioBorges to merge through a PR and includes the self-review exception.
Keep JulioBorges as the sole upstream writer; grant contributors no write roles.

Configure npm's trusted publisher for `@julioborges/gantry`:

| Field | Value |
|---|---|
| Provider | GitHub Actions |
| Owner | JulioBorges |
| Repository | gantry |
| Workflow file | release.yml |
| Environment | npm-release |
| Allowed action | Publish |

With npm 11.15+ and an eligible authenticated account:

```bash
npm trust github @julioborges/gantry --repo JulioBorges/gantry --file release.yml --env npm-release --allow-publish
npm trust list @julioborges/gantry
```

npm may require 2FA or browser authentication to change this setting. Do not
add an npm token to PR workflows. See [npm trusted publishing](https://docs.npmjs.com/trusted-publishers/)
and [GitHub rulesets](https://docs.github.com/en/rest/repos/rules).
