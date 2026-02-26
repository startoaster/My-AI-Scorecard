"""
Enterprise governance hook protocol and built-in adapters.

Provides an open extension point for organizations to plug their own
InfoSec, compliance, and audit systems into the AI governance framework.

The core abstraction is :class:`GovernanceHook` — a base class whose methods
are called at key lifecycle moments (flag raised, resolved, escalated, etc.).
Register hook instances via :func:`register_hook` and the framework calls
them automatically.

Built-in adapters included for common patterns:

  - :class:`AuditLogger` — structured audit log with pluggable sinks
  - :class:`ComplianceGate` — blocks progression until compliance criteria met
  - :class:`NotificationBridge` — webhook / SIEM / messaging integration point

Usage::

    from ai_use_case_context.governance_hooks import (
        GovernanceHook, register_hook, AuditLogger, ComplianceGate,
    )

    # Use the built-in audit logger
    register_hook(AuditLogger())

    # Or write your own
    class SIEMHook(GovernanceHook):
        def on_flag_raised(self, event):
            send_to_siem(event)

    register_hook(SIEMHook())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

class GovernanceEventType(Enum):
    """Categories of governance lifecycle events."""
    FLAG_RAISED = "flag_raised"
    FLAG_RESOLVED = "flag_resolved"
    FLAG_ACCEPTED = "flag_accepted"
    FLAG_ESCALATED = "flag_escalated"
    REVIEW_STARTED = "review_started"
    COMPLIANCE_CHECK = "compliance_check"
    COMPLIANCE_GATE_PASSED = "compliance_gate_passed"
    COMPLIANCE_GATE_FAILED = "compliance_gate_failed"
    SECURITY_PROFILE_APPLIED = "security_profile_applied"
    AUDIT_QUERY = "audit_query"
    CUSTOM = "custom"


@dataclass
class GovernanceEvent:
    """A structured governance event passed to hooks.

    All hook callbacks receive a single ``GovernanceEvent`` instance,
    making it easy to add new fields without breaking existing hooks.

    Attributes:
        event_type: The category of event.
        use_case_name: Name of the affected use case (if applicable).
        dimension: Dimension name (if applicable).
        level: Risk level name (if applicable).
        description: Human-readable description of what happened.
        actor: Who or what triggered the event (user, system, policy).
        timestamp: When the event occurred.
        metadata: Arbitrary key-value pairs for extension.
    """
    event_type: GovernanceEventType
    use_case_name: str = ""
    dimension: str = ""
    level: str = ""
    description: str = ""
    actor: str = "system"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging, webhooks, or SIEM ingestion."""
        return {
            "event_type": self.event_type.value,
            "use_case_name": self.use_case_name,
            "dimension": self.dimension,
            "level": self.level,
            "description": self.description,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "metadata": dict(self.metadata),
        }


# ---------------------------------------------------------------------------
# Hook base class — the enterprise extension point
# ---------------------------------------------------------------------------

class GovernanceHook:
    """Base class for enterprise governance integrations.

    Override any of the ``on_*`` methods to react to governance events.
    All methods are no-ops by default, so subclasses only need to
    implement the events they care about.

    Lifecycle methods:
        on_flag_raised      — A new risk flag was created
        on_flag_resolved    — A flag was marked resolved
        on_flag_accepted    — A flag's risk was accepted
        on_flag_escalated   — A flag was auto-escalated by policy
        on_review_started   — A flag entered review
        on_compliance_check — A compliance evaluation was performed
        on_security_profile_applied — A security preset was applied
        on_event            — Catch-all for any event (including CUSTOM)

    The ``on_event`` method is always called for every event, in addition
    to the specific ``on_*`` method. This allows hooks that want to
    handle all events uniformly (e.g. audit loggers) to do so.
    """

    def on_flag_raised(self, event: GovernanceEvent) -> None:
        pass

    def on_flag_resolved(self, event: GovernanceEvent) -> None:
        pass

    def on_flag_accepted(self, event: GovernanceEvent) -> None:
        pass

    def on_flag_escalated(self, event: GovernanceEvent) -> None:
        pass

    def on_review_started(self, event: GovernanceEvent) -> None:
        pass

    def on_compliance_check(self, event: GovernanceEvent) -> None:
        pass

    def on_security_profile_applied(self, event: GovernanceEvent) -> None:
        pass

    def on_event(self, event: GovernanceEvent) -> None:
        """Catch-all handler called for every event type."""
        pass


# ---------------------------------------------------------------------------
# Hook registry
# ---------------------------------------------------------------------------

_hooks: list[GovernanceHook] = []


def register_hook(hook: GovernanceHook) -> None:
    """Register a governance hook to receive lifecycle events."""
    if hook not in _hooks:
        _hooks.append(hook)


def unregister_hook(hook: GovernanceHook) -> bool:
    """Remove a governance hook. Returns True if it was registered."""
    try:
        _hooks.remove(hook)
        return True
    except ValueError:
        return False


def clear_hooks() -> None:
    """Remove all registered governance hooks."""
    _hooks.clear()


def registered_hooks() -> list[GovernanceHook]:
    """Return a copy of the currently registered hooks."""
    return list(_hooks)


_DISPATCH: dict[GovernanceEventType, str] = {
    GovernanceEventType.FLAG_RAISED: "on_flag_raised",
    GovernanceEventType.FLAG_RESOLVED: "on_flag_resolved",
    GovernanceEventType.FLAG_ACCEPTED: "on_flag_accepted",
    GovernanceEventType.FLAG_ESCALATED: "on_flag_escalated",
    GovernanceEventType.REVIEW_STARTED: "on_review_started",
    GovernanceEventType.COMPLIANCE_CHECK: "on_compliance_check",
    GovernanceEventType.COMPLIANCE_GATE_PASSED: "on_compliance_check",
    GovernanceEventType.COMPLIANCE_GATE_FAILED: "on_compliance_check",
    GovernanceEventType.SECURITY_PROFILE_APPLIED: "on_security_profile_applied",
}


