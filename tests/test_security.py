"""Tests for security dimension presets and SecurityProfile."""

import pytest

from ai_use_case_context.core import (
    RiskDimension,
    RiskLevel,
    UseCaseContext,
    DEFAULT_ROUTING,
)
from ai_use_case_context.security import (
    # TPN
    TPN_CONTENT_SECURITY,
    TPN_PHYSICAL_SECURITY,
    TPN_DIGITAL_SECURITY,
    TPN_ASSET_MANAGEMENT,
    TPN_INCIDENT_RESPONSE,
    TPN_PERSONNEL_SECURITY,
    TPN_DIMENSIONS,
    TPN_ROUTING,
    # VFX
    VFX_SECURE_TRANSFER,
    VFX_RENDER_ISOLATION,
    VFX_WORKSTATION_SECURITY,
    VFX_CLOUD_SECURITY,
    VFX_DATA_CLASSIFICATION,
    VFX_VENDOR_SECURITY,
    VFX_DIMENSIONS,
    VFX_ROUTING,
    # Enterprise
    ENTERPRISE_ACCESS_CONTROL,
    ENTERPRISE_AUDIT_TRAIL,
    ENTERPRISE_DATA_PRIVACY,
    ENTERPRISE_COMPLIANCE,
    ENTERPRISE_BUSINESS_CONTINUITY,
    ENTERPRISE_DIMENSIONS,
    ENTERPRISE_ROUTING,
    # Profile helpers
    SecurityProfile,
    security_profile,
    apply_security_profile,
    list_presets,
    register_preset,
    unregister_preset,
)


# ---------------------------------------------------------------------------
# TPN dimension tests
# ---------------------------------------------------------------------------

class TestTPNDimensions:
    def test_tpn_dimensions_count(self):
        assert len(TPN_DIMENSIONS) == 6

    def test_tpn_dimension_names(self):
        names = {d.name for d in TPN_DIMENSIONS}
        assert names == {
            "TPN_CONTENT_SECURITY",
            "TPN_PHYSICAL_SECURITY",
            "TPN_DIGITAL_SECURITY",
            "TPN_ASSET_MANAGEMENT",
            "TPN_INCIDENT_RESPONSE",
            "TPN_PERSONNEL_SECURITY",
        }

    def test_tpn_dimensions_have_labels(self):
        for dim in TPN_DIMENSIONS:
            assert "TPN" in dim.value
            assert len(dim.value) > 0

    def test_tpn_routing_covers_all_dimensions(self):
        for dim in TPN_DIMENSIONS:
            for level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
                assert (dim, level) in TPN_ROUTING, f"Missing TPN routing for {dim.name} x {level.name}"

    def test_tpn_routing_values_nonempty(self):
        for key, reviewer in TPN_ROUTING.items():
            assert reviewer, f"Empty reviewer for {key}"

    def test_tpn_can_flag_use_case(self):
        ctx = UseCaseContext("Test", routing_table=TPN_ROUTING)
        flag = ctx.flag_risk(TPN_CONTENT_SECURITY, RiskLevel.HIGH, "Encryption gap")
        assert flag.reviewer == "VP Security / CISO"
        assert flag.dimension == TPN_CONTENT_SECURITY


# ---------------------------------------------------------------------------
# VFX dimension tests
# ---------------------------------------------------------------------------

class TestVFXDimensions:
    def test_vfx_dimensions_count(self):
        assert len(VFX_DIMENSIONS) == 6

    def test_vfx_dimension_names(self):
        names = {d.name for d in VFX_DIMENSIONS}
        assert names == {
            "VFX_SECURE_TRANSFER",
            "VFX_RENDER_ISOLATION",
            "VFX_WORKSTATION_SECURITY",
            "VFX_CLOUD_SECURITY",
            "VFX_DATA_CLASSIFICATION",
            "VFX_VENDOR_SECURITY",
        }

    def test_vfx_routing_covers_all_dimensions(self):
        for dim in VFX_DIMENSIONS:
            for level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
                assert (dim, level) in VFX_ROUTING, f"Missing VFX routing for {dim.name} x {level.name}"

    def test_vfx_can_flag_use_case(self):
        ctx = UseCaseContext("Test", routing_table=VFX_ROUTING)
        flag = ctx.flag_risk(VFX_RENDER_ISOLATION, RiskLevel.CRITICAL, "Render farm exposed")
        assert flag.reviewer == "CTO + External Infrastructure Audit"
        assert ctx.is_blocked()


# ---------------------------------------------------------------------------
# Enterprise dimension tests
# ---------------------------------------------------------------------------

