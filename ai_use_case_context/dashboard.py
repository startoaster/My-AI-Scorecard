"""
Governance Dashboard — portfolio-level aggregation across multiple use cases.

Provides a GovernanceDashboard that aggregates risk scores, blocker counts,
and reviewer workloads across all registered UseCaseContexts. Designed for
production-level oversight of AI governance across an entire project or
multi-project portfolio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    RiskFlag,
    UseCaseContext,
    DimensionType,
)


@dataclass
class DimensionSummary:
    """Aggregated stats for a single risk dimension across all use cases."""
    dimension: DimensionType
    total_flags: int = 0
    open_flags: int = 0
    blocking_flags: int = 0
    max_level: RiskLevel = RiskLevel.NONE
    affected_use_cases: list[str] = field(default_factory=list)


class GovernanceDashboard:
    """
    Portfolio-level governance dashboard.

    Register multiple UseCaseContexts and get aggregated views of risk,
    blockers, reviewer workloads, and per-dimension summaries.
    """

    def __init__(self):
        self._use_cases: dict[str, UseCaseContext] = {}

    # -- Registration ------------------------------------------------------

    def register(self, use_case: UseCaseContext) -> None:
        """Add a use case to the dashboard."""
        self._use_cases[use_case.name] = use_case

    def unregister(self, name: str) -> Optional[UseCaseContext]:
        """Remove a use case by name. Returns the removed context or None."""
        return self._use_cases.pop(name, None)

    @property
    def use_cases(self) -> list[UseCaseContext]:
        """All registered use cases."""
        return list(self._use_cases.values())

    # -- Aggregated queries ------------------------------------------------

    def all_flags(self) -> list[tuple[str, RiskFlag]]:
        """Return all flags across all use cases as (use_case_name, flag) tuples."""
        results: list[tuple[str, RiskFlag]] = []
        for uc in self._use_cases.values():
            for flag in uc.risk_flags:
                results.append((uc.name, flag))
        return results

    def blocked_use_cases(self) -> list[UseCaseContext]:
        """Return all use cases that are currently blocked."""
        return [uc for uc in self._use_cases.values() if uc.is_blocked()]

    def clear_use_cases(self) -> list[UseCaseContext]:
        """Return all use cases that are not blocked."""
        return [uc for uc in self._use_cases.values() if not uc.is_blocked()]

    def portfolio_risk_scores(self) -> dict[str, dict[str, int]]:
        """
        Return risk scores for every use case, keyed by use case name.
        Each value is a dict mapping dimension label -> max risk level value.
        """
        return {
            uc.name: uc.risk_score()
            for uc in self._use_cases.values()
        }

    # -- Per-dimension aggregation -----------------------------------------

    def all_dimensions(self) -> list[DimensionType]:
        """Return all dimensions across all use cases (built-in + custom)."""
        seen: dict[str, DimensionType] = {}
        for uc in self._use_cases.values():
            for dim in uc.dimensions():
                seen.setdefault(dim.name, dim)
        # Ensure built-ins are always present even with no use cases
        for dim in RiskDimension:
            seen.setdefault(dim.name, dim)
        return list(seen.values())

    def dimension_summary(self, dimension: DimensionType) -> DimensionSummary:
        """Aggregate stats for a single dimension across all use cases."""
        summary = DimensionSummary(dimension=dimension)
        for uc in self._use_cases.values():
            dim_flags = uc.get_flags_by_dimension(dimension)
            if not dim_flags:
                continue
            summary.affected_use_cases.append(uc.name)
            for flag in dim_flags:
                summary.total_flags += 1
                if flag.status not in (ReviewStatus.RESOLVED, ReviewStatus.ACCEPTED):
                    summary.open_flags += 1
                if flag.is_blocking:
                    summary.blocking_flags += 1
                if flag.level.value > summary.max_level.value:
                    summary.max_level = flag.level
        return summary

    def all_dimension_summaries(self) -> dict[DimensionType, DimensionSummary]:
        """Return DimensionSummary for every dimension (built-in + custom)."""
        return {dim: self.dimension_summary(dim) for dim in self.all_dimensions()}

    # -- Reviewer workload -------------------------------------------------

    def reviewer_workload(self) -> dict[str, list[tuple[str, RiskFlag]]]:
        """
        Map each reviewer to their assigned (use_case_name, flag) pairs
        that still need action (needs_review or is_blocking).
        """
        workload: dict[str, list[tuple[str, RiskFlag]]] = {}
        for uc in self._use_cases.values():
            for flag in uc.risk_flags:
                if flag.needs_review or flag.is_blocking:
                    workload.setdefault(flag.reviewer, []).append((uc.name, flag))
        return workload

    # -- Workflow phase view -----------------------------------------------

    def by_workflow_phase(self) -> dict[str, list[UseCaseContext]]:
        """Group use cases by their workflow phase."""
        phases: dict[str, list[UseCaseContext]] = {}
        for uc in self._use_cases.values():
            phase = uc.workflow_phase or "(unassigned)"
            phases.setdefault(phase, []).append(uc)
        return phases

    # -- Summary -----------------------------------------------------------

    def summary(self) -> str:
        """Human-readable portfolio summary."""
        total = len(self._use_cases)
        blocked = self.blocked_use_cases()
        all_flags = self.all_flags()
        blocking_count = sum(1 for _, f in all_flags if f.is_blocking)
        pending_count = sum(1 for _, f in all_flags if f.needs_review)

        lines = [
            f"Governance Dashboard — {total} use case(s)",
            f"  Blocked: {len(blocked)}  |  Clear: {total - len(blocked)}",
            f"  Total flags: {len(all_flags)}  |  Blocking: {blocking_count}  |  Pending review: {pending_count}",
            "",
        ]

        if blocked:
            lines.append("Blocked use cases:")
            for uc in blocked:
                blockers = uc.get_blockers()
                lines.append(f"  🚫 {uc.name} ({len(blockers)} blocker(s))")
            lines.append("")

        # Per-dimension overview
        lines.append("Dimension overview:")
        for dim in self.all_dimensions():
            ds = self.dimension_summary(dim)
            level_icon = {
                RiskLevel.NONE: "✅",
                RiskLevel.LOW: "🔵",
                RiskLevel.MEDIUM: "🟡",
                RiskLevel.HIGH: "🟠",
                RiskLevel.CRITICAL: "🔴",
            }.get(ds.max_level, "⚪")
            lines.append(
                f"  {level_icon} {dim.value}: "
                f"{ds.open_flags} open / {ds.total_flags} total"
            )

        # Reviewer workload
        workload = self.reviewer_workload()
        if workload:
            lines.append("")
            lines.append("Reviewer workload:")
            for reviewer, items in sorted(workload.items(), key=lambda x: -len(x[1])):
                lines.append(f"  {reviewer}: {len(items)} item(s)")

        return "\n".join(lines)

    def __str__(self):
        return self.summary()

    def __repr__(self):
        return (
            f"GovernanceDashboard(use_cases={len(self._use_cases)}, "
            f"blocked={len(self.blocked_use_cases())})"
        )
