"""Tests for AI vendor scorecard evaluation module."""

import pytest
from datetime import datetime

from ai_use_case_context.authority import Authority
from ai_use_case_context.core import RiskDimension, RiskLevel, UseCaseContext
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
    tier_from_flags,
    VendorRule,
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
            eu_dsm_article4_compliance=True,
            eu_training_data_summary_published=True,
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


# ---------------------------------------------------------------------------
# Weight validation and score reporting
# ---------------------------------------------------------------------------

class TestWeightValidation:
    def _scorecard(self):
        return VendorScorecard(
            vendor_name="X", data_provenance=DimensionScore(score=100)
        )

    def test_weights_not_summing_to_one_are_rejected(self):
        # Previously this silently returned a composite of 500 on a 0-100 scale.
        bad = {d: 5.0 for d in ScorecardDimension}
        with pytest.raises(ValueError) as exc:
            evaluate_vendor(self._scorecard(), weights=bad)
        assert "sum to 1.0" in str(exc.value)

    def test_weights_summing_below_one_are_rejected(self):
        low = {d: 0.05 for d in ScorecardDimension}
        with pytest.raises(ValueError):
            evaluate_vendor(self._scorecard(), weights=low)

    def test_negative_weights_are_rejected(self):
        weights = dict(DEFAULT_WEIGHTS)
        weights[ScorecardDimension.DATA_PROVENANCE] = -0.25
        weights[ScorecardDimension.OPERATING_MODEL] = 0.60
        with pytest.raises(ValueError) as exc:
            evaluate_vendor(self._scorecard(), weights=weights)
        assert "negative" in str(exc.value)

    def test_float_error_within_tolerance_is_accepted(self):
        weights = {
            ScorecardDimension.DATA_PROVENANCE: 0.1,
            ScorecardDimension.GOVERNANCE_SECURITY: 0.2,
            ScorecardDimension.ETHICS_COMPLIANCE: 0.2,
            ScorecardDimension.TECHNICAL_FIT: 0.2,
            ScorecardDimension.COMMERCIAL_TERMS: 0.2,
            ScorecardDimension.OPERATING_MODEL: 0.1,
        }
        evaluate_vendor(self._scorecard(), weights=weights)

    def test_defaults_still_pass_validation(self):
        evaluate_vendor(self._scorecard())


class TestScoreReporting:
    def test_dimension_scores_are_raw_not_weighted(self):
        sc = VendorScorecard(
            vendor_name="Y", data_provenance=DimensionScore(score=80)
        )
        result = evaluate_vendor(sc)
        assert result.dimension_scores["Data & Provenance"] == 80.0

    def test_weighted_contributions_sum_to_overall(self):
        sc = VendorScorecard(
            vendor_name="Y",
            data_provenance=DimensionScore(score=80),
            governance_security=DimensionScore(score=60),
            ethics_compliance=DimensionScore(score=40),
            technical_fit=DimensionScore(score=90),
            commercial_terms=DimensionScore(score=70),
            operating_model=DimensionScore(score=50),
        )
        result = evaluate_vendor(sc)
        assert abs(
            sum(result.weighted_contributions.values()) - result.overall_score
        ) < 0.001

    def test_weighted_contribution_applies_the_weight(self):
        sc = VendorScorecard(
            vendor_name="Y", data_provenance=DimensionScore(score=80)
        )
        result = evaluate_vendor(sc)
        # 80 * 0.25
        assert result.weighted_contributions["Data & Provenance"] == 20.0

    def test_contributions_round_trip(self):
        sc = VendorScorecard(
            vendor_name="Y", data_provenance=DimensionScore(score=80)
        )
        result = evaluate_vendor(sc)
        restored = VendorResult.from_dict(result.to_dict())
        assert restored.weighted_contributions["Data & Provenance"] == 20.0

    def test_legacy_payload_without_contributions_loads(self):
        legacy = {
            "overall_score": 75.0,
            "tier": "approved",
            "dimension_scores": {"Data & Provenance": 80.0},
            "gaps": [],
            "recommendations": [],
            "copyright_risk": "low",
        }
        restored = VendorResult.from_dict(legacy)
        assert restored.weighted_contributions == {}