class TestEnterpriseDimensions:
    def test_enterprise_dimensions_count(self):
        assert len(ENTERPRISE_DIMENSIONS) == 5

    def test_enterprise_dimension_names(self):
        names = {d.name for d in ENTERPRISE_DIMENSIONS}
        assert names == {
            "ENTERPRISE_ACCESS_CONTROL",
            "ENTERPRISE_AUDIT_TRAIL",
            "ENTERPRISE_DATA_PRIVACY",
            "ENTERPRISE_COMPLIANCE",
            "ENTERPRISE_BUSINESS_CONTINUITY",
        }

    def test_enterprise_routing_covers_all_dimensions(self):
        for dim in ENTERPRISE_DIMENSIONS:
            for level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
                assert (dim, level) in ENTERPRISE_ROUTING

    def test_enterprise_can_flag_use_case(self):
        ctx = UseCaseContext("Test", routing_table=ENTERPRISE_ROUTING)
        flag = ctx.flag_risk(ENTERPRISE_DATA_PRIVACY, RiskLevel.MEDIUM, "PII exposure")
        assert flag.reviewer == "Data Protection Officer"


# ---------------------------------------------------------------------------
# SecurityProfile tests
# ---------------------------------------------------------------------------

class TestSecurityProfile:
    def test_empty_profile(self):
        profile = SecurityProfile()
        assert profile.dimensions == []
        assert profile.routing == {}
        assert profile.presets == []

    def test_profile_with_dimensions(self):
        profile = SecurityProfile(
            dimensions=list(TPN_DIMENSIONS),
            routing=dict(TPN_ROUTING),
            presets=["tpn"],
        )
        assert len(profile.dimensions) == 6
        assert len(profile.routing) == 24
        assert profile.presets == ["tpn"]

    def test_profile_merge(self):
        p1 = SecurityProfile(list(TPN_DIMENSIONS), dict(TPN_ROUTING), ["tpn"])
        p2 = SecurityProfile(list(VFX_DIMENSIONS), dict(VFX_ROUTING), ["vfx"])
        merged = p1.merge(p2)
        assert len(merged.dimensions) == 12
        assert len(merged.routing) == 48
        assert merged.presets == ["tpn", "vfx"]

    def test_profile_merge_deduplicates(self):
        p1 = SecurityProfile(list(TPN_DIMENSIONS), dict(TPN_ROUTING), ["tpn"])
        merged = p1.merge(p1)
        assert len(merged.dimensions) == 6  # No duplicates

    def test_profile_repr(self):
        profile = SecurityProfile(list(TPN_DIMENSIONS), {}, ["tpn"])
        assert "dimensions=6" in repr(profile)
        assert "tpn" in repr(profile)


# ---------------------------------------------------------------------------
# security_profile() factory tests
# ---------------------------------------------------------------------------

class TestSecurityProfileFactory:
    def test_single_preset(self):
        profile = security_profile("tpn")
        assert len(profile.dimensions) == 6
        assert profile.presets == ["tpn"]

    def test_multiple_presets(self):
        profile = security_profile("tpn", "vfx", "enterprise")
        assert len(profile.dimensions) == 17
        assert profile.presets == ["tpn", "vfx", "enterprise"]

    def test_unknown_preset_raises(self):
        with pytest.raises(KeyError, match="Unknown security preset"):
            security_profile("nonexistent")

    def test_case_insensitive(self):
        profile = security_profile("TPN")
        assert len(profile.dimensions) == 6

    def test_combined_routing(self):
        profile = security_profile("tpn", "vfx")
        # All TPN + VFX routing entries should be present
        for dim in TPN_DIMENSIONS + VFX_DIMENSIONS:
            for level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
                assert (dim, level) in profile.routing


# ---------------------------------------------------------------------------
# apply_security_profile() tests
# ---------------------------------------------------------------------------

class TestApplySecurityProfile:
    def test_apply_merges_routing(self):
        ctx = UseCaseContext("Test")
        profile = security_profile("tpn")
        apply_security_profile(ctx, profile)

        # Original routing still works
        assert (RiskDimension.LEGAL_IP, RiskLevel.HIGH) in ctx.routing_table
        # TPN routing now available
        assert (TPN_CONTENT_SECURITY, RiskLevel.HIGH) in ctx.routing_table

    def test_apply_enables_auto_routing(self):
        ctx = UseCaseContext("Test")
        apply_security_profile(ctx, security_profile("vfx"))
        flag = ctx.flag_risk(VFX_CLOUD_SECURITY, RiskLevel.MEDIUM, "S3 bucket open")
        assert flag.reviewer == "Cloud Security Architect"

    def test_apply_multiple_profiles(self):
        ctx = UseCaseContext("Test")
        apply_security_profile(ctx, security_profile("tpn", "enterprise"))
        # Should auto-route both TPN and enterprise dimensions
        f1 = ctx.flag_risk(TPN_INCIDENT_RESPONSE, RiskLevel.HIGH, "Breach detected")
        f2 = ctx.flag_risk(ENTERPRISE_COMPLIANCE, RiskLevel.MEDIUM, "SOC2 gap")
        assert f1.reviewer == "CISO / VP Security"
        assert f2.reviewer == "Compliance Officer"


