# AI Use Case Context Framework

> **v2.0.0-alpha.1** — This is a pre-release. APIs may change before the stable 2.0.0 release. See the [changelog](CHANGELOG.md) for breaking changes from v1.x.

A generalizable governance model for AI-driven media production use cases. Provides **flag**, **route**, and **block** capabilities across risk dimensions — six built-in plus unlimited user-defined custom dimensions. Includes configurable **security dimension presets** (TPN, VFX, Enterprise) and an open **governance hook protocol** for enterprise InfoSec integration. Designed to integrate with PRD and taxonomy frameworks including MovieLabs OMC-aligned production workflows.

## Documentation

Full documentation lives in [`docs/`](docs/index.md).

| | |
| --- | --- |
| [Getting started](docs/getting-started.md) | One shot, end to end, in about ten minutes |
| [Concepts](docs/concepts.md) | The model and the decisions behind it |
| [Guides](docs/guides.md) | Task-oriented walkthroughs by role |
| [Customising](docs/customising.md) | Your rules, routing, thresholds, vocabularies |
| [Integration](docs/integration.md) | Events, hooks, persistence, dashboard |
| [Limitations](docs/limitations.md) | What it deliberately does not do |
| [Reference](docs/reference-rules.md) | All 41 rules and every vocabulary *(generated)* |

The rest of this README is a feature overview. For anything task-shaped, the
guides are the better starting point.

## Risk Dimensions

### Built-in Dimensions

| Dimension | Scope |
|-----------|-------|
| **Legal / IP Ownership** | Licensing, likeness rights, training data provenance |
| **Bias / Fairness** | Bias in outputs, representation, demographic fairness |
| **Safety / Harmful Output** | Harmful, misleading, or unsafe model outputs |
| **Security / Model Integrity** | Model vulnerabilities, adversarial attacks, supply chain security |
| **Technical Feasibility** | Pipeline compatibility, model validation, infrastructure readiness |
| **Output Quality** | Visual/audio fidelity, resolution, production-grade quality standards |

### Custom Dimensions

Define your own risk dimensions to match your organization's governance needs:

```python
from ai_use_case_context import custom_dimension, UseCaseContext, RiskLevel

FINANCIAL = custom_dimension("FINANCIAL", "Financial Risk")
REGULATORY = custom_dimension("REGULATORY", "Regulatory Compliance")
ENVIRONMENTAL = custom_dimension("ENV", "Environmental Impact")

ctx = UseCaseContext(name="AI Data Pipeline")
ctx.flag_risk(FINANCIAL, RiskLevel.HIGH, "Budget overrun likely")
ctx.flag_risk(REGULATORY, RiskLevel.MEDIUM, "GDPR review required")
```

Custom dimensions work everywhere built-in dimensions do — routing tables, dashboards, serialization, the web UI, and escalation policies all discover and render them automatically.

Each dimension is evaluated at five severity levels:

| Level | Value | Behavior |
|-------|-------|----------|
| `NONE` | 0 | No concerns |
| `LOW` | 1 | Informational — no review needed |
| `MEDIUM` | 2 | Requires review before proceeding |
| `HIGH` | 3 | **Blocks** the workflow until resolved |
| `CRITICAL` | 4 | **Blocks** + escalates to senior leadership |

## Authority Weighting

Not every obligation carries the same force. A term written into an enforceable
agreement is binding; a voluntary technical standard is not. Flags carry an
`Authority` so that distinction survives into routing and clearance.

| Authority | Meaning |
|-----------|---------|
| `STATUTE` | Legislation or regulation |
| `BINDING_CONTRACT` | Enforceable agreement term |
| `REGULATORY_GUIDANCE` | Agency or registry guidance |
| `TECHNICAL_STANDARD` | Published voluntary standard |
| `ADVOCACY` | Principles from a convening body |
| `EMERGING` | In use but not formally published |
| `UNSPECIFIED` | No source attributed (the default) |

