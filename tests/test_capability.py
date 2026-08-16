"""Tests for capability classification and rule-driven flag derivation."""

import pytest

from ai_use_case_context.authority import Authority
from ai_use_case_context.capability import (
    CapabilityProfile,
    CapabilityRule,
    ControlMode,
    DEFAULT_CAPABILITY_RULES,
    FinalPixelRole,
    LikenessPresence,
    RegionProfile,
    TransformationClass,
)
from ai_use_case_context.core import RiskDimension, RiskLevel, UseCaseContext
from ai_use_case_context.vocabulary import VocabularyMapping


def region(**overrides) -> RegionProfile:
    """A neutral region that triggers no rules, for targeted overriding."""
    defaults = dict(
        region="test",
        transformation=TransformationClass.EXTRACTION,
        control=ControlMode.COMPOSED,
        likeness=LikenessPresence.NONE,
        final_pixel=FinalPixelRole.REFERENCE_ONLY,
    )
    defaults.update(overrides)
    return RegionProfile(**defaults)


class TestOrdering:
    def test_transformation_introduces_new_content(self):
        assert not TransformationClass.EXTRACTION.introduces_new_content
        assert not TransformationClass.CONVERSION.introduces_new_content
        assert not TransformationClass.ENHANCEMENT.introduces_new_content
        assert TransformationClass.REPAIR.introduces_new_content
        assert TransformationClass.MODIFICATION.introduces_new_content
        assert TransformationClass.SYNTHESIS.introduces_new_content

    def test_control_human_direction_boundary(self):
        assert not ControlMode.PRESET.is_substantially_human_directed
        assert not ControlMode.PARAMETERIZED.is_substantially_human_directed
        assert ControlMode.CONDITIONED.is_substantially_human_directed
        assert ControlMode.COMPOSED.is_substantially_human_directed

    def test_final_pixel_reaches_audience(self):
        assert not FinalPixelRole.NONE.reaches_audience
        assert not FinalPixelRole.REFERENCE_ONLY.reaches_audience
        assert FinalPixelRole.COMPOSITED_ELEMENT.reaches_audience
        assert FinalPixelRole.DELIVERED_FRAME.reaches_audience


class TestRegionProfile:
    def test_guidance_strength_bounds_enforced(self):
        with pytest.raises(ValueError):
            region(guidance_strength=1.5)
        with pytest.raises(ValueError):
            region(guidance_strength=-0.1)

    def test_guidance_strength_optional(self):
        assert region().guidance_strength is None

    def test_round_trip(self):
        original = region(
            region="hero",
            transformation=TransformationClass.MODIFICATION,
            control=ControlMode.CONDITIONED,
            likeness=LikenessPresence.PERFORMANCE,
            final_pixel=FinalPixelRole.DELIVERED_FRAME,
            guidance_strength=0.75,
            notes="n",
        )
        assert RegionProfile.from_dict(original.to_dict()) == original

    def test_str_includes_likeness_when_present(self):
        text = str(region(likeness=LikenessPresence.VOICE, guidance_strength=0.4))
        assert "likeness=Voice" in text
        assert "guidance=0.40" in text


class TestAggregates:
    def test_empty_profile_aggregates(self):
        profile = CapabilityProfile(name="empty")
        assert profile.max_transformation() is TransformationClass.EXTRACTION
        assert profile.max_final_pixel() is FinalPixelRole.NONE
        assert profile.max_likeness() is LikenessPresence.NONE
        assert profile.is_uniform()

    def test_min_control_reports_weakest_region(self):
        profile = CapabilityProfile(name="mixed")
        profile.add_region(region(region="a", control=ControlMode.COMPOSED))
        profile.add_region(region(region="b", control=ControlMode.PRESET))
        # The weakest region is the one a reviewer needs to see.
        assert profile.min_control() is ControlMode.PRESET

    def test_max_transformation_reports_most_novel(self):
        profile = CapabilityProfile(name="mixed")
        profile.add_region(
            region(region="a", transformation=TransformationClass.ENHANCEMENT)
        )
        profile.add_region(
            region(region="b", transformation=TransformationClass.SYNTHESIS)
        )
        assert profile.max_transformation() is TransformationClass.SYNTHESIS

    def test_is_uniform_detects_mixed_classification(self):
        profile = CapabilityProfile(name="mixed")
        profile.add_region(
            region(region="hero", transformation=TransformationClass.ENHANCEMENT)
        )
        profile.add_region(
            region(region="bg", transformation=TransformationClass.SYNTHESIS)
        )
        assert not profile.is_uniform()
        assert "mixed classification" in profile.summary()

    def test_single_region_is_uniform(self):
        profile = CapabilityProfile(name="one")
        profile.add_region(region())
        assert profile.is_uniform()

    def test_regions_with_likeness(self):
        profile = CapabilityProfile(name="p")
        profile.add_region(region(region="bg"))
        profile.add_region(
            region(region="hero", likeness=LikenessPresence.PERFORMANCE)
        )
        assert [r.region for r in profile.regions_with_likeness()] == ["hero"]


