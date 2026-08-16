"""
Operational characteristics — where the AI runs and what happens to the data.

Security and privacy reviewers ask a fairly stable set of questions, and almost
none of them are about what a capability does to the media. They are about
where it executes, who controls updates, who holds the inputs and outputs, what
the vendor collects, how long it is kept, and whether customer material can be
used to refine a model.

None of that is derivable from a capability classification, which is why it
lives here rather than being folded into one. A denoiser and a text-to-video
model deployed identically raise identical operational questions; the same
denoiser deployed on-premises and in a vendor's cloud does not.

The rules in :data:`DEFAULT_OPERATIONAL_RULES` key on the pairing of an
operational fact with the sensitivity of the material involved, because neither
alone is decisive: a vendor-hosted deployment is unremarkable for material with
no restrictions and significant for pre-release production content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, TYPE_CHECKING

from ai_use_case_context.authority import Authority, AuthoritySource
from ai_use_case_context.core import RiskDimension, RiskLevel
from ai_use_case_context.intake import IPClass, RESTRICTED_IP_CLASSES

if TYPE_CHECKING:  # pragma: no cover
    from ai_use_case_context.core import RiskFlag, UseCaseContext


# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------

class HostEnvironment(Enum):
    """Where the AI executes, ordered by decreasing customer control."""
    ON_DEVICE = "On-device"
    ON_PREMISES = "On-premises"
    CUSTOMER_CLOUD = "Customer-controlled data centre or cloud"
    VENDOR_CLOUD = "Vendor-controlled data centre or cloud"

    @property
    def is_customer_controlled(self) -> bool:
        return self is not HostEnvironment.VENDOR_CLOUD


class UpdateControl(Enum):
    """Who decides when the deployed version changes.

    This matters more than it first appears: a vendor-controlled rollout means
    the thing that was approved and the thing running today may differ without
    notice, which undermines any approval tied to a specific behaviour.
    """
    CUSTOMER = "Customer-controlled rollout"
    VENDOR = "Vendor-controlled rollout"


@dataclass
class Deployment:
    """Where the AI is deployed and who controls its rollout."""
    host: HostEnvironment = HostEnvironment.VENDOR_CLOUD
    region: str = ""
    update_control: UpdateControl = UpdateControl.VENDOR

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host.name,
            "region": self.region,
            "update_control": self.update_control.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Deployment":
        return cls(
            host=HostEnvironment[data["host"]],
            region=data.get("region", ""),
            update_control=UpdateControl[data["update_control"]],
        )


# ---------------------------------------------------------------------------
# Data residency
# ---------------------------------------------------------------------------

class Custodian(Enum):
    """Who has operational control over inputs and outputs."""
    USER = "User (the artist operating the tool)"
    CUSTOMER = "Customer organization"
    VENDOR = "Tool vendor"


@dataclass
class DataResidency:
    """Where inputs and outputs live, and who holds them."""
    custodian: Custodian = Custodian.VENDOR
    location: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"custodian": self.custodian.name, "location": self.location}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataResidency":
        return cls(
            custodian=Custodian[data["custodian"]],
            location=data.get("location", ""),
        )


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

class CollectionPolicy(Enum):
    """Whether the vendor collects something, and whether you can decline."""
    NOT_COLLECTED = "Not collected"
    COLLECTED_OPT_OUT = "Collected, opt-out available"
    COLLECTED_REQUIRED = "Collected, no opt-out"

    @property
    def is_collected(self) -> bool:
        return self is not CollectionPolicy.NOT_COLLECTED

    @property
    def is_mandatory(self) -> bool:
        return self is CollectionPolicy.COLLECTED_REQUIRED


#: Sentinel for a retention period with no stated end.
INDEFINITE_RETENTION = "indefinite"


@dataclass
class DataCollection:
    """What the vendor collects from use, and for how long.

    ``retention_period`` is free text because vendors state it in
    incompatible units. Set it to :data:`INDEFINITE_RETENTION` when no end is
    stated — that specific case is worth flagging and worth not guessing at.
    """
    customer_data: CollectionPolicy = CollectionPolicy.NOT_COLLECTED
    metadata: CollectionPolicy = CollectionPolicy.NOT_COLLECTED
    retention_period: str = ""

    @property
    def is_indefinite(self) -> bool:
        return self.retention_period.strip().lower() == INDEFINITE_RETENTION

    @property
    def collects_anything(self) -> bool:
        return self.customer_data.is_collected or self.metadata.is_collected

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_data": self.customer_data.name,
            "metadata": self.metadata.name,
            "retention_period": self.retention_period,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataCollection":
        return cls(
            customer_data=CollectionPolicy[data["customer_data"]],
            metadata=CollectionPolicy[data["metadata"]],
            retention_period=data.get("retention_period", ""),
        )


# ---------------------------------------------------------------------------
# Customer model refinement
# ---------------------------------------------------------------------------

class RefinementLocation(Enum):
    """Where customer-driven model refinement happens, if it is supported."""
    NOT_SUPPORTED = "Not supported"
    CUSTOMER_CONTROLLED = "Customer-controlled data centre or cloud"
    VENDOR_CONTROLLED = "Vendor-controlled data centre or cloud"


@dataclass
class ModelRefinement:
    """Whether customers may refine models with their own material."""
    allowed: bool = False
    location: RefinementLocation = RefinementLocation.NOT_SUPPORTED

    def to_dict(self) -> dict[str, Any]:
        return {"allowed": self.allowed, "location": self.location.name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelRefinement":
        return cls(
            allowed=data.get("allowed", False),
            location=RefinementLocation[data["location"]],
        )


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@dataclass
class OperationalRule:
    """A rule keyed on operational facts and material sensitivity.

    ``applies`` receives the profile and the IP class of the material in play,
    which may be ``None`` when the material has not been characterized.
    """
    rule_id: str
    title: str
    applies: Callable[["OperationalProfile", Optional[IPClass]], bool]
    dimension: Any
    level: RiskLevel
    describe: Callable[["OperationalProfile", Optional[IPClass]], str]
    authority: Authority = Authority.UNSPECIFIED
    source: Optional[AuthoritySource] = None


def _is_restricted(ip_class: Optional[IPClass]) -> bool:
    return ip_class is not None and ip_class in RESTRICTED_IP_CLASSES


DEFAULT_OPERATIONAL_RULES: list[OperationalRule] = [
    OperationalRule(
        rule_id="RESTRICTED_MATERIAL_IN_VENDOR_ENVIRONMENT",
        title="Restricted material processed in a vendor environment",
        applies=lambda p, ip: (
            _is_restricted(ip)
            and p.deployment.host is HostEnvironment.VENDOR_CLOUD
        ),
        dimension=RiskDimension.SECURITY,
        level=RiskLevel.HIGH,
        describe=lambda p, ip: (
            f"{ip.value} is processed in a vendor-controlled environment"
            + (f" ({p.deployment.region})" if p.deployment.region else "")
            + ". Confirm the contractual and technical controls covering that "
              "environment."
        ),
    ),
    OperationalRule(
        rule_id="RESTRICTED_MATERIAL_HELD_BY_VENDOR",
        title="Vendor is custodian of restricted material",
        applies=lambda p, ip: (
            _is_restricted(ip) and p.residency.custodian is Custodian.VENDOR
        ),
        dimension=RiskDimension.SECURITY,
        level=RiskLevel.HIGH,
        describe=lambda p, ip: (
            f"The vendor holds inputs and outputs derived from: {ip.value}"
            + (f", located in {p.residency.location}" if p.residency.location else "")
            + ". Confirm deletion rights and breach obligations."
        ),
    ),
    OperationalRule(
        rule_id="MANDATORY_COLLECTION_OF_RESTRICTED_MATERIAL",
        title="Collection of restricted material cannot be declined",
        applies=lambda p, ip: (
            _is_restricted(ip) and p.collection.customer_data.is_mandatory
        ),
        dimension=RiskDimension.SECURITY,
        level=RiskLevel.CRITICAL,
        describe=lambda p, ip: (
            f"Customer data is collected with no opt-out while {ip.value} "
            f"is in scope. There is no configuration that prevents this "
            f"material leaving the production's control."
        ),
    ),
    OperationalRule(
        rule_id="INDEFINITE_RETENTION",
        title="No stated end to retention",
        applies=lambda p, ip: (
            p.collection.collects_anything and p.collection.is_indefinite
        ),
        dimension=RiskDimension.SECURITY,
        level=RiskLevel.MEDIUM,
        describe=lambda p, ip: (
            "Collected data is retained indefinitely. An approval granted "
            "today extends to material held after the production ends."
        ),
    ),
    OperationalRule(
        rule_id="VENDOR_CONTROLLED_UPDATES",
        title="Deployed version can change without customer action",
        applies=lambda p, ip: (
            p.deployment.update_control is UpdateControl.VENDOR
            and _is_restricted(ip)
        ),
        dimension=RiskDimension.FEASIBILITY,
        level=RiskLevel.MEDIUM,
        describe=lambda p, ip: (
            "Rollout is vendor-controlled, so the behaviour approved here may "
            "change without notice. Re-validation conditions should be stated "
            "as part of any approval."
        ),
    ),
    OperationalRule(
        rule_id="REFINEMENT_IN_VENDOR_ENVIRONMENT",
        title="Model refinement over customer material in a vendor environment",
        applies=lambda p, ip: (
            p.refinement.allowed
            and p.refinement.location is RefinementLocation.VENDOR_CONTROLLED
        ),
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        authority=Authority.BINDING_CONTRACT,
        source=AuthoritySource(
            body="Content licence and vendor terms",
            authority=Authority.BINDING_CONTRACT,
            citation="Training rights are commonly reserved separately",
        ),
        describe=lambda p, ip: (
            "Refinement occurs in a vendor-controlled environment. Whether "
            "customer material may be used to adapt a model, and what happens "
            "to the resulting weights, requires confirmation."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@dataclass
class OperationalProfile:
    """The full operational picture for a deployment."""
    deployment: Deployment = field(default_factory=Deployment)
    residency: DataResidency = field(default_factory=DataResidency)
    collection: DataCollection = field(default_factory=DataCollection)
    refinement: ModelRefinement = field(default_factory=ModelRefinement)
    notes: str = ""

    @property
    def is_fully_customer_controlled(self) -> bool:
        """True if nothing leaves the customer's control at any stage."""
        return (
            self.deployment.host.is_customer_controlled
            and self.residency.custodian is not Custodian.VENDOR
            and not self.collection.collects_anything
        )

    def derive_flags(
        self,
        ctx: "UseCaseContext",
        ip_class: Optional[IPClass] = None,
        rules: Optional[list[OperationalRule]] = None,
    ) -> list["RiskFlag"]:
        """Raise flags for every rule matching this profile.

        Pass ``ip_class`` so the rules can weigh operational facts against the
        sensitivity of what is being processed. Without it, rules that depend
        on sensitivity stay silent rather than assuming the worst — guessing
        would produce flags nobody can act on.
        """
        active = DEFAULT_OPERATIONAL_RULES if rules is None else rules
        added: list["RiskFlag"] = []
        for rule in active:
            if not rule.applies(self, ip_class):
                continue
            added.append(
                ctx.flag_risk(
                    dimension=rule.dimension,
                    level=rule.level,
                    description=rule.describe(self, ip_class),
                    authority=rule.authority,
                    source=rule.source,
                )
            )
        return added

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment": self.deployment.to_dict(),
            "residency": self.residency.to_dict(),
            "collection": self.collection.to_dict(),
            "refinement": self.refinement.to_dict(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationalProfile":
        return cls(
            deployment=Deployment.from_dict(data["deployment"]),
            residency=DataResidency.from_dict(data["residency"]),
            collection=DataCollection.from_dict(data["collection"]),
            refinement=ModelRefinement.from_dict(data["refinement"]),
            notes=data.get("notes", ""),
        )

    def summary(self) -> str:
        return "\n".join([
            f"Host:       {self.deployment.host.value}"
            + (f" ({self.deployment.region})" if self.deployment.region else ""),
            f"Updates:    {self.deployment.update_control.value}",
            f"Custodian:  {self.residency.custodian.value}"
            + (f" — {self.residency.location}" if self.residency.location else ""),
            f"Collection: customer data {self.collection.customer_data.value.lower()}; "
            f"metadata {self.collection.metadata.value.lower()}",
            f"Retention:  {self.collection.retention_period or '(not stated)'}",
            f"Refinement: {self.refinement.location.value}",
        ])

    def __str__(self) -> str:
        return self.summary()
