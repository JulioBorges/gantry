# Enclosing-symbol derivation and the fallback ladder

Type: issue
Status: ready-for-agent
Slice: verification-adapters#02
Spec: [`../spec.md`](../spec.md) (spec 12, wave 3)
Created: 2026-09-12

## Parent

[`.scratch/verification-adapters/spec.md`](../spec.md)

## What to build

Gantry-side derivation of the enclosing symbol from the file and the reported line using tree-sitter, with grammars for the languages in the approved adapter set. This completes the finding identity tuple, promoting it from `rule` + `path` + `contentAnchor` to the settled `rule` + `path` + `symbol` + `contentAnchor` with the message still excluded. The grammar version travels in the report alongside the tool version and participates in the reuse key.

Tree-sitter is an engine dependency shared by every adapter rather than reimplemented per tool; its runtime is installed and proven by `release-engineering#01`, and this slice owns only the grammar set. Adapters are untouched — they never derive identity themselves — which is what lets the adapter slices and the validity, stability, and resource slices run concurrently with this one.

Complete and order the fallback ladder: symbol-anchored first, then no-grammar (`rule` + `path` + `contentAnchor`), then no-location (count per identity). Every finding records which rung it used.

## Acceptance criteria

- [ ] A finding in a language with a grammar gets a symbol-anchored identity; the derivation used is recorded on the finding.
- [ ] A tool that reports no symbol still produces per-occurrence identities, because the symbol comes from the file and line.
- [ ] A file whose language has no available grammar falls back to `rule` + `path` + `contentAnchor` and records that fallback rather than failing.
- [ ] Identity is unchanged when the tool's message text changes between versions, and unchanged when a function is moved within a file without its body changing.
- [ ] Symbol derivation is deterministic across two runs of the same file; a grammar that parses wrongly still parses consistently.
- [ ] Grammar version is present on every report and participates in the reuse key.

## Blocked by

- `verification-adapters#01` — the normalized finding shape, the content anchor, and the recorded derivation field this ladder extends.
- `release-engineering#01` — the tree-sitter engine dependency installed and proven to parse.
