"""Tests for the enterprise governance hook protocol."""

import pytest
from datetime import datetime, timedelta

from ai_use_case_context.governance_hooks import (
    GovernanceEventType,
    GovernanceEvent,
    GovernanceHook,
    register_hook,
    unregister_hook,
    clear_hooks,
    registered_hooks,
    emit_governance_event,
    AuditLogger,
    ComplianceGate,
    NotificationBridge,
)


@pytest.fixture(autouse=True)
def _clean_hooks():
    """Ensure no hooks leak between tests."""
    clear_hooks()
    yield
    clear_hooks()


# ---------------------------------------------------------------------------
# GovernanceEvent tests
# ---------------------------------------------------------------------------

class TestGovernanceEvent:
    def test_event_creation(self):
        event = GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RAISED,
            use_case_name="Test UC",
            dimension="TPN_CONTENT_SECURITY",
            level="HIGH",
            description="Encryption missing",
        )
        assert event.event_type == GovernanceEventType.FLAG_RAISED
        assert event.use_case_name == "Test UC"
        assert event.actor == "system"
        assert isinstance(event.timestamp, datetime)

    def test_event_to_dict(self):
        event = GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RESOLVED,
            use_case_name="Test",
            description="Fixed",
            metadata={"key": "value"},
        )
        d = event.to_dict()
        assert d["event_type"] == "flag_resolved"
        assert d["use_case_name"] == "Test"
        assert d["metadata"] == {"key": "value"}
        assert "timestamp" in d

    def test_event_defaults(self):
        event = GovernanceEvent(event_type=GovernanceEventType.CUSTOM)
        assert event.use_case_name == ""
        assert event.dimension == ""
        assert event.level == ""
        assert event.actor == "system"
        assert event.metadata == {}

    def test_all_event_types(self):
        # Verify all enum members exist
        assert len(GovernanceEventType) == 11
        assert GovernanceEventType.FLAG_RAISED.value == "flag_raised"
        assert GovernanceEventType.COMPLIANCE_GATE_PASSED.value == "compliance_gate_passed"
        assert GovernanceEventType.CUSTOM.value == "custom"


# ---------------------------------------------------------------------------
# Hook registration tests
# ---------------------------------------------------------------------------

class TestHookRegistry:
    def test_register_hook(self):
        hook = GovernanceHook()
        register_hook(hook)
        assert hook in registered_hooks()

    def test_register_duplicate_ignored(self):
        hook = GovernanceHook()
        register_hook(hook)
        register_hook(hook)
        assert len(registered_hooks()) == 1

    def test_unregister_hook(self):
        hook = GovernanceHook()
        register_hook(hook)
        assert unregister_hook(hook) is True
        assert hook not in registered_hooks()

    def test_unregister_nonexistent(self):
        hook = GovernanceHook()
        assert unregister_hook(hook) is False

    def test_clear_hooks(self):
        register_hook(GovernanceHook())
        register_hook(GovernanceHook())
        clear_hooks()
        assert len(registered_hooks()) == 0


# ---------------------------------------------------------------------------
# Event dispatch tests
# ---------------------------------------------------------------------------

class TestEventDispatch:
    def test_on_flag_raised(self):
        received = []

        class MyHook(GovernanceHook):
            def on_flag_raised(self, event):
                received.append(("specific", event))
            def on_event(self, event):
                received.append(("catch_all", event))

        register_hook(MyHook())
        event = GovernanceEvent(event_type=GovernanceEventType.FLAG_RAISED)
        emit_governance_event(event)
        assert len(received) == 2
        assert received[0][0] == "specific"
        assert received[1][0] == "catch_all"

    def test_on_flag_resolved(self):
        received = []

        class MyHook(GovernanceHook):
            def on_flag_resolved(self, event):
                received.append(event)

        register_hook(MyHook())
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_RESOLVED))
        assert len(received) == 1

    def test_on_flag_accepted(self):
        received = []

        class MyHook(GovernanceHook):
            def on_flag_accepted(self, event):
                received.append(event)

        register_hook(MyHook())
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_ACCEPTED))
        assert len(received) == 1

    def test_on_flag_escalated(self):
        received = []

        class MyHook(GovernanceHook):
            def on_flag_escalated(self, event):
                received.append(event)

        register_hook(MyHook())
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_ESCALATED))
        assert len(received) == 1

    def test_on_review_started(self):
        received = []

        class MyHook(GovernanceHook):
            def on_review_started(self, event):
                received.append(event)

        register_hook(MyHook())
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.REVIEW_STARTED))
        assert len(received) == 1

    def test_on_compliance_check(self):
        received = []

        class MyHook(GovernanceHook):
            def on_compliance_check(self, event):
                received.append(event)

        register_hook(MyHook())
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.COMPLIANCE_CHECK))
        assert len(received) == 1

    def test_on_security_profile_applied(self):
        received = []

        class MyHook(GovernanceHook):
            def on_security_profile_applied(self, event):
                received.append(event)

        register_hook(MyHook())
        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.SECURITY_PROFILE_APPLIED
        ))
        assert len(received) == 1

    def test_custom_event_goes_to_on_event_only(self):
        specific = []
        catch_all = []

        class MyHook(GovernanceHook):
            def on_flag_raised(self, event):
                specific.append(event)
            def on_event(self, event):
                catch_all.append(event)

        register_hook(MyHook())
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.CUSTOM))
        assert len(specific) == 0
        assert len(catch_all) == 1

    def test_multiple_hooks(self):
        counts = {"a": 0, "b": 0}

        class HookA(GovernanceHook):
            def on_event(self, event):
                counts["a"] += 1

        class HookB(GovernanceHook):
            def on_event(self, event):
                counts["b"] += 1

        register_hook(HookA())
        register_hook(HookB())
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_RAISED))
        assert counts["a"] == 1
        assert counts["b"] == 1


