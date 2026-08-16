"""
Where a tool and its models come from.

Supply facts about an AI tool — who provides it, how it is packaged, which
models it runs, and what those models were trained on — determine a large share
of the governance questions that follow, and none of them are visible from what
the tool does to the media.

These are recorded as **facts with rules**, not as scored dimensions. The
distinction matters: a vendor's headquarters or a training corpus that includes
web crawl is either the case or it is not, and a reviewer can check it. A
"training data transparency: 70/100" is a judgment nobody can reproduce, and
averaging it with five other judgments produces a number that survives contact
with no scrutiny at all.

Two fields here carry more weight than their size suggests:

* **Separability** — whether the generative parts of a tool can be turned off
  independently. A tool whose capabilities cannot be separated forces an
  all-or-nothing approval, which is why a low-novelty feature can drag a whole
  product into a review it would not otherwise need.
* **Source commitment** — how long the training-data arrangements hold. An
  approval granted against today's corpus means little if the corpus can be
  replaced next quarter without notice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING

from ai_use_case_context.authority import Authority, AuthoritySource
from ai_use_case_context.core import RiskDimension, RiskLevel

if TYPE_CHECKING:  # pragma: no cover
    from ai_use_case_context.core import RiskFlag, UseCaseContext


# ---------------------------------------------------------------------------
# Vendor profile
# ---------------------------------------------------------------------------

class AIPosture(Enum):
    """How a vendor obtains the AI it ships.

    Not ordered. Each posture carries different questions rather than more or
    less risk: a vendor training its own models owns its training data story,
    while one routing to third-party services inherits someone else's.
    """
    OWN_MODELS = "Provides its own models"
    CUSTOMIZES_THIRD_PARTY = "Customizes third-party models"
    OPEN_SOURCE_MODELS = "Uses open-source models"
    RELIES_ON_AI_SERVICES = "Relies on other AI services"


@dataclass
class VendorProfile:
    """The organization providing the tool."""
    name: str = ""
    headquarters: str = ""
    operating_locations: list[str] = field(default_factory=list)
    postures: list[AIPosture] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "headquarters": self.headquarters,
            "operating_locations": list(self.operating_locations),
            "postures": [p.name for p in self.postures],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VendorProfile":
        return cls(
            name=data.get("name", ""),
            headquarters=data.get("headquarters", ""),
            operating_locations=list(data.get("operating_locations", [])),
            postures=[AIPosture[p] for p in data.get("postures", [])],
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Packaging
# ---------------------------------------------------------------------------

class Packaging(Enum):
    """How the tool is delivered as a single unit."""
    DESKTOP_SOFTWARE = "Desktop software"
    SAAS = "SaaS"
    API_SERVICE = "API-driven service"
    PLUGIN = "Plug-in"
    PIPELINE_NODE = "Node for node-driven workflows"
    WORKFLOW_PLATFORM = "Workflow platform"
    MODEL_ROUTER = "Model aggregator or router"


class Separability(Enum):
    """Whether individual AI capabilities can be governed independently."""
    CUSTOMER_CONFIGURABLE = "Customer can enable or disable per capability"
    VENDOR_CONFIGURABLE = "Vendor can enable or disable per capability"
    USER_DISCRETION = "Left to user discretion under guideline"
    NOT_SEPARABLE = "Capabilities are integrated and cannot be separated"

    @property
    def is_enforceable_by_configuration(self) -> bool:
        """True if a restriction can be imposed technically, not just asked for.

        User discretion is a policy, not a control: it depends on everyone
        following the guideline every time.
        """
        return self in (
            Separability.CUSTOMER_CONFIGURABLE,
            Separability.VENDOR_CONFIGURABLE,
        )


@dataclass
class ToolPackaging:
    """What is licensed, and how much of it can be governed separately."""
    packaging: Packaging = Packaging.SAAS
    separability: Separability = Separability.NOT_SEPARABLE
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "packaging": self.packaging.name,
            "separability": self.separability.name,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolPackaging":
        return cls(
            packaging=Packaging[data["packaging"]],
            separability=Separability[data["separability"]],
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Model provisioning
# ---------------------------------------------------------------------------

class ModelOrigin(Enum):
    """Where a model came from."""
    VENDOR_TRAINED = "Trained by the vendor"
    OPEN_WEIGHTS = "Obtained as open weights"
    DERIVED_FROM_OPEN_WEIGHTS = "Derived from open weights"
    COMMERCIAL = "Commercial model"
    DERIVED_FROM_COMMERCIAL = "Derived from a commercial model"

    @property
    def is_derived(self) -> bool:
        """True if an upstream licence chain sits behind this model."""
        return self in (
            ModelOrigin.DERIVED_FROM_OPEN_WEIGHTS,
            ModelOrigin.DERIVED_FROM_COMMERCIAL,
        )


class BYOPolicy(Enum):
    """Whether customers may supply their own models."""
    NOT_SUPPORTED = "No bring-your-own support"
    SPECIFIC_MODELS = "Specific supported models only"
    ANY_MODEL = "Any model meeting stated characteristics"


@dataclass
class ModelProvisioning:
    """Which models are available within or alongside the tool."""
    vendor_models: list[str] = field(default_factory=list)
    origins: list[ModelOrigin] = field(default_factory=list)
    model_provider_headquarters: str = ""
    byo_policy: BYOPolicy = BYOPolicy.NOT_SUPPORTED
    notes: str = ""

    @property
    def has_derived_models(self) -> bool:
        return any(o.is_derived for o in self.origins)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor_models": list(self.vendor_models),
            "origins": [o.name for o in self.origins],
            "model_provider_headquarters": self.model_provider_headquarters,
            "byo_policy": self.byo_policy.name,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelProvisioning":
        return cls(
            vendor_models=list(data.get("vendor_models", [])),
            origins=[ModelOrigin[o] for o in data.get("origins", [])],
            model_provider_headquarters=data.get(
                "model_provider_headquarters", ""
            ),
            byo_policy=BYOPolicy[data.get("byo_policy", "NOT_SUPPORTED")],
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Training data
# ---------------------------------------------------------------------------

class TrainingDataSource(Enum):
    """Broad source types used to train or adapt a model."""
    COMMERCIALLY_LICENSED = "Commercially licensed"
    OPEN_SOURCE_LICENSED = "Open-source licensed"
    PUBLIC_DOMAIN = "Public domain"
    WEB_CRAWL = "Web crawl"
    VENDOR_OWNED = "Vendor-owned"
    ALGORITHMICALLY_GENERATED = "Algorithmically generated"
    DISTILLED_FROM_MODEL = "Distilled from another model"


class SourceCommitment(Enum):
    """How long the training-data arrangements are guaranteed to hold."""
    TOOL_LIFETIME = "For the lifetime of the tool"
    LONG_TERM_SUPPORT = "For a long-term support period"
    DATE_BOUND = "Until a stated date"
    NONE_STATED = "No commitment stated"


@dataclass
class TrainingDataProfile:
    """What the models were trained on, and for how long that holds."""
    source_types: list[TrainingDataSource] = field(default_factory=list)
    named_datasets: list[str] = field(default_factory=list)
    commitment: SourceCommitment = SourceCommitment.NONE_STATED
    commitment_date: str = ""
    notes: str = ""

    @property
    def is_documented(self) -> bool:
        return bool(self.source_types)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_types": [s.name for s in self.source_types],
            "named_datasets": list(self.named_datasets),
            "commitment": self.commitment.name,
            "commitment_date": self.commitment_date,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainingDataProfile":
        return cls(
            source_types=[
                TrainingDataSource[s] for s in data.get("source_types", [])
            ],
            named_datasets=list(data.get("named_datasets", [])),
            commitment=SourceCommitment[data.get("commitment", "NONE_STATED")],
            commitment_date=data.get("commitment_date", ""),
            notes=data.get("notes", ""),
        )


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@dataclass
class SourcingRule:
    """A rule that turns a recorded supply fact into a risk flag."""
    rule_id: str
    title: str
    applies: Callable[["SourcingProfile"], bool]
    dimension: Any
    level: RiskLevel
    describe: Callable[["SourcingProfile"], str]
    authority: Authority = Authority.UNSPECIFIED
    source: Optional[AuthoritySource] = None


_TDM_RESERVATION = AuthoritySource(
    body="Text and data mining reservation",
    authority=Authority.STATUTE,
    citation="Applicable regime depends on where mining occurred",
)

_UPSTREAM_MODEL_TERMS = AuthoritySource(
    body="Upstream model licence",
    authority=Authority.BINDING_CONTRACT,
    citation="Terms of the model this one was derived from",
)


DEFAULT_SOURCING_RULES: list[SourcingRule] = [
    SourcingRule(
        rule_id="TRAINING_SOURCES_UNDOCUMENTED",
        title="Training data sources not documented",
        applies=lambda p: not p.training_data.is_documented,
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        describe=lambda p: (
            "No training data source types are documented. Every downstream "
            "question about rights in the output rests on this and cannot be "
            "answered without it."
        ),
    ),
    SourcingRule(
        rule_id="WEB_CRAWL_TRAINING_DATA",
        title="Training corpus includes web crawl",
        applies=lambda p: (
            TrainingDataSource.WEB_CRAWL in p.training_data.source_types
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        authority=Authority.STATUTE,
        source=_TDM_RESERVATION,
        describe=lambda p: (
            "The training corpus includes web crawl. Whether rights-holder "
            "reservations were honoured, and under which regime, requires "
            "confirmation from the provider."
        ),
    ),
    SourcingRule(
        rule_id="DISTILLED_FROM_ANOTHER_MODEL",
        title="Model distilled from another model",
        applies=lambda p: (
            TrainingDataSource.DISTILLED_FROM_MODEL
            in p.training_data.source_types
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.MEDIUM,
        authority=Authority.BINDING_CONTRACT,
        source=_UPSTREAM_MODEL_TERMS,
        describe=lambda p: (
            "The model was distilled from another model. Upstream terms "
            "commonly restrict this, and the restriction travels with any "
            "output produced downstream."
        ),
    ),
    SourcingRule(
        rule_id="SYNTHETIC_TRAINING_DATA",
        title="Training corpus includes generated material",
        applies=lambda p: (
            TrainingDataSource.ALGORITHMICALLY_GENERATED
            in p.training_data.source_types
        ),
        dimension=RiskDimension.QUALITY,
        level=RiskLevel.MEDIUM,
        describe=lambda p: (
            "The training corpus includes algorithmically generated material. "
            "Confirm the share and how it is tracked; degradation from "
            "recursive training is not visible in ordinary output review."
        ),
    ),
    SourcingRule(
        rule_id="DERIVED_MODEL_LICENCE_CHAIN",
        title="Model derived from an upstream model",
        applies=lambda p: p.model_provisioning.has_derived_models,
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.MEDIUM,
        authority=Authority.BINDING_CONTRACT,
        source=_UPSTREAM_MODEL_TERMS,
        describe=lambda p: (
            "One or more models are derived from upstream models. Confirm "
            "that the upstream licence permits the derivation and the "
            "intended use of its outputs."
        ),
    ),
    SourcingRule(
        rule_id="NO_SOURCE_COMMITMENT",
        title="No commitment to current training-data arrangements",
        applies=lambda p: (
            p.training_data.commitment is SourceCommitment.NONE_STATED
            and p.training_data.is_documented
        ),
        dimension=RiskDimension.FEASIBILITY,
        level=RiskLevel.MEDIUM,
        describe=lambda p: (
            "No commitment period is stated for the training-data "
            "arrangements. An approval granted against today's corpus does "
            "not carry to a replacement."
        ),
    ),
    SourcingRule(
        rule_id="CAPABILITIES_NOT_SEPARABLE",
        title="Capabilities cannot be governed independently",
        applies=lambda p: (
            not p.packaging.separability.is_enforceable_by_configuration
        ),
        dimension=RiskDimension.FEASIBILITY,
        level=RiskLevel.MEDIUM,
        describe=lambda p: (
            f"Separability is '{p.packaging.separability.value}', so a "
            f"restriction on individual capabilities cannot be imposed "
            f"technically. Any approval covers what the tool can do, not what "
            f"it is intended to be used for."
        ),
    ),
    SourcingRule(
        rule_id="UNRESTRICTED_BYO_MODELS",
        title="Arbitrary customer-supplied models accepted",
        applies=lambda p: (
            p.model_provisioning.byo_policy is BYOPolicy.ANY_MODEL
        ),
        dimension=RiskDimension.SECURITY,
        level=RiskLevel.MEDIUM,
        describe=lambda p: (
            "The tool accepts any model meeting stated characteristics, so "
            "models outside this assessment can be introduced after approval "
            "without a further review."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@dataclass
class SourcingProfile:
    """The full supply picture for a tool and the models behind it."""
    vendor: VendorProfile = field(default_factory=VendorProfile)
    packaging: ToolPackaging = field(default_factory=ToolPackaging)
    model_provisioning: ModelProvisioning = field(
        default_factory=ModelProvisioning
    )
    training_data: TrainingDataProfile = field(
        default_factory=TrainingDataProfile
    )
    notes: str = ""

    def derive_flags(
        self,
        ctx: "UseCaseContext",
        rules: Optional[list[SourcingRule]] = None,
    ) -> list["RiskFlag"]:
        """Raise flags on ``ctx`` for every rule matching this profile."""
        active = DEFAULT_SOURCING_RULES if rules is None else rules
        added: list["RiskFlag"] = []
        for rule in active:
            if not rule.applies(self):
                continue
            added.append(
                ctx.flag_risk(
                    dimension=rule.dimension,
                    level=rule.level,
                    description=rule.describe(self),
                    authority=rule.authority,
                    source=rule.source,
                )
            )
        return added

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor": self.vendor.to_dict(),
            "packaging": self.packaging.to_dict(),
            "model_provisioning": self.model_provisioning.to_dict(),
            "training_data": self.training_data.to_dict(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourcingProfile":
        return cls(
            vendor=VendorProfile.from_dict(data["vendor"]),
            packaging=ToolPackaging.from_dict(data["packaging"]),
            model_provisioning=ModelProvisioning.from_dict(
                data["model_provisioning"]
            ),
            training_data=TrainingDataProfile.from_dict(data["training_data"]),
            notes=data.get("notes", ""),
        )

    def summary(self) -> str:
        td = self.training_data
        return "\n".join([
            f"Vendor:       {self.vendor.name or '(not stated)'}"
            + (f" — {self.vendor.headquarters}" if self.vendor.headquarters else ""),
            f"Packaging:    {self.packaging.packaging.value}",
            f"Separability: {self.packaging.separability.value}",
            f"BYO models:   {self.model_provisioning.byo_policy.value}",
            f"Training data: "
            + (
                ", ".join(s.value for s in td.source_types)
                if td.source_types else "(not documented)"
            ),
            f"Commitment:   {td.commitment.value}"
            + (f" ({td.commitment_date})" if td.commitment_date else ""),
        ])

    def __str__(self) -> str:
        return self.summary()
