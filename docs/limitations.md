# Limitations

What this framework deliberately does not do, and why each boundary is where it
is. Read this before building anything that depends on the framework being
stricter than it is.

## It does not decide whether anything is acceptable

The framework raises findings, routes them, and records what happened to them.
It never concludes that a use is permitted, that a contract applies, or that a
risk is acceptable. Those determinations belong to people with standing to make
them.

This shows up in the wording of the rules themselves. A performer in
synthesized output produces a finding that says the replica-versus-alteration
question *turns on facts this framework does not evaluate*, and that a
determination is required — not that a particular agreement applies.

## It does not enforce who may clear a finding

`accept_risk()` records an acceptance. It does not check whether the person
accepting has authority to.

That is deliberate, for two reasons:

**It cannot work.** Standing comes from an organization's delegation of
authority and its identity systems, neither of which a library can see. Any
check would be bypassed by assigning `status` directly, so it would buy false
assurance rather than control.

**It breaks the contract.** `is_blocked()` reports and lets the caller decide.
A method that raises instead is inconsistent with everything around it, and
pushes callers into working around the library.

What it does instead is make the gap findable:

```python
from ai_use_case_context import (
    UseCaseContext, RiskDimension, RiskLevel, Authority,
)

ctx = UseCaseContext(name="Example")
flag = ctx.flag_risk(
    RiskDimension.LEGAL_IP, RiskLevel.HIGH, "Contract question",
    authority=Authority.BINDING_CONTRACT,
)
flag.accept_risk("proceeding")          # allowed

ctx.get_unattributed_acceptances()      # ... and findable
```

If you want acceptance actually gated, express it in a `GovernanceHook`, where
it sits under your control and can consult your identity system. `ComplianceGate`
exists for this.

## It does not decide "sufficient human authorship"

No industry body or settled authority defines how much human contribution
sustains copyright in a work incorporating AI output. The question is live in
case law.

So `AuthorshipRecord` produces the *record* a court or registry would evaluate,
not a verdict. `evidence_points` is a count of recorded contributions, not a
score, and `thin_evidence_regions()` is a reporting cut-off rather than a
sufficiency threshold. Thin does not mean insufficient — it means a reviewer
will find little to point at.

## It is not a substitute for legal advice

The starter `Lexicon` contains short **paraphrases** of public sources, included
so routing rules have something to key on. They are not contract or statutory
language. The rule descriptions name regimes and agreements in general terms
("the applicable agreement", "applicable regime depends on where the work is
exploited") precisely because the framework cannot know which one governs your
production.

## It does not know your jurisdiction

Several facts only matter somewhere. `CopyrightAssessment` reports its two EU
fields in `gaps` but deliberately keeps them out of `risk_level`, because
whether they matter depends on where the work is exploited and the object
carries no jurisdiction to weigh that against.

Where a rule does cite a jurisdictional regime, it says so on the
`AuthoritySource` and leaves the applicability question open.

## Thresholds are conventions, not measurements

The guidance-strength bands that map a recorded value onto a
`TransformationClass` encode a defensible reading, not an empirical finding.
Calibrate them against your own pipeline:

```python
from ai_use_case_context import DerivationThresholds, PipelineRecord

record = PipelineRecord(
    stage="Shot 0100",
    thresholds=DerivationThresholds(
        enhancement_at=0.99, repair_at=0.90,
        modification_at=0.60, synthesis_below=0.60,
    ),
)
```

They serialize with the record, so a classification can always be read back
against the thresholds that produced it.

The same applies to `RESTRICTED_IP_CLASSES`, which encodes a judgment about
which material carries consequence beyond the production. `IPClass` itself is
deliberately **unordered** — ranking it would assert a hierarchy no source
supplies.

## The dimension set is a convention

The six built-in `RiskDimension` members are a starting shape, not a sourced
taxonomy. No standards body supplies this partition. Every *rule* carries an
`AuthoritySource` naming what stands behind that finding; the dimensions
themselves carry nothing, and the framework does not imply otherwise. Add your
own with `custom_dimension()`.

Two of the six have **no default rules at all**:

| Dimension | Default rules |
| --- | --- |
| `BIAS` — Bias / Fairness | 0 |
| `SAFETY` — Safety / Harmful Output | 0 |

They name real concerns, and this framework derives nothing into them.
Assessing representational harm or harmful output requires evidence about how
a model behaves — evaluation results, red-team findings, measured output
distributions. This framework records supply, deployment, and output-role
facts, and holds none of that. A finding raised there on the facts available
would be an assertion dressed as a derivation.

They stay in the enum because they are legitimate places to route a flag you
raise by hand, or one your own rules produce from evidence you do hold.
`tests/test_packaging.py` pins the count at zero so the claim cannot go stale.

## Crowd or vendor input is a prior, never a clearance

If you feed the framework practitioner consensus or vendor self-assessment,
treat it as evidence that can *raise* a finding and never as something that
clears one. An average of opinions is not a legal determination, and a vendor's
own account of its training data is a claim rather than a fact.

## The legacy composite is not an approval basis

`evaluate_vendor()` is retained because comparing vendors on documentation
quality is genuinely useful. Its weighted composite is compensatory and will
rate a vendor in active copyright litigation as `PREFERRED`. Use
`VendorScorecard.derive_flags()` and `tier_from_flags()` for anything that
gates a decision.

## It is not the last word, and knows it

Both the Visual Effects Society and MovieLabs have work in progress on
classifying and communicating AI use in production. That work is unpublished
at the time of writing, and nothing from it is reflected here — but it is
reasonable to expect that some of what this framework names, the industry will
eventually name differently, and with more standing behind it.

Two design choices exist so that adopting a published vocabulary later is a
data change rather than a rewrite:

- **Nothing in the logic keys on external names.** Rules, routing, and storage
  use this project's own enum members. A `VocabularyMapping` crosswalks them
  onto anyone else's terms without touching any of it. See
  [Customising](customising.md).
- **Classes are finely split.** Where an external vocabulary merges two of
  ours, the crosswalk maps both onto its one term. Merging is always
  expressible after the fact; splitting is not.

Expect the crosswalks, not a migration.

## What it does not cover at all

- **Agentic workflows** — planning, orchestration, and tool selection performed
  dynamically by an AI system. No published framework covers this well yet, and
  neither does this one.
- **Runtime enforcement** — nothing here inspects or intercepts a running
  pipeline. It records what a pipeline reports.
- **Identity, access control, and secrets** — entirely out of scope.
- **`compliance.py` does not derive flags.** ISO 42001, NIST AI RMF, and EU AI
  Act assessments still produce scores and string gaps that nothing consumes,
  and must be transcribed by hand into flags. The other assessment modules have
  been converted; this one has not yet.