**The framework records; it does not adjudicate.** Whether a given person may
accept a given finding depends on an organization's delegation of authority and
its identity systems — neither of which a library can see, and a check here
would be bypassed by assigning `status` directly. So acceptance is recorded,
and the gaps are made findable:

```python
flag = ctx.flag_risk(
    RiskDimension.LEGAL_IP, RiskLevel.HIGH,
    "Performer likeness in generated output",
    authority=Authority.BINDING_CONTRACT,
)

flag.accept_risk("looks fine")                      # allowed, nobody named
flag.accept_risk("reviewed", cleared_by="Counsel")  # attributed

ctx.get_unattributed_acceptances()   # enforceable findings accepted anonymously
```

Organizations that want acceptance actually gated should express that in a
`GovernanceHook`, where it sits under their control rather than in a library
default. An organization's own routing table always wins; the authority's
suggested clearance role fills only a gap the table has no entry for.

Routing is configured per context. Omit `routing_table` for `DEFAULT_ROUTING`;
pass an empty mapping to switch automatic assignment off entirely:

```python
UseCaseContext(name="X")                      # default routing
UseCaseContext(name="X", routing_table={})    # nothing assigned automatically
```

Terms defined differently by different bodies are held as conflicts rather than
resolved to one reading:

```python
for conflict in default_lexicon().conflicts():
    print(conflict.describe())
# 'Digital Replica' is defined by 2 sources ...; wording and thresholds may differ.
```

## Capability Classification

Two independent properties drive most governance questions: what a capability
does to the media, and how much of the recipe the human supplies.

| `TransformationClass` | `ControlMode` |
|-----------------------|---------------|
| `EXTRACTION` → `CONVERSION` → `ENHANCEMENT` → `REPAIR` → `MODIFICATION` → `SYNTHESIS` | `PRESET` → `PARAMETERIZED` → `CONDITIONED` → `COMPOSED` |

Classification is **per region**, not per shot — one frame can carry a
performer held to the recorded plate alongside a fully generated background,
and those are not the same case. `FinalPixelRole` records whether the output
reaches the delivered work; `LikenessPresence` records whether a performer is
in it.

Flags follow from the classification rather than being typed in, so two people
describing the same workflow raise the same flags:

```python
profile = CapabilityProfile(name="Set extension")
profile.add_region(RegionProfile(
    region="set_extension",
    transformation=TransformationClass.SYNTHESIS,
    control=ControlMode.CONDITIONED,
    final_pixel=FinalPixelRole.DELIVERED_FRAME,
))
profile.derive_flags(ctx)
```

Rules live in `DEFAULT_CAPABILITY_RULES` as data — inspect, reorder, or replace
them by passing your own list to `derive_flags()`.

Deliberately absent is classification by model architecture: the same
architecture serves both metadata tagging and full scene generation, so it
predicts very little about governance treatment.

## Pipeline-Emitted Classification

Where a pipeline records how tightly each region was held to its source
material, classification can be derived from what actually ran instead of
asserted on a form:

```python
record = PipelineRecord(stage="Shot 0100", primary_region="hero_actor")
record.add_signal(GuidanceSignal(
    region="hero_actor",
    guidance_strength=0.97,          # 1.0 = fully constrained by the source
    conditioning=["depth", "segmentation", "motion"],
    region_specific=True,
    likeness=LikenessPresence.PERFORMANCE,
))
record.to_capability_profile().derive_flags(ctx)
```

Thresholds are defaults, not measurements — calibrate them against your own
pipeline via `DerivationThresholds`. They travel with the record, because the
numbers are part of the finding.

## Use Case Intake

A classification says what an operation does. It does not say whether doing it
*here*, to *this* material, for *this* audience, is acceptable. `UseCaseProfile`
carries those facts as structured fields across four groups — business context,
approval context, inputs, outputs.

The reason to structure them: **escalation triggers are combinations, not
severities.** Real guidance reads "these inputs, producing this output, at this
final-use potential, using this class of capability, are pre-approved; anything
else escalates." As fields, that becomes executable.

