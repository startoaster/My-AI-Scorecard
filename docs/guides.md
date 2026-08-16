# Guides

Task-oriented walkthroughs. Each assumes you have read
[Getting started](getting-started.md).

---

## Proposing a use of AI

*You are a production technologist, pipeline lead, or artist who wants to use
an AI capability and needs it reviewed.*

Describe the facts and let the rules do the flagging. You do not judge severity.

1. **Classify the capability**, per region. If your pipeline records how
   tightly each region was held to its source, derive it rather than typing it
   — see *Recording pipeline signals* below.
2. **Record the intake facts** — what material goes in, what comes out, how
   visible the project is, and what exactly you are asking to be allowed to do.
   Keep `proposed_use` narrow; a bounded request is easier to approve than a
   broad one.
3. **Record where it runs**, if the tool is hosted anywhere you do not control.
4. **Derive**, then read `ctx.summary()` and fix what you can before submitting.

```python
from ai_use_case_context import (
    UseCaseContext, CapabilityProfile, RegionProfile, UseCaseProfile,
    OperationalProfile, TransformationClass, ControlMode, IPClass,
)

ctx = UseCaseContext(name="Proposal", workflow_phase="Post")
capability = CapabilityProfile(name="Upres")
capability.add_region(RegionProfile(
    region="full_frame",
    transformation=TransformationClass.ENHANCEMENT,
    control=ControlMode.PARAMETERIZED,
))
intake = UseCaseProfile()
operations = OperationalProfile()

capability.derive_flags(ctx)
intake.derive_flags(ctx, capability=capability)
operations.derive_flags(ctx, ip_class=intake.inputs.ip_class)
```

Pass `ip_class` to the operational rules. Without it, the rules that weigh an
operational fact against material sensitivity stay silent rather than assuming
the worst.

---

## Reviewing a proposal

*You sit on a governance or review body.*

The framework's job is to make the proposal answerable, not to answer it.

**Read the state:**

```python
ctx.is_blocked()                  # unresolved HIGH or CRITICAL
ctx.get_blockers()
ctx.get_enforceable_flags()       # statute or binding term, any severity
ctx.max_authority()
ctx.get_reviewers_needed()
```

`get_enforceable_flags()` is the one worth reading separately from severity. A
low-severity contract question and a low-severity preference are not the same
thing, and only one of them is somebody else's call.

**Then decide, and record it:**

```python
from ai_use_case_context import ApprovalDecision

intake.record_decision(
    ctx, ApprovalDecision.APPROVED_WITH_CONSTRAINTS,
    decided_by="Review Board",
    notes="Limited to shots 0100-0140; re-review if the model version changes.",
)
```

Four outcomes are available: `APPROVED`, `APPROVED_WITH_CONSTRAINTS`,
`APPROVED_FOR_INTERNAL_TESTING`, `REJECTED`. Approving over an open enforceable
finding is permitted — it is your call to make — and
`decision_was_contested()` will report that it happened, with
`open_findings_at_decision` preserving what was outstanding.

**Clearing individual findings:**

```python
for flag in ctx.get_blockers():
    flag.resolve("Consent obtained and filed.")                # issue is gone

for flag in ctx.get_enforceable_flags():
    flag.accept_risk("Accepted for this shot.", cleared_by="J. Reyes, Counsel")
```

`resolve()` means the underlying issue is gone. `accept_risk()` means it stands
and you are proceeding anyway — which is why that one takes a name.

Name who accepted. Nothing enforces it, and `get_unattributed_acceptances()`
is how the omission gets found later.

---

## Recording pipeline signals

*You maintain a pipeline that can report what it did.*

This is the highest-value integration available, because it makes the
classification a record of what ran rather than an assertion made afterwards.

```python
from ai_use_case_context import (
    PipelineRecord, GuidanceSignal, OutputComposition, LikenessPresence,
)

record = PipelineRecord(
    stage="Shot 0100",
    primary_region="hero_actor",
    model="internal-conditioned-video-v3",
)
record.add_signal(GuidanceSignal(
    region="hero_actor",
    guidance_strength=0.97,        # normalize yours to [0,1]; 1.0 = fully constrained
    conditioning=["depth", "segmentation", "motion"],
    region_specific=True,          # this region addressed separately
    user_authored=True,            # a human supplied the conditioning
    composition=OutputComposition.HYBRID,
    likeness=LikenessPresence.PERFORMANCE,
))

capability = record.to_capability_profile()
```

Three things to get right:

- **Normalize guidance strength** to `[0.0, 1.0]` where 1.0 means fully
  constrained by the source. Whatever your pipeline calls it locally.
- **`user_authored` matters more than it looks.** Conditioning the tool
  produced is not the user shaping the result; it drops the control mode to
  `PRESET`.
- **Only derive for stages that produce media.** Segmentation, depth
  estimation, and tracking introduce nothing regardless of guidance value —
  classify those directly with a `RegionProfile`.

---

## Assessing a vendor or a dataset

Use the flag-producing path for anything that gates a decision:

```python
from ai_use_case_context import (
    VendorScorecard, CopyrightAssessment, tier_from_flags,
    ProvenanceCard, ModelCollapseGuard,
)

scorecard = VendorScorecard(
    vendor_name="Example",
    copyright=CopyrightAssessment(
        training_data_lawfully_obtained=True,
        license_verification_documented=True,
    ),
)
scorecard.derive_flags(ctx)
tier_from_flags(ctx)          # non-compensatory, reads live flag state
```

`tier_from_flags()` reads authority and severity together: an enforceable
finding always costs at least one tier and can never be averaged away, but a
low-severity contract point lands at `CONDITIONAL` rather than disqualifying
the vendor. Because it reads live state, clearing findings moves the tier.

For datasets, `ProvenanceCard.derive_flags(ctx, guard)` covers licence status,
rights-holder reservations, unclassified origin, and synthetic share. Keep
using `evaluate_provenance()` alongside it — it answers a different question,
how thoroughly the lineage is *documented*.

Attach a `CopyrightAssessment` explicitly. An absent assessment raises nothing,
and that is not the same as a clean one.

---

## Tracking human authorship

*You need to be able to answer "what did a person actually contribute?" later.*

```python
from ai_use_case_context import AuthorshipRecord

authorship = AuthorshipRecord.from_capability_profile(
    capability, compiled_by="Pipeline"
)

for evidence in authorship.evidence:
    if evidence.region == "set_extension":
        evidence.contributions.append("Art-directed reference selection")
        evidence.iterations = 4
        evidence.human_reviewed = True

authorship.undocumented_regions()    # generative regions with nothing recorded
print(authorship.summary())
```

Seeding from a capability profile captures what the pipeline recorded. Only a
person can report what a person contributed, so fill in `contributions`,
`iterations`, and the review flags yourself — and be concrete. "Supervised the
process" is not evidence; "authored the depth map and hand-corrected the
silhouette on frames 40–58" is.

---

## Where next

- [Customising](customising.md) — your rules, routing, dimensions, vocabularies
- [Integration](integration.md) — hooks, events, persistence, the dashboard
- [Limitations](limitations.md) — the boundaries, and why they are where they are
