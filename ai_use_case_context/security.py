"""
Security dimension presets aligned with industry standards.

Provides pre-built security dimension packs based on:
  - **TPN** (Trusted Partner Network / MPA Content Security)
  - **VFX platform** best practices for pipeline and facility security
  - **Enterprise InfoSec** controls (ISO 27001, SOC 2, NIST-aligned)

Each pack includes dimensions, a routing table, and helper functions
to apply them to ``UseCaseContext`` objects individually or in combination.

Usage::

    from ai_use_case_context.security import (
        TPN_DIMENSIONS, VFX_DIMENSIONS, ENTERPRISE_DIMENSIONS,
        security_profile, apply_security_profile,
    )

    # Combine packs into a single profile
    profile = security_profile("tpn", "vfx")

    # Apply to a use case (merges routing tables)
    ctx = UseCaseContext("AI Dailies Review", ...)
    apply_security_profile(ctx, profile)
"""

from __future__ import annotations

from typing import Optional

from ai_use_case_context.core import (
    Dimension,
    DimensionType,
    RiskLevel,
    UseCaseContext,
    custom_dimension,
)


# ---------------------------------------------------------------------------
# TPN (Trusted Partner Network) dimensions
# ---------------------------------------------------------------------------

TPN_CONTENT_SECURITY = custom_dimension(
    "TPN_CONTENT_SECURITY", "Content Security (TPN)"
)
TPN_PHYSICAL_SECURITY = custom_dimension(
    "TPN_PHYSICAL_SECURITY", "Physical Security (TPN)"
)
TPN_DIGITAL_SECURITY = custom_dimension(
    "TPN_DIGITAL_SECURITY", "Digital Security (TPN)"
)
TPN_ASSET_MANAGEMENT = custom_dimension(
    "TPN_ASSET_MANAGEMENT", "Asset Management (TPN)"
)
TPN_INCIDENT_RESPONSE = custom_dimension(
    "TPN_INCIDENT_RESPONSE", "Incident Response (TPN)"
)
TPN_PERSONNEL_SECURITY = custom_dimension(
    "TPN_PERSONNEL_SECURITY", "Personnel Security (TPN)"
)

TPN_DIMENSIONS: list[Dimension] = [
    TPN_CONTENT_SECURITY,
    TPN_PHYSICAL_SECURITY,
    TPN_DIGITAL_SECURITY,
    TPN_ASSET_MANAGEMENT,
    TPN_INCIDENT_RESPONSE,
    TPN_PERSONNEL_SECURITY,
]

TPN_ROUTING: dict[tuple[DimensionType, RiskLevel], str] = {
    # Content Security
    (TPN_CONTENT_SECURITY, RiskLevel.LOW): "Security Coordinator",
    (TPN_CONTENT_SECURITY, RiskLevel.MEDIUM): "Content Security Manager",
    (TPN_CONTENT_SECURITY, RiskLevel.HIGH): "VP Security / CISO",
    (TPN_CONTENT_SECURITY, RiskLevel.CRITICAL): "CISO + Studio Security Liaison",
    # Physical Security
    (TPN_PHYSICAL_SECURITY, RiskLevel.LOW): "Facility Manager",
    (TPN_PHYSICAL_SECURITY, RiskLevel.MEDIUM): "Physical Security Lead",
    (TPN_PHYSICAL_SECURITY, RiskLevel.HIGH): "VP Facilities / CISO",
    (TPN_PHYSICAL_SECURITY, RiskLevel.CRITICAL): "CISO + External Security Audit",
    # Digital Security
    (TPN_DIGITAL_SECURITY, RiskLevel.LOW): "IT Security Analyst",
    (TPN_DIGITAL_SECURITY, RiskLevel.MEDIUM): "IT Security Manager",
    (TPN_DIGITAL_SECURITY, RiskLevel.HIGH): "CISO / VP Engineering",
    (TPN_DIGITAL_SECURITY, RiskLevel.CRITICAL): "CISO + External Penetration Review",
    # Asset Management
    (TPN_ASSET_MANAGEMENT, RiskLevel.LOW): "Asset Coordinator",
    (TPN_ASSET_MANAGEMENT, RiskLevel.MEDIUM): "Asset Management Lead",
    (TPN_ASSET_MANAGEMENT, RiskLevel.HIGH): "VP Production Technology",
    (TPN_ASSET_MANAGEMENT, RiskLevel.CRITICAL): "CTO + Studio Asset Security",
    # Incident Response
    (TPN_INCIDENT_RESPONSE, RiskLevel.LOW): "SOC Analyst",
    (TPN_INCIDENT_RESPONSE, RiskLevel.MEDIUM): "Incident Response Lead",
    (TPN_INCIDENT_RESPONSE, RiskLevel.HIGH): "CISO / VP Security",
    (TPN_INCIDENT_RESPONSE, RiskLevel.CRITICAL): "CISO + Legal + Crisis Management",
    # Personnel Security
    (TPN_PERSONNEL_SECURITY, RiskLevel.LOW): "HR Security Coordinator",
    (TPN_PERSONNEL_SECURITY, RiskLevel.MEDIUM): "HR Director + Security Lead",
    (TPN_PERSONNEL_SECURITY, RiskLevel.HIGH): "VP HR + CISO",
    (TPN_PERSONNEL_SECURITY, RiskLevel.CRITICAL): "C-Suite + External Investigation",
}