```python
intake = UseCaseProfile(
    business=BusinessContext(
        visibility=ProjectVisibility.PUBLIC,
        ip_class=IPClass.PRE_RELEASE_IP,
        commercial_nature=CommercialNature.COMMERCIAL_RELEASE,
    ),
    approval=ApprovalContext(subject=ApprovalSubject.WORKFLOW),
    inputs=InputProfile(
        ip_class=IPClass.PRE_RELEASE_IP,
        input_types=[InputType.TALENT_LIKENESS],
    ),
    outputs=OutputProfile(final_pixel=FinalPixelRole.DELIVERED_FRAME),
)
intake.derive_flags(ctx, capability=profile)
```

`IPClass` is deliberately **unordered** — which class is most restricted is an
organization's judgment, and encoding a ranking would assert a hierarchy no
source supplies. Express yours by overriding `RESTRICTED_IP_CLASSES`.

Approvals go through `record_decision()`, which captures what was still open
when the call was made:

```python
intake.record_decision(ctx, ApprovalDecision.APPROVED, decided_by="Board")
intake.decision_was_contested()               # True if it went ahead over one
intake.approval.open_findings_at_decision     # what was outstanding, verbatim
```

Approving over an outstanding finding is a call an organization is entitled to
make, and a framework that refused would only be telling reviewers they are
wrong about their own risk appetite. What the record must not do is lose the
fact that the decision was taken knowingly.

## Operational Characteristics

Where the AI runs and what happens to the data. None of this is derivable from
a capability classification: the same denoiser on-premises and in a vendor cloud
raises different questions, while a denoiser and a video model deployed
identically raise the same ones.

```python
operations = OperationalProfile(
    deployment=Deployment(host=HostEnvironment.VENDOR_CLOUD, region="US"),
    residency=DataResidency(custodian=Custodian.VENDOR),
    collection=DataCollection(
        customer_data=CollectionPolicy.COLLECTED_REQUIRED,
        retention_period="indefinite",
    ),
)
operations.derive_flags(ctx, ip_class=intake.inputs.ip_class)
```

Rules key on the **pairing** of an operational fact with material sensitivity,
because neither alone is decisive. Omit `ip_class` and the sensitivity-dependent
rules stay silent rather than assuming the worst — guessing produces flags
nobody can act on.

## Governance Events

Lifecycle events fire from the core API, not just the web dashboard. Raising,
resolving, accepting, and starting review on a flag all emit a
`GovernanceEvent`, so an `AuditLogger` or SIEM bridge sees the same picture
whether a change came from the dashboard, a derivation rule, or a script:

```python
register_hook(AuditLogger())
ctx.flag_risk(...)          # FLAG_RAISED
flag.accept_risk("ok", cleared_by="Counsel", actor="web_dashboard")  # FLAG_ACCEPTED
```

Events carry the use case, dimension, level, authority, source, reviewer, and
`cleared_by` in metadata — so an unattributed acceptance of an enforceable
finding is visible in the audit trail even though nothing refused it. `actor`
defaults to `"system"` and callers override it to say what drove the change.

## Tool and Model Sourcing

Where a tool and its models come from, recorded as facts with rules rather than
scored dimensions: vendor profile and AI posture, packaging and **separability**,
model provisioning and origin, training-data source types and **source
commitment**.

```python
sourcing = SourcingProfile(
    packaging=ToolPackaging(
        packaging=Packaging.SAAS,
        separability=Separability.NOT_SEPARABLE,
    ),
    training_data=TrainingDataProfile(
        source_types=[TrainingDataSource.WEB_CRAWL],
        commitment=SourceCommitment.NONE_STATED,
    ),
)
sourcing.derive_flags(ctx)
```

Two fields carry more weight than their size suggests. **Separability** decides
whether a restriction can be imposed technically or only asked for — user
discretion is a policy, not a control, and both it and `NOT_SEPARABLE` flag.
**Source commitment** decides whether an approval granted against today's
training corpus survives its replacement.

