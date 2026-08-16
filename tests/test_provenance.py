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


# ---------------------------------------------------------------------------
# Flag derivation
# ---------------------------------------------------------------------------

from ai_use_case_context.authority import Authority as _Authority
from ai_use_case_context.core import (
    RiskDimension as _RiskDimension,
    RiskLevel as _RiskLevel,
    UseCaseContext as _UseCaseContext,
)
from ai_use_case_context.provenance import (
    DEFAULT_PROVENANCE_RULES as _RULES,
    ProvenanceRule as _ProvenanceRule,
)


def _clean_card() -> ProvenanceCard:
    return ProvenanceCard(
        dataset_name="Clean",
        generation_flag=GenerationFlag.HUMAN_ORIGIN,
        generation_confidence=1.0,
        sources=[
            DataSource(
                name="Licensed A",
                license_compliance=LicenseCompliance.VERIFIED,
                copyright_holder="Rights Co",
                opt_out_honored=True,
            )
        ],
    )


def _fired(card, guard=None) -> set:
    return {r.rule_id for r in _RULES if r.applies(card, guard)}


class TestProvenanceFlagDerivation:
    def test_clean_card_fires_nothing(self):
        assert _fired(_clean_card()) == set()

    def test_non_compliant_licence_is_critical(self):
        card = _clean_card()
        card.sources.append(
            DataSource(name="Bad", license_compliance=LicenseCompliance.NON_COMPLIANT)
        )
        rule = next(r for r in _RULES if r.rule_id == "NON_COMPLIANT_LICENCE")
        assert rule.applies(card, None)
        assert rule.level is _RiskLevel.CRITICAL
        assert rule.authority is _Authority.BINDING_CONTRACT

    def test_unknown_licence_is_lower_than_non_compliant(self):
        card = _clean_card()
        card.sources.append(
            DataSource(name="Unknown", license_compliance=LicenseCompliance.UNKNOWN)
        )
        fired = _fired(card)
        assert "UNKNOWN_LICENCE_STATUS" in fired
        assert "NON_COMPLIANT_LICENCE" not in fired

    def test_opt_out_gap_flags_under_statute(self):
        card = _clean_card()
        card.sources[0].opt_out_honored = False
        rule = next(r for r in _RULES if r.rule_id == "OPT_OUT_NOT_HONOURED")
        assert rule.applies(card, None)
        assert rule.authority is _Authority.STATUTE

    def test_no_sources_documented(self):
        card = ProvenanceCard(
            dataset_name="Empty",
            generation_flag=GenerationFlag.HUMAN_ORIGIN,
            generation_confidence=1.0,
        )
        assert "NO_SOURCES_DOCUMENTED" in _fired(card)

    def test_unknown_origin_below_confidence_threshold(self):
        card = _clean_card()
        card.generation_flag = GenerationFlag.UNKNOWN
        card.generation_confidence = 0.5
        assert "UNKNOWN_GENERATION_ORIGIN" in _fired(card)

    def test_unknown_origin_with_high_confidence_does_not_flag(self):
        card = _clean_card()
        card.generation_flag = GenerationFlag.UNKNOWN
        card.generation_confidence = 0.9
        assert "UNKNOWN_GENERATION_ORIGIN" not in _fired(card)

    def test_synthetic_over_cap(self):
        guard = ModelCollapseGuard(
            max_synthetic_percentage=30.0, actual_synthetic_percentage=55.0
        )
        assert "SYNTHETIC_SHARE_OVER_CAP" in _fired(_clean_card(), guard)

    def test_synthetic_within_cap_does_not_flag(self):
        guard = ModelCollapseGuard(
            max_synthetic_percentage=30.0, actual_synthetic_percentage=10.0,
            vendor_disclosure_received=True,
        )
        assert _fired(_clean_card(), guard) == set()

    def test_no_guard_means_no_guard_rules(self):
        assert _fired(_clean_card(), None) == set()

    def test_high_stakes_without_disclosure(self):
        guard = ModelCollapseGuard(
            high_stakes_domain=True, vendor_disclosure_received=False
        )
        assert "NO_SYNTHETIC_DISCLOSURE_HIGH_STAKES" in _fired(_clean_card(), guard)

    def test_derive_flags_lands_on_context(self):
        ctx = _UseCaseContext(name="Dataset review")
        card = _clean_card()
        card.sources.append(
            DataSource(name="Bad", license_compliance=LicenseCompliance.NON_COMPLIANT)
        )
        flags = card.derive_flags(ctx)
        assert len(flags) == 1
        assert ctx.is_blocked()
        assert ctx.get_enforceable_flags()

    def test_coverage_score_and_risk_are_independent(self):
        # A fully documented card can still be unusable: documenting a
        # non-compliant licence raises the coverage score and the risk both.
        card = ProvenanceCard(
            dataset_name="Documented but unusable",
            generation_flag=GenerationFlag.HUMAN_ORIGIN,
            generation_confidence=1.0,
            sources=[
                DataSource(
                    name="Bad",
                    license_type="Proprietary",
                    license_compliance=LicenseCompliance.NON_COMPLIANT,
                    capture_method=CaptureMethod.CRAWL,
                    collection_date=datetime.now(),
                )
            ],
        )
        ctx = _UseCaseContext(name="Dataset review")
        card.derive_flags(ctx)
        assert card.provenance_complete is True
        assert ctx.is_blocked()

    def test_custom_rules_replace_defaults(self):
        ctx = _UseCaseContext(name="T")
        catch_all = _ProvenanceRule(
            rule_id="ALWAYS", title="always",
            applies=lambda c, g: True,
            dimension=_RiskDimension.QUALITY,
            level=_RiskLevel.LOW,
            describe=lambda c, g: "always",
        )
        flags = _clean_card().derive_flags(ctx, rules=[catch_all])
        assert [f.description for f in flags] == ["always"]
