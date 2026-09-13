# Round workflow template

One Workflow invocation implements **one round**: a set of issues whose blockers are all done, so they are
independent of each other. Every issue flows through its own chain with no barrier between issues:

```
implement (TDD)  →  code review  →  [one fix pass]  →  adversarial critic  →  [fix ⇄ critic, ≤ correctionBudget]
```

In Claude Code, pass the script inline to the Workflow tool. In any other harness, follow the same chain by
hand using the `implementPrompt` / `reviewPrompt` / `criticPrompt` functions below as the prompt text and the
schemas as the required JSON shape of each reply (see **Harness notes** in SKILL.md). Do not edit the
JavaScript except where marked; everything variable comes in through `args`.

## `args` shape

```json
{
  "round": 1,
  "issues": [
    { "ref": "<spec-slug>#01", "path": "<rendered-issue-path>",
      "title": "<issue title>", "specPath": "<rendered-spec-path>" }
  ],
  "models": { "implement": "opus", "review": "sonnet", "critic": "fable" },
  "branch": "<policy-prefix><scope-slug>",
  "baseRef": "<round-base-ref>",
  "isolate": false,
  "correctionBudget": 2,
  "skillDir": "/abs/path/to/repo/.agents/skills/asdlc",
  "repoRoot": "/abs/path/to/repo",
  "policy": { "artifacts": {}, "templates": {}, "git": {}, "budget": {}, "dashboard": {} },
  "paths": {
    "decisions": "<repository-decisions-path>",
    "issueTracker": "<repository-issue-tracker-path>"
  },
  "date": "2026-09-12"
}
```

- `issues` comes straight from `frontier.py --json` (`rounds[k]` resolved through `issues[ref]`).
- `policy` is the effective pack policy resolved by `common.py`; `paths` holds its repository-specific
  paths after the caller renders the artifact patterns.
- `isolate` is `true` whenever the round has more than one issue: each implementer then gets its own git
  worktree and the orchestrator integrates the branches serially afterwards (ADR-0002).
- `repoRoot` is where the run lives: the dedicated ASDLC worktree when the user accepted one in preflight,
  otherwise the checkout. Per-implementer worktrees are created relative to it; git places them as siblings
  of the main repository regardless of nesting, so a worktree-inside-a-worktree run is fine.
- `baseRef` is the commit the round starts from (`git rev-parse HEAD` on the round branch), so reviewers
  and the critic diff exactly this round's work.
- `date` is passed in because scripts cannot call `Date`.

## Script

