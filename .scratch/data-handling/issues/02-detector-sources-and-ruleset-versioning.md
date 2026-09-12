# Detector sources and ruleset versioning

Type: issue
Status: ready-for-agent
Slice: data-handling#02
Spec: [`../spec.md`](../spec.md) (spec 04, wave 0)
Created: 2026-09-12

## Parent

[`.scratch/data-handling/spec.md`](../spec.md)

## What to build

The three declared detector sources, in precedence order: the literal values of environment variables referenced by the effective configuration (matched as values, never stored), a versioned catalog of pattern detectors for common shapes (bearer tokens, API key formats, PEM private key blocks, signed URL query parameters, connection strings with embedded credentials), and the repository's configured secret scanner rules where one exists, so redaction agrees with the scanner the repository already trusts.

The ruleset version is emitted with every outcome and is derived from the composed source set, so adding a repository scanner changes the version.

This is the one place in the spec where tests bind to the pipeline interface directly rather than through a sink. It is an **authorized exception** to the standing test seam, granted explicitly by the spec: enumerating detector cases through operations would be slow and would obscure what is being asserted. Those tests assert only on the outcome value, never on internals, and the slice still carries one end-to-end criterion per detector source.

## Acceptance criteria

- [ ] An output containing the value of an environment variable named in the effective configuration is redacted, and the variable's value appears nowhere in the stored record or in the metadata.
- [ ] Each pattern detector in the catalog has a positive case and a negative near-miss case, and a detector's identity appears in metadata only when it hit.
- [ ] A repository with a configured secret scanner contributes its rules; the resulting ruleset version differs from the same repository with no scanner configured.
- [ ] Two outputs redacted under the same source set record the same ruleset version; changing any source changes it.
- [ ] At least one detector from each of the three sources is proven end-to-end through a sink, not only through the pipeline interface.

## Blocked by

- `data-handling#01` — the pipeline, the `RedactionOutcome` shape, and the redaction metadata this slice populates.
- `config-and-snapshot#01` — the effective configuration document and its environment variable references, which supply detector source 1.
- `repository-readiness#03` — secret scanner rule source reference (scanner identity and resolved rule-configuration location), consumed as detector source 3.
