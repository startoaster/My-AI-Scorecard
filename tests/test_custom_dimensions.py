"""Tests for custom dimensions across all layers."""

import json
import pytest

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    ReviewStatus,
    RiskFlag,
    UseCaseContext,
    Dimension,
    DimensionType,
    custom_dimension,
    DEFAULT_ROUTING,
)
from ai_use_case_context.dashboard import GovernanceDashboard
from ai_use_case_context.escalation import EscalationPolicy
from ai_use_case_context.serialization import to_dict, from_dict, to_json, from_json
from ai_use_case_context.web import create_app, _dashboard, _hooks


# -- Fixtures --------------------------------------------------------------

FINANCIAL = custom_dimension("FINANCIAL", "Financial Risk")
REGULATORY = custom_dimension("REGULATORY", "Regulatory Compliance")
ENV = custom_dimension("ENV", "Environmental Impact")


@pytest.fixture()
def web_client():
    app = create_app()
    app.config["TESTING"] = True
    _dashboard._use_cases.clear()
    _hooks.clear()
    with app.test_client() as c:
        yield c
    _dashboard._use_cases.clear()
    _hooks.clear()


# -- Dimension class -------------------------------------------------------


class TestDimension:
    def test_basic_creation(self):
        d = Dimension("FINANCIAL", "Financial Risk")
        assert d.name == "FINANCIAL"
        assert d.value == "Financial Risk"

    def test_custom_dimension_factory(self):
        d = custom_dimension("FOO", "Foo Dimension")
        assert isinstance(d, Dimension)
        assert d.name == "FOO"
        assert d.value == "Foo Dimension"

    def test_str_is_value(self):
        assert str(FINANCIAL) == "Financial Risk"

    def test_repr(self):
        assert "FINANCIAL" in repr(FINANCIAL)
        assert "Financial Risk" in repr(FINANCIAL)

    def test_eq_same_name(self):
        a = Dimension("X", "Label A")
        b = Dimension("X", "Label B")
        assert a == b

    def test_neq_different_name(self):
        assert FINANCIAL != REGULATORY

    def test_hash_same_name(self):
        a = Dimension("X", "A")
        b = Dimension("X", "B")
        assert hash(a) == hash(b)
        assert len({a, b}) == 1

    def test_eq_with_builtin(self):
        """A Dimension with same name as a RiskDimension should be equal."""
        d = Dimension("LEGAL_IP", "Legal / IP Ownership")
        assert d == RiskDimension.LEGAL_IP
        assert RiskDimension.LEGAL_IP == d

    def test_neq_with_different_builtin(self):
        assert FINANCIAL != RiskDimension.LEGAL_IP

    def test_hash_matches_builtin(self):
        d = Dimension("LEGAL_IP", "Legal / IP Ownership")
        assert hash(d) == hash(RiskDimension.LEGAL_IP)

    def test_usable_as_dict_key_with_builtin(self):
        d = Dimension("LEGAL_IP", "Custom Label")
        table = {d: "value"}
        assert table.get(RiskDimension.LEGAL_IP) == "value"

    def test_builtin_eq_preserved(self):
        """Built-in dimensions still compare correctly with each other."""
        assert RiskDimension.LEGAL_IP == RiskDimension.LEGAL_IP
        assert RiskDimension.LEGAL_IP != RiskDimension.BIAS


# -- RiskFlag with custom dimension ----------------------------------------


class TestCustomDimensionFlag:
    def test_flag_with_custom_dimension(self):
        flag = RiskFlag(dimension=FINANCIAL, level=RiskLevel.HIGH, description="Over budget")
        assert flag.dimension == FINANCIAL
        assert flag.is_blocking
        assert str(flag)  # should not crash

    def test_flag_str_shows_custom_label(self):
        flag = RiskFlag(dimension=FINANCIAL, level=RiskLevel.MEDIUM, description="Cost")
        assert "Financial Risk" in str(flag)


# -- UseCaseContext with custom dimensions ----------------------------------


