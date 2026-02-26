"""Tests for the escalation policy module."""

import pytest
from datetime import datetime, timedelta

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    RiskFlag,
    UseCaseContext,
)
from ai_use_case_context.escalation import (
    EscalationPolicy,
    EscalationRule,
    EscalationResult,
)


class TestEscalationPolicy:
    def test_no_escalation_fresh_flag(self):
        """A newly created flag should not trigger escalation."""
        policy = EscalationPolicy()
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.MEDIUM,
            description="test",
            created_at=datetime.now(),
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is None

    def test_escalation_stale_medium(self):
        """A MEDIUM flag open > 3 days should escalate to HIGH."""
        policy = EscalationPolicy()
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.MEDIUM,
            description="stale issue",
            created_at=datetime.now() - timedelta(days=4),
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is not None
        assert result.escalate_to_level == RiskLevel.HIGH

    def test_escalation_stale_low(self):
        """A LOW flag open > 7 days should escalate to MEDIUM."""
        policy = EscalationPolicy()
        flag = RiskFlag(
            dimension=RiskDimension.COMMS,
            level=RiskLevel.LOW,
            description="info flag",
            created_at=datetime.now() - timedelta(days=8),
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is not None
        assert result.escalate_to_level == RiskLevel.MEDIUM

    def test_escalation_stale_high(self):
        """A HIGH flag open > 1 day should escalate to CRITICAL."""
        policy = EscalationPolicy()
        flag = RiskFlag(
            dimension=RiskDimension.ETHICAL,
            level=RiskLevel.HIGH,
            description="serious issue",
            created_at=datetime.now() - timedelta(days=2),
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is not None
        assert result.escalate_to_level == RiskLevel.CRITICAL

    def test_escalation_stale_critical(self):
        """A CRITICAL flag open > 4 hours should re-escalate."""
        policy = EscalationPolicy()
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.CRITICAL,
            description="urgent",
            created_at=datetime.now() - timedelta(hours=5),
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is not None
        assert result.escalate_to_level == RiskLevel.CRITICAL
        assert "C-Suite Escalation" in result.escalate_to_reviewer

    def test_no_escalation_resolved(self):
        """Resolved flags should not trigger escalation."""
        policy = EscalationPolicy()
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.MEDIUM,
            description="resolved issue",
            created_at=datetime.now() - timedelta(days=10),
            status=ReviewStatus.RESOLVED,
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is None

    def test_no_escalation_accepted(self):
        """Accepted flags should not trigger escalation."""
        policy = EscalationPolicy()
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.HIGH,
            description="accepted risk",
            created_at=datetime.now() - timedelta(days=10),
            status=ReviewStatus.ACCEPTED,
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is None

    def test_no_escalation_none_level(self):
        """NONE-level flags have no escalation rule."""
        policy = EscalationPolicy()
        flag = RiskFlag(
            dimension=RiskDimension.TECHNICAL,
            level=RiskLevel.NONE,
            description="no issue",
            created_at=datetime.now() - timedelta(days=30),
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is None

    def test_check_use_case(self):
        """Check all flags on a use case at once."""
        policy = EscalationPolicy()
        ctx = UseCaseContext(name="test")
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.MEDIUM, "stale")
        ctx.flag_risk(RiskDimension.ETHICAL, RiskLevel.LOW, "fresh")

        # Make the first flag old
        ctx.risk_flags[0].created_at = datetime.now() - timedelta(days=5)

        results = policy.check_use_case(ctx)
        assert len(results) == 1
        assert results[0].flag.description == "stale"

    def test_apply_escalations(self):
        """Apply escalations should modify flags in place."""
        policy = EscalationPolicy()
        ctx = UseCaseContext(name="test")
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.MEDIUM, "stale")
        ctx.risk_flags[0].created_at = datetime.now() - timedelta(days=5)

        results = policy.apply_escalations(ctx)
        assert len(results) == 1
        # The flag level should now be HIGH
        assert ctx.risk_flags[0].level == RiskLevel.HIGH

    def test_custom_rules(self):
        """Custom escalation rules should override defaults."""
        custom_rules = [
            EscalationRule(
                from_level=RiskLevel.LOW,
                threshold=timedelta(hours=1),
                escalate_to_level=RiskLevel.CRITICAL,
                escalate_to_reviewer="CEO",
            ),
        ]
        policy = EscalationPolicy(rules=custom_rules)
        flag = RiskFlag(
            dimension=RiskDimension.COMMS,
            level=RiskLevel.LOW,
            description="test",
            created_at=datetime.now() - timedelta(hours=2),
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is not None
        assert result.escalate_to_level == RiskLevel.CRITICAL
        assert result.escalate_to_reviewer == "CEO"

    def test_escalation_result_message(self):
        """Escalation results should have a human-readable message."""
        policy = EscalationPolicy()
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.MEDIUM,
            description="test issue",
            created_at=datetime.now() - timedelta(days=4),
        )
        result = policy.check_flag(flag, "test_uc")
        assert result is not None
        assert "test issue" in result.message
        assert "MEDIUM" in result.message
        assert "HIGH" in result.message

    def test_with_explicit_now(self):
        """Passing an explicit 'now' parameter should work."""
        policy = EscalationPolicy()
        created = datetime(2025, 1, 1)
        check_time = datetime(2025, 1, 5)  # 4 days later
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.MEDIUM,
            description="test",
            created_at=created,
        )
        result = policy.check_flag(flag, "test_uc", now=check_time)
        assert result is not None
        assert result.age == timedelta(days=4)
