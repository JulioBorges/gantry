# Spec structural validation and requirement review

Type: spec
Status: ready-for-agent
Map: [`.scratch/gantry-v4/map.md`](../gantry-v4/map.md) (spec 08, wave 2)
Source: `PRD.md` §7.2
Created: 2026-09-11

## Problem Statement

Everything downstream of a spec inherits its defects. A slice cut from an ambiguous requirement
produces acceptance criteria nobody can verify, a builder implements a plausible reading of an
underspecified behavior, and a gate passes because the criteria it checks were the wrong ones. The
failure is silent: every step reports success.

`PRD.md` splits the response into two parts that are easy to collapse into one. Structural validation
is mechanical and pass or fail — required sections present, formal contracts declared, criteria
identifiable, at least three Given-When-Then scenarios, explicit security and architecture invariants —
and explicitly "rather than a weighted quality score". Requirement review is semantic and belongs to
the Requirement Critic: ambiguity, coherence, whether the requirements describe verifiable behavior.
The PRD is blunt that one does not substitute for the other: "section presence or a structurally valid
contract does not establish semantic quality". And neither is approval: technical readiness "is not
operator approval or authorization to start AFK execution".

The second problem is that specs already exist. A repository using another skill's template has a
canonical document its team maintains, and the PRD forbids demanding a rewrite: inspect it, identify
gaps, "propose only the missing complements in that original document while preserving its format",
and assess mapped content rather than requiring identical headings. Getting this wrong produces the
duplicate documentation tree that spec 06 exists to avoid, one layer up.

The mechanisms are all deferred: "exact lint rules, supported contract formats, criterion identifiers,
and the critic result schema remain to be specified", and "supported format mappings and normalization
mechanics remain to be specified".

## Solution

`gantry lint-spec` normalizes a spec document into a canonical content model — required content
identified by what it contains rather than by the heading above it — and evaluates declared structural
rules against that model. Each rule has a stable identity and produces a structured finding with a
location, so results are comparable across runs and across documents. Nothing is scored; every rule is
pass or fail.

The Requirement Critic runs as a GTP role against the same normalized model plus the structural
findings, and returns semantic findings in declared classes with severities. It is not optional: the
PRD's optional reviewer is the delivery-time adversarial critic, and the PRD review explicitly
corrected the impression that all LLM reviewers are opt-in.

Technical readiness is the conjunction of both: all mandatory structural rules pass and a valid critic
review returns no blocking findings. Readiness is recorded against the spec's content hash, so editing
the spec invalidates it. Readiness authorizes slicing and nothing else.

For an existing document, normalization maps its sections onto canonical content, and gaps become
proposed complements written into that same document in its own format. Adaptation never rewrites a
document into a Gantry template and never grants approval.

## User Stories

