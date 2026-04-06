"""Tests for AI vendor scorecard evaluation module."""

import pytest
from datetime import datetime

from ai_use_case_context.vendor_scorecard import (
    ScorecardDimension,
    VendorTier,
    DEFAULT_WEIGHTS,
    DEFAULT_TIER_THRESHOLDS,
    DimensionScore,
    VendorQuestion,
    KBYUTSScores,
    CopyrightAssessment,
    VendorScorecard,
    VendorResult,
    evaluate_vendor,
    essential_vendor_questions,
)


# ---------------------------------------------------------------------------
# DimensionScore
# ---------------------------------------------------------------------------

class TestDimensionScore:
    def test_defaults(self):
        d = DimensionScore()
        assert d.score == 0.0

    def test_round_trip(self):
        d = DimensionScore(score=85.0, evidence="SOC 2 cert", gaps="Minor gap")
        restored = DimensionScore.from_dict(d.to_dict())
        assert restored.score == 85.0
        assert restored.evidence == "SOC 2 cert"


# ---------------------------------------------------------------------------
# VendorQuestion
# ---------------------------------------------------------------------------

class TestVendorQuestion:
    def test_round_trip(self):
        q = VendorQuestion(
            question_id="VQ-001",
            question="Encryption standards?",
            dimension=ScorecardDimension.GOVERNANCE_SECURITY,
            response="AES-256",
            satisfactory=True,
        )
        restored = VendorQuestion.from_dict(q.to_dict())
        assert restored.question_id == "VQ-001"
        assert restored.dimension == ScorecardDimension.GOVERNANCE_SECURITY
        assert restored.satisfactory is True


# ---------------------------------------------------------------------------
# KBYUTSScores
# ---------------------------------------------------------------------------

class TestKBYUTSScores:
    def test_composite_all_100(self):
        k = KBYUTSScores(
            training_data_transparency=100,
            creative_professional_treatment=100,
            governance_maturity=100,
            output_attribution=100,
            legal_risk=100,
        )
        assert k.composite_score == 100.0

    def test_composite_weighted(self):
        k = KBYUTSScores(
            training_data_transparency=80,
            creative_professional_treatment=60,
            governance_maturity=40,
            output_attribution=20,
            legal_risk=10,
        )
        expected = 80 * 0.25 + 60 * 0.20 + 40 * 0.20 + 20 * 0.20 + 10 * 0.15
        assert abs(k.composite_score - expected) < 0.01

    def test_round_trip(self):
        k = KBYUTSScores(training_data_transparency=90, legal_risk=75)
        restored = KBYUTSScores.from_dict(k.to_dict())
        assert restored.training_data_transparency == 90
        assert restored.legal_risk == 75


# ---------------------------------------------------------------------------
# CopyrightAssessment
# ---------------------------------------------------------------------------

class TestCopyrightAssessment:
    def test_low_risk(self):
        c = CopyrightAssessment(
            training_data_lawfully_obtained=True,
            license_verification_documented=True,
            opt_out_compliance_process=True,
            indemnification_for_ai_outputs=True,
        )
        assert c.risk_level == "low"
        assert len(c.gaps) == 0

    def test_critical_risk_litigation(self):
        c = CopyrightAssessment(pending_litigation=True)
        assert c.risk_level == "critical"

    def test_critical_risk_competes_unlawful(self):
        c = CopyrightAssessment(
            competes_with_training_sources=True,
            training_data_lawfully_obtained=False,
        )
        assert c.risk_level == "critical"

    def test_high_risk(self):
        c = CopyrightAssessment(
            training_data_lawfully_obtained=False,
            license_verification_documented=False,
        )
        assert c.risk_level == "high"

    def test_medium_risk(self):
        c = CopyrightAssessment(
            training_data_lawfully_obtained=True,
            license_verification_documented=True,
            opt_out_compliance_process=False,
        )
        assert c.risk_level == "medium"

    def test_gaps_comprehensive(self):
        c = CopyrightAssessment()  # all defaults = False
        gaps = c.gaps
        assert any("lawfully" in g.lower() for g in gaps)
        assert any("license" in g.lower() for g in gaps)
        assert any("opt-out" in g.lower() for g in gaps)
        assert any("indemnification" in g.lower() for g in gaps)

    def test_round_trip(self):
        c = CopyrightAssessment(
            training_data_lawfully_obtained=True,
            pending_litigation=True,
        )
        restored = CopyrightAssessment.from_dict(c.to_dict())
        assert restored.training_data_lawfully_obtained is True
        assert restored.pending_litigation is True


