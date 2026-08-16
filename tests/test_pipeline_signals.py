"""Tests for deriving classification from recorded pipeline signals."""

import pytest

from ai_use_case_context.capability import (
    ControlMode,
    FinalPixelRole,
    LikenessPresence,
    TransformationClass,
)
from ai_use_case_context.core import UseCaseContext
from ai_use_case_context.pipeline_signals import (
    DEFAULT_THRESHOLDS,
    DerivationThresholds,
    GuidanceSignal,
    OutputComposition,
    PipelineRecord,
    derive_control_mode,
    derive_final_pixel_role,
    derive_region_profile,
    derive_transformation,
)


class TestThresholds:
    def test_rejects_out_of_order(self):
        with pytest.raises(ValueError):
            DerivationThresholds(enhancement_at=0.2, repair_at=0.9)

    def test_rejects_out_of_range(self):
        with pytest.raises(ValueError):
            DerivationThresholds(enhancement_at=1.4)

    def test_defaults_are_ordered(self):
        t = DEFAULT_THRESHOLDS
        assert t.enhancement_at >= t.repair_at >= t.modification_at


class TestTransformationDerivation:
    @pytest.mark.parametrize(
        "guidance,expected",
        [
            (1.0, TransformationClass.ENHANCEMENT),
            (0.95, TransformationClass.ENHANCEMENT),
            (0.9, TransformationClass.REPAIR),
            (0.8, TransformationClass.REPAIR),
            (0.7, TransformationClass.MODIFICATION),
            (0.5, TransformationClass.MODIFICATION),
            (0.49, TransformationClass.SYNTHESIS),
            (0.0, TransformationClass.SYNTHESIS),
        ],
    )
    def test_bands(self, guidance, expected):
        assert derive_transformation(guidance) is expected

    def test_monotonic_in_guidance(self):
        # Less constraint must never yield a less novel classification.
        values = [i / 20 for i in range(21)]
        classes = [derive_transformation(v).value for v in values]
        assert classes == sorted(classes, reverse=True)

    def test_never_returns_non_generative_class(self):
        for i in range(21):
            result = derive_transformation(i / 20)
            assert result.introduces_new_content or result is (
                TransformationClass.ENHANCEMENT
            )
            assert result not in (
                TransformationClass.EXTRACTION,
                TransformationClass.CONVERSION,
            )

    def test_rejects_out_of_range(self):
        with pytest.raises(ValueError):
            derive_transformation(1.2)

    def test_custom_thresholds_shift_bands(self):
        strict = DerivationThresholds(
            enhancement_at=0.99, repair_at=0.9,
            modification_at=0.7, synthesis_below=0.7,
        )
        # Same recorded value, different calibration, different class — which
        # is why the thresholds travel with the record.
        assert derive_transformation(0.95) is TransformationClass.ENHANCEMENT
        assert derive_transformation(0.95, strict) is TransformationClass.REPAIR
        assert derive_transformation(0.8, strict) is (
            TransformationClass.MODIFICATION
        )


class TestControlDerivation:
    def test_no_conditioning_is_parameterized(self):
        signal = GuidanceSignal(region="r", guidance_strength=0.5)
        assert derive_control_mode(signal) is ControlMode.PARAMETERIZED

    def test_no_conditioning_and_not_user_authored_is_preset(self):
        signal = GuidanceSignal(
            region="r", guidance_strength=0.5, user_authored=False
        )
        assert derive_control_mode(signal) is ControlMode.PRESET

    def test_tool_derived_conditioning_is_preset(self):
        # Conditioning the tool produced is not the user shaping the result.
        signal = GuidanceSignal(
            region="r",
            guidance_strength=0.5,
            conditioning=["depth", "segmentation"],
            region_specific=True,
            user_authored=False,
        )
        assert derive_control_mode(signal) is ControlMode.PRESET

    def test_user_conditioning_is_conditioned(self):
        signal = GuidanceSignal(
            region="r", guidance_strength=0.5, conditioning=["depth"]
        )
        assert derive_control_mode(signal) is ControlMode.CONDITIONED

    def test_region_specific_multi_signal_is_composed(self):
        signal = GuidanceSignal(
            region="r",
            guidance_strength=0.5,
            conditioning=["depth", "segmentation"],
            region_specific=True,
        )
        assert derive_control_mode(signal) is ControlMode.COMPOSED

    def test_whole_frame_multi_signal_is_only_conditioned(self):
        signal = GuidanceSignal(
            region="r",
            guidance_strength=0.5,
            conditioning=["depth", "segmentation"],
            region_specific=False,
        )
        assert derive_control_mode(signal) is ControlMode.CONDITIONED


class TestFinalPixelDerivation:
    def test_direct_is_delivered_frame(self):
        assert derive_final_pixel_role(OutputComposition.DIRECT) is (
            FinalPixelRole.DELIVERED_FRAME
        )

    def test_layered_is_composited_element(self):
        assert derive_final_pixel_role(OutputComposition.LAYERED) is (
            FinalPixelRole.COMPOSITED_ELEMENT
        )

    def test_hybrid_depends_on_primary(self):
        assert derive_final_pixel_role(
            OutputComposition.HYBRID, region_is_primary=True
        ) is FinalPixelRole.DELIVERED_FRAME
        assert derive_final_pixel_role(
            OutputComposition.HYBRID, region_is_primary=False
        ) is FinalPixelRole.COMPOSITED_ELEMENT


