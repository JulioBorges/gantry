# Evidence: Run execution reliability

Audit date: 2026-10-02
Planning date: 2026-10-03
Inspected Gantry revision: `06617ee` (1.2.0)
Observed Codex CLI: `0.160.0`

## Method and limits

The operator requested analysis of long Gantry Runs. The revised audit inventoried 22 machine-local Runs across five Git execution units, dated September 17 through October 2, and cross-checked selected Codex session records, macOS power events, current adapter code and the current Dashboard reducer. The inventory contained 1,780 events, including 19 Run-finished events, 12 Issue-paused events and 12 refutation events. Event counts are not unique delivery counts or failure rates.

This is observational evidence, not a controlled comparison of models or harnesses. Matched phase intervals are wall time. They can include pauses or missing telemetry, and concurrent intervals cannot be summed into Run elapsed time. No speedup percentage is established.

## Findings supporting the Spec

| Observation | Evidence | Planning consequence |
|---|---|---|
| Machine suspension inflated an Implement phase | Middleware Swagger Run `run-1790948391`: 124.1 minutes elapsed, including 96.75 minutes of measured sleep. macOS recorded clamshell sleep around 10:45 and full wake at 12:23 local on October 2. | Report known suspension only with provenance; otherwise keep gaps unknown. No power-setting automation is required. |
| Host ended before consuming its child result | Middleware NestJS Run `run-1790885229`: recovered Critic started at 21:00:53 UTC, Host turn ended at 21:01:00, Critic finished at 21:05:15, and Issue completion followed another operator message at 23:16. | Preserve Host responsibility for pending launched work while its capability remains available. |
| CLI parser rejects the emitted effort option | At the inspected revision, the adapter emits `codex exec ... --effort medium`; installed Codex 0.160.0 rejects it with exit code 2, even with help-only parsing. | Verify invocation grammar against the actual CLI, and keep generic role effort translation at the adapter boundary. |
| Existing tests certify the incompatible command | Two narrow existing dispatch tests passed while the actual parser rejected the argument. Their assertions/fake CLI expected the same unsupported form. | Fakes remain useful for injected failures but cannot be sole compatibility evidence. |
| Injected-runner probe loses capture | The default version probe succeeded; injecting a subprocess-compatible runner failed with an empty version string because the first call omitted capture/text arguments. | Use one consistent runner I/O contract for both probes and execution. |
| External prerequisites recur across correction cycles | MyShopList `run-1790692539` repeatedly lacked Docker and remote protection proof; SaaS `run-1790612567` lacked deployment proof for trusted client-IP handling. Both also contained genuine code findings. | Distinguish external verification waits from actionable corrections, and preserve actual acceptance requirements. |
| Pause time and approval state are misrepresented | Replaying NestJS events produced 1,735 seconds attributed to Critic after a successful span of roughly 4.4 minutes. Pause did not close its phase clock; Critic finish unconditionally set operator waiting. | Preserve total elapsed time while separating known pause and result-handling states; honor real configured human gates. |

## Causal qualifications

- About 77 minutes of machine sleep also overlapped the 131.6-minute NestJS result-to-completion gap. These intervals must not be added or described as fully recoverable latency. The result was available for more than 36 minutes before that sleep began.
- Removing the entire 101.4-minute Swagger event gap would incorrectly exclude time after full wake. Approximately 27.4 minutes of wall time remained outside the measured sleep intervals; that is not a pure inference measurement.
- The unsupported effort option is a reproduced current defect, not a demonstrated cause of every historical pause. Some Runs used custom wrappers or omitted explicit effort.
- The historical strict-output schema error arose in a manually constructed CLI invocation. The inspected default command builder did not itself pass the native schema option.
- Review and Critic found substantive defects, including architectural bypasses and unsafe proxy handling. Their independence remains required.
- Measured Swagger checks took roughly 30–40 seconds per invocation. Repeated checks and large context may still be worth optimizing later, but those observations do not explain the largest wall-time gaps.

## Reproducible acceptance basis

Use the selected installed CLI's help/parser path to verify emitted options without a model request. Compare real parser behavior with existing unit/fake coverage. Exercise the public dispatcher with an ordinary subprocess-compatible runner and a bounded selected-profile invocation under approved execution settings. Replay a synthetic equivalent of the pause/result-ready historical trace through the public Dashboard data/report interface, then verify its rendered states with Playwright.

Historical machine-local logs support the diagnosis but are not required test fixtures. New automated proofs must use disposable repository fixtures and synthetic event/input data; keep prompts, credentials, raw command output and source diffs outside the Run log. The delivery revision and actual selected execution capability must be named in future evidence.

## Source provenance

The full read-only audit package from October 2 remains in the current conversation's temporary artifact directory, `gantry-run-analysis-2026-10-02-v2`, with the report, sanitized measurements, power-event extract and reproduction results. This durable summary records the findings needed to implement the Spec without depending on that temporary directory or an operator's private session archive. It does not claim that the old observations revalidate a future CLI version or live account capability.
