"""Tests for operational characteristics and deployment-keyed rules."""

import pytest

from ai_use_case_context.authority import Authority
from ai_use_case_context.core import RiskDimension, RiskLevel, UseCaseContext
from ai_use_case_context.intake import IPClass
from ai_use_case_context.operations import (
    CollectionPolicy,
    Custodian,
    DEFAULT_OPERATIONAL_RULES,
    DataCollection,
    DataResidency,
    Deployment,
    HostEnvironment,
    INDEFINITE_RETENTION,
    ModelRefinement,
    OperationalProfile,
    OperationalRule,
    RefinementLocation,
    UpdateControl,
)


def contained() -> OperationalProfile:
    """A profile where nothing leaves the customer's control."""
    return OperationalProfile(
        deployment=Deployment(
            host=HostEnvironment.ON_PREMISES,
            update_control=UpdateControl.CUSTOMER,
        ),
        residency=DataResidency(custodian=Custodian.CUSTOMER),
        collection=DataCollection(
            customer_data=CollectionPolicy.NOT_COLLECTED,
            metadata=CollectionPolicy.NOT_COLLECTED,
        ),
        refinement=ModelRefinement(allowed=False),
    )


def fired(p: OperationalProfile, ip=None) -> set:
    return {r.rule_id for r in DEFAULT_OPERATIONAL_RULES if r.applies(p, ip)}


class TestEnums:
    def test_customer_controlled_hosts(self):
        assert HostEnvironment.ON_DEVICE.is_customer_controlled
        assert HostEnvironment.ON_PREMISES.is_customer_controlled
        assert HostEnvironment.CUSTOMER_CLOUD.is_customer_controlled
        assert not HostEnvironment.VENDOR_CLOUD.is_customer_controlled

    def test_collection_policy_properties(self):
        assert not CollectionPolicy.NOT_COLLECTED.is_collected
        assert CollectionPolicy.COLLECTED_OPT_OUT.is_collected
        assert not CollectionPolicy.COLLECTED_OPT_OUT.is_mandatory
        assert CollectionPolicy.COLLECTED_REQUIRED.is_mandatory

    def test_indefinite_retention_detection(self):
        assert DataCollection(retention_period="Indefinite").is_indefinite
        assert DataCollection(retention_period=INDEFINITE_RETENTION).is_indefinite
        assert not DataCollection(retention_period="90 days").is_indefinite
        assert not DataCollection().is_indefinite

    def test_collects_anything(self):
        assert not DataCollection().collects_anything
        assert DataCollection(
            metadata=CollectionPolicy.COLLECTED_OPT_OUT
        ).collects_anything


class TestFullyContained:
    def test_contained_profile_reports_containment(self):
        assert contained().is_fully_customer_controlled

    def test_vendor_host_breaks_containment(self):
        p = contained()
        p.deployment.host = HostEnvironment.VENDOR_CLOUD
        assert not p.is_fully_customer_controlled

    def test_collection_breaks_containment(self):
        p = contained()
        p.collection.metadata = CollectionPolicy.COLLECTED_OPT_OUT
        assert not p.is_fully_customer_controlled

    def test_contained_profile_fires_nothing_even_for_restricted(self):
        assert fired(contained(), IPClass.PRE_RELEASE_IP) == set()


class TestSensitivityPairing:
    def test_vendor_host_alone_does_not_fire(self):
        # A vendor-hosted deployment is unremarkable without sensitive material.
        p = contained()
        p.deployment.host = HostEnvironment.VENDOR_CLOUD
        assert "RESTRICTED_MATERIAL_IN_VENDOR_ENVIRONMENT" not in fired(
            p, IPClass.NO_IP
        )

    def test_vendor_host_with_restricted_material_fires(self):
        p = contained()
        p.deployment.host = HostEnvironment.VENDOR_CLOUD
        assert "RESTRICTED_MATERIAL_IN_VENDOR_ENVIRONMENT" in fired(
            p, IPClass.PRE_RELEASE_IP
        )

    def test_unknown_sensitivity_stays_silent(self):
        # Guessing at sensitivity would produce flags nobody can act on.
        p = contained()
        p.deployment.host = HostEnvironment.VENDOR_CLOUD
        p.residency.custodian = Custodian.VENDOR
        assert fired(p, None) == set()

    def test_vendor_custodian_with_restricted_material(self):
        p = contained()
        p.residency.custodian = Custodian.VENDOR
        assert "RESTRICTED_MATERIAL_HELD_BY_VENDOR" in fired(
            p, IPClass.TALENT_MATERIAL
        )

    def test_mandatory_collection_of_restricted_is_critical(self):
        p = contained()
        p.collection.customer_data = CollectionPolicy.COLLECTED_REQUIRED
        assert "MANDATORY_COLLECTION_OF_RESTRICTED_MATERIAL" in fired(
            p, IPClass.PRODUCTION_IP
        )
        rule = next(
            r for r in DEFAULT_OPERATIONAL_RULES
            if r.rule_id == "MANDATORY_COLLECTION_OF_RESTRICTED_MATERIAL"
        )
        assert rule.level is RiskLevel.CRITICAL

    def test_opt_out_collection_is_not_the_critical_case(self):
        p = contained()
        p.collection.customer_data = CollectionPolicy.COLLECTED_OPT_OUT
        assert "MANDATORY_COLLECTION_OF_RESTRICTED_MATERIAL" not in fired(
            p, IPClass.PRODUCTION_IP
        )

    def test_vendor_controlled_updates_with_restricted_material(self):
        p = contained()
        p.deployment.update_control = UpdateControl.VENDOR
        assert "VENDOR_CONTROLLED_UPDATES" in fired(p, IPClass.PRODUCTION_IP)


