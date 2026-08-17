# Documentation

A governance framework for AI use in media production. It records what an AI
capability does, raises findings from those facts, routes them to the people
who have to act, and keeps a record of what was decided — without deciding
anything itself.

## Start here

| If you want to | Read |
| --- | --- |
| Get something working | [Getting started](getting-started.md) |
| Understand the design | [Concepts](concepts.md) |
| Do a specific job | [Guides](guides.md) |
| Know what it won't do | [Limitations](limitations.md) |

## By role

**Production technologist, pipeline lead, or artist** proposing a use of AI —
[Getting started](getting-started.md), then *Proposing a use of AI* and
*Recording pipeline signals* in [Guides](guides.md).

**Governance or review body** — [Concepts](concepts.md) for what the findings
mean, *Reviewing a proposal* in [Guides](guides.md) for the mechanics, and
[Limitations](limitations.md) for where the framework stops and you begin.

**Engineer integrating this into a studio system** —
[Integration](integration.md) for hooks, events, and persistence;
[Customising](customising.md) for your own rules, routing, and vocabularies.

**Anyone evaluating whether to adopt it** — [Limitations](limitations.md)
first. It is the most honest page here.

## All pages

- **[Getting started](getting-started.md)** — one shot, end to end, in about ten minutes
- **[Concepts](concepts.md)** — the model, and the three decisions behind it: facts not scores, authority separate from severity, regions not shots
- **[Guides](guides.md)** — proposing a use, reviewing one, recording pipeline signals, assessing vendors and datasets, tracking authorship
- **[Customising](customising.md)** — routing, rules, sensitivity, thresholds, dimensions, lexicon, vocabularies
- **[Integration](integration.md)** — governance events, hooks, persistence, portfolio views, escalation, the dashboard
- **[Limitations](limitations.md)** — every boundary, and why it is where it is
- **[Reference: rules](reference-rules.md)** — all 45 default rules *(generated)*
- **[Reference: vocabularies](reference-vocabularies.md)** — every classification enum *(generated)*

The two reference pages are generated from the code by
`scripts/gen_reference_docs.py`. Regenerate them as part of any change to a
rule set or a classification enum.

## The one-paragraph version

Describe facts — what the operation does to the media and how much of the
recipe a human supplied, what material goes in and what comes out, where it
runs, where the models came from. Rules turn those facts into flags. Each flag
carries the **authority** behind it, so a contract term and a voluntary
standard do not read the same. Flags route, block, and get resolved or accepted
with a name attached. Then a person decides, and the record shows what was open
when they did.
