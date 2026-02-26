#!/usr/bin/env python3
"""
Portfolio dashboard example for the AI Use Case Context Framework.

Demonstrates registering multiple use cases into a GovernanceDashboard,
viewing aggregated risk, reviewer workloads, and per-dimension summaries.
"""

from ai_use_case_context import (
    UseCaseContext,
    RiskDimension,
    RiskLevel,
    GovernanceDashboard,
)


def main():
    dashboard = GovernanceDashboard()

    # --- Use Case 1: AI Upscaling ---
    uc1 = UseCaseContext(
        name="AI Super-Resolution — Archival Footage",
        workflow_phase="Element Regeneration",
        tags=["upscaling", "archival"],
    )
    uc1.flag_risk(
        RiskDimension.LEGAL_IP, RiskLevel.HIGH,
        "Actor likeness rights unclear for AI-modified footage",
    )
    uc1.flag_risk(
        RiskDimension.ETHICAL, RiskLevel.MEDIUM,
        "AI may alter skin tones or facial features",
    )
    dashboard.register(uc1)

    # --- Use Case 2: AI Color Grading ---
    uc2 = UseCaseContext(
        name="AI Color Grading — Season 2",
        workflow_phase="Post-Production",
        tags=["color", "grading"],
    )
    uc2.flag_risk(
        RiskDimension.TECHNICAL, RiskLevel.MEDIUM,
        "Color model not validated on HDR10+ pipeline",
    )
    dashboard.register(uc2)

    # --- Use Case 3: AI Script Analysis ---
    uc3 = UseCaseContext(
        name="AI Script Coverage Tool",
        workflow_phase="Pre-Production",
        tags=["script", "analysis", "NLP"],
    )
    uc3.flag_risk(
        RiskDimension.COMMS, RiskLevel.CRITICAL,
        "Writers' guild concerns about AI involvement in creative process",
    )
    uc3.flag_risk(
        RiskDimension.ETHICAL, RiskLevel.HIGH,
        "Potential bias in genre and demographic scoring",
    )
    dashboard.register(uc3)

    # --- Use Case 4: AI Background Generation ---
    uc4 = UseCaseContext(
        name="AI Background Generation — Pickup Shots",
        workflow_phase="Element Regeneration",
        tags=["generation", "backgrounds"],
    )
    uc4.flag_risk(
        RiskDimension.LEGAL_IP, RiskLevel.MEDIUM,
        "Training data provenance needs audit",
    )
    uc4.flag_risk(
        RiskDimension.TECHNICAL, RiskLevel.LOW,
        "Resolution adequate for mid-ground but not hero shots",
    )
    dashboard.register(uc4)

    # --- Print the portfolio summary ---
    print(dashboard.summary())
    print()

    # --- Show blocked use cases ---
    print("=" * 60)
    print("DETAILED BLOCKER REPORT")
    print("=" * 60)
    for uc in dashboard.blocked_use_cases():
        print(f"\n{uc.name}:")
        for blocker in uc.get_blockers():
            print(f"  {blocker}")
            print(f"    Reviewer: {blocker.reviewer}")

    # --- Show workflow phases ---
    print()
    print("=" * 60)
    print("BY WORKFLOW PHASE")
    print("=" * 60)
    for phase, use_cases in dashboard.by_workflow_phase().items():
        blocked_count = sum(1 for uc in use_cases if uc.is_blocked())
        print(f"\n{phase}: {len(use_cases)} use case(s), {blocked_count} blocked")
        for uc in use_cases:
            status = "BLOCKED" if uc.is_blocked() else "CLEAR"
            print(f"  [{status}] {uc.name}")


if __name__ == "__main__":
    main()
