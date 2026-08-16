"""
Core governance classes for the AI Use Case Context Framework.

Contains the enums, data classes, routing table, and main UseCaseContext class
that implement the flag / route / block governance model.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Union

from ai_use_case_context.authority import (
    Authority,
    AuthoritySource,
    suggested_clearance_role,
)
from ai_use_case_context.governance_hooks import (
    GovernanceEvent,
    GovernanceEventType,
    emit_governance_event,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RiskDimension(Enum):
    """The six built-in governance dimensions."""
    LEGAL_IP = "Legal / IP Ownership"
    BIAS = "Bias / Fairness"
    SAFETY = "Safety / Harmful Output"
    SECURITY = "Security / Model Integrity"
    FEASIBILITY = "Technical Feasibility"
    QUALITY = "Output Quality"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RiskDimension):
            return self is other
        if isinstance(other, Dimension):
            return self.name == other.name
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)


# ---------------------------------------------------------------------------
# Custom dimensions
# ---------------------------------------------------------------------------

class Dimension:
    """A user-defined risk dimension.

    Works interchangeably with built-in ``RiskDimension`` enum members
    everywhere in the framework — routing tables, dashboards, serialization,
    and the web UI all discover and render custom dimensions automatically.

    Use the ``custom_dimension()`` factory for convenience::

        FINANCIAL = custom_dimension("FINANCIAL", "Financial Risk")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget overrun likely")

    Attributes:
        name:  Short identifier (e.g. ``"FINANCIAL"``).  Must be unique.
        value: Human-readable label (e.g. ``"Financial Risk"``).
    """

    __slots__ = ("name", "value")

    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Dimension):
            return self.name == other.name
        if isinstance(other, RiskDimension):
            return self.name == other.name
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"Dimension({self.name!r}, {self.value!r})"

    def __str__(self) -> str:
        return self.value


def custom_dimension(name: str, label: str) -> Dimension:
    """Create a custom risk dimension.

    Example::

        FINANCIAL = custom_dimension("FINANCIAL", "Financial Risk")
        REGULATORY = custom_dimension("REGULATORY", "Regulatory Compliance")

        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget overrun")
    """
    return Dimension(name, label)


# Type accepted everywhere a dimension is needed.
DimensionType = Union[RiskDimension, Dimension]


class RiskLevel(Enum):
    """
    How severe the risk is. Determines routing and blocking behavior.
      NONE      - No concerns identified.
      LOW       - Informational flag; no review needed.
      MEDIUM    - Requires review before proceeding.
      HIGH      - Blocks the workflow until resolved.
      CRITICAL  - Escalates to senior leadership; hard block.
    """
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ReviewStatus(Enum):
    """Tracks where a flagged risk is in the review process."""
    OPEN = "Open"
    IN_REVIEW = "In Review"
    RESOLVED = "Resolved"
    ACCEPTED = "Accepted (Risk Acknowledged)"
    BLOCKED = "Blocked"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RiskFlag:
    """A single risk flag attached to a use case.

    ``authority`` records how much force the source behind this flag carries.
    It defaults to ``UNSPECIFIED``, which behaves exactly as flags did before
    authority existed.

    State transitions record what happened and emit a governance event. They
    do not refuse. Whether a given person may accept a given finding is a
    question about an organization's delegation of authority and its identity
    systems, and this framework has no way to answer it — a check here would
    be trivially bypassed and would buy false assurance. Organizations that
    want that enforced should express it in a
    :class:`~ai_use_case_context.governance_hooks.GovernanceHook`, where it
    sits in their control rather than in a library default.
    """
    dimension: DimensionType
    level: RiskLevel
    description: str
    reviewer: str = ""
    status: ReviewStatus = ReviewStatus.OPEN
    resolution_notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    authority: Authority = Authority.UNSPECIFIED
    source: Optional[AuthoritySource] = None
    cleared_by: str = ""
    use_case_name: str = ""

    def _emit(self, event_type: GovernanceEventType, actor: str) -> None:
        """Emit a lifecycle event for this flag.

        Emitted from the flag itself rather than from any one caller, so hooks
        fire the same way whether a change came from the web dashboard, a
        derivation rule, or a script.
        """
        emit_governance_event(GovernanceEvent(
            event_type=event_type,
            use_case_name=self.use_case_name,
            dimension=self.dimension.name,
            level=self.level.name,
            description=self.description,
            actor=actor or "system",
            metadata={
                "authority": self.authority.name,
                "source": self.source.to_dict() if self.source else None,
                "reviewer": self.reviewer,
                "cleared_by": self.cleared_by,
                "status": self.status.name,
            },
        ))

    @property
    def is_blocking(self) -> bool:
        """A flag blocks the workflow if it's HIGH or CRITICAL and not yet resolved."""
        return (
            self.level.value >= RiskLevel.HIGH.value
            and self.status not in (ReviewStatus.RESOLVED, ReviewStatus.ACCEPTED)
        )

    @property
    def needs_review(self) -> bool:
        """A flag needs review if it's MEDIUM or above and still open."""
        return (
            self.level.value >= RiskLevel.MEDIUM.value
            and self.status == ReviewStatus.OPEN
        )

    def resolve(self, notes: str = "", actor: str = "system"):
        """Mark this flag as resolved."""
        self.status = ReviewStatus.RESOLVED
        self.resolution_notes = notes
        self.resolved_at = datetime.now()
        self._emit(GovernanceEventType.FLAG_RESOLVED, actor)

    @property
    def is_from_enforceable_source(self) -> bool:
        """True if the source behind this flag is a statute or binding term.

        A statement about the finding, not a rule about who may act on it.
        """
        return self.authority.is_enforceable

    @property
    def is_attributed(self) -> bool:
        """True if an accepted flag names who accepted it.

        Meaningful only once accepted; open flags are trivially unattributed.
        """
        return bool(self.cleared_by)

    def accept_risk(
        self, notes: str = "", cleared_by: str = "", actor: str = "system"
    ):
        """Acknowledge the risk and allow the workflow to proceed.

        Records the acceptance and who made it. Naming ``cleared_by`` is
        strongly advisable for a finding from an enforceable source — see
        :meth:`UseCaseContext.get_unattributed_acceptances` — but it is not
        required, because this framework cannot verify standing and refusing
        would only push callers into setting ``status`` directly.

        Args:
            notes:      Rationale for accepting.
            cleared_by: Who accepted it.
            actor:      What performed the change, for the emitted event.
        """
        self.status = ReviewStatus.ACCEPTED
        self.resolution_notes = notes
        self.cleared_by = cleared_by
        self.resolved_at = datetime.now()
        self._emit(GovernanceEventType.FLAG_ACCEPTED, actor)

    def begin_review(self, actor: str = "system"):
        """Move this flag into the In Review state."""
        self.status = ReviewStatus.IN_REVIEW
        self._emit(GovernanceEventType.REVIEW_STARTED, actor)

    def mark_blocked(self):
        """Hard-block this flag, indicating a structural issue."""
        self.status = ReviewStatus.BLOCKED

    def __str__(self):
        icon = {
            RiskLevel.NONE: "✅",
            RiskLevel.LOW: "🔵",
            RiskLevel.MEDIUM: "🟡",
            RiskLevel.HIGH: "🟠",
            RiskLevel.CRITICAL: "🔴",
        }.get(self.level, "⚪")
        base = (
            f"{icon} [{self.dimension.value}] {self.level.name}: "
            f"{self.description} ({self.status.value})"
        )
        if self.authority is not Authority.UNSPECIFIED:
            src = f" — {self.source}" if self.source else ""
            base += f" ⟨{self.authority.label}{src}⟩"
        return base