# ---------------------------------------------------------------------------
# VFX platform security dimensions
# ---------------------------------------------------------------------------

VFX_SECURE_TRANSFER = custom_dimension(
    "VFX_SECURE_TRANSFER", "Secure Transfer / Delivery"
)
VFX_RENDER_ISOLATION = custom_dimension(
    "VFX_RENDER_ISOLATION", "Render Farm Isolation"
)
VFX_WORKSTATION_SECURITY = custom_dimension(
    "VFX_WORKSTATION_SECURITY", "Workstation Security"
)
VFX_CLOUD_SECURITY = custom_dimension(
    "VFX_CLOUD_SECURITY", "Cloud / Hybrid Security"
)
VFX_DATA_CLASSIFICATION = custom_dimension(
    "VFX_DATA_CLASSIFICATION", "Data Classification & Handling"
)
VFX_VENDOR_SECURITY = custom_dimension(
    "VFX_VENDOR_SECURITY", "Third-Party Vendor Security"
)

VFX_DIMENSIONS: list[Dimension] = [
    VFX_SECURE_TRANSFER,
    VFX_RENDER_ISOLATION,
    VFX_WORKSTATION_SECURITY,
    VFX_CLOUD_SECURITY,
    VFX_DATA_CLASSIFICATION,
    VFX_VENDOR_SECURITY,
]

VFX_ROUTING: dict[tuple[DimensionType, RiskLevel], str] = {
    # Secure Transfer
    (VFX_SECURE_TRANSFER, RiskLevel.LOW): "Pipeline TD",
    (VFX_SECURE_TRANSFER, RiskLevel.MEDIUM): "Pipeline Supervisor",
    (VFX_SECURE_TRANSFER, RiskLevel.HIGH): "Head of Technology / CISO",
    (VFX_SECURE_TRANSFER, RiskLevel.CRITICAL): "CTO + Studio Delivery Security",
    # Render Farm Isolation
    (VFX_RENDER_ISOLATION, RiskLevel.LOW): "Render Wrangler",
    (VFX_RENDER_ISOLATION, RiskLevel.MEDIUM): "Systems Administrator",
    (VFX_RENDER_ISOLATION, RiskLevel.HIGH): "VP Technology / CISO",
    (VFX_RENDER_ISOLATION, RiskLevel.CRITICAL): "CTO + External Infrastructure Audit",
    # Workstation Security
    (VFX_WORKSTATION_SECURITY, RiskLevel.LOW): "IT Support Lead",
    (VFX_WORKSTATION_SECURITY, RiskLevel.MEDIUM): "IT Security Manager",
    (VFX_WORKSTATION_SECURITY, RiskLevel.HIGH): "CISO / VP Technology",
    (VFX_WORKSTATION_SECURITY, RiskLevel.CRITICAL): "CISO + Endpoint Security Review",
    # Cloud / Hybrid Security
    (VFX_CLOUD_SECURITY, RiskLevel.LOW): "Cloud Operations Engineer",
    (VFX_CLOUD_SECURITY, RiskLevel.MEDIUM): "Cloud Security Architect",
    (VFX_CLOUD_SECURITY, RiskLevel.HIGH): "VP Cloud Infrastructure / CISO",
    (VFX_CLOUD_SECURITY, RiskLevel.CRITICAL): "CTO + External Cloud Audit",
    # Data Classification
    (VFX_DATA_CLASSIFICATION, RiskLevel.LOW): "Data Steward",
    (VFX_DATA_CLASSIFICATION, RiskLevel.MEDIUM): "Data Governance Lead",
    (VFX_DATA_CLASSIFICATION, RiskLevel.HIGH): "CISO / VP Data Governance",
    (VFX_DATA_CLASSIFICATION, RiskLevel.CRITICAL): "CISO + Legal + Studio Compliance",
    # Vendor Security
    (VFX_VENDOR_SECURITY, RiskLevel.LOW): "Vendor Manager",
    (VFX_VENDOR_SECURITY, RiskLevel.MEDIUM): "Procurement Security Lead",
    (VFX_VENDOR_SECURITY, RiskLevel.HIGH): "VP Procurement + CISO",
    (VFX_VENDOR_SECURITY, RiskLevel.CRITICAL): "C-Suite + External Vendor Audit",
}


