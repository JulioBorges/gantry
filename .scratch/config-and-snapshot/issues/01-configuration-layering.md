# Configuration layering and the effective document

Type: issue
Status: ready-for-agent
Slice: config-and-snapshot#01
Spec: [`../spec.md`](../spec.md) (spec 02, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/config-and-snapshot/spec.md`](../spec.md)

## What to build

The `ConfigStore` module and the configuration schema with all sections declared: host and role routing, context policy (Context Watermark, Initial Context Budget, and the PBI file-count threshold), capacity limits, budgets, Git Workflow Policy, Artifact Location Mapping, verification commands and declared Check Resources, data handling (Data Egress Policy matrix, Telemetry Retention level), dashboard settings, and the `gates.*` section holding blocking thresholds, absolute-rule flags, and the adversarial review mode. The schema carries the approved defaults so a fresh install is already correct: global capacity two, Correction Budget five, Infrastructure Retry allowance three, Context Watermark forty percent, Initial Context Budget fifteen percent.

Layer resolution runs built-in defaults, then the machine-wide file, then the repository override, with fixed merge semantics: objects merge key by key, arrays are replaced wholesale, an explicit `null` in a higher layer clears the inherited value, and an unknown key is a rejection rather than a preserved extension.

The store's read surface returns one resolved immutable document plus per-field provenance naming the supplying layer, reached through a `config.read` operation registered in the shared operation core's catalog, with `gantry config show` as the reading transport. Sections whose semantics belong to other specs are declared and shaped here but not interpreted here; their inner shapes may start as placeholders while the owning spec settles them.

## Acceptance criteria

- [ ] With no files present on either layer, `config.read` returns every approved default and provenance reports the built-in layer for each.
- [ ] A sparse repository override inherits every unstated value; provenance names the repository layer for stated fields and the lower layer for the rest.
- [ ] An array-valued setting stated in the repository override replaces the inherited list rather than appending to it; an explicit `null` clears an inherited value rather than being treated as absent.
- [ ] An unknown configuration key at any layer is rejected, naming the key path and the layer that supplied it.
- [ ] The `gates.*` section is declared and readable through `config.read`, carrying blocking thresholds, absolute-rule flags, and `gates.adversarial.mode`, with provenance per field like every other section.
- [ ] The PBI file-count threshold is declared under context policy, carries its approved default, and is readable through `config.read` with provenance.
- [ ] Tests drive `config.read` through the operation core's `invoke` against layer files written into a temporary home and repository directory; `gantry config show` has one parity test proving delegation.

## Blocked by

- `execution-core#01` — the operation core `invoke` entry point, the catalog registration mechanism, and the rejection-code vocabulary.
