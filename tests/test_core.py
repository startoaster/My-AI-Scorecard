"""Tests for the core governance classes."""

import pytest
from datetime import datetime

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    RiskFlag,
    UseCaseContext,
    DEFAULT_ROUTING,
)


# ---------------------------------------------------------------------------
# RiskFlag tests
# ---------------------------------------------------------------------------

class TestRiskFlag:
    def test_blocking_high_open(self):
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.HIGH,
            description="test",
        )
        assert flag.is_blocking is True

    def test_blocking_critical_open(self):
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.CRITICAL,
            description="test",
        )
        assert flag.is_blocking is True

    def test_not_blocking_medium(self):
        flag = RiskFlag(
            dimension=RiskDimension.BIAS,
            level=RiskLevel.MEDIUM,
            description="test",
        )
        assert flag.is_blocking is False

    def test_not_blocking_low(self):
        flag = RiskFlag(
            dimension=RiskDimension.SAFETY,
            level=RiskLevel.LOW,
            description="test",
        )
        assert flag.is_blocking is False

    def test_not_blocking_none(self):
        flag = RiskFlag(
            dimension=RiskDimension.FEASIBILITY,
            level=RiskLevel.NONE,
            description="test",
        )
        assert flag.is_blocking is False

    def test_not_blocking_after_resolve(self):
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.HIGH,
            description="test",
        )
        flag.resolve("Fixed")
        assert flag.is_blocking is False
        assert flag.status == ReviewStatus.RESOLVED
        assert flag.resolution_notes == "Fixed"
        assert flag.resolved_at is not None

    def test_not_blocking_after_accept(self):
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.CRITICAL,
            description="test",
        )
        flag.accept_risk("Risk acknowledged")
        assert flag.is_blocking is False
        assert flag.status == ReviewStatus.ACCEPTED

    def test_needs_review_medium_open(self):
        flag = RiskFlag(
            dimension=RiskDimension.BIAS,
            level=RiskLevel.MEDIUM,
            description="test",
        )
        assert flag.needs_review is True

    def test_needs_review_high_open(self):
        flag = RiskFlag(
            dimension=RiskDimension.BIAS,
            level=RiskLevel.HIGH,
            description="test",
        )
        assert flag.needs_review is True

    def test_no_review_needed_low(self):
        flag = RiskFlag(
            dimension=RiskDimension.SAFETY,
            level=RiskLevel.LOW,
            description="test",
        )
        assert flag.needs_review is False

    def test_no_review_needed_resolved(self):
        flag = RiskFlag(
            dimension=RiskDimension.BIAS,
            level=RiskLevel.MEDIUM,
            description="test",
            status=ReviewStatus.RESOLVED,
        )
        assert flag.needs_review is False

    def test_no_review_needed_in_review(self):
        flag = RiskFlag(
            dimension=RiskDimension.BIAS,
            level=RiskLevel.MEDIUM,
            description="test",
            status=ReviewStatus.IN_REVIEW,
        )
        assert flag.needs_review is False

    def test_begin_review(self):
        flag = RiskFlag(
            dimension=RiskDimension.FEASIBILITY,
            level=RiskLevel.MEDIUM,
            description="test",
        )
        flag.begin_review()
        assert flag.status == ReviewStatus.IN_REVIEW

    def test_mark_blocked(self):
        flag = RiskFlag(
            dimension=RiskDimension.FEASIBILITY,
            level=RiskLevel.HIGH,
            description="test",
        )
        flag.mark_blocked()
        assert flag.status == ReviewStatus.BLOCKED

    def test_str_representation(self):
        flag = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.HIGH,
            description="Actor likeness issue",
        )
        s = str(flag)
        assert "Legal / IP Ownership" in s
        assert "HIGH" in s
        assert "Actor likeness issue" in s
        assert "Open" in s

    def test_created_at_auto_set(self):
        before = datetime.now()
        flag = RiskFlag(
            dimension=RiskDimension.QUALITY,
            level=RiskLevel.LOW,
            description="test",
        )
        after = datetime.now()
        assert before <= flag.created_at <= after


# ---------------------------------------------------------------------------
# UseCaseContext tests
# ---------------------------------------------------------------------------