# ---------------------------------------------------------------------------
# Preset registry tests
# ---------------------------------------------------------------------------

class TestPresetRegistry:
    def test_list_presets(self):
        presets = list_presets()
        assert "tpn" in presets
        assert "vfx" in presets
        assert "enterprise" in presets

    def test_register_custom_preset(self):
        from ai_use_case_context.core import custom_dimension

        MY_DIM = custom_dimension("MY_SEC", "My Security Dimension")
        my_routing = {(MY_DIM, RiskLevel.HIGH): "My Reviewer"}
        register_preset("my_custom", [MY_DIM], my_routing)
        try:
            assert "my_custom" in list_presets()
            profile = security_profile("my_custom")
            assert len(profile.dimensions) == 1
            assert profile.dimensions[0].name == "MY_SEC"
        finally:
            unregister_preset("my_custom")

    def test_unregister_preset(self):
        from ai_use_case_context.core import custom_dimension

        DIM = custom_dimension("TEMP", "Temp")
        register_preset("temp_test", [DIM], {})
        assert unregister_preset("temp_test") is True
        assert "temp_test" not in list_presets()

    def test_unregister_nonexistent(self):
        assert unregister_preset("does_not_exist") is False


# ---------------------------------------------------------------------------
# Integration: security dimensions with dashboard
# ---------------------------------------------------------------------------

class TestSecurityDashboardIntegration:
    def test_security_dims_in_dashboard(self):
        from ai_use_case_context.dashboard import GovernanceDashboard

        ctx = UseCaseContext("Secure Pipeline")
        apply_security_profile(ctx, security_profile("tpn"))
        ctx.flag_risk(TPN_CONTENT_SECURITY, RiskLevel.HIGH, "No watermarking")

        dashboard = GovernanceDashboard()
        dashboard.register(ctx)

        all_dims = dashboard.all_dimensions()
        dim_names = {d.name for d in all_dims}
        assert "TPN_CONTENT_SECURITY" in dim_names

        summary = dashboard.dimension_summary(TPN_CONTENT_SECURITY)
        assert summary.total_flags == 1
        assert summary.blocking_flags == 1

    def test_security_dims_in_risk_score(self):
        ctx = UseCaseContext("Test")
        apply_security_profile(ctx, security_profile("vfx"))
        ctx.flag_risk(VFX_SECURE_TRANSFER, RiskLevel.MEDIUM, "FTP in use")
        scores = ctx.risk_score()
        assert scores["Secure Transfer / Delivery"] == 2


# ---------------------------------------------------------------------------
# Integration: security dimensions with serialization
# ---------------------------------------------------------------------------

class TestSecuritySerialization:
    def test_security_dim_roundtrip(self):
        from ai_use_case_context.serialization import to_dict, from_dict

        ctx = UseCaseContext("Test")
        apply_security_profile(ctx, security_profile("tpn"))
        ctx.flag_risk(TPN_DIGITAL_SECURITY, RiskLevel.HIGH, "Network not segmented")

        data = to_dict(ctx)
        restored = from_dict(data)

        assert len(restored.risk_flags) == 1
        flag = restored.risk_flags[0]
        assert flag.dimension.name == "TPN_DIGITAL_SECURITY"
        assert flag.dimension.value == "Digital Security (TPN)"
        assert flag.level == RiskLevel.HIGH

    def test_security_dim_json_roundtrip(self):
        from ai_use_case_context.serialization import to_json, from_json

        ctx = UseCaseContext("Test")
        apply_security_profile(ctx, security_profile("enterprise"))
        ctx.flag_risk(ENTERPRISE_ACCESS_CONTROL, RiskLevel.CRITICAL, "No MFA")

        json_str = to_json(ctx)
        restored = from_json(json_str)

        flag = restored.risk_flags[0]
        assert flag.dimension.name == "ENTERPRISE_ACCESS_CONTROL"
        assert flag.dimension.value == "Access Control (IAM)"


# ---------------------------------------------------------------------------
# Integration: security dimensions with escalation
# ---------------------------------------------------------------------------

class TestSecurityEscalation:
    def test_security_flag_escalates(self):
        from datetime import datetime, timedelta
        from ai_use_case_context.escalation import EscalationPolicy

        ctx = UseCaseContext("Test")
        apply_security_profile(ctx, security_profile("tpn"))
        flag = ctx.flag_risk(TPN_CONTENT_SECURITY, RiskLevel.MEDIUM, "Weak DRM")
        flag.created_at = datetime.now() - timedelta(days=5)

        policy = EscalationPolicy()
        results = policy.check_use_case(ctx)
        assert len(results) == 1
        assert results[0].escalate_to_level == RiskLevel.HIGH
