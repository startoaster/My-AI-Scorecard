"""
Deriving classification from pipeline signals.

Governance metadata is usually asserted: someone fills in a form saying what a
workflow does. Assertions drift from what actually ran, they vary between the
people filling them in, and they are produced once — at approval time — rather
than per shot.

Some pipelines can do better. A workflow that conditions a generative model on
signals extracted from source material typically records how tightly each
region was held to that source, which conditioning signals were supplied, and
how the result was composited. Those recorded values are a direct measure of
the two things classification cares about: how much new content was introduced,
and how much of the recipe the human supplied.

This module converts recorded signals into a
:class:`~ai_use_case_context.capability.CapabilityProfile`. The result is
governance metadata the pipeline emits rather than metadata a person types.

**Guidance strength** is the central signal: a recorded value in [0.0, 1.0]
where 1.0 means the operation was fully constrained by its source material and
0.0 means it was unconstrained. Pipelines name this differently; whatever it is
called locally, normalize it to this range before passing it in.

.. note::
   Derivation covers stages that *produce* media. Stages that only read from
   the input — segmentation, depth estimation, tracking — introduce no new
   content regardless of any guidance value, so classify those directly with
   :class:`~ai_use_case_context.capability.RegionProfile` instead of deriving.

.. warning::
   Thresholds here are defaults, not measurements. They encode a defensible
   reading of what guidance values mean, and an organization that calibrates
   against its own pipeline should override them via :class:`DerivationThresholds`.
   Record which thresholds produced a classification if it will be relied on
   later — the numbers are part of the finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from ai_use_case_context.capability import (
    CapabilityProfile,
    ControlMode,
    FinalPixelRole,
    LikenessPresence,
    RegionProfile,
    TransformationClass,
)


class OutputComposition(Enum):
    """How a stage's output is delivered downstream.

      LAYERED  - Separate components a compositor works with independently.
                 Human work necessarily follows.
      HYBRID   - Primary subject delivered merged and locked; surrounding
                 material remains as editable layers.
      DIRECT   - A single finished frame, composited and ready for editorial.
                 No further artist work is expected.
    """
    LAYERED = 0
    HYBRID = 1
    DIRECT = 2

    @property
    def label(self) -> str:
        return self.name.title()


@dataclass
class DerivationThresholds:
    """Guidance-strength cut points for transformation class.

    Read as: at or above ``enhancement_at`` the operation is so tightly bound
    to its source that it introduces no material new content; below
    ``synthesis_below`` it is substantially unconstrained. The two middle bands
    cover local repair and material modification.

    Defaults are deliberately conservative — where a value sits near a
    boundary, they choose the more novel class, because under-classifying is
    the failure that skips a review.
    """
    enhancement_at: float = 0.95
    repair_at: float = 0.80
    modification_at: float = 0.50
    synthesis_below: float = 0.50

    def __post_init__(self):
        ordered = (
            self.enhancement_at >= self.repair_at >= self.modification_at
            >= self.synthesis_below
        )
        if not ordered:
            raise ValueError(
                "Thresholds must be ordered: enhancement_at >= repair_at "
                ">= modification_at >= synthesis_below"
            )
        for name, value in (
            ("enhancement_at", self.enhancement_at),
            ("repair_at", self.repair_at),
            ("modification_at", self.modification_at),
            ("synthesis_below", self.synthesis_below),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be within [0.0, 1.0], got {value}"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enhancement_at": self.enhancement_at,
            "repair_at": self.repair_at,
            "modification_at": self.modification_at,
            "synthesis_below": self.synthesis_below,
        }


DEFAULT_THRESHOLDS = DerivationThresholds()


@dataclass
class GuidanceSignal:
    """Recorded signals for one region of one generative stage.

    Attributes:
        region:              Identifier for the region — a semantic mask, a
                             layer, an element.
        guidance_strength:   Recorded [0.0, 1.0]; 1.0 = fully constrained by
                             the source material.
        conditioning:        Names of the conditioning signals supplied to the
                             stage for this region (for example depth,
                             segmentation, motion, or a reference image). The
                             count and provenance of these is what separates a
                             conditioned operation from a preset one.
        region_specific:     True if this region was addressed separately
                             rather than inheriting a whole-frame setting.
        user_authored:       True if a human, rather than the tool, supplied
                             the conditioning inputs.
        composition:         How the stage's output is delivered downstream.
        likeness:            Whether a performer is present in this region.
        notes:               Free text carried through to the profile.
    """
    region: str
    guidance_strength: float
    conditioning: list[str] = field(default_factory=list)
    region_specific: bool = False
    user_authored: bool = True
    composition: OutputComposition = OutputComposition.LAYERED
    likeness: LikenessPresence = LikenessPresence.NONE
    notes: str = ""

    def __post_init__(self):
        if not 0.0 <= self.guidance_strength <= 1.0:
            raise ValueError(
                f"guidance_strength must be within [0.0, 1.0], "
                f"got {self.guidance_strength}"
            )


# ---------------------------------------------------------------------------
# Derivation
# ---------------------------------------------------------------------------

def derive_transformation(
    guidance_strength: float,
    thresholds: DerivationThresholds = DEFAULT_THRESHOLDS,
) -> TransformationClass:
    """Map a recorded guidance value onto a transformation class.

    Only ever returns classes that produce media. Extraction and conversion
    are not derivable from a guidance value — a stage that reads from the
    input introduces nothing regardless of how it was conditioned.
    """
    if not 0.0 <= guidance_strength <= 1.0:
        raise ValueError(
            f"guidance_strength must be within [0.0, 1.0], "
            f"got {guidance_strength}"
        )
    if guidance_strength >= thresholds.enhancement_at:
        return TransformationClass.ENHANCEMENT
    if guidance_strength >= thresholds.repair_at:
        return TransformationClass.REPAIR
    if guidance_strength >= thresholds.modification_at:
        return TransformationClass.MODIFICATION
    return TransformationClass.SYNTHESIS


def derive_control_mode(signal: GuidanceSignal) -> ControlMode:
    """Infer how much of the recipe the human supplied.

    The ladder: conditioning signals the user authored move an operation above
    preset; addressing regions separately — deciding what gets treated how —
    is what distinguishes assembling the operation from configuring it.
    """
    if not signal.conditioning:
        # Guidance strength alone is a tunable parameter, not a recipe.
        return ControlMode.PARAMETERIZED if signal.user_authored else ControlMode.PRESET
    if not signal.user_authored:
        # Conditioning exists but the tool produced it — the user did not
        # shape the result, they accepted what the tool derived.
        return ControlMode.PRESET
    if signal.region_specific and len(signal.conditioning) >= 2:
        return ControlMode.COMPOSED
    return ControlMode.CONDITIONED


def derive_final_pixel_role(
    composition: OutputComposition,
    region_is_primary: bool = False,
) -> FinalPixelRole:
    """Infer whether output reaches the delivered work substantially as made.

    Layered output implies human compositing follows, so no single layer is
    the delivered frame. Direct output is the delivered frame by definition.
    Hybrid locks the primary subject while leaving the rest editable, so the
    answer depends on which region is being classified.
    """
    if composition is OutputComposition.DIRECT:
        return FinalPixelRole.DELIVERED_FRAME
    if composition is OutputComposition.HYBRID:
        return (
            FinalPixelRole.DELIVERED_FRAME
            if region_is_primary
            else FinalPixelRole.COMPOSITED_ELEMENT
        )
    return FinalPixelRole.COMPOSITED_ELEMENT


def derive_region_profile(
    signal: GuidanceSignal,
    thresholds: DerivationThresholds = DEFAULT_THRESHOLDS,
    region_is_primary: bool = False,
) -> RegionProfile:
    """Build a region classification from one region's recorded signals."""
    return RegionProfile(
        region=signal.region,
        transformation=derive_transformation(
            signal.guidance_strength, thresholds
        ),
        control=derive_control_mode(signal),
        likeness=signal.likeness,
        final_pixel=derive_final_pixel_role(
            signal.composition, region_is_primary
        ),
        guidance_strength=signal.guidance_strength,
        notes=signal.notes,
    )


