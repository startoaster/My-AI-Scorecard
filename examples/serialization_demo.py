#!/usr/bin/env python3
"""
Serialization example for the AI Use Case Context Framework.

Demonstrates saving and loading UseCaseContext objects to/from JSON,
enabling integration with external systems and persistence.
"""

from ai_use_case_context import (
    UseCaseContext,
    RiskDimension,
    RiskLevel,
    to_json,
    from_json,
    to_dict,
)


def main():
    # Create and populate a use case
    ctx = UseCaseContext(
        name="AI Background Extension",
        description="Use generative AI to extend set backgrounds for wide shots",
        workflow_phase="Element Regeneration",
        tags=["generation", "backgrounds", "set-extension"],
    )

    ctx.flag_risk(
        RiskDimension.LEGAL_IP, RiskLevel.MEDIUM,
        "Generated content may resemble copyrighted locations",
    )
    ctx.flag_risk(
        RiskDimension.TECHNICAL, RiskLevel.LOW,
        "Output resolution capped at 4K",
    )

    # Resolve one flag
    ctx.risk_flags[1].resolve("4K is sufficient for distribution requirements")

    # Serialize to JSON
    json_str = to_json(ctx)
    print("=== SERIALIZED JSON ===")
    print(json_str)
    print()

    # Restore from JSON
    restored = from_json(json_str)
    print("=== RESTORED CONTEXT ===")
    print(restored.summary())
    print()

    # Verify round-trip integrity
    print("=== ROUND-TRIP VERIFICATION ===")
    print(f"  Name match: {restored.name == ctx.name}")
    print(f"  Flags match: {len(restored.risk_flags) == len(ctx.risk_flags)}")
    print(f"  Blocked match: {restored.is_blocked() == ctx.is_blocked()}")

    # Show dict format (useful for database storage)
    print()
    print("=== DICT FORMAT ===")
    d = to_dict(ctx)
    for key, value in d.items():
        if key != "risk_flags":
            print(f"  {key}: {value}")
    print(f"  risk_flags: [{len(d['risk_flags'])} flag(s)]")


if __name__ == "__main__":
    main()