# ---------------------------------------------------------------------------
# VendorScorecard
# ---------------------------------------------------------------------------

class TestVendorScorecard:
    def test_dimension_scores(self):
        sc = VendorScorecard(
            vendor_name="Acme AI",
            data_provenance=DimensionScore(score=80),
            governance_security=DimensionScore(score=70),
            ethics_compliance=DimensionScore(score=60),
            technical_fit=DimensionScore(score=50),
            commercial_terms=DimensionScore(score=40),
            operating_model=DimensionScore(score=30),
        )
        scores = sc.dimension_scores()
        assert scores[ScorecardDimension.DATA_PROVENANCE] == 80
        assert scores[ScorecardDimension.OPERATING_MODEL] == 30

    def test_round_trip(self):
        sc = VendorScorecard(
            vendor_name="Acme AI",
            data_provenance=DimensionScore(score=80),
            kbyuts=KBYUTSScores(training_data_transparency=90),
            copyright=CopyrightAssessment(pending_litigation=True),
            questions=[
                VendorQuestion("VQ-001", "Q?", ScorecardDimension.DATA_PROVENANCE),
            ],
        )
        restored = VendorScorecard.from_dict(sc.to_dict())
        assert restored.vendor_name == "Acme AI"
        assert restored.data_provenance.score == 80
        assert restored.kbyuts.training_data_transparency == 90
        assert restored.copyright.pending_litigation is True
        assert len(restored.questions) == 1


# ---------------------------------------------------------------------------
# evaluate_vendor
# ---------------------------------------------------------------------------

