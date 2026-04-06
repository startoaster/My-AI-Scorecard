"""
AI vendor scorecard evaluation module.

Implements a six-dimension weighted scoring framework for evaluating
AI vendors against current best practices in governance, provenance,
ethics, and commercial terms.

Scoring Dimensions (default weights):
  - **Data & Provenance** (25%) — training data transparency, lineage, license compliance
  - **Governance & Security** (20%) — ISO 42001, SOC 2, data isolation, incident response
  - **Ethics & Compliance** (20%) — bias mitigation, ethics board, NIST AI RMF, labor protections
  - **Technical Fit** (15%) — integration, API maturity, version control, production readiness
  - **Commercial Terms** (10%) — IP ownership, termination rights, data portability
  - **Operating Model** (10%) — support, implementation, training, monitoring

All schemas use plain Python dataclasses with ``to_dict()`` / ``from_dict()``
round-trip support for open-source interoperability.

Usage::

    from ai_use_case_context.vendor_scorecard import (
        VendorScorecard,
        ScorecardDimension,
        evaluate_vendor,
    )

    scorecard = VendorScorecard(
        vendor_name="Acme AI",
        data_provenance=DimensionScore(score=85, ...),
        governance_security=DimensionScore(score=70, ...),
    )
    result = evaluate_vendor(scorecard)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ScorecardDimension(Enum):
    """The six vendor evaluation dimensions."""
    DATA_PROVENANCE = "Data & Provenance"
    GOVERNANCE_SECURITY = "Governance & Security"
    ETHICS_COMPLIANCE = "Ethics & Compliance"
    TECHNICAL_FIT = "Technical Fit"
    COMMERCIAL_TERMS = "Commercial Terms"
    OPERATING_MODEL = "Operating Model"


class VendorTier(Enum):
    """Vendor classification tier based on overall score."""
    PREFERRED = "preferred"
    APPROVED = "approved"
    CONDITIONAL = "conditional"
    NOT_APPROVED = "not_approved"


# Default weights per dimension (must sum to 1.0)
DEFAULT_WEIGHTS: dict[ScorecardDimension, float] = {
    ScorecardDimension.DATA_PROVENANCE: 0.25,
    ScorecardDimension.GOVERNANCE_SECURITY: 0.20,
    ScorecardDimension.ETHICS_COMPLIANCE: 0.20,
    ScorecardDimension.TECHNICAL_FIT: 0.15,
    ScorecardDimension.COMMERCIAL_TERMS: 0.10,
    ScorecardDimension.OPERATING_MODEL: 0.10,
}

# Tier thresholds
DEFAULT_TIER_THRESHOLDS: dict[VendorTier, float] = {
    VendorTier.PREFERRED: 80.0,
    VendorTier.APPROVED: 60.0,
    VendorTier.CONDITIONAL: 40.0,
    VendorTier.NOT_APPROVED: 0.0,
}


# ---------------------------------------------------------------------------
# Dimension score
# ---------------------------------------------------------------------------

@dataclass
class DimensionScore:
    """Score for a single evaluation dimension (0-100).

    Attributes:
        score:    Numeric score 0-100.
        evidence: Supporting evidence or documentation references.
        gaps:     Identified gaps or weaknesses.
        notes:    Additional assessor notes.
    """
    score: float = 0.0
    evidence: str = ""
    gaps: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DimensionScore:
        return cls(**data)


# ---------------------------------------------------------------------------
# Vendor question responses
# ---------------------------------------------------------------------------

@dataclass
class VendorQuestion:
    """A single vendor assessment question and response.

    Based on the AI Vendor Security and Safety Assessment Guide
    and ISO 42001 requirements.
    """
    question_id: str
    question: str
    dimension: ScorecardDimension
    response: str = ""
    satisfactory: bool = False
    evidence_url: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["dimension"] = self.dimension.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VendorQuestion:
        data = dict(data)
        data["dimension"] = ScorecardDimension(data["dimension"])
        return cls(**data)


# ---------------------------------------------------------------------------
# KBYUTS (Know Before You Use Their Stuff) scoring criteria
# ---------------------------------------------------------------------------

@dataclass
class KBYUTSScores:
    """Quantitative scoring criteria for the KBYUTS evaluation engine.

    Each score is 0-100 and maps to a specific aspect of vendor assessment.
    """
    training_data_transparency: float = 0.0
    creative_professional_treatment: float = 0.0
    governance_maturity: float = 0.0
    output_attribution: float = 0.0
    legal_risk: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KBYUTSScores:
        return cls(**data)

    @property
    def composite_score(self) -> float:
        """Weighted composite of all KBYUTS criteria."""
        return (
            self.training_data_transparency * 0.25
            + self.creative_professional_treatment * 0.20
            + self.governance_maturity * 0.20
            + self.output_attribution * 0.20
            + self.legal_risk * 0.15
        )


# ---------------------------------------------------------------------------
# Copyright compliance assessment
# ---------------------------------------------------------------------------

@dataclass
class CopyrightAssessment:
    """Copyright compliance evaluation for an AI vendor.

    Post-Thomson Reuters v. ROSS Intelligence (Feb 2025) landscape assessment.
    """
    training_data_lawfully_obtained: bool = False
    license_verification_documented: bool = False
    opt_out_compliance_process: bool = False
    indemnification_for_ai_outputs: bool = False
    competes_with_training_sources: bool = False
    pending_litigation: bool = False
    eu_dsm_article4_compliance: bool = False
    eu_training_data_summary_published: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CopyrightAssessment:
        return cls(**data)

    @property
    def risk_level(self) -> str:
        """Assess copyright risk level: low, medium, high, critical."""
        critical_flags = [
            self.competes_with_training_sources and not self.training_data_lawfully_obtained,
            self.pending_litigation,
        ]
        high_flags = [
            not self.training_data_lawfully_obtained,
            not self.license_verification_documented,
            self.competes_with_training_sources,
        ]
        if any(critical_flags):
            return "critical"
        if sum(high_flags) >= 2:
            return "high"
        if not self.opt_out_compliance_process or not self.indemnification_for_ai_outputs:
            return "medium"
        return "low"

    @property
    def gaps(self) -> list[str]:
        """Return list of copyright compliance gaps."""
        gaps = []
        if not self.training_data_lawfully_obtained:
            gaps.append("Training data not confirmed as lawfully obtained")
        if not self.license_verification_documented:
            gaps.append("License verification not documented")
        if not self.opt_out_compliance_process:
            gaps.append("No opt-out compliance process (EU DSM Directive Art. 4)")
        if not self.indemnification_for_ai_outputs:
            gaps.append("No indemnification for copyright claims from AI outputs")
        if self.competes_with_training_sources:
            gaps.append("AI tool competes with training data sources (Thomson Reuters risk)")
        if self.pending_litigation:
            gaps.append("Vendor has pending copyright litigation")
        return gaps


# ---------------------------------------------------------------------------
# Vendor scorecard
# ---------------------------------------------------------------------------

@dataclass
class VendorScorecard:
    """Complete vendor evaluation scorecard.

    Aggregates six scoring dimensions, KBYUTS criteria, copyright assessment,
    and vendor questionnaire responses into a single evaluable document.

    Designed as an open schema for easy open-source adoption.
    """
    vendor_name: str
    vendor_url: str = ""
    assessed_at: datetime = field(default_factory=datetime.now)
    assessor: str = ""
    # Six dimension scores
    data_provenance: DimensionScore = field(default_factory=DimensionScore)
    governance_security: DimensionScore = field(default_factory=DimensionScore)
    ethics_compliance: DimensionScore = field(default_factory=DimensionScore)
    technical_fit: DimensionScore = field(default_factory=DimensionScore)
    commercial_terms: DimensionScore = field(default_factory=DimensionScore)
    operating_model: DimensionScore = field(default_factory=DimensionScore)
    # Extended scoring
    kbyuts: Optional[KBYUTSScores] = None
    copyright: Optional[CopyrightAssessment] = None
    questions: list[VendorQuestion] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor_name": self.vendor_name,
            "vendor_url": self.vendor_url,
            "assessed_at": self.assessed_at.isoformat(),
            "assessor": self.assessor,
            "data_provenance": self.data_provenance.to_dict(),
            "governance_security": self.governance_security.to_dict(),
            "ethics_compliance": self.ethics_compliance.to_dict(),
            "technical_fit": self.technical_fit.to_dict(),
            "commercial_terms": self.commercial_terms.to_dict(),
            "operating_model": self.operating_model.to_dict(),
            "kbyuts": self.kbyuts.to_dict() if self.kbyuts else None,
            "copyright": self.copyright.to_dict() if self.copyright else None,
            "questions": [q.to_dict() for q in self.questions],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VendorScorecard:
        return cls(
            vendor_name=data["vendor_name"],
            vendor_url=data.get("vendor_url", ""),
            assessed_at=datetime.fromisoformat(data["assessed_at"]) if data.get("assessed_at") else datetime.now(),
            assessor=data.get("assessor", ""),
            data_provenance=DimensionScore.from_dict(data.get("data_provenance", {})),
            governance_security=DimensionScore.from_dict(data.get("governance_security", {})),
            ethics_compliance=DimensionScore.from_dict(data.get("ethics_compliance", {})),
            technical_fit=DimensionScore.from_dict(data.get("technical_fit", {})),
            commercial_terms=DimensionScore.from_dict(data.get("commercial_terms", {})),
            operating_model=DimensionScore.from_dict(data.get("operating_model", {})),
            kbyuts=KBYUTSScores.from_dict(data["kbyuts"]) if data.get("kbyuts") else None,
            copyright=CopyrightAssessment.from_dict(data["copyright"]) if data.get("copyright") else None,
            questions=[VendorQuestion.from_dict(q) for q in data.get("questions", [])],
            notes=data.get("notes", ""),
        )

    def dimension_scores(self) -> dict[ScorecardDimension, float]:
        """Return all dimension scores as a mapping."""
        return {
            ScorecardDimension.DATA_PROVENANCE: self.data_provenance.score,
            ScorecardDimension.GOVERNANCE_SECURITY: self.governance_security.score,
            ScorecardDimension.ETHICS_COMPLIANCE: self.ethics_compliance.score,
            ScorecardDimension.TECHNICAL_FIT: self.technical_fit.score,
            ScorecardDimension.COMMERCIAL_TERMS: self.commercial_terms.score,
            ScorecardDimension.OPERATING_MODEL: self.operating_model.score,
        }


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

@dataclass
class VendorResult:
    """Result of a vendor scorecard evaluation.

    Attributes:
        overall_score:    Weighted composite 0-100.
        tier:             Vendor classification tier.
        dimension_scores: Per-dimension weighted contributions.
        gaps:             Identified gaps across all dimensions.
        recommendations:  Actionable recommendations.
        copyright_risk:   Copyright risk level (low/medium/high/critical).
    """
    overall_score: float
    tier: VendorTier
    dimension_scores: dict[str, float]
    gaps: list[str]
    recommendations: list[str]
    copyright_risk: str = "unknown"
    assessed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 1),
            "tier": self.tier.value,
            "dimension_scores": {k: round(v, 1) for k, v in self.dimension_scores.items()},
            "gaps": self.gaps,
            "recommendations": self.recommendations,
            "copyright_risk": self.copyright_risk,
            "assessed_at": self.assessed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VendorResult:
        return cls(
            overall_score=data["overall_score"],
            tier=VendorTier(data["tier"]),
            dimension_scores=data["dimension_scores"],
            gaps=data["gaps"],
            recommendations=data["recommendations"],
            copyright_risk=data.get("copyright_risk", "unknown"),
            assessed_at=datetime.fromisoformat(data["assessed_at"]) if data.get("assessed_at") else datetime.now(),
        )


def evaluate_vendor(
    scorecard: VendorScorecard,
    weights: Optional[dict[ScorecardDimension, float]] = None,
    tier_thresholds: Optional[dict[VendorTier, float]] = None,
) -> VendorResult:
    """Evaluate a vendor scorecard and return a comprehensive result.

    Args:
        scorecard:        The vendor scorecard to evaluate.
        weights:          Optional custom dimension weights (must sum to 1.0).
        tier_thresholds:  Optional custom tier thresholds.

    Returns:
        A :class:`VendorResult` with overall score, tier, gaps, and recommendations.
    """
    w = weights or DEFAULT_WEIGHTS
    thresholds = tier_thresholds or DEFAULT_TIER_THRESHOLDS

    gaps: list[str] = []
    recommendations: list[str] = []

    # Compute weighted score
    scores = scorecard.dimension_scores()
    dim_contributions: dict[str, float] = {}
    overall = 0.0
    for dim, score in scores.items():
        weight = w.get(dim, 0)
        contribution = score * weight
        dim_contributions[dim.value] = score
        overall += contribution

        # Identify dimension-level gaps
        if score < 40:
            gaps.append(f"{dim.value}: Score {score}/100 — critical gap")
        elif score < 60:
            gaps.append(f"{dim.value}: Score {score}/100 — needs improvement")

    # Dimension-specific recommendations
    if scorecard.data_provenance.score < 60:
        recommendations.append(
            "Improve training data transparency: require dataset cards, "
            "provenance documentation, and license verification"
        )
    if scorecard.governance_security.score < 60:
        recommendations.append(
            "Strengthen governance: pursue ISO 42001 certification, "
            "SOC 2 Type II, data isolation controls"
        )
    if scorecard.ethics_compliance.score < 60:
        recommendations.append(
            "Enhance ethics: establish bias mitigation processes, "
            "ethics board, NIST AI RMF alignment"
        )
    if scorecard.technical_fit.score < 60:
        recommendations.append(
            "Address technical gaps: improve integration capabilities, "
            "API maturity, version control practices"
        )

    # Copyright assessment
    copyright_risk = "unknown"
    if scorecard.copyright:
        copyright_risk = scorecard.copyright.risk_level
        cr_gaps = scorecard.copyright.gaps
        gaps.extend(cr_gaps)
        if copyright_risk in ("high", "critical"):
            recommendations.append(
                "Address copyright risk: verify training data provenance, "
                "obtain indemnification, assess Thomson Reuters precedent risk"
            )

    # KBYUTS integration
    if scorecard.kbyuts:
        kbyuts_score = scorecard.kbyuts.composite_score
        if kbyuts_score < 50:
            recommendations.append(
                f"KBYUTS composite score ({kbyuts_score:.0f}/100) is low — "
                "review training data transparency and creative professional treatment"
            )

    # Determine tier
    tier = VendorTier.NOT_APPROVED
    for t in [VendorTier.PREFERRED, VendorTier.APPROVED, VendorTier.CONDITIONAL]:
        if overall >= thresholds[t]:
            tier = t
            break

    return VendorResult(
        overall_score=overall,
        tier=tier,
        dimension_scores=dim_contributions,
        gaps=gaps,
        recommendations=recommendations,
        copyright_risk=copyright_risk,
    )


# ---------------------------------------------------------------------------
# Pre-built vendor questionnaire templates
# ---------------------------------------------------------------------------

def essential_vendor_questions() -> list[VendorQuestion]:
    """Return the essential vendor assessment questions.

    Based on the AI Vendor Security and Safety Assessment Guide
    and ISO 42001 requirements. Organizations should require vendors
    to answer these before engagement.
    """
    questions = [
        VendorQuestion(
            question_id="VQ-001",
            question="What specific encryption standards (e.g., AES-256) do you use for production data at rest and in transit?",
            dimension=ScorecardDimension.GOVERNANCE_SECURITY,
        ),
        VendorQuestion(
            question_id="VQ-002",
            question="Have you adopted ISO 42001 or NIST AI RMF? If so, provide certification documentation.",
            dimension=ScorecardDimension.GOVERNANCE_SECURITY,
        ),
        VendorQuestion(
            question_id="VQ-003",
            question="How do you document model testing and validation for auditing purposes?",
            dimension=ScorecardDimension.GOVERNANCE_SECURITY,
        ),
        VendorQuestion(
            question_id="VQ-004",
            question="What frameworks address potential AI bias in your systems?",
            dimension=ScorecardDimension.ETHICS_COMPLIANCE,
        ),
        VendorQuestion(
            question_id="VQ-005",
            question="Can you provide field-level lineage showing how production data would flow through your system?",
            dimension=ScorecardDimension.DATA_PROVENANCE,
        ),
        VendorQuestion(
            question_id="VQ-006",
            question="What is your policy on using client data to train or improve your models?",
            dimension=ScorecardDimension.DATA_PROVENANCE,
        ),
        VendorQuestion(
            question_id="VQ-007",
            question="How do you address model drift and when does retraining occur?",
            dimension=ScorecardDimension.TECHNICAL_FIT,
        ),
        VendorQuestion(
            question_id="VQ-008",
            question="What percentage of your training data is synthetic, and how is synthetic data provenance tracked?",
            dimension=ScorecardDimension.DATA_PROVENANCE,
        ),
        VendorQuestion(
            question_id="VQ-009",
            question="Do you provide indemnification for copyright claims arising from AI outputs?",
            dimension=ScorecardDimension.COMMERCIAL_TERMS,
        ),
        VendorQuestion(
            question_id="VQ-010",
            question="Has your training data been obtained through lawful means with appropriate licenses?",
            dimension=ScorecardDimension.DATA_PROVENANCE,
        ),
        VendorQuestion(
            question_id="VQ-011",
            question="What processes exist to honor rights holder opt-outs from AI training?",
            dimension=ScorecardDimension.ETHICS_COMPLIANCE,
        ),
        VendorQuestion(
            question_id="VQ-012",
            question="Does your AI tool compete with the sources of its training data?",
            dimension=ScorecardDimension.COMMERCIAL_TERMS,
        ),
        VendorQuestion(
            question_id="VQ-013",
            question="What is your incident response SLA for AI system failures?",
            dimension=ScorecardDimension.OPERATING_MODEL,
        ),
        VendorQuestion(
            question_id="VQ-014",
            question="What data portability and export capabilities do you provide upon contract termination?",
            dimension=ScorecardDimension.COMMERCIAL_TERMS,
        ),
        VendorQuestion(
            question_id="VQ-015",
            question="Have you published a training data summary per EU AI Act requirements for GPAI providers?",
            dimension=ScorecardDimension.ETHICS_COMPLIANCE,
        ),
    ]
    return questions
