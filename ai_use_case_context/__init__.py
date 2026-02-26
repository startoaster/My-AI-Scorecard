"""
AI Use Case Context Framework
==============================
A generalizable governance model for AI-driven media production use cases.

Provides flag, route, and block capabilities across four risk dimensions:
  - Legal / IP Ownership
  - Ethical / Bias / Safety
  - Communications / Public Perception
  - Technical Feasibility / Quality

Plus configurable security dimensions aligned with industry standards:
  - **TPN** (Trusted Partner Network / MPA Content Security)
  - **VFX platform** security best practices
  - **Enterprise InfoSec** controls (ISO 27001, SOC 2, NIST-aligned)

And an open governance hook protocol for enterprise integrations:
  - Audit logging, compliance gates, notification bridges
  - Custom hook classes for SIEM, ticketing, and policy enforcement

Designed to integrate with PRD and taxonomy frameworks, including
MovieLabs OMC-aligned production workflows.
"""

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    RiskFlag,
    UseCaseContext,
    Dimension,
    DimensionType,
    custom_dimension,
    DEFAULT_ROUTING,
)
from ai_use_case_context.dashboard import GovernanceDashboard
from ai_use_case_context.escalation import EscalationPolicy, EscalationResult
from ai_use_case_context.serialization import (
    to_dict,
    from_dict,
    to_json,
    from_json,
)
from ai_use_case_context.security import (
    # TPN dimensions
    TPN_CONTENT_SECURITY,
    TPN_PHYSICAL_SECURITY,
    TPN_DIGITAL_SECURITY,
    TPN_ASSET_MANAGEMENT,
    TPN_INCIDENT_RESPONSE,
    TPN_PERSONNEL_SECURITY,
    TPN_DIMENSIONS,
    TPN_ROUTING,
    # VFX dimensions
    VFX_SECURE_TRANSFER,
    VFX_RENDER_ISOLATION,
    VFX_WORKSTATION_SECURITY,
    VFX_CLOUD_SECURITY,
    VFX_DATA_CLASSIFICATION,
    VFX_VENDOR_SECURITY,
    VFX_DIMENSIONS,
    VFX_ROUTING,
    # Enterprise dimensions
    ENTERPRISE_ACCESS_CONTROL,
    ENTERPRISE_AUDIT_TRAIL,
    ENTERPRISE_DATA_PRIVACY,
    ENTERPRISE_COMPLIANCE,
    ENTERPRISE_BUSINESS_CONTINUITY,
    ENTERPRISE_DIMENSIONS,
    ENTERPRISE_ROUTING,
    # Profile helpers
    SecurityProfile,
    security_profile,
    apply_security_profile,
    list_presets,
    register_preset,
    unregister_preset,
)
from ai_use_case_context.governance_hooks import (
    GovernanceEventType,
    GovernanceEvent,
    GovernanceHook,
    register_hook,
    unregister_hook,
    clear_hooks,
    registered_hooks,
    emit_governance_event,
    AuditLogger,
    ComplianceGate,
    NotificationBridge,
)

__all__ = [
    # Core governance
    "RiskDimension",
    "RiskLevel",
    "ReviewStatus",
    "RiskFlag",
    "UseCaseContext",
    "Dimension",
    "DimensionType",
    "custom_dimension",
    "DEFAULT_ROUTING",
    # Dashboard & escalation
    "GovernanceDashboard",
    "EscalationPolicy",
    "EscalationResult",
    # Serialization
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
    # Security presets — TPN
    "TPN_CONTENT_SECURITY",
    "TPN_PHYSICAL_SECURITY",
    "TPN_DIGITAL_SECURITY",
    "TPN_ASSET_MANAGEMENT",
    "TPN_INCIDENT_RESPONSE",
    "TPN_PERSONNEL_SECURITY",
    "TPN_DIMENSIONS",
    "TPN_ROUTING",
    # Security presets — VFX
    "VFX_SECURE_TRANSFER",
    "VFX_RENDER_ISOLATION",
    "VFX_WORKSTATION_SECURITY",
    "VFX_CLOUD_SECURITY",
    "VFX_DATA_CLASSIFICATION",
    "VFX_VENDOR_SECURITY",
    "VFX_DIMENSIONS",
    "VFX_ROUTING",
    # Security presets — Enterprise
    "ENTERPRISE_ACCESS_CONTROL",
    "ENTERPRISE_AUDIT_TRAIL",
    "ENTERPRISE_DATA_PRIVACY",
    "ENTERPRISE_COMPLIANCE",
    "ENTERPRISE_BUSINESS_CONTINUITY",
    "ENTERPRISE_DIMENSIONS",
    "ENTERPRISE_ROUTING",
    # Security profile helpers
    "SecurityProfile",
    "security_profile",
    "apply_security_profile",
    "list_presets",
    "register_preset",
    "unregister_preset",
    # Governance hooks
    "GovernanceEventType",
    "GovernanceEvent",
    "GovernanceHook",
    "register_hook",
    "unregister_hook",
    "clear_hooks",
    "registered_hooks",
    "emit_governance_event",
    "AuditLogger",
    "ComplianceGate",
    "NotificationBridge",
]

__version__ = "2.0.0"