@dataclass
class PipelineRecord:
    """Recorded signals for one generative stage, across all its regions.

    ``primary_region`` names the region carrying the main subject, which
    matters only when output composition is hybrid — that is the region
    delivered locked while the rest stays editable.
    """
    stage: str
    signals: list[GuidanceSignal] = field(default_factory=list)
    primary_region: str = ""
    thresholds: DerivationThresholds = field(
        default_factory=lambda: DEFAULT_THRESHOLDS
    )
    model: str = ""
    notes: str = ""

    def add_signal(self, signal: GuidanceSignal) -> GuidanceSignal:
        self.signals.append(signal)
        return signal

    def to_capability_profile(self) -> CapabilityProfile:
        """Derive a full capability classification from the recorded signals."""
        profile = CapabilityProfile(
            name=self.stage,
            description=self.notes,
        )
        for signal in self.signals:
            profile.add_region(
                derive_region_profile(
                    signal,
                    thresholds=self.thresholds,
                    region_is_primary=(signal.region == self.primary_region),
                )
            )
        return profile

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "model": self.model,
            "primary_region": self.primary_region,
            "thresholds": self.thresholds.to_dict(),
            "notes": self.notes,
            "signals": [
                {
                    "region": s.region,
                    "guidance_strength": s.guidance_strength,
                    "conditioning": list(s.conditioning),
                    "region_specific": s.region_specific,
                    "user_authored": s.user_authored,
                    "composition": s.composition.name,
                    "likeness": s.likeness.name,
                    "notes": s.notes,
                }
                for s in self.signals
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PipelineRecord":
        thresholds = (
            DerivationThresholds(**data["thresholds"])
            if data.get("thresholds")
            else DEFAULT_THRESHOLDS
        )
        record = cls(
            stage=data["stage"],
            primary_region=data.get("primary_region", ""),
            thresholds=thresholds,
            model=data.get("model", ""),
            notes=data.get("notes", ""),
        )
        for s in data.get("signals", []):
            record.add_signal(
                GuidanceSignal(
                    region=s["region"],
                    guidance_strength=s["guidance_strength"],
                    conditioning=list(s.get("conditioning", [])),
                    region_specific=s.get("region_specific", False),
                    user_authored=s.get("user_authored", True),
                    composition=OutputComposition[
                        s.get("composition", "LAYERED")
                    ],
                    likeness=LikenessPresence[s.get("likeness", "NONE")],
                    notes=s.get("notes", ""),
                )
            )
        return record
