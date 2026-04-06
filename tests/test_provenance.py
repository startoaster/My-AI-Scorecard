"""Tests for data provenance and lineage tracking module."""

import pytest
from datetime import datetime

from ai_use_case_context.provenance import (
    GenerationFlag,
    CaptureMethod,
    TransformationType,
    LicenseCompliance,
    DataSource,
    TransformationRecord,
    DatasetVersion,
    ProvenanceCard,
    ModelCollapseGuard,
    ProvenanceResult,
    evaluate_provenance,
)


# ---------------------------------------------------------------------------
# DataSource
# ---------------------------------------------------------------------------

class TestDataSource:
    def test_defaults(self):
        s = DataSource(name="Test Source")
        assert s.name == "Test Source"
        assert s.license_compliance == LicenseCompliance.UNKNOWN
        assert s.capture_method == CaptureMethod.OTHER

    def test_round_trip(self):
        s = DataSource(
            name="MoCap Library",
            url="https://example.com",
            collection_date=datetime(2025, 1, 15),
            license_type="Commercial",
            license_compliance=LicenseCompliance.VERIFIED,
            capture_method=CaptureMethod.MOTION_CAPTURE,
            copyright_holder="Studio X",
            opt_out_honored=True,
        )
        restored = DataSource.from_dict(s.to_dict())
        assert restored.name == "MoCap Library"
        assert restored.license_compliance == LicenseCompliance.VERIFIED
        assert restored.capture_method == CaptureMethod.MOTION_CAPTURE
        assert restored.opt_out_honored is True


# ---------------------------------------------------------------------------
# TransformationRecord
# ---------------------------------------------------------------------------

class TestTransformationRecord:
    def test_round_trip(self):
        t = TransformationRecord(
            transformation_type=TransformationType.DEDUPLICATION,
            description="Removed duplicate frames",
            applied_by="Pipeline v2",
            parameters={"threshold": 0.95},
            input_hash="abc123",
            output_hash="def456",
        )
        restored = TransformationRecord.from_dict(t.to_dict())
        assert restored.transformation_type == TransformationType.DEDUPLICATION
        assert restored.parameters["threshold"] == 0.95
        assert restored.input_hash == "abc123"


# ---------------------------------------------------------------------------
# DatasetVersion (bi-temporal lineage)
# ---------------------------------------------------------------------------

class TestDatasetVersion:
    def test_round_trip(self):
        now = datetime.now()
        v = DatasetVersion(
            version_id="v2.1.0",
            dataset_name="Hero MoCap",
            valid_from=now,
            record_count=10000,
            size_bytes=5_000_000,
            checksum="sha256:abc",
            parent_version_id="v2.0.0",
            tags=["production", "verified"],
        )
        restored = DatasetVersion.from_dict(v.to_dict())
        assert restored.version_id == "v2.1.0"
        assert restored.record_count == 10000
        assert restored.parent_version_id == "v2.0.0"
        assert "production" in restored.tags


# ---------------------------------------------------------------------------
# ProvenanceCard
# ---------------------------------------------------------------------------

class TestProvenanceCard:
    def test_empty_card(self):
        card = ProvenanceCard(dataset_name="Test")
        assert card.all_licenses_verified is False
        assert card.provenance_complete is False

    def test_all_licenses_verified(self):
        card = ProvenanceCard(
            dataset_name="Test",
            sources=[
                DataSource("S1", license_compliance=LicenseCompliance.VERIFIED),
                DataSource("S2", license_compliance=LicenseCompliance.VERIFIED),
            ],
        )
        assert card.all_licenses_verified is True

    def test_not_all_licenses_verified(self):
        card = ProvenanceCard(
            dataset_name="Test",
            sources=[
                DataSource("S1", license_compliance=LicenseCompliance.VERIFIED),
                DataSource("S2", license_compliance=LicenseCompliance.UNKNOWN),
            ],
        )
        assert card.all_licenses_verified is False

    def test_opt_out_gaps(self):
        card = ProvenanceCard(
            dataset_name="Test",
            sources=[
                DataSource("S1", copyright_holder="Artist A", opt_out_honored=False),
            ],
        )
        assert card.has_opt_out_gaps is True

    def test_no_opt_out_gaps(self):
        card = ProvenanceCard(
            dataset_name="Test",
            sources=[
                DataSource("S1", copyright_holder="Artist A", opt_out_honored=True),
            ],
        )
        assert card.has_opt_out_gaps is False

    def test_provenance_complete(self):
        card = ProvenanceCard(
            dataset_name="Test",
            sources=[
                DataSource("S1", license_compliance=LicenseCompliance.VERIFIED),
            ],
            generation_flag=GenerationFlag.HUMAN_ORIGIN,
            generation_confidence=0.95,
        )
        assert card.provenance_complete is True

    def test_provenance_incomplete_unknown_flag(self):
        card = ProvenanceCard(
            dataset_name="Test",
            sources=[
                DataSource("S1", license_compliance=LicenseCompliance.VERIFIED),
            ],
            generation_flag=GenerationFlag.UNKNOWN,
            generation_confidence=0.5,
        )
        assert card.provenance_complete is False

    def test_round_trip(self):
        card = ProvenanceCard(
            dataset_name="Hero MoCap v2",
            sources=[DataSource("S1", license_type="Commercial")],
            generation_flag=GenerationFlag.HUMAN_ORIGIN,
            generation_confidence=0.95,
            transformations=[
                TransformationRecord(TransformationType.CLEANING, "Cleaned noise"),
            ],
            versions=[
                DatasetVersion("v1.0", "Hero MoCap v2"),
            ],
            synthetic_percentage=5.0,
        )
        restored = ProvenanceCard.from_dict(card.to_dict())
        assert restored.dataset_name == "Hero MoCap v2"
        assert len(restored.sources) == 1
        assert restored.generation_flag == GenerationFlag.HUMAN_ORIGIN
        assert len(restored.transformations) == 1
        assert len(restored.versions) == 1
        assert restored.synthetic_percentage == 5.0