## Vendor and Provenance Findings

`VendorScorecard` and `ProvenanceCard` reach the governance engine through
`derive_flags()`, the same way everything else does.

```python
scorecard.derive_flags(ctx)          # copyright facts, unanswered questions
card.derive_flags(ctx, guard)        # licence status, opt-out, synthetic share
tier_from_flags(ctx)                 # VendorTier, non-compensatory
```

`tier_from_flags()` replaces the weighted composite for approval decisions.
The composite is **compensatory** — strength in one dimension offsets a
disqualifying failure in another. A vendor in active copyright litigation whose
tool competes with its own training sources scores 95 and lands in `PREFERRED`,
because `copyright_risk` was computed and never consulted by the tiering logic.
The same vendor via `derive_flags()` is `NOT_APPROVED` and blocks.

The tier reads authority and severity together: an enforceable finding always
costs at least one tier and can never be averaged away, but a low-severity
contract point that only needs confirming lands at `CONDITIONAL` rather than
disqualifying the vendor outright.

`evaluate_vendor()` is retained and still useful for comparing vendors on
documentation quality. It is not a basis for approving one.

`evaluate_provenance()` stays as-is, because a **coverage** score is a
legitimate measurement — it counts how thoroughly lineage is documented, which
is objective. That is a different question from risk: a fully documented
dataset can still be unusable, and `provenance_complete` can be `True` on a
card whose licence is known to be non-compliant. Use `derive_flags()` for the
risk, `evaluate_provenance()` for the coverage.

## Authorship Evidence

No settled authority defines how much human contribution sustains copyright in
a work incorporating AI output. This framework does not guess. It records what
a human actually contributed, per region, so whoever does decide has evidence
to evaluate:

```python
record = AuthorshipRecord.from_capability_profile(profile)
record.undocumented_regions()   # generative regions with nothing recorded
record.thin_evidence_regions()  # sparse — a reporting cut-off, not a threshold
```

`evidence_points` is a count of recorded contributions, not a score. It tells a
reviewer how much there is to look at, and nothing about whether it is enough.

## External Vocabularies

Classification uses this project's own names. `VocabularyMapping` crosswalks
them onto any external vocabulary without touching rules, routing, or storage:

```python
mapping = VocabularyMapping(name="some-body", version="1.0", terms={...})
register_vocabulary(mapping)
profile.to_external(mapping)
```

Our classes are split finely on purpose: where an external vocabulary merges
two of ours, the crosswalk maps both onto its one term. Merging is always
expressible after the fact; splitting is not. Unmapped members translate to
`None` rather than falling back to our names, so a lossy crosswalk is visible
instead of silently presenting our vocabulary as someone else's.

## Installation

```bash
pip install -e .
```

Requires Python 3.9+. No external dependencies for the core library.

For the web dashboard:

```bash
pip install -e ".[web]"
```

For development (tests):

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from ai_use_case_context import UseCaseContext, RiskDimension, RiskLevel

# Create a use case
ctx = UseCaseContext(
    name="AI Upscaling - Hero Shots",
    description="Use AI super-resolution on key character close-ups",
    workflow_phase="Element Regeneration",
)

# Flag a risk (reviewer is auto-assigned from routing table)
ctx.flag_risk(
    dimension=RiskDimension.LEGAL_IP,
    level=RiskLevel.HIGH,
    description="Character likenesses may trigger actor likeness rights",
)

# Check if workflow can proceed
if ctx.is_blocked():
    print("Blocked! Unresolved issues:", ctx.get_blockers())
else:
    print("Clear to proceed.")

# Print full governance summary
print(ctx.summary())
```

Output:
```
Use Case: AI Upscaling - Hero Shots
Phase:    Element Regeneration
Status:   🚫 BLOCKED
Flags:    1 total, 1 blocking, 1 pending review

Risk Flags:
  🟠 [Legal / IP Ownership] HIGH: Character likenesses may trigger actor likeness rights (Open)
    → Routed to: VP Legal / Business Affairs

