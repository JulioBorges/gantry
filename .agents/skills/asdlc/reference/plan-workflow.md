# Plan workflow template

Used only when the scope is **unplanned**: a spec with no `issues/` directory, an issue file with no
acceptance criteria, or a free-text goal. It produces issue files in `Status: draft` and stops. It never
writes to `ROADMAP.md` and never sets `ready-for-agent`: AGENTS.md says changing the approved breakdown
needs the operator's approval, so the orchestrator presents the drafts and waits.

## `args` shape

```json
{
  "target": { "kind": "spec", "slug": "<spec-slug>", "specPath": "<rendered-spec-path>" },
  "models": { "plan": "opus", "critic": "fable" },
  "skillDir": "/abs/path/to/repo/.agents/skills/asdlc",
  "repoRoot": "/abs/path/to/repo",
  "policy": { "artifacts": {}, "templates": {}, "git": {}, "budget": {}, "dashboard": {} },
  "paths": {
    "issueDir": "<rendered-issue-directory>",
    "specPath": "<rendered-spec-path>",
    "exemplarIssue": "<existing-issue-path>",
    "decisions": "<repository-decisions-path>",
    "issueTracker": "<repository-issue-tracker-path>",
    "context": "<repository-context-path>",
    "adrs": "<repository-ADRs-path>"
  },
  "date": "2026-09-12"
}
```

`target.kind` is `spec` (slice an existing spec), `issue` (rewrite one issue that lacks criteria;
add `issuePath`) or `goal` (free text in `goal`; the planner first drafts the rendered `paths.specPath`
following an existing spec's section layout, then slices it). The caller resolves `policy` with
`common.py` and renders every repository path into `paths` before invoking this workflow.

## Script

```js
export const meta = {
  name: 'asdlc-plan',
  description: 'ASDLC planning: research, draft vertical-slice issues with testable acceptance criteria, adversarial critique',
  phases: [
    { title: 'Research', detail: 'codebase state, spec + settled decisions, sibling issue format' },
    { title: 'Plan', detail: 'write draft issue files' },
    { title: 'Critique', detail: 'refute slicing and criteria quality; one revision pass' },
  ],
}

const A = args
const scripts = `${A.skillDir}/scripts`
const t = A.target
const policy = A.policy
const paths = A.paths
const targetText = t.kind === 'goal' ? `the goal: "${t.goal}" (new slug: ${t.slug})`
  : t.kind === 'issue' ? `the issue at ${t.issuePath} (spec ${t.specPath})`
  : `the spec at ${t.specPath} (slug ${t.slug})`

const PLAN_SCHEMA = {
  type: 'object',
  properties: {
    filesWritten: { type: 'array', items: { type: 'string' } },
    issues: { type: 'array', items: { type: 'object', properties: {
      ref: { type: 'string' }, path: { type: 'string' }, title: { type: 'string' },
      criteriaCount: { type: 'integer' }, blockedBy: { type: 'array', items: { type: 'string' } } },
      required: ['ref', 'path', 'title', 'criteriaCount', 'blockedBy'] } },
    roadmapAdditions: { type: 'array', items: { type: 'string' }, description: 'ROADMAP.md lines the operator would add, in the file\'s exact format' },
    openDecisions: { type: 'array', items: { type: 'string' } },
  },
  required: ['filesWritten', 'issues', 'roadmapAdditions'],
}

const CRITIQUE_SCHEMA = {
  type: 'object',
  properties: {
    acceptable: { type: 'boolean' },
    problems: { type: 'array', items: { type: 'object', properties: {
      issue: { type: 'string' }, problem: { type: 'string' }, fix: { type: 'string' } }, required: ['issue', 'problem', 'fix'] } },
    frontierErrors: { type: 'array', items: { type: 'string' } },
  },
  required: ['acceptable', 'problems', 'frontierErrors'],
}

phase('Research')
const research = await parallel([
  () => agent(`Survey the repository at ${A.repoRoot} for ${targetText}: what exists today (package manifest, src/, tests/, CI), conventions in AGENTS.md, vocabulary at ${paths.context}, decisions at ${paths.adrs} that constrain this work. Return a dense factual brief for a planner — paths, facts, constraints, no advice.`,
    { label: 'research:codebase', phase: 'Research', model: A.models.plan, effort: 'medium' }),
  () => agent(`Read ${t.specPath || 'the PRD sections relevant to ' + t.goal}, ${paths.decisions} and the relevant repository documents. Return: the contracts this scope owns, the contracts it consumes and who owns them (exact \`slug#NN\` refs), the settled decisions it must not reopen, and the testing seam it must bind to. Facts and refs only.`,
    { label: 'research:spec', phase: 'Research', model: A.models.plan, effort: 'medium' }),
  () => agent(`Read ${paths.exemplarIssue} and two other files in the same directory. Return the exact issue file format as a template: header lines (Type/Status/Slice/Spec/Created), section order, how acceptance criteria are phrased (observable, one behaviour each, runnable where possible), how \`## Blocked by\` cites refs. Also run \`python3 ${scripts}/frontier.py --scope frontier\` and report the current frontier.`,
    { label: 'research:format', phase: 'Research', model: A.models.plan, effort: 'low' }),
])
const brief = research.filter(Boolean).join('\n\n---\n\n')

