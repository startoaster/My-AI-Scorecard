#!/usr/bin/env python3
"""
Example: Security governance with TPN, VFX, and enterprise dimensions.

Demonstrates:
  1. Applying TPN + VFX security profiles to production use cases
  2. Registering governance hooks (audit logger, compliance gate, notifications)
  3. Flagging security risks and watching hooks fire
  4. Running a compliance gate evaluation
  5. Querying the audit log
"""

from ai_use_case_context import (
    UseCaseContext,
    RiskLevel,
    GovernanceDashboard,
)
from ai_use_case_context.security import (
    TPN_CONTENT_SECURITY,
    TPN_DIGITAL_SECURITY,
    VFX_SECURE_TRANSFER,
    VFX_CLOUD_SECURITY,
    ENTERPRISE_ACCESS_CONTROL,
    security_profile,
    apply_security_profile,
)
from ai_use_case_context.governance_hooks import (
    GovernanceEvent,
    GovernanceEventType,
    GovernanceHook,
    AuditLogger,
    ComplianceGate,
    NotificationBridge,
    register_hook,
    emit_governance_event,
    clear_hooks,
)


def main():
    clear_hooks()

    # ------------------------------------------------------------------
    # 1. Set up governance hooks
    # ------------------------------------------------------------------

    # Audit logger — records every governance event
    audit = AuditLogger()
    register_hook(audit)

    # Notification bridge — prints HIGH/CRITICAL events to console
    def alert(event_dict):
        print(f"  [ALERT] {event_dict['event_type']}: {event_dict['description']}")

    bridge = NotificationBridge(
        callback=alert,
        event_filter=lambda e: e.level in ("HIGH", "CRITICAL"),
    )
    register_hook(bridge)

    # Compliance gate — blocks CRITICAL flags without a reviewer
    gate = ComplianceGate()

    @gate.criterion("reviewer_assigned")
    def check_reviewer(event):
        return event.metadata.get("reviewer", "") != ""

    @gate.criterion("no_critical_unresolved")
    def check_no_critical(event):
        return event.level != "CRITICAL"

    register_hook(gate)

    print("=== Governance hooks registered ===\n")

    # ------------------------------------------------------------------
    # 2. Build a combined TPN + VFX security profile
    # ------------------------------------------------------------------

    profile = security_profile("tpn", "vfx")
    print(f"Security profile: {profile}")
    print(f"  Dimensions: {len(profile.dimensions)}")
    print(f"  Routing entries: {len(profile.routing)}")
    print()

    # ------------------------------------------------------------------
    # 3. Create use cases and apply the security profile
    # ------------------------------------------------------------------

    uc1 = UseCaseContext(
        name="AI Dailies Review",
        description="AI-assisted shot review for dailies pipeline",
        workflow_phase="Review & Approval",
        tags=["dailies", "review", "AI"],
    )
    apply_security_profile(uc1, profile)

    uc2 = UseCaseContext(
        name="Cloud Render Burst",
        description="Burst rendering to cloud GPU farm for deadline shots",
        workflow_phase="Rendering",
        tags=["render", "cloud", "GPU"],
    )
    apply_security_profile(uc2, profile)

    # ------------------------------------------------------------------
    # 4. Flag security risks (hooks will fire)
    # ------------------------------------------------------------------

    print("--- Flagging security risks ---\n")

    flag1 = uc1.flag_risk(
        TPN_CONTENT_SECURITY, RiskLevel.HIGH,
        "Dailies footage not encrypted in transit",
    )
    emit_governance_event(GovernanceEvent(
        event_type=GovernanceEventType.FLAG_RAISED,
        use_case_name=uc1.name,
        dimension=TPN_CONTENT_SECURITY.name,
        level="HIGH",
        description=flag1.description,
        metadata={"reviewer": flag1.reviewer},
    ))

    flag2 = uc1.flag_risk(
        TPN_DIGITAL_SECURITY, RiskLevel.MEDIUM,
        "Review workstations on shared VLAN",
    )
    emit_governance_event(GovernanceEvent(
        event_type=GovernanceEventType.FLAG_RAISED,
        use_case_name=uc1.name,
        dimension=TPN_DIGITAL_SECURITY.name,
        level="MEDIUM",
        description=flag2.description,
        metadata={"reviewer": flag2.reviewer},
    ))

    flag3 = uc2.flag_risk(
        VFX_CLOUD_SECURITY, RiskLevel.CRITICAL,
        "Cloud render API keys exposed in build config",
    )
    emit_governance_event(GovernanceEvent(
        event_type=GovernanceEventType.FLAG_RAISED,
        use_case_name=uc2.name,
        dimension=VFX_CLOUD_SECURITY.name,
        level="CRITICAL",
        description=flag3.description,
        metadata={"reviewer": flag3.reviewer},
    ))

    flag4 = uc2.flag_risk(
        VFX_SECURE_TRANSFER, RiskLevel.HIGH,
        "Rendered frames transferred over unencrypted channel",
    )
    emit_governance_event(GovernanceEvent(
        event_type=GovernanceEventType.FLAG_RAISED,
        use_case_name=uc2.name,
        dimension=VFX_SECURE_TRANSFER.name,
        level="HIGH",
        description=flag4.description,
        metadata={"reviewer": flag4.reviewer},
    ))

    print()

    # ------------------------------------------------------------------
    # 5. Dashboard overview
    # ------------------------------------------------------------------

    dashboard = GovernanceDashboard()
    dashboard.register(uc1)
    dashboard.register(uc2)
    print(dashboard.summary())
    print()

    # ------------------------------------------------------------------
    # 6. Compliance gate evaluation
    # ------------------------------------------------------------------

    print("--- Compliance gate evaluation ---\n")

    # Check the CRITICAL cloud security flag
    check_event = GovernanceEvent(
        event_type=GovernanceEventType.COMPLIANCE_CHECK,
        use_case_name=uc2.name,
        dimension=VFX_CLOUD_SECURITY.name,
        level="CRITICAL",
        description="Cloud render API keys exposed",
        metadata={"reviewer": flag3.reviewer},
    )
    passed, failed = gate.evaluate(check_event)
    print(f"  Compliance check for '{uc2.name}' CRITICAL flag:")
    print(f"    Passed: {passed}")
    print(f"    Failed criteria: {failed}")
    print()

    # Check a flag that should pass
    ok_event = GovernanceEvent(
        event_type=GovernanceEventType.COMPLIANCE_CHECK,
        use_case_name=uc1.name,
        dimension=TPN_DIGITAL_SECURITY.name,
        level="MEDIUM",
        description="Shared VLAN",
        metadata={"reviewer": flag2.reviewer},
    )
    passed, failed = gate.evaluate(ok_event)
    print(f"  Compliance check for '{uc1.name}' MEDIUM flag:")
    print(f"    Passed: {passed}")
    print(f"    Failed criteria: {failed}")
    print()

    # ------------------------------------------------------------------
    # 7. Query the audit log
    # ------------------------------------------------------------------

    print("--- Audit log summary ---\n")
    print(f"  Total events logged: {len(audit.log)}")

    flag_raised = audit.query(event_type=GovernanceEventType.FLAG_RAISED)
    print(f"  FLAG_RAISED events: {len(flag_raised)}")

    compliance = audit.query(event_type=GovernanceEventType.COMPLIANCE_CHECK)
    print(f"  COMPLIANCE_CHECK events: {len(compliance)}")

    uc2_events = audit.query(use_case_name=uc2.name)
    print(f"  Events for '{uc2.name}': {len(uc2_events)}")

    print(f"\n  Notification bridge sent: {bridge.sent_count} alert(s)")
    print()

    clear_hooks()


if __name__ == "__main__":
    main()
