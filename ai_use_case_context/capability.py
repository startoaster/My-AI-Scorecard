"""
Capability classification for AI-enabled production work.

Two properties of an AI capability drive most governance questions, and they
are independent of each other:

  * **What it does to the media** — does it read information out of an input,
    improve it, repair it, materially change it, or create new media?
    (:class:`TransformationClass`)
  * **Who defines the recipe** — is the operation fixed by the tool, tuned by
    parameters, conditioned on inputs the user supplies, or assembled by the
    user? (:class:`ControlMode`)

Deliberately absent is any classification by model architecture. Whether a
capability is built on a diffusion model or a transformer predicts very little
about its governance treatment — the same architecture serves both metadata
tagging and full scene generation. What matters is the effect on the media and
the degree of human direction.

Two further properties determine whether anyone outside the production is
affected: whether the output reaches the audience (:class:`FinalPixelRole`) and
whether a performer is present in it (:class:`LikenessPresence`).

**Classification is per region, not per shot.** A single frame can carry a hero
performer locked to the recorded plate alongside a fully generated background,
and those are not the same governance case. :class:`RegionProfile` classifies
one region; :class:`CapabilityProfile` holds the set.

.. note::
   :meth:`CapabilityProfile.derive_flags` raises flags and routes them. It does
   not determine whether any agreement or statute applies — that determination
   belongs to a qualified human, and the flags say so explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING

from ai_use_case_context.authority import Authority, AuthoritySource
from ai_use_case_context.core import RiskDimension, RiskLevel
from ai_use_case_context.vocabulary import VocabularyMapping

if TYPE_CHECKING:  # pragma: no cover
    from ai_use_case_context.core import RiskFlag, UseCaseContext


# ---------------------------------------------------------------------------
# Dimensions of a capability
# ---------------------------------------------------------------------------

class TransformationClass(Enum):
    """What the capability does to the media, in increasing order of novelty.

      EXTRACTION    - Reads information already present in the input. Produces
                      no media. (Script breakdown, segmentation, speech-to-text.)
      CONVERSION    - Represents existing content in another modality without
                      adding to it. (Transcription to caption, 2D to depth.)
      ENHANCEMENT   - Improves fidelity without introducing new elements.
                      (Formulaic denoise, formulaic upres.)
      REPAIR        - Introduces limited new material to locally complete or
                      fix an otherwise existing asset. (Plate cleanup, small
                      object removal, detail reconstruction.)
      MODIFICATION  - Materially changes existing media, but the output remains
                      traceable to the original. (De-aging, visual dubbing.)
      SYNTHESIS     - Produces substantially new media, where similar inputs
                      admit many valid outputs. (Text-to-video, text-to-3D.)
    """
    EXTRACTION = 0
    CONVERSION = 1
    ENHANCEMENT = 2
    REPAIR = 3
    MODIFICATION = 4
    SYNTHESIS = 5

    @property
    def introduces_new_content(self) -> bool:
        """True if the capability adds material that was not in the input."""
        return self.value >= TransformationClass.REPAIR.value

    @property
    def label(self) -> str:
        return self.name.replace("_", " ").title()


class ControlMode(Enum):
    """How much of the operation the user defines, in increasing order.

      PRESET         - The user selects a predefined operation; the tool
                       determines the output.
      PARAMETERIZED  - The user tunes predefined parameters within a fixed
                       processing path.
      CONDITIONED    - User-supplied inputs meaningfully shape the result
                       within a constrained recipe; several valid outputs exist.
      COMPOSED       - The user assembles the operation — regions, layers,
                       ordering — and substantially determines the outcome.
    """
    PRESET = 0
    PARAMETERIZED = 1
    CONDITIONED = 2
    COMPOSED = 3

    @property
    def is_substantially_human_directed(self) -> bool:
        """True if the human, not the tool, determines most of the recipe."""
        return self.value >= ControlMode.CONDITIONED.value

    @property
    def label(self) -> str:
        return self.name.replace("_", " ").title()


class FinalPixelRole(Enum):
    """Whether and how the output reaches the delivered work.

      NONE                - Output is discarded or used only to inform a human.
      REFERENCE_ONLY      - Internal reference; not composited into the work.
      COMPOSITED_ELEMENT  - Combined with other material on the way to final.
      DELIVERED_FRAME     - Appears in the delivered work substantially as
                            produced.
    """
    NONE = 0
    REFERENCE_ONLY = 1
    COMPOSITED_ELEMENT = 2
    DELIVERED_FRAME = 3

    @property
    def reaches_audience(self) -> bool:
        return self.value >= FinalPixelRole.COMPOSITED_ELEMENT.value

    @property
    def label(self) -> str:
        return self.name.replace("_", " ").title()


class LikenessPresence(Enum):
    """How a performer is present in the output.

      NONE         - No performer present.
      AESTHETIC    - Style or associated visual signature only.
      VOICE        - The performer's voice.
      PERFORMANCE  - The performer's recorded or depicted performance.
    """
    NONE = 0
    AESTHETIC = 1
    VOICE = 2
    PERFORMANCE = 3

    @property
    def label(self) -> str:
        return self.name.title()


# ---------------------------------------------------------------------------
# Region and capability profiles
# ---------------------------------------------------------------------------

@dataclass
class RegionProfile:
    """Classification of one region of the output.

    A region is whatever unit the pipeline can treat independently — a semantic
    mask, a layer, a shot element. ``guidance_strength``, when the pipeline
    reports it, is the recorded [0.0, 1.0] measure of how tightly the operation
    was held to its source material; 1.0 means fully constrained by the source.
    """
    region: str
    transformation: TransformationClass
    control: ControlMode
    likeness: LikenessPresence = LikenessPresence.NONE
    final_pixel: FinalPixelRole = FinalPixelRole.COMPOSITED_ELEMENT
    guidance_strength: Optional[float] = None
    notes: str = ""

    def __post_init__(self):
        if self.guidance_strength is not None:
            if not 0.0 <= self.guidance_strength <= 1.0:
                raise ValueError(
                    f"guidance_strength must be within [0.0, 1.0], "
                    f"got {self.guidance_strength}"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "region": self.region,
            "transformation": self.transformation.name,
            "control": self.control.name,
            "likeness": self.likeness.name,
            "final_pixel": self.final_pixel.name,
            "guidance_strength": self.guidance_strength,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegionProfile":
        return cls(
            region=data["region"],
            transformation=TransformationClass[data["transformation"]],
            control=ControlMode[data["control"]],
            likeness=LikenessPresence[data.get("likeness", "NONE")],
            final_pixel=FinalPixelRole[
                data.get("final_pixel", "COMPOSITED_ELEMENT")
            ],
            guidance_strength=data.get("guidance_strength"),
            notes=data.get("notes", ""),
        )

    def to_external(self, mapping: "VocabularyMapping") -> dict[str, Any]:
        """Render this region in an external vocabulary's terms.

        Unmapped members come back as ``None`` rather than falling back to our
        own names — a silent fallback would misrepresent our terms as theirs.
        """
        return {
            "region": self.region,
            "transformation": mapping.term_for(self.transformation),
            "control": mapping.term_for(self.control),
            "likeness": mapping.term_for(self.likeness),
            "final_pixel": mapping.term_for(self.final_pixel),
            "guidance_strength": self.guidance_strength,
            "notes": self.notes,
        }

    def __str__(self) -> str:
        bits = [
            f"{self.region}: {self.transformation.label}",
            self.control.label,
            self.final_pixel.label,
        ]
        if self.likeness is not LikenessPresence.NONE:
            bits.append(f"likeness={self.likeness.label}")
        if self.guidance_strength is not None:
            bits.append(f"guidance={self.guidance_strength:.2f}")
        return " | ".join(bits)


# ---------------------------------------------------------------------------
# Derivation rules
# ---------------------------------------------------------------------------

@dataclass
class CapabilityRule:
    """A rule that turns a region classification into a risk flag.

    Rules are data, not hardcoded branches, so an organization can inspect,
    reorder, remove, or extend them. ``describe`` receives the region and
    returns the flag description.
    """
    rule_id: str
    title: str
    applies: Callable[[RegionProfile], bool]
    dimension: Any
    level: RiskLevel
    describe: Callable[[RegionProfile], str]
    authority: Authority = Authority.UNSPECIFIED
    source: Optional[AuthoritySource] = None


_PERFORMER_AGREEMENT = AuthoritySource(
    body="Performer collective bargaining agreement",
    authority=Authority.BINDING_CONTRACT,
    citation="Applicable agreement to be confirmed for this production",
)

_REGISTRATION_GUIDANCE = AuthoritySource(
    body="Copyright registration guidance",
    authority=Authority.REGULATORY_GUIDANCE,
    citation="Disclosure of AI-generated material in registration",
)

_AUTHORSHIP_UNSETTLED = AuthoritySource(
    body="No settled definition",
    authority=Authority.EMERGING,
    citation="Human authorship threshold undecided",
)


DEFAULT_CAPABILITY_RULES: list[CapabilityRule] = [
    CapabilityRule(
        rule_id="PERFORMER_IN_GENERATED_CONTENT",
        title="Performer present in materially changed or synthesized media",
        applies=lambda r: (
            r.likeness is not LikenessPresence.NONE
            and r.transformation.value >= TransformationClass.MODIFICATION.value
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        authority=Authority.BINDING_CONTRACT,
        source=_PERFORMER_AGREEMENT,
        describe=lambda r: (
            f"Region '{r.region}': performer {r.likeness.label.lower()} present "
            f"in {r.transformation.label.lower()} output. Whether this is an "
            f"alteration of a recorded performance or a created replica turns "
            f"on facts this framework does not evaluate. Determination and "
            f"consent analysis required before proceeding."
        ),
    ),
    CapabilityRule(
        rule_id="RECORDED_PERFORMANCE_ALTERED",
        title="Recorded performance altered without synthesis",
        applies=lambda r: (
            r.likeness is LikenessPresence.PERFORMANCE
            and TransformationClass.ENHANCEMENT.value
            <= r.transformation.value
            <= TransformationClass.REPAIR.value
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.MEDIUM,
        authority=Authority.BINDING_CONTRACT,
        source=_PERFORMER_AGREEMENT,
        describe=lambda r: (
            f"Region '{r.region}': a recorded performance is being altered "
            f"({r.transformation.label.lower()}). Consent obligations may "
            f"attach depending on the nature and extent of the alteration."
        ),
    ),
    CapabilityRule(
        rule_id="SYNTHESIS_IN_DELIVERED_FRAME",
        title="Synthesized media in the delivered work",
        applies=lambda r: (
            r.transformation is TransformationClass.SYNTHESIS
            and r.final_pixel is FinalPixelRole.DELIVERED_FRAME
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        authority=Authority.REGULATORY_GUIDANCE,
        source=_REGISTRATION_GUIDANCE,
        describe=lambda r: (
            f"Region '{r.region}': synthesized media appears in the delivered "
            f"work substantially as produced. Disclosure and copyrightability "
            f"review required."
        ),
    ),
    CapabilityRule(
        rule_id="THIN_HUMAN_DIRECTION",
        title="New content produced under weak human direction",
        applies=lambda r: (
            r.transformation.introduces_new_content
            and not r.control.is_substantially_human_directed
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.MEDIUM,
        authority=Authority.EMERGING,
        source=_AUTHORSHIP_UNSETTLED,
        describe=lambda r: (
            f"Region '{r.region}': new content produced under "
            f"{r.control.label.lower()} control. Evidence of human authorship "
            f"is thin here. No source supplies a sufficiency threshold — record "
            f"the human contribution and route for review."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Capability profile
# ---------------------------------------------------------------------------

@dataclass
class CapabilityProfile:
    """A capability's classification across all the regions it touches."""
    name: str
    description: str = ""
    regions: list[RegionProfile] = field(default_factory=list)

    def add_region(self, region: RegionProfile) -> RegionProfile:
        self.regions.append(region)
        return region

    # -- Aggregates --------------------------------------------------------

    def max_transformation(self) -> TransformationClass:
        """The most novel transformation across regions."""
        return max(
            (r.transformation for r in self.regions),
            key=lambda t: t.value,
            default=TransformationClass.EXTRACTION,
        )

    def min_control(self) -> ControlMode:
        """The weakest human direction across regions.

        Weakest, not average — a single region left to the tool is the part a
        reviewer needs to see.
        """
        return min(
            (r.control for r in self.regions),
            key=lambda c: c.value,
            default=ControlMode.COMPOSED,
        )

    def max_final_pixel(self) -> FinalPixelRole:
        return max(
            (r.final_pixel for r in self.regions),
            key=lambda f: f.value,
            default=FinalPixelRole.NONE,
        )

    def max_likeness(self) -> LikenessPresence:
        return max(
            (r.likeness for r in self.regions),
            key=lambda p: p.value,
            default=LikenessPresence.NONE,
        )

    def is_uniform(self) -> bool:
        """True if every region carries the same classification.

        A non-uniform profile is the interesting case: it means one summary
        classification for the whole shot would misrepresent part of it.
        """
        if len(self.regions) <= 1:
            return True
        first = self.regions[0]
        return all(
            r.transformation is first.transformation
            and r.control is first.control
            and r.final_pixel is first.final_pixel
            and r.likeness is first.likeness
            for r in self.regions[1:]
        )

    def regions_with_likeness(self) -> list[RegionProfile]:
        return [
            r for r in self.regions if r.likeness is not LikenessPresence.NONE
        ]

    # -- Derivation --------------------------------------------------------

    def derive_flags(
        self,
        ctx: "UseCaseContext",
        rules: Optional[list[CapabilityRule]] = None,
    ) -> list["RiskFlag"]:
        """Raise flags on ``ctx`` for every rule that matches any region.

        This is the entry point that replaces hand-entered severity: the
        classification determines what gets flagged, so two people describing
        the same workflow raise the same flags.

        Returns the flags that were added.
        """
        active = DEFAULT_CAPABILITY_RULES if rules is None else rules
        added: list["RiskFlag"] = []
        for region in self.regions:
            for rule in active:
                if not rule.applies(region):
                    continue
                flag = ctx.flag_risk(
                    dimension=rule.dimension,
                    level=rule.level,
                    description=rule.describe(region),
                    authority=rule.authority,
                    source=rule.source,
                )
                added.append(flag)
        return added

    # -- Serialization -----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "regions": [r.to_dict() for r in self.regions],
        }

    def to_external(self, mapping: VocabularyMapping) -> dict[str, Any]:
        """Render the whole profile in an external vocabulary's terms."""
        return {
            "name": self.name,
            "description": self.description,
            "vocabulary": {"name": mapping.name, "version": mapping.version},
            "regions": [r.to_external(mapping) for r in self.regions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityProfile":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            regions=[
                RegionProfile.from_dict(r) for r in data.get("regions", [])
            ],
        )

    def summary(self) -> str:
        lines = [
            f"Capability: {self.name}",
            f"Regions:    {len(self.regions)}"
            + ("" if self.is_uniform() else "  (mixed classification)"),
            "",
        ]
        for region in self.regions:
            lines.append(f"  {region}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.summary()
