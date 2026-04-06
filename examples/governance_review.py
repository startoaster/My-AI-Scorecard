#!/usr/bin/env python3
"""
Governance review example — compliance, provenance, and vendor scorecard.

Demonstrates the three new governance modules added for 2025 best practices:

1. **Compliance standards** — ISO 42001, NIST AI RMF, EU AI Act, MovieLabs OMC
2. **Data provenance** — source lineage, generation flags, model collapse guards
3. **Vendor scorecard** — six-dimension weighted scoring with KBYUTS and copyright

Run:
    python -m examples.governance_review
    # or
    python examples/governance_review.py
"""

from datetime import date, datetime

from ai_use_case_context import (
    UseCaseContext,
    RiskDimension,
    RiskLevel,
)
from ai_use_case_context.compliance import (
    AIMSMaturity,
    ISO42001Assessment,
    ISO42001Control,
    NISTAIRMFMapping,
    EUAIActChecklist,
    RiskClassification,
    MovieLabsOMCAlignment,
    OMCWorkflowPhase,
    ComplianceProfile,
    evaluate_compliance,
    iso42001_annex_a_controls,
    nist_ai_rmf_subcategories,
)
from ai_use_case_context.provenance import (
    DataSource,
    CaptureMethod,
    LicenseCompliance,
    GenerationFlag,
    TransformationRecord,
    TransformationType,
    DatasetVersion,
    ProvenanceCard,
    ModelCollapseGuard,
    evaluate_provenance,
)
from ai_use_case_context.vendor_scorecard import (
    DimensionScore,
    KBYUTSScores,
    CopyrightAssessment,
    VendorScorecard,
    evaluate_vendor,
    essential_vendor_questions,
)


