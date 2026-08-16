"""Tests for tool and model sourcing facts and their rules."""

import pytest

from ai_use_case_context.authority import Authority
from ai_use_case_context.core import RiskDimension, RiskLevel, UseCaseContext
from ai_use_case_context.sourcing import (
    AIPosture,
    BYOPolicy,
    DEFAULT_SOURCING_RULES,
    ModelOrigin,
    ModelProvisioning,
    Packaging,
    Separability,
    SourceCommitment,
    SourcingProfile,
    SourcingRule,
    ToolPackaging,
    TrainingDataProfile,
    TrainingDataSource,
    VendorProfile,
)


def clean() -> SourcingProfile:
    """A well-documented, separable, committed profile that fires no rules."""
    return SourcingProfile(
        vendor=VendorProfile(name="V", headquarters="US",
                             postures=[AIPosture.OWN_MODELS]),
        packaging=ToolPackaging(
            packaging=Packaging.DESKTOP_SOFTWARE,
            separability=Separability.CUSTOMER_CONFIGURABLE,
        ),
        model_provisioning=ModelProvisioning(
            origins=[ModelOrigin.VENDOR_TRAINED],
            byo_policy=BYOPolicy.NOT_SUPPORTED,
        ),
        training_data=TrainingDataProfile(
            source_types=[TrainingDataSource.COMMERCIALLY_LICENSED],
            commitment=SourceCommitment.TOOL_LIFETIME,
        ),
    )


def fired(p: SourcingProfile) -> set:
    return {r.rule_id for r in DEFAULT_SOURCING_RULES if r.applies(p)}


class TestEnums:
    def test_separability_enforceable_by_configuration(self):
        assert Separability.CUSTOMER_CONFIGURABLE.is_enforceable_by_configuration
        assert Separability.VENDOR_CONFIGURABLE.is_enforceable_by_configuration
        # User discretion is a policy, not a control.
        assert not Separability.USER_DISCRETION.is_enforceable_by_configuration
        assert not Separability.NOT_SEPARABLE.is_enforceable_by_configuration

    def test_model_origin_derived(self):
        assert ModelOrigin.DERIVED_FROM_OPEN_WEIGHTS.is_derived
        assert ModelOrigin.DERIVED_FROM_COMMERCIAL.is_derived
        assert not ModelOrigin.VENDOR_TRAINED.is_derived
        assert not ModelOrigin.OPEN_WEIGHTS.is_derived

    def test_training_data_documented(self):
        assert not TrainingDataProfile().is_documented
        assert TrainingDataProfile(
            source_types=[TrainingDataSource.PUBLIC_DOMAIN]
        ).is_documented

    def test_has_derived_models(self):
        assert not ModelProvisioning(
            origins=[ModelOrigin.VENDOR_TRAINED]
        ).has_derived_models
        assert ModelProvisioning(
            origins=[ModelOrigin.VENDOR_TRAINED,
                     ModelOrigin.DERIVED_FROM_COMMERCIAL]
        ).has_derived_models


class TestBaseline:
    def test_clean_profile_fires_nothing(self):
        assert fired(clean()) == set()