# ---------------------------------------------------------------------------
# Enterprise governance / InfoSec dimensions
# ---------------------------------------------------------------------------

ENTERPRISE_ACCESS_CONTROL = custom_dimension(
    "ENTERPRISE_ACCESS_CONTROL", "Access Control (IAM)"
)
ENTERPRISE_AUDIT_TRAIL = custom_dimension(
    "ENTERPRISE_AUDIT_TRAIL", "Audit Trail / Logging"
)
ENTERPRISE_DATA_PRIVACY = custom_dimension(
    "ENTERPRISE_DATA_PRIVACY", "Data Privacy (GDPR/CCPA)"
)
ENTERPRISE_COMPLIANCE = custom_dimension(
    "ENTERPRISE_COMPLIANCE", "Regulatory Compliance"
)
ENTERPRISE_BUSINESS_CONTINUITY = custom_dimension(
    "ENTERPRISE_BUSINESS_CONTINUITY", "Business Continuity / DR"
)

ENTERPRISE_DIMENSIONS: list[Dimension] = [
    ENTERPRISE_ACCESS_CONTROL,
    ENTERPRISE_AUDIT_TRAIL,
    ENTERPRISE_DATA_PRIVACY,
    ENTERPRISE_COMPLIANCE,
    ENTERPRISE_BUSINESS_CONTINUITY,
]

ENTERPRISE_ROUTING: dict[tuple[DimensionType, RiskLevel], str] = {
    # Access Control
    (ENTERPRISE_ACCESS_CONTROL, RiskLevel.LOW): "IAM Administrator",
    (ENTERPRISE_ACCESS_CONTROL, RiskLevel.MEDIUM): "IAM Security Lead",
    (ENTERPRISE_ACCESS_CONTROL, RiskLevel.HIGH): "CISO / VP Security",
    (ENTERPRISE_ACCESS_CONTROL, RiskLevel.CRITICAL): "CISO + External Identity Audit",
    # Audit Trail
    (ENTERPRISE_AUDIT_TRAIL, RiskLevel.LOW): "Compliance Analyst",
    (ENTERPRISE_AUDIT_TRAIL, RiskLevel.MEDIUM): "Compliance Manager",
    (ENTERPRISE_AUDIT_TRAIL, RiskLevel.HIGH): "VP Compliance / CISO",
    (ENTERPRISE_AUDIT_TRAIL, RiskLevel.CRITICAL): "CISO + External Auditor",
    # Data Privacy
    (ENTERPRISE_DATA_PRIVACY, RiskLevel.LOW): "Privacy Analyst",
    (ENTERPRISE_DATA_PRIVACY, RiskLevel.MEDIUM): "Data Protection Officer",
    (ENTERPRISE_DATA_PRIVACY, RiskLevel.HIGH): "DPO + Legal Counsel",
    (ENTERPRISE_DATA_PRIVACY, RiskLevel.CRITICAL): "DPO + General Counsel + C-Suite",
    # Regulatory Compliance
    (ENTERPRISE_COMPLIANCE, RiskLevel.LOW): "Compliance Analyst",
    (ENTERPRISE_COMPLIANCE, RiskLevel.MEDIUM): "Compliance Officer",
    (ENTERPRISE_COMPLIANCE, RiskLevel.HIGH): "VP Compliance + Legal",
    (ENTERPRISE_COMPLIANCE, RiskLevel.CRITICAL): "General Counsel + Board Audit Committee",
    # Business Continuity
    (ENTERPRISE_BUSINESS_CONTINUITY, RiskLevel.LOW): "BC Coordinator",
    (ENTERPRISE_BUSINESS_CONTINUITY, RiskLevel.MEDIUM): "BC Manager",
    (ENTERPRISE_BUSINESS_CONTINUITY, RiskLevel.HIGH): "VP Operations / CTO",
    (ENTERPRISE_BUSINESS_CONTINUITY, RiskLevel.CRITICAL): "C-Suite + External DR Review",
}


