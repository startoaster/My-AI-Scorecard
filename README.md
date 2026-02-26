# AI Use Case Context Framework

A generalizable governance model for AI-driven media production use cases. Provides **flag**, **route**, and **block** capabilities across risk dimensions — four built-in plus unlimited user-defined custom dimensions. Designed to integrate with PRD and taxonomy frameworks including MovieLabs OMC-aligned production workflows.

## Risk Dimensions

### Built-in Dimensions

| Dimension | Scope |
|-----------|-------|
| **Legal / IP Ownership** | Licensing, likeness rights, training data provenance |
| **Ethical / Bias / Safety** | Bias in outputs, safety concerns, fairness |
| **Communications / Public Perception** | Public backlash, guild concerns, brand risk |
| **Technical Feasibility / Quality** | Model validation, pipeline compatibility, output quality |

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
    dimension=RiskDimension.ETHICAL,
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
| **Ethical** | Ethics Review Board | Ethics Review Board | VP Ethics / Policy | C-Suite + External Ethics Advisor |
| **Comms** | Comms Coordinator | VP Communications | VP Communications + PR Agency | C-Suite + Crisis Communications |
| **Technical** | Tech Lead | VFX Supervisor | VP Technology / CTO | CTO + External Technical Review |

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
| `/seed` | Load 5 demo use cases with realistic risk flags |

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

## Running Tests

```bash
pytest
```

157 tests covering core classes, custom dimensions, dashboard aggregation, escalation policies, serialization round-trips, web dashboard pages, interactive actions, and Python sync hooks.

## Project Structure

```
ai_use_case_context/
  __init__.py          Public API exports
  __main__.py          CLI entry point (launches web dashboard)
  core.py              RiskDimension, RiskLevel, ReviewStatus, RiskFlag, UseCaseContext
  dashboard.py         GovernanceDashboard, DimensionSummary
  escalation.py        EscalationPolicy, EscalationRule, EscalationResult
  serialization.py     to_dict, from_dict, to_json, from_json
  web.py               Flask web dashboard with event hooks
tests/
  test_core.py         Core class tests
  test_dashboard.py    Dashboard aggregation tests
  test_escalation.py   Escalation policy tests
  test_serialization.py  Serialization round-trip tests
  test_web.py          Web dashboard and event hook tests
examples/
  basic_usage.py       Flag, route, block, resolve workflow
  portfolio_dashboard.py  Multi-use-case aggregation
  escalation_demo.py   Stale flag auto-escalation
  serialization_demo.py  JSON persistence
```

## License

Apache 2.0
