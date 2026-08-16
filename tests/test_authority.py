"""Tests for authority weighting and the term lexicon."""

import pytest

from ai_use_case_context.authority import (
    Authority,
    AuthoritySource,
    Lexicon,
    TermDefinition,
    default_lexicon,
    suggested_clearance_role,
)
from ai_use_case_context.core import (
    RiskDimension,
    RiskFlag,
    RiskLevel,
    ReviewStatus,
    UseCaseContext,
)


class TestAuthority:
    def test_precedence_order(self):
        assert Authority.STATUTE.outranks(Authority.BINDING_CONTRACT)
        assert Authority.BINDING_CONTRACT.outranks(Authority.TECHNICAL_STANDARD)
        assert Authority.TECHNICAL_STANDARD.outranks(Authority.ADVOCACY)
        assert not Authority.ADVOCACY.outranks(Authority.STATUTE)

    def test_enforceable_boundary(self):
        assert Authority.STATUTE.is_enforceable
        assert Authority.BINDING_CONTRACT.is_enforceable
        assert not Authority.REGULATORY_GUIDANCE.is_enforceable
        assert not Authority.TECHNICAL_STANDARD.is_enforceable
        assert not Authority.UNSPECIFIED.is_enforceable

    def test_suggested_clearance_role_for_enforceable(self):
        assert "counsel" in suggested_clearance_role(Authority.STATUTE).lower()
        assert "counsel" in suggested_clearance_role(
            Authority.BINDING_CONTRACT
        ).lower()

    def test_label(self):
        assert Authority.BINDING_CONTRACT.label == "Binding Contract"


class TestAcceptanceIsRecordedNotPoliced:
    def _enforceable_flag(self, level=RiskLevel.HIGH):
        return RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=level,
            description="test",
            authority=Authority.BINDING_CONTRACT,
        )

    def test_unattributed_acceptance_is_allowed(self):
        # The framework cannot verify standing, and refusing would only push
        # callers into assigning status directly. It records instead.
        flag = self._enforceable_flag()
        flag.accept_risk("proceeding anyway")
        assert flag.status is ReviewStatus.ACCEPTED
        assert not flag.is_attributed

    def test_attributed_acceptance_is_recorded(self):
        flag = self._enforceable_flag()
        flag.accept_risk("reviewed", cleared_by="Jordan Reyes, Counsel")
        assert flag.status is ReviewStatus.ACCEPTED
        assert flag.cleared_by == "Jordan Reyes, Counsel"
        assert flag.is_attributed

    def test_is_from_enforceable_source_is_about_authority_not_severity(self):
        enforceable = self._enforceable_flag(level=RiskLevel.LOW)
        voluntary = RiskFlag(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.CRITICAL,
            description="t",
            authority=Authority.TECHNICAL_STANDARD,
        )
        assert enforceable.is_from_enforceable_source
        assert not voluntary.is_from_enforceable_source

    def test_resolve_records_without_gating(self):
        flag = self._enforceable_flag()
        flag.resolve("consent obtained")
        assert flag.status is ReviewStatus.RESOLVED

    def test_unattributed_acceptances_are_surfaced(self):
        ctx = UseCaseContext(name="Test")
        bare = ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.HIGH, "a",
            authority=Authority.BINDING_CONTRACT,
        )
        named = ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.HIGH, "b",
            authority=Authority.STATUTE,
        )
        voluntary = ctx.flag_risk(RiskDimension.QUALITY, RiskLevel.HIGH, "c")
        bare.accept_risk("fine")
        named.accept_risk("fine", cleared_by="Counsel")
        voluntary.accept_risk("fine")

        unattributed = ctx.get_unattributed_acceptances()
        assert [f.description for f in unattributed] == ["a"]

    def test_open_enforceable_flags_are_not_unattributed_acceptances(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.HIGH, "still open",
            authority=Authority.STATUTE,
        )
        assert ctx.get_unattributed_acceptances() == []