Action needed from: VP Legal / Business Affairs
```

## Web Dashboard

The framework includes an interactive web dashboard for managing risk flags, viewing portfolio status, and tracking reviewer workload — all from a browser.

### Launch

```bash
pip install -e ".[web]"
python -m ai_use_case_context.web
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000). Click **Seed Demo Data** in the navigation bar to load five realistic use cases.

> **macOS note:** Port 5000 is used by AirPlay Receiver on macOS Monterey and later. Either disable it in System Settings > AirDrop & Handoff, or use a different port: `python -m ai_use_case_context.web --port 8080`.

### Features

- **Portfolio overview** — risk heatmap, blocker list, and KPI cards at a glance
- **Score reports** — per-use-case composite risk bars and flag breakdown
- **Reviewer workload** — see open assignments grouped by reviewer
- **Flag management** — add, resolve, accept, or begin review on flags directly from the UI
- **Escalation alerts** — stale flags are highlighted when they exceed policy thresholds

### Programmatic usage

Start the dashboard from Python and subscribe to events so your code stays in sync with actions taken in the browser:

```python
from ai_use_case_context.web import create_app, get_dashboard, on

# Register your own use cases alongside the web UI
dashboard = get_dashboard()
dashboard.register(my_use_case)

# React to web actions in Python
@on("flag_resolved")
def handle_resolve(use_case_name, flag_index, flag):
    print(f"Resolved on {use_case_name}: {flag.description}")

app = create_app()
app.run()
```

Available events: `use_case_registered`, `flag_added`, `flag_resolved`, `flag_accepted`, `flag_review_started`, `escalation_applied`, `dashboard_reset`.

## Core API

### UseCaseContext

The main governance wrapper for a single AI use case.

```python
ctx = UseCaseContext(
    name="AI Super-Resolution",
    description="Upscale archival footage to HD",
    workflow_phase="Element Regeneration",
    tags=["upscaling", "archival"],
    routing_table=None,  # uses DEFAULT_ROUTING if omitted
)
```

**Flagging:**

```python
flag = ctx.flag_risk(
    dimension=RiskDimension.BIAS,
    level=RiskLevel.MEDIUM,
    description="AI may alter skin tones unintentionally",
    reviewer="",  # auto-assigned from routing table
)
```

**Querying:**

```python
ctx.is_blocked()                                  # True if any HIGH/CRITICAL flag is unresolved
ctx.get_blockers()                                # List of blocking RiskFlag objects
ctx.get_pending_reviews()                         # Flags needing review (MEDIUM+ and OPEN)
ctx.get_reviewers_needed()                        # Deduplicated reviewer list
ctx.risk_score()                                  # {dimension_label: max_level_value}
ctx.max_risk_level()                              # Highest unresolved RiskLevel
ctx.dimensions()                                  # All dimensions (built-in + custom with flags)
ctx.get_flags_by_dimension(RiskDimension.LEGAL_IP)
ctx.get_flags_by_dimension(FINANCIAL)             # Works with custom dimensions too
ctx.get_flags_by_status(ReviewStatus.OPEN)
ctx.get_flags_by_level(RiskLevel.HIGH)
```

### RiskFlag

Individual risk flags support lifecycle transitions:

```python
flag.begin_review()                    # OPEN → IN_REVIEW
flag.resolve("Fixed the issue")        # → RESOLVED (unblocks workflow)
flag.accept_risk("Risk acknowledged")  # → ACCEPTED (unblocks workflow)
flag.mark_blocked()                    # → BLOCKED (structural issue)

flag.is_blocking   # True if HIGH/CRITICAL and not resolved/accepted
flag.needs_review  # True if MEDIUM+ and still OPEN
```

## Auto-Routing

When a risk is flagged without specifying a reviewer, one is auto-assigned from the routing table based on the dimension and severity level:

