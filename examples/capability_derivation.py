"""
Deriving governance from recorded facts instead of a form.

Shows the path end to end:

    pipeline signals ─┐
    intake facts      ├─> risk flags -> clearance -> approval decision
    operational facts ─┘

Nobody types a severity anywhere in this script. Every flag follows from a
recorded fact or a stated field, which is what makes two people describing the
same proposal produce the same result.

The shot below is one frame with two governance cases in it: a performer held
tightly to the recorded plate, and a fully generated background. Classifying
the shot as a whole would misrepresent both.

Run with:  python examples/capability_derivation.py
"""

from ai_use_case_context import (
    ApprovalContext,
    ApprovalDecision,
    ApprovalError,
    ApprovalSubject,
    AuthorshipRecord,
    BusinessContext,
    ClearanceError,
    CollectionPolicy,
    CommercialNature,
    Custodian,
    DataCollection,
    DataResidency,
    Deployment,
    FinalPixelRole,
    GuidanceSignal,
    HostEnvironment,
    InputProfile,
    InputType,
    IPClass,
    LikenessPresence,
    ModelRefinement,
    OperationalProfile,
    OutputComposition,
    OutputProfile,
    OutputRole,
    PipelineRecord,
    ProjectVisibility,
    UpdateControl,
    UseCaseContext,
    UseCaseMaturity,
    UseCaseProfile,
    default_lexicon,
)


def main():
    # ------------------------------------------------------------------
    # 1. What the pipeline recorded
    # ------------------------------------------------------------------
    record = PipelineRecord(
        stage="Shot 0100 — environment extension",
        primary_region="hero_actor",
        model="internal-conditioned-video-v3",
        notes="Hero locked to plate; set extension generated behind them.",
    )

    record.add_signal(
        GuidanceSignal(
            region="hero_actor",
            guidance_strength=0.97,          # held tightly to the plate
            conditioning=["depth", "segmentation", "motion"],
            region_specific=True,
            composition=OutputComposition.HYBRID,
            likeness=LikenessPresence.PERFORMANCE,
            notes="Recorded performance retained; relight only.",
        )
    )
    record.add_signal(
        GuidanceSignal(
            region="set_extension",
            guidance_strength=0.15,          # substantially unconstrained
            conditioning=["depth"],
            region_specific=False,
            composition=OutputComposition.HYBRID,
            notes="Generated background, composited as a separate layer.",
        )
    )

    # ------------------------------------------------------------------
    # 2. Classification, derived rather than asserted
    # ------------------------------------------------------------------
    profile = record.to_capability_profile()
    print(profile.summary())
    print()

    # ------------------------------------------------------------------
    # 3. The intake facts an approval actually rests on
    # ------------------------------------------------------------------
    intake = UseCaseProfile(
        business=BusinessContext(
            visibility=ProjectVisibility.PUBLIC,
            ip_class=IPClass.PRE_RELEASE_IP,
            commercial_nature=CommercialNature.COMMERCIAL_RELEASE,
            maturity=UseCaseMaturity.PRODUCTION_READY,
            benefit="Avoids a location build for a single establishing beat.",
            department="VFX",
        ),
        approval=ApprovalContext(
            subject=ApprovalSubject.WORKFLOW,
            proposed_use="Set extension on shots 0100-0140 only.",
            capabilities_in_scope=["Conditioned environment generation"],
        ),
        inputs=InputProfile(
            ip_class=IPClass.PRE_RELEASE_IP,
            input_types=[InputType.VIDEO, InputType.PERFORMER_LIKENESS],
        ),
        outputs=OutputProfile(
            output_types=["background plate"],
            role=OutputRole.FINISHED_MEDIA_ASSET,
            final_pixel=FinalPixelRole.DELIVERED_FRAME,
            likeness=LikenessPresence.PERFORMANCE,
        ),
    )

    # ------------------------------------------------------------------
    # 4. Where it runs and what happens to the data
    # ------------------------------------------------------------------
    operations = OperationalProfile(
        deployment=Deployment(
            host=HostEnvironment.VENDOR_CLOUD,
            region="US",
            update_control=UpdateControl.VENDOR,
        ),
        residency=DataResidency(custodian=Custodian.VENDOR, location="US"),
        collection=DataCollection(
            customer_data=CollectionPolicy.COLLECTED_OPT_OUT,
            metadata=CollectionPolicy.COLLECTED_REQUIRED,
            retention_period="indefinite",
        ),
        refinement=ModelRefinement(allowed=False),
    )

    # ------------------------------------------------------------------
    # 5. Flags follow from all three, not from a severity someone typed
    # ------------------------------------------------------------------
    ctx = UseCaseContext(
        name="Shot 0100 — environment extension",
        description="Set extension behind a retained hero performance.",
        workflow_phase="Element Regeneration",
    )
    profile.derive_flags(ctx)
    intake.derive_flags(ctx, capability=profile)
    operations.derive_flags(ctx, ip_class=intake.inputs.ip_class)
    print(ctx.summary())
    print()

    # ------------------------------------------------------------------
    # 6. Enforceable findings cannot be self-cleared
    # ------------------------------------------------------------------
    for flag in ctx.get_enforceable_flags():
        try:
            flag.accept_risk("looks fine to me")
        except ClearanceError as exc:
            print(f"Refused clearance: {exc}")
            break
    print()

    # ------------------------------------------------------------------
    # 7. Nor can the proposal be approved around them
    # ------------------------------------------------------------------
    try:
        intake.record_decision(
            ctx, ApprovalDecision.APPROVED, decided_by="Review Board"
        )
    except ApprovalError as exc:
        print(f"Refused approval: {exc}")
    print()

    # ------------------------------------------------------------------
    # 8. Where the terms themselves disagree
    # ------------------------------------------------------------------
    lexicon = default_lexicon()
    print("Contested terms in play:")
    for conflict in lexicon.conflicts():
        print(f"  - {conflict.describe()}")
    print()

    # ------------------------------------------------------------------
    # 9. The authorship record — evidence, not a verdict
    # ------------------------------------------------------------------
    authorship = AuthorshipRecord.from_capability_profile(
        profile, compiled_by="Pipeline"
    )
    # Only a human can report what a human contributed.
    for evidence in authorship.evidence:
        if evidence.region == "set_extension":
            evidence.contributions.append("Art-directed reference selection")
            evidence.iterations = 4
            evidence.human_reviewed = True
    print(authorship.summary())


if __name__ == "__main__":
    main()
