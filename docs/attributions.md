# Attributions

Every external standard, regulatory instrument, and published framework this
project names, draws on, or was influenced by.

Two things this page is not. It is not a claim of conformance: naming a
standard means the framework has a place to record an assessment against it,
not that any assessment has been made or validated. And it is not a claim of
endorsement or affiliation — none of the bodies below have reviewed,
approved, or are associated with this project.

## Standards and regulatory instruments

These are named directly in `ai_use_case_context/compliance.py`, which
provides structures for recording an assessment against each. See
[Limitations](limitations.md) for why that module does not derive findings.

| Instrument | Body | What the code does with it |
| --- | --- | --- |
| ISO/IEC 42001:2023 — *Information technology — Artificial intelligence — Management system* | ISO/IEC | `ISO42001Assessment`, `ISO42001Control` — records Annex A control assessments and a maturity level |
| NIST AI Risk Management Framework 1.0 (NIST AI 100-1) | NIST, U.S. Department of Commerce | `NISTAIRMFMapping`, `NISTFunction` — records scores against the Govern / Map / Measure / Manage functions |
| NIST AI 600-1 — *Generative AI Profile* | NIST, U.S. Department of Commerce | Companion profile to the above; informs the subcategory set |
| Regulation (EU) 2024/1689 — the EU AI Act | European Union | `EUAIActChecklist`, `EUAIActRiskTier`; GPAI transparency obligations cited by a vendor rule |
| Directive (EU) 2019/790 — the DSM Directive, Article 4 | European Union | Text-and-data-mining reservation; cited by sourcing, provenance, and vendor rules |
| Ontology for Media Creation (OMC) and the 2030 Vision | MovieLabs | `MovieLabsOMCAlignment`, `OMCWorkflowPhase` — records alignment with production workflow phases |

ISO and IEC standards are copyrighted works available for purchase from those
bodies. Nothing in this repository reproduces their text; the code records
whether *you* have assessed against a control, using short paraphrased labels.

## Authority sources cited by the default rules

Each of the 41 default rules carries an `AuthoritySource` naming the kind of
source behind it and the force that source carries. These are deliberately
written in general terms — the framework cannot know which agreement or
jurisdiction governs your production, and says so on every rule.

| Source | Authority | Citation as recorded | Jurisdiction |
| --- | --- | --- | --- |
| Copyright law | Statute | Applicable regime depends on where the work is exploited | — |
| Data protection law | Statute | Applicable regime depends on data subjects and processing location | — |
| EU AI Act | Statute | General-purpose AI transparency obligations | EU |
| EU DSM Directive | Statute | Article 4 text and data mining reservation | EU |
| Text and data mining reservation | Statute | Applicable regime depends on where mining occurred | — |
| Performer collective bargaining agreement | Binding contract | Applicable agreement to be confirmed for this production | — |
| Vendor agreement | Binding contract | Terms to be confirmed for this engagement | — |
| Content licence terms | Binding contract | Applicable licence to be confirmed for this material | — |
| Content licence and vendor terms | Binding contract | Training rights are commonly reserved separately | — |
| Source licence terms | Binding contract | Terms vary by source; confirm per dataset | — |
| Upstream model licence | Binding contract | Terms of the model this one was derived from | — |
| Copyright registration guidance | Regulatory guidance | Disclosure of AI-generated material in registration | — |
| No settled definition | Emerging | Human authorship threshold undecided | — |

The starter `Lexicon` in `ai_use_case_context/authority.py` contains short
**paraphrases** of public sources, present so routing rules have something to
key on. They are not contract or statutory language, and must not be relied on
as either. To regenerate the rule-level view of this table, run
`scripts/gen_reference_docs.py` and read
[Reference: rules](reference-rules.md).

## Conceptual influences

Work that shaped the design without being implemented from, or reproduced.

**The AI Filmmaking Spectrum** — Rob Bredow.
<https://rbredow.github.io/AI-Filmmaking-Spectrum/>
Informed the decision to treat *how much of the recipe a human supplied* as an
axis independent of *what the operation does to the media* — the split between
`ControlMode` and `TransformationClass` in `capability.py`.

**Creative Commons licence elements** — Creative Commons.
<https://creativecommons.org/>
The compositional idea that a small set of named, memorable elements can
combine into a legible whole is the model behind element-style classification
schemes generally. Referenced here because it is the acknowledged ancestor of
the VES draft below, not because this project implements CC licences.

## Drafts reviewed but not implemented

Both entries below are **unpublished drafts** circulated for comment. They are
listed for disclosure — so that the influence on this project's design is on
the record — and nothing from either is reproduced here.

**Da-M-I-C-Us: A classification framework for AI solutions**, Version 1.0
Draft 2, June 2026 — Visual Effects Society, Technology Committee (Michele
Sciolette et al.). Reviewed August 2026. Its Data, Model, Infrastructure and
Code dimensions overlap substantially with `sourcing.py` and `operations.py`,
and a crosswalk is the natural way to adopt it once published — see
[Customising](customising.md) for the vocabulary-mapping mechanism. Not
implemented while in draft.

**MovieLabs AI Communication Framework**, draft, May 2026 — MovieLabs.
Reviewed. Informed the general shape of separating a capability's intrinsic
description from its deployment. No terms, codes, or structures from the draft
are reproduced in this project's vocabulary.

If you are an author or rightsholder of either draft and would prefer a
different treatment here, open an issue.

## Licence of this project

Apache License 2.0. See [`LICENSE`](../LICENSE) and [`NOTICE`](../NOTICE) if
present. Attribution of *this* project is governed by that licence, not by
this page.

## Maintaining this page

Attribution lives in two places and they must agree:

1. **In code** — every rule's `AuthoritySource` carries the body, authority
   level, citation, and jurisdiction. That is the machine-readable record and
   it travels with each finding.
2. **Here** — the human-readable roll-up, including influences that leave no
   trace in a rule.

When you add a rule that cites a new source, add the source to the table
above in the same change. When you add a `VocabularyMapping` for an external
vocabulary, add it under *Conceptual influences* or a new section, with its
publisher and version.