# ---------------------------------------------------------------------------
# Preset registry
# ---------------------------------------------------------------------------

_PRESETS: dict[str, tuple[list[Dimension], dict]] = {
    "tpn": (TPN_DIMENSIONS, TPN_ROUTING),
    "vfx": (VFX_DIMENSIONS, VFX_ROUTING),
    "enterprise": (ENTERPRISE_DIMENSIONS, ENTERPRISE_ROUTING),
}


def list_presets() -> list[str]:
    """Return the names of all registered security presets."""
    return list(_PRESETS.keys())


def register_preset(
    name: str,
    dimensions: list[Dimension],
    routing: dict[tuple[DimensionType, RiskLevel], str],
) -> None:
    """Register a custom security preset pack.

    This is the extension point for organizations to add their own
    security dimension packs alongside the built-in TPN / VFX / Enterprise
    presets::

        register_preset("studio_custom", MY_DIMS, MY_ROUTING)
        profile = security_profile("tpn", "studio_custom")
    """
    _PRESETS[name] = (dimensions, routing)


def unregister_preset(name: str) -> bool:
    """Remove a registered preset. Returns True if it existed."""
    return _PRESETS.pop(name, None) is not None


# ---------------------------------------------------------------------------
# SecurityProfile — composable bundle of dimensions + routing
# ---------------------------------------------------------------------------

class SecurityProfile:
    """A composable bundle of security dimensions and routing rules.

    Created by :func:`security_profile` or assembled manually.  Can be
    applied to any :class:`UseCaseContext` to extend its routing table
    with security-specific reviewer assignments.

    Attributes:
        dimensions: Combined list of security dimensions.
        routing:    Merged routing table mapping (dimension, level) -> reviewer.
        presets:    Names of presets this profile was built from.
    """

    def __init__(
        self,
        dimensions: Optional[list[Dimension]] = None,
        routing: Optional[dict[tuple[DimensionType, RiskLevel], str]] = None,
        presets: Optional[list[str]] = None,
    ):
        self.dimensions: list[Dimension] = dimensions or []
        self.routing: dict[tuple[DimensionType, RiskLevel], str] = routing or {}
        self.presets: list[str] = presets or []

    def merge(self, other: SecurityProfile) -> SecurityProfile:
        """Return a new profile that combines both profiles."""
        seen_names: set[str] = set()
        merged_dims: list[Dimension] = []
        for dim in self.dimensions + other.dimensions:
            if dim.name not in seen_names:
                seen_names.add(dim.name)
                merged_dims.append(dim)
        merged_routing = {**self.routing, **other.routing}
        merged_presets = list(dict.fromkeys(self.presets + other.presets))
        return SecurityProfile(merged_dims, merged_routing, merged_presets)

    def __repr__(self) -> str:
        return (
            f"SecurityProfile(dimensions={len(self.dimensions)}, "
            f"presets={self.presets!r})"
        )


def security_profile(*preset_names: str) -> SecurityProfile:
    """Build a :class:`SecurityProfile` by combining one or more preset packs.

    Example::

        profile = security_profile("tpn", "vfx")
        # -> SecurityProfile with 12 dimensions + merged routing

    Raises ``KeyError`` if a preset name is not recognized.
    """
    profile = SecurityProfile()
    for name in preset_names:
        key = name.lower()
        if key not in _PRESETS:
            raise KeyError(
                f"Unknown security preset {name!r}. "
                f"Available: {list(_PRESETS.keys())}"
            )
        dims, routing = _PRESETS[key]
        other = SecurityProfile(list(dims), dict(routing), [key])
        profile = profile.merge(other)
    return profile


def apply_security_profile(
    ctx: UseCaseContext,
    profile: SecurityProfile,
) -> None:
    """Apply a :class:`SecurityProfile` to a use case.

    Merges the profile's routing table into the context's existing routing
    table (profile entries take precedence for overlapping keys).
    """
    ctx.routing_table = {**ctx.routing_table, **profile.routing}
