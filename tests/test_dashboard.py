"""Tests for the GovernanceDashboard."""

import pytest

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    UseCaseContext,
)
from ai_use_case_context.dashboard import GovernanceDashboard, DimensionSummary


class TestGovernanceDashboard:
    def _make_dashboard(self) -> GovernanceDashboard:
        """Create a dashboard with a few test use cases."""
        db = GovernanceDashboard()

        uc1 = UseCaseContext(
            name="AI Upscaling",
            workflow_phase="Element Regeneration",
        )
        uc1.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "Likeness rights")
        uc1.flag_risk(RiskDimension.ETHICAL, RiskLevel.MEDIUM, "Skin tone concern")

        uc2 = UseCaseContext(
            name="AI Color Grading",
            workflow_phase="Post-Production",
        )
        uc2.flag_risk(RiskDimension.TECHNICAL, RiskLevel.LOW, "Needs validation")

        uc3 = UseCaseContext(
            name="AI Script Analysis",
            workflow_phase="Pre-Production",
        )
        uc3.flag_risk(RiskDimension.COMMS, RiskLevel.CRITICAL, "Public backlash risk")

        db.register(uc1)
        db.register(uc2)
        db.register(uc3)
        return db

    def test_register_and_use_cases(self):
        db = self._make_dashboard()
        assert len(db.use_cases) == 3

    def test_unregister(self):
        db = self._make_dashboard()
        removed = db.unregister("AI Color Grading")
        assert removed is not None
        assert removed.name == "AI Color Grading"
        assert len(db.use_cases) == 2

    def test_unregister_nonexistent(self):
        db = self._make_dashboard()
        assert db.unregister("Nonexistent") is None

    def test_all_flags(self):
        db = self._make_dashboard()
        flags = db.all_flags()
        assert len(flags) == 4  # 2 + 1 + 1
        # Each is a (name, flag) tuple
        names = [name for name, _ in flags]
        assert "AI Upscaling" in names
        assert "AI Color Grading" in names
        assert "AI Script Analysis" in names

    def test_blocked_use_cases(self):
        db = self._make_dashboard()
        blocked = db.blocked_use_cases()
        names = [uc.name for uc in blocked]
        assert "AI Upscaling" in names  # HIGH legal flag
        assert "AI Script Analysis" in names  # CRITICAL comms flag
        assert "AI Color Grading" not in names

    def test_clear_use_cases(self):
        db = self._make_dashboard()
        clear = db.clear_use_cases()
        names = [uc.name for uc in clear]
        assert "AI Color Grading" in names
        assert len(clear) == 1

    def test_portfolio_risk_scores(self):
        db = self._make_dashboard()
        scores = db.portfolio_risk_scores()
        assert "AI Upscaling" in scores
        assert scores["AI Upscaling"]["Legal / IP Ownership"] == 3

    def test_dimension_summary(self):
        db = self._make_dashboard()
        summary = db.dimension_summary(RiskDimension.LEGAL_IP)
        assert summary.total_flags == 1
        assert summary.open_flags == 1
        assert summary.blocking_flags == 1
        assert summary.max_level == RiskLevel.HIGH
        assert "AI Upscaling" in summary.affected_use_cases

    def test_dimension_summary_empty(self):
        db = GovernanceDashboard()
        summary = db.dimension_summary(RiskDimension.LEGAL_IP)
        assert summary.total_flags == 0
        assert summary.max_level == RiskLevel.NONE

    def test_all_dimension_summaries(self):
        db = self._make_dashboard()
        summaries = db.all_dimension_summaries()
        assert len(summaries) == 4
        assert RiskDimension.LEGAL_IP in summaries

    def test_reviewer_workload(self):
        db = self._make_dashboard()
        workload = db.reviewer_workload()
        # VP Legal should have work
        assert "VP Legal / Business Affairs" in workload
        # Ethics Review Board should have work
        assert "Ethics Review Board" in workload

    def test_by_workflow_phase(self):
        db = self._make_dashboard()
        phases = db.by_workflow_phase()
        assert "Element Regeneration" in phases
        assert "Post-Production" in phases
        assert "Pre-Production" in phases
        assert len(phases["Element Regeneration"]) == 1

    def test_summary_output(self):
        db = self._make_dashboard()
        summary = db.summary()
        assert "3 use case(s)" in summary
        assert "Blocked" in summary
        assert "Dimension overview" in summary

    def test_repr(self):
        db = self._make_dashboard()
        r = repr(db)
        assert "GovernanceDashboard" in r
        assert "use_cases=3" in r

    def test_str_equals_summary(self):
        db = self._make_dashboard()
        assert str(db) == db.summary()

    def test_empty_dashboard(self):
        db = GovernanceDashboard()
        assert db.use_cases == []
        assert db.blocked_use_cases() == []
        assert db.all_flags() == []
        summary = db.summary()
        assert "0 use case(s)" in summary
