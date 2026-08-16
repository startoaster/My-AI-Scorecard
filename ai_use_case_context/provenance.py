"""
Data provenance and lineage tracking module.

Provides open-schema dataclasses for tracking data provenance through
AI production pipelines, aligned with 2025 best practices:

  - **Source-level metadata** — URL, collection date, license, capture method
  - **Generation flags** — human-origin, machine-origin, unknown with confidence
  - **Transformation logs** — dedup, cleaning, OCR, translation, augmentation
  - **Bi-temporal lineage** — reconstruct data state at any historical moment
  - **Dataset versioning** — unique version, timestamps, lineage metadata
  - **Model collapse prevention** — synthetic data caps and disclosure

All schemas use plain Python dataclasses with ``to_dict()`` / ``from_dict()``
round-trip support for open-source interoperability.

Usage::

    from ai_use_case_context.provenance import (
        DataSource,
        GenerationFlag,
        TransformationRecord,
        DatasetVersion,
        ProvenanceCard,
        ModelCollapseGuard,
    )

    source = DataSource(
        name="Licensed Motion Library",
        url="https://example.com/mocap",
        license_type="Commercial",
        capture_method="motion_capture",
    )
    card = ProvenanceCard(
        dataset_name="Hero Character MoCap v2",
        sources=[source],
        generation_flag=GenerationFlag.HUMAN_ORIGIN,
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING

from ai_use_case_context.authority import Authority, AuthoritySource
from ai_use_case_context.core import RiskDimension, RiskLevel

if TYPE_CHECKING:  # pragma: no cover
    from ai_use_case_context.core import RiskFlag, UseCaseContext


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GenerationFlag(Enum):
    """Content origin classification with confidence scoring."""
    HUMAN_ORIGIN = "human_origin"
    MACHINE_ORIGIN = "machine_origin"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


class CaptureMethod(Enum):
    """How the source data was captured or obtained."""
    CRAWL = "crawl"
    PARTNER_FEED = "partner_feed"
    USER_SUBMISSION = "user_submission"
    SENSOR = "sensor"
    MOTION_CAPTURE = "motion_capture"
    LIDAR = "lidar"
    VOLUMETRIC = "volumetric"
    FACS = "facs"
    PHOTOGRAMMETRY = "photogrammetry"
    MANUAL_CREATION = "manual_creation"
    API = "api"
    LICENSED_DATASET = "licensed_dataset"
    SYNTHETIC = "synthetic"
    OTHER = "other"


class TransformationType(Enum):
    """Types of data transformations applied during processing."""
    DEDUPLICATION = "deduplication"
    CLEANING = "cleaning"
    OCR = "ocr"
    TRANSLATION = "translation"
    AUGMENTATION = "augmentation"
    NORMALIZATION = "normalization"
    FILTERING = "filtering"
    ANONYMIZATION = "anonymization"
    COMPRESSION = "compression"
    FORMAT_CONVERSION = "format_conversion"
    ANNOTATION = "annotation"
    SYNTHETIC_GENERATION = "synthetic_generation"
    OTHER = "other"


class LicenseCompliance(Enum):
    """License compliance status."""
    VERIFIED = "verified"
    PENDING_REVIEW = "pending_review"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


# ---------------------------------------------------------------------------
# Data source metadata
# ---------------------------------------------------------------------------

@dataclass
class DataSource:
    """Source-level metadata for a data asset.

    Captures the essential provenance information for a single data source
    per 2025 data provenance standards.
    """
    name: str
    url: str = ""
    collection_date: Optional[datetime] = None
    license_type: str = ""
    license_compliance: LicenseCompliance = LicenseCompliance.UNKNOWN
    capture_method: CaptureMethod = CaptureMethod.OTHER
    copyright_holder: str = ""
    opt_out_honored: bool = False
    consent_documented: bool = False
    geographic_origin: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["collection_date"] = (
            self.collection_date.isoformat() if self.collection_date else None
        )
        d["license_compliance"] = self.license_compliance.value
        d["capture_method"] = self.capture_method.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataSource:
        data = dict(data)
        if data.get("collection_date"):
            data["collection_date"] = datetime.fromisoformat(data["collection_date"])
        data["license_compliance"] = LicenseCompliance(
            data.get("license_compliance", "unknown")
        )
        data["capture_method"] = CaptureMethod(
            data.get("capture_method", "other")
        )
        return cls(**data)


# ---------------------------------------------------------------------------
# Transformation log
# ---------------------------------------------------------------------------

@dataclass
class TransformationRecord:
    """A single transformation applied to data during processing.

    Maintains an ordered log of all transformations for full lineage
    reconstruction and audit compliance.
    """
    transformation_type: TransformationType
    description: str = ""
    applied_at: datetime = field(default_factory=datetime.now)
    applied_by: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    input_hash: str = ""
    output_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["transformation_type"] = self.transformation_type.value
        d["applied_at"] = self.applied_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransformationRecord:
        data = dict(data)
        data["transformation_type"] = TransformationType(
            data.get("transformation_type", "other")
        )
        if data.get("applied_at"):
            data["applied_at"] = datetime.fromisoformat(data["applied_at"])
        return cls(**data)


# ---------------------------------------------------------------------------
# Dataset versioning (bi-temporal lineage)
# ---------------------------------------------------------------------------

@dataclass
class DatasetVersion:
    """A versioned snapshot of a dataset with bi-temporal lineage support.

    Bi-temporal lineage allows reconstruction of the dataset state at any
    historical moment for audit purposes:
      - ``valid_from`` / ``valid_to``: when this version was the active version
      - ``recorded_at``: when the version record was created
    """
    version_id: str
    dataset_name: str
    created_at: datetime = field(default_factory=datetime.now)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    recorded_at: datetime = field(default_factory=datetime.now)
    record_count: int = 0
    size_bytes: int = 0
    checksum: str = ""
    parent_version_id: str = ""
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for dt_field in ("created_at", "valid_from", "valid_to", "recorded_at"):
            val = getattr(self, dt_field)
            d[dt_field] = val.isoformat() if val else None
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetVersion:
        data = dict(data)
        for dt_field in ("created_at", "valid_from", "valid_to", "recorded_at"):
            if data.get(dt_field):
                data[dt_field] = datetime.fromisoformat(data[dt_field])
        return cls(**data)


# ---------------------------------------------------------------------------
# Provenance card — human-readable provenance summary
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceCard:
    """Human-readable provenance card for a dataset.

    Adopts the emerging standard of provenance cards that aggregate
    source metadata, generation flags, transformation history, and
    compliance status into a single auditable document.

    Designed for open-schema interoperability — serialize to JSON/YAML
    and share with regulators, auditors, or collaborators.
    """
    dataset_name: str
    description: str = ""
    sources: list[DataSource] = field(default_factory=list)
    generation_flag: GenerationFlag = GenerationFlag.UNKNOWN
    generation_confidence: float = 0.0
    transformations: list[TransformationRecord] = field(default_factory=list)
    versions: list[DatasetVersion] = field(default_factory=list)
    current_version_id: str = ""
    synthetic_percentage: float = 0.0
    license_summary: str = ""
    lawful_basis: str = ""
    consent_documentation_url: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name": self.dataset_name,
            "description": self.description,
            "sources": [s.to_dict() for s in self.sources],
            "generation_flag": self.generation_flag.value,
            "generation_confidence": self.generation_confidence,
            "transformations": [t.to_dict() for t in self.transformations],
            "versions": [v.to_dict() for v in self.versions],
            "current_version_id": self.current_version_id,
            "synthetic_percentage": self.synthetic_percentage,
            "license_summary": self.license_summary,
            "lawful_basis": self.lawful_basis,
            "consent_documentation_url": self.consent_documentation_url,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceCard:
        data = dict(data)
        data["sources"] = [DataSource.from_dict(s) for s in data.get("sources", [])]
        data["generation_flag"] = GenerationFlag(
            data.get("generation_flag", "unknown")
        )
        data["transformations"] = [
            TransformationRecord.from_dict(t) for t in data.get("transformations", [])
        ]
        data["versions"] = [
            DatasetVersion.from_dict(v) for v in data.get("versions", [])
        ]
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)

    @property
    def all_licenses_verified(self) -> bool:
        """True if all sources have verified license compliance."""
        if not self.sources:
            return False
        return all(
            s.license_compliance == LicenseCompliance.VERIFIED
            for s in self.sources
        )

    @property
    def has_opt_out_gaps(self) -> bool:
        """True if any source has not honored opt-out requests."""
        return any(
            not s.opt_out_honored
            for s in self.sources
            if s.copyright_holder
        )

    @property
    def provenance_complete(self) -> bool:
        """True if provenance is considered complete for audit.

        Complete means *documented*, not *clean*. A card recording a source
        whose licence is known to be non-compliant is complete and still
        raises a critical finding — see :meth:`derive_flags`.
        """
        if not self.sources:
            return False
        if self.generation_flag == GenerationFlag.UNKNOWN and self.generation_confidence < 0.8:
            return False
        return all(
            s.license_compliance != LicenseCompliance.UNKNOWN
            for s in self.sources
        )

    def derive_flags(
        self,
        ctx: "UseCaseContext",
        guard: Optional["ModelCollapseGuard"] = None,
        rules: Optional[list["ProvenanceRule"]] = None,
    ) -> list["RiskFlag"]:
        """Raise flags on ``ctx`` for every rule matching this card.

        This is how provenance reaches the governance engine.
        :func:`evaluate_provenance` measures how thoroughly lineage is
        *documented*, which is a real and separate question — a fully
        documented dataset can still be unusable, and an undocumented one is
        not automatically unlawful. Use this for the risk, that for the
        coverage.

        Returns the flags that were added.
        """
        active = DEFAULT_PROVENANCE_RULES if rules is None else rules
        added: list["RiskFlag"] = []
        for rule in active:
            if not rule.applies(self, guard):
                continue
            added.append(
                ctx.flag_risk(
                    dimension=rule.dimension,
                    level=rule.level,
                    description=rule.describe(self, guard),
                    authority=rule.authority,
                    source=rule.source,
                )
            )
        return added


# ---------------------------------------------------------------------------
# Model collapse prevention guard
# ---------------------------------------------------------------------------

@dataclass
class ModelCollapseGuard:
    """Configuration and evaluation for model collapse prevention.

    Model collapse occurs when AI systems train on outputs from other
    AI models, leading to degraded quality. This guard tracks synthetic
    data percentages and enforces caps.

    Attributes:
        max_synthetic_percentage: Maximum allowed synthetic content (0-100).
        actual_synthetic_percentage: Measured synthetic content percentage.
        unknown_provenance_allowed: Whether unknown-provenance data is allowed.
        high_stakes_domain: If True, stricter rules apply.
        vendor_disclosure_received: Vendor has disclosed synthetic data use.
    """
    max_synthetic_percentage: float = 30.0
    actual_synthetic_percentage: float = 0.0
    unknown_provenance_allowed: bool = False
    high_stakes_domain: bool = False
    vendor_disclosure_received: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModelCollapseGuard:
        return cls(**data)

    @property
    def within_limits(self) -> bool:
        """True if synthetic content is within allowed limits."""
        return self.actual_synthetic_percentage <= self.max_synthetic_percentage

    @property
    def violations(self) -> list[str]:
        """Return list of model collapse guard violations."""
        issues = []
        if not self.within_limits:
            issues.append(
                f"Synthetic content ({self.actual_synthetic_percentage}%) "
                f"exceeds cap ({self.max_synthetic_percentage}%)"
            )
        if not self.vendor_disclosure_received:
            issues.append("Vendor has not disclosed synthetic data percentages")
        if self.high_stakes_domain and not self.vendor_disclosure_received:
            issues.append(
                "High-stakes domain requires vendor synthetic data disclosure"
            )
        if self.high_stakes_domain and self.actual_synthetic_percentage > 0 and not self.vendor_disclosure_received:
            issues.append(
                "Unknown-provenance content in high-stakes domain requires strict review"
            )
        return issues


# ---------------------------------------------------------------------------
# Flag derivation — the path into the governance engine
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceRule:
    """A rule that turns a recorded provenance fact into a risk flag.

    ``applies`` receives the card and the model collapse guard, which may be
    ``None`` when no guard is configured.
    """
    rule_id: str
    title: str
    applies: Callable[["ProvenanceCard", Optional["ModelCollapseGuard"]], bool]
    dimension: Any
    level: RiskLevel
    describe: Callable[["ProvenanceCard", Optional["ModelCollapseGuard"]], str]
    authority: Authority = Authority.UNSPECIFIED
    source: Optional[AuthoritySource] = None


_LICENCE_TERMS = AuthoritySource(
    body="Source licence terms",
    authority=Authority.BINDING_CONTRACT,
    citation="Terms vary by source; confirm per dataset",
)

_TDM_RESERVATION = AuthoritySource(
    body="Text and data mining reservation",
    authority=Authority.STATUTE,
    citation="Applicable regime depends on where mining occurred",
)


def _non_compliant_sources(card: "ProvenanceCard") -> list[DataSource]:
    return [
        s for s in card.sources
        if s.license_compliance == LicenseCompliance.NON_COMPLIANT
    ]


def _unknown_licence_sources(card: "ProvenanceCard") -> list[DataSource]:
    return [
        s for s in card.sources
        if s.license_compliance == LicenseCompliance.UNKNOWN
    ]


DEFAULT_PROVENANCE_RULES: list[ProvenanceRule] = [
    ProvenanceRule(
        rule_id="NON_COMPLIANT_LICENCE",
        title="Source with a licence known to be non-compliant",
        applies=lambda card, guard: bool(_non_compliant_sources(card)),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.CRITICAL,
        authority=Authority.BINDING_CONTRACT,
        source=_LICENCE_TERMS,
        describe=lambda card, guard: (
            "Sources with non-compliant licences: "
            + ", ".join(s.name for s in _non_compliant_sources(card))
            + ". A known breach is not a documentation gap and cannot be "
              "cleared by documenting it."
        ),
    ),
    ProvenanceRule(
        rule_id="UNKNOWN_LICENCE_STATUS",
        title="Source with unknown licence status",
        applies=lambda card, guard: bool(_unknown_licence_sources(card)),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        describe=lambda card, guard: (
            "Sources with unknown licence status: "
            + ", ".join(s.name for s in _unknown_licence_sources(card))
            + ". Determine status before this material is relied on."
        ),
    ),
    ProvenanceRule(
        rule_id="OPT_OUT_NOT_HONOURED",
        title="Rights-holder reservation not honoured",
        applies=lambda card, guard: card.has_opt_out_gaps,
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        authority=Authority.STATUTE,
        source=_TDM_RESERVATION,
        describe=lambda card, guard: (
            "One or more sources with an identified copyright holder have no "
            "record of a reservation being honoured."
        ),
    ),
    ProvenanceRule(
        rule_id="NO_SOURCES_DOCUMENTED",
        title="No sources documented at all",
        applies=lambda card, guard: not card.sources,
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        describe=lambda card, guard: (
            f"'{card.dataset_name}' documents no sources. Nothing about its "
            f"lineage can be asserted or checked."
        ),
    ),
    ProvenanceRule(
        rule_id="UNKNOWN_GENERATION_ORIGIN",
        title="Content origin unknown",
        applies=lambda card, guard: (
            card.generation_flag is GenerationFlag.UNKNOWN
            and card.generation_confidence < 0.8
        ),
        dimension=RiskDimension.QUALITY,
        level=RiskLevel.MEDIUM,
        describe=lambda card, guard: (
            f"Origin of '{card.dataset_name}' is unclassified at "
            f"{card.generation_confidence:.0%} confidence. Whether the "
            f"material is human, machine, or mixed in origin is unresolved."
        ),
    ),
    ProvenanceRule(
        rule_id="SYNTHETIC_SHARE_OVER_CAP",
        title="Synthetic content over the configured cap",
        applies=lambda card, guard: guard is not None and not guard.within_limits,
        dimension=RiskDimension.QUALITY,
        level=RiskLevel.HIGH,
        describe=lambda card, guard: (
            f"Synthetic content is {guard.actual_synthetic_percentage:.0f}% "
            f"against a cap of {guard.max_synthetic_percentage:.0f}%. "
            f"Recursive training on generated material degrades quality in "
            f"ways that are hard to detect downstream."
        ),
    ),
    ProvenanceRule(
        rule_id="NO_SYNTHETIC_DISCLOSURE_HIGH_STAKES",
        title="No synthetic-content disclosure in a high-stakes domain",
        applies=lambda card, guard: (
            guard is not None
            and guard.high_stakes_domain
            and not guard.vendor_disclosure_received
        ),
        dimension=RiskDimension.QUALITY,
        level=RiskLevel.HIGH,
        describe=lambda card, guard: (
            "This is a high-stakes domain and the vendor has not disclosed "
            "synthetic data percentages, so the cap cannot be verified."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Lineage evaluation helper
# ---------------------------------------------------------------------------

@dataclass
class ProvenanceResult:
    """Result of a provenance evaluation.

    Attributes:
        score:           0-100 provenance completeness score.
        gaps:            Identified provenance gaps.
        recommendations: Actionable recommendations.
    """
    score: float
    gaps: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "gaps": self.gaps,
            "recommendations": self.recommendations,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProvenanceResult:
        return cls(**data)


def evaluate_provenance(card: ProvenanceCard, guard: Optional[ModelCollapseGuard] = None) -> ProvenanceResult:
    """Evaluate a provenance card against 2025 best practices.

    Checks source metadata completeness, license compliance, generation
    flags, transformation logging, versioning, and model collapse guards.

    Returns a :class:`ProvenanceResult` with score, gaps, and recommendations.
    """
    gaps: list[str] = []
    recommendations: list[str] = []
    points = 0.0
    max_points = 0.0

    # Source metadata completeness (30 points)
    max_points += 30
    if card.sources:
        source_scores = []
        for src in card.sources:
            src_score = 0
            checks = 0
            if src.name:
                src_score += 1
            checks += 1
            if src.license_type:
                src_score += 1
            checks += 1
            if src.license_compliance == LicenseCompliance.VERIFIED:
                src_score += 1
            checks += 1
            if src.capture_method != CaptureMethod.OTHER:
                src_score += 1
            checks += 1
            if src.collection_date:
                src_score += 1
            checks += 1
            source_scores.append(src_score / checks if checks else 0)
        points += 30 * (sum(source_scores) / len(source_scores))
    else:
        gaps.append("No data sources documented")
        recommendations.append("Document all data sources with metadata")

    # License compliance (20 points)
    max_points += 20
    if card.all_licenses_verified:
        points += 20
    elif card.sources:
        verified = sum(
            1 for s in card.sources
            if s.license_compliance == LicenseCompliance.VERIFIED
        )
        points += 20 * (verified / len(card.sources))
        unverified = [
            s.name for s in card.sources
            if s.license_compliance != LicenseCompliance.VERIFIED
        ]
        if unverified:
            gaps.append(f"Unverified licenses: {', '.join(unverified)}")
            recommendations.append("Verify license compliance for all data sources")

    # Generation flags (15 points)
    max_points += 15
    if card.generation_flag != GenerationFlag.UNKNOWN:
        points += 10
        if card.generation_confidence >= 0.8:
            points += 5
    else:
        gaps.append("Generation origin not classified")
        recommendations.append(
            "Classify content as human-origin, machine-origin, or hybrid "
            "with confidence score"
        )

    # Transformation logging (15 points)
    max_points += 15
    if card.transformations:
        points += 15
    else:
        gaps.append("No transformation history recorded")
        recommendations.append(
            "Log all data transformations (dedup, cleaning, OCR, etc.)"
        )

    # Versioning (10 points)
    max_points += 10
    if card.versions:
        points += 10
    else:
        gaps.append("No dataset versioning")
        recommendations.append(
            "Implement dataset versioning with bi-temporal lineage"
        )

    # Opt-out compliance (10 points)
    max_points += 10
    if not card.has_opt_out_gaps:
        points += 10
    else:
        gaps.append("Opt-out requests not fully honored")
        recommendations.append(
            "Ensure all copyright holder opt-out requests are honored "
            "(EU DSM Directive Article 4)"
        )

    # Model collapse guard
    if guard:
        violations = guard.violations
        for v in violations:
            gaps.append(f"Model collapse: {v}")
            recommendations.append(f"Address: {v}")

    score = (points / max_points * 100) if max_points else 0

    return ProvenanceResult(
        score=score,
        gaps=gaps,
        recommendations=recommendations,
    )
