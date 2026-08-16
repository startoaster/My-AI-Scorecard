"""Tests for external vocabulary mapping."""

import pytest

from ai_use_case_context.capability import ControlMode, TransformationClass
from ai_use_case_context.vocabulary import (
    VocabularyMapping,
    get_vocabulary,
    list_vocabularies,
    register_vocabulary,
    unregister_vocabulary,
)


@pytest.fixture
def mapping():
    return VocabularyMapping(
        name="example-body",
        version="1.0",
        url="https://example.invalid/vocab",
        terms={
            TransformationClass.EXTRACTION: "ExampleTerm-Readout",
            TransformationClass.CONVERSION: "ExampleTerm-Readout",
            TransformationClass.SYNTHESIS: "ExampleTerm-Generate",
            ControlMode.COMPOSED: "ExampleTerm-Assemble",
        },
    )


@pytest.fixture(autouse=True)
def clean_registry():
    yield
    for name in list_vocabularies():
        unregister_vocabulary(name)


class TestMapping:
    def test_term_for_mapped_member(self, mapping):
        assert mapping.term_for(TransformationClass.SYNTHESIS) == "ExampleTerm-Generate"

    def test_term_for_unmapped_member_is_none(self, mapping):
        assert mapping.term_for(TransformationClass.REPAIR) is None

    def test_many_of_ours_can_map_to_one_of_theirs(self, mapping):
        # A coarser external vocabulary is expected, not an error. Splitting
        # our classes finely is what keeps this direction always expressible.
        members = mapping.members_for("ExampleTerm-Readout")
        assert set(members) == {
            TransformationClass.EXTRACTION,
            TransformationClass.CONVERSION,
        }

    def test_members_for_is_case_insensitive(self, mapping):
        assert mapping.members_for("exampleterm-generate") == [
            TransformationClass.SYNTHESIS
        ]

    def test_members_for_unknown_term(self, mapping):
        assert mapping.members_for("Nonexistent") == []

    def test_unmapped_reports_coverage_gaps(self, mapping):
        gaps = mapping.unmapped(TransformationClass)
        assert TransformationClass.REPAIR in gaps
        assert TransformationClass.SYNTHESIS not in gaps

    def test_translate_preserves_order(self, mapping):
        result = mapping.translate(
            [TransformationClass.SYNTHESIS, TransformationClass.REPAIR]
        )
        assert result == ["ExampleTerm-Generate", None]

    def test_to_dict_qualifies_member_names(self, mapping):
        keys = mapping.to_dict()["terms"]
        assert "TransformationClass.SYNTHESIS" in keys
        assert "ControlMode.COMPOSED" in keys


class TestRegistry:
    def test_register_and_get(self, mapping):
        register_vocabulary(mapping)
        assert get_vocabulary("example-body") is mapping
        assert "example-body" in list_vocabularies()

    def test_register_replaces_existing(self, mapping):
        register_vocabulary(mapping)
        replacement = VocabularyMapping(name="example-body", version="2.0")
        register_vocabulary(replacement)
        assert get_vocabulary("example-body") is replacement
        assert len(list_vocabularies()) == 1

    def test_unregister(self, mapping):
        register_vocabulary(mapping)
        assert unregister_vocabulary("example-body") is True
        assert unregister_vocabulary("example-body") is False
        assert get_vocabulary("example-body") is None

    def test_unknown_lookup_returns_none(self):
        assert get_vocabulary("never-registered") is None
