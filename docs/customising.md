# Customising

Almost everything with a judgment baked into it is replaceable. This page
covers the seams, roughly in order of how often you will reach for them.

## Routing

Routing maps `(dimension, level)` to a reviewer role. The shipped
`DEFAULT_ROUTING` is a plausible studio structure, not a recommendation.

```python
from ai_use_case_context import UseCaseContext, RiskDimension, RiskLevel

MY_ROUTING = {
    (RiskDimension.LEGAL_IP, RiskLevel.HIGH): "Business Affairs",
    (RiskDimension.SECURITY, RiskLevel.HIGH): "Head of InfoSec",
}

ctx = UseCaseContext(name="Shot 0100", routing_table=MY_ROUTING)
```

Three behaviours worth knowing:

- **A partial table is fine.** Anything it does not cover falls through to
  `Unassigned`, or — for a finding from an enforceable source — to that
  authority's suggested clearance role.
- **An empty table means "assign nothing".** `routing_table={}` is honoured as
  written; it is not treated as "use the defaults".
- **Your table always wins.** The suggested clearance role only ever fills a
  gap your table left.

Each context gets its own copy, so mutating one context's routing does not
reconfigure another.

## Rules

Every rule set is a plain list of dataclasses. Inspect them, filter them,
reorder them, or replace them:

```python
from ai_use_case_context import (
    DEFAULT_CAPABILITY_RULES, CapabilityRule, CapabilityProfile, RegionProfile,
    TransformationClass, ControlMode, LikenessPresence, RiskDimension, RiskLevel,
    Authority, AuthoritySource,
)

# Drop one you do not want
without_authorship = [
    r for r in DEFAULT_CAPABILITY_RULES if r.rule_id != "THIN_HUMAN_DIRECTION"
]

# Add one of your own
house_rule = CapabilityRule(
    rule_id="VOICE_IN_ANY_GENERATED_OUTPUT",
    title="House policy: performer voice in any generated output",
    applies=lambda r: (
        r.likeness is LikenessPresence.VOICE
        and r.transformation.introduces_new_content
    ),
    dimension=RiskDimension.LEGAL_IP,
    level=RiskLevel.CRITICAL,
    authority=Authority.BINDING_CONTRACT,
    source=AuthoritySource(
        body="Internal policy AI-07",
        authority=Authority.BINDING_CONTRACT,
        citation="Voice usage standing order",
    ),
    describe=lambda r: (
        f"Region '{r.region}': performer voice appears in generated output. "
        f"House policy requires talent relations sign-off before any use."
    ),
)

profile = CapabilityProfile(name="Dub")
profile.add_region(RegionProfile(
    region="dialogue",
    transformation=TransformationClass.SYNTHESIS,
    control=ControlMode.CONDITIONED,
    likeness=LikenessPresence.VOICE,
))

ctx = UseCaseContext(name="Dub pass")
profile.derive_flags(ctx, rules=without_authorship + [house_rule])
```

The same shape applies to `IntakeRule`, `OperationalRule`, `SourcingRule`,
`VendorRule`, and `ProvenanceRule`. Their `applies` and `describe` callables
take different arguments — see
[Reference: rules](reference-rules.md) for what each set receives.

Two conventions worth keeping when you write your own:

- **Describe the finding, do not conclude.** Say what was observed and what
  needs determining, not that a particular agreement applies.
- **Set an honest authority.** If your rule expresses a house preference, it is
  `TECHNICAL_STANDARD` or `EMERGING`, not `STATUTE`. Authority drives clearance
  routing, and inflating it routes ordinary decisions to counsel.

## Material sensitivity

`IPClass` is deliberately unordered — which class is most restricted is your
judgment. That judgment lives in one frozenset:

```python
import ai_use_case_context.intake as intake_mod
from ai_use_case_context import IPClass

intake_mod.RESTRICTED_IP_CLASSES = frozenset({
    IPClass.PRE_RELEASE_IP,
    IPClass.TALENT_MATERIAL,
})
```

Rules that ask "is this restricted?" consult it, so changing it changes what
the operational and intake rules consider worth flagging.