1. As an operator, I want my spec checked mechanically before anyone reasons about it, so that obvious gaps are caught for free.
2. As an operator, I want structural results as pass or fail per rule, so that I fix specific things rather than chase a score.
3. As an operator, I want each structural rule to have a stable identity, so that I can discuss, suppress, or track a rule over time.
4. As an operator, I want each finding to name its location in my document, so that I can go straight to the problem.
5. As an operator, I want a required problem and context section enforced, so that a spec states what it is solving.
6. As an operator, I want explicit non-goals enforced, so that scope is bounded before anyone slices it.
7. As an operator, I want formal contracts or schemas required, so that interfaces are stated rather than implied.
8. As an operator, I want declared contracts structurally validated, so that a malformed schema is caught before an agent implements against it.
9. As an operator, I want a contract in an unsupported format flagged rather than silently accepted, so that I know it was not actually validated.
10. As an operator, I want acceptance criteria required to be individually identifiable, so that later work can refer to a specific criterion.
11. As an operator, I want stable criterion identifiers required, so that "criterion three" means the same thing after an edit.
12. As an operator, I want at least three Given-When-Then scenarios required, so that behavior is described concretely rather than abstractly.
13. As an operator, I want scenarios parsed for structure, so that a malformed scenario is caught even when its prose reads well.
14. As an operator, I want explicit security invariants required, so that security is stated rather than assumed.
15. As an operator, I want explicit architecture invariants required, so that boundaries exist before code is written against them.
16. As an operator, I want structural validation to run without any model, so that it is fast, deterministic, and free.
17. As an operator, I want semantic review as a separate step, so that I never mistake a well-formatted spec for a well-reasoned one.
18. As an operator, I want the Requirement Critic to identify ambiguity, so that a sentence with two readings is fixed before it is implemented twice.
19. As an operator, I want it to identify incoherence between sections, so that a spec that contradicts itself is caught.
20. As an operator, I want it to identify requirements that cannot be verified, so that no criterion is unfalsifiable.
21. As an operator, I want it to identify false premises, so that a spec built on a wrong assumption is challenged.
22. As an operator, I want critic findings classified and severity-tagged, so that a blocking problem is distinguishable from an advisory note.
23. As an operator, I want the critic to state what it reviewed, so that I know its coverage rather than assuming completeness.
24. As an operator, I want an unavailable or failed critic to leave the spec not ready, so that an infrastructure problem never reads as approval.
25. As an operator, I want the Requirement Critic to be mandatory, so that semantic review is not something I can accidentally skip.
26. As an operator, I want technical readiness to require both structural passing and a clean review, so that neither alone can advance my spec.
27. As an operator, I want readiness recorded against my spec's exact content, so that an edit after readiness invalidates it.
28. As an operator, I want readiness to authorize slicing only, so that it is never confused with approving a plan or starting execution.
29. As an operator, I want my existing spec accepted in its own format, so that adopting Gantry does not mean rewriting my documents.
30. As an operator, I want equivalent content recognized under different headings, so that my structure is respected.
31. As an operator, I want to see how my sections were mapped onto required content, so that I can correct a wrong mapping.
32. As an operator, I want to override the mapping, so that normalization is a proposal rather than a verdict.
33. As an operator, I want gaps proposed as complements to my original document, so that nothing is duplicated elsewhere.
34. As an operator, I want proposed complements to preserve my document's format, so that the result still looks like my team's spec.
35. As an operator, I want adaptation to grant no approval, so that filling a gap is not consent to execute.
36. As an operator, I want to author a new spec conversationally and have it produced in the structure that passes validation, so that authoring and validation agree.
37. As an operator, I want the authored structure to be the one my repository already uses when it has one, so that new specs match existing ones.
38. As an operator, I want a spec written to the wrong location rejected, so that documents land where my mapping says.
39. As a host harness, I want structural findings and critic findings as structured data, so that I can present them and drive fixes without parsing text.
40. As a host harness, I want the normalized content model available, so that I can reason about a spec without re-parsing it.
41. As a Gantry implementer, I want structural rules declared as data with stable identities, so that adding a rule does not change existing ones.
42. As an auditor, I want each readiness record to name the rule version, critic review, and content hash that produced it, so that readiness is reconstructible.

## Implementation Decisions

### Normalization before validation

Validation never reads headings directly. A normalizer produces a canonical content model, and rules
evaluate the model:

```ts
type NormalizedSpec = {
  source: { path: string; contentHash: string; format: SpecFormat };
  mapping: Array<{ canonical: CanonicalSection; sourceHeading: string; confidence: "declared" | "matched" | "absent" }>;
  problemContext?: Block;
  nonGoals?: Block;
  contracts: DeclaredContract[];
  criteria: Array<{ id: string; text: string; location: Location }>;
  scenarios: Array<{ given: string[]; when: string[]; then: string[]; location: Location }>;
  securityInvariants?: Block;
  architectureInvariants?: Block;
  userStories: Array<{ id: string; text: string }>;
  unmapped: Array<{ heading: string; location: Location }>;
};
```

`SpecFormat` is a declared set with a mapping table per format: the `to-spec` structure this repository
uses, the Gantry template, and a generic fallback that matches on content signals. Format is detected,
shown, and overridable. `confidence: "declared"` means the repository or operator stated the mapping;
`"matched"` means a signal matched; `"absent"` means required content was not found.

Content is assessed, not headings. A document whose non-goals live under a heading called "Out of
Scope" satisfies the non-goals requirement, because the mapping resolved it. `unmapped` sections are
reported but never penalized — a spec is allowed to contain more than Gantry requires.

### Structural rules

Rules are declared data with stable identities, each producing findings in the same structured shape the
rest of the system uses:

| Rule | Requirement |
|---|---|
| `SPEC-PROBLEM` | Problem and context content present and non-trivial |
| `SPEC-NONGOALS` | Explicit non-goals present |
| `SPEC-CONTRACT-PRESENT` | At least one formal contract or schema declared |
| `SPEC-CONTRACT-VALID` | Each declared contract passes structural validation for its format |
| `SPEC-CONTRACT-FORMAT` | Each declared contract is in a supported, validatable format |
| `SPEC-CRITERIA-PRESENT` | Acceptance criteria present and individually identifiable |
| `SPEC-CRITERIA-ID` | Every criterion carries a stable identifier |
| `SPEC-SCENARIOS-COUNT` | At least three Given-When-Then scenarios |
| `SPEC-SCENARIOS-PARSE` | Every scenario parses into given, when, and then parts |
| `SPEC-SECURITY` | Explicit security invariants present |
| `SPEC-ARCHITECTURE` | Explicit architecture invariants present |
| `SPEC-LOCATION` | The document sits at the mapped canonical location |