```js
export const meta = {
  name: 'asdlc-round',
  description: 'ASDLC round: TDD implementation, two-axis code review and adversarial acceptance critic per issue',
  phases: [
    { title: 'Implement', detail: 'one TDD implementer per issue' },
    { title: 'Review', detail: 'standards + spec review; one fix pass when blocking' },
    { title: 'Critic', detail: 'adversarial acceptance and gates verification; bounded fix loop' },
  ],
}

const A = args
const budget = A.correctionBudget ?? 2
const scripts = `${A.skillDir}/scripts`
const policy = A.policy
const paths = A.paths

const IMPL_SCHEMA = {
  type: 'object',
  properties: {
    worktree: { type: 'string', description: 'absolute path printed by `pwd` where the work lives' },
    branch: { type: 'string' },
    commits: { type: 'array', items: { type: 'string' }, description: 'short SHA + subject, oldest first' },
    summary: { type: 'string' },
    testsAdded: { type: 'array', items: { type: 'string' } },
    gatesResult: { type: 'string', description: 'the `verdict:` line printed by gates.py plus any failing gate names' },
    decisions: { type: 'array', items: { type: 'string' }, description: 'choices the issue left to the implementer, with where they were recorded' },
    blockers: { type: 'array', items: { type: 'string' }, description: 'anything that made a criterion impossible to satisfy' },
  },
  required: ['worktree', 'branch', 'commits', 'summary', 'gatesResult'],
}

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    blocking: { type: 'array', items: { type: 'object', properties: {
      axis: { type: 'string', enum: ['standards', 'spec'] }, file: { type: 'string' }, finding: { type: 'string' }, fix: { type: 'string' } },
      required: ['axis', 'finding', 'fix'] } },
    nonBlocking: { type: 'array', items: { type: 'object', properties: {
      axis: { type: 'string', enum: ['standards', 'spec'] }, file: { type: 'string' }, finding: { type: 'string' } },
      required: ['axis', 'finding'] } },
    summary: { type: 'string' },
  },
  required: ['blocking', 'nonBlocking', 'summary'],
}

const CRITIC_SCHEMA = {
  type: 'object',
  properties: {
    complete: { type: 'boolean' },
    criteria: { type: 'array', items: { type: 'object', properties: {
      index: { type: 'integer' }, text: { type: 'string' }, met: { type: 'boolean' },
      evidence: { type: 'string', description: 'file:line and/or command + observed output that proves or refutes it' } },
      required: ['index', 'met', 'evidence'] } },
    gatesVerdict: { type: 'string', enum: ['pass', 'fail', 'no_gates', 'not_run'] },
    gateFailures: { type: 'array', items: { type: 'string' } },
    refutations: { type: 'array', items: { type: 'string' }, description: 'why the delivery is not complete, strongest first' },
    requiredFixes: { type: 'array', items: { type: 'string' }, description: 'concrete, ordered, actionable' },
    decisionsForOperator: { type: 'array', items: { type: 'string' } },
  },
  required: ['complete', 'criteria', 'gatesVerdict', 'gateFailures', 'refutations', 'requiredFixes'],
}

function where(impl) {
  return impl && impl.worktree ? impl.worktree : A.repoRoot
}

function implementPrompt(issue, feedback, prev) {
  const loc = prev
    ? `Continue in the existing working copy at ${prev.worktree} on branch ${prev.branch}. Run \`cd ${prev.worktree}\` first.`
    : A.isolate
      ? 'You are running inside a dedicated git worktree created for this issue. All work stays there. Start with `pwd` and `git branch --show-current` and report both verbatim.'
      : `Work directly in ${A.repoRoot} on branch ${A.branch} (verify with \`git branch --show-current\`; never switch branches).`
  const fb = feedback ? `
## Feedback you must address first (source: ${feedback.kind})
${feedback.items.map((f, i) => `${i + 1}. ${typeof f === 'string' ? f : `[${f.axis}] ${f.file || ''} ${f.finding} → ${f.fix || ''}`}`).join('\n')}
${feedback.gateFailures && feedback.gateFailures.length ? `Gate failures reported: ${feedback.gateFailures.join('; ')}` : ''}
Address every item, keep the tests that already pass green, then re-run the gates.` : ''
  return `You are the implementer for issue ${issue.ref} — "${issue.title}" in the repository.
${loc}

## Read first, in this order
1. ${issue.path} — the whole file. The \`## Acceptance criteria\` list is the contract; \`## What to build\` is the design.
2. ${issue.specPath} — the parent spec.
3. ${paths.decisions} — settled operator decisions and contract ownership. Never re-litigate them.
4. CONTEXT.md and docs/adr/ — vocabulary and standing architectural decisions.

## Scope
Deliver this slice completely: every acceptance criterion, demonstrable on its own. Nothing beyond it — other
issues own their contracts; if you need one that does not exist yet, build the thinnest seam and say so in
\`blockers\`. Where the issue says a choice is yours to decide, decide it, record it where the issue says, and
list it in \`decisions\`.

## Method — mandatory
Invoke the \`tdd\` skill (Skill tool, skill name "tdd") and follow it for each behaviour: failing test → minimal
code → refactor. No test may be skipped, disabled, weakened or replaced by a mock for something the criterion
says must be real (real SQLite file, real Git repository, real second OS process, etc.). A criterion that
names a command must be proven by running that command.

## Gates
Before you finish run:
    python3 ${scripts}/gates.py --run --diff-base ${A.baseRef} --cwd "$(pwd)"
and make it pass. If it prints \`verdict: no_gates\`, the acceptance criteria themselves define the gates
(this is the case for the bootstrap issue): create the real scripts and make them pass. If it reports
\`frontend_touched\`, AGENTS.md requires Playwright validation before the work counts as done.
The effective Git policy is target \`${policy.git.target}\` with branch prefix \`${policy.git.prefix}\`.

## Hard rules
- Commit in small, meaningful commits on the current branch. Leave a clean working tree (\`git status --porcelain\` empty).
- Do NOT edit ROADMAP.md, do NOT change the \`Status:\` line and do NOT tick any checkbox in the issue file.
  The orchestrator does that only after the adversarial critic accepts the delivery.
- Do not touch files that belong to other issues' scope. Do not create files outside the repository.
- No TODO / FIXME / "not implemented" left in delivered code.
${fb}
## Return
Structured output only: worktree (absolute path from \`pwd\`), branch, commits, summary, testsAdded, gatesResult,
decisions, blockers. The summary is for another agent, not a human — facts, paths, commands.`
}

