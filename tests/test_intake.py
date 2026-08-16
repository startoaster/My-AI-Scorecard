"""Tests for use case intake, combination rules, and approval decisions."""

import pytest

from ai_use_case_context.authority import Authority
from ai_use_case_context.capability import (
    CapabilityProfile,
    ControlMode,
    FinalPixelRole,
    LikenessPresence,
    RegionProfile,
    TransformationClass,
)
from ai_use_case_context.core import RiskDimension, RiskLevel, UseCaseContext
from ai_use_case_context.intake import (
    ApprovalContext,
    ApprovalDecision,
    ApprovalSubject,
    BrandPresence,
    BusinessContext,
    CommercialNature,
    DEFAULT_INTAKE_RULES,
    InputProfile,
    InputType,
    IntakeRule,
    IPClass,
    OutputProfile,
    OutputRole,
    ProjectVisibility,
    RESTRICTED_IP_CLASSES,
    UseCaseMaturity,
    UseCaseProfile,
)


def capability(transformation=TransformationClass.SYNTHESIS) -> CapabilityProfile:
    profile = CapabilityProfile(name="cap")
    profile.add_region(
        RegionProfile(
            region="r",
            transformation=transformation,
            control=ControlMode.COMPOSED,
        )
    )
    return profile


def profile(**overrides) -> UseCaseProfile:
    """A benign profile that fires no rules, for targeted overriding."""
    p = UseCaseProfile(
        business=BusinessContext(
            visibility=ProjectVisibility.INTERNAL_TESTING,
            ip_class=IPClass.NO_IP,
            commercial_nature=CommercialNature.NON_COMMERCIAL,
            maturity=UseCaseMaturity.PRODUCTION_READY,
        ),
        approval=ApprovalContext(subject=ApprovalSubject.WORKFLOW),
        inputs=InputProfile(ip_class=IPClass.NO_IP),
        outputs=OutputProfile(
            role=OutputRole.NON_MEDIA_ASSET,
            final_pixel=FinalPixelRole.NONE,
        ),
    )
    for key, value in overrides.items():
        setattr(p, key, value)
    return p


def fired(p: UseCaseProfile, cap=None) -> set:
    return {r.rule_id for r in DEFAULT_INTAKE_RULES if r.applies(p, cap)}


class TestIPClass:
    def test_restricted_set_membership(self):
        assert IPClass.PRE_RELEASE_IP in RESTRICTED_IP_CLASSES
        assert IPClass.TALENT_MATERIAL in RESTRICTED_IP_CLASSES
        assert IPClass.NO_IP not in RESTRICTED_IP_CLASSES
        assert IPClass.RELEASED_IP not in RESTRICTED_IP_CLASSES

    def test_input_profile_is_restricted(self):
        assert InputProfile(ip_class=IPClass.PRODUCTION_IP).is_restricted
        assert not InputProfile(ip_class=IPClass.NO_IP).is_restricted


class TestBaselineProfile:
    def test_benign_profile_fires_nothing(self):
        assert fired(profile()) == set()

    def test_benign_profile_with_capability_fires_nothing(self):
        # Even a synthesis capability is unremarkable with no IP, no public
        # exposure, and no final-pixel presence.
        assert fired(profile(), capability()) == set()


