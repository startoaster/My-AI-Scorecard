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

That was tried and removed. Two reasons:

**It cannot work.** Standing comes from an organization's delegation of
authority and its identity systems, neither of which a library can see. Any
check would be bypassed by assigning `status` directly, so it bought false
assurance rather than control.

**It breaks the contract.** `is_blocked()` reports and lets the caller decide.
A method that raises instead is inconsistent with everything around it, and
pushes callers into working around the library.

What replaced it is visibility:

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
- **Software licensing of the tool itself.** `sourcing.py` records where the
  weights came from and how the tool is packaged, and `ModelOrigin` carries the
  licence position of the *model*. Nothing records the licence on the
  *implementing source code* — permissive, restrictive, closed, or absent
  altogether. An unlicensed reference implementation from a paper confers no
  usage rights at all, and the framework currently has nowhere to say so.

## What it draws on

Where a rule cites a statute, an agreement, or a standard, the source travels
with the finding on its `AuthoritySource`. [Attributions](attributions.md)
rolls all of them up, together with the external frameworks that influenced
the design. Naming a standard there is not a claim of conformance with it.