function reviewPrompt(issue, impl) {
  return `You are the code reviewer for ${issue.ref} — "${issue.title}".
Working copy: ${where(impl)} (run \`cd ${where(impl)}\` first). Fixed point: ${A.baseRef}. Commits: ${impl.commits.join(' | ')}.

Invoke the \`code-review\` skill (Skill tool, skill name "code-review") with fixed point \`${A.baseRef}\` and the
spec at ${issue.path}. If the skill cannot be invoked, run the same two-axis review yourself and say so:
- Standards: documented repo standards (AGENTS.md, CONTEXT.md, docs/adr/, any CONTRIBUTING/CODING_STANDARDS) plus
  the Fowler smell baseline as judgement calls. Skip anything tooling enforces.
- Spec: for every acceptance criterion and every paragraph of \`## What to build\`, report what is missing or
  partial, what was built that was not asked for, and what looks implemented but wrong. Quote the issue line.

Classify each finding:
- blocking — must be fixed before delivery: a missing/partial criterion, wrong behaviour, a skipped/disabled/
  weakened test, a mock standing in for something the criterion says must be real, a breach of a documented
  standard, a settled decision re-litigated, scope from another issue implemented here.
- nonBlocking — everything else worth recording.

Do not fix anything. Do not edit files. Return structured output only.`
}

function criticPrompt(issue, impl, review, attempt) {
  const priorBlocking = review && review.blocking && review.blocking.length
    ? `\nPrior review findings that were supposed to be fixed:\n${review.blocking.map(b => `- [${b.axis}] ${b.finding}`).join('\n')}\n` : ''
  return `You are the adversarial critic for ${issue.ref} — "${issue.title}". Attempt ${attempt}.
Your job is to REFUTE the claim that this issue is complete. The burden of proof is on the delivery.
Default to complete=false whenever you are uncertain. Never trust the implementer's summary; verify everything yourself.

Working copy: ${where(impl)} (run \`cd ${where(impl)}\` first). Fixed point: ${A.baseRef}.
Implementer claims: ${impl.summary}
Implementer gates claim: ${impl.gatesResult}
${priorBlocking}
## Verification procedure — run all of it
1. \`python3 ${scripts}/acceptance.py ${A.repoRoot}/${issue.path} --json\` — the authoritative criteria list.
   For EACH criterion: locate the code and the test that prove it; if it names a command or observable
   (e.g. \`node dist/bin/gantry.js --version\`, \`git check-ignore ...\`, "a test spawns a second OS process"),
   run it and record the output. A criterion with no test and no runnable proof is NOT met. Record evidence
   as file:line and/or command + observed output.
2. \`python3 ${scripts}/gates.py --run --diff-base ${A.baseRef} --cwd "$(pwd)" --json\` — do not paraphrase,
   read the JSON. verdict fail → complete=false. verdict no_gates → complete=false unless this issue's
   criteria are about creating the gates and you executed those commands yourself and they passed.
   Every \`requirements\` entry (dirty tree, Playwright required) must be satisfied.
3. \`git status --porcelain\` must be empty. \`git log ${A.baseRef}..HEAD --oneline\` must be non-empty.
4. Inspect \`git diff ${A.baseRef}...HEAD\` for: skipped/disabled/focused tests (skip, only, xit, todo,
   @pytest.mark.skip, it.skip), TODO / FIXME / "not implemented", mocks or stubs replacing something a
   criterion says must be real, tests that pass without asserting anything.
5. AGENTS.md compliance: ROADMAP.md untouched by the implementer; the issue's \`Status:\` line and checkboxes
   untouched; Playwright evidence present if frontend_touched.
6. ${paths.decisions}: no settled decision re-litigated, no other issue's contract implemented
   here (scope creep), the boundaries named in \`## What to build\` respected.
7. Prior review findings (above) actually addressed, not just acknowledged.

## Return
Structured output only. \`complete\` is true ONLY if every criterion is met with evidence, gatesVerdict is pass
(or the no_gates exception above holds), the tree is clean and nothing in steps 4–7 stands.
\`requiredFixes\` must be concrete and ordered so the implementer can act without re-investigating.
Put choices only the operator can make into \`decisionsForOperator\`.`
}