class TestRules:
    def test_undocumented_training_data(self):
        p = clean()
        p.training_data = TrainingDataProfile()
        assert "TRAINING_SOURCES_UNDOCUMENTED" in fired(p)
        # The commitment rule needs documented sources to be meaningful.
        assert "NO_SOURCE_COMMITMENT" not in fired(p)

    def test_web_crawl_flags_under_statute(self):
        p = clean()
        p.training_data.source_types.append(TrainingDataSource.WEB_CRAWL)
        assert "WEB_CRAWL_TRAINING_DATA" in fired(p)
        rule = next(
            r for r in DEFAULT_SOURCING_RULES
            if r.rule_id == "WEB_CRAWL_TRAINING_DATA"
        )
        assert rule.authority is Authority.STATUTE

    def test_distillation_flags_under_contract(self):
        p = clean()
        p.training_data.source_types.append(
            TrainingDataSource.DISTILLED_FROM_MODEL
        )
        rule = next(
            r for r in DEFAULT_SOURCING_RULES
            if r.rule_id == "DISTILLED_FROM_ANOTHER_MODEL"
        )
        assert rule.applies(p)
        assert rule.authority is Authority.BINDING_CONTRACT

    def test_synthetic_training_data_is_a_quality_concern(self):
        p = clean()
        p.training_data.source_types.append(
            TrainingDataSource.ALGORITHMICALLY_GENERATED
        )
        rule = next(
            r for r in DEFAULT_SOURCING_RULES
            if r.rule_id == "SYNTHETIC_TRAINING_DATA"
        )
        assert rule.applies(p)
        assert rule.dimension is RiskDimension.QUALITY

    def test_derived_model_licence_chain(self):
        p = clean()
        p.model_provisioning.origins.append(
            ModelOrigin.DERIVED_FROM_OPEN_WEIGHTS
        )
        assert "DERIVED_MODEL_LICENCE_CHAIN" in fired(p)

    def test_no_source_commitment(self):
        p = clean()
        p.training_data.commitment = SourceCommitment.NONE_STATED
        assert "NO_SOURCE_COMMITMENT" in fired(p)

    def test_date_bound_commitment_does_not_flag(self):
        p = clean()
        p.training_data.commitment = SourceCommitment.DATE_BOUND
        p.training_data.commitment_date = "2028-01-01"
        assert "NO_SOURCE_COMMITMENT" not in fired(p)

    def test_not_separable_flags(self):
        p = clean()
        p.packaging.separability = Separability.NOT_SEPARABLE
        assert "CAPABILITIES_NOT_SEPARABLE" in fired(p)

    def test_user_discretion_also_flags(self):
        # A guideline everyone must remember is not a control.
        p = clean()
        p.packaging.separability = Separability.USER_DISCRETION
        assert "CAPABILITIES_NOT_SEPARABLE" in fired(p)

    def test_vendor_configurable_does_not_flag(self):
        p = clean()
        p.packaging.separability = Separability.VENDOR_CONFIGURABLE
        assert "CAPABILITIES_NOT_SEPARABLE" not in fired(p)

    def test_unrestricted_byo_flags_security(self):
        p = clean()
        p.model_provisioning.byo_policy = BYOPolicy.ANY_MODEL
        rule = next(
            r for r in DEFAULT_SOURCING_RULES
            if r.rule_id == "UNRESTRICTED_BYO_MODELS"
        )
        assert rule.applies(p)
        assert rule.dimension is RiskDimension.SECURITY

    def test_specific_byo_models_do_not_flag(self):
        p = clean()
        p.model_provisioning.byo_policy = BYOPolicy.SPECIFIC_MODELS
        assert "UNRESTRICTED_BYO_MODELS" not in fired(p)


class TestDeriveFlags:
    def test_flags_land_on_context(self):
        ctx = UseCaseContext(name="Tool review")
        p = clean()
        p.training_data.source_types.append(TrainingDataSource.WEB_CRAWL)
        p.packaging.separability = Separability.NOT_SEPARABLE
        flags = p.derive_flags(ctx)
        assert len(flags) == 2
        assert ctx.is_blocked()
        assert ctx.get_enforceable_flags()

    def test_custom_rules_replace_defaults(self):
        ctx = UseCaseContext(name="T")
        catch_all = SourcingRule(
            rule_id="ALWAYS",
            title="fires always",
            applies=lambda p: True,
            dimension=RiskDimension.QUALITY,
            level=RiskLevel.LOW,
            describe=lambda p: "always",
        )
        flags = clean().derive_flags(ctx, rules=[catch_all])
        assert [f.description for f in flags] == ["always"]

    def test_empty_rules_derive_nothing(self):
        ctx = UseCaseContext(name="T")
        assert clean().derive_flags(ctx, rules=[]) == []


class TestSerialization:
    def test_round_trip(self):
        p = SourcingProfile(
            vendor=VendorProfile(
                name="V", headquarters="FR",
                operating_locations=["FR", "US"],
                postures=[AIPosture.OPEN_SOURCE_MODELS,
                          AIPosture.CUSTOMIZES_THIRD_PARTY],
                notes="n",
            ),
            packaging=ToolPackaging(
                packaging=Packaging.PIPELINE_NODE,
                separability=Separability.USER_DISCRETION,
            ),
            model_provisioning=ModelProvisioning(
                vendor_models=["m1"],
                origins=[ModelOrigin.DERIVED_FROM_COMMERCIAL],
                model_provider_headquarters="US",
                byo_policy=BYOPolicy.SPECIFIC_MODELS,
            ),
            training_data=TrainingDataProfile(
                source_types=[TrainingDataSource.WEB_CRAWL,
                              TrainingDataSource.PUBLIC_DOMAIN],
                named_datasets=["d1"],
                commitment=SourceCommitment.DATE_BOUND,
                commitment_date="2030-01-01",
            ),
            notes="n",
        )
        assert SourcingProfile.from_dict(p.to_dict()) == p

    def test_summary_marks_undocumented_training_data(self):
        p = clean()
        p.training_data = TrainingDataProfile()
        assert "(not documented)" in p.summary()
