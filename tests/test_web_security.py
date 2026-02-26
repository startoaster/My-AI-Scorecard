"""Tests for security profile integration in the web dashboard."""

import pytest

from ai_use_case_context.web import (
    create_app,
    get_dashboard,
    set_dashboard,
    get_security_profile,
    set_security_profile,
)
from ai_use_case_context.core import RiskLevel, UseCaseContext
from ai_use_case_context.dashboard import GovernanceDashboard
from ai_use_case_context.security import (
    TPN_CONTENT_SECURITY,
    VFX_SECURE_TRANSFER,
    ENTERPRISE_ACCESS_CONTROL,
    security_profile,
    apply_security_profile,
)
from ai_use_case_context.governance_hooks import (
    clear_hooks,
    AuditLogger,
    register_hook,
)


@pytest.fixture
def client():
    """Fresh Flask test client with empty dashboard."""
    set_dashboard(GovernanceDashboard())
    set_security_profile(None)
    clear_hooks()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c
    clear_hooks()


class TestSecurityPage:
    def test_security_page_loads(self, client):
        resp = client.get("/security")
        assert resp.status_code == 200
        assert b"Security Profiles" in resp.data

    def test_no_active_profile(self, client):
        resp = client.get("/security")
        assert b"No security profile active" in resp.data

    def test_apply_tpn_preset(self, client):
        resp = client.post("/security", data={
            "action": "apply",
            "presets": ["tpn"],
        }, follow_redirects=False)
        assert resp.status_code == 200
        assert b"Security profile applied" in resp.data
        assert b"TPN" in resp.data

        profile = get_security_profile()
        assert profile is not None
        assert "tpn" in profile.presets

    def test_apply_multiple_presets(self, client):
        resp = client.post("/security", data={
            "action": "apply",
            "presets": ["tpn", "vfx"],
        })
        assert resp.status_code == 200
        profile = get_security_profile()
        assert len(profile.dimensions) == 12

    def test_apply_updates_existing_use_cases(self, client):
        uc = UseCaseContext("Test UC")
        get_dashboard().register(uc)

        client.post("/security", data={
            "action": "apply",
            "presets": ["enterprise"],
        })

        # The use case should now have enterprise routing
        flag = uc.flag_risk(ENTERPRISE_ACCESS_CONTROL, RiskLevel.HIGH, "No MFA")
        assert flag.reviewer == "CISO / VP Security"

    def test_clear_profile(self, client):
        # First apply
        client.post("/security", data={
            "action": "apply",
            "presets": ["tpn"],
        })
        assert get_security_profile() is not None

        # Then clear
        resp = client.post("/security", data={"action": "clear"})
        assert resp.status_code == 200
        assert b"Security profile cleared" in resp.data
        assert get_security_profile() is None

    def test_active_profile_shows_dimensions(self, client):
        client.post("/security", data={
            "action": "apply",
            "presets": ["vfx"],
        })
        resp = client.get("/security")
        assert b"Secure Transfer" in resp.data
        assert b"Render Farm" in resp.data
        assert b"Cloud" in resp.data


class TestSecurityNavLink:
    def test_nav_has_security_link(self, client):
        resp = client.get("/")
        assert b"/security" in resp.data
        assert b"Security" in resp.data


class TestSecurityAddFlag:
    def test_security_dims_in_add_flag_form(self, client):
        set_security_profile(security_profile("tpn"))
        uc = UseCaseContext("Test UC")
        get_dashboard().register(uc)

        resp = client.get("/use-case/Test UC")
        assert resp.status_code == 200
        assert b"TPN_CONTENT_SECURITY" in resp.data
        assert b"[Security]" in resp.data

    def test_add_security_dim_flag(self, client):
        profile = security_profile("tpn")
        set_security_profile(profile)
        uc = UseCaseContext("Test UC")
        apply_security_profile(uc, profile)
        get_dashboard().register(uc)

        resp = client.post("/use-case/Test UC/add-flag", data={
            "dimension": "TPN_CONTENT_SECURITY",
            "level": "HIGH",
            "description": "No encryption at rest",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert len(uc.risk_flags) == 1
        assert uc.risk_flags[0].dimension.name == "TPN_CONTENT_SECURITY"


class TestGovernanceEventsFromWeb:
    def test_resolve_emits_governance_event(self, client):
        logger = AuditLogger()
        register_hook(logger)

        uc = UseCaseContext("Test UC")
        uc.flag_risk(TPN_CONTENT_SECURITY, RiskLevel.HIGH, "Test")
        get_dashboard().register(uc)

        client.post("/use-case/Test UC/flag/0/resolve")

        events = logger.query(use_case_name="Test UC")
        assert any(e["event_type"] == "flag_resolved" for e in events)

    def test_accept_emits_governance_event(self, client):
        logger = AuditLogger()
        register_hook(logger)

        uc = UseCaseContext("Test UC")
        uc.flag_risk(TPN_CONTENT_SECURITY, RiskLevel.HIGH, "Test")
        get_dashboard().register(uc)

        client.post("/use-case/Test UC/flag/0/accept")

        events = logger.query(use_case_name="Test UC")
        assert any(e["event_type"] == "flag_accepted" for e in events)

    def test_add_flag_emits_governance_event(self, client):
        logger = AuditLogger()
        register_hook(logger)

        profile = security_profile("vfx")
        set_security_profile(profile)
        uc = UseCaseContext("Test UC")
        apply_security_profile(uc, profile)
        get_dashboard().register(uc)

        client.post("/use-case/Test UC/add-flag", data={
            "dimension": "VFX_SECURE_TRANSFER",
            "level": "MEDIUM",
            "description": "Unsecured FTP",
        }, follow_redirects=True)

        events = logger.query(use_case_name="Test UC")
        assert any(e["event_type"] == "flag_raised" for e in events)

    def test_review_emits_governance_event(self, client):
        logger = AuditLogger()
        register_hook(logger)

        uc = UseCaseContext("Test UC")
        uc.flag_risk(TPN_CONTENT_SECURITY, RiskLevel.MEDIUM, "Test")
        get_dashboard().register(uc)

        client.post("/use-case/Test UC/flag/0/review")

        events = logger.query(use_case_name="Test UC")
        assert any(e["event_type"] == "review_started" for e in events)