class TestDerivedFlags:
    def _rule_ids_fired(self, r: RegionProfile) -> set:
        return {
            rule.rule_id
            for rule in DEFAULT_CAPABILITY_RULES
            if rule.applies(r)
        }

    def test_performer_in_synthesized_content_flags_binding(self):
        ctx = UseCaseContext(name="Test")
        profile = CapabilityProfile(name="cap")
        profile.add_region(
            region(
                region="hero",
                transformation=TransformationClass.SYNTHESIS,
                control=ControlMode.CONDITIONED,
                likeness=LikenessPresence.PERFORMANCE,
                final_pixel=FinalPixelRole.DELIVERED_FRAME,
            )
        )
        flags = profile.derive_flags(ctx)
        assert any(
            f.authority is Authority.BINDING_CONTRACT for f in flags
        )
        assert ctx.is_blocked()

    def test_derived_flag_does_not_conclude(self):
        ctx = UseCaseContext(name="Test")
        profile = CapabilityProfile(name="cap")
        profile.add_region(
            region(
                region="hero",
                transformation=TransformationClass.MODIFICATION,
                control=ControlMode.CONDITIONED,
                likeness=LikenessPresence.VOICE,
            )
        )
        flags = profile.derive_flags(ctx)
        text = " ".join(f.description for f in flags).lower()
        # The framework routes the question; it does not answer it.
        assert "determination" in text or "review" in text

    def test_plate_locked_performance_is_lower_severity(self):
        # A performance held to the recorded plate raises an alteration
        # question, not a replica question.
        fired = self._rule_ids_fired(
            region(
                transformation=TransformationClass.ENHANCEMENT,
                likeness=LikenessPresence.PERFORMANCE,
            )
        )
        assert "RECORDED_PERFORMANCE_ALTERED" in fired
        assert "PERFORMER_IN_GENERATED_CONTENT" not in fired

    def test_generated_performance_is_higher_severity(self):
        fired = self._rule_ids_fired(
            region(
                transformation=TransformationClass.SYNTHESIS,
                likeness=LikenessPresence.PERFORMANCE,
            )
        )
        assert "PERFORMER_IN_GENERATED_CONTENT" in fired
        assert "RECORDED_PERFORMANCE_ALTERED" not in fired

    def test_synthesis_in_delivered_frame_flags_registration(self):
        ctx = UseCaseContext(name="Test")
        profile = CapabilityProfile(name="cap")
        profile.add_region(
            region(
                region="bg",
                transformation=TransformationClass.SYNTHESIS,
                control=ControlMode.COMPOSED,
                final_pixel=FinalPixelRole.DELIVERED_FRAME,
            )
        )
        flags = profile.derive_flags(ctx)
        assert any(
            f.authority is Authority.REGULATORY_GUIDANCE for f in flags
        )

    def test_synthesis_as_layer_does_not_flag_registration(self):
        fired = self._rule_ids_fired(
            region(
                transformation=TransformationClass.SYNTHESIS,
                control=ControlMode.COMPOSED,
                final_pixel=FinalPixelRole.COMPOSITED_ELEMENT,
            )
        )
        assert "SYNTHESIS_IN_DELIVERED_FRAME" not in fired

    def test_thin_human_direction_flags(self):
        fired = self._rule_ids_fired(
            region(
                transformation=TransformationClass.REPAIR,
                control=ControlMode.PRESET,
            )
        )
        assert "THIN_HUMAN_DIRECTION" in fired

    def test_strong_direction_does_not_flag_authorship(self):
        fired = self._rule_ids_fired(
            region(
                transformation=TransformationClass.SYNTHESIS,
                control=ControlMode.COMPOSED,
            )
        )
        assert "THIN_HUMAN_DIRECTION" not in fired

    def test_extraction_raises_nothing(self):
        ctx = UseCaseContext(name="Test")
        profile = CapabilityProfile(name="cap")
        profile.add_region(
            region(
                region="analysis",
                transformation=TransformationClass.EXTRACTION,
                control=ControlMode.PRESET,
            )
        )
        assert profile.derive_flags(ctx) == []
        assert not ctx.is_blocked()

    def test_per_region_classification_flags_only_the_risky_region(self):
        # One frame, two governance cases: the point of per-region profiles.
        ctx = UseCaseContext(name="Test")
        profile = CapabilityProfile(name="shot")
        profile.add_region(
            region(
                region="hero_actor",
                transformation=TransformationClass.ENHANCEMENT,
                control=ControlMode.COMPOSED,
                likeness=LikenessPresence.NONE,
            )
        )
        profile.add_region(
            region(
                region="background",
                transformation=TransformationClass.SYNTHESIS,
                control=ControlMode.COMPOSED,
                final_pixel=FinalPixelRole.DELIVERED_FRAME,
            )
        )
        flags = profile.derive_flags(ctx)
        assert len(flags) == 1
        assert "background" in flags[0].description

    def test_custom_rule_set_replaces_defaults(self):
        ctx = UseCaseContext(name="Test")
        profile = CapabilityProfile(name="cap")
        profile.add_region(region(region="r"))
        catch_all = CapabilityRule(
            rule_id="ALWAYS",
            title="fires on everything",
            applies=lambda r: True,
            dimension=RiskDimension.QUALITY,
            level=RiskLevel.LOW,
            describe=lambda r: f"saw {r.region}",
        )
        flags = profile.derive_flags(ctx, rules=[catch_all])
        assert len(flags) == 1
        assert flags[0].description == "saw r"

    def test_empty_rule_set_derives_nothing(self):
        ctx = UseCaseContext(name="Test")
        profile = CapabilityProfile(name="cap")
        profile.add_region(
            region(
                transformation=TransformationClass.SYNTHESIS,
                likeness=LikenessPresence.PERFORMANCE,
            )
        )
        assert profile.derive_flags(ctx, rules=[]) == []


