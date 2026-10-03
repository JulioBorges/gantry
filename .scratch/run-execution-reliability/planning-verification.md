# Planning verification: Reliable Run execution and truthful timing

Date: 2026-10-03
Branch: `docs/run-execution-reliability`
Base: `06617ee` (Gantry 1.2.0)

## Approval and publication

The operator accepted the revised Run audit, Spec direction and testing seams, requested Spec/Issue publication and a roadmap update, and then explicitly approved the five-Issue breakdown and dependencies in conversation. The five canonical Issues were promoted through the roadmap status writer to `ready-for-agent`. The authorized Spec index entry was added and generated roadmap sections were refreshed using `roadmap.py waves`.

All 40 Issue acceptance criteria remain unticked. Planning approval does not start an implementation Run, claim Critic acceptance, open a PR or publish a release.

## Verification results

- Spec structural check: valid; no missing/out-of-order required headings, placeholders or malformed scenarios.
- Acceptance CLI: all five canonical Issues parsed successfully with eight criteria each.
- Story coverage: the union of the Issue mappings covers all 32 Spec user stories.
- Frontier over all work: zero graph errors; rounds are `01`, then `02 + 03`, then `04`, then `05`.
- Current frontier: `run-execution-reliability#01` only.
- Roadmap check: zero drift, **52/57 Issues** completed, **9/10 Specs** completed.
- Generated execution waves: **30–33**, increasing the roadmap to 34 waves numbered 0–33.
- Historical preservation: all 52 preexisting completed Issues retain their exact wave placement.
- Relative Markdown artifact links and initial reading references resolve.
- Whitespace checks pass.

## Initial context budget

The size audit uses the shipped `claude-opus-5-5` declaration as a planning baseline: a 200,000-token window and the existing 0.15 context share produce a 30,000-estimated-token limit. This is not a role selection or a live model-availability claim. Execution must validate the operator-selected model and its actual context metadata.

| Issue | Estimated initial tokens | Limit | Verdict |
|---|---:|---:|---|
| `run-execution-reliability#01` | 24,134.50 | 30,000 | pass |
| `run-execution-reliability#02` | 24,449.25 | 30,000 | pass |
| `run-execution-reliability#03` | 28,171.00 | 30,000 | pass |
| `run-execution-reliability#04` | 24,391.25 | 30,000 | pass |
| `run-execution-reliability#05` | 23,426.00 | 30,000 | pass |

The initial Issue 05 package exceeded the baseline by about 88 tokens. Moving Run-log exploration to focused follow-up reading brought it below the limit without changing behavior, acceptance criteria or dependencies. Other additional integration references also remain available through focused exploration rather than mandatory preloading.

## Reproduction commands

From the repository root:

```sh
python3 -B .agents/skills/gantry/scripts/spec.py --check .scratch/run-execution-reliability/spec.md --json
python3 -B .agents/skills/gantry/scripts/roadmap.py check --json
python3 -B .agents/skills/gantry/scripts/frontier.py --scope all --json
python3 -B .agents/skills/gantry/scripts/frontier.py --scope frontier --json
git diff --check
```

For each canonical Issue, run the acceptance CLI with its path and `--json`, and the budget CLI with that path, `--model claude-opus-5-5 --cwd . --json`. The completed-wave comparison uses the base revision's roadmap and current authoritative Issue state.

This change contains planning artifacts and generated roadmap metadata only. The Spec's actual CLI, supported Host continuation and Playwright evidence are future implementation acceptance requirements; this verification does not claim those behaviors are already fixed.