# ---------------------------------------------------------------------------
# Flag derivation — the non-compensatory path
# ---------------------------------------------------------------------------

class TestVendorFlagDerivation:
    def _strong_but_litigating(self):
        return VendorScorecard(
            vendor_name="Z",
            copyright=CopyrightAssessment(
                pending_litigation=True,
                competes_with_training_sources=True,
            ),
            data_provenance=DimensionScore(score=95),
            governance_security=DimensionScore(score=95),
            ethics_compliance=DimensionScore(score=95),
            technical_fit=DimensionScore(score=95),
            commercial_terms=DimensionScore(score=95),
            operating_model=DimensionScore(score=95),
        )

    def test_composite_still_rates_it_preferred(self):
        # Documents the behaviour the flag path exists to replace: the
        # weighted average lets strength elsewhere absorb a disqualifying fact.
        assert evaluate_vendor(self._strong_but_litigating()).tier is (
            VendorTier.PREFERRED
        )

    def test_flag_path_rates_the_same_vendor_not_approved(self):
        ctx = UseCaseContext(name="Vendor review")
        self._strong_but_litigating().derive_flags(ctx)
        assert tier_from_flags(ctx) is VendorTier.NOT_APPROVED
        assert ctx.is_blocked()

    def test_litigation_is_critical_and_statutory(self):
        ctx = UseCaseContext(name="Vendor review")
        flags = self._strong_but_litigating().derive_flags(ctx)
        litigation = next(f for f in flags if "litigation" in f.description)
        assert litigation.level is RiskLevel.CRITICAL
        assert litigation.authority is Authority.STATUTE
        assert litigation.is_from_enforceable_source

    def test_no_copyright_assessment_raises_no_copyright_flags(self):
        ctx = UseCaseContext(name="Vendor review")
        sc = VendorScorecard(vendor_name="Bare")
        assert sc.derive_flags(ctx) == []

    def test_clean_copyright_assessment_raises_nothing(self):
        ctx = UseCaseContext(name="Vendor review")
        sc = VendorScorecard(
            vendor_name="Clean",
            copyright=CopyrightAssessment(
                training_data_lawfully_obtained=True,
                license_verification_documented=True,
                opt_out_compliance_process=True,
                indemnification_for_ai_outputs=True,
                eu_training_data_summary_published=True,
            ),
        )
        assert sc.derive_flags(ctx) == []
        assert tier_from_flags(ctx) is VendorTier.PREFERRED

    def test_unsatisfactory_security_questions_flag(self):
        ctx = UseCaseContext(name="Vendor review")
        sc = VendorScorecard(
            vendor_name="Q",
            questions=[
                VendorQuestion(
                    question_id="VQ-001", question="q",
                    dimension=ScorecardDimension.GOVERNANCE_SECURITY,
                    satisfactory=False,
                ),
                VendorQuestion(
                    question_id="VQ-009", question="q",
                    dimension=ScorecardDimension.COMMERCIAL_TERMS,
                    satisfactory=False,
                ),
            ],
        )
        flags = sc.derive_flags(ctx)
        assert len(flags) == 1
        assert "VQ-001" in flags[0].description
        assert "VQ-009" not in flags[0].description

    def test_satisfactory_questions_do_not_flag(self):
        ctx = UseCaseContext(name="Vendor review")
        sc = VendorScorecard(
            vendor_name="Q",
            questions=[
                VendorQuestion(
                    question_id="VQ-001", question="q",
                    dimension=ScorecardDimension.GOVERNANCE_SECURITY,
                    satisfactory=True,
                ),
            ],
        )
        assert sc.derive_flags(ctx) == []

    def test_unsatisfactory_questions_filter_by_dimension(self):
        sc = VendorScorecard(
            vendor_name="Q",
            questions=[
                VendorQuestion(
                    question_id="A", question="q",
                    dimension=ScorecardDimension.GOVERNANCE_SECURITY,
                ),
                VendorQuestion(
                    question_id="B", question="q",
                    dimension=ScorecardDimension.TECHNICAL_FIT,
                    satisfactory=True,
                ),
            ],
        )
        assert len(sc.unsatisfactory_questions()) == 1
        assert sc.unsatisfactory_questions(
            ScorecardDimension.TECHNICAL_FIT
        ) == []

    def test_custom_rules_replace_defaults(self):
        ctx = UseCaseContext(name="Vendor review")
        catch_all = VendorRule(
            rule_id="ALWAYS", title="always",
            applies=lambda sc: True,
            dimension=RiskDimension.QUALITY,
            level=RiskLevel.LOW,
            describe=lambda sc: "always",
        )
        flags = VendorScorecard(vendor_name="X").derive_flags(
            ctx, rules=[catch_all]
        )
        assert [f.description for f in flags] == ["always"]


