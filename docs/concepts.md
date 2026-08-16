# Concepts

The mental model, and the three decisions that shape everything else.

## The shape of the thing

```
   recorded facts  ──▶  rules  ──▶  risk flags  ──▶  routing, blocking, records
   ───────────────       ─────       ──────────
   capability            data        carry an authority
   intake                not         and a source
   operations            branches
   sourcing
   vendor
   provenance
```

You describe **facts**. Rules turn facts into **flags**. Flags carry the
**authority** behind them, route to a reviewer, and make the state of a use
case answerable. Nothing in that chain decides anything on your behalf.

The unit everything attaches to is a `UseCaseContext`. Profiles are the
descriptions; `derive_flags()` is how a description reaches the context.

## Decision 1 — facts, not scores

The tempting design is a scorecard: rate each dimension 0–100, weight them,
average, compare. This framework deliberately does not work that way, for two
reasons.

**A hand-typed severity is not reproducible.** Two people assessing the same
workflow produce different numbers, and neither can say why. Structured facts —
*this operation was constrained to 0.97 of its source*, *the input is
pre-release IP*, *the vendor has pending litigation* — are checkable, and two
people recording them agree.

**Averaging hides disqualifying facts.** A weighted composite is
*compensatory*: strength in one dimension offsets failure in another. The
framework's own legacy `evaluate_vendor()` demonstrates the failure mode — a
vendor in active copyright litigation whose tool competes with its own training
sources scores 95 and lands in the top tier, because the litigation is averaged
against six other dimensions. Flags do not average. A CRITICAL finding is
CRITICAL regardless of what else is true.

Scores still appear where a score is honest. `evaluate_provenance()` measures
how *thoroughly* lineage is documented, which is an objective coverage metric.
That is a different question from whether the lineage is acceptable — a fully
documented dataset can still be unusable.

## Decision 2 — authority is separate from severity

Two flags at HIGH are not the same flag.

| | Severity | Authority |
| --- | --- | --- |
| Answers | How bad is it? | What is the force behind it? |
| Scale | `RiskLevel.NONE` → `CRITICAL` | `UNSPECIFIED` → `STATUTE` |
| Set by | The rule, from the facts | The source the rule cites |

A term written into an enforceable agreement is binding on a signatory
production. A voluntary technical standard is not. An advocacy principle is
weaker still. Collapsing them into one severity number loses the single most
important property of a finding: whether ignoring it is a breach or a
preference.

Authority drives two things: `get_enforceable_flags()` surfaces findings backed
by a statute or binding term regardless of their severity, and routing falls
back to a suggested clearance role where your table has no entry.

A related idea: a term can be **defined differently by different bodies**. The
`Lexicon` holds several definitions per term rather than picking one, and
`conflicts()` reports where they diverge — "digital replica" is defined in a
guild agreement *and* several statutes, with different thresholds.

## Decision 3 — the atomic unit is a region, not a shot

One frame can carry a performer held tightly to the recorded plate alongside a
fully generated background. Those are not the same governance case, and a
single classification for the shot misrepresents both.

So `CapabilityProfile` holds a list of `RegionProfile`, and capability rules
evaluate **per region**. A region is whatever unit your pipeline can treat
independently — a semantic mask, a layer, a shot element.

`is_uniform()` tells you whether a profile's regions actually agree. A
non-uniform profile is the interesting case.

## The two capability axes

What an operation does to the media, and how much of the recipe the human
supplied, are independent. Something can be highly novel and tightly directed,
or barely novel and entirely automatic.

```
TransformationClass   EXTRACTION → CONVERSION → ENHANCEMENT → REPAIR
                      → MODIFICATION → SYNTHESIS

ControlMode           PRESET → PARAMETERIZED → CONDITIONED → COMPOSED
```

Deliberately absent is any classification by **model architecture**. Whether a
capability runs on a diffusion model or a transformer predicts very little
about its governance treatment — the same architecture serves metadata tagging
and full scene generation. What matters is the effect on the media and the
degree of human direction.

## Derived, not asserted

Where a pipeline records how tightly each region was held to its source, the
classification can come from what actually ran rather than from a form somebody
filled in afterwards:

```python
from ai_use_case_context import PipelineRecord, GuidanceSignal, LikenessPresence

record = PipelineRecord(stage="Shot 0100", primary_region="hero_actor")
record.add_signal(GuidanceSignal(
    region="hero_actor",
    guidance_strength=0.97,          # 1.0 = fully constrained by the source
    conditioning=["depth", "segmentation", "motion"],
    region_specific=True,
    likeness=LikenessPresence.PERFORMANCE,
))

profile = record.to_capability_profile()
```

Thresholds are defaults rather than measurements, so they are configurable —
and they serialize *with* the record, because the numbers are part of the
finding.

## Where a decision lives

| Question | Answered by |
| --- | --- |
| What does this operation do? | `CapabilityProfile` — per region |
| To what material, for what audience? | `UseCaseProfile` |
| Where does it run, who holds the data? | `OperationalProfile` |
| Where do the tool and models come from? | `SourcingProfile` |
| What do we know about the vendor? | `VendorScorecard` |
| What is the dataset's lineage? | `ProvenanceCard` |
| What did a human contribute? | `AuthorshipRecord` |
| **Is it acceptable?** | **A person. Not this framework.** |

That last row is the subject of [Limitations](limitations.md), and it is worth
reading before you build on any of this.
