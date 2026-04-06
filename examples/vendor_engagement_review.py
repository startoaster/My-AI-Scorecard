#!/usr/bin/env python3
"""
End-to-end governance review for a VFX production AI vendor engagement.

Walks through a realistic scenario: a VFX studio is evaluating whether to
use a third-party GenAI tool for digital character creation.  The review
covers compliance standards, data provenance, vendor scoring, copyright
risk, and integrates findings into the core governance framework to
produce a go / no-go decision.

Run:
    python examples/vendor_engagement_review.py
"""

from datetime import date, datetime

from ai_use_case_context import (
    UseCaseContext,
    RiskDimension,
    RiskLevel,
    GovernanceDashboard,
)
from ai_use_case_context.compliance import (
    AIMSMaturity,
    ISO42001Assessment,
    NISTAIRMFMapping,
    EUAIActChecklist,
    RiskClassification,
    MovieLabsOMCAlignment,
    OMCWorkflowPhase,
    ComplianceProfile,
    ComplianceResult,
    evaluate_compliance,
    iso42001_annex_a_controls,
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
    ProvenanceResult,
    evaluate_provenance,
)
from ai_use_case_context.vendor_scorecard import (
    DimensionScore,
    KBYUTSScores,
    CopyrightAssessment,
    VendorScorecard,
    VendorResult,
    VendorTier,
    evaluate_vendor,
    essential_vendor_questions,
)
from ai_use_case_context.security import (
    security_profile,
    apply_security_profile,
)


def banner(title: str) -> None:
    width = 64
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}\n")


def section(title: str) -> None:
    print(f"\n--- {title} ---\n")


