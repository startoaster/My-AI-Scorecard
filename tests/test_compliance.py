"""Tests for compliance standards alignment module."""

import pytest
from datetime import date, datetime

from ai_use_case_context.compliance import (
    RiskClassification,
    AIMSMaturity,
    NISTFunction,
    OMCWorkflowPhase,
    ISO42001Control,
    ISO42001Assessment,
    NISTSubcategory,
    NISTAIRMFMapping,
    EUAIActChecklist,
    MovieLabsOMCAlignment,
    ComplianceProfile,
    ComplianceResult,
    evaluate_compliance,
    iso42001_annex_a_controls,
    nist_ai_rmf_subcategories,
)


# ---------------------------------------------------------------------------
# ISO 42001
# ---------------------------------------------------------------------------

class TestISO42001Control:
    def test_defaults(self):
        c = ISO42001Control(control_id="A.5.2", title="Bias and Fairness")
        assert c.control_id == "A.5.2"
        assert c.implemented is False

    def test_round_trip(self):
        c = ISO42001Control("A.5.2", "Bias", True, "Evidence here", "Gap note")
        restored = ISO42001Control.from_dict(c.to_dict())
        assert restored.control_id == c.control_id
        assert restored.implemented is True
        assert restored.evidence == "Evidence here"


class TestISO42001Assessment:
    def test_score_zero(self):
        a = ISO42001Assessment()
        assert a.score == 0.0

    def test_score_full_criteria_no_controls(self):
        a = ISO42001Assessment(
            aims_documented=True,
            risk_assessment_process=True,
            ai_impact_assessment=True,
            continuous_improvement_cycle=True,
        )
        assert a.score == 60.0

    def test_score_with_controls(self):
        controls = [
            ISO42001Control("A.1", "T1", implemented=True),
            ISO42001Control("A.2", "T2", implemented=False),
        ]
        a = ISO42001Assessment(
            aims_documented=True,
            risk_assessment_process=True,
            ai_impact_assessment=True,
            continuous_improvement_cycle=True,
            annex_a_controls=controls,
        )
        # 60 + 40*(1/2) = 80
        assert a.score == 80.0

    def test_controls_implemented_count(self):
        controls = [
            ISO42001Control("A.1", "T1", implemented=True),
            ISO42001Control("A.2", "T2", implemented=True),
            ISO42001Control("A.3", "T3", implemented=False),
        ]
        a = ISO42001Assessment(annex_a_controls=controls)
        assert a.controls_implemented == 2
        assert a.controls_total == 3

    def test_round_trip(self):
        a = ISO42001Assessment(
            aims_documented=True,
            maturity=AIMSMaturity.DEFINED,
            certification_date=date(2025, 6, 15),
            annex_a_controls=[ISO42001Control("A.1", "T1", True)],
        )
        restored = ISO42001Assessment.from_dict(a.to_dict())
        assert restored.aims_documented is True
        assert restored.maturity == AIMSMaturity.DEFINED
        assert restored.certification_date == date(2025, 6, 15)
        assert len(restored.annex_a_controls) == 1


# ---------------------------------------------------------------------------
# NIST AI RMF
# ---------------------------------------------------------------------------

class TestNISTAIRMFMapping:
    def test_composite_score(self):
        n = NISTAIRMFMapping(
            govern_score=100,
            map_score=100,
            measure_score=100,
            manage_score=100,
        )
        assert n.composite_score == 100.0

    def test_composite_score_weighted(self):
        n = NISTAIRMFMapping(
            govern_score=80,
            map_score=60,
            measure_score=40,
            manage_score=20,
        )
        expected = 80 * 0.30 + 60 * 0.25 + 40 * 0.25 + 20 * 0.20
        assert abs(n.composite_score - expected) < 0.01

    def test_round_trip(self):
        n = NISTAIRMFMapping(
            govern_score=80,
            governance_committee_established=True,
            committee_roles=["Legal", "Tech", "Ethics"],
            subcategories=[NISTSubcategory("GV-1.1", "Policies", True)],
        )
        restored = NISTAIRMFMapping.from_dict(n.to_dict())
        assert restored.govern_score == 80
        assert restored.governance_committee_established is True
        assert len(restored.subcategories) == 1


# ---------------------------------------------------------------------------
# EU AI Act
# ---------------------------------------------------------------------------

class TestEUAIActChecklist:
    def test_not_applicable(self):
        c = EUAIActChecklist(eu_distribution_planned=False)
        assert c.applicable is False
        assert c.compliant is True
        assert c.gaps == []

    def test_minimal_compliant(self):
        c = EUAIActChecklist(
            eu_distribution_planned=True,
            training_data_summary_published=True,
            copyright_opt_out_policy=True,
            transparency_obligations=True,
        )
        assert c.compliant is True

    def test_minimal_not_compliant(self):
        c = EUAIActChecklist(eu_distribution_planned=True)
        assert c.compliant is False
        assert len(c.gaps) == 3

    def test_high_risk_additional_checks(self):
        c = EUAIActChecklist(
            risk_classification=RiskClassification.HIGH,
            eu_distribution_planned=True,
        )
        gaps = c.gaps
        assert len(gaps) == 6  # 3 base + 3 high-risk

    def test_round_trip(self):
        c = EUAIActChecklist(
            risk_classification=RiskClassification.HIGH,
            eu_distribution_planned=True,
            training_data_summary_published=True,
        )
        restored = EUAIActChecklist.from_dict(c.to_dict())
        assert restored.risk_classification == RiskClassification.HIGH
        assert restored.training_data_summary_published is True


