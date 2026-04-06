"""
Standards compliance alignment module.

Provides open-schema dataclasses and evaluation helpers for aligning
AI governance with international standards:

  - **ISO/IEC 42001:2023** — AI Management System (AIMS)
  - **NIST AI RMF 1.0 / 600-1** — AI Risk Management Framework
  - **EU AI Act** — European AI regulation (effective Aug 2, 2025)
  - **MovieLabs OMC** — Open Media Cloud production workflow standard

All schemas use plain Python dataclasses with ``to_dict()`` / ``from_dict()``
round-trip support, making them easy to serialize to JSON, YAML, or any
format an adopter prefers.  No proprietary dependencies.

Usage::

    from ai_use_case_context.compliance import (
        ComplianceProfile,
        ISO42001Assessment,
        NISTAIRMFMapping,
        EUAIActChecklist,
        MovieLabsOMCAlignment,
        evaluate_compliance,
    )

    profile = ComplianceProfile(
        iso42001=ISO42001Assessment(aims_documented=True, ...),
        nist_ai_rmf=NISTAIRMFMapping(govern_score=80, ...),
    )
    result = evaluate_compliance(profile)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskClassification(Enum):
    """EU AI Act risk classification tiers."""
    UNACCEPTABLE = "unacceptable"
    HIGH = "high"
    LIMITED = "limited"
    MINIMAL = "minimal"


class AIMSMaturity(Enum):
    """ISO 42001 AI Management System maturity levels."""
    INITIAL = "initial"
    MANAGED = "managed"
    DEFINED = "defined"
    QUANTITATIVELY_MANAGED = "quantitatively_managed"
    OPTIMIZING = "optimizing"


class NISTFunction(Enum):
    """NIST AI RMF core functions."""
    GOVERN = "govern"
    MAP = "map"
    MEASURE = "measure"
    MANAGE = "manage"


class OMCWorkflowPhase(Enum):
    """MovieLabs OMC 2030 Vision workflow phases."""
    CONCEPT = "concept"
    PRE_PRODUCTION = "pre_production"
    PRODUCTION = "production"
    POST_PRODUCTION = "post_production"
    DISTRIBUTION = "distribution"
    ARCHIVE = "archive"


# ---------------------------------------------------------------------------
# ISO/IEC 42001:2023 — AI Management System
# ---------------------------------------------------------------------------

@dataclass
class ISO42001Control:
    """A single ISO 42001 Annex A control assessment.

    Attributes:
        control_id:    Annex A control identifier (e.g. ``"A.5.2"``).
        title:         Control title.
        implemented:   Whether the control is implemented.
        evidence:      Description of implementation evidence.
        gaps:          Known gaps or findings.
    """
    control_id: str
    title: str
    implemented: bool = False
    evidence: str = ""
    gaps: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ISO42001Control:
        return cls(**data)


@dataclass
class ISO42001Assessment:
    """ISO/IEC 42001:2023 AI Management System assessment.

    Captures the Plan-Do-Check-Act methodology required by the standard
    and maps to the 38 Annex A controls for bias mitigation, transparency,
    accountability, and data governance.
    """
    aims_documented: bool = False
    risk_assessment_process: bool = False
    ai_impact_assessment: bool = False
    continuous_improvement_cycle: bool = False
    maturity: AIMSMaturity = AIMSMaturity.INITIAL
    certification_body: str = ""
    certification_date: Optional[date] = None
    annex_a_controls: list[ISO42001Control] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["maturity"] = self.maturity.value
        d["certification_date"] = (
            self.certification_date.isoformat() if self.certification_date else None
        )
        d["annex_a_controls"] = [c.to_dict() for c in self.annex_a_controls]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ISO42001Assessment:
        data = dict(data)
        data["maturity"] = AIMSMaturity(data.get("maturity", "initial"))
        if data.get("certification_date"):
            data["certification_date"] = date.fromisoformat(data["certification_date"])
        data["annex_a_controls"] = [
            ISO42001Control.from_dict(c) for c in data.get("annex_a_controls", [])
        ]
        return cls(**data)

    @property
    def controls_implemented(self) -> int:
        return sum(1 for c in self.annex_a_controls if c.implemented)

    @property
    def controls_total(self) -> int:
        return len(self.annex_a_controls)

    @property
    def score(self) -> float:
        """0-100 score based on key criteria and control implementation."""
        points = 0.0
        # Core AIMS criteria (60 points)
        if self.aims_documented:
            points += 15
        if self.risk_assessment_process:
            points += 15
        if self.ai_impact_assessment:
            points += 15
        if self.continuous_improvement_cycle:
            points += 15
        # Annex A controls (40 points)
        if self.controls_total > 0:
            points += 40 * (self.controls_implemented / self.controls_total)
        return min(points, 100.0)


# ---------------------------------------------------------------------------
# NIST AI RMF 1.0 / 600-1
# ---------------------------------------------------------------------------

@dataclass
class NISTSubcategory:
    """A single NIST AI RMF subcategory assessment.

    Attributes:
        subcategory_id: e.g. ``"GOVERN-1.1"`` or ``"GV-1.1-001"``
        description:    What this subcategory covers.
        addressed:      Whether the organization addresses this.
        evidence:       Implementation evidence.
    """
    subcategory_id: str
    description: str = ""
    addressed: bool = False
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NISTSubcategory:
        return cls(**data)


@dataclass
class NISTAIRMFMapping:
    """NIST AI Risk Management Framework alignment.

    Organized around the four core functions: Govern, Map, Measure, Manage.
    Includes support for NIST AI 600-1 (2025) generative AI supplement
    with 200+ actions specific to generative AI risks.

    Scores are 0-100 per function.
    """
    govern_score: float = 0.0
    map_score: float = 0.0
    measure_score: float = 0.0
    manage_score: float = 0.0
    # Governance committee
    governance_committee_established: bool = False
    committee_roles: list[str] = field(default_factory=list)
    # NIST AI 600-1 generative AI supplement
    gen_ai_supplement_addressed: bool = False
    training_data_poisoning_controls: bool = False
    bias_detection_processes: bool = False
    incident_response_procedures: bool = False
    subcategories: list[NISTSubcategory] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["subcategories"] = [s.to_dict() for s in self.subcategories]
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NISTAIRMFMapping:
        data = dict(data)
        data["subcategories"] = [
            NISTSubcategory.from_dict(s) for s in data.get("subcategories", [])
        ]
        return cls(**data)

    @property
    def composite_score(self) -> float:
        """Weighted composite across the four functions."""
        return (
            self.govern_score * 0.30
            + self.map_score * 0.25
            + self.measure_score * 0.25
            + self.manage_score * 0.20
        )


# ---------------------------------------------------------------------------
# EU AI Act
# ---------------------------------------------------------------------------

@dataclass
class EUAIActChecklist:
    """EU AI Act compliance checklist.

    Covers key GPAI provider obligations effective August 2, 2025.
    Applicable to productions with European distribution or EU-based vendors.

    Attributes:
        risk_classification:        EU AI Act risk tier for this use case.
        training_data_summary_published: GPAI providers must publish summaries.
        copyright_opt_out_policy:   Documented Article 4 opt-out compliance.
        conformity_assessment:      For high-risk systems.
        fundamental_rights_impact:  Impact assessment completed.
        human_oversight_mechanisms: Required for high-risk systems.
        transparency_obligations:   Disclosure that content is AI-generated.
        eu_distribution_planned:    Whether EU distribution is planned.
    """
    risk_classification: RiskClassification = RiskClassification.MINIMAL
    training_data_summary_published: bool = False
    copyright_opt_out_policy: bool = False
    conformity_assessment: bool = False
    fundamental_rights_impact: bool = False
    human_oversight_mechanisms: bool = False
    transparency_obligations: bool = False
    eu_distribution_planned: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["risk_classification"] = self.risk_classification.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EUAIActChecklist:
        data = dict(data)
        data["risk_classification"] = RiskClassification(
            data.get("risk_classification", "minimal")
        )
        return cls(**data)

    @property
    def applicable(self) -> bool:
        """True if EU AI Act requirements apply to this use case."""
        return self.eu_distribution_planned

    @property
    def compliant(self) -> bool:
        """True if all applicable requirements are met."""
        if not self.applicable:
            return True
        checks = [
            self.training_data_summary_published,
            self.copyright_opt_out_policy,
            self.transparency_obligations,
        ]
        if self.risk_classification == RiskClassification.HIGH:
            checks.extend([
                self.conformity_assessment,
                self.fundamental_rights_impact,
                self.human_oversight_mechanisms,
            ])
        return all(checks)

    @property
    def gaps(self) -> list[str]:
        """Return list of unmet requirements."""
        if not self.applicable:
            return []
        gaps = []
        if not self.training_data_summary_published:
            gaps.append("Training data summary not published (EU AI Act Art. 53)")
        if not self.copyright_opt_out_policy:
            gaps.append("Copyright opt-out policy not documented (DSM Directive Art. 4)")
        if not self.transparency_obligations:
            gaps.append("Transparency obligations not met (EU AI Act Art. 52)")
        if self.risk_classification == RiskClassification.HIGH:
            if not self.conformity_assessment:
                gaps.append("Conformity assessment not completed (EU AI Act Art. 43)")
            if not self.fundamental_rights_impact:
                gaps.append("Fundamental rights impact assessment missing (Art. 27)")
            if not self.human_oversight_mechanisms:
                gaps.append("Human oversight mechanisms not established (Art. 14)")
        return gaps


# ---------------------------------------------------------------------------
# MovieLabs OMC (Open Media Cloud) 2030 Vision
# ---------------------------------------------------------------------------

@dataclass
class MovieLabsOMCAlignment:
    """MovieLabs Open Media Cloud alignment assessment.

    Evaluates alignment with the MovieLabs 2030 Vision and OMC framework
    for cloud-based, software-defined production workflows.

    Attributes:
        workflow_phase:             OMC workflow phase for this use case.
        software_defined_workflow:  Uses software-defined workflow patterns.
        cloud_native_architecture:  Runs on cloud-native infrastructure.
        interoperable_data_model:   Uses OMC-compatible data model.
        security_first_design:      Security built into architecture.
        asset_provenance_tracking:  Full asset lineage maintained.
        component_based_pipeline:   Modular, component-based pipeline.
        open_api_interfaces:        Exposes/consumes open API interfaces.
        rights_management:          Integrated rights management.
    """
    workflow_phase: OMCWorkflowPhase = OMCWorkflowPhase.POST_PRODUCTION
    software_defined_workflow: bool = False
    cloud_native_architecture: bool = False
    interoperable_data_model: bool = False
    security_first_design: bool = False
    asset_provenance_tracking: bool = False
    component_based_pipeline: bool = False
    open_api_interfaces: bool = False
    rights_management: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["workflow_phase"] = self.workflow_phase.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MovieLabsOMCAlignment:
        data = dict(data)
        data["workflow_phase"] = OMCWorkflowPhase(
            data.get("workflow_phase", "post_production")
        )
        return cls(**data)

    @property
    def score(self) -> float:
        """0-100 alignment score across OMC principles."""
        criteria = [
            self.software_defined_workflow,
            self.cloud_native_architecture,
            self.interoperable_data_model,
            self.security_first_design,
            self.asset_provenance_tracking,
            self.component_based_pipeline,
            self.open_api_interfaces,
            self.rights_management,
        ]
        return (sum(criteria) / len(criteria)) * 100


# ---------------------------------------------------------------------------
# Composite compliance profile
# ---------------------------------------------------------------------------

@dataclass
class ComplianceProfile:
    """Composite compliance profile aggregating all standards.

    Provides a single entry point for evaluating an AI use case or vendor
    against multiple governance frameworks simultaneously.

    All fields are optional — populate only the standards relevant to
    your organization or jurisdiction.

    Designed as an open schema: serialize with ``to_dict()`` and
    reconstruct with ``from_dict()`` for interoperability with any
    JSON/YAML-based toolchain.
    """
    iso42001: Optional[ISO42001Assessment] = None
    nist_ai_rmf: Optional[NISTAIRMFMapping] = None
    eu_ai_act: Optional[EUAIActChecklist] = None
    movielabs_omc: Optional[MovieLabsOMCAlignment] = None
    assessed_at: datetime = field(default_factory=datetime.now)
    assessor: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "iso42001": self.iso42001.to_dict() if self.iso42001 else None,
            "nist_ai_rmf": self.nist_ai_rmf.to_dict() if self.nist_ai_rmf else None,
            "eu_ai_act": self.eu_ai_act.to_dict() if self.eu_ai_act else None,
            "movielabs_omc": self.movielabs_omc.to_dict() if self.movielabs_omc else None,
            "assessed_at": self.assessed_at.isoformat(),
            "assessor": self.assessor,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComplianceProfile:
        return cls(
            iso42001=(
                ISO42001Assessment.from_dict(data["iso42001"])
                if data.get("iso42001") else None
            ),
            nist_ai_rmf=(
                NISTAIRMFMapping.from_dict(data["nist_ai_rmf"])
                if data.get("nist_ai_rmf") else None
            ),
            eu_ai_act=(
                EUAIActChecklist.from_dict(data["eu_ai_act"])
                if data.get("eu_ai_act") else None
            ),
            movielabs_omc=(
                MovieLabsOMCAlignment.from_dict(data["movielabs_omc"])
                if data.get("movielabs_omc") else None
            ),
            assessed_at=datetime.fromisoformat(data["assessed_at"]) if data.get("assessed_at") else datetime.now(),
            assessor=data.get("assessor", ""),
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

@dataclass
class ComplianceResult:
    """Result of a compliance evaluation.

    Attributes:
        overall_score:  Weighted composite 0-100.
        section_scores: Per-standard scores.
        gaps:           List of identified gaps.
        recommendations: Actionable recommendations.
        assessed_at:    Evaluation timestamp.
    """
    overall_score: float
    section_scores: dict[str, float]
    gaps: list[str]
    recommendations: list[str]
    assessed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "section_scores": {k: round(v, 1) for k, v in self.section_scores.items()},
            "gaps": self.gaps,
            "recommendations": self.recommendations,
            "assessed_at": self.assessed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ComplianceResult:
        return cls(
            overall_score=data["overall_score"],
            section_scores=data["section_scores"],
            gaps=data["gaps"],
            recommendations=data["recommendations"],
            assessed_at=datetime.fromisoformat(data["assessed_at"]) if data.get("assessed_at") else datetime.now(),
        )


def evaluate_compliance(profile: ComplianceProfile) -> ComplianceResult:
    """Evaluate a compliance profile and return scored results.

    Computes per-standard scores, identifies gaps, and generates
    actionable recommendations based on current best practices.

    Returns a :class:`ComplianceResult` with overall and section scores.
    """
    scores: dict[str, float] = {}
    gaps: list[str] = []
    recommendations: list[str] = []

    # --- ISO 42001 ---
    if profile.iso42001:
        iso = profile.iso42001
        scores["iso42001"] = iso.score
        if not iso.aims_documented:
            gaps.append("ISO 42001: AI Management System not documented")
            recommendations.append(
                "Document AIMS structure following ISO 42001 Plan-Do-Check-Act methodology"
            )
        if not iso.ai_impact_assessment:
            gaps.append("ISO 42001: AI impact assessment not performed")
            recommendations.append(
                "Conduct formal AI impact assessment before deployment"
            )
        if not iso.risk_assessment_process:
            gaps.append("ISO 42001: Risk assessment process not established")
    else:
        recommendations.append(
            "Consider ISO/IEC 42001:2023 alignment for AI management system certification"
        )

    # --- NIST AI RMF ---
    if profile.nist_ai_rmf:
        nist = profile.nist_ai_rmf
        scores["nist_ai_rmf"] = nist.composite_score
        if not nist.governance_committee_established:
            gaps.append("NIST GOVERN: Cross-functional governance committee not established")
            recommendations.append(
                "Establish AI governance committee with legal, creative, "
                "technical, and compliance representation per NIST AI RMF GOVERN function"
            )
        if not nist.incident_response_procedures:
            gaps.append("NIST MANAGE: AI-specific incident response procedures missing")
            recommendations.append(
                "Develop incident response procedures specific to AI failures"
            )
        if not nist.gen_ai_supplement_addressed:
            recommendations.append(
                "Address NIST AI 600-1 (2025) generative AI supplement actions"
            )
    else:
        recommendations.append(
            "Map governance framework to NIST AI RMF Govern/Map/Measure/Manage functions"
        )

    # --- EU AI Act ---
    if profile.eu_ai_act:
        eu = profile.eu_ai_act
        eu_gaps = eu.gaps
        gaps.extend(eu_gaps)
        if eu.applicable:
            total_checks = 3
            if eu.risk_classification == RiskClassification.HIGH:
                total_checks = 6
            passed = total_checks - len(eu_gaps)
            scores["eu_ai_act"] = (passed / total_checks) * 100 if total_checks else 100
        else:
            scores["eu_ai_act"] = 100.0
        for g in eu_gaps:
            recommendations.append(f"Address: {g}")
    elif profile.nist_ai_rmf or profile.iso42001:
        recommendations.append(
            "Consider EU AI Act compliance if European distribution is planned"
        )

    # --- MovieLabs OMC ---
    if profile.movielabs_omc:
        omc = profile.movielabs_omc
        scores["movielabs_omc"] = omc.score
        if not omc.asset_provenance_tracking:
            gaps.append("OMC: Asset provenance tracking not implemented")
            recommendations.append(
                "Implement asset-level provenance tracking per MovieLabs OMC 2030 Vision"
            )
        if not omc.interoperable_data_model:
            gaps.append("OMC: Interoperable data model not adopted")
            recommendations.append(
                "Adopt OMC-compatible interoperable data model for production workflows"
            )
        if not omc.security_first_design:
            gaps.append("OMC: Security-first design not established")

    # --- Overall ---
    if scores:
        overall = sum(scores.values()) / len(scores)
    else:
        overall = 0.0

    return ComplianceResult(
        overall_score=overall,
        section_scores=scores,
        gaps=gaps,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# Pre-built Annex A control templates
# ---------------------------------------------------------------------------

def iso42001_annex_a_controls() -> list[ISO42001Control]:
    """Return the standard ISO 42001 Annex A control set as blank templates.

    Organizations can use these as a starting checklist and fill in
    ``implemented``, ``evidence``, and ``gaps`` fields as they assess.
    """
    controls = [
        ("A.2.2", "AI Policy"),
        ("A.2.3", "AI Roles and Responsibilities"),
        ("A.2.4", "Resources for AI"),
        ("A.3.2", "AI Risk Assessment"),
        ("A.3.3", "AI Risk Treatment"),
        ("A.4.2", "AI System Impact Assessment"),
        ("A.4.3", "AI System Lifecycle Documentation"),
        ("A.4.4", "Data Quality for AI Systems"),
        ("A.4.5", "AI System Testing and Validation"),
        ("A.4.6", "AI System Deployment"),
        ("A.4.7", "AI System Monitoring"),
        ("A.5.2", "Bias and Fairness"),
        ("A.5.3", "Transparency"),
        ("A.5.4", "Accountability"),
        ("A.5.5", "Privacy"),
        ("A.6.2", "Data Governance"),
        ("A.6.3", "Data Provenance"),
        ("A.6.4", "Data Quality Management"),
        ("A.7.2", "Third-Party AI Components"),
        ("A.7.3", "AI Supply Chain Security"),
        ("A.8.2", "AI System Security"),
        ("A.8.3", "AI Model Protection"),
        ("A.9.2", "Stakeholder Communication"),
        ("A.9.3", "AI System Documentation"),
        ("A.10.2", "Continual Improvement of AI Systems"),
    ]
    return [ISO42001Control(control_id=cid, title=title) for cid, title in controls]


def nist_ai_rmf_subcategories() -> list[NISTSubcategory]:
    """Return key NIST AI RMF subcategories as blank templates.

    Covers the four core functions: GOVERN, MAP, MEASURE, MANAGE.
    """
    subcats = [
        # GOVERN
        ("GV-1.1", "Policies and procedures for AI risk management are established"),
        ("GV-1.2", "AI risk management roles and responsibilities are defined"),
        ("GV-2.1", "Organizational AI risk tolerance is established"),
        ("GV-3.1", "Cross-functional AI governance committee is operational"),
        ("GV-4.1", "AI talent management and development program exists"),
        ("GV-5.1", "Organizational culture supports AI risk management"),
        # MAP
        ("MP-1.1", "AI system context and intended purpose are documented"),
        ("MP-2.1", "AI system risks are identified and categorized"),
        ("MP-3.1", "AI system benefits and costs are assessed"),
        ("MP-4.1", "Risks from third-party AI components are mapped"),
        ("MP-5.1", "AI system impacts on individuals and communities are mapped"),
        # MEASURE
        ("MS-1.1", "AI system performance metrics are defined and tracked"),
        ("MS-2.1", "AI system fairness and bias metrics are measured"),
        ("MS-3.1", "AI system reliability and robustness are tested"),
        ("MS-4.1", "AI system security testing is conducted"),
        # MANAGE
        ("MG-1.1", "AI risk response strategies are defined"),
        ("MG-2.1", "AI system incidents are reported and tracked"),
        ("MG-3.1", "AI model drift is monitored and managed"),
        ("MG-4.1", "AI system decommissioning procedures are established"),
    ]
    return [NISTSubcategory(subcategory_id=sid, description=desc) for sid, desc in subcats]