| Dimension | LOW | MEDIUM | HIGH | CRITICAL |
|-----------|-----|--------|------|----------|
| **Legal/IP** | IP Coordinator | Legal Counsel | VP Legal / Business Affairs | General Counsel + C-Suite |
| **Bias** | Fairness Analyst | Bias Review Board | VP Ethics / Policy | C-Suite + External Fairness Auditor |
| **Safety** | Safety Analyst | Safety Review Board | VP Safety / Policy | C-Suite + External Safety Advisor |
| **Security** | Security Analyst | Security Engineer | CISO / VP Security | CISO + External Security Audit |
| **Feasibility** | Tech Lead | VFX Supervisor | VP Technology / CTO | CTO + External Technical Review |
| **Quality** | QA Lead | Department Supervisor | VP Production / Post | Executive Producer + Department Head |

Override by passing a custom `routing_table` dict to `UseCaseContext`:

```python
custom_routing = {
    (RiskDimension.LEGAL_IP, RiskLevel.HIGH): "My Studio Legal Team",
}
ctx = UseCaseContext(name="...", routing_table=custom_routing)
```

Custom dimensions can also be routed:

```python
from ai_use_case_context import custom_dimension

FINANCIAL = custom_dimension("FINANCIAL", "Financial Risk")

routing = {
    (FINANCIAL, RiskLevel.HIGH): "CFO",
    (FINANCIAL, RiskLevel.CRITICAL): "CFO + Board",
}
ctx = UseCaseContext(name="...", routing_table=routing)
```

## Portfolio Dashboard

Aggregate governance status across multiple use cases:

```python
from ai_use_case_context import GovernanceDashboard

dashboard = GovernanceDashboard()
dashboard.register(use_case_1)
dashboard.register(use_case_2)
dashboard.register(use_case_3)

# Portfolio-level views
dashboard.blocked_use_cases()       # All blocked use cases
dashboard.clear_use_cases()         # All non-blocked use cases
dashboard.portfolio_risk_scores()   # Risk scores per use case

# Per-dimension aggregation
summary = dashboard.dimension_summary(RiskDimension.LEGAL_IP)
# → DimensionSummary(total_flags=3, open_flags=2, blocking_flags=1, max_level=HIGH, ...)

# Reviewer workload
workload = dashboard.reviewer_workload()
# → {"VP Legal / Business Affairs": [(use_case_name, flag), ...], ...}

# Group by workflow phase
phases = dashboard.by_workflow_phase()
# → {"Element Regeneration": [...], "Post-Production": [...], ...}

# Full summary
print(dashboard.summary())
```

## Escalation Policy

Automatically escalate stale risk flags based on configurable time thresholds:

```python
from ai_use_case_context import EscalationPolicy

policy = EscalationPolicy()

# Check which flags need escalation
results = policy.check_use_case(ctx)
for result in results:
    print(result.message)

# Apply escalations (modifies flags in-place)
applied = policy.apply_escalations(ctx)
```

**Default escalation thresholds:**

| From Level | Threshold | Escalates To |
|------------|-----------|--------------|
| LOW | 7 days | MEDIUM |
| MEDIUM | 3 days | HIGH |
| HIGH | 1 day | CRITICAL |
| CRITICAL | 4 hours | Re-notifies C-Suite |

Custom rules:

```python
from datetime import timedelta
from ai_use_case_context.escalation import EscalationRule

policy = EscalationPolicy(rules=[
    EscalationRule(
        from_level=RiskLevel.MEDIUM,
        threshold=timedelta(hours=12),
        escalate_to_level=RiskLevel.CRITICAL,
        escalate_to_reviewer="CEO",
    ),
])
```

## Serialization

Save and load use cases as JSON for persistence or API integration:

```python
from ai_use_case_context import to_json, from_json, to_dict, from_dict

# JSON round-trip
json_str = to_json(ctx, indent=2)
restored = from_json(json_str)

# Dict round-trip (for databases, APIs)
data = to_dict(ctx)
restored = from_dict(data)
```

