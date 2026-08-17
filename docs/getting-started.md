# Getting started

A working governance record for one shot, in about ten minutes.

This walks through a single realistic case end to end. If you would rather read
about the design first, start with [Concepts](concepts.md).

## Install

```bash
pip install -e .
```

Python 3.9 or later. The core library has no dependencies; the web dashboard
needs Flask (`pip install -e ".[web]"`).

## The case

A set extension behind a performer. The performer is held tightly to the plate
and only relit; the background behind them is generated. It is going into a
commercial release, and the source material is pre-release.

That single shot contains two different governance situations, which is the
point of the example.

## 1. Create a context

Everything attaches to a `UseCaseContext`.

```python
from ai_use_case_context import UseCaseContext

ctx = UseCaseContext(
    name="Shot 0100 — environment extension",
    description="Set extension behind a retained hero performance.",
    workflow_phase="Element Regeneration",
)
```

## 2. Describe what the AI actually does

Classification is **per region**, because "what does this shot do" has two
answers here. A `RegionProfile` classifies one region on two independent axes —
what the operation does to the media, and how much of the recipe the human
supplied.

```python
from ai_use_case_context import (
    CapabilityProfile, RegionProfile,
    TransformationClass, ControlMode, FinalPixelRole, LikenessPresence,
)

capability = CapabilityProfile(name="Environment extension")

capability.add_region(RegionProfile(
    region="hero_actor",
    transformation=TransformationClass.ENHANCEMENT,   # relit, nothing new added
    control=ControlMode.COMPOSED,
    likeness=LikenessPresence.PERFORMANCE,
    final_pixel=FinalPixelRole.DELIVERED_FRAME,
))

capability.add_region(RegionProfile(
    region="set_extension",
    transformation=TransformationClass.SYNTHESIS,     # substantially new media
    control=ControlMode.CONDITIONED,
    final_pixel=FinalPixelRole.COMPOSITED_ELEMENT,
))
```

The full member lists are in
[Reference: vocabularies](reference-vocabularies.md).

## 3. Describe the context the approval rests on

What the operation does is not enough to decide whether it is acceptable. That
depends on the material, the audience, and what is being asked for.

```python
from ai_use_case_context import (
    UseCaseProfile, BusinessContext, ApprovalContext, InputProfile, OutputProfile,
    ProjectVisibility, IPClass, CommercialNature, UseCaseMaturity,
    ApprovalSubject, InputType, OutputRole,
)

intake = UseCaseProfile(
    business=BusinessContext(
        visibility=ProjectVisibility.PUBLIC,
        ip_class=IPClass.PRE_RELEASE_IP,
        commercial_nature=CommercialNature.COMMERCIAL_RELEASE,
        maturity=UseCaseMaturity.PRODUCTION_READY,
    ),
    approval=ApprovalContext(
        subject=ApprovalSubject.WORKFLOW,
        proposed_use="Set extension on shots 0100-0140 only.",
    ),
    inputs=InputProfile(
        ip_class=IPClass.PRE_RELEASE_IP,
        input_types=[InputType.VIDEO, InputType.PERFORMER_LIKENESS],
    ),
    outputs=OutputProfile(
        role=OutputRole.FINISHED_MEDIA_ASSET,
        final_pixel=FinalPixelRole.DELIVERED_FRAME,
        likeness=LikenessPresence.PERFORMANCE,
    ),
)
```

## 4. Derive the flags

Now let the rules read those facts. Note what you are **not** doing: nobody
types a severity anywhere.

```python
capability.derive_flags(ctx)
intake.derive_flags(ctx, capability=capability)

print(ctx.summary())
```

You will see several flags, each naming the region or field that produced it
and the authority behind it — a performer-agreement question on the hero
region, a copyright question on the synthesized media reaching a commercial
release, a security question on pre-release material feeding public output.

Two people describing this shot the same way get the same flags. That is the
whole reason the facts are structured.

## 5. Read the state

```python
ctx.is_blocked()                    # any unresolved HIGH or CRITICAL
ctx.get_blockers()                  # which ones
ctx.get_enforceable_flags()         # backed by a statute or binding term
ctx.max_authority()                 # highest authority in play
ctx.get_reviewers_needed()          # who has to act
```

These **report**. Nothing here refuses an operation — see
[Limitations](limitations.md) for why that is deliberate.

## 6. Resolve or accept, and record who

```python
for flag in ctx.get_blockers():
    flag.resolve("Consent confirmed against the applicable agreement.")

# Or proceed despite one, naming who decided:
flag.accept_risk("Accepted for this shot only.", cleared_by="J. Reyes, Counsel")

ctx.get_unattributed_acceptances()   # accepted, nobody named — worth chasing
```

## 7. Record the decision

```python
from ai_use_case_context import ApprovalDecision

intake.record_decision(
    ctx, ApprovalDecision.APPROVED_WITH_CONSTRAINTS,
    decided_by="Review Board",
    notes="Limited to shots 0100-0140.",
)

intake.decision_was_contested()                  # approved over an open finding?
intake.approval.open_findings_at_decision        # what was outstanding, verbatim
```

## 8. Persist it

```python
from ai_use_case_context import to_json, from_json

blob = to_json(ctx)
restored = from_json(blob)
```

Authority, source attribution, and clearance all survive the round trip. The
profiles have their own `to_dict()` / `from_dict()`.

## Run the whole thing

A complete, runnable version of this — plus pipeline-derived classification and
an authorship record — is in
[`examples/capability_derivation.py`](../examples/capability_derivation.py):

```bash
python examples/capability_derivation.py
```

## Where next

- [Concepts](concepts.md) — the mental model, and the three decisions that shape everything
- [Guides](guides.md) — task-oriented walkthroughs by role
- [Reference: rules](reference-rules.md) — all 45 default rules
- [Limitations](limitations.md) — what this deliberately does not do
