"""Tests for the web dashboard."""

import pytest
from ai_use_case_context.web import (
    create_app, _dashboard, _hooks,
    on, off, get_dashboard, set_dashboard,
    get_escalation_policy, set_escalation_policy,
)
from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    UseCaseContext,
)
from ai_use_case_context.dashboard import GovernanceDashboard
from ai_use_case_context.escalation import EscalationPolicy


@pytest.fixture()
def client():
    """Create a test client and clear dashboard state between tests."""
    app = create_app()
    app.config["TESTING"] = True
    _dashboard._use_cases.clear()
    with app.test_client() as c:
        yield c
    _dashboard._use_cases.clear()


# -- Page loading ----------------------------------------------------------


class TestPageLoading:
    def test_dashboard_empty(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert b"Portfolio Dashboard" in r.data
        assert b"No use cases registered" in r.data

    def test_scores_empty(self, client):
        r = client.get("/scores")
        assert r.status_code == 200
        assert b"Score Reports" in r.data

    def test_reviewers_empty(self, client):
        r = client.get("/reviewers")
        assert r.status_code == 200
        assert b"Reviewer Workload" in r.data
        assert b"No pending reviews" in r.data

    def test_add_use_case_form(self, client):
        r = client.get("/add-use-case")
        assert r.status_code == 200
        assert b"Add Use Case" in r.data

    def test_nonexistent_use_case(self, client):
        r = client.get("/use-case/nope")
        assert r.status_code == 200
        assert b"not found" in r.data.lower()


# -- Seed demo data --------------------------------------------------------


class TestSeedData:
    def test_seed_loads_data(self, client):
        r = client.get("/seed")
        assert r.status_code == 200
        assert b"Demo Data Seeded" in r.data
        assert len(_dashboard.use_cases) == 5

    def test_seed_then_dashboard(self, client):
        client.get("/seed")
        r = client.get("/")
        assert b"AI Upscaling" in r.data
        assert b"AI Voice Synthesis" in r.data
        assert b"BLOCKED" in r.data

    def test_seed_then_scores(self, client):
        client.get("/seed")
        r = client.get("/scores")
        assert b"Composite Risk Score" in r.data

    def test_seed_then_reviewers(self, client):
        client.get("/seed")
        r = client.get("/reviewers")
        # There should be several reviewers with pending work
        assert b"item" in r.data

    def test_seed_replaces_previous(self, client):
        client.get("/seed")
        assert len(_dashboard.use_cases) == 5
        client.get("/seed")
        assert len(_dashboard.use_cases) == 5


# -- Add use case ----------------------------------------------------------


class TestAddUseCase:
    def test_create_use_case(self, client):
        r = client.post("/add-use-case", data={
            "name": "Test UC",
            "description": "A test use case",
            "phase": "Pre-Production",
            "tags": "tag1, tag2",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b"Test UC" in r.data
        assert len(_dashboard.use_cases) == 1
        uc = _dashboard.use_cases[0]
        assert uc.name == "Test UC"
        assert uc.description == "A test use case"
        assert uc.workflow_phase == "Pre-Production"
        assert uc.tags == ["tag1", "tag2"]

    def test_create_empty_name_ignored(self, client):
        r = client.post("/add-use-case", data={"name": "", "description": ""})
        # Should not redirect to a use case page
        assert len(_dashboard.use_cases) == 0


# -- Use case detail -------------------------------------------------------


class TestUseCaseDetail:
    def test_view_use_case(self, client):
        uc = UseCaseContext(name="Detail Test", workflow_phase="Post")
        uc.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "Blocking issue")
        _dashboard.register(uc)

        r = client.get("/use-case/Detail Test")
        assert r.status_code == 200
        assert b"Detail Test" in r.data
        assert b"BLOCKED" in r.data
        assert b"Blocking issue" in r.data

    def test_risk_heatmap_renders(self, client):
        client.get("/seed")
        r = client.get("/")
        assert b"Risk Heatmap" in r.data


# -- Flag actions ----------------------------------------------------------


class TestFlagActions:
    def _setup_uc(self):
        uc = UseCaseContext(name="ActionUC")
        uc.flag_risk(RiskDimension.ETHICAL, RiskLevel.HIGH, "Test flag")
        _dashboard.register(uc)
        return uc

    def test_begin_review(self, client):
        uc = self._setup_uc()
        r = client.post("/use-case/ActionUC/flag/0/review", follow_redirects=True)
        assert r.status_code == 200
        assert uc.risk_flags[0].status == ReviewStatus.IN_REVIEW

    def test_resolve_flag(self, client):
        uc = self._setup_uc()
        r = client.post("/use-case/ActionUC/flag/0/resolve", follow_redirects=True)
        assert r.status_code == 200
        assert uc.risk_flags[0].status == ReviewStatus.RESOLVED
        assert not uc.is_blocked()

    def test_accept_risk(self, client):
        uc = self._setup_uc()
        r = client.post("/use-case/ActionUC/flag/0/accept", follow_redirects=True)
        assert r.status_code == 200
        assert uc.risk_flags[0].status == ReviewStatus.ACCEPTED
        assert not uc.is_blocked()

    def test_add_flag(self, client):
        uc = self._setup_uc()
        r = client.post("/use-case/ActionUC/add-flag", data={
            "dimension": "COMMS",
            "level": "MEDIUM",
            "description": "New flag via form",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert len(uc.risk_flags) == 2
        assert uc.risk_flags[1].dimension == RiskDimension.COMMS
        assert uc.risk_flags[1].level == RiskLevel.MEDIUM

    def test_invalid_flag_index(self, client):
        self._setup_uc()
        r = client.post("/use-case/ActionUC/flag/99/resolve", follow_redirects=True)
        assert r.status_code == 200  # Should not crash


# -- Escalation ------------------------------------------------------------


class TestEscalation:
    def test_escalate_action(self, client):
        client.get("/seed")
        # AI Script Analysis has a 5-day-old MEDIUM flag — should escalate
        r = client.post("/use-case/AI Script Analysis/escalate", follow_redirects=True)
        assert r.status_code == 200
        assert b"escalation" in r.data.lower()
        uc = _dashboard._use_cases["AI Script Analysis"]
        # The stale flag should now be HIGH
        escalated = [f for f in uc.risk_flags if f.level == RiskLevel.HIGH]
        assert len(escalated) >= 1

    def test_escalation_shown_on_scores(self, client):
        client.get("/seed")
        r = client.get("/scores")
        assert b"Escalation Check" in r.data


# -- Hooks / Python sync ---------------------------------------------------


class TestHooks:
    @pytest.fixture(autouse=True)
    def _clear_hooks(self):
        """Clear all hooks before and after each test."""
        _hooks.clear()
        yield
        _hooks.clear()

    def test_on_decorator(self, client):
        events = []

        @on("flag_resolved")
        def handler(uc_name, idx, flag):
            events.append(("resolved", uc_name, idx))

        uc = UseCaseContext(name="HookUC")
        uc.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "test")
        _dashboard.register(uc)
        client.post("/use-case/HookUC/flag/0/resolve")
        assert len(events) == 1
        assert events[0] == ("resolved", "HookUC", 0)

    def test_on_direct_call(self, client):
        events = []

        def handler(uc_name, idx, flag):
            events.append(uc_name)

        on("flag_accepted", handler)

        uc = UseCaseContext(name="HookUC2")
        uc.flag_risk(RiskDimension.ETHICAL, RiskLevel.HIGH, "test")
        _dashboard.register(uc)
        client.post("/use-case/HookUC2/flag/0/accept")
        assert events == ["HookUC2"]

    def test_off_removes_specific_callback(self, client):
        events = []

        def handler(uc_name, idx, flag):
            events.append(uc_name)

        on("flag_resolved", handler)
        off("flag_resolved", handler)

        uc = UseCaseContext(name="HookUC3")
        uc.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "test")
        _dashboard.register(uc)
        client.post("/use-case/HookUC3/flag/0/resolve")
        assert events == []

    def test_off_removes_all_for_event(self):
        on("flag_resolved", lambda *a: None)
        on("flag_resolved", lambda *a: None)
        off("flag_resolved")
        assert "flag_resolved" not in _hooks

    def test_flag_added_hook(self, client):
        events = []

        @on("flag_added")
        def handler(uc_name, flag):
            events.append((uc_name, flag.description))

        uc = UseCaseContext(name="AddHookUC")
        _dashboard.register(uc)
        client.post("/use-case/AddHookUC/add-flag", data={
            "dimension": "COMMS",
            "level": "MEDIUM",
            "description": "hook test flag",
        })
        assert len(events) == 1
        assert events[0] == ("AddHookUC", "hook test flag")

    def test_flag_review_started_hook(self, client):
        events = []

        @on("flag_review_started")
        def handler(uc_name, idx, flag):
            events.append(uc_name)

        uc = UseCaseContext(name="ReviewHookUC")
        uc.flag_risk(RiskDimension.ETHICAL, RiskLevel.MEDIUM, "test")
        _dashboard.register(uc)
        client.post("/use-case/ReviewHookUC/flag/0/review")
        assert events == ["ReviewHookUC"]

    def test_use_case_registered_hook(self, client):
        events = []

        @on("use_case_registered")
        def handler(uc):
            events.append(uc.name)

        client.post("/add-use-case", data={"name": "HookRegistered", "description": ""})
        assert events == ["HookRegistered"]

    def test_escalation_applied_hook(self, client):
        events = []

        @on("escalation_applied")
        def handler(uc_name, count, results):
            events.append((uc_name, count))

        client.get("/seed")
        client.post("/use-case/AI Script Analysis/escalate")
        assert len(events) == 1
        assert events[0][0] == "AI Script Analysis"
        assert events[0][1] >= 1

    def test_multiple_hooks_same_event(self, client):
        events_a = []
        events_b = []

        @on("flag_resolved")
        def handler_a(uc_name, idx, flag):
            events_a.append(uc_name)

        @on("flag_resolved")
        def handler_b(uc_name, idx, flag):
            events_b.append(uc_name)

        uc = UseCaseContext(name="MultiHookUC")
        uc.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.HIGH, "test")
        _dashboard.register(uc)
        client.post("/use-case/MultiHookUC/flag/0/resolve")
        assert events_a == ["MultiHookUC"]
        assert events_b == ["MultiHookUC"]


# -- get/set dashboard sync ------------------------------------------------


class TestDashboardSync:
    def test_get_dashboard_returns_live_instance(self):
        dash = get_dashboard()
        uc = UseCaseContext(name="SyncTest")
        dash.register(uc)
        assert "SyncTest" in [u.name for u in _dashboard.use_cases]
        _dashboard._use_cases.clear()

    def test_set_dashboard_replaces_instance(self, client):
        new_dash = GovernanceDashboard()
        uc = UseCaseContext(name="ReplacedDash")
        new_dash.register(uc)
        set_dashboard(new_dash)
        try:
            r = client.get("/")
            assert b"ReplacedDash" in r.data
        finally:
            # Restore original empty dashboard
            set_dashboard(GovernanceDashboard())

    def test_set_dashboard_fires_reset_hook(self):
        events = []
        _hooks.clear()

        @on("dashboard_reset")
        def handler():
            events.append("reset")

        set_dashboard(GovernanceDashboard())
        assert events == ["reset"]
        _hooks.clear()

    def test_get_set_escalation_policy(self):
        original = get_escalation_policy()
        new_policy = EscalationPolicy(rules=[])
        set_escalation_policy(new_policy)
        assert get_escalation_policy() is new_policy
        assert get_escalation_policy().rules == []
        set_escalation_policy(original)

    def test_python_changes_reflected_in_web(self, client):
        dash = get_dashboard()
        uc = UseCaseContext(name="PythonAdded", workflow_phase="Test")
        uc.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.CRITICAL, "added from python")
        dash.register(uc)
        r = client.get("/")
        assert b"PythonAdded" in r.data
        assert b"BLOCKED" in r.data