async function implement(issue, feedback, prev) {
  const opts = { label: `implement:${issue.ref}`, phase: 'Implement', schema: IMPL_SCHEMA, model: A.models.implement }
  if (A.isolate && !prev) opts.isolation = 'worktree'
  const r = await agent(implementPrompt(issue, feedback, prev), opts)
  if (!r) return prev || null
  if (prev && !r.worktree) r.worktree = prev.worktree
  if (prev && !r.branch) r.branch = prev.branch
  return r
}

const results = await pipeline(
  A.issues,
  issue => implement(issue, null, null),
  async (impl, issue) => {
    if (!impl) return null
    const review = await agent(reviewPrompt(issue, impl), {
      label: `review:${issue.ref}`, phase: 'Review', schema: REVIEW_SCHEMA, model: A.models.review,
    })
    let cur = impl
    let reviewFix = false
    if (review && review.blocking.length) {
      log(`${issue.ref}: review found ${review.blocking.length} blocking finding(s) — one fix pass`)
      cur = await implement(issue, { kind: 'code-review', items: review.blocking }, impl)
      reviewFix = true
    }
    return { impl: cur, review, reviewFix }
  },
  async (state, issue) => {
    if (!state) return { ref: issue.ref, outcome: 'implementer_failed' }
    let impl = state.impl
    let verdict = null
    let corrections = 0
    for (let attempt = 1; ; attempt++) {
      verdict = await agent(criticPrompt(issue, impl, state.review, attempt), {
        label: `critic:${issue.ref}#${attempt}`, phase: 'Critic', schema: CRITIC_SCHEMA, model: A.models.critic,
      })
      if (!verdict || verdict.complete) break
      if (corrections >= budget) {
        log(`${issue.ref}: correction budget (${budget}) exhausted — leaving refuted`)
        break
      }
      corrections++
      log(`${issue.ref}: critic refuted — ${verdict.requiredFixes.length} fix(es), correction ${corrections}/${budget}`)
      impl = await implement(issue, { kind: 'adversarial-critic', items: verdict.requiredFixes, gateFailures: verdict.gateFailures }, impl)
    }
    return {
      ref: issue.ref,
      outcome: verdict && verdict.complete ? 'complete' : (verdict ? 'refuted' : 'critic_failed'),
      worktree: impl.worktree, branch: impl.branch, commits: impl.commits,
      corrections, reviewFix: state.reviewFix,
      review: state.review, verdict,
      decisions: [...(impl.decisions || []), ...((verdict && verdict.decisionsForOperator) || [])],
      blockers: impl.blockers || [],
    }
  },
)

const out = results.filter(Boolean)
log(`round ${A.round}: ${out.filter(r => r.outcome === 'complete').length}/${A.issues.length} complete`)
return { round: A.round, date: A.date, results: out }
```

## Reading the result

Per issue, `outcome` is one of:

| outcome | meaning | orchestrator action |
|---|---|---|
| `complete` | critic accepted with evidence | integrate branch (if isolated), `roadmap.py done <ref>`, commit |
| `refuted` | correction budget spent, critic still refutes | `roadmap.py status <ref> blocked`, `roadmap.py comment <ref> "<top refutations>"`, keep branch, report |
| `implementer_failed` / `critic_failed` | agent died or was skipped | report; retry the issue in the next round only if the user asks |

Never mark anything done from a `refuted` result, however close it looks.