phase('Plan')
function planPrompt(feedback) {
  return `You are the planner for ${targetText} in the repository at ${A.repoRoot}.

Research briefs:
${brief}

Write the implementation issues as files under ${A.paths.issueDir}/NN-<slug>.md (numbered from 01, one
file per issue), following ${paths.issueTracker} and the exemplar format exactly. ${t.kind === 'goal' ? `First write ${paths.specPath} following the section layout of an existing spec.` : ''}${t.kind === 'issue' ? `Rewrite only ${t.issuePath}; keep its number and slug.` : ''}
The effective Git policy is target \`${policy.git.target}\` with branch prefix \`${policy.git.prefix}\`.

Rules for each issue:
- A vertical slice: demonstrable on its own, through the shared testing seam described in the map, sized for
  one agent context. Not a layer, not a file list.
- \`## Acceptance criteria\`: checkbox items, each one observable behaviour, testable or runnable, no
  "should be fast", no "works correctly". Include the commands or observations that prove them.
- \`## Blocked by\`: real \`slug#NN\` refs from ${paths.decisions} and existing issues. No cycles. Consume
  contracts from their owners; never re-own one.
- Header: \`Type: issue\`, \`Status: draft\` (NOT ready-for-agent — the operator approves), \`Slice: ${t.slug}#NN\`,
  \`Spec:\`, \`Created: ${A.date}\`.
- Never edit ROADMAP.md, the decision source or any other spec's issues. List the roadmap lines you would add
  in roadmapAdditions, in the file's exact checkbox format.
- Record choices you could not settle in openDecisions instead of guessing.
${feedback ? `\nA critic refuted the previous draft. Fix every item:\n${feedback.map((p, i) => `${i + 1}. ${p.issue}: ${p.problem} → ${p.fix}`).join('\n')}\n` : ''}
Return structured output only.`
}
let plan = await agent(planPrompt(null), { label: 'plan', phase: 'Plan', schema: PLAN_SCHEMA, model: A.models.plan })

phase('Critique')
function critiquePrompt(p) {
  return `You are the adversarial critic of a planning breakdown for ${targetText}. Try to REFUTE that it is ready
for implementation. Default to acceptable=false when uncertain.

Files written: ${p.filesWritten.join(', ')}

Check, reading every file:
1. Each issue is a vertical slice demonstrable alone (not a horizontal layer, not "set up the module").
2. Every acceptance criterion is observable and testable; flag vague ones verbatim.
3. Run \`python3 ${scripts}/frontier.py --scope ${t.slug} --include-parked\`: zero errors, no cycles, no dangling refs.
4. Every consumed contract is owned by the ref cited, per ${paths.decisions}; nothing re-owns an
   existing contract; no settled decision reopened.
5. Format matches ${paths.exemplarIssue} and ${paths.issueTracker}; Status is draft; Created is ${A.date}.
6. Coverage: every requirement and user story of the spec maps to at least one criterion; nothing invented.
Do not edit files. Return structured output only; \`fix\` must be actionable.`
}
let critique = plan ? await agent(critiquePrompt(plan), { label: 'critique', phase: 'Critique', schema: CRITIQUE_SCHEMA, model: A.models.critic }) : null
if (plan && critique && !critique.acceptable) {
  log(`plan refuted: ${critique.problems.length} problem(s) — one revision pass`)
  plan = await agent(planPrompt(critique.problems), { label: 'plan:revise', phase: 'Plan', schema: PLAN_SCHEMA, model: A.models.plan }) || plan
  critique = await agent(critiquePrompt(plan), { label: 'critique:2', phase: 'Critique', schema: CRITIQUE_SCHEMA, model: A.models.critic }) || critique
}
return { target: t, plan, critique }
```

## After it returns

1. Show the operator: the issue list, the critique verdict and remaining problems, `roadmapAdditions`,
   `openDecisions`.
2. Stop for planning approval. Do not implement from drafts. When the operator approves: set each issue to `ready-for-agent`
   with `roadmap.py status <ref> ready-for-agent`, add the roadmap lines exactly as proposed (and bump the
   spec heading's `/total`), run `roadmap.py check`, commit, then re-run `frontier.py` and continue with
   the round loop.