def main() -> None:
    banner("VFX STUDIO — AI VENDOR ENGAGEMENT REVIEW")
    print("Production:  'Stellar Horizons' (Feature Film)")
    print("Use case:    AI-assisted digital character creation")
    print("Vendor:      NeuralForge Studio AI v4.2")
    print("Reviewed by: AI Governance Board")
    print(f"Date:        {date.today()}")

    # =================================================================
    # Step 1: Create the use case and apply security profile
    # =================================================================
    section("STEP 1: USE CASE SETUP")

    ctx = UseCaseContext(
        name="Digital Character Creation — NeuralForge",
        description=(
            "Use NeuralForge Studio AI to generate base character meshes "
            "and texture maps from concept art, with artist refinement."
        ),
        workflow_phase="Asset Creation",
        tags=["character", "genai", "mesh", "texture", "vendor:neuralforge"],
    )

    # Apply TPN + VFX security profiles (studio requirement)
    profile = security_profile("tpn", "vfx")
    apply_security_profile(ctx, profile)
    print(f"Use case created: {ctx.name}")
    print(f"Security profiles applied: TPN + VFX ({len(profile.dimensions)} dimensions)")

    # =================================================================
    # Step 2: Compliance standards assessment
    # =================================================================
    section("STEP 2: COMPLIANCE STANDARDS ASSESSMENT")

    # Assess NeuralForge's ISO 42001 posture
    annex_a = iso42001_annex_a_controls()
    # Simulate: vendor has implemented 18 of 25 controls
    for ctrl in annex_a[:18]:
        ctrl.implemented = True
        ctrl.evidence = "Verified via vendor audit package (March 2026)"

    iso = ISO42001Assessment(
        aims_documented=True,
        risk_assessment_process=True,
        ai_impact_assessment=True,
        continuous_improvement_cycle=True,
        maturity=AIMSMaturity.DEFINED,
        certification_body="BSI Group",
        certification_date=date(2025, 11, 15),
        annex_a_controls=annex_a,
    )

    # NIST AI RMF mapping from vendor questionnaire
    nist = NISTAIRMFMapping(
        govern_score=82,
        map_score=75,
        measure_score=60,
        manage_score=55,
        governance_committee_established=True,
        committee_roles=["CTO", "VP Ethics", "Legal Counsel", "Head of ML Research"],
        gen_ai_supplement_addressed=True,
        training_data_poisoning_controls=True,
        bias_detection_processes=True,
        incident_response_procedures=False,  # GAP
    )

    # EU AI Act — film has European distribution
    eu = EUAIActChecklist(
        risk_classification=RiskClassification.LIMITED,
        eu_distribution_planned=True,
        training_data_summary_published=True,
        copyright_opt_out_policy=True,
        transparency_obligations=True,  # AI-generated content disclosed in credits
    )

    # MovieLabs OMC alignment
    omc = MovieLabsOMCAlignment(
        workflow_phase=OMCWorkflowPhase.PRODUCTION,
        software_defined_workflow=True,
        cloud_native_architecture=True,
        interoperable_data_model=False,  # GAP — proprietary format
        security_first_design=True,
        asset_provenance_tracking=True,
        component_based_pipeline=True,
        open_api_interfaces=True,
        rights_management=True,
    )

    compliance = ComplianceProfile(
        iso42001=iso,
        nist_ai_rmf=nist,
        eu_ai_act=eu,
        movielabs_omc=omc,
        assessor="AI Governance Board",
    )

    compliance_result = evaluate_compliance(compliance)
    print(f"Overall Compliance Score: {compliance_result.overall_score:.1f}/100")
    for name, score in compliance_result.section_scores.items():
        status = "PASS" if score >= 70 else "REVIEW"
        print(f"  {name}: {score:.1f}/100  [{status}]")

    if compliance_result.gaps:
        print(f"\nCompliance Gaps ({len(compliance_result.gaps)}):")
        for gap in compliance_result.gaps:
            print(f"  ! {gap}")

    # =================================================================
    # Step 3: Data provenance assessment
    # =================================================================
    section("STEP 3: DATA PROVENANCE ASSESSMENT")

    # Provenance card for NeuralForge's training data (from vendor disclosure)
    card = ProvenanceCard(
        dataset_name="NeuralForge Character Training Set v4",
        description="Multi-modal dataset for 3D character mesh and texture generation",
        sources=[
            DataSource(
                name="Licensed 3D Scan Library (3DScanStore)",
                license_type="Commercial Perpetual",
                license_compliance=LicenseCompliance.VERIFIED,
                capture_method=CaptureMethod.PHOTOGRAMMETRY,
                collection_date=datetime(2023, 6, 1),
                copyright_holder="3DScanStore Ltd.",
                opt_out_honored=True,
                consent_documented=True,
            ),
            DataSource(
                name="Academic Human Mesh Dataset (SMPL-X)",
                license_type="Academic / Research (CC-BY-NC)",
                license_compliance=LicenseCompliance.VERIFIED,
                capture_method=CaptureMethod.SENSOR,
                collection_date=datetime(2022, 3, 15),
                copyright_holder="Max Planck Institute",
                opt_out_honored=True,
            ),
            DataSource(
                name="Internal Artist-Created Assets",
                license_type="Work-for-hire (full ownership)",
                license_compliance=LicenseCompliance.VERIFIED,
                capture_method=CaptureMethod.MANUAL_CREATION,
                collection_date=datetime(2024, 1, 1),
                copyright_holder="NeuralForge Inc.",
                opt_out_honored=True,
            ),
            DataSource(
                name="Web-Scraped Reference Images",
                license_type="Fair use claim (disputed)",
                license_compliance=LicenseCompliance.PENDING_REVIEW,  # GAP
                capture_method=CaptureMethod.CRAWL,
                collection_date=datetime(2023, 9, 1),
                copyright_holder="Various / Unknown",
                opt_out_honored=False,  # GAP
            ),
        ],
        generation_flag=GenerationFlag.HYBRID,
        generation_confidence=0.85,
        transformations=[
            TransformationRecord(
                transformation_type=TransformationType.DEDUPLICATION,
                description="Removed duplicate meshes across sources",
                applied_by="NeuralForge Data Pipeline v3",
            ),
            TransformationRecord(
                transformation_type=TransformationType.NORMALIZATION,
                description="Unified vertex format, UV mapping, and scale",
                applied_by="NeuralForge Data Pipeline v3",
            ),
            TransformationRecord(
                transformation_type=TransformationType.AUGMENTATION,
                description="Procedural variations for body proportions",
                applied_by="NeuralForge Augmentor v2",
            ),
            TransformationRecord(
                transformation_type=TransformationType.FILTERING,
                description="Removed assets below quality threshold",
                applied_by="QA review + automated metrics",
            ),
        ],
        versions=[
            DatasetVersion(
                version_id="v4.0.0",
                dataset_name="NeuralForge Character Training Set",
                record_count=250_000,
                size_bytes=180_000_000_000,
                checksum="sha256:9f8e7d6c5b4a3210",
                parent_version_id="v3.2.1",
                tags=["production", "character", "mesh", "texture"],
            ),
        ],
        current_version_id="v4.0.0",
        synthetic_percentage=12.0,
        license_summary="75% commercial/owned, 25% mixed (includes disputed web-scraped data)",
        lawful_basis="Contractual obligation + legitimate interest + disputed fair use",
        created_by="NeuralForge Data Team",
    )

    guard = ModelCollapseGuard(
        max_synthetic_percentage=20.0,
        actual_synthetic_percentage=12.0,
        vendor_disclosure_received=True,
        high_stakes_domain=True,  # Feature film = high stakes
    )

    prov_result = evaluate_provenance(card, guard)
    print(f"Provenance Score:     {prov_result.score:.1f}/100")
    print(f"Licenses Verified:    {card.all_licenses_verified}")
    print(f"Opt-out Gaps:         {card.has_opt_out_gaps}")
    print(f"Provenance Complete:  {card.provenance_complete}")
    print(f"Synthetic Content:    {card.synthetic_percentage}% (cap: {guard.max_synthetic_percentage}%)")
    print(f"Model Collapse Guard: {'PASS' if guard.within_limits else 'FAIL'}")

    if prov_result.gaps:
        print(f"\nProvenance Gaps ({len(prov_result.gaps)}):")
        for gap in prov_result.gaps:
            print(f"  ! {gap}")

    # =================================================================
    # Step 4: Vendor scorecard
    # =================================================================
    section("STEP 4: VENDOR SCORECARD")

    scorecard = VendorScorecard(
        vendor_name="NeuralForge Studio AI",
        vendor_url="https://example.com/neuralforge",
        assessor="Vendor Assessment Board",
        data_provenance=DimensionScore(
            score=62,
            evidence="Dataset cards for 3 of 4 sources; web-scraped data has no lineage",
            gaps="Web-scraped source lacks license verification and opt-out compliance",
        ),
        governance_security=DimensionScore(
            score=80,
            evidence="ISO 42001 certified; SOC 2 Type II; dedicated security team",
            gaps="No AI-specific incident response procedure documented",
        ),
        ethics_compliance=DimensionScore(
            score=72,
            evidence="Bias review board; fairness metrics dashboard; content labeling",
            gaps="Creative professional opt-out mechanism needs strengthening",
        ),
        technical_fit=DimensionScore(
            score=88,
            evidence="REST API v3; USD/glTF export; Maya/Houdini plugins; version-controlled outputs",
        ),
        commercial_terms=DimensionScore(
            score=65,
            evidence="Clear output IP ownership; data portability clause",
            gaps="Indemnification capped at contract value; no Thomson Reuters risk clause",
        ),
        operating_model=DimensionScore(
            score=75,
            evidence="Dedicated account team; 4hr SLA; quarterly model refresh",
            gaps="No on-premise deployment option; retraining notification is T+30 days",
        ),
        kbyuts=KBYUTSScores(
            training_data_transparency=65,
            creative_professional_treatment=50,
            governance_maturity=78,
            output_attribution=40,
            legal_risk=70,
        ),
        copyright=CopyrightAssessment(
            training_data_lawfully_obtained=True,  # vendor claims
            license_verification_documented=True,
            opt_out_compliance_process=True,
            indemnification_for_ai_outputs=True,
            competes_with_training_sources=False,
            pending_litigation=False,
            eu_dsm_article4_compliance=True,
        ),
    )

    vendor_result = evaluate_vendor(scorecard)
    print(f"Vendor:          {scorecard.vendor_name}")
    print(f"Overall Score:   {vendor_result.overall_score:.1f}/100")
    print(f"Tier:            {vendor_result.tier.value.upper()}")
    print(f"Copyright Risk:  {vendor_result.copyright_risk}")

    print(f"\nDimension Breakdown:")
    for dim_name, score in vendor_result.dimension_scores.items():
        bar = "#" * int(score / 5) + "." * (20 - int(score / 5))
        print(f"  {dim_name:25s} [{bar}] {score:.0f}")

    if vendor_result.gaps:
        print(f"\nVendor Gaps ({len(vendor_result.gaps)}):")
        for gap in vendor_result.gaps:
            print(f"  ! {gap}")

    # =================================================================
    # Step 5: Integrated risk flagging
    # =================================================================
    section("STEP 5: INTEGRATED RISK FLAGS")

    # Flag risks based on automated evaluation results

    # Compliance gaps -> risk flags
    if compliance_result.overall_score < 70:
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.HIGH,
            f"Compliance score {compliance_result.overall_score:.0f}/100 below 70 threshold",
        )

    for gap in compliance_result.gaps:
        if "incident response" in gap.lower():
            ctx.flag_risk(
                RiskDimension.SECURITY, RiskLevel.MEDIUM,
                f"Compliance gap: {gap}",
            )

    # Provenance gaps -> risk flags
    if not card.all_licenses_verified:
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.HIGH,
            "Vendor training data includes sources with unverified licenses "
            "(web-scraped content with disputed fair use claim)",
        )

    if card.has_opt_out_gaps:
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.MEDIUM,
            "Vendor has not honored all copyright holder opt-out requests "
            "(EU DSM Directive Article 4 risk)",
        )

    if not guard.within_limits:
        ctx.flag_risk(
            RiskDimension.SECURITY, RiskLevel.HIGH,
            f"Synthetic data ({guard.actual_synthetic_percentage}%) exceeds "
            f"cap ({guard.max_synthetic_percentage}%) — model collapse risk",
        )

    # Vendor scorecard -> risk flags
    if vendor_result.tier == VendorTier.NOT_APPROVED:
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.CRITICAL,
            f"Vendor scored {vendor_result.overall_score:.0f}/100 — NOT APPROVED tier",
        )
    elif vendor_result.copyright_risk in ("high", "critical"):
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.CRITICAL,
            f"Vendor copyright risk assessed as {vendor_result.copyright_risk}",
        )

    if scorecard.ethics_compliance.score < 70:
        ctx.flag_risk(
            RiskDimension.BIAS, RiskLevel.MEDIUM,
            f"Vendor ethics/compliance score {scorecard.ethics_compliance.score}/100 "
            "— creative professional protections need strengthening",
        )

    # =================================================================
    # Step 6: Governance decision
    # =================================================================
    section("STEP 6: GOVERNANCE SUMMARY")

    print(ctx.summary())

    # Register in dashboard for portfolio tracking
    dashboard = GovernanceDashboard()
    dashboard.register(ctx)

    print(f"\n{'=' * 64}")
    if ctx.is_blocked():
        blockers = ctx.get_blockers()
        print(f"  DECISION: BLOCKED — {len(blockers)} blocking issue(s) must be resolved")
        print(f"  Action needed from: {', '.join(ctx.get_reviewers_needed())}")
        print()
        print("  Recommended next steps:")
        print("    1. Require vendor to remove web-scraped data from training set")
        print("       or provide verified license documentation")
        print("    2. Negotiate enhanced indemnification with Thomson Reuters clause")
        print("    3. Request vendor incident response procedure for AI failures")
        print("    4. Re-evaluate after vendor remediation (target: 30 days)")
    else:
        print(f"  DECISION: APPROVED (conditional)")
        print(f"  Vendor tier: {vendor_result.tier.value.upper()}")
        pending = ctx.get_pending_reviews()
        if pending:
            print(f"  {len(pending)} flag(s) pending review before production use")
    print(f"{'=' * 64}")

    # =================================================================
    # Step 7: Serialization — save review artifacts
    # =================================================================
    section("STEP 7: REVIEW ARTIFACTS (JSON-ready)")

    import json
    artifacts = {
        "compliance": compliance_result.to_dict(),
        "provenance": prov_result.to_dict(),
        "vendor": vendor_result.to_dict(),
        "provenance_card": card.to_dict(),
    }
    print(f"Artifacts serialized: {list(artifacts.keys())}")
    print(f"Total JSON size: {len(json.dumps(artifacts)):,} bytes")
    print("\nSample — vendor result:")
    print(json.dumps(vendor_result.to_dict(), indent=2)[:500] + "...")

    print("\n\nReview complete.")


if __name__ == "__main__":
    main()