## Derivation thresholds

The bands mapping a recorded guidance value onto a `TransformationClass` are a
convention. Calibrate them against your own pipeline:

```python
from ai_use_case_context import DerivationThresholds, PipelineRecord, GuidanceSignal

record = PipelineRecord(
    stage="Shot 0100",
    thresholds=DerivationThresholds(
        enhancement_at=0.99,
        repair_at=0.90,
        modification_at=0.60,
        synthesis_below=0.60,
    ),
)
record.add_signal(GuidanceSignal(region="r", guidance_strength=0.95))
profile = record.to_capability_profile()
```

Thresholds must be ordered and within `[0,1]`; the constructor enforces both.
They serialize with the record, so a classification can always be read back
against the numbers that produced it.

## Risk dimensions

Beyond the six built-ins, define your own — they work everywhere the built-ins
do, including routing, dashboards, serialization, and the web UI:

```python
from ai_use_case_context import custom_dimension, UseCaseContext, RiskLevel

SUSTAINABILITY = custom_dimension("SUSTAINABILITY", "Environmental Impact")

ctx = UseCaseContext(name="Render farm")
ctx.flag_risk(SUSTAINABILITY, RiskLevel.MEDIUM, "Compute budget not modelled")
```

The security presets (`TPN`, `VFX`, `Enterprise`) are prebuilt bundles of
custom dimensions plus routing — see `security_profile()` and
`apply_security_profile()`.

## The lexicon

The starter lexicon covers terms that recur across productions. Extend it with
your own agreements and jurisdictions:

```python
from ai_use_case_context import (
    default_lexicon, TermDefinition, AuthoritySource, Authority,
)

lexicon = default_lexicon()
lexicon.add(TermDefinition(
    term="Digital Replica",
    source=AuthoritySource(
        body="Our 2026 talent agreement template",
        authority=Authority.BINDING_CONTRACT,
        citation="Schedule C",
    ),
    summary="Definition as negotiated for this production slate.",
))

for conflict in lexicon.conflicts():
    print(conflict.describe())
```

Adding a definition that differs from an existing one is the point, not a
problem — `conflicts()` exists to surface exactly that.

## External vocabularies

If you need to speak another body's terms, register a crosswalk. Nothing in the
framework's logic keys on external names, so this is a data change:

```python
from ai_use_case_context import (
    VocabularyMapping, register_vocabulary, TransformationClass, ControlMode,
)

mapping = VocabularyMapping(
    name="partner-vocabulary",
    version="1.0",
    terms={
        TransformationClass.EXTRACTION: "Readout",
        TransformationClass.CONVERSION: "Readout",
        ControlMode.COMPOSED: "Assembled",
    },
)
register_vocabulary(mapping)

mapping.unmapped(TransformationClass)   # check coverage before relying on it
```

Check `unmapped()` before trusting a crosswalk. An unmapped member means the
external vocabulary has no term for a case you can express, and translated
output is silently lossy there — which is why `to_external()` renders unmapped
members as `None` rather than falling back to our names.

## Vendor scoring weights

If you keep using the legacy composite for vendor comparison, its weights and
tier thresholds are configurable — and now validated:

```python
from ai_use_case_context import (
    evaluate_vendor, VendorScorecard, ScorecardDimension, DimensionScore,
)

weights = {
    ScorecardDimension.DATA_PROVENANCE: 0.40,
    ScorecardDimension.GOVERNANCE_SECURITY: 0.20,
    ScorecardDimension.ETHICS_COMPLIANCE: 0.20,
    ScorecardDimension.TECHNICAL_FIT: 0.10,
    ScorecardDimension.COMMERCIAL_TERMS: 0.05,
    ScorecardDimension.OPERATING_MODEL: 0.05,
}
result = evaluate_vendor(
    VendorScorecard(vendor_name="V", data_provenance=DimensionScore(score=80)),
    weights=weights,
)
```

Weights must sum to 1.0 and tier thresholds must cover every classified tier;
both raise `ValueError` otherwise rather than silently falling back.