class TestContextAuthorityRouting:
    def test_organisation_routing_table_wins_over_suggestion(self):
        # The framework does not override an organisation's own routing.
        ctx = UseCaseContext(name="Test")
        flag = ctx.flag_risk(
            dimension=RiskDimension.QUALITY,
            level=RiskLevel.LOW,
            description="contract question surfacing under quality",
            authority=Authority.BINDING_CONTRACT,
        )
        assert flag.reviewer == "QA Lead"

    def test_suggestion_fills_only_an_unrouted_gap(self):
        sparse = {(RiskDimension.LEGAL_IP, RiskLevel.HIGH): "Named Reviewer"}
        ctx = UseCaseContext(name="Test", routing_table=sparse)
        flag = ctx.flag_risk(
            dimension=RiskDimension.QUALITY,
            level=RiskLevel.LOW,
            description="t",
            authority=Authority.BINDING_CONTRACT,
        )
        assert flag.reviewer == suggested_clearance_role(
            Authority.BINDING_CONTRACT
        )

    def test_unrouted_and_unattributed_falls_back_to_unassigned(self):
        sparse = {(RiskDimension.LEGAL_IP, RiskLevel.HIGH): "Named Reviewer"}
        ctx = UseCaseContext(name="Test", routing_table=sparse)
        flag = ctx.flag_risk(RiskDimension.QUALITY, RiskLevel.LOW, "t")
        assert flag.reviewer == "Unassigned"

    def test_non_enforceable_uses_routing_table(self):
        ctx = UseCaseContext(name="Test")
        flag = ctx.flag_risk(
            dimension=RiskDimension.QUALITY,
            level=RiskLevel.LOW,
            description="ordinary quality issue",
        )
        assert flag.reviewer == "QA Lead"

    def test_explicit_reviewer_still_wins(self):
        ctx = UseCaseContext(name="Test")
        flag = ctx.flag_risk(
            dimension=RiskDimension.LEGAL_IP,
            level=RiskLevel.HIGH,
            description="t",
            reviewer="Named Person",
            authority=Authority.STATUTE,
        )
        assert flag.reviewer == "Named Person"

    def test_get_enforceable_flags(self):
        ctx = UseCaseContext(name="Test")
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.HIGH, "binding",
            authority=Authority.BINDING_CONTRACT,
        )
        ctx.flag_risk(RiskDimension.QUALITY, RiskLevel.HIGH, "ordinary")
        enforceable = ctx.get_enforceable_flags()
        assert len(enforceable) == 1
        assert enforceable[0].description == "binding"

    def test_enforceable_flags_exclude_resolved(self):
        ctx = UseCaseContext(name="Test")
        flag = ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.HIGH, "binding",
            authority=Authority.BINDING_CONTRACT,
        )
        flag.resolve("done")
        assert ctx.get_enforceable_flags() == []

    def test_max_authority(self):
        ctx = UseCaseContext(name="Test")
        assert ctx.max_authority() is Authority.UNSPECIFIED
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.LOW, "a",
            authority=Authority.TECHNICAL_STANDARD,
        )
        ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.LOW, "b",
            authority=Authority.STATUTE,
        )
        assert ctx.max_authority() is Authority.STATUTE

    def test_flag_str_includes_authority(self):
        ctx = UseCaseContext(name="Test")
        flag = ctx.flag_risk(
            RiskDimension.LEGAL_IP, RiskLevel.HIGH, "t",
            authority=Authority.BINDING_CONTRACT,
            source=AuthoritySource(
                body="Example Body", authority=Authority.BINDING_CONTRACT
            ),
        )
        assert "Binding Contract" in str(flag)
        assert "Example Body" in str(flag)


class TestAuthoritySource:
    def test_round_trip(self):
        src = AuthoritySource(
            body="Example Body",
            authority=Authority.STATUTE,
            citation="§1",
            jurisdiction="US",
        )
        assert AuthoritySource.from_dict(src.to_dict()) == src

    def test_str_includes_parts(self):
        src = AuthoritySource(
            body="Body", authority=Authority.STATUTE,
            citation="§1", jurisdiction="US",
        )
        text = str(src)
        assert "Body" in text and "§1" in text and "US" in text


class TestLexicon:
    def test_conflicts_detects_multiple_definitions(self):
        lex = default_lexicon()
        conflicted = {c.term for c in lex.conflicts()}
        # Both terms are defined by more than one body in the starter set.
        assert "Digital Replica" in conflicted
        assert "Generative AI" in conflicted

    def test_single_source_term_is_not_a_conflict(self):
        lex = default_lexicon()
        conflicted = {c.term for c in lex.conflicts()}
        assert "Synthetic Performer" not in conflicted

    def test_governing_definition_picks_highest_authority(self):
        lex = default_lexicon()
        governing = lex.governing_definition("Digital Replica")
        assert governing is not None
        assert governing.source.authority is Authority.STATUTE

    def test_definitions_sorted_by_authority(self):
        lex = default_lexicon()
        defs = lex.definitions_for("Digital Replica")
        values = [d.source.authority.value for d in defs]
        assert values == sorted(values, reverse=True)

    def test_lookup_is_case_insensitive(self):
        lex = default_lexicon()
        assert lex.definitions_for("digital replica")

    def test_unknown_term_returns_nothing(self):
        lex = default_lexicon()
        assert lex.definitions_for("Nonexistent Term") == []
        assert lex.governing_definition("Nonexistent Term") is None

    def test_conflict_reports_jurisdictions_and_description(self):
        lex = default_lexicon()
        conflict = next(
            c for c in lex.conflicts() if c.term == "Digital Replica"
        )
        assert conflict.highest_authority is Authority.STATUTE
        assert conflict.jurisdictions  # statute entry carries one
        assert "Digital Replica" in conflict.describe()

    def test_add_and_terms(self):
        lex = Lexicon()
        assert lex.terms() == []
        lex.add(
            TermDefinition(
                term="Example",
                source=AuthoritySource(body="B", authority=Authority.ADVOCACY),
            )
        )
        assert lex.terms() == ["Example"]
        assert len(lex) == 1

    def test_term_definition_round_trip(self):
        original = TermDefinition(
            term="Example",
            source=AuthoritySource(body="B", authority=Authority.STATUTE),
            summary="s",
            threshold_notes="n",
        )
        assert TermDefinition.from_dict(original.to_dict()) == original
