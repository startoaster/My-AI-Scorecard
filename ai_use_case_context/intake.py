"""
Use case intake — the facts an approval decision rests on.

A capability classification says what an operation does. It does not say
whether doing it here, to this material, for this audience, is acceptable.
That depends on context: what the project is, what went in, what comes out,
and what is actually being asked for.

This module models that context as structured fields rather than prose, for
one reason above all: **escalation triggers are combinations, not severities.**
Studio guidance in practice reads "these inputs, producing this kind of output,
at this final-use potential, using this class of capability, are pre-approved;
anything else escalates." Expressed as fields, that guidance becomes executable
— and two people describing the same proposal produce the same flags.

Compare with the older path through :meth:`UseCaseContext.flag_risk`, where a
person judges severity directly. That still works and is still appropriate when
a reviewer knows something the fields do not capture. But the fields should
come first, because they are checkable and a severity judgment is not.

:class:`ApprovalContext` also carries the decision itself. Approving a proposal
while a finding from an enforceable source is still open is refused — the same
principle that governs clearing an individual flag.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING

from ai_use_case_context.authority import Authority, AuthoritySource
from ai_use_case_context.capability import (
    CapabilityProfile,
    FinalPixelRole,
    LikenessPresence,
    TransformationClass,
)
from ai_use_case_context.core import RiskDimension, RiskLevel

if TYPE_CHECKING:  # pragma: no cover
    from ai_use_case_context.core import RiskFlag, UseCaseContext


# ---------------------------------------------------------------------------
# Business context
# ---------------------------------------------------------------------------

class ProjectVisibility(Enum):
    """Who will see the work this AI use feeds into."""
    INTERNAL_TESTING = "Internal testing"
    INTERNAL_PRODUCTION = "Internal production use"
    PUBLIC = "Public-facing"


class IPClass(Enum):
    """The nature of the media content involved.

    Deliberately unordered. Which of these is most restricted is an
    organization's judgment and varies by production — encoding a severity
    ranking here would assert a hierarchy no source supplies. Use
    :data:`RESTRICTED_IP_CLASSES` to express one, and override it if yours
    differs.
    """
    NO_IP = "No IP"
    RELEASED_IP = "Existing released IP"
    INTERNAL_LIBRARY = "Approved internal library assets"
    PRODUCTION_IP = "Production IP"
    PRE_RELEASE_IP = "Pre-release IP"
    TALENT_MATERIAL = "Talent-related material"
    BRAND_MATERIAL = "Brand-related material"


#: IP classes whose exposure carries consequence beyond the production.
#: Replace with your own set if your classification differs.
RESTRICTED_IP_CLASSES: frozenset = frozenset({
    IPClass.PRODUCTION_IP,
    IPClass.PRE_RELEASE_IP,
    IPClass.TALENT_MATERIAL,
    IPClass.BRAND_MATERIAL,
})


class CommercialNature(Enum):
    """The commercial character of the project or activity."""
    NON_COMMERCIAL = "Non-commercial (demonstration, evaluation)"
    PROMOTIONAL = "Marketing or promotional use"
    COMMERCIAL_RELEASE = "Commercial release"


class UseCaseMaturity(Enum):
    """How settled the proposed use is."""
    LONG_TERM_RESEARCH = "Long-term research"
    SHORT_TERM_RESEARCH = "Short-term research"
    ENGINEERING = "Engineering effort"
    PRODUCTION_READY = "Ready for production use"


class PrimaryUser(Enum):
    """Who will actually operate the capability."""
    SERVICE_VENDOR = "Servicing vendor"
    TECHNOLOGIST = "Technologist within a department"
    CREATIVE_ARTIST = "Creative artist"


@dataclass
class BusinessContext:
    """The organizational and production setting for the proposed use."""
    visibility: ProjectVisibility = ProjectVisibility.INTERNAL_TESTING
    ip_class: IPClass = IPClass.NO_IP
    commercial_nature: CommercialNature = CommercialNature.NON_COMMERCIAL
    maturity: UseCaseMaturity = UseCaseMaturity.SHORT_TERM_RESEARCH
    primary_user: PrimaryUser = PrimaryUser.TECHNOLOGIST
    benefit: str = ""
    department: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "visibility": self.visibility.name,
            "ip_class": self.ip_class.name,
            "commercial_nature": self.commercial_nature.name,
            "maturity": self.maturity.name,
            "primary_user": self.primary_user.name,
            "benefit": self.benefit,
            "department": self.department,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BusinessContext":
        return cls(
            visibility=ProjectVisibility[data["visibility"]],
            ip_class=IPClass[data["ip_class"]],
            commercial_nature=CommercialNature[data["commercial_nature"]],
            maturity=UseCaseMaturity[data["maturity"]],
            primary_user=PrimaryUser[data["primary_user"]],
            benefit=data.get("benefit", ""),
            department=data.get("department", ""),
        )


# ---------------------------------------------------------------------------
# Approval context
# ---------------------------------------------------------------------------

class ApprovalSubject(Enum):
    """What is actually being put forward for approval.

    When the subject is a fine-tuning workflow, every other field in the
    profile describes conditions *after* fine-tuning — the inputs the tuned
    model will see and the outputs it will produce, not the tuning corpus.
    """
    TOOL = "AI tool"
    MODEL = "AI model"
    WORKFLOW = "AI workflow"
    FINE_TUNING_WORKFLOW = "AI fine-tuning workflow"


class ApprovalDecision(Enum):
    """The outcome of a review.

    Distinct from per-flag :class:`~ai_use_case_context.core.ReviewStatus`,
    which tracks one finding. This tracks the proposal.
    """
    PENDING = "Pending"
    APPROVED = "Approved"
    APPROVED_WITH_CONSTRAINTS = "Approved with constraints"
    APPROVED_FOR_INTERNAL_TESTING = "Approved for internal testing only"
    REJECTED = "Rejected"

    @property
    def is_approval(self) -> bool:
        return self in (
            ApprovalDecision.APPROVED,
            ApprovalDecision.APPROVED_WITH_CONSTRAINTS,
            ApprovalDecision.APPROVED_FOR_INTERNAL_TESTING,
        )


class ApprovalError(RuntimeError):
    """Raised when a proposal is approved with enforceable findings open."""


@dataclass
class ApprovalContext:
    """What is being requested, and what was decided."""
    subject: ApprovalSubject = ApprovalSubject.WORKFLOW
    proposed_use: str = ""
    tools_in_scope: list[str] = field(default_factory=list)
    capabilities_in_scope: list[str] = field(default_factory=list)
    required_reviews: list[str] = field(default_factory=list)
    decision: ApprovalDecision = ApprovalDecision.PENDING
    decision_notes: str = ""
    decided_by: str = ""
    decided_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject.name,
            "proposed_use": self.proposed_use,
            "tools_in_scope": list(self.tools_in_scope),
            "capabilities_in_scope": list(self.capabilities_in_scope),
            "required_reviews": list(self.required_reviews),
            "decision": self.decision.name,
            "decision_notes": self.decision_notes,
            "decided_by": self.decided_by,
            "decided_at": (
                self.decided_at.isoformat() if self.decided_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApprovalContext":
        return cls(
            subject=ApprovalSubject[data["subject"]],
            proposed_use=data.get("proposed_use", ""),
            tools_in_scope=list(data.get("tools_in_scope", [])),
            capabilities_in_scope=list(data.get("capabilities_in_scope", [])),
            required_reviews=list(data.get("required_reviews", [])),
            decision=ApprovalDecision[data.get("decision", "PENDING")],
            decision_notes=data.get("decision_notes", ""),
            decided_by=data.get("decided_by", ""),
            decided_at=(
                datetime.fromisoformat(data["decided_at"])
                if data.get("decided_at") else None
            ),
        )


# ---------------------------------------------------------------------------
# Inputs and outputs
# ---------------------------------------------------------------------------

class InputType(Enum):
    """Kinds of material entering the workflow."""
    PERSONAL_DATA = "Personally identifiable information"
    LICENSED_MUSIC = "Licensed music"
    PERFORMER_LIKENESS = "Performer likeness"
    BRAND_PRESENCE = "Brand presence"
    CONTRACTED_ASSETS = "Contracted assets"
    SCRIPT = "Script or written material"
    STORYBOARD = "Storyboard"
    VIDEO = "Video"
    AUDIO = "Audio"
    METADATA = "Metadata"
    EMBEDDINGS = "Embeddings"
    POINT_CLOUD = "Point cloud data"


class OutputRole(Enum):
    """What the produced output is for."""
    NON_MEDIA_ASSET = "Non-media asset (report, breakdown, tags)"
    WORKING_MEDIA_ASSET = "Working or WIP media asset"
    FINISHED_MEDIA_ASSET = "Finished media asset"


class BrandPresence(Enum):
    """How a brand appears in the output, where relevant."""
    NONE = "None"
    ORIGINAL_IN_NEW_CONTEXT = "Original brand in a new context"
    DEPICTED_ALTERED = "Brand depicted altered or damaged"


@dataclass
class InputProfile:
    """What material the capability consumes."""
    ip_class: IPClass = IPClass.NO_IP
    input_types: list[InputType] = field(default_factory=list)
    notes: str = ""

    @property
    def is_restricted(self) -> bool:
        return self.ip_class in RESTRICTED_IP_CLASSES

    def to_dict(self) -> dict[str, Any]:
        return {
            "ip_class": self.ip_class.name,
            "input_types": [t.name for t in self.input_types],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InputProfile":
        return cls(
            ip_class=IPClass[data["ip_class"]],
            input_types=[InputType[t] for t in data.get("input_types", [])],
            notes=data.get("notes", ""),
        )


@dataclass
class OutputProfile:
    """What the capability produces and where it goes.

    ``final_pixel`` and ``likeness`` reuse the capability enums rather than
    redefining them, so a profile and a classification always agree on terms.
    """
    output_types: list[str] = field(default_factory=list)
    role: OutputRole = OutputRole.NON_MEDIA_ASSET
    final_pixel: FinalPixelRole = FinalPixelRole.NONE
    likeness: LikenessPresence = LikenessPresence.NONE
    brand: BrandPresence = BrandPresence.NONE
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_types": list(self.output_types),
            "role": self.role.name,
            "final_pixel": self.final_pixel.name,
            "likeness": self.likeness.name,
            "brand": self.brand.name,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OutputProfile":
        return cls(
            output_types=list(data.get("output_types", [])),
            role=OutputRole[data["role"]],
            final_pixel=FinalPixelRole[data["final_pixel"]],
            likeness=LikenessPresence[data.get("likeness", "NONE")],
            brand=BrandPresence[data.get("brand", "NONE")],
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Combination rules
# ---------------------------------------------------------------------------

@dataclass
class IntakeRule:
    """A rule keyed on a combination of intake fields.

    ``applies`` receives the whole profile and the capability classification
    (which may be ``None`` when a proposal has not been classified yet), so a
    rule can depend on any combination of the two.
    """
    rule_id: str
    title: str
    applies: Callable[["UseCaseProfile", Optional[CapabilityProfile]], bool]
    dimension: Any
    level: RiskLevel
    describe: Callable[["UseCaseProfile", Optional[CapabilityProfile]], str]
    authority: Authority = Authority.UNSPECIFIED
    source: Optional[AuthoritySource] = None


_LICENSE_TERMS = AuthoritySource(
    body="Content licence terms",
    authority=Authority.BINDING_CONTRACT,
    citation="Applicable licence to be confirmed for this material",
)

_PERFORMER_AGREEMENT = AuthoritySource(
    body="Performer collective bargaining agreement",
    authority=Authority.BINDING_CONTRACT,
    citation="Applicable agreement to be confirmed for this production",
)

_PRIVACY_LAW = AuthoritySource(
    body="Data protection law",
    authority=Authority.STATUTE,
    citation="Applicable regime depends on data subjects and processing location",
)


def _max_transformation(
    capability: Optional[CapabilityProfile],
) -> Optional[TransformationClass]:
    if capability is None or not capability.regions:
        return None
    return capability.max_transformation()


DEFAULT_INTAKE_RULES: list[IntakeRule] = [
    IntakeRule(
        rule_id="RESTRICTED_INPUT_TO_PUBLIC_OUTPUT",
        title="Restricted material feeding public-facing output",
        applies=lambda p, c: (
            p.inputs.is_restricted
            and p.outputs.final_pixel.reaches_audience
            and p.business.visibility is ProjectVisibility.PUBLIC
        ),
        dimension=RiskDimension.SECURITY,
        level=RiskLevel.HIGH,
        describe=lambda p, c: (
            f"{p.inputs.ip_class.value} enters a workflow whose output reaches "
            f"a public-facing work. Confirm handling and disclosure conditions "
            f"before proceeding."
        ),
    ),
    IntakeRule(
        rule_id="PERSONAL_DATA_IN_INPUTS",
        title="Personal data entering the workflow",
        applies=lambda p, c: InputType.PERSONAL_DATA in p.inputs.input_types,
        dimension=RiskDimension.SECURITY,
        level=RiskLevel.HIGH,
        authority=Authority.STATUTE,
        source=_PRIVACY_LAW,
        describe=lambda p, c: (
            "Personally identifiable information is supplied as input. Lawful "
            "basis, retention, and cross-border transfer conditions require "
            "review; which regime applies is not determined here."
        ),
    ),
    IntakeRule(
        rule_id="PERFORMER_LIKENESS_INPUT",
        title="Performer likeness supplied as input",
        applies=lambda p, c: InputType.PERFORMER_LIKENESS in p.inputs.input_types,
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        authority=Authority.BINDING_CONTRACT,
        source=_PERFORMER_AGREEMENT,
        describe=lambda p, c: (
            "Performer likeness is supplied as input. Consent scope and "
            "compensation terms require confirmation against the applicable "
            "agreement before this material is used."
        ),
    ),
    IntakeRule(
        rule_id="LICENSED_MUSIC_INTO_NEW_MEDIA",
        title="Licensed music feeding generated output",
        applies=lambda p, c: (
            InputType.LICENSED_MUSIC in p.inputs.input_types
            and (_max_transformation(c) or TransformationClass.EXTRACTION)
            .introduces_new_content
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        authority=Authority.BINDING_CONTRACT,
        source=_LICENSE_TERMS,
        describe=lambda p, c: (
            "Licensed music is supplied to a capability that introduces new "
            "content. Whether the licence permits derivative or generated "
            "output requires confirmation."
        ),
    ),
    IntakeRule(
        rule_id="COMMERCIAL_RELEASE_OF_GENERATED_MEDIA",
        title="Generated media in a commercial release",
        applies=lambda p, c: (
            p.business.commercial_nature is CommercialNature.COMMERCIAL_RELEASE
            and p.outputs.final_pixel is FinalPixelRole.DELIVERED_FRAME
            and (_max_transformation(c) or TransformationClass.EXTRACTION)
            is TransformationClass.SYNTHESIS
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        describe=lambda p, c: (
            "Synthesized media is delivered in a commercial release. "
            "Copyrightability, disclosure, and downstream licensing all turn "
            "on facts outside this framework."
        ),
    ),
    IntakeRule(
        rule_id="FINE_TUNING_ON_RESTRICTED_MATERIAL",
        title="Fine-tuning proposed over restricted material",
        applies=lambda p, c: (
            p.approval.subject is ApprovalSubject.FINE_TUNING_WORKFLOW
            and p.inputs.is_restricted
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.CRITICAL,
        authority=Authority.BINDING_CONTRACT,
        source=_LICENSE_TERMS,
        describe=lambda p, c: (
            f"Fine-tuning is proposed over: {p.inputs.ip_class.value}. "
            f"Training rights are frequently reserved separately from use "
            f"rights, and notification obligations may attach."
        ),
    ),
    IntakeRule(
        rule_id="BRAND_DEPICTED_ALTERED",
        title="Brand depicted altered or damaged",
        applies=lambda p, c: (
            p.outputs.brand is BrandPresence.DEPICTED_ALTERED
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.MEDIUM,
        describe=lambda p, c: (
            "Output depicts a brand altered or damaged. Clearance conditions "
            "for the depiction require review."
        ),
    ),
    IntakeRule(
        rule_id="UNPROVEN_USE_IN_PUBLIC_WORK",
        title="Research-stage capability proposed for public-facing work",
        applies=lambda p, c: (
            p.business.visibility is ProjectVisibility.PUBLIC
            and p.business.maturity in (
                UseCaseMaturity.LONG_TERM_RESEARCH,
                UseCaseMaturity.SHORT_TERM_RESEARCH,
            )
        ),
        dimension=RiskDimension.FEASIBILITY,
        level=RiskLevel.MEDIUM,
        describe=lambda p, c: (
            f"A capability at {p.business.maturity.value.lower()} maturity is "
            f"proposed for public-facing work. Confirm the pipeline has been "
            f"validated at production conditions."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Use case profile
# ---------------------------------------------------------------------------

@dataclass
class UseCaseProfile:
    """The full intake record for a proposed AI use."""
    business: BusinessContext = field(default_factory=BusinessContext)
    approval: ApprovalContext = field(default_factory=ApprovalContext)
    inputs: InputProfile = field(default_factory=InputProfile)
    outputs: OutputProfile = field(default_factory=OutputProfile)

    # -- Derivation --------------------------------------------------------

    def derive_flags(
        self,
        ctx: "UseCaseContext",
        capability: Optional[CapabilityProfile] = None,
        rules: Optional[list[IntakeRule]] = None,
    ) -> list["RiskFlag"]:
        """Raise flags for every rule matching this profile.

        Pass ``capability`` when the proposal has been classified — several
        rules key on the combination of intake facts and what the capability
        actually does, which is the pairing that carries the most signal.
        """
        active = DEFAULT_INTAKE_RULES if rules is None else rules
        added: list["RiskFlag"] = []
        for rule in active:
            if not rule.applies(self, capability):
                continue
            added.append(
                ctx.flag_risk(
                    dimension=rule.dimension,
                    level=rule.level,
                    description=rule.describe(self, capability),
                    authority=rule.authority,
                    source=rule.source,
                )
            )
        return added

    # -- Decision ----------------------------------------------------------

    def record_decision(
        self,
        ctx: "UseCaseContext",
        decision: ApprovalDecision,
        decided_by: str = "",
        notes: str = "",
    ) -> ApprovalDecision:
        """Record the outcome of a review.

        Approving while a finding from an enforceable source is still open is
        refused. Rejecting, or returning the proposal to pending, is always
        allowed — those never need a clearance the framework can check.

        Raises:
            ApprovalError: If approving with unresolved enforceable findings,
                or approving without naming who decided.
        """
        if decision.is_approval:
            if not decided_by:
                raise ApprovalError(
                    "An approval must name who decided."
                )
            open_enforceable = ctx.get_enforceable_flags()
            if open_enforceable:
                summary = ", ".join(
                    f.authority.label for f in open_enforceable
                )
                raise ApprovalError(
                    f"Cannot record '{decision.value}' while "
                    f"{len(open_enforceable)} finding(s) from an enforceable "
                    f"source remain open ({summary}). Resolve or clear them "
                    f"first."
                )
        self.approval.decision = decision
        self.approval.decided_by = decided_by
        self.approval.decision_notes = notes
        self.approval.decided_at = datetime.now()
        return decision

    # -- Serialization -----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "business": self.business.to_dict(),
            "approval": self.approval.to_dict(),
            "inputs": self.inputs.to_dict(),
            "outputs": self.outputs.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UseCaseProfile":
        return cls(
            business=BusinessContext.from_dict(data["business"]),
            approval=ApprovalContext.from_dict(data["approval"]),
            inputs=InputProfile.from_dict(data["inputs"]),
            outputs=OutputProfile.from_dict(data["outputs"]),
        )

    def summary(self) -> str:
        lines = [
            f"Subject:     {self.approval.subject.value}",
            f"Proposed:    {self.approval.proposed_use or '(not stated)'}",
            f"Visibility:  {self.business.visibility.value}",
            f"IP class:    {self.business.ip_class.value}",
            f"Commercial:  {self.business.commercial_nature.value}",
            f"Maturity:    {self.business.maturity.value}",
            f"Inputs:      {self.inputs.ip_class.value}"
            + (
                " — " + ", ".join(t.value for t in self.inputs.input_types)
                if self.inputs.input_types else ""
            ),
            f"Outputs:     {self.outputs.role.value}, "
            f"{self.outputs.final_pixel.label}",
            f"Decision:    {self.approval.decision.value}"
            + (f" by {self.approval.decided_by}" if self.approval.decided_by else ""),
        ]
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()
