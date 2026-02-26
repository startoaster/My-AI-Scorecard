"""
Escalation policies for stale and aging risk flags.

Provides EscalationPolicy to define thresholds and auto-escalation rules,
and check_escalations() to evaluate a UseCaseContext or GovernanceDashboard
for flags that have exceeded their review window.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from ai_use_case_context.core import (
    RiskLevel,
    ReviewStatus,
    RiskFlag,
    UseCaseContext,
)


@dataclass
class EscalationResult:
    """The result of checking a single flag against an escalation policy."""
    flag: RiskFlag
    use_case_name: str
    age: timedelta
    threshold: timedelta
    escalate_to_level: RiskLevel
    escalate_to_reviewer: str
    message: str


@dataclass
class EscalationRule:
    """
    A single escalation rule: if a flag at a given level remains unresolved
    for longer than `threshold`, escalate it to `escalate_to_level`.
    """
    from_level: RiskLevel
    threshold: timedelta
    escalate_to_level: RiskLevel
    escalate_to_reviewer: str = ""


class EscalationPolicy:
    """
    Define and enforce time-based escalation rules for risk flags.

    Default rules (can be overridden):
      - LOW flags open > 7 days  -> escalate to MEDIUM
      - MEDIUM flags open > 3 days -> escalate to HIGH
      - HIGH flags open > 1 day   -> escalate to CRITICAL
      - CRITICAL flags open > 4h  -> re-notify
    """

    DEFAULT_RULES = [
        EscalationRule(
            from_level=RiskLevel.LOW,
            threshold=timedelta(days=7),
            escalate_to_level=RiskLevel.MEDIUM,
        ),
        EscalationRule(
            from_level=RiskLevel.MEDIUM,
            threshold=timedelta(days=3),
            escalate_to_level=RiskLevel.HIGH,
        ),
        EscalationRule(
            from_level=RiskLevel.HIGH,
            threshold=timedelta(days=1),
            escalate_to_level=RiskLevel.CRITICAL,
        ),
        EscalationRule(
            from_level=RiskLevel.CRITICAL,
            threshold=timedelta(hours=4),
            escalate_to_level=RiskLevel.CRITICAL,
            escalate_to_reviewer="C-Suite Escalation",
        ),
    ]

    def __init__(
        self,
        rules: Optional[list[EscalationRule]] = None,
        routing_table: Optional[dict] = None,
    ):
        self.rules = rules if rules is not None else list(self.DEFAULT_RULES)
        self.routing_table = routing_table or {}

    def _get_rule(self, level: RiskLevel) -> Optional[EscalationRule]:
        """Find the escalation rule for a given risk level."""
        for rule in self.rules:
            if rule.from_level == level:
                return rule
        return None

    def check_flag(
        self,
        flag: RiskFlag,
        use_case_name: str = "",
        now: Optional[datetime] = None,
    ) -> Optional[EscalationResult]:
        """
        Check a single flag against escalation rules.
        Returns an EscalationResult if the flag should be escalated, else None.
        """
        if flag.status in (ReviewStatus.RESOLVED, ReviewStatus.ACCEPTED):
            return None

        now = now or datetime.now()
        age = now - flag.created_at
        rule = self._get_rule(flag.level)
        if rule is None:
            return None

        if age < rule.threshold:
            return None

        # Determine who to escalate to
        escalate_reviewer = rule.escalate_to_reviewer
        if not escalate_reviewer and self.routing_table:
            escalate_reviewer = self.routing_table.get(
                (flag.dimension, rule.escalate_to_level), ""
            )
        if not escalate_reviewer:
            escalate_reviewer = f"Escalated from {flag.reviewer}"

        return EscalationResult(
            flag=flag,
            use_case_name=use_case_name,
            age=age,
            threshold=rule.threshold,
            escalate_to_level=rule.escalate_to_level,
            escalate_to_reviewer=escalate_reviewer,
            message=(
                f"Flag '{flag.description}' ({flag.level.name}) has been open for "
                f"{age.days}d {age.seconds // 3600}h — exceeds threshold of "
                f"{rule.threshold.days}d {rule.threshold.seconds // 3600}h. "
                f"Escalating to {rule.escalate_to_level.name}."
            ),
        )

    def check_use_case(
        self,
        use_case: UseCaseContext,
        now: Optional[datetime] = None,
    ) -> list[EscalationResult]:
        """Check all flags on a use case for escalation."""
        results: list[EscalationResult] = []
        for flag in use_case.risk_flags:
            result = self.check_flag(flag, use_case.name, now)
            if result is not None:
                results.append(result)
        return results

    def apply_escalations(
        self,
        use_case: UseCaseContext,
        now: Optional[datetime] = None,
    ) -> list[EscalationResult]:
        """
        Check and apply escalations: update flag levels and reviewers in-place.
        Returns the list of escalations that were applied.
        """
        results = self.check_use_case(use_case, now)
        for result in results:
            result.flag.level = result.escalate_to_level
            if result.escalate_to_reviewer:
                result.flag.reviewer = result.escalate_to_reviewer
        return results
