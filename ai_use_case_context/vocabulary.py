"""
External vocabulary mapping.

The classification enums in :mod:`ai_use_case_context.capability` use this
project's own names. Other bodies publish — or will publish — their own
vocabularies for the same underlying distinctions, and an organization will
want to speak whichever one its counterparties use.

This module keeps that swap cheap. A :class:`VocabularyMapping` is a named,
versioned crosswalk between our enum members and an external vocabulary's
terms. Registering one is a data change, not a code change: nothing in the
framework's logic keys on external names, so adopting a vocabulary later
requires no edits to rules, routing, or storage.

Two design choices exist to keep future mappings possible:

* **Classes are ordered and finely split.** Where an external vocabulary
  merges two of our classes, the crosswalk maps both of ours onto its one
  term. Merging is always expressible; splitting after the fact is not. That
  is why, for example, extraction and modality conversion are separate members
  here even though some vocabularies treat them as one.
* **Mappings are many-to-one in both directions.** :meth:`VocabularyMapping.term_for`
  answers "what would they call this", and :meth:`VocabularyMapping.members_for`
  answers "which of ours does their term cover".

Example::

    mapping = VocabularyMapping(
        name="example-body", version="1.0",
        terms={
            TransformationClass.EXTRACTION: "Information Extraction",
            TransformationClass.CONVERSION: "Information Extraction",
        },
    )
    register_vocabulary(mapping)
    mapping.term_for(TransformationClass.CONVERSION)  # "Information Extraction"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


@dataclass
class VocabularyMapping:
    """A crosswalk between our classification members and external terms.

    Attributes:
        name:     Identifier for the external vocabulary.
        version:  Version of that vocabulary this mapping targets.
        terms:    Our enum member -> the external term for it. Several of our
                  members may map to the same external term.
        url:      Where the external vocabulary is published, if anywhere.
        notes:    Anything a reader needs in order to trust the crosswalk —
                  known imprecision, terms deliberately left unmapped.
    """
    name: str
    version: str = ""
    terms: dict[Enum, str] = field(default_factory=dict)
    url: str = ""
    notes: str = ""

    def term_for(self, member: Enum) -> Optional[str]:
        """The external term for one of our members, or None if unmapped."""
        return self.terms.get(member)

    def members_for(self, term: str) -> list[Enum]:
        """Every one of our members that the external term covers.

        More than one is normal and not an error — it means the external
        vocabulary is coarser than ours at that point.
        """
        return [
            member
            for member, mapped in self.terms.items()
            if mapped.lower() == term.lower()
        ]

    def unmapped(self, enum_cls: type[Enum]) -> list[Enum]:
        """Members of ``enum_cls`` this mapping does not cover.

        Worth checking before relying on a mapping: an unmapped member means
        the external vocabulary has no term for a case we can express, and
        translated output will be silently lossy there.
        """
        return [m for m in enum_cls if m not in self.terms]

    def translate(self, members: list[Enum]) -> list[Optional[str]]:
        """Translate several members at once, preserving order."""
        return [self.term_for(m) for m in members]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "url": self.url,
            "notes": self.notes,
            "terms": {
                f"{type(m).__name__}.{m.name}": t for m, t in self.terms.items()
            },
        }

    def __repr__(self) -> str:
        return (
            f"VocabularyMapping(name={self.name!r}, "
            f"version={self.version!r}, terms={len(self.terms)})"
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_VOCABULARIES: dict[str, VocabularyMapping] = {}


def register_vocabulary(mapping: VocabularyMapping) -> VocabularyMapping:
    """Register a vocabulary mapping under its name. Replaces any existing."""
    _VOCABULARIES[mapping.name] = mapping
    return mapping


def unregister_vocabulary(name: str) -> bool:
    """Remove a registered mapping. Returns True if one was removed."""
    return _VOCABULARIES.pop(name, None) is not None


def get_vocabulary(name: str) -> Optional[VocabularyMapping]:
    """Look up a registered mapping by name."""
    return _VOCABULARIES.get(name)


def list_vocabularies() -> list[str]:
    """Names of all registered vocabulary mappings."""
    return sorted(_VOCABULARIES)
