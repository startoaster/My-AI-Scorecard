#!/usr/bin/env python3
"""
Basic usage example for the AI Use Case Context Framework.

Demonstrates flagging risks, checking blockers, resolving issues,
and printing governance summaries.
"""

from ai_use_case_context import (
    UseCaseContext,
    RiskDimension,
    RiskLevel,
)


def main():
    # Create a use case
    ctx = UseCaseContext(
        name="AI Super-Resolution on Archival Footage",
        description=(
            "Apply AI upscaling to standard-definition archival footage "
            "to produce HD-quality output for streaming distribution."
        ),
        workflow_phase="Element Regeneration",
        tags=["upscaling", "archival", "streaming"],
    )

    # Flag some risks
    ctx.flag_risk(
        dimension=RiskDimension.LEGAL_IP,
        level=RiskLevel.HIGH,
        description="Actor likeness rights unclear for AI-modified footage",
    )

    ctx.flag_risk(
        dimension=RiskDimension.BIAS,
        level=RiskLevel.MEDIUM,
        description="AI may alter skin tones or facial features unintentionally",
    )

    ctx.flag_risk(
        dimension=RiskDimension.SECURITY,
        level=RiskLevel.LOW,
        description="Model checkpoint provenance needs verification",
    )

    ctx.flag_risk(
        dimension=RiskDimension.FEASIBILITY,
        level=RiskLevel.MEDIUM,
        description="ControlNet vs LoRA approach not yet validated for this content type",
    )

    # Print the summary
    print(ctx.summary())
    print()

    # Show it's blocked
    print(f"Blocked? {ctx.is_blocked()}")
    print(f"Blockers: {ctx.get_blockers()}")
    print(f"Risk scores: {ctx.risk_score()}")
    print()

    # Resolve the legal blocker
    legal_flag = ctx.get_blockers()[0]
    legal_flag.accept_risk(
        "Legal reviewed; proceeding under existing SAG-AFTRA agreement"
    )

    print("--- After resolving legal flag ---")
    print(ctx.summary())


if __name__ == "__main__":
    main()