All are mandatory and all are pass or fail. There is no weighting and no aggregate. `SPEC-CONTRACT-FORMAT`
exists so that an unvalidatable contract is a visible finding rather than a silent pass: the operator
either converts it or explicitly declares its format, and in the latter case the finding records that no
structural validation was performed.

Supported contract formats, each with a structural validator: JSON Schema, TypeScript type
declarations, and OpenAPI fragments. Anything else is `SPEC-CONTRACT-FORMAT`.

Criterion identifiers are required rather than generated, because a generated identifier renumbers when
a criterion is inserted and every downstream reference breaks. When identifiers are missing, adaptation
proposes adding them — an edit the operator accepts once, after which they are stable.

Structural validation runs with no model and no network.

### Requirement review

The Requirement Critic is a GTP role receiving the normalized model, the applicable rules, and the
structural findings, and returning:

```ts
type RequirementFinding = {
  class: "ambiguity" | "incoherence" | "unverifiable" | "false_premise" | "missing_non_goal" | "scope_undefined";
  severity: "blocker" | "warning";
  location: Location;
  statement: string;        // what is wrong
  rationale: string;        // why it matters
};

type RequirementReview = {
  findings: RequirementFinding[];
  coverage: string;         // what was reviewed and what was not
  status: GtpStatus;
};
```

A review is valid when the envelope validates, coverage is stated, and status is `complete`. An
unavailable critic, a failed execution, or a missing or malformed result leaves the spec not ready and
records the failure; there is no static-only fallback for this role. Infrastructure failures follow the
separate retry allowance; protocol failures follow spec 03 and are not reclassified as infrastructure.

The critic adds findings. It has no field capable of clearing a structural finding, for the same reason
the adversarial critic has none in spec 03: the shape enforces the rule.

### Technical readiness

```ts
type TechnicalReadiness = {
  spec: { path: string; contentHash: string };
  structural: { ruleSetVersion: string; allMandatoryPassed: boolean; findings: Finding[] };
  review: { submissionId: string; blockingFindings: number };
  ready: boolean;           // allMandatoryPassed && review valid && blockingFindings === 0
  snapshot: SnapshotId;
};
```

Readiness is persisted and bound to the content hash. Any edit invalidates it, both structural results
and review, because a semantic review of an earlier draft says nothing about the current one. Readiness
authorizes slicing. It is not planning approval, and it does not authorize builder dispatch — which is
also why it is computed by a non-operator channel safely: nothing it produces requires consent.

### Adaptation of existing specs

Adaptation produces proposed complements, never a rewrite:

```ts
type SpecComplement = {
  canonical: CanonicalSection | "criterion_identifiers";
  reason: string;                    // which rule is unsatisfied
  proposedInsertion: { location: Location; content: string; styleBasis: string };
};
```

`styleBasis` records which existing part of the document the proposed content was patterned on, so the
insertion matches the document's own conventions rather than importing a template's voice. Complements
are applied to the original document at its canonical location. No parallel Gantry copy is created, and
no heading is renamed to match a template.

Applying a complement does not establish readiness — validation runs again afterwards — and it grants no
approval.

### Authoring

Authoring produces a spec in the structure the repository already uses when one is detected, and in the
`to-spec` structure otherwise, since that is the structure this repository's own skills produce and the
PRD names it as the basis. Authored specs are written to the mapped canonical location from spec 06;
writing elsewhere is `SPEC-LOCATION`.

## Testing Decisions

**What makes a good test here.** Tests feed real spec documents — as fixture files in a temporary
repository — through the lint and review operations and assert on the normalized mapping, the set of
rule identities that failed, readiness, and the document's byte content after adaptation. Assertions
are on rule identities rather than on message text, so rule wording can change freely.

**The seam.** The same seam as spec 01, with a fake harness driver scripted to return Requirement Critic
results: clean, with blocking findings, with warnings only, malformed, and absent. The normalizer is
exercised through the lint operation rather than directly, because a normalizer that produces a correct
model the rules do not consult would pass a direct test and fail the product.

**Fixtures.** Documents covering: a spec in this repository's `to-spec` structure; one in the Gantry
template; one with non-goals under an "Out of Scope" heading; one missing non-goals entirely; one with a
malformed JSON Schema; one with a contract in an unsupported format; one with unnumbered criteria; one
with two Given-When-Then scenarios; one with a scenario missing its `then`; one with no security
invariants; one with extra sections Gantry does not require.

**Modules under test.** Format detection and mapping, the normalizer, each structural rule, contract
validators per format, the review role's result validation and readiness computation, content-hash
binding and invalidation, complement generation and application, and authoring location enforcement.