class TestSensitivityIndependentRules:
    def test_indefinite_retention_fires_without_ip_class(self):
        p = contained()
        p.collection.metadata = CollectionPolicy.COLLECTED_OPT_OUT
        p.collection.retention_period = "indefinite"
        assert "INDEFINITE_RETENTION" in fired(p, None)

    def test_indefinite_retention_needs_actual_collection(self):
        p = contained()
        p.collection.retention_period = "indefinite"
        assert "INDEFINITE_RETENTION" not in fired(p, None)

    def test_vendor_refinement_fires_and_is_binding(self):
        p = contained()
        p.refinement = ModelRefinement(
            allowed=True, location=RefinementLocation.VENDOR_CONTROLLED
        )
        assert "REFINEMENT_IN_VENDOR_ENVIRONMENT" in fired(p, None)
        rule = next(
            r for r in DEFAULT_OPERATIONAL_RULES
            if r.rule_id == "REFINEMENT_IN_VENDOR_ENVIRONMENT"
        )
        assert rule.authority is Authority.BINDING_CONTRACT

    def test_customer_side_refinement_does_not_fire(self):
        p = contained()
        p.refinement = ModelRefinement(
            allowed=True, location=RefinementLocation.CUSTOMER_CONTROLLED
        )
        assert "REFINEMENT_IN_VENDOR_ENVIRONMENT" not in fired(p, None)


class TestDeriveFlags:
    def test_flags_land_on_context(self):
        ctx = UseCaseContext(name="Test")
        p = contained()
        p.deployment.host = HostEnvironment.VENDOR_CLOUD
        p.residency = DataResidency(
            custodian=Custodian.VENDOR, location="Ireland"
        )
        flags = p.derive_flags(ctx, ip_class=IPClass.PRE_RELEASE_IP)
        assert len(flags) == 2
        assert ctx.is_blocked()
        assert any("Ireland" in f.description for f in flags)

    def test_custom_rules_replace_defaults(self):
        ctx = UseCaseContext(name="Test")
        catch_all = OperationalRule(
            rule_id="ALWAYS",
            title="fires always",
            applies=lambda p, ip: True,
            dimension=RiskDimension.SECURITY,
            level=RiskLevel.LOW,
            describe=lambda p, ip: "always",
        )
        flags = contained().derive_flags(ctx, rules=[catch_all])
        assert [f.description for f in flags] == ["always"]

    def test_empty_rules_derive_nothing(self):
        ctx = UseCaseContext(name="Test")
        assert contained().derive_flags(ctx, rules=[]) == []


class TestSerialization:
    def test_round_trip(self):
        p = OperationalProfile(
            deployment=Deployment(
                host=HostEnvironment.CUSTOMER_CLOUD,
                region="US",
                update_control=UpdateControl.CUSTOMER,
            ),
            residency=DataResidency(
                custodian=Custodian.CUSTOMER, location="US"
            ),
            collection=DataCollection(
                customer_data=CollectionPolicy.COLLECTED_OPT_OUT,
                metadata=CollectionPolicy.COLLECTED_REQUIRED,
                retention_period="90 days",
            ),
            refinement=ModelRefinement(
                allowed=True, location=RefinementLocation.CUSTOMER_CONTROLLED
            ),
            notes="n",
        )
        assert OperationalProfile.from_dict(p.to_dict()) == p

    def test_summary_shows_key_fields(self):
        text = contained().summary()
        assert "Host:" in text
        assert "Retention:" in text
        assert "(not stated)" in text