def divider(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


# -----------------------------------------------------------------------
# 1. Compliance standards evaluation
# -----------------------------------------------------------------------

divider("1. COMPLIANCE STANDARDS EVALUATION")

# Build ISO 42001 assessment
annex_a = iso42001_annex_a_controls()[:5]  # first 5 controls for demo
for ctrl in annex_a[:3]:
    ctrl.implemented = True
    ctrl.evidence = "Documented in governance handbook v3"

iso_assessment = ISO42001Assessment(
    aims_documented=True,
    risk_assessment_process=True,
    ai_impact_assessment=False,  # gap
    continuous_improvement_cycle=True,
    maturity=AIMSMaturity.DEFINED,
    certification_body="BSI Group",
    certification_date=date(2025, 9, 1),
    annex_a_controls=annex_a,
)

# Build NIST AI RMF mapping
nist_mapping = NISTAIRMFMapping(
    govern_score=85,
    map_score=70,
    measure_score=55,
    manage_score=60,
    governance_committee_established=True,
    committee_roles=["VP Legal", "CTO", "Ethics Officer", "Creative Director"],
    gen_ai_supplement_addressed=True,
    training_data_poisoning_controls=True,
    bias_detection_processes=True,
    incident_response_procedures=False,  # gap
)

# EU AI Act checklist
eu_checklist = EUAIActChecklist(
    risk_classification=RiskClassification.LIMITED,
    eu_distribution_planned=True,
    training_data_summary_published=True,
    copyright_opt_out_policy=True,
    transparency_obligations=True,
)

# MovieLabs OMC alignment
omc_alignment = MovieLabsOMCAlignment(
    workflow_phase=OMCWorkflowPhase.POST_PRODUCTION,
    software_defined_workflow=True,
    cloud_native_architecture=True,
    interoperable_data_model=True,
    security_first_design=True,
    asset_provenance_tracking=True,
    component_based_pipeline=False,  # gap
    open_api_interfaces=True,
    rights_management=True,
)

# Evaluate composite profile
profile = ComplianceProfile(
    iso42001=iso_assessment,
    nist_ai_rmf=nist_mapping,
    eu_ai_act=eu_checklist,
    movielabs_omc=omc_alignment,
    assessor="AI Governance Team",
)

result = evaluate_compliance(profile)
print(f"Overall Compliance Score: {result.overall_score:.1f}/100")
print(f"\nSection Scores:")
for section, score in result.section_scores.items():
    print(f"  {section}: {score:.1f}")
print(f"\nGaps ({len(result.gaps)}):")
for gap in result.gaps:
    print(f"  - {gap}")
print(f"\nRecommendations ({len(result.recommendations)}):")
for rec in result.recommendations:
    print(f"  - {rec}")


# -----------------------------------------------------------------------
# 2. Data provenance evaluation
# -----------------------------------------------------------------------

divider("2. DATA PROVENANCE EVALUATION")

# Define data sources
sources = [
    DataSource(
        name="Licensed MoCap Library (Phase Space)",
        url="https://example.com/mocap-lib",
        collection_date=datetime(2024, 6, 15),
        license_type="Commercial Perpetual",
        license_compliance=LicenseCompliance.VERIFIED,
        capture_method=CaptureMethod.MOTION_CAPTURE,
        copyright_holder="Phase Space Inc.",
        opt_out_honored=True,
        consent_documented=True,
    ),
    DataSource(
        name="Internal Reference Photography",
        collection_date=datetime(2025, 1, 10),
        license_type="Internal / Work-for-hire",
        license_compliance=LicenseCompliance.VERIFIED,
        capture_method=CaptureMethod.MANUAL_CREATION,
        copyright_holder="Studio Production LLC",
        opt_out_honored=True,
    ),
]

# Define transformations
transformations = [
    TransformationRecord(
        transformation_type=TransformationType.CLEANING,
        description="Removed corrupted frames and noise",
        applied_by="Pipeline v2.1",
        input_hash="sha256:a1b2c3",
        output_hash="sha256:d4e5f6",
    ),
    TransformationRecord(
        transformation_type=TransformationType.NORMALIZATION,
        description="Normalized skeleton rig to production standard",
        applied_by="Rig Normalizer v1.0",
    ),
]

# Build provenance card
card = ProvenanceCard(
    dataset_name="Hero Character Performance Capture v2",
    description="Performance capture data for lead character animation",
    sources=sources,
    generation_flag=GenerationFlag.HUMAN_ORIGIN,
    generation_confidence=0.98,
    transformations=transformations,
    versions=[
        DatasetVersion(
            version_id="v2.0.0",
            dataset_name="Hero Character Performance Capture",
            record_count=15000,
            size_bytes=2_500_000_000,
            checksum="sha256:xyz789",
            parent_version_id="v1.0.0",
            tags=["production", "verified", "hero-character"],
        ),
    ],
    current_version_id="v2.0.0",
    synthetic_percentage=0.0,
    license_summary="All sources commercially licensed or internal work-for-hire",
    lawful_basis="Contractual obligation + legitimate interest",
    created_by="Data Governance Team",
)

# Model collapse guard
guard = ModelCollapseGuard(
    max_synthetic_percentage=15.0,
    actual_synthetic_percentage=0.0,
    vendor_disclosure_received=True,
    high_stakes_domain=True,
)

prov_result = evaluate_provenance(card, guard)
print(f"Provenance Score: {prov_result.score:.1f}/100")
print(f"All Licenses Verified: {card.all_licenses_verified}")
print(f"Opt-out Gaps: {card.has_opt_out_gaps}")
print(f"Provenance Complete: {card.provenance_complete}")
print(f"Model Collapse Guard: {'PASS' if guard.within_limits else 'FAIL'}")
if prov_result.gaps:
    print(f"\nGaps ({len(prov_result.gaps)}):")
    for gap in prov_result.gaps:
        print(f"  - {gap}")


# -----------------------------------------------------------------------
# 3. Vendor scorecard evaluation
# -----------------------------------------------------------------------

divider("3. VENDOR SCORECARD EVALUATION")

scorecard = VendorScorecard(
    vendor_name="Acme GenAI Studio Tools",
    vendor_url="https://example.com/acme-ai",
    assessor="Vendor Assessment Board",
    data_provenance=DimensionScore(
        score=75,
        evidence="Dataset cards available for 80% of training data; lineage documentation partial",
        gaps="Field-level lineage not available; 20% training data undocumented",
    ),
    governance_security=DimensionScore(
        score=82,
        evidence="ISO 42001 certified (BSI, Sept 2025); SOC 2 Type II current",
        gaps="Data isolation controls need verification for multi-tenant deployment",
    ),
    ethics_compliance=DimensionScore(
        score=68,
        evidence="Bias review board established; NIST AI RMF partially adopted",
        gaps="No formal ethics board; creative professional opt-out process immature",
    ),
    technical_fit=DimensionScore(
        score=85,
        evidence="REST API v3; version-controlled model outputs; CI/CD pipeline integration",
    ),
    commercial_terms=DimensionScore(
        score=70,
        evidence="Clear IP ownership clause; data portability via API export",
        gaps="Indemnification limited to $1M; no explicit termination data deletion SLA",
    ),
    operating_model=DimensionScore(
        score=78,
        evidence="24/7 support tier; 4-hour incident response SLA; quarterly model updates",
    ),
    kbyuts=KBYUTSScores(
        training_data_transparency=70,
        creative_professional_treatment=55,
        governance_maturity=80,
        output_attribution=45,
        legal_risk=60,
    ),
    copyright=CopyrightAssessment(
        training_data_lawfully_obtained=True,
        license_verification_documented=True,
        opt_out_compliance_process=True,
        indemnification_for_ai_outputs=True,
        competes_with_training_sources=False,
        pending_litigation=False,
        eu_dsm_article4_compliance=True,
    ),
)

vendor_result = evaluate_vendor(scorecard)
print(f"Vendor: {scorecard.vendor_name}")
print(f"Overall Score: {vendor_result.overall_score:.1f}/100")
print(f"Tier: {vendor_result.tier.value.upper()}")
print(f"Copyright Risk: {vendor_result.copyright_risk}")
print(f"\nDimension Scores:")
for dim, score in vendor_result.dimension_scores.items():
    print(f"  {dim}: {score:.0f}/100")
if vendor_result.gaps:
    print(f"\nGaps ({len(vendor_result.gaps)}):")
    for gap in vendor_result.gaps:
        print(f"  - {gap}")
if vendor_result.recommendations:
    print(f"\nRecommendations ({len(vendor_result.recommendations)}):")
    for rec in vendor_result.recommendations:
        print(f"  - {rec}")

# Show essential questions
print(f"\n--- Essential Vendor Questions ({len(essential_vendor_questions())}) ---")
for q in essential_vendor_questions()[:5]:
    print(f"  [{q.question_id}] {q.question}")
print(f"  ... and {len(essential_vendor_questions()) - 5} more")


# -----------------------------------------------------------------------
# 4. Integration with UseCaseContext
# -----------------------------------------------------------------------

divider("4. INTEGRATED GOVERNANCE REVIEW")

ctx = UseCaseContext(
    name="AI Character Animation",
    description="Using GenAI for character performance synthesis",
    workflow_phase="Post-Production",
    tags=["animation", "genai", "character"],
)

# Flag risks based on compliance evaluation
if result.overall_score < 70:
    ctx.flag_risk(
        RiskDimension.LEGAL_IP,
        RiskLevel.HIGH,
        f"Compliance score {result.overall_score:.0f}/100 below threshold",
    )

if vendor_result.copyright_risk in ("high", "critical"):
    ctx.flag_risk(
        RiskDimension.LEGAL_IP,
        RiskLevel.CRITICAL,
        f"Vendor copyright risk: {vendor_result.copyright_risk}",
    )

if not guard.within_limits:
    ctx.flag_risk(
        RiskDimension.SECURITY,
        RiskLevel.HIGH,
        "Model collapse guard violated: synthetic data exceeds cap",
    )

if not card.all_licenses_verified:
    ctx.flag_risk(
        RiskDimension.LEGAL_IP,
        RiskLevel.MEDIUM,
        "Not all data source licenses verified",
    )

print(ctx.summary())
print("\nGovernance review complete.")
