#!/usr/bin/env python3
"""
Escalation policy example for the AI Use Case Context Framework.

Demonstrates how stale risk flags get automatically escalated
based on configurable time thresholds.
"""

from datetime import datetime, timedelta

from ai_use_case_context import (
    UseCaseContext,
    RiskDimension,
    RiskLevel,
    EscalationPolicy,
)


def main():
    # Create a use case with some flags
    ctx = UseCaseContext(
        name="AI Upscaling — Archival Footage",
        workflow_phase="Element Regeneration",
    )

    # Flag some risks
    ctx.flag_risk(
        RiskDimension.LEGAL_IP, RiskLevel.MEDIUM,
        "Training data licensing needs review",
    )
    ctx.flag_risk(
        RiskDimension.BIAS, RiskLevel.LOW,
        "Minor concern about color accuracy bias",
    )
    ctx.flag_risk(
        RiskDimension.FEASIBILITY, RiskLevel.HIGH,
        "LoRA checkpoint not validated",
    )

    print("=== BEFORE ESCALATION ===")
    print(ctx.summary())
    print()

    # Simulate flags being created days ago
    ctx.risk_flags[0].created_at = datetime.now() - timedelta(days=5)  # MEDIUM, >3d
    ctx.risk_flags[1].created_at = datetime.now() - timedelta(days=10)  # LOW, >7d
    ctx.risk_flags[2].created_at = datetime.now() - timedelta(days=2)  # HIGH, >1d

    # Create an escalation policy and apply it
    policy = EscalationPolicy()
    results = policy.apply_escalations(ctx)

    print(f"=== {len(results)} ESCALATION(S) APPLIED ===")
    for result in results:
        print(f"  {result.message}")
    print()

    print("=== AFTER ESCALATION ===")
    print(ctx.summary())


if __name__ == "__main__":
    main()