# ---------------------------------------------------------------------------
# MovieLabs OMC
# ---------------------------------------------------------------------------

class TestMovieLabsOMCAlignment:
    def test_score_zero(self):
        m = MovieLabsOMCAlignment()
        assert m.score == 0.0

    def test_score_full(self):
        m = MovieLabsOMCAlignment(
            software_defined_workflow=True,
            cloud_native_architecture=True,
            interoperable_data_model=True,
            security_first_design=True,
            asset_provenance_tracking=True,
            component_based_pipeline=True,
            open_api_interfaces=True,
            rights_management=True,
        )
        assert m.score == 100.0

    def test_score_partial(self):
        m = MovieLabsOMCAlignment(
            software_defined_workflow=True,
            cloud_native_architecture=True,
            interoperable_data_model=True,
            security_first_design=True,
        )
        assert m.score == 50.0

    def test_round_trip(self):
        m = MovieLabsOMCAlignment(
            workflow_phase=OMCWorkflowPhase.PRODUCTION,
            asset_provenance_tracking=True,
        )
        restored = MovieLabsOMCAlignment.from_dict(m.to_dict())
        assert restored.workflow_phase == OMCWorkflowPhase.PRODUCTION
        assert restored.asset_provenance_tracking is True


# ---------------------------------------------------------------------------
# Compliance profile & evaluation
# ---------------------------------------------------------------------------

class TestComplianceProfile:
    def test_empty_profile(self):
        p = ComplianceProfile()
        result = evaluate_compliance(p)
        assert result.overall_score == 0.0
        assert len(result.recommendations) > 0

    def test_full_profile(self):
        p = ComplianceProfile(
            iso42001=ISO42001Assessment(
                aims_documented=True,
                risk_assessment_process=True,
                ai_impact_assessment=True,
                continuous_improvement_cycle=True,
            ),
            nist_ai_rmf=NISTAIRMFMapping(
                govern_score=80,
                map_score=70,
                measure_score=60,
                manage_score=50,
                governance_committee_established=True,
                incident_response_procedures=True,
                gen_ai_supplement_addressed=True,
            ),
            eu_ai_act=EUAIActChecklist(eu_distribution_planned=False),
            movielabs_omc=MovieLabsOMCAlignment(
                asset_provenance_tracking=True,
                interoperable_data_model=True,
                security_first_design=True,
            ),
        )
        result = evaluate_compliance(p)
        assert result.overall_score > 0
        assert "iso42001" in result.section_scores
        assert "nist_ai_rmf" in result.section_scores
        assert "eu_ai_act" in result.section_scores
        assert "movielabs_omc" in result.section_scores

    def test_round_trip(self):
        p = ComplianceProfile(
            iso42001=ISO42001Assessment(aims_documented=True),
            assessor="Test Assessor",
        )
        restored = ComplianceProfile.from_dict(p.to_dict())
        assert restored.iso42001.aims_documented is True
        assert restored.assessor == "Test Assessor"

    def test_evaluate_identifies_iso_gaps(self):
        p = ComplianceProfile(
            iso42001=ISO42001Assessment()  # all defaults = all False
        )
        result = evaluate_compliance(p)
        gap_text = " ".join(result.gaps)
        assert "ISO 42001" in gap_text

    def test_evaluate_identifies_nist_gaps(self):
        p = ComplianceProfile(
            nist_ai_rmf=NISTAIRMFMapping()  # all defaults
        )
        result = evaluate_compliance(p)
        gap_text = " ".join(result.gaps)
        assert "NIST" in gap_text

    def test_evaluate_identifies_omc_gaps(self):
        p = ComplianceProfile(
            movielabs_omc=MovieLabsOMCAlignment()  # all defaults
        )
        result = evaluate_compliance(p)
        gap_text = " ".join(result.gaps)
        assert "OMC" in gap_text


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------

class TestTemplates:
    def test_annex_a_controls_not_empty(self):
        controls = iso42001_annex_a_controls()
        assert len(controls) > 0
        assert all(isinstance(c, ISO42001Control) for c in controls)
        assert all(c.control_id.startswith("A.") for c in controls)
        assert all(not c.implemented for c in controls)

    def test_nist_subcategories_not_empty(self):
        subcats = nist_ai_rmf_subcategories()
        assert len(subcats) > 0
        assert all(isinstance(s, NISTSubcategory) for s in subcats)
        assert all(not s.addressed for s in subcats)

    def test_nist_covers_all_functions(self):
        subcats = nist_ai_rmf_subcategories()
        prefixes = {s.subcategory_id[:2] for s in subcats}
        assert "GV" in prefixes  # GOVERN
        assert "MP" in prefixes  # MAP
        assert "MS" in prefixes  # MEASURE
        assert "MG" in prefixes  # MANAGE


# ---------------------------------------------------------------------------
# Result serialization
# ---------------------------------------------------------------------------

class TestComplianceResult:
    def test_round_trip(self):
        r = ComplianceResult(
            overall_score=75.5,
            section_scores={"iso42001": 80.0, "nist_ai_rmf": 71.0},
            gaps=["Gap 1"],
            recommendations=["Rec 1"],
        )
        restored = ComplianceResult.from_dict(r.to_dict())
        assert restored.overall_score == 75.5
        assert len(restored.gaps) == 1
