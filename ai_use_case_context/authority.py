"""
Authority weighting for governance findings.

Not every governance obligation carries the same force. A definition written
into an enforceable collective bargaining agreement is binding on a signatory
production; a voluntary technical standard is not; an advocacy principle is
weaker still. Treating all of them as interchangeable booleans — which is what
a flat checklist does — loses the single most important property of a finding:
whether ignoring it is a breach or a preference.

This module adds that property. An :class:`Authority` value ranks the force of
the source behind a finding, and :class:`AuthoritySource` records which body
said it and where. Findings backed by an enforceable source cannot be silently
self-cleared (see :meth:`RiskFlag.accept_risk`); they require an attributed
clearance from a qualified reviewer.

A second problem this module addresses is *definitional conflict*. Some terms
are defined in more than one place, by bodies of differing authority, with
materially different wording and thresholds. "Digital replica" is the canonical
example: it is defined in guild agreements and, separately, in several state
statutes and a pending federal proposal, and the definitions do not agree.
:class:`Lexicon` holds multiple definitions per term and reports where they
diverge, so a use case sitting near a contested threshold can be routed rather
than silently resolved against whichever definition happened to be consulted.

.. warning::
   Definition summaries in :func:`default_lexicon` are short non-authoritative
   paraphrases included to support routing decisions. They are **not** contract
   or statutory language and must not be relied on as such. Consult the source
   documents for operative wording.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------

class Authority(Enum):
    """How much force the source behind a finding carries.

    Values are ordered by precedence — a higher value outranks a lower one when
    two sources speak to the same question.

      UNSPECIFIED          - No source attributed. The default.
      EMERGING             - Terminology in use but not formally published.
      ADVOCACY             - Principles from a convening or advocacy body.
      TECHNICAL_STANDARD   - Published standard, vocabulary, or engineering
                             report. Voluntary adoption.
      REGULATORY_GUIDANCE  - Guidance from an agency or registry. Not itself
                             law, but determines how a body will act.
      BINDING_CONTRACT     - Enforceable agreement term (e.g. a collective
                             bargaining agreement a production is signatory to).
      STATUTE              - Legislation or regulation with the force of law.
    """
    UNSPECIFIED = 0
    EMERGING = 1
    ADVOCACY = 2
    TECHNICAL_STANDARD = 3
    REGULATORY_GUIDANCE = 4
    BINDING_CONTRACT = 5
    STATUTE = 6

    @property
    def is_enforceable(self) -> bool:
        """True if breaching this source has legal or contractual consequence."""
        return self.value >= Authority.BINDING_CONTRACT.value

    @property
    def label(self) -> str:
        """Human-readable label."""
        return self.name.replace("_", " ").title()

    def outranks(self, other: "Authority") -> bool:
        """True if this authority takes precedence over ``other``."""
        return self.value > other.value


# Who must sign off before a finding at a given authority can be accepted.
# Findings from enforceable sources are not self-clearable — the framework
# surfaces them and routes them, but the determination belongs to a human with
# standing to make it.
CLEARANCE_ROLE: dict[Authority, str] = {
    Authority.STATUTE: "Qualified legal counsel",
    Authority.BINDING_CONTRACT: "Qualified legal counsel or labor relations",
    Authority.REGULATORY_GUIDANCE: "Compliance lead",
    Authority.TECHNICAL_STANDARD: "Department supervisor",
    Authority.ADVOCACY: "Department supervisor",
    Authority.EMERGING: "Department supervisor",
    Authority.UNSPECIFIED: "Department supervisor",
}


def required_clearance_role(authority: Authority) -> str:
    """Return the role required to clear a finding at this authority level."""
    return CLEARANCE_ROLE.get(authority, "Department supervisor")


class ClearanceError(RuntimeError):
    """Raised when a finding from an enforceable source is cleared without
    an attributed, qualified reviewer."""


# ---------------------------------------------------------------------------
# Sources and definitions
# ---------------------------------------------------------------------------

@dataclass
class AuthoritySource:
    """Where a governance finding comes from.

    Attributes:
        body:         Organization or instrument (e.g. a guild, a standards
                      body, a statute).
        authority:    Force the source carries.
        citation:     Document, section, or agreement reference.
        jurisdiction: Where it applies, if geographically bounded. Empty means
                      the source is not jurisdictional (e.g. a contract term
                      or a voluntary standard).
    """
    body: str
    authority: Authority = Authority.UNSPECIFIED
    citation: str = ""
    jurisdiction: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "body": self.body,
            "authority": self.authority.name,
            "citation": self.citation,
            "jurisdiction": self.jurisdiction,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuthoritySource":
        return cls(
            body=data["body"],
            authority=Authority[data.get("authority", "UNSPECIFIED")],
            citation=data.get("citation", ""),
            jurisdiction=data.get("jurisdiction", ""),
        )

    def __str__(self) -> str:
        parts = [self.body]
        if self.citation:
            parts.append(self.citation)
        if self.jurisdiction:
            parts.append(f"[{self.jurisdiction}]")
        return " — ".join(parts)


@dataclass
class TermDefinition:
    """One body's definition of a term.

    ``summary`` is a short paraphrase for routing purposes only — never
    operative language. See the module docstring warning.
    """
    term: str
    source: AuthoritySource
    summary: str = ""
    threshold_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "term": self.term,
            "source": self.source.to_dict(),
            "summary": self.summary,
            "threshold_notes": self.threshold_notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TermDefinition":
        return cls(
            term=data["term"],
            source=AuthoritySource.from_dict(data["source"]),
            summary=data.get("summary", ""),
            threshold_notes=data.get("threshold_notes", ""),
        )


@dataclass
class TermConflict:
    """A term defined by more than one source, where the definitions may not
    agree on scope or threshold."""
    term: str
    definitions: list[TermDefinition] = field(default_factory=list)

    @property
    def highest_authority(self) -> Authority:
        return max(
            (d.source.authority for d in self.definitions),
            key=lambda a: a.value,
            default=Authority.UNSPECIFIED,
        )

    @property
    def jurisdictions(self) -> list[str]:
        return sorted({
            d.source.jurisdiction for d in self.definitions if d.source.jurisdiction
        })

    def describe(self) -> str:
        bodies = ", ".join(d.source.body for d in self.definitions)
        return (
            f"'{self.term}' is defined by {len(self.definitions)} sources "
            f"({bodies}); wording and thresholds may differ. Highest authority: "
            f"{self.highest_authority.label}."
        )


class Lexicon:
    """A collection of term definitions drawn from multiple bodies.

    The point of holding several definitions per term rather than picking one
    is that picking one hides the disagreement. :meth:`conflicts` surfaces it.
    """

    def __init__(self, definitions: Optional[list[TermDefinition]] = None):
        self._definitions: list[TermDefinition] = list(definitions or [])

    def add(self, definition: TermDefinition) -> None:
        self._definitions.append(definition)

    def terms(self) -> list[str]:
        return sorted({d.term for d in self._definitions})

    def definitions_for(self, term: str) -> list[TermDefinition]:
        """All definitions of ``term``, highest authority first."""
        matches = [
            d for d in self._definitions if d.term.lower() == term.lower()
        ]
        return sorted(
            matches, key=lambda d: d.source.authority.value, reverse=True
        )

    def governing_definition(self, term: str) -> Optional[TermDefinition]:
        """The highest-authority definition of ``term``, if any.

        Where several sources tie at the top authority level, this returns the
        first and :meth:`conflicts` will still report the term — a tie between
        enforceable sources is precisely the case a human needs to resolve.
        """
        matches = self.definitions_for(term)
        return matches[0] if matches else None

    def conflicts(self) -> list[TermConflict]:
        """Terms carrying more than one definition."""
        grouped: dict[str, list[TermDefinition]] = {}
        for d in self._definitions:
            grouped.setdefault(d.term, []).append(d)
        return [
            TermConflict(term=term, definitions=defs)
            for term, defs in sorted(grouped.items())
            if len(defs) > 1
        ]

    def __len__(self) -> int:
        return len(self._definitions)

    def __repr__(self) -> str:
        return f"Lexicon(terms={len(self.terms())}, definitions={len(self)})"


def default_lexicon() -> Lexicon:
    """A starter lexicon of terms that recur in production AI governance.

    Summaries are short non-authoritative paraphrases of public sources,
    included so that routing rules have something to key on. They are not
    contract or statutory language. Extend or replace this for your own
    jurisdictions and agreements.
    """
    return Lexicon([
        TermDefinition(
            term="Generative AI",
            source=AuthoritySource(
                body="Writers Guild of America",
                authority=Authority.BINDING_CONTRACT,
                citation="2023 MBA",
            ),
            summary=(
                "A subset of AI that learns patterns from data and produces "
                "content on that basis. Excludes 'traditional AI' such as "
                "CGI/VFX and tools performing operational or analytical "
                "functions."
            ),
            threshold_notes=(
                "The exclusion matters more than the inclusion: utility and "
                "finishing operations may fall outside the defined term."
            ),
        ),
        TermDefinition(
            term="Generative AI",
            source=AuthoritySource(
                body="SAG-AFTRA",
                authority=Authority.BINDING_CONTRACT,
                citation="2025 Commercials",
            ),
            summary=(
                "A subset of AI that learns patterns from data and produces "
                "content on that basis. Excludes 'traditional AI' programmed "
                "for specific functions such as CGI/VFX."
            ),
            threshold_notes="Closely aligned with the WGA formulation.",
        ),
        TermDefinition(
            term="Digital Replica",
            source=AuthoritySource(
                body="SAG-AFTRA",
                authority=Authority.BINDING_CONTRACT,
                citation="2023 TV/Theatrical",
            ),
            summary=(
                "A replica of a performer's voice and/or likeness created "
                "using digital technology. Principal subtypes distinguish "
                "employment-based from independently created replicas."
            ),
            threshold_notes=(
                "Consent and compensation obligations attach differently by "
                "subtype."
            ),
        ),
        TermDefinition(
            term="Digital Replica",
            source=AuthoritySource(
                body="State and proposed federal law",
                authority=Authority.STATUTE,
                citation="e.g. Cal. Lab. Code §927; TN ELVIS Act; NO FAKES (proposed)",
                jurisdiction="US (varies by state)",
            ),
            summary=(
                "Defined separately in several statutes, with differing "
                "wording and differing 'materially altered' thresholds."
            ),
            threshold_notes=(
                "Most likely term in this set to carry conflicting meanings "
                "across sources. Confirm which definition governs before "
                "relying on any single one."
            ),
        ),
        TermDefinition(
            term="Synthetic Performer",
            source=AuthoritySource(
                body="SAG-AFTRA",
                authority=Authority.BINDING_CONTRACT,
                citation="2023 TV/Theatrical",
            ),
            summary=(
                "A digitally created asset intended to give the clear "
                "impression of a human performer while not being recognizable "
                "as an identifiable natural performer."
            ),
            threshold_notes="Single-source term; no competing definition.",
        ),
        TermDefinition(
            term="Digital Alteration",
            source=AuthoritySource(
                body="SAG-AFTRA",
                authority=Authority.BINDING_CONTRACT,
                citation="2023 TV/Theatrical",
            ),
            summary=(
                "Digital alteration of a performer's actual recorded "
                "performance — distinct from a replica of that performer."
            ),
            threshold_notes=(
                "The distinction from Digital Replica turns on whether the "
                "delivered performance originates in the recorded plate."
            ),
        ),
        TermDefinition(
            term="Sufficient Human Authorship",
            source=AuthoritySource(
                body="No settled definition",
                authority=Authority.EMERGING,
                citation="",
            ),
            summary=(
                "The threshold of human contribution required for copyright "
                "protection of a work incorporating AI output. Undecided in "
                "case law and undefined by industry bodies."
            ),
            threshold_notes=(
                "No source supplies a threshold. The framework can record "
                "evidence of human contribution but cannot determine "
                "sufficiency — see the authorship module."
            ),
        ),
    ])