# ---------------------------------------------------------------------------
# ModelCollapseGuard
# ---------------------------------------------------------------------------

class TestModelCollapseGuard:
    def test_within_limits(self):
        g = ModelCollapseGuard(
            max_synthetic_percentage=30,
            actual_synthetic_percentage=10,
            vendor_disclosure_received=True,
        )
        assert g.within_limits is True
        assert len(g.violations) == 0

    def test_exceeds_limits(self):
        g = ModelCollapseGuard(
            max_synthetic_percentage=30,
            actual_synthetic_percentage=50,
            vendor_disclosure_received=True,
        )
        assert g.within_limits is False
        assert any("exceeds" in v for v in g.violations)

    def test_no_disclosure(self):
        g = ModelCollapseGuard(vendor_disclosure_received=False)
        assert len(g.violations) > 0

    def test_high_stakes_stricter(self):
        g = ModelCollapseGuard(
            high_stakes_domain=True,
            vendor_disclosure_received=False,
            actual_synthetic_percentage=5,
        )
        assert len(g.violations) >= 2

    def test_round_trip(self):
        g = ModelCollapseGuard(
            max_synthetic_percentage=20,
            actual_synthetic_percentage=15,
            high_stakes_domain=True,
        )
        restored = ModelCollapseGuard.from_dict(g.to_dict())
        assert restored.max_synthetic_percentage == 20
        assert restored.high_stakes_domain is True


# ---------------------------------------------------------------------------
# evaluate_provenance
# ---------------------------------------------------------------------------

class TestEvaluateProvenance:
    def test_empty_card(self):
        card = ProvenanceCard(dataset_name="Empty")
        result = evaluate_provenance(card)
        assert result.score <= 15.0  # low score, only opt-out may pass vacuously
        assert len(result.gaps) > 0

    def test_complete_card_high_score(self):
        card = ProvenanceCard(
            dataset_name="Complete",
            sources=[
                DataSource(
                    name="Licensed Source",
                    license_type="Commercial",
                    license_compliance=LicenseCompliance.VERIFIED,
                    capture_method=CaptureMethod.MOTION_CAPTURE,
                    collection_date=datetime.now(),
                    copyright_holder="Studio",
                    opt_out_honored=True,
                ),
            ],
            generation_flag=GenerationFlag.HUMAN_ORIGIN,
            generation_confidence=0.95,
            transformations=[
                TransformationRecord(TransformationType.CLEANING, "Cleaned"),
            ],
            versions=[
                DatasetVersion("v1.0", "Complete"),
            ],
        )
        result = evaluate_provenance(card)
        assert result.score == 100.0
        assert len(result.gaps) == 0

    def test_with_model_collapse_guard_violations(self):
        card = ProvenanceCard(
            dataset_name="Test",
            sources=[DataSource("S1", license_compliance=LicenseCompliance.VERIFIED)],
            generation_flag=GenerationFlag.HUMAN_ORIGIN,
            generation_confidence=0.9,
        )
        guard = ModelCollapseGuard(
            max_synthetic_percentage=10,
            actual_synthetic_percentage=50,
            vendor_disclosure_received=False,
        )
        result = evaluate_provenance(card, guard)
        assert any("Model collapse" in g for g in result.gaps)

    def test_result_round_trip(self):
        r = ProvenanceResult(
            score=75.0,
            gaps=["Missing lineage"],
            recommendations=["Add lineage"],
        )
        restored = ProvenanceResult.from_dict(r.to_dict())
        assert restored.score == 75.0

    def test_partial_sources_score(self):
        card = ProvenanceCard(
            dataset_name="Partial",
            sources=[
                DataSource(
                    name="Good Source",
                    license_type="CC-BY",
                    license_compliance=LicenseCompliance.VERIFIED,
                    capture_method=CaptureMethod.API,
                    collection_date=datetime.now(),
                ),
                DataSource(name="Bad Source"),  # minimal metadata
            ],
            generation_flag=GenerationFlag.HYBRID,
            generation_confidence=0.7,
        )
        result = evaluate_provenance(card)
        assert 0 < result.score < 100