class TestTierFromFlags:
    def test_ladder(self):
        cases = [
            (None, VendorTier.PREFERRED),
            (RiskLevel.LOW, VendorTier.PREFERRED),
            (RiskLevel.MEDIUM, VendorTier.APPROVED),
            (RiskLevel.HIGH, VendorTier.CONDITIONAL),
            (RiskLevel.CRITICAL, VendorTier.NOT_APPROVED),
        ]
        for level, expected in cases:
            ctx = UseCaseContext(name="T")
            if level is not None:
                ctx.flag_risk(RiskDimension.QUALITY, level, "x")
            assert tier_from_flags(ctx) is expected, level

    def test_low_severity_enforceable_finding_costs_one_tier(self):
        # Proportionate, but never averageable: a contract point that only
        # needs confirming should not read the same as a breach.
        ctx = UseCaseContext(name="T")
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.LOW, "minor contract point",
            authority=Authority.BINDING_CONTRACT,
        )
        assert tier_from_flags(ctx) is VendorTier.CONDITIONAL

    def test_medium_enforceable_finding_is_conditional_not_approved(self):
        ctx = UseCaseContext(name="T")
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.MEDIUM, "transparency question",
            authority=Authority.STATUTE,
        )
        assert tier_from_flags(ctx) is VendorTier.CONDITIONAL

    def test_high_enforceable_finding_disqualifies(self):
        ctx = UseCaseContext(name="T")
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.HIGH, "likely breach",
            authority=Authority.BINDING_CONTRACT,
        )
        assert tier_from_flags(ctx) is VendorTier.NOT_APPROVED

    def test_high_non_enforceable_finding_is_only_conditional(self):
        # Same severity, no enforceable source behind it — one tier better.
        ctx = UseCaseContext(name="T")
        ctx.flag_risk(RiskDimension.QUALITY, RiskLevel.HIGH, "quality concern")
        assert tier_from_flags(ctx) is VendorTier.CONDITIONAL

    def test_tier_improves_when_findings_are_resolved(self):
        ctx = UseCaseContext(name="T")
        flag = ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.CRITICAL, "x",
            authority=Authority.STATUTE,
        )
        assert tier_from_flags(ctx) is VendorTier.NOT_APPROVED
        flag.resolve("addressed")
        assert tier_from_flags(ctx) is VendorTier.PREFERRED


class TestExplicitEmptyConfiguration:
    def _scorecard(self):
        return VendorScorecard(
            vendor_name="X", data_provenance=DimensionScore(score=100)
        )

    def test_empty_weights_fail_loudly_rather_than_silently_defaulting(self):
        # Unlike a routing table, an empty weight map is a mis-specification:
        # it cannot sum to 1.0. Better a clear error than the defaults.
        with pytest.raises(ValueError) as exc:
            evaluate_vendor(self._scorecard(), weights={})
        assert "sum to 1.0" in str(exc.value)

    def test_empty_thresholds_report_the_missing_tiers(self):
        with pytest.raises(ValueError) as exc:
            evaluate_vendor(self._scorecard(), tier_thresholds={})
        assert "Missing" in str(exc.value)

    def test_partial_thresholds_are_rejected(self):
        with pytest.raises(ValueError):
            evaluate_vendor(
                self._scorecard(),
                tier_thresholds={VendorTier.PREFERRED: 80.0},
            )

    def test_complete_custom_thresholds_are_accepted_and_applied(self):
        sc = self._scorecard()
        # 100 on one dimension at the default 0.25 weight -> overall 25.0,
        # which the default thresholds put below CONDITIONAL (40).
        assert evaluate_vendor(sc).tier is VendorTier.NOT_APPROVED
        result = evaluate_vendor(
            sc,
            tier_thresholds={
                VendorTier.PREFERRED: 90.0,
                VendorTier.APPROVED: 50.0,
                VendorTier.CONDITIONAL: 20.0,
                VendorTier.NOT_APPROVED: 0.0,
            },
        )
        assert result.tier is VendorTier.CONDITIONAL