# ---------------------------------------------------------------------------
# Routing rules
# ---------------------------------------------------------------------------

# Default routing table: dimension + level -> suggested reviewer role.
# Override by passing a custom routing_table to UseCaseContext.
DEFAULT_ROUTING: dict[tuple[RiskDimension, RiskLevel], str] = {
    (RiskDimension.LEGAL_IP, RiskLevel.LOW): "IP Coordinator",
    (RiskDimension.LEGAL_IP, RiskLevel.MEDIUM): "Legal Counsel",
    (RiskDimension.LEGAL_IP, RiskLevel.HIGH): "VP Legal / Business Affairs",
    (RiskDimension.LEGAL_IP, RiskLevel.CRITICAL): "General Counsel + C-Suite",

    (RiskDimension.BIAS, RiskLevel.LOW): "Fairness Analyst",
    (RiskDimension.BIAS, RiskLevel.MEDIUM): "Bias Review Board",
    (RiskDimension.BIAS, RiskLevel.HIGH): "VP Ethics / Policy",
    (RiskDimension.BIAS, RiskLevel.CRITICAL): "C-Suite + External Fairness Auditor",

    (RiskDimension.SAFETY, RiskLevel.LOW): "Safety Analyst",
    (RiskDimension.SAFETY, RiskLevel.MEDIUM): "Safety Review Board",
    (RiskDimension.SAFETY, RiskLevel.HIGH): "VP Safety / Policy",
    (RiskDimension.SAFETY, RiskLevel.CRITICAL): "C-Suite + External Safety Advisor",

    (RiskDimension.SECURITY, RiskLevel.LOW): "Security Analyst",
    (RiskDimension.SECURITY, RiskLevel.MEDIUM): "Security Engineer",
    (RiskDimension.SECURITY, RiskLevel.HIGH): "CISO / VP Security",
    (RiskDimension.SECURITY, RiskLevel.CRITICAL): "CISO + External Security Audit",

    (RiskDimension.FEASIBILITY, RiskLevel.LOW): "Tech Lead",
    (RiskDimension.FEASIBILITY, RiskLevel.MEDIUM): "VFX Supervisor",
    (RiskDimension.FEASIBILITY, RiskLevel.HIGH): "VP Technology / CTO",
    (RiskDimension.FEASIBILITY, RiskLevel.CRITICAL): "CTO + External Technical Review",

    (RiskDimension.QUALITY, RiskLevel.LOW): "QA Lead",
    (RiskDimension.QUALITY, RiskLevel.MEDIUM): "Department Supervisor",
    (RiskDimension.QUALITY, RiskLevel.HIGH): "VP Production / Post",
    (RiskDimension.QUALITY, RiskLevel.CRITICAL): "Executive Producer + Department Head",
}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class UseCaseContext:
    """
    Governance wrapper for an AI production use case.

    Carries metadata about which risks have been identified, who needs to
    review them, and whether the workflow is blocked from proceeding.

    Attributes:
        name:             Short name for the use case.
        description:      What the AI is being used for.
        workflow_phase:    Which phase of the production pipeline this falls in.
        tags:             Freeform tags for taxonomy/categorization.
        risk_flags:       List of RiskFlag objects.
        routing_table:    Mapping of (dimension, level) -> reviewer role.
                          Omit it to use :data:`DEFAULT_ROUTING`; pass an empty
                          mapping to disable automatic assignment entirely.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        workflow_phase: str = "",
        tags: Optional[list[str]] = None,
        routing_table: Optional[dict[tuple[DimensionType, RiskLevel], str]] = None,
    ):
        self.name = name
        self.description = description
        self.workflow_phase = workflow_phase
        self.tags = list(tags) if tags is not None else []
        self.risk_flags: list[RiskFlag] = []
        # `is None`, not a falsy check: an empty routing table is a valid
        # configuration meaning "assign nothing automatically", and is not the
        # same instruction as "use the defaults".
        self.routing_table = (
            dict(routing_table) if routing_table is not None
            else dict(DEFAULT_ROUTING)
        )
        self.created_at = datetime.now()

    # -- Flagging ----------------------------------------------------------

    def flag_risk(
        self,
        dimension: DimensionType,
        level: RiskLevel,
        description: str,
        reviewer: str = "",
        authority: Authority = Authority.UNSPECIFIED,
        source: Optional[AuthoritySource] = None,
        actor: str = "system",
    ) -> RiskFlag:
        """
        Flag a risk on this use case.

        If no reviewer is provided, one is assigned from this context's
        routing table. The organization's table always wins; the authority's
        suggested clearance role is used only where the table has no entry,
        in place of leaving the flag unassigned.

        Returns the created RiskFlag so you can further manipulate it.
        """
        if not reviewer:
            reviewer = self.routing_table.get((dimension, level), "")
        if not reviewer and authority.is_enforceable:
            reviewer = suggested_clearance_role(authority)
        if not reviewer:
            reviewer = "Unassigned"

        flag = RiskFlag(
            dimension=dimension,
            level=level,
            description=description,
            reviewer=reviewer,
            authority=authority,
            source=source,
            use_case_name=self.name,
        )
        self.risk_flags.append(flag)
        flag._emit(GovernanceEventType.FLAG_RAISED, actor)
        return flag

    # -- Routing -----------------------------------------------------------

    def get_pending_reviews(self) -> list[RiskFlag]:
        """Return all flags that still need review."""
        return [f for f in self.risk_flags if f.needs_review]

    def get_reviewers_needed(self) -> list[str]:
        """Return a deduplicated list of reviewers who need to act."""
        return list({
            f.reviewer
            for f in self.risk_flags
            if f.needs_review or f.is_blocking
        })

    # -- Blocking ----------------------------------------------------------

    def is_blocked(self) -> bool:
        """True if any unresolved HIGH or CRITICAL flag exists."""
        return any(f.is_blocking for f in self.risk_flags)

    def get_blockers(self) -> list[RiskFlag]:
        """Return the specific flags that are blocking the workflow."""
        return [f for f in self.risk_flags if f.is_blocking]

    # -- Scoring -----------------------------------------------------------

    def dimensions(self) -> list[DimensionType]:
        """Return all dimensions present in flags, plus all built-in ones."""
        seen: dict[str, DimensionType] = {}
        for flag in self.risk_flags:
            seen.setdefault(flag.dimension.name, flag.dimension)
        for dim in RiskDimension:
            seen.setdefault(dim.name, dim)
        return list(seen.values())

    def risk_score(self) -> dict[str, int]:
        """
        Return a simple risk score per dimension (max unresolved level).
        Includes all built-in dimensions plus any custom ones with flags.
        Useful for dashboards and summary views.
        """
        scores: dict[str, int] = {}
        for dim in self.dimensions():
            dim_flags = [
                f for f in self.risk_flags
                if f.dimension == dim
                and f.status not in (ReviewStatus.RESOLVED, ReviewStatus.ACCEPTED)
            ]
            scores[dim.value] = max(
                (f.level.value for f in dim_flags), default=0
            )
        return scores

    # -- Querying ----------------------------------------------------------

    def get_flags_by_dimension(self, dimension: DimensionType) -> list[RiskFlag]:
        """Return all flags for a specific dimension."""
        return [f for f in self.risk_flags if f.dimension == dimension]

    def get_flags_by_status(self, status: ReviewStatus) -> list[RiskFlag]:
        """Return all flags with a specific review status."""
        return [f for f in self.risk_flags if f.status == status]

    def get_flags_by_level(self, level: RiskLevel) -> list[RiskFlag]:
        """Return all flags at a specific risk level."""
        return [f for f in self.risk_flags if f.level == level]

    def get_enforceable_flags(self) -> list[RiskFlag]:
        """Return unresolved flags backed by a binding agreement or statute.

        Worth surfacing separately from severity: a low-severity contract
        question and a low-severity preference are not the same thing.
        """
        return [
            f for f in self.risk_flags
            if f.is_from_enforceable_source
            and f.status not in (ReviewStatus.RESOLVED, ReviewStatus.ACCEPTED)
        ]

    def get_unattributed_acceptances(self) -> list[RiskFlag]:
        """Return accepted enforceable findings with nobody named.

        The framework records acceptances rather than policing them, so this
        is how an audit, a hook, or a reviewer finds the ones where standing
        was never recorded. An empty list is not proof that the people who
        accepted had authority to — only that somebody was named.
        """
        return [
            f for f in self.risk_flags
            if f.is_from_enforceable_source
            and f.status is ReviewStatus.ACCEPTED
            and not f.is_attributed
        ]

    def max_authority(self) -> Authority:
        """Return the highest authority across unresolved flags."""
        unresolved = [
            f for f in self.risk_flags
            if f.status not in (ReviewStatus.RESOLVED, ReviewStatus.ACCEPTED)
        ]
        return max(
            (f.authority for f in unresolved),
            key=lambda a: a.value,
            default=Authority.UNSPECIFIED,
        )

    def max_risk_level(self) -> RiskLevel:
        """Return the highest unresolved risk level across all dimensions."""
        unresolved = [
            f for f in self.risk_flags
            if f.status not in (ReviewStatus.RESOLVED, ReviewStatus.ACCEPTED)
        ]
        if not unresolved:
            return RiskLevel.NONE
        return max(unresolved, key=lambda f: f.level.value).level

    # -- Summary -----------------------------------------------------------

    def summary(self) -> str:
        """Human-readable summary of this use case's governance status."""
        lines = [
            f"Use Case: {self.name}",
            f"Phase:    {self.workflow_phase or '(not set)'}",
            f"Status:   {'🚫 BLOCKED' if self.is_blocked() else '✅ CLEAR'}",
            f"Flags:    {len(self.risk_flags)} total, "
            f"{len(self.get_blockers())} blocking, "
            f"{len(self.get_pending_reviews())} pending review",
            "",
        ]

        if self.risk_flags:
            lines.append("Risk Flags:")
            for flag in self.risk_flags:
                lines.append(f"  {flag}")
                if flag.reviewer:
                    lines.append(f"    → Routed to: {flag.reviewer}")

        reviewers = self.get_reviewers_needed()
        if reviewers:
            lines.append("")
            lines.append("Action needed from: " + ", ".join(reviewers))

        return "\n".join(lines)

    def __str__(self):
        return self.summary()

    def __repr__(self):
        return (
            f"UseCaseContext(name={self.name!r}, "
            f"flags={len(self.risk_flags)}, "
            f"blocked={self.is_blocked()})"
        )
