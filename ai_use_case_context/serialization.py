"""
Serialization utilities for the AI Use Case Context Framework.

Provides JSON/dict round-trip serialization for UseCaseContext objects,
enabling integration with external systems, databases, and APIs.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    RiskFlag,
    UseCaseContext,
    DEFAULT_ROUTING,
)

_DATETIME_FMT = "%Y-%m-%dT%H:%M:%S.%f"


def _serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.strftime(_DATETIME_FMT)


def _deserialize_datetime(s: Optional[str]) -> Optional[datetime]:
    if s is None:
        return None
    return datetime.strptime(s, _DATETIME_FMT)


def _flag_to_dict(flag: RiskFlag) -> dict[str, Any]:
    return {
        "dimension": flag.dimension.name,
        "level": flag.level.name,
        "description": flag.description,
        "reviewer": flag.reviewer,
        "status": flag.status.name,
        "resolution_notes": flag.resolution_notes,
        "created_at": _serialize_datetime(flag.created_at),
        "resolved_at": _serialize_datetime(flag.resolved_at),
    }


def _flag_from_dict(data: dict[str, Any]) -> RiskFlag:
    return RiskFlag(
        dimension=RiskDimension[data["dimension"]],
        level=RiskLevel[data["level"]],
        description=data["description"],
        reviewer=data.get("reviewer", ""),
        status=ReviewStatus[data["status"]],
        resolution_notes=data.get("resolution_notes", ""),
        created_at=_deserialize_datetime(data["created_at"]) or datetime.now(),
        resolved_at=_deserialize_datetime(data.get("resolved_at")),
    )


def to_dict(ctx: UseCaseContext) -> dict[str, Any]:
    """Serialize a UseCaseContext to a plain dict."""
    return {
        "name": ctx.name,
        "description": ctx.description,
        "workflow_phase": ctx.workflow_phase,
        "tags": list(ctx.tags),
        "created_at": _serialize_datetime(ctx.created_at),
        "risk_flags": [_flag_to_dict(f) for f in ctx.risk_flags],
    }


def from_dict(
    data: dict[str, Any],
    routing_table: Optional[dict] = None,
) -> UseCaseContext:
    """Deserialize a UseCaseContext from a plain dict."""
    ctx = UseCaseContext(
        name=data["name"],
        description=data.get("description", ""),
        workflow_phase=data.get("workflow_phase", ""),
        tags=data.get("tags", []),
        routing_table=routing_table,
    )
    ctx.created_at = _deserialize_datetime(data.get("created_at")) or datetime.now()
    for flag_data in data.get("risk_flags", []):
        ctx.risk_flags.append(_flag_from_dict(flag_data))
    return ctx


def to_json(ctx: UseCaseContext, indent: int = 2) -> str:
    """Serialize a UseCaseContext to a JSON string."""
    return json.dumps(to_dict(ctx), indent=indent)


def from_json(
    json_str: str,
    routing_table: Optional[dict] = None,
) -> UseCaseContext:
    """Deserialize a UseCaseContext from a JSON string."""
    return from_dict(json.loads(json_str), routing_table=routing_table)
