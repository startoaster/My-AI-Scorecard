"""Tests for human authorship evidence records."""

import pytest

from ai_use_case_context.authorship import AuthorshipEvidence, AuthorshipRecord
from ai_use_case_context.capability import (
    CapabilityProfile,
    ControlMode,
    FinalPixelRole,
    LikenessPresence,
    RegionProfile,
    TransformationClass,
)


def evidence(**overrides) -> AuthorshipEvidence:
    defaults = dict(
        region="test",
        transformation=TransformationClass.SYNTHESIS,
        control=ControlMode.PRESET,
    )
    defaults.update(overrides)
    return AuthorshipEvidence(**defaults)


class TestAuthorshipEvidence:
    def test_introduces_new_content_follows_transformation(self):
        assert evidence(
            transformation=TransformationClass.SYNTHESIS
        ).introduces_new_content
        assert not evidence(
            transformation=TransformationClass.EXTRACTION
        ).introduces_new_content

    def test_unknown_transformation_is_not_generative(self):
        assert not evidence(transformation=None).introduces_new_content

    def test_evidence_points_counts_distinct_contributions(self):
        e = evidence(
            contributions=["authored depth map", "hand-corrected output"],
            iterations=3,
            human_reviewed=True,
            human_modified=True,
            control=ControlMode.COMPOSED,
        )
        # 2 contributions + iterations + reviewed + modified + strong control
        assert e.evidence_points == 6

    def test_bare_evidence_has_no_points(self):
        assert evidence().evidence_points == 0

    def test_iterations_count_once_regardless_of_number(self):
        assert evidence(iterations=1).evidence_points == 1
        assert evidence(iterations=50).evidence_points == 1

    def test_round_trip(self):
        original = evidence(
            region="hero",
            contributions=["a"],
            iterations=2,
            human_reviewed=True,
            human_modified=False,
            control=ControlMode.CONDITIONED,
            transformation=TransformationClass.MODIFICATION,
            guidance_strength=0.4,
            notes="n",
        )
        assert AuthorshipEvidence.from_dict(original.to_dict()) == original

    def test_round_trip_with_none_fields(self):
        original = AuthorshipEvidence(region="r")
        assert AuthorshipEvidence.from_dict(original.to_dict()) == original


class TestAuthorshipRecord:
    def test_generative_regions_exclude_non_generative(self):
        record = AuthorshipRecord(work="W")
        record.add_evidence(
            evidence(region="analysis", transformation=TransformationClass.EXTRACTION)
        )
        record.add_evidence(
            evidence(region="bg", transformation=TransformationClass.SYNTHESIS)
        )
        assert [e.region for e in record.generative_regions()] == ["bg"]

    def test_undocumented_regions_flagged(self):
        record = AuthorshipRecord(work="W")
        record.add_evidence(evidence(region="bare"))
        record.add_evidence(
            evidence(region="documented", contributions=["authored prompt"])
        )
        assert [e.region for e in record.undocumented_regions()] == ["bare"]

    def test_thin_evidence_cutoff_is_adjustable(self):
        record = AuthorshipRecord(work="W")
        record.add_evidence(
            evidence(region="one_point", contributions=["a"])
        )
        assert record.thin_evidence_regions(minimum_points=1) == []
        assert len(record.thin_evidence_regions(minimum_points=2)) == 1

    def test_non_generative_regions_never_reported_as_thin(self):
        # No AI-introduced content means no authorship question to answer.
        record = AuthorshipRecord(work="W")
        record.add_evidence(
            evidence(region="roto", transformation=TransformationClass.EXTRACTION)
        )
        assert record.thin_evidence_regions() == []
        assert record.undocumented_regions() == []

    def test_from_capability_profile_carries_recorded_fields(self):
        profile = CapabilityProfile(name="cap", description="d")
        profile.add_region(
            RegionProfile(
                region="hero",
                transformation=TransformationClass.SYNTHESIS,
                control=ControlMode.CONDITIONED,
                likeness=LikenessPresence.PERFORMANCE,
                final_pixel=FinalPixelRole.DELIVERED_FRAME,
                guidance_strength=0.3,
                notes="n",
            )
        )
        record = AuthorshipRecord.from_capability_profile(profile)
        assert record.work == "cap"
        e = record.evidence[0]
        assert e.region == "hero"
        assert e.transformation is TransformationClass.SYNTHESIS
        assert e.control is ControlMode.CONDITIONED
        assert e.guidance_strength == 0.3

    def test_seeded_record_has_no_human_contribution_yet(self):
        # A pipeline can report what it did; only a person can report what
        # they contributed. The seeded record must show that gap, not hide it.
        profile = CapabilityProfile(name="cap")
        profile.add_region(
            RegionProfile(
                region="hero",
                transformation=TransformationClass.SYNTHESIS,
                control=ControlMode.CONDITIONED,
            )
        )
        record = AuthorshipRecord.from_capability_profile(profile)
        assert len(record.undocumented_regions()) == 0  # strong control scores
        record2 = AuthorshipRecord.from_capability_profile(
            _profile_with_control(ControlMode.PRESET)
        )
        assert len(record2.undocumented_regions()) == 1

    def test_summary_states_it_is_not_a_determination(self):
        record = AuthorshipRecord(work="W")
        record.add_evidence(evidence(region="r", contributions=["a"]))
        text = record.summary()
        assert "does not determine" in text
        assert "threshold" in text

    def test_summary_marks_undocumented_regions(self):
        record = AuthorshipRecord(work="W")
        record.add_evidence(evidence(region="bare"))
        text = record.summary()
        assert "No human contribution recorded" in text
        assert "bare" in text

    def test_summary_lists_contributions(self):
        record = AuthorshipRecord(work="W")
        record.add_evidence(
            evidence(region="hero", contributions=["authored depth map"])
        )
        assert "authored depth map" in record.summary()

    def test_round_trip(self):
        record = AuthorshipRecord(
            work="W", description="d", compiled_by="Someone"
        )
        record.add_evidence(
            evidence(region="hero", contributions=["a"], iterations=2)
        )
        restored = AuthorshipRecord.from_dict(record.to_dict())
        assert restored.work == record.work
        assert restored.compiled_by == record.compiled_by
        assert restored.evidence == record.evidence
        assert restored.compiled_at == record.compiled_at


def _profile_with_control(control: ControlMode) -> CapabilityProfile:
    profile = CapabilityProfile(name="cap")
    profile.add_region(
        RegionProfile(
            region="hero",
            transformation=TransformationClass.SYNTHESIS,
            control=control,
        )
    )
    return profile