class TestUseCaseCustomDimensions:
    def test_flag_custom_dimension(self):
        ctx = UseCaseContext(name="Test")
        flag = ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget overrun")
        assert flag.dimension == FINANCIAL
        assert flag.reviewer == "Unassigned"
        assert ctx.is_blocked()

    def test_custom_routing_table(self):
        routing = {
            (FINANCIAL, RiskLevel.HIGH): "CFO",
            (REGULATORY, RiskLevel.MEDIUM): "Compliance Officer",
        }
        ctx = UseCaseContext(name="Test", routing_table=routing)
        f1 = ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget")
        f2 = ctx.flag_risk(REGULATORY, RiskLevel.MEDIUM, "GDPR")
        assert f1.reviewer == "CFO"
        assert f2.reviewer == "Compliance Officer"

    def test_risk_score_includes_custom(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget issue")
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.LOW, "Minor")
        scores = ctx.risk_score()
        assert scores["Financial Risk"] == 3
        assert scores["Legal / IP Ownership"] == 1
        # Built-in dimensions with no flags still appear
        assert "Technical Feasibility" in scores

    def test_dimensions_method(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.LOW, "test")
        dims = ctx.dimensions()
        dim_names = [d.name for d in dims]
        assert "FINANCIAL" in dim_names
        # All 4 built-ins should be present too
        for rd in RiskDimension:
            assert rd.name in dim_names

    def test_get_flags_by_custom_dimension(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget")
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.LOW, "Minor")
        ctx.flag_risk(FINANCIAL, RiskLevel.LOW, "Misc cost")
        assert len(ctx.get_flags_by_dimension(FINANCIAL)) == 2
        assert len(ctx.get_flags_by_dimension(RiskDimension.LEGAL_IP)) == 1

    def test_mixed_dimensions_blocking(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.CRITICAL, "Blocker")
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.LOW, "OK")
        assert ctx.is_blocked()
        blockers = ctx.get_blockers()
        assert len(blockers) == 1
        assert blockers[0].dimension == FINANCIAL

    def test_summary_shows_custom_dimensions(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Over budget")
        s = ctx.summary()
        assert "Financial Risk" in s


# -- Dashboard with custom dimensions --------------------------------------


class TestDashboardCustomDimensions:
    def test_all_dimensions_includes_custom(self):
        dash = GovernanceDashboard()
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget")
        dash.register(ctx)
        all_dims = dash.all_dimensions()
        dim_names = [d.name for d in all_dims]
        assert "FINANCIAL" in dim_names
        for rd in RiskDimension:
            assert rd.name in dim_names

    def test_dimension_summary_custom(self):
        dash = GovernanceDashboard()
        ctx = UseCaseContext(name="UC1")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Over budget")
        ctx.flag_risk(FINANCIAL, RiskLevel.LOW, "Misc")
        dash.register(ctx)
        ds = dash.dimension_summary(FINANCIAL)
        assert ds.total_flags == 2
        assert ds.max_level == RiskLevel.HIGH
        assert "UC1" in ds.affected_use_cases

    def test_all_dimension_summaries_includes_custom(self):
        dash = GovernanceDashboard()
        ctx = UseCaseContext(name="UC1")
        ctx.flag_risk(FINANCIAL, RiskLevel.MEDIUM, "Cost")
        dash.register(ctx)
        summaries = dash.all_dimension_summaries()
        # Should contain both built-in and custom dimensions
        dim_names = [d.name for d in summaries.keys()]
        assert "FINANCIAL" in dim_names
        assert "LEGAL_IP" in dim_names

    def test_portfolio_risk_scores_custom(self):
        dash = GovernanceDashboard()
        ctx = UseCaseContext(name="UC1")
        ctx.flag_risk(FINANCIAL, RiskLevel.CRITICAL, "Big problem")
        dash.register(ctx)
        scores = dash.portfolio_risk_scores()
        assert scores["UC1"]["Financial Risk"] == 4

    def test_summary_shows_custom_dimensions(self):
        dash = GovernanceDashboard()
        ctx = UseCaseContext(name="UC1")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget")
        dash.register(ctx)
        s = dash.summary()
        assert "Financial Risk" in s


# -- Serialization with custom dimensions ----------------------------------


class TestSerializationCustomDimensions:
    def test_to_dict_custom_dimension(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Over budget")
        data = to_dict(ctx)
        flag_data = data["risk_flags"][0]
        assert flag_data["dimension"] == "FINANCIAL"
        assert flag_data["dimension_label"] == "Financial Risk"

    def test_builtin_no_dimension_label(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(RiskDimension.LEGAL_IP, RiskLevel.LOW, "Minor")
        data = to_dict(ctx)
        flag_data = data["risk_flags"][0]
        assert flag_data["dimension"] == "LEGAL_IP"
        assert "dimension_label" not in flag_data

    def test_round_trip_dict_custom(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget")
        ctx.flag_risk(RiskDimension.BIAS, RiskLevel.LOW, "OK")
        data = to_dict(ctx)
        restored = from_dict(data)
        assert len(restored.risk_flags) == 2
        assert isinstance(restored.risk_flags[0].dimension, Dimension)
        assert restored.risk_flags[0].dimension.name == "FINANCIAL"
        assert restored.risk_flags[0].dimension.value == "Financial Risk"
        assert restored.risk_flags[1].dimension == RiskDimension.BIAS

    def test_round_trip_json_custom(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.CRITICAL, "Blocker")
        ctx.flag_risk(REGULATORY, RiskLevel.MEDIUM, "GDPR")
        json_str = to_json(ctx)
        restored = from_json(json_str)
        assert restored.risk_flags[0].dimension.name == "FINANCIAL"
        assert restored.risk_flags[1].dimension.name == "REGULATORY"
        assert restored.risk_flags[1].dimension.value == "Regulatory Compliance"

    def test_json_contains_label(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.LOW, "test")
        parsed = json.loads(to_json(ctx))
        assert parsed["risk_flags"][0]["dimension_label"] == "Financial Risk"

    def test_round_trip_preserves_blocking(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Blocker")
        assert ctx.is_blocked()
        restored = from_json(to_json(ctx))
        assert restored.is_blocked()
        assert restored.risk_flags[0].dimension.name == "FINANCIAL"


# -- Escalation with custom dimensions ------------------------------------


class TestEscalationCustomDimensions:
    def test_escalation_applies_to_custom(self):
        from datetime import timedelta

        ctx = UseCaseContext(name="Test")
        flag = ctx.flag_risk(FINANCIAL, RiskLevel.MEDIUM, "Stale budget flag")
        flag.created_at = flag.created_at - timedelta(days=5)

        policy = EscalationPolicy()
        results = policy.apply_escalations(ctx)
        assert len(results) == 1
        assert flag.level == RiskLevel.HIGH


# -- Web dashboard with custom dimensions ----------------------------------


class TestWebCustomDimensions:
    def test_heatmap_shows_custom_dimension(self, web_client):
        ctx = UseCaseContext(name="CustomDimUC")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget")
        _dashboard.register(ctx)
        r = web_client.get("/")
        assert r.status_code == 200
        assert b"Financial" in r.data

    def test_dimension_overview_shows_custom(self, web_client):
        ctx = UseCaseContext(name="CustomDimUC")
        ctx.flag_risk(REGULATORY, RiskLevel.MEDIUM, "GDPR")
        _dashboard.register(ctx)
        r = web_client.get("/")
        assert b"Regulatory" in r.data

    def test_scores_page_shows_custom(self, web_client):
        ctx = UseCaseContext(name="CustomDimUC")
        ctx.flag_risk(FINANCIAL, RiskLevel.CRITICAL, "Big problem")
        _dashboard.register(ctx)
        r = web_client.get("/scores")
        assert b"Financial Risk" in r.data

    def test_use_case_detail_shows_custom(self, web_client):
        ctx = UseCaseContext(name="CustomDimUC")
        ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Over budget")
        _dashboard.register(ctx)
        r = web_client.get("/use-case/CustomDimUC")
        assert r.status_code == 200
        assert b"Financial Risk" in r.data
        assert b"Over budget" in r.data

    def test_add_flag_form_lists_custom_dimensions(self, web_client):
        ctx = UseCaseContext(name="CustomDimUC")
        ctx.flag_risk(FINANCIAL, RiskLevel.LOW, "existing")
        _dashboard.register(ctx)
        r = web_client.get("/use-case/CustomDimUC")
        # The dimension dropdown should include FINANCIAL
        assert b"FINANCIAL" in r.data

    def test_add_flag_with_custom_dimension_via_form(self, web_client):
        ctx = UseCaseContext(name="CustomDimUC")
        ctx.flag_risk(FINANCIAL, RiskLevel.LOW, "seed")
        _dashboard.register(ctx)
        r = web_client.post("/use-case/CustomDimUC/add-flag", data={
            "dimension": "FINANCIAL",
            "level": "HIGH",
            "description": "new budget flag",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert len(ctx.risk_flags) == 2
        assert ctx.risk_flags[1].dimension == FINANCIAL
        assert ctx.risk_flags[1].level == RiskLevel.HIGH
