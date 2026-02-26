"""
AI Use Case Context Framework
==============================
A generalizable governance model for AI-driven media production use cases.

Provides flag, route, and block capabilities across four risk dimensions:
  - Legal / IP Ownership
  - Ethical / Bias / Safety
  - Communications / Public Perception
  - Technical Feasibility / Quality

Designed to integrate with PRD and taxonomy frameworks, including
MovieLabs OMC-aligned production workflows.
"""

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    RiskFlag,
    UseCaseContext,
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

__all__ = [
    "RiskDimension",
    "RiskLevel",
    "ReviewStatus",
    "RiskFlag",
    "UseCaseContext",
    "DEFAULT_ROUTING",
    "GovernanceDashboard",
    "EscalationPolicy",
    "EscalationResult",
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
]

__version__ = "1.0.0"