class TestCombinationRules:
    def test_restricted_input_to_public_output(self):
        p = profile(
            business=BusinessContext(
                visibility=ProjectVisibility.PUBLIC,
                ip_class=IPClass.PRE_RELEASE_IP,
                maturity=UseCaseMaturity.PRODUCTION_READY,
            ),
            inputs=InputProfile(ip_class=IPClass.PRE_RELEASE_IP),
            outputs=OutputProfile(final_pixel=FinalPixelRole.DELIVERED_FRAME),
        )
        assert "RESTRICTED_INPUT_TO_PUBLIC_OUTPUT" in fired(p)

    def test_restricted_input_alone_is_not_enough(self):
        # The combination is the trigger, not any single field.
        p = profile(inputs=InputProfile(ip_class=IPClass.PRE_RELEASE_IP))
        assert "RESTRICTED_INPUT_TO_PUBLIC_OUTPUT" not in fired(p)

    def test_public_output_alone_is_not_enough(self):
        p = profile(
            business=BusinessContext(
                visibility=ProjectVisibility.PUBLIC,
                maturity=UseCaseMaturity.PRODUCTION_READY,
            ),
            outputs=OutputProfile(final_pixel=FinalPixelRole.DELIVERED_FRAME),
        )
        assert "RESTRICTED_INPUT_TO_PUBLIC_OUTPUT" not in fired(p)

    def test_personal_data_flags_under_statute(self):
        p = profile(
            inputs=InputProfile(input_types=[InputType.PERSONAL_DATA])
        )
        rule = next(
            r for r in DEFAULT_INTAKE_RULES
            if r.rule_id == "PERSONAL_DATA_IN_INPUTS"
        )
        assert rule.applies(p, None)
        assert rule.authority is Authority.STATUTE

    def test_performer_likeness_input_flags_binding(self):
        p = profile(
            inputs=InputProfile(input_types=[InputType.PERFORMER_LIKENESS])
        )
        rule = next(
            r for r in DEFAULT_INTAKE_RULES
            if r.rule_id == "PERFORMER_LIKENESS_INPUT"
        )
        assert rule.applies(p, None)
        assert rule.authority is Authority.BINDING_CONTRACT

    def test_licensed_music_needs_generative_capability(self):
        p = profile(
            inputs=InputProfile(input_types=[InputType.LICENSED_MUSIC])
        )
        assert "LICENSED_MUSIC_INTO_NEW_MEDIA" not in fired(p)
        assert "LICENSED_MUSIC_INTO_NEW_MEDIA" not in fired(
            p, capability(TransformationClass.EXTRACTION)
        )
        assert "LICENSED_MUSIC_INTO_NEW_MEDIA" in fired(
            p, capability(TransformationClass.SYNTHESIS)
        )

    def test_commercial_release_of_synthesized_media(self):
        p = profile(
            business=BusinessContext(
                commercial_nature=CommercialNature.COMMERCIAL_RELEASE,
                maturity=UseCaseMaturity.PRODUCTION_READY,
            ),
            outputs=OutputProfile(final_pixel=FinalPixelRole.DELIVERED_FRAME),
        )
        assert "COMMERCIAL_RELEASE_OF_GENERATED_MEDIA" in fired(
            p, capability(TransformationClass.SYNTHESIS)
        )
        # A modification delivered commercially is a different question.
        assert "COMMERCIAL_RELEASE_OF_GENERATED_MEDIA" not in fired(
            p, capability(TransformationClass.MODIFICATION)
        )

    def test_fine_tuning_on_restricted_material_is_critical(self):
        p = profile(
            approval=ApprovalContext(
                subject=ApprovalSubject.FINE_TUNING_WORKFLOW
            ),
            inputs=InputProfile(ip_class=IPClass.PRODUCTION_IP),
        )
        rule = next(
            r for r in DEFAULT_INTAKE_RULES
            if r.rule_id == "FINE_TUNING_ON_RESTRICTED_MATERIAL"
        )
        assert rule.applies(p, None)
        assert rule.level is RiskLevel.CRITICAL

    def test_fine_tuning_on_unrestricted_material_does_not_fire(self):
        p = profile(
            approval=ApprovalContext(
                subject=ApprovalSubject.FINE_TUNING_WORKFLOW
            ),
            inputs=InputProfile(ip_class=IPClass.NO_IP),
        )
        assert "FINE_TUNING_ON_RESTRICTED_MATERIAL" not in fired(p)

    def test_brand_altered_flags(self):
        p = profile(
            outputs=OutputProfile(brand=BrandPresence.DEPICTED_ALTERED)
        )
        assert "BRAND_DEPICTED_ALTERED" in fired(p)

    def test_brand_in_new_context_does_not_flag(self):
        p = profile(
            outputs=OutputProfile(brand=BrandPresence.ORIGINAL_IN_NEW_CONTEXT)
        )
        assert "BRAND_DEPICTED_ALTERED" not in fired(p)

    def test_research_maturity_in_public_work_flags_feasibility(self):
        p = profile(
            business=BusinessContext(
                visibility=ProjectVisibility.PUBLIC,
                maturity=UseCaseMaturity.SHORT_TERM_RESEARCH,
            )
        )
        assert "UNPROVEN_USE_IN_PUBLIC_WORK" in fired(p)

    def test_research_maturity_internally_does_not_flag(self):
        p = profile(
            business=BusinessContext(
                visibility=ProjectVisibility.INTERNAL_TESTING,
                maturity=UseCaseMaturity.SHORT_TERM_RESEARCH,
            )
        )
        assert "UNPROVEN_USE_IN_PUBLIC_WORK" not in fired(p)


class TestDeriveFlags:
    def test_flags_land_on_context(self):
        ctx = UseCaseContext(name="Test")
        p = profile(
            inputs=InputProfile(input_types=[InputType.PERFORMER_LIKENESS])
        )
        flags = p.derive_flags(ctx)
        assert len(flags) == 1
        assert ctx.get_enforceable_flags()

    def test_custom_rules_replace_defaults(self):
        ctx = UseCaseContext(name="Test")
        catch_all = IntakeRule(
            rule_id="ALWAYS",
            title="fires always",
            applies=lambda p, c: True,
            dimension=RiskDimension.QUALITY,
            level=RiskLevel.LOW,
            describe=lambda p, c: "always",
        )
        flags = profile().derive_flags(ctx, rules=[catch_all])
        assert [f.description for f in flags] == ["always"]

    def test_empty_rules_derive_nothing(self):
        ctx = UseCaseContext(name="Test")
        assert profile().derive_flags(ctx, rules=[]) == []


