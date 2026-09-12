# Honest PBI projection and Monitor swimlanes

Type: issue
Status: ready-for-agent
Slice: dashboard#03
Spec: [`../spec.md`](../spec.md) (spec 17, wave 5)
Created: 2026-09-12

## Parent

[`.scratch/dashboard/spec.md`](../spec.md)

## What to build

The projection builder and the Monitor screen that renders it, one swimlane per pipeline. This is the slice that makes misrepresentation require effort, and the mechanism is the absence of data rather than a rule against drawing it. **The projection has no single "done" value and no numeric context value when usage is unknown** — not because a guideline forbids rendering one, but because there is nothing in the shape to render. Keep that property intact under design pressure: a designer will ask for one progress bar and one status chip per slice, and the answer is that the three stages and the two readiness booleans are a product requirement, not a data-modeling preference.

`stageLabels` carries three independent fields, so implementation completion cannot be displayed as integration. `readiness` carries two booleans, so technical readiness cannot be displayed as operator approval. `context` carries `estimated` and `observed` separately, with `observed` as the union that includes the `unknown` variant carrying a reason and no number. `budgets` carries correction and infrastructure counts separately. Waiting, blocked, and failed project as distinct states each with its reason. Local and provider evidence project as separate lists.

The watermark indicator variant is derived from the declared `monitoring` granularity, never from a threshold value: a threshold marker for `per_tool_call`, a between-turns marker with explicit granularity for `between_turns`, a clearly-labeled self-reported marker for `self_reported`, and no indicator at all for `none`. No variant renders as an enforced ceiling. This is the single place in the product where an unenforced guarantee would be most persuasive, which is why the variant follows the declaration rather than the number.

The projection also carries `mode`, and a `demo` unit renders the persistent simulated-evidence indicator on every record while it is on screen. Note on the demo surface: it is distributed across three slices rather than owned by one — the mode marker here, the re-run control in `dashboard#05`, and the latency measurement in `dashboard#04`. The consequence is that **no single issue owns "the demo looks right end to end"**. Adding that guarantee back as an eighth slice is possible but would carry blockers on `dashboard#02`, `dashboard#03` and `dashboard#04` — the worst blocking profile in the spec — so it was deliberately not done.

Test seam: dashboard-owned. The projection shape and its honesty constraints are this spec's behavior, tested as type-level and unit-level assertions on the builder. No rendering tests beyond the demo-marker persistence check, because a rendering test proves a rendering while the requirement is that a dishonest rendering has no data to draw from.

## Acceptance criteria

- [ ] A PBI at implementation completion projects `implementation: "complete"` with `integration: "not_authorized"`; no code path produces a single aggregate status value for a PBI.
- [ ] A technically ready spec with no operator approval projects `technical: true, operatorApproved: false` as two fields.
- [ ] An `unknown` observed usage projects with no numeric value reachable by the bar renderer, asserted structurally rather than by inspecting rendered output.
- [ ] Each of the four `monitoring` values produces its designated indicator variant, and no value produces an enforced-ceiling variant.
- [ ] Waiting, blocked, and failed project as distinct states each carrying its reason; correction and infrastructure retry counts project as separate fields; local and provider evidence project as separate lists including when one is empty.
- [ ] A demo unit projects `mode: "demo"` on every record and the Monitor shows the simulated-evidence indicator persistently, verified on a screenshot-equivalent render of a scrolled view.

## Blocked by

- `dashboard#01` — the server, the shell, and the `state.project` read path the projection is built from.
- `gtp-protocol#04` — the `ContextUsage` union including its `unknown` variant carrying a reason and no numeric value.
- `harness-adapters#02` — the `contextMonitoring` granularity value on the Integration Capability declaration, which the watermark indicator variant is derived from.
- `execution-core#03` — the distinct waiting states and their reasons that project as `waitingReason`.
- `execution-core#05` — the Correction Budget counters (consumed and limit) that project as separate fields.
- `execution-core#06` — the Infrastructure Retry counter and the infrastructure-blocked reason.
- `demo-mode#01` — the demo mode marker on the Repository Execution Unit and its propagation into projections.
- `verification-adapters#01` — the local evidence reference shape and its structured-report binding.
- `git-integration#07` — the provider evidence reference shape from the Pull Request Observation record.