class TestCopyrightRiskSingleDefects:
    """Each high-severity fact must stand on its own.

    The earlier rule required two before reporting "high", so a single
    disqualifying fact reported as "low".
    """

    def _clean(self, **overrides):
        kw = dict(
            training_data_lawfully_obtained=True,
            license_verification_documented=True,
            opt_out_compliance_process=True,
            indemnification_for_ai_outputs=True,
            eu_dsm_article4_compliance=True,
            eu_training_data_summary_published=True,
            competes_with_training_sources=False,
            pending_litigation=False,
        )
        kw.update(overrides)
        return CopyrightAssessment(**kw)

    def test_clean_assessment_is_low(self):
        assert self._clean().risk_level == "low"

    def test_unlawful_training_data_alone_is_high(self):
        assert self._clean(
            training_data_lawfully_obtained=False
        ).risk_level == "high"

    def test_undocumented_licence_verification_alone_is_high(self):
        assert self._clean(
            license_verification_documented=False
        ).risk_level == "high"

    def test_competing_with_training_sources_alone_is_high(self):
        assert self._clean(
            competes_with_training_sources=True
        ).risk_level == "high"

    def test_litigation_alone_is_critical(self):
        assert self._clean(pending_litigation=True).risk_level == "critical"

    def test_competing_and_unlawful_together_is_critical(self):
        assert self._clean(
            competes_with_training_sources=True,
            training_data_lawfully_obtained=False,
        ).risk_level == "critical"

    def test_missing_opt_out_alone_is_medium(self):
        assert self._clean(opt_out_compliance_process=False).risk_level == "medium"

    def test_missing_indemnification_alone_is_medium(self):
        assert self._clean(
            indemnification_for_ai_outputs=False
        ).risk_level == "medium"


class TestJurisdictionScopedFields:
    """The EU fields are reported but do not drive an unscoped risk level."""

    def _clean(self, **overrides):
        kw = dict(
            training_data_lawfully_obtained=True,
            license_verification_documented=True,
            opt_out_compliance_process=True,
            indemnification_for_ai_outputs=True,
            eu_dsm_article4_compliance=True,
            eu_training_data_summary_published=True,
        )
        kw.update(overrides)
        return CopyrightAssessment(**kw)

    def test_eu_fields_appear_in_gaps(self):
        # Previously these two inputs affected nothing at all.
        c = self._clean(
            eu_dsm_article4_compliance=False,
            eu_training_data_summary_published=False,
        )
        assert len(c.gaps) == 2
        assert any("Art. 4" in g for g in c.gaps)
        assert any("Training data summary" in g for g in c.gaps)

    def test_eu_fields_do_not_change_risk_level(self):
        # Whether they matter depends on where the work is exploited, and this
        # object carries no jurisdiction.
        c = self._clean(
            eu_dsm_article4_compliance=False,
            eu_training_data_summary_published=False,
        )
        assert c.risk_level == "low"

    def test_monotonicity_across_all_combinations(self):
        import itertools

        order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        good = [
            "training_data_lawfully_obtained",
            "license_verification_documented",
            "opt_out_compliance_process",
            "indemnification_for_ai_outputs",
        ]
        bad = ["competes_with_training_sources", "pending_litigation"]
        levels = {}
        for combo in itertools.product([False, True], repeat=len(good) + len(bad)):
            kw = dict(zip(good + bad, combo))
            levels[tuple(sorted(kw.items()))] = CopyrightAssessment(**kw).risk_level

        for key, lvl in levels.items():
            kw = dict(key)
            for f in good:
                if kw[f]:
                    worse = dict(kw)
                    worse[f] = False
                    assert order[levels[tuple(sorted(worse.items()))]] >= order[lvl]
            for f in bad:
                if not kw[f]:
                    worse = dict(kw)
                    worse[f] = True
                    assert order[levels[tuple(sorted(worse.items()))]] >= order[lvl]