class TestUseCaseContext:
    def _make_context(self, **kwargs) -> UseCaseContext:
        defaults = {
            "name": "Test Use Case",
            "description": "A test",
            "workflow_phase": "Element Regeneration",
        }
        defaults.update(kwargs)
        return UseCaseContext(**defaults)

    def test_basic_creation(self):
        ctx = self._make_context()
        assert ctx.name == "Test Use Case"
        assert ctx.description == "A test"
        assert ctx.workflow_phase == "Element Regeneration"
        assert ctx.tags == []
        assert ctx.risk_flags == []
        assert ctx.is_blocked() is False

    def test_creation_with_tags(self):
        ctx = self._make_context(tags=["upscaling", "archival"])
        assert ctx.tags == ["upscaling", "archival"]

    def test_flag_risk_auto_routing(self):
        ctx = self._make_context()
        flag = ctx.flag_risk(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.HIGH,
            description="Actor likeness rights unclear",
        )
        assert flag.reviewer == "VP Legal / Business Affairs"
        assert len(ctx.risk_flags) == 1

    def test_flag_risk_manual_reviewer(self):
        ctx = self._make_context()
        flag = ctx.flag_risk(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.HIGH,
            description="test",
            reviewer="Custom Reviewer",
        )
        assert flag.reviewer == "Custom Reviewer"

    def test_flag_risk_unknown_route(self):
        ctx = self._make_context()
        flag = ctx.flag_risk(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.NONE,
            description="No risk",
        )
        assert flag.reviewer == "Unassigned"

    def test_custom_routing_table(self):
        custom_table = {
            (RiskDimension.LEGAL_IP, RiskLevel.HIGH): "My Custom Reviewer",
        }
        ctx = self._make_context(routing_table=custom_table)
        flag = ctx.flag_risk(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.HIGH,
            description="test",
        )
        assert flag.reviewer == "My Custom Reviewer"

    def test_is_blocked_with_high_flag(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "blocker")
        assert ctx.is_blocked() is True

    def test_is_blocked_with_critical_flag(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.CRITICAL, "hard block")
        assert ctx.is_blocked() is True

    def test_not_blocked_medium_only(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.MEDIUM, "needs review")
        assert ctx.is_blocked() is False

    def test_unblocked_after_resolve(self):
        ctx = self._make_context()
        flag = ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "blocker")
        assert ctx.is_blocked() is True
        flag.resolve("Fixed it")
        assert ctx.is_blocked() is False

    def test_unblocked_after_accept(self):
        ctx = self._make_context()
        flag = ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "blocker")
        flag.accept_risk("Acknowledged")
        assert ctx.is_blocked() is False

    def test_get_blockers(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "blocker1")
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.LOW, "info only")
        ctx.flag_risk(RiskDimension.SAFETY, RiskLevel.CRITICAL, "blocker2")
        blockers = ctx.get_blockers()
        assert len(blockers) == 2
        assert all(b.is_blocking for b in blockers)

    def test_get_pending_reviews(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.MEDIUM, "review me")
        ctx.flag_risk(RiskDimension.SAFETY, RiskLevel.LOW, "no review needed")
        ctx.flag_risk(RiskDimension.FEASIBILITY, RiskLevel.HIGH, "also review")
        pending = ctx.get_pending_reviews()
        assert len(pending) == 2

    def test_get_reviewers_needed(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "issue")
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.MEDIUM, "concern")
        reviewers = ctx.get_reviewers_needed()
        assert len(reviewers) >= 2
        assert "VP Legal / Business Affairs" in reviewers
        assert "Bias Review Board" in reviewers

    def test_risk_score(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "high legal")
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.LOW, "low legal")
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.MEDIUM, "medium bias")
        scores = ctx.risk_score()
        assert scores["Legal / IP Ownership"] == 3  # HIGH
        assert scores["Bias / Fairness"] == 2  # MEDIUM
        assert scores["Safety / Harmful Output"] == 0
        assert scores["Security / Model Integrity"] == 0
        assert scores["Technical Feasibility"] == 0
        assert scores["Output Quality"] == 0

    def test_risk_score_ignores_resolved(self):
        ctx = self._make_context()
        flag = ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "resolved")
        flag.resolve()
        scores = ctx.risk_score()
        assert scores["Legal / IP Ownership"] == 0

    def test_get_flags_by_dimension(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "legal1")
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.LOW, "bias1")
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.MEDIUM, "legal2")
        legal_flags = ctx.get_flags_by_dimension(RiskDimension.LEGAL_IP)
        assert len(legal_flags) == 2

    def test_get_flags_by_status(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "open1")
        flag = ctx.flag_risk(RiskDimension.BIAS, RiskLevel.MEDIUM, "resolved")
        flag.resolve()
        open_flags = ctx.get_flags_by_status(ReviewStatus.OPEN)
        assert len(open_flags) == 1

    def test_get_flags_by_level(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "h1")
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.HIGH, "h2")
        ctx.flag_risk(RiskDimension.SAFETY, RiskLevel.LOW, "l1")
        high_flags = ctx.get_flags_by_level(RiskLevel.HIGH)
        assert len(high_flags) == 2

    def test_max_risk_level(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.LOW, "low")
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.HIGH, "high")
        assert ctx.max_risk_level() == RiskLevel.HIGH

    def test_max_risk_level_empty(self):
        ctx = self._make_context()
        assert ctx.max_risk_level() == RiskLevel.NONE

    def test_max_risk_level_ignores_resolved(self):
        ctx = self._make_context()
        flag = ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.CRITICAL, "crit")
        flag.resolve()
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.LOW, "low")
        assert ctx.max_risk_level() == RiskLevel.LOW

    def test_summary_contains_key_info(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "blocker")
        summary = ctx.summary()
        assert "Test Use Case" in summary
        assert "BLOCKED" in summary
        assert "blocker" in summary

    def test_summary_clear_when_no_blockers(self):
        ctx = self._make_context()
        ctx.flag_risk(RiskDimension.QUALITY, RiskLevel.LOW, "minor")
        summary = ctx.summary()
        assert "CLEAR" in summary

    def test_repr(self):
        ctx = self._make_context()
        r = repr(ctx)
        assert "UseCaseContext" in r
        assert "Test Use Case" in r

    def test_str_equals_summary(self):
        ctx = self._make_context()
        assert str(ctx) == ctx.summary()


# ---------------------------------------------------------------------------
# DEFAULT_ROUTING coverage
# ---------------------------------------------------------------------------

class TestDefaultRouting:
    def test_all_dimensions_have_routing(self):
        """Every non-NONE dimension+level combo should have a routing entry."""
        for dim in RiskDimension:
            for level in RiskLevel:
                if level == RiskLevel.NONE:
                    continue
                assert (dim, level) in DEFAULT_ROUTING, (
                    f"Missing routing for ({dim.name}, {level.name})"
                )

    def test_routing_values_are_strings(self):
        for key, value in DEFAULT_ROUTING.items():
            assert isinstance(value, str)
            assert len(value) > 0