All metadata, flag states, timestamps, and resolution notes are preserved through round-trips. Enums are serialized by name (e.g., `"CRITICAL"` not `4`), datetimes as ISO-8601 strings. Custom dimensions are preserved with their labels via a `dimension_label` field in the serialized output.

## Web Dashboard (detailed)

A browser-based dashboard for running score reports and managing governance status interactively. All data is held **in-memory** — it resets when the server restarts. Use the [serialization API](#serialization) to persist data across sessions.

### Launch

```bash
# Install Flask (required)
pip install -e ".[web]"

# Run directly
python -m ai_use_case_context

# Or with a custom port
python -m ai_use_case_context.web --port 8080
```

Then visit `http://127.0.0.1:5000` (or your custom port). Click **Seed Demo Data** in the navigation bar to load 5 sample use cases.

### Pages

| Route | Description |
|-------|-------------|
| `/` | Portfolio dashboard — KPI cards, risk heatmap, dimension overview, use case list |
| `/scores` | Score reports — composite risk bars per use case, escalation alerts |
| `/reviewers` | Reviewer workload — flags grouped by assigned reviewer |
| `/use-case/<name>` | Use case detail — flag table with action buttons, score breakdown |
| `/add-use-case` | Create a new use case |
| `/security` | Security profiles — apply TPN/VFX/Enterprise presets, manage active profile |
| `/seed` | Load 5 demo use cases with realistic risk flags (GET shows confirmation, POST seeds) |

### Interactive Actions

From each use case detail page you can:
- **Begin Review** — move a flag to In Review
- **Resolve** — mark a flag as resolved (unblocks workflow)
- **Accept Risk** — acknowledge and allow workflow to proceed
- **Add Flag** — create a new risk flag with dimension, level, and description
- **Apply Escalations** — auto-escalate stale flags per the escalation policy

### Python Integration

The web dashboard shares state with the Python API. Changes made in either direction are immediately reflected.

**Access the live dashboard from Python:**

```python
from ai_use_case_context.web import get_dashboard, set_dashboard

# Read/modify the dashboard backing the web UI
dashboard = get_dashboard()
dashboard.register(my_use_case)

# Or replace it entirely with your own
set_dashboard(my_existing_dashboard)
```

**Subscribe to web events with hooks:**

```python
from ai_use_case_context.web import on, off

@on("flag_resolved")
def handle_resolve(use_case_name, flag_index, flag):
    print(f"Resolved on {use_case_name}: {flag.description}")

# Remove a specific hook
off("flag_resolved", handle_resolve)

# Remove all hooks for an event
off("flag_resolved")
```

**Available events:**

| Event | Callback Signature |
|-------|--------------------|
| `use_case_registered` | `(use_case: UseCaseContext)` |
| `flag_added` | `(use_case_name: str, flag: RiskFlag)` |
| `flag_resolved` | `(use_case_name: str, flag_index: int, flag: RiskFlag)` |
| `flag_accepted` | `(use_case_name: str, flag_index: int, flag: RiskFlag)` |
| `flag_review_started` | `(use_case_name: str, flag_index: int, flag: RiskFlag)` |
| `escalation_applied` | `(use_case_name: str, count: int, results: list)` |
| `dashboard_reset` | `()` |

**Programmatic usage (e.g., embedding in another Flask app):**

```python
from ai_use_case_context.web import create_app, get_dashboard

app = create_app()

# Pre-populate with your data
dashboard = get_dashboard()
dashboard.register(use_case_1)
dashboard.register(use_case_2)

app.run(port=8080)
```

## Examples

Runnable examples are in the `examples/` directory:

```bash
# Basic flag/route/block workflow
python -m examples.basic_usage

# Portfolio dashboard with multiple use cases
python -m examples.portfolio_dashboard

# Time-based escalation of stale flags
python -m examples.escalation_demo

# JSON serialization round-trip
python -m examples.serialization_demo
```

## Security Dimension Presets

Pre-built security dimension packs aligned with industry standards:

```python
from ai_use_case_context.security import security_profile, apply_security_profile

# Combine TPN + VFX security dimensions
profile = security_profile("tpn", "vfx")

# Apply to a use case (merges routing tables)
apply_security_profile(ctx, profile)

# Now security dimensions auto-route like built-in ones
ctx.flag_risk(TPN_CONTENT_SECURITY, RiskLevel.HIGH, "No watermarking")
```

| Preset | Dimensions | Aligned With |
|--------|-----------|--------------|
| **TPN** (6) | Content Security, Physical Security, Digital Security, Asset Management, Incident Response, Personnel Security | MPA Trusted Partner Network |
| **VFX** (6) | Secure Transfer, Render Farm Isolation, Workstation Security, Cloud/Hybrid Security, Data Classification, Vendor Security | VFX platform best practices |
| **Enterprise** (5) | Access Control (IAM), Audit Trail, Data Privacy (GDPR/CCPA), Regulatory Compliance, Business Continuity/DR | ISO 27001 / SOC 2 / NIST |

Register your own presets:

```python
from ai_use_case_context.security import register_preset

register_preset("studio_custom", MY_DIMS, MY_ROUTING)
profile = security_profile("tpn", "studio_custom")
```

## Governance Hooks (Enterprise Integration)

Open extension point for InfoSec, compliance, and audit systems:

```python
from ai_use_case_context.governance_hooks import (
    GovernanceHook, register_hook, AuditLogger, ComplianceGate, NotificationBridge,
)

# Audit logger — records all governance events
logger = AuditLogger()
register_hook(logger)

# Compliance gate — blocks on criteria failure
gate = ComplianceGate()
gate.add_criterion("no_critical", lambda e: e.level != "CRITICAL")
passed, failed = gate.evaluate(event)

# Notification bridge — forward to Slack/PagerDuty/SIEM
bridge = NotificationBridge(
    callback=lambda d: requests.post(WEBHOOK_URL, json=d),
    event_filter=lambda e: e.level in ("HIGH", "CRITICAL"),
)
register_hook(bridge)

# Or write your own
class SIEMHook(GovernanceHook):
    def on_flag_raised(self, event):
        send_to_siem(event.to_dict())
    def on_flag_escalated(self, event):
        page_on_call(event)
```

## Running Tests

```bash
pytest
```

246 tests covering core classes, custom dimensions, security presets, governance hooks, dashboard aggregation, escalation policies, serialization round-trips, web dashboard pages, interactive actions, and Python sync hooks.

## Project Structure

```
ai_use_case_context/
  __init__.py          Public API exports
  __main__.py          CLI entry point (launches web dashboard)
  core.py              RiskDimension, RiskLevel, ReviewStatus, RiskFlag, UseCaseContext
  dashboard.py         GovernanceDashboard, DimensionSummary
  escalation.py        EscalationPolicy, EscalationRule, EscalationResult
  serialization.py     to_dict, from_dict, to_json, from_json
  security.py          TPN/VFX/Enterprise security presets, SecurityProfile, preset registry
  governance_hooks.py  GovernanceHook protocol, AuditLogger, ComplianceGate, NotificationBridge
  web.py               Flask web dashboard, hooks, Python sync API
tests/
  test_core.py               Core class tests
  test_custom_dimensions.py  Custom dimension tests across all layers
  test_dashboard.py          Dashboard aggregation tests
  test_escalation.py         Escalation policy tests
  test_serialization.py      Serialization round-trip tests
  test_web.py                Web dashboard, actions, hooks, and sync tests
  test_security.py           Security preset and profile tests
  test_governance_hooks.py   Governance hook protocol tests
  test_web_security.py       Security profile web integration tests
examples/
  basic_usage.py            Flag, route, block, resolve workflow
  portfolio_dashboard.py    Multi-use-case aggregation
  escalation_demo.py        Stale flag auto-escalation
  serialization_demo.py     JSON persistence
  security_governance.py    TPN/VFX security + governance hooks demo
```

## License

Apache 2.0