# ---------------------------------------------------------------------------
# AuditLogger tests
# ---------------------------------------------------------------------------

class TestAuditLogger:
    def test_logs_events(self):
        logger = AuditLogger()
        register_hook(logger)

        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RAISED,
            use_case_name="UC1",
            description="Test flag",
        ))
        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RESOLVED,
            use_case_name="UC1",
        ))

        assert len(logger.log) == 2
        assert logger.log[0]["event_type"] == "flag_raised"
        assert logger.log[1]["event_type"] == "flag_resolved"

    def test_custom_sink(self):
        external = []
        logger = AuditLogger(sink=lambda entry: external.append(entry))
        register_hook(logger)

        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RAISED,
        ))
        assert len(external) == 1
        assert external[0]["event_type"] == "flag_raised"

    def test_query_by_event_type(self):
        logger = AuditLogger()
        register_hook(logger)

        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_RAISED))
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_RESOLVED))
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_RAISED))

        results = logger.query(event_type=GovernanceEventType.FLAG_RAISED)
        assert len(results) == 2

    def test_query_by_use_case(self):
        logger = AuditLogger()
        register_hook(logger)

        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RAISED,
            use_case_name="UC1",
        ))
        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RAISED,
            use_case_name="UC2",
        ))

        results = logger.query(use_case_name="UC1")
        assert len(results) == 1

    def test_query_by_since(self):
        logger = AuditLogger()
        register_hook(logger)

        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_RAISED))

        future = datetime.now() + timedelta(hours=1)
        results = logger.query(since=future)
        assert len(results) == 0

    def test_query_no_filters(self):
        logger = AuditLogger()
        register_hook(logger)

        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_RAISED))
        assert len(logger.query()) == 1


# ---------------------------------------------------------------------------
# ComplianceGate tests
# ---------------------------------------------------------------------------