class TestSerializationAndVocabulary:
    def test_profile_round_trip(self):
        profile = CapabilityProfile(name="cap", description="d")
        profile.add_region(
            region(region="a", guidance_strength=0.5, notes="n")
        )
        restored = CapabilityProfile.from_dict(profile.to_dict())
        assert restored == profile

    def test_to_external_translates_mapped_terms(self):
        mapping = VocabularyMapping(
            name="example",
            version="1.0",
            terms={
                TransformationClass.EXTRACTION: "ExampleTerm-Readout",
                TransformationClass.CONVERSION: "ExampleTerm-Readout",
                ControlMode.COMPOSED: "ExampleTerm-Assemble",
            },
        )
        profile = CapabilityProfile(name="cap")
        profile.add_region(region(region="a"))
        external = profile.to_external(mapping)
        assert external["regions"][0]["transformation"] == "ExampleTerm-Readout"
        assert external["regions"][0]["control"] == "ExampleTerm-Assemble"

    def test_unmapped_terms_come_back_none_not_our_names(self):
        # A silent fallback would present our vocabulary as theirs.
        mapping = VocabularyMapping(name="sparse")
        profile = CapabilityProfile(name="cap")
        profile.add_region(region(region="a"))
        external = profile.to_external(mapping)
        assert external["regions"][0]["transformation"] is None
