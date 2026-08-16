# Integration

Connecting the framework to the systems around it — audit logs, ticketing,
storage, and the bundled dashboard.

## Governance events

Every lifecycle change emits a `GovernanceEvent`, from the core API rather than
from any one caller. A hook sees the same picture whether a change came from
the web dashboard, a derivation rule, or a script.

```python
from ai_use_case_context import (
    GovernanceHook, register_hook, clear_hooks,
    UseCaseContext, RiskDimension, RiskLevel, Authority,
)

class Recorder(GovernanceHook):
    def on_flag_raised(self, event):
        print("raised:", event.use_case_name, event.level,
              event.metadata["authority"])

    def on_flag_accepted(self, event):
        if event.metadata["authority"] in ("STATUTE", "BINDING_CONTRACT"):
            if not event.metadata["cleared_by"]:
                print("unattributed acceptance of an enforceable finding")

register_hook(Recorder())

ctx = UseCaseContext(name="Shot 0100")
flag = ctx.flag_risk(
    RiskDimension.LEGAL_IP, RiskLevel.HIGH, "Contract question",
    authority=Authority.BINDING_CONTRACT,
)
flag.accept_risk("proceeding")

clear_hooks()
```

Events fire on `flag_risk()`, `resolve()`, `accept_risk()`, and
`begin_review()`. Each carries the use case name, dimension, level, and
description, plus authority, source, reviewer, `cleared_by`, and status in
`metadata`.

**Actor.** Every one of those methods takes an `actor` argument, defaulting to
`"system"`. Pass something meaningful so the audit trail records what drove the
change — the bundled dashboard passes `"web_dashboard"`.

```python
flag.resolve("Fixed", actor="pipeline-hook")
```

## Built-in hooks

- **`AuditLogger`** — structured, queryable log. Takes an optional sink
  callable, so you can forward every event to Splunk, a file, or a queue.
- **`ComplianceGate`** — policy enforcement with named criteria. **This is
  where enforcement belongs.** The framework itself records rather than
  refuses; if your organization wants acceptance actually gated, express it
  here, where it can consult your identity system.
- **`NotificationBridge`** — filtered forwarding for webhooks, SIEM, or chat.

```python
from ai_use_case_context import AuditLogger, register_hook, clear_hooks

logger = AuditLogger()
register_hook(logger)
# ... work happens ...
logger.query()          # every event, filterable
clear_hooks()
```

## Persistence

`UseCaseContext` round-trips through JSON or plain dicts:

```python
from ai_use_case_context import to_json, from_json, to_dict, from_dict

blob = to_json(ctx)
restored = from_json(blob)

payload = to_dict(ctx)
restored = from_dict(payload)
```

Authority, source attribution, `cleared_by`, and the originating use case name
all survive. Payloads written before those fields existed still load — missing
keys fall back to unattributed defaults.

Custom dimensions survive too: the label is stored alongside the name so a
`Dimension` can be reconstructed on the far side.

Every profile has its own `to_dict()` / `from_dict()`:

```python
from ai_use_case_context import (
    CapabilityProfile, UseCaseProfile, OperationalProfile, SourcingProfile,
    PipelineRecord, AuthorshipRecord,
)

for profile in (
    CapabilityProfile(name="c"),
    UseCaseProfile(),
    OperationalProfile(),
    SourcingProfile(),
    PipelineRecord(stage="s"),      # thresholds travel with it
    AuthorshipRecord(work="w"),
):
    payload = profile.to_dict()
    assert type(profile).from_dict(payload) is not None
```

If you are storing a classification you may rely on later, store the
`PipelineRecord` rather than only the derived profile. The thresholds are part
of the finding, and the record carries them.

## Portfolio views

`GovernanceDashboard` aggregates across use cases:

```python
from ai_use_case_context import GovernanceDashboard

dashboard = GovernanceDashboard()
dashboard.register(ctx)

dashboard.use_cases                    # property, not a call
dashboard.blocked_use_cases()
dashboard.portfolio_risk_scores()
dashboard.dimension_summary(RiskDimension.LEGAL_IP)
dashboard.reviewer_workload()          # who is holding up what
dashboard.by_workflow_phase()
print(dashboard.summary())
```

## Escalation

Time-based escalation for findings left open:

```python
from ai_use_case_context import EscalationPolicy

policy = EscalationPolicy()
policy.check_flag(flag)                # would this escalate?
policy.check_use_case(ctx)             # which ones would
policy.apply_escalations(ctx)          # raise their levels in place
```

Defaults escalate LOW after 7 days, MEDIUM after 3, HIGH after 1. CRITICAL
"escalates" to CRITICAL after 4 hours — that is a re-notification with a
different reviewer rather than a level change, and it is intentional.

Escalation mutates flag levels directly rather than going through the flag
methods, so it does not emit lifecycle events. The dashboard emits
`FLAG_ESCALATED` itself when it applies them.

## Web dashboard

```bash
pip install -e ".[web]"
python -m ai_use_case_context
```

Serves on `http://localhost:5000` — portfolio view, per-use-case detail,
security profiles, and a seeding route for demo data. Actions taken through it
emit governance events with `actor="web_dashboard"`.

For embedding, `create_app()` returns a Flask app you can mount or test
against:

```python
import ai_use_case_context.web as web

app = web.create_app()
client = app.test_client()
client.get("/")
```

## Compliance frameworks

ISO 42001, NIST AI RMF, EU AI Act, and MovieLabs OMC alignment are available as
structured assessments:

```python
from ai_use_case_context import (
    ComplianceProfile, ISO42001Assessment, evaluate_compliance,
)

profile = ComplianceProfile(iso42001=ISO42001Assessment(aims_documented=True))
result = evaluate_compliance(profile)
result.overall_score
result.gaps
```

Note the gap: **`compliance.py` does not derive flags yet.** It produces scores
and string gaps that nothing consumes, so its findings have to be transcribed
into flags by hand. The other assessment modules have been converted; this one
has not. See [Limitations](limitations.md).