class TestComplianceGate:
    def test_all_criteria_pass(self):
        gate = ComplianceGate()
        gate.add_criterion("always_pass", lambda e: True)
        register_hook(gate)

        event = GovernanceEvent(event_type=GovernanceEventType.COMPLIANCE_CHECK)
        passed, failed = gate.evaluate(event)
        assert passed is True
        assert failed == []

    def test_criterion_fails(self):
        gate = ComplianceGate()
        gate.add_criterion("no_critical", lambda e: e.level != "CRITICAL")
        register_hook(gate)

        event = GovernanceEvent(
            event_type=GovernanceEventType.COMPLIANCE_CHECK,
            level="CRITICAL",
        )
        passed, failed = gate.evaluate(event)
        assert passed is False
        assert "no_critical" in failed

    def test_multiple_criteria(self):
        gate = ComplianceGate()
        gate.add_criterion("pass1", lambda e: True)
        gate.add_criterion("fail1", lambda e: False)
        gate.add_criterion("pass2", lambda e: True)
        register_hook(gate)

        event = GovernanceEvent(event_type=GovernanceEventType.COMPLIANCE_CHECK)
        passed, failed = gate.evaluate(event)
        assert passed is False
        assert failed == ["fail1"]

    def test_decorator_syntax(self):
        gate = ComplianceGate()

        @gate.criterion("decorated")
        def check(event):
            return event.level != "HIGH"

        event = GovernanceEvent(
            event_type=GovernanceEventType.COMPLIANCE_CHECK,
            level="HIGH",
        )
        passed, failed = gate.evaluate(event)
        assert passed is False
        assert "decorated" in failed

    def test_remove_criterion(self):
        gate = ComplianceGate()
        gate.add_criterion("temp", lambda e: False)
        assert gate.remove_criterion("temp") is True
        assert gate.remove_criterion("temp") is False

        event = GovernanceEvent(event_type=GovernanceEventType.COMPLIANCE_CHECK)
        passed, _ = gate.evaluate(event)
        assert passed is True  # No criteria = pass

    def test_criteria_names(self):
        gate = ComplianceGate()
        gate.add_criterion("a", lambda e: True)
        gate.add_criterion("b", lambda e: True)
        assert gate.criteria_names == ["a", "b"]

    def test_results_log(self):
        gate = ComplianceGate()
        gate.add_criterion("check", lambda e: True)
        register_hook(gate)

        event = GovernanceEvent(event_type=GovernanceEventType.COMPLIANCE_CHECK)
        gate.evaluate(event)
        assert len(gate.results_log) == 1
        assert gate.results_log[0]["passed"] is True

    def test_gate_emits_sub_events(self):
        gate = ComplianceGate()
        gate.add_criterion("check", lambda e: True)

        # Register both gate and a logger to catch sub-events
        logger = AuditLogger()
        register_hook(gate)
        register_hook(logger)

        event = GovernanceEvent(event_type=GovernanceEventType.COMPLIANCE_CHECK)
        gate.evaluate(event)

        # Logger should have caught the COMPLIANCE_GATE_PASSED sub-event
        gate_events = [
            e for e in logger.log
            if e["event_type"] == "compliance_gate_passed"
        ]
        assert len(gate_events) == 1

    def test_gate_emits_failure_event(self):
        gate = ComplianceGate()
        gate.add_criterion("fail", lambda e: False)

        logger = AuditLogger()
        register_hook(gate)
        register_hook(logger)

        event = GovernanceEvent(event_type=GovernanceEventType.COMPLIANCE_CHECK)
        gate.evaluate(event)

        gate_events = [
            e for e in logger.log
            if e["event_type"] == "compliance_gate_failed"
        ]
        assert len(gate_events) == 1


# ---------------------------------------------------------------------------
# NotificationBridge tests
# ---------------------------------------------------------------------------

class TestNotificationBridge:
    def test_sends_all_events(self):
        received = []
        bridge = NotificationBridge(callback=lambda d: received.append(d))
        register_hook(bridge)

        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RAISED,
            description="Test",
        ))
        assert len(received) == 1
        assert received[0]["description"] == "Test"
        assert bridge.sent_count == 1

    def test_filter_blocks_events(self):
        received = []
        bridge = NotificationBridge(
            callback=lambda d: received.append(d),
            event_filter=lambda e: e.level in ("HIGH", "CRITICAL"),
        )
        register_hook(bridge)

        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RAISED,
            level="LOW",
        ))
        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RAISED,
            level="HIGH",
        ))
        assert len(received) == 1
        assert received[0]["level"] == "HIGH"
        assert bridge.sent_count == 1

    def test_filter_passes_all(self):
        received = []
        bridge = NotificationBridge(
            callback=lambda d: received.append(d),
            event_filter=lambda e: True,
        )
        register_hook(bridge)

        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_RAISED))
        emit_governance_event(GovernanceEvent(event_type=GovernanceEventType.FLAG_RESOLVED))
        assert len(received) == 2
        assert bridge.sent_count == 2


# ---------------------------------------------------------------------------
# Custom hook subclass tests
# ---------------------------------------------------------------------------

class TestCustomHook:
    def test_custom_hook_subclass(self):
        events = []

        class SIEMHook(GovernanceHook):
            def on_flag_raised(self, event):
                events.append(("SIEM_ALERT", event.use_case_name))

            def on_flag_escalated(self, event):
                events.append(("SIEM_ESCALATION", event.use_case_name))

        register_hook(SIEMHook())

        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_RAISED,
            use_case_name="Pipeline A",
        ))
        emit_governance_event(GovernanceEvent(
            event_type=GovernanceEventType.FLAG_ESCALATED,
            use_case_name="Pipeline B",
        ))
        assert events == [
            ("SIEM_ALERT", "Pipeline A"),
            ("SIEM_ESCALATION", "Pipeline B"),
        ]

    def test_base_hook_noop(self):
        """Base GovernanceHook methods are all no-ops."""
        hook = GovernanceHook()
        event = GovernanceEvent(event_type=GovernanceEventType.FLAG_RAISED)
        # None of these should raise
        hook.on_flag_raised(event)
        hook.on_flag_resolved(event)
        hook.on_flag_accepted(event)
        hook.on_flag_escalated(event)
        hook.on_review_started(event)
        hook.on_compliance_check(event)
        hook.on_security_profile_applied(event)
        hook.on_event(event)