class TestGuidanceSignal:
    def test_rejects_out_of_range(self):
        with pytest.raises(ValueError):
            GuidanceSignal(region="r", guidance_strength=2.0)

    def test_region_profile_carries_guidance_through(self):
        signal = GuidanceSignal(
            region="hero",
            guidance_strength=0.85,
            conditioning=["depth"],
            likeness=LikenessPresence.PERFORMANCE,
            notes="n",
        )
        profile = derive_region_profile(signal)
        assert profile.guidance_strength == 0.85
        assert profile.transformation is TransformationClass.REPAIR
        assert profile.likeness is LikenessPresence.PERFORMANCE
        assert profile.notes == "n"


class TestPipelineRecord:
    def _mixed_record(self) -> PipelineRecord:
        record = PipelineRecord(stage="comp", primary_region="hero")
        record.add_signal(
            GuidanceSignal(
                region="hero",
                guidance_strength=0.98,
                conditioning=["depth", "segmentation"],
                region_specific=True,
                composition=OutputComposition.HYBRID,
                likeness=LikenessPresence.PERFORMANCE,
            )
        )
        record.add_signal(
            GuidanceSignal(
                region="background",
                guidance_strength=0.2,
                conditioning=["depth"],
                composition=OutputComposition.HYBRID,
            )
        )
        return record

    def test_produces_mixed_profile(self):
        profile = self._mixed_record().to_capability_profile()
        assert not profile.is_uniform()
        hero, background = profile.regions
        assert hero.transformation is TransformationClass.ENHANCEMENT
        assert background.transformation is TransformationClass.SYNTHESIS

    def test_primary_region_gets_delivered_frame_under_hybrid(self):
        profile = self._mixed_record().to_capability_profile()
        hero, background = profile.regions
        assert hero.final_pixel is FinalPixelRole.DELIVERED_FRAME
        assert background.final_pixel is FinalPixelRole.COMPOSITED_ELEMENT

    def test_derived_profile_drives_flags(self):
        # The whole point: signals in, governance flags out, no form filled.
        ctx = UseCaseContext(name="Shot 0100")
        profile = self._mixed_record().to_capability_profile()
        flags = profile.derive_flags(ctx)
        assert flags
        # The performer region is the one in question here. The synthesized
        # background is user-conditioned and delivered as a layer, so it
        # raises nothing — under-flagging that would be noise, not safety.
        assert all("hero" in f.description for f in flags)

    def test_synthesized_background_flags_when_delivered_directly(self):
        # Same background, no compositing stage after it: now it is the frame.
        ctx = UseCaseContext(name="Shot 0100")
        record = PipelineRecord(stage="comp")
        record.add_signal(
            GuidanceSignal(
                region="background",
                guidance_strength=0.2,
                conditioning=["depth"],
                composition=OutputComposition.DIRECT,
            )
        )
        flags = record.to_capability_profile().derive_flags(ctx)
        assert any("background" in f.description for f in flags)

    def test_plate_locked_performer_avoids_replica_flag(self):
        ctx = UseCaseContext(name="Shot")
        record = PipelineRecord(stage="s", primary_region="hero")
        record.add_signal(
            GuidanceSignal(
                region="hero",
                guidance_strength=0.99,
                conditioning=["depth", "segmentation"],
                region_specific=True,
                likeness=LikenessPresence.PERFORMANCE,
            )
        )
        flags = record.to_capability_profile().derive_flags(ctx)
        rule_titles = " ".join(f.description for f in flags).lower()
        assert "altered" in rule_titles
        assert not ctx.is_blocked()

    def test_unconstrained_performer_blocks(self):
        ctx = UseCaseContext(name="Shot")
        record = PipelineRecord(stage="s")
        record.add_signal(
            GuidanceSignal(
                region="hero",
                guidance_strength=0.1,
                conditioning=["reference_image"],
                likeness=LikenessPresence.PERFORMANCE,
            )
        )
        record.to_capability_profile().derive_flags(ctx)
        assert ctx.is_blocked()

    def test_round_trip(self):
        record = self._mixed_record()
        restored = PipelineRecord.from_dict(record.to_dict())
        assert restored.stage == record.stage
        assert restored.primary_region == record.primary_region
        assert len(restored.signals) == len(record.signals)
        assert (
            restored.to_capability_profile().to_dict()
            == record.to_capability_profile().to_dict()
        )

    def test_round_trip_preserves_custom_thresholds(self):
        record = PipelineRecord(
            stage="s",
            thresholds=DerivationThresholds(
                enhancement_at=0.99, repair_at=0.9,
                modification_at=0.6, synthesis_below=0.6,
            ),
        )
        record.add_signal(GuidanceSignal(region="r", guidance_strength=0.95))
        restored = PipelineRecord.from_dict(record.to_dict())
        assert restored.thresholds.enhancement_at == 0.99
        assert restored.to_capability_profile().regions[0].transformation is (
            TransformationClass.REPAIR
        )