class TestEvaluateVendor:
    def test_preferred_tier(self):
        sc = VendorScorecard(
            vendor_name="Top Vendor",
            data_provenance=DimensionScore(score=90),
            governance_security=DimensionScore(score=90),
            ethics_compliance=DimensionScore(score=90),
            technical_fit=DimensionScore(score=90),
            commercial_terms=DimensionScore(score=90),
            operating_model=DimensionScore(score=90),
        )
        result = evaluate_vendor(sc)
        assert result.tier == VendorTier.PREFERRED
        assert result.overall_score == 90.0

    def test_not_approved_tier(self):
        sc = VendorScorecard(
            vendor_name="Bad Vendor",
            data_provenance=DimensionScore(score=10),
            governance_security=DimensionScore(score=10),
            ethics_compliance=DimensionScore(score=10),
            technical_fit=DimensionScore(score=10),
            commercial_terms=DimensionScore(score=10),
            operating_model=DimensionScore(score=10),
        )
        result = evaluate_vendor(sc)
        assert result.tier == VendorTier.NOT_APPROVED
        assert result.overall_score == 10.0

    def test_conditional_tier(self):
        sc = VendorScorecard(
            vendor_name="Mid Vendor",
            data_provenance=DimensionScore(score=50),
            governance_security=DimensionScore(score=50),
            ethics_compliance=DimensionScore(score=50),
            technical_fit=DimensionScore(score=50),
            commercial_terms=DimensionScore(score=50),
            operating_model=DimensionScore(score=50),
        )
        result = evaluate_vendor(sc)
        assert result.tier == VendorTier.CONDITIONAL

    def test_gaps_identified(self):
        sc = VendorScorecard(
            vendor_name="Weak Vendor",
            data_provenance=DimensionScore(score=30),
            governance_security=DimensionScore(score=30),
        )
        result = evaluate_vendor(sc)
        assert len(result.gaps) > 0
        assert len(result.recommendations) > 0

    def test_copyright_risk_integrated(self):
        sc = VendorScorecard(
            vendor_name="Risky Vendor",
            data_provenance=DimensionScore(score=70),
            governance_security=DimensionScore(score=70),
            ethics_compliance=DimensionScore(score=70),
            technical_fit=DimensionScore(score=70),
            commercial_terms=DimensionScore(score=70),
            operating_model=DimensionScore(score=70),
            copyright=CopyrightAssessment(pending_litigation=True),
        )
        result = evaluate_vendor(sc)
        assert result.copyright_risk == "critical"
        assert any("copyright" in r.lower() for r in result.recommendations)

    def test_kbyuts_low_score_warning(self):
        sc = VendorScorecard(
            vendor_name="Low KBYUTS",
            data_provenance=DimensionScore(score=70),
            governance_security=DimensionScore(score=70),
            ethics_compliance=DimensionScore(score=70),
            technical_fit=DimensionScore(score=70),
            commercial_terms=DimensionScore(score=70),
            operating_model=DimensionScore(score=70),
            kbyuts=KBYUTSScores(
                training_data_transparency=20,
                creative_professional_treatment=20,
                governance_maturity=20,
                output_attribution=20,
                legal_risk=20,
            ),
        )
        result = evaluate_vendor(sc)
        assert any("KBYUTS" in r for r in result.recommendations)

    def test_custom_weights(self):
        sc = VendorScorecard(
            vendor_name="Custom",
            data_provenance=DimensionScore(score=100),
            governance_security=DimensionScore(score=0),
            ethics_compliance=DimensionScore(score=0),
            technical_fit=DimensionScore(score=0),
            commercial_terms=DimensionScore(score=0),
            operating_model=DimensionScore(score=0),
        )
        # Give all weight to data provenance
        custom_weights = {
            ScorecardDimension.DATA_PROVENANCE: 1.0,
            ScorecardDimension.GOVERNANCE_SECURITY: 0.0,
            ScorecardDimension.ETHICS_COMPLIANCE: 0.0,
            ScorecardDimension.TECHNICAL_FIT: 0.0,
            ScorecardDimension.COMMERCIAL_TERMS: 0.0,
            ScorecardDimension.OPERATING_MODEL: 0.0,
        }
        result = evaluate_vendor(sc, weights=custom_weights)
        assert result.overall_score == 100.0

    def test_result_round_trip(self):
        r = VendorResult(
            overall_score=75.0,
            tier=VendorTier.APPROVED,
            dimension_scores={"Data & Provenance": 80.0},
            gaps=["Gap 1"],
            recommendations=["Rec 1"],
            copyright_risk="medium",
        )
        restored = VendorResult.from_dict(r.to_dict())
        assert restored.overall_score == 75.0
        assert restored.tier == VendorTier.APPROVED


# ---------------------------------------------------------------------------
# Default weights
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_weights_sum_to_one(self):
        assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 0.001

    def test_all_dimensions_have_weight(self):
        for dim in ScorecardDimension:
            assert dim in DEFAULT_WEIGHTS

    def test_tier_thresholds_ordered(self):
        assert DEFAULT_TIER_THRESHOLDS[VendorTier.PREFERRED] > DEFAULT_TIER_THRESHOLDS[VendorTier.APPROVED]
        assert DEFAULT_TIER_THRESHOLDS[VendorTier.APPROVED] > DEFAULT_TIER_THRESHOLDS[VendorTier.CONDITIONAL]
        assert DEFAULT_TIER_THRESHOLDS[VendorTier.CONDITIONAL] > DEFAULT_TIER_THRESHOLDS[VendorTier.NOT_APPROVED]


# ---------------------------------------------------------------------------
# Essential vendor questions
# ---------------------------------------------------------------------------

class TestEssentialVendorQuestions:
    def test_not_empty(self):
        qs = essential_vendor_questions()
        assert len(qs) > 0

    def test_all_have_ids(self):
        qs = essential_vendor_questions()
        ids = [q.question_id for q in qs]
        assert len(ids) == len(set(ids))  # unique IDs

    def test_covers_multiple_dimensions(self):
        qs = essential_vendor_questions()
        dims = {q.dimension for q in qs}
        assert len(dims) >= 4  # should cover at least 4 dimensions

    def test_all_questions_nonempty(self):
        qs = essential_vendor_questions()
        for q in qs:
            assert q.question, f"Empty question for {q.question_id}"
