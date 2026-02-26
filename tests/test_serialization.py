"""Tests for serialization round-trips."""

import json
import pytest
from datetime import datetime

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    UseCaseContext,
)
from ai_use_case_context.serialization import (
    to_dict,
    from_dict,
    to_json,
    from_json,
)


class TestSerialization:
    def _make_context(self) -> UseCaseContext:
        ctx = UseCaseContext(
            name="AI Upscaling",
            description="Upscale archival footage",
            workflow_phase="Element Regeneration",
            tags=["upscaling", "archival"],
        )
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "Likeness rights")
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.MEDIUM, "Skin tone concern")
        # Resolve one flag
        ctx.risk_flags[1].resolve("Validated with test suite")
        return ctx

    def test_to_dict_structure(self):
        ctx = self._make_context()
        d = to_dict(ctx)
        assert d["name"] == "AI Upscaling"
        assert d["description"] == "Upscale archival footage"
        assert d["workflow_phase"] == "Element Regeneration"
        assert d["tags"] == ["upscaling", "archival"]
        assert len(d["risk_flags"]) == 2
        assert d["created_at"] is not None

    def test_flag_dict_structure(self):
        ctx = self._make_context()
        d = to_dict(ctx)
        flag = d["risk_flags"][0]
        assert flag["dimension"] == "LEGAL_IP"
        assert flag["level"] == "HIGH"
        assert flag["description"] == "Likeness rights"
        assert flag["status"] == "OPEN"

    def test_resolved_flag_dict(self):
        ctx = self._make_context()
        d = to_dict(ctx)
        flag = d["risk_flags"][1]
        assert flag["status"] == "RESOLVED"
        assert flag["resolution_notes"] == "Validated with test suite"
        assert flag["resolved_at"] is not None

    def test_round_trip_dict(self):
        ctx = self._make_context()
        d = to_dict(ctx)
        restored = from_dict(d)

        assert restored.name == ctx.name
        assert restored.description == ctx.description
        assert restored.workflow_phase == ctx.workflow_phase
        assert restored.tags == ctx.tags
        assert len(restored.risk_flags) == len(ctx.risk_flags)

        for orig, rest in zip(ctx.risk_flags, restored.risk_flags):
            assert rest.dimension == orig.dimension
            assert rest.level == orig.level
            assert rest.description == orig.description
            assert rest.reviewer == orig.reviewer
            assert rest.status == orig.status
            assert rest.resolution_notes == orig.resolution_notes

    def test_round_trip_json(self):
        ctx = self._make_context()
        json_str = to_json(ctx)
        restored = from_json(json_str)

        assert restored.name == ctx.name
        assert len(restored.risk_flags) == len(ctx.risk_flags)
        assert restored.is_blocked() == ctx.is_blocked()

    def test_json_is_valid_json(self):
        ctx = self._make_context()
        json_str = to_json(ctx)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_from_dict_minimal(self):
        d = {"name": "Minimal"}
        ctx = from_dict(d)
        assert ctx.name == "Minimal"
        assert ctx.description == ""
        assert ctx.risk_flags == []

    def test_from_dict_with_custom_routing(self):
        d = {"name": "Custom Route"}
        custom_routing = {
            (RiskDimension.LEGAL_IP, RiskLevel.HIGH): "Custom Reviewer",
        }
        ctx = from_dict(d, routing_table=custom_routing)
        flag = ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "test")
        assert flag.reviewer == "Custom Reviewer"

    def test_blocked_state_preserved(self):
        ctx = self._make_context()
        assert ctx.is_blocked() is True
        json_str = to_json(ctx)
        restored = from_json(json_str)
        assert restored.is_blocked() is True

    def test_empty_context_round_trip(self):
        ctx = UseCaseContext(name="Empty")
        json_str = to_json(ctx)
        restored = from_json(json_str)
        assert restored.name == "Empty"
        assert restored.risk_flags == []
        assert restored.is_blocked() is False