**Scenarios that must exist:**

- A document with non-goals under "Out of Scope" passes `SPEC-NONGOALS`; the mapping shows the resolution.
- A document missing non-goals fails `SPEC-NONGOALS` with a location.
- Extra unrequired sections appear in `unmapped` and cause no failure.
- A malformed JSON Schema fails `SPEC-CONTRACT-VALID`; a contract in an unsupported format fails `SPEC-CONTRACT-FORMAT`, and an operator-declared format records that no structural validation was performed.
- Two scenarios fail `SPEC-SCENARIOS-COUNT`; a scenario missing `then` fails `SPEC-SCENARIOS-PARSE`.
- Criteria without identifiers fail `SPEC-CRITERIA-ID`; after applying the identifier complement, they pass and the identifiers are unchanged by a later unrelated edit.
- Structural validation completes with no driver invoked, verified by a fake that fails the test if called.
- All structural rules passing with a review carrying a blocking finding yields `ready: false`.
- All structural rules passing with a clean valid review yields `ready: true`.
- A review with warnings only does not block readiness.
- An absent or malformed review leaves `ready: false` and records the failure; it is not a static-only pass.
- A critic infrastructure failure consumes the infrastructure allowance and not a correction attempt.
- Editing the spec after readiness invalidates both the structural result and the review.
- Readiness does not authorize dispatch, and does not substitute for planning approval.
- Adaptation of an existing document inserts complements in place; the document's other bytes are unchanged and no parallel copy exists.
- A proposed complement records the `styleBasis` it patterned itself on.
- Applying complements does not set readiness and grants no approval.
- An authored spec written outside the mapped location fails `SPEC-LOCATION`.
- Authoring in a repository with a detected spec format produces that format.

## Out of Scope

- **Operations, persistence, budgets, channels** (spec 01) and **snapshot binding** (spec 02).
- **Envelope contracts and role validation** (spec 03): the Requirement Critic's envelope shape, status semantics, and protocol failure handling.
- **Artifact location mapping and detection** (spec 06): where specs live. This spec enforces the mapping; it does not resolve it.
- **Slicing, context budget estimation, dependencies, planning approval, amendments** (spec 09): everything after readiness. This spec ends at "ready to slice".
- **PBI-level linting** (spec 09): `lint-pbi` and its rules.
- **Delivery-time adversarial review** (spec 13): the optional critic that reviews a diff. This spec's critic reviews requirements, and the two must not be conflated — the PRD review corrected exactly that confusion.
- **Executable architecture and security checks** (specs 12, 13): this spec requires invariants to be stated; enforcing them against code is elsewhere.
- **Redaction and retention of critic output** (spec 04).
- **Skill packaging and distribution** (spec 05).

Out of scope by product decision:

- A weighted spec quality score. §7.2 replaces it with pass-or-fail rules, and the glossary marks "spec quality score" as a term to avoid.
- A mandatory Gantry spec template. §7.2 requires accepting existing formats without rewrite.
- Making the Requirement Critic optional. The PRD review explicitly corrected the impression that all LLM reviewers are opt-in; only the delivery adversarial reviewer is.
- Generating criterion identifiers automatically. Generated identifiers renumber and break downstream references.

## Further Notes

**Binding decisions.** Nothing here contradicts either ADR. The critic's structural inability to clear a
structural finding mirrors the same decision in spec 03, and both exist because a rule enforced by shape
cannot be forgotten.

**Glossary alignment.** Spec Structural Validation, Requirement Review, and Spec Adaptation follow
`CONTEXT.md`, including the terms it marks to avoid: structural validation is not a spec quality score
and not spec approval; requirement review is not a structural lint; adaptation is not a mandatory
template rewrite and not automatic approval.

**Glossary gap for `/domain-modeling`.** Normalized spec model, canonical section, and spec complement
are introduced here without entries and should get them.

**Where the risk actually sits.** Normalization is the part that will be wrong most often, for the same
reason detection is in spec 06: real documents vary more than any mapping table. The mitigation is the
same and deliberately so — the mapping is shown, overridable, and improvable by the repository declaring
its own format. The sharper risk is `SPEC-CRITERIA-ID` on an existing document: requiring stable
identifiers means editing a document a team already maintains, and while adaptation makes that a
one-time accepted complement, it is the most intrusive thing this spec asks for. The alternative —
positional criterion references — breaks silently on insertion, which is worse.

**Sequencing note.** This spec depends on spec 03 for the critic role and on spec 06 for the mapping. Its
own output, the normalized model and criterion identifiers, is what spec 09 consumes, so the criterion
identity rule is the piece to settle before starting either — spec 03 already requires stable identities
at PBI approval, and this is where they originate.
