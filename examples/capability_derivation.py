"""
Deriving governance from pipeline signals instead of a form.

Shows the path end to end:

    recorded signals -> capability classification -> risk flags -> clearance

The shot below is one frame with two governance cases in it: a performer held
tightly to the recorded plate, and a fully generated background. Classifying
the shot as a whole would misrepresent both.

Run with:  python examples/capability_derivation.py
"""

from ai_use_case_context import (
    Authority,
    AuthorshipRecord,
    ClearanceError,
    GuidanceSignal,
    LikenessPresence,
    OutputComposition,
    PipelineRecord,
    UseCaseContext,
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
    # 3. Flags follow from the classification
    # ------------------------------------------------------------------
    ctx = UseCaseContext(
        name="Shot 0100 — environment extension",
        description="Set extension behind a retained hero performance.",
        workflow_phase="Element Regeneration",
    )
    profile.derive_flags(ctx)
    print(ctx.summary())
    print()

    # ------------------------------------------------------------------
    # 4. Enforceable findings cannot be self-cleared
    # ------------------------------------------------------------------
    for flag in ctx.get_enforceable_flags():
        try:
            flag.accept_risk("looks fine to me")
        except ClearanceError as exc:
            print(f"Refused: {exc}")
    print()

    # ------------------------------------------------------------------
    # 5. Where the terms themselves disagree
    # ------------------------------------------------------------------
    lexicon = default_lexicon()
    print("Contested terms in play:")
    for conflict in lexicon.conflicts():
        print(f"  - {conflict.describe()}")
    print()

    # ------------------------------------------------------------------
    # 6. The authorship record — evidence, not a verdict
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
