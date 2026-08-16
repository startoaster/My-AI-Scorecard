"""
Human authorship evidence records.

No industry body or settled authority supplies a threshold for how much human
contribution is enough to sustain copyright in a work incorporating AI output.
The question is live in case law and undefined by every published vocabulary.

So this module does not answer it. It produces the *record* that whoever does
answer it — counsel, a registry, a court — would need: for each region of a
work, what a human actually contributed, how tightly the operation was
constrained, and what review followed.

The distinction matters. A tool that scored authorship would be asserting a
threshold nobody has set, and the score would be worth nothing at the moment it
was tested. A tool that records contribution produces evidence that stays
useful however the threshold eventually lands.

:meth:`AuthorshipRecord.thin_evidence_regions` therefore reports where the
record is *thin* — where a reviewer will find little to point at — without
claiming that thin means insufficient.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from ai_use_case_context.capability import (
    CapabilityProfile,
    ControlMode,
    RegionProfile,
    TransformationClass,
)


@dataclass
class AuthorshipEvidence:
    """What a human contributed to one region of a work.

    Attributes:
        region:              Region identifier, matching the capability profile.
        contributions:       Specific human acts — selecting and framing source
                             material, authoring conditioning inputs, directing
                             iterations, hand-correcting output. Be concrete;
                             "supervised the process" is not evidence.
        iterations:          How many times a human reviewed and redirected the
                             output for this region.
        human_reviewed:      Whether a human evaluated the result before it was
                             accepted.
        human_modified:      Whether a human altered the output after
                             generation.
        control:             Recorded control mode for the region.
        transformation:      Recorded transformation class for the region.
        guidance_strength:   Recorded [0.0, 1.0] constraint value, if any.
        notes:               Anything else a reviewer would want.
    """
    region: str
    contributions: list[str] = field(default_factory=list)
    iterations: int = 0
    human_reviewed: bool = False
    human_modified: bool = False
    control: Optional[ControlMode] = None
    transformation: Optional[TransformationClass] = None
    guidance_strength: Optional[float] = None
    notes: str = ""

    @property
    def introduces_new_content(self) -> bool:
        """True if this region's operation added material to the work.

        Regions that introduce nothing new raise no authorship question at all
        — there is no AI-generated element to attribute.
        """
        return (
            self.transformation is not None
            and self.transformation.introduces_new_content
        )

    @property
    def evidence_points(self) -> int:
        """A count of distinct recorded human contributions for this region.

        A count, deliberately — not a score. It tells a reviewer how much
        there is to look at, and nothing about whether it is enough.
        """
        points = len(self.contributions)
        if self.iterations > 0:
            points += 1
        if self.human_reviewed:
            points += 1
        if self.human_modified:
            points += 1
        if self.control is not None and self.control.is_substantially_human_directed:
            points += 1
        return points

    def to_dict(self) -> dict[str, Any]:
        return {
            "region": self.region,
            "contributions": list(self.contributions),
            "iterations": self.iterations,
            "human_reviewed": self.human_reviewed,
            "human_modified": self.human_modified,
            "control": self.control.name if self.control else None,
            "transformation": (
                self.transformation.name if self.transformation else None
            ),
            "guidance_strength": self.guidance_strength,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthorshipEvidence":
        return cls(
            region=data["region"],
            contributions=list(data.get("contributions", [])),
            iterations=data.get("iterations", 0),
            human_reviewed=data.get("human_reviewed", False),
            human_modified=data.get("human_modified", False),
            control=(
                ControlMode[data["control"]] if data.get("control") else None
            ),
            transformation=(
                TransformationClass[data["transformation"]]
                if data.get("transformation") else None
            ),
            guidance_strength=data.get("guidance_strength"),
            notes=data.get("notes", ""),
        )


@dataclass
class AuthorshipRecord:
    """The assembled evidence of human contribution to a work.

    This is a record for a human to evaluate, not a determination. Nothing here
    concludes that authorship is or is not sufficient, because no source
    supplies the threshold that would make such a conclusion meaningful.
    """
    work: str
    description: str = ""
    evidence: list[AuthorshipEvidence] = field(default_factory=list)
    compiled_at: datetime = field(default_factory=datetime.now)
    compiled_by: str = ""

    def add_evidence(self, evidence: AuthorshipEvidence) -> AuthorshipEvidence:
        self.evidence.append(evidence)
        return evidence

    # -- Queries -----------------------------------------------------------

    def generative_regions(self) -> list[AuthorshipEvidence]:
        """Regions where AI introduced new content — the ones in question."""
        return [e for e in self.evidence if e.introduces_new_content]

    def thin_evidence_regions(
        self, minimum_points: int = 2
    ) -> list[AuthorshipEvidence]:
        """Generative regions with little recorded human contribution.

        ``minimum_points`` is a reporting cut-off for what to draw attention
        to, not a sufficiency threshold. Raising it surfaces more regions for
        review; it does not make any of them non-compliant.
        """
        return [
            e for e in self.generative_regions()
            if e.evidence_points < minimum_points
        ]

    def undocumented_regions(self) -> list[AuthorshipEvidence]:
        """Generative regions with no recorded human contribution at all.

        These are the gaps that will be hardest to answer for later, because
        the evidence was never captured — not because it did not exist.
        """
        return [e for e in self.generative_regions() if e.evidence_points == 0]

    # -- Construction ------------------------------------------------------

    @classmethod
    def from_capability_profile(
        cls,
        profile: CapabilityProfile,
        work: str = "",
        compiled_by: str = "",
    ) -> "AuthorshipRecord":
        """Seed a record from a capability profile.

        This captures what the pipeline recorded — transformation, control,
        guidance. It cannot capture what a human did, which is the part that
        matters; fill in ``contributions``, ``iterations``, and the review
        flags per region afterwards.
        """
        record = cls(
            work=work or profile.name,
            description=profile.description,
            compiled_by=compiled_by,
        )
        for region in profile.regions:
            record.add_evidence(_evidence_from_region(region))
        return record

    # -- Output ------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "work": self.work,
            "description": self.description,
            "compiled_at": self.compiled_at.isoformat(),
            "compiled_by": self.compiled_by,
            "evidence": [e.to_dict() for e in self.evidence],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthorshipRecord":
        record = cls(
            work=data["work"],
            description=data.get("description", ""),
            compiled_by=data.get("compiled_by", ""),
        )
        if data.get("compiled_at"):
            record.compiled_at = datetime.fromisoformat(data["compiled_at"])
        for e in data.get("evidence", []):
            record.add_evidence(AuthorshipEvidence.from_dict(e))
        return record

    def summary(self) -> str:
        generative = self.generative_regions()
        undocumented = self.undocumented_regions()
        thin = self.thin_evidence_regions()

        lines = [
            f"Authorship Record: {self.work}",
            f"Compiled:  {self.compiled_at:%Y-%m-%d %H:%M}"
            + (f" by {self.compiled_by}" if self.compiled_by else ""),
            f"Regions:   {len(self.evidence)} total, "
            f"{len(generative)} introducing new content",
            "",
            "This record documents human contribution. It does not determine "
            "whether that contribution is sufficient for copyright — no "
            "source supplies that threshold.",
            "",
        ]

        if generative:
            lines.append("Regions introducing new content:")
            for e in generative:
                marker = "⚠️ " if e.evidence_points == 0 else "   "
                lines.append(
                    f"{marker}{e.region}: {e.evidence_points} recorded "
                    f"contribution(s)"
                    + (
                        f", {e.transformation.label.lower()}"
                        if e.transformation else ""
                    )
                )
                for contribution in e.contributions:
                    lines.append(f"      - {contribution}")

        if undocumented:
            lines.append("")
            lines.append(
                "No human contribution recorded for: "
                + ", ".join(e.region for e in undocumented)
            )
        elif thin:
            lines.append("")
            lines.append(
                "Sparse evidence for: " + ", ".join(e.region for e in thin)
            )

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()


def _evidence_from_region(region: RegionProfile) -> AuthorshipEvidence:
    """Build an evidence stub carrying what the pipeline recorded."""
    return AuthorshipEvidence(
        region=region.region,
        control=region.control,
        transformation=region.transformation,
        guidance_strength=region.guidance_strength,
        notes=region.notes,
    )