class TestApprovalDecision:
    def test_is_approval(self):
        assert ApprovalDecision.APPROVED.is_approval
        assert ApprovalDecision.APPROVED_WITH_CONSTRAINTS.is_approval
        assert ApprovalDecision.APPROVED_FOR_INTERNAL_TESTING.is_approval
        assert not ApprovalDecision.REJECTED.is_approval
        assert not ApprovalDecision.PENDING.is_approval

    def test_approval_over_open_finding_is_recorded_not_refused(self):
        # The organisation is entitled to decide this; the record must not
        # lose the fact that it decided knowingly.
        ctx = UseCaseContext(name="Test")
        p = profile(
            inputs=InputProfile(input_types=[InputType.PERFORMER_LIKENESS])
        )
        p.derive_flags(ctx)
        p.record_decision(ctx, ApprovalDecision.APPROVED, decided_by="X")
        assert p.approval.decision is ApprovalDecision.APPROVED
        assert p.approval.open_findings_at_decision
        assert p.decision_was_contested()

    def test_open_findings_snapshot_names_authority_and_severity(self):
        ctx = UseCaseContext(name="Test")
        p = profile(
            inputs=InputProfile(input_types=[InputType.PERFORMER_LIKENESS])
        )
        p.derive_flags(ctx)
        p.record_decision(ctx, ApprovalDecision.APPROVED, decided_by="X")
        entry = p.approval.open_findings_at_decision[0]
        assert "Binding Contract" in entry
        assert "HIGH" in entry

    def test_uncontested_approval_records_nothing_outstanding(self):
        ctx = UseCaseContext(name="Test")
        p = profile()
        p.record_decision(ctx, ApprovalDecision.APPROVED, decided_by="X")
        assert p.approval.open_findings_at_decision == []
        assert not p.decision_was_contested()

    def test_rejection_is_never_contested(self):
        ctx = UseCaseContext(name="Test")
        p = profile(
            inputs=InputProfile(input_types=[InputType.PERFORMER_LIKENESS])
        )
        p.derive_flags(ctx)
        p.record_decision(ctx, ApprovalDecision.REJECTED)
        assert not p.decision_was_contested()

    def test_approval_after_clearing(self):
        ctx = UseCaseContext(name="Test")
        p = profile(
            inputs=InputProfile(input_types=[InputType.PERFORMER_LIKENESS])
        )
        for flag in p.derive_flags(ctx):
            flag.accept_risk("consent on file", cleared_by="Counsel")
        p.record_decision(
            ctx, ApprovalDecision.APPROVED_WITH_CONSTRAINTS,
            decided_by="Review Board", notes="Limited to shots 100-140",
        )
        assert p.approval.decision is ApprovalDecision.APPROVED_WITH_CONSTRAINTS
        assert p.approval.decided_at is not None

    def test_non_enforceable_flags_do_not_count_as_contested(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(RiskDimension.QUALITY, RiskLevel.HIGH, "ordinary")
        p = profile()
        p.record_decision(ctx, ApprovalDecision.APPROVED, decided_by="X")
        assert p.approval.decision is ApprovalDecision.APPROVED
        assert not p.decision_was_contested()


class TestSerialization:
    def test_round_trip(self):
        p = UseCaseProfile(
            business=BusinessContext(
                visibility=ProjectVisibility.PUBLIC,
                ip_class=IPClass.PRE_RELEASE_IP,
                commercial_nature=CommercialNature.COMMERCIAL_RELEASE,
                maturity=UseCaseMaturity.ENGINEERING,
                benefit="b",
                department="VFX",
            ),
            approval=ApprovalContext(
                subject=ApprovalSubject.FINE_TUNING_WORKFLOW,
                proposed_use="u",
                tools_in_scope=["t"],
                capabilities_in_scope=["c"],
                required_reviews=["creative"],
            ),
            inputs=InputProfile(
                ip_class=IPClass.PRODUCTION_IP,
                input_types=[InputType.VIDEO, InputType.PERFORMER_LIKENESS],
            ),
            outputs=OutputProfile(
                output_types=["plate"],
                role=OutputRole.FINISHED_MEDIA_ASSET,
                final_pixel=FinalPixelRole.DELIVERED_FRAME,
                likeness=LikenessPresence.PERFORMANCE,
                brand=BrandPresence.ORIGINAL_IN_NEW_CONTEXT,
            ),
        )
        assert UseCaseProfile.from_dict(p.to_dict()) == p

    def test_decision_round_trips(self):
        ctx = UseCaseContext(name="Test")
        p = profile()
        p.record_decision(ctx, ApprovalDecision.APPROVED, decided_by="X")
        restored = UseCaseProfile.from_dict(p.to_dict())
        assert restored.approval.decision is ApprovalDecision.APPROVED
        assert restored.approval.decided_at == p.approval.decided_at

    def test_summary_shows_key_fields(self):
        text = profile().summary()
        assert "Subject" in text and "Decision" in text