def emit_governance_event(event: GovernanceEvent) -> None:
    """Dispatch a governance event to all registered hooks.

    Calls the specific ``on_*`` method for the event type, then always
    calls ``on_event`` as a catch-all.
    """
    method_name = _DISPATCH.get(event.event_type)
    for hook in _hooks:
        if method_name:
            getattr(hook, method_name)(event)
        hook.on_event(event)


# ---------------------------------------------------------------------------
# Built-in adapters
# ---------------------------------------------------------------------------

class AuditLogger(GovernanceHook):
    """Structured audit logger that records all governance events.

    By default stores events in an in-memory list (``self.log``).
    Supply a custom ``sink`` callable to forward to external systems::

        def send_to_splunk(event_dict):
            requests.post(SPLUNK_URL, json=event_dict)

        logger = AuditLogger(sink=send_to_splunk)
    """

    def __init__(self, sink: Optional[Callable[[dict[str, Any]], None]] = None):
        self.log: list[dict[str, Any]] = []
        self._sink = sink

    def on_event(self, event: GovernanceEvent) -> None:
        entry = event.to_dict()
        self.log.append(entry)
        if self._sink is not None:
            self._sink(entry)

    def query(
        self,
        event_type: Optional[GovernanceEventType] = None,
        use_case_name: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Query the audit log with optional filters."""
        results = self.log
        if event_type is not None:
            results = [e for e in results if e["event_type"] == event_type.value]
        if use_case_name is not None:
            results = [e for e in results if e["use_case_name"] == use_case_name]
        if since is not None:
            cutoff = since.isoformat()
            results = [e for e in results if e["timestamp"] >= cutoff]
        return results


class ComplianceGate(GovernanceHook):
    """Policy enforcement gate that evaluates compliance criteria.

    Register criteria functions that inspect a governance event and
    return ``True`` (pass) or ``False`` (fail).  Call :meth:`evaluate`
    to run all criteria against an event and get a pass/fail result.

    Example::

        gate = ComplianceGate()

        @gate.criterion("no_critical_unresolved")
        def no_critical(event):
            return event.level != "CRITICAL"

        gate.evaluate(some_event)  # -> (True/False, [failed_names])
    """

    def __init__(self):
        self._criteria: dict[str, Callable[[GovernanceEvent], bool]] = {}
        self.results_log: list[dict[str, Any]] = []

    def criterion(
        self, name: str
    ) -> Callable[[Callable[[GovernanceEvent], bool]], Callable[[GovernanceEvent], bool]]:
        """Decorator to register a named compliance criterion."""
        def decorator(fn: Callable[[GovernanceEvent], bool]) -> Callable[[GovernanceEvent], bool]:
            self._criteria[name] = fn
            return fn
        return decorator

    def add_criterion(
        self, name: str, fn: Callable[[GovernanceEvent], bool]
    ) -> None:
        """Register a compliance criterion directly."""
        self._criteria[name] = fn

    def remove_criterion(self, name: str) -> bool:
        """Remove a criterion by name. Returns True if it existed."""
        return self._criteria.pop(name, None) is not None

    @property
    def criteria_names(self) -> list[str]:
        """Names of all registered criteria."""
        return list(self._criteria.keys())

    def evaluate(self, event: GovernanceEvent) -> tuple[bool, list[str]]:
        """Evaluate all criteria against an event.

        Returns:
            A tuple of (passed: bool, failed_criteria: list[str]).
        """
        failed: list[str] = []
        for name, fn in self._criteria.items():
            if not fn(event):
                failed.append(name)

        passed = len(failed) == 0
        result = {
            "event": event.to_dict(),
            "passed": passed,
            "failed_criteria": failed,
            "evaluated_at": datetime.now().isoformat(),
        }
        self.results_log.append(result)

        # Emit sub-event for compliance gate result
        gate_event = GovernanceEvent(
            event_type=(
                GovernanceEventType.COMPLIANCE_GATE_PASSED
                if passed
                else GovernanceEventType.COMPLIANCE_GATE_FAILED
            ),
            use_case_name=event.use_case_name,
            description=f"Compliance gate {'PASSED' if passed else 'FAILED'}: {failed or 'all criteria met'}",
            actor="compliance_gate",
            metadata={"source_event": event.event_type.value, "failed": failed},
        )
        emit_governance_event(gate_event)

        return passed, failed


class NotificationBridge(GovernanceHook):
    """Webhook / SIEM / messaging integration point.

    Calls a user-supplied function for every governance event,
    providing a clean integration point for enterprise notification
    systems (Slack, PagerDuty, Splunk, SIEM, email, etc.)::

        def slack_notify(event_dict):
            requests.post(SLACK_WEBHOOK, json={"text": event_dict["description"]})

        bridge = NotificationBridge(callback=slack_notify)

    Apply optional filters to control which events get forwarded::

        bridge = NotificationBridge(
            callback=slack_notify,
            event_filter=lambda e: e.level in ("HIGH", "CRITICAL"),
        )
    """

    def __init__(
        self,
        callback: Callable[[dict[str, Any]], None],
        event_filter: Optional[Callable[[GovernanceEvent], bool]] = None,
    ):
        self._callback = callback
        self._filter = event_filter
        self.sent_count: int = 0

    def on_event(self, event: GovernanceEvent) -> None:
        if self._filter is not None and not self._filter(event):
            return
        self._callback(event.to_dict())
        self.sent_count += 1
