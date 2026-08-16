# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Authority weighting** (`authority.py`) — `Authority` precedence enum (statute → binding contract → regulatory guidance → technical standard → advocacy → emerging), `AuthoritySource` attribution, and clearance gating. Flags from an enforceable source route to the qualified clearance role regardless of dimension, and `accept_risk()` raises `ClearanceError` unless a clearing party is named.
- **Term lexicon and conflict detection** — `Lexicon` holds multiple definitions per term rather than resolving to one, and `conflicts()` reports terms whose definitions differ across bodies. Starter set in `default_lexicon()` covers terms that recur in production AI governance.
- **Capability classification** (`capability.py`) — two independent ordered dimensions, `TransformationClass` and `ControlMode`, plus `FinalPixelRole` and `LikenessPresence`. Classification is **per region** via `RegionProfile`, so one frame can carry several governance cases. `CapabilityProfile.derive_flags()` raises flags from the classification using `DEFAULT_CAPABILITY_RULES`, which are data and can be inspected, reordered, or replaced.
- **Pipeline signal derivation** (`pipeline_signals.py`) — `GuidanceSignal` and `PipelineRecord` convert recorded pipeline values into a capability profile, so governance metadata is emitted by the workflow rather than typed into a form. Cut points are configurable via `DerivationThresholds` and travel with the record.
- **Authorship evidence records** (`authorship.py`) — `AuthorshipRecord` documents human contribution per region without determining sufficiency, since no source supplies that threshold. Reports undocumented and sparsely documented generative regions.
- **External vocabulary mapping** (`vocabulary.py`) — `VocabularyMapping` crosswalks the classification enums onto any external vocabulary without changes to rules, routing, or storage. Unmapped members translate to `None` rather than falling back to our own names.
- **Use case intake** (`intake.py`) — the facts an approval rests on, as structured fields across business context, approval context, inputs, and outputs. `DEFAULT_INTAKE_RULES` key on *combinations* (restricted input plus public-facing output; licensed music plus a capability that introduces new content; fine-tuning plus restricted material) rather than on a severity someone typed. `IPClass` is unordered by design, with `RESTRICTED_IP_CLASSES` carrying the organization's judgment.
- **Approval decisions** — `ApprovalSubject` (tool / model / workflow / fine-tuning workflow) and `ApprovalDecision` (approved / approved with constraints / approved for internal testing only / rejected), distinct from per-flag `ReviewStatus`. `record_decision()` refuses to approve while a finding from an enforceable source is open, and requires a named decider; rejection is never gated.
- **Operational characteristics** (`operations.py`) — deployment host, region and update control; data residency and custodian; collection policy and retention; customer model refinement. Rules key on the pairing of an operational fact with material sensitivity, and stay silent when sensitivity is unknown rather than assuming it.
- **Tool and model sourcing** (`sourcing.py`) — vendor profile and AI posture, packaging and separability, model provisioning and origin, training-data source types and commitment period. Recorded as facts with rules, not scored dimensions.
- **Vendor findings reach the engine** — `VendorScorecard.derive_flags()` turns recorded copyright facts and unsatisfactory questionnaire responses into authority-carrying flags. `tier_from_flags()` classifies a vendor non-compensatorily from live flag state, reading authority and severity together.
- **Provenance findings reach the engine** — `ProvenanceCard.derive_flags()` covers licence status, rights-holder reservations, unclassified origin, and synthetic share against the model collapse guard.
- **236 new tests** (563 total, up from 327).

### Changed

- **`evaluate_vendor()` is no longer the approval path.** Its weighted composite is compensatory: a vendor in active copyright litigation whose tool competes with its own training sources scored 95 and landed in `PREFERRED`, because `copyright_risk` was computed and never consulted by the tiering logic. It is retained for comparing vendors on documentation quality and is documented as unsuitable for approving one. Use `derive_flags()` and `tier_from_flags()` instead.
- **`evaluate_provenance()` is unchanged and stays.** A coverage score measures how thoroughly lineage is documented, which is objective and separate from risk — `provenance_complete` can be `True` for a dataset whose licence is known to be non-compliant.

### Fixed

- **OMC expanded correctly** — `compliance.py` described MovieLabs OMC as "Open Media Cloud"; it is the **Ontology for Media Creation**.

### Notes

- `RiskFlag` gains `authority`, `source`, and `cleared_by`. All three default to unattributed, so existing flags, stored payloads, and `accept_risk()` calls behave exactly as before.

## [2.0.0a1] - 2026-02-26

### Added

- **Security dimension presets** — composable TPN, VFX, and Enterprise security profiles via `security_profile()` and `apply_security_profile()`. Custom presets via `register_preset()`.
- **Governance hook protocol** — `GovernanceHook` base class with built-in implementations: `AuditLogger` (queryable event log), `ComplianceGate` (policy enforcement with named criteria), `NotificationBridge` (filtered event forwarding). Custom hooks via subclassing.
- **Web security page** — `/security` route for applying/clearing security profiles and viewing active dimensions.
- **Governance events from web** — resolve, accept, add-flag, and review actions emit governance hook events.
- **Seed confirmation page** — `/seed` GET now shows a confirmation page; POST performs the actual seeding.

### Changed

- **BREAKING: Core dimensions expanded from 4 to 6** — `ETHICAL` split into `BIAS` (Bias/Fairness) and `SAFETY` (Safety/Harmful Output); `COMMS` replaced by `SECURITY` (Security/Model Integrity); `TECHNICAL` split into `FEASIBILITY` (Technical Feasibility) and `QUALITY` (Output Quality). Default routing table updated with 24 entries.
- **Score calculation** — composite risk score now uses `uc.dimensions()` instead of `len(RiskDimension)` to correctly account for custom dimensions.
- **246 tests** (up from 157) covering core, dashboard, escalation, serialization, web, security presets, governance hooks, custom dimensions, and web security integration.

### Fixed

- Removed unused `DEFAULT_ROUTING` import from `serialization.py`.
- Removed unused `RiskDimension` import from `escalation.py`.
- Fixed stale comment referencing old dimension name in `test_dashboard.py`.

### Migration from 1.x

- Replace `RiskDimension.ETHICAL` with `RiskDimension.BIAS` or `RiskDimension.SAFETY`
- Replace `RiskDimension.COMMS` with `RiskDimension.SECURITY`
- Replace `RiskDimension.TECHNICAL` with `RiskDimension.FEASIBILITY` or `RiskDimension.QUALITY`
- Update any code using `len(RiskDimension)` for score normalization — use `ctx.dimensions()` instead

## [1.1.0] - 2025-02-26

### Added

- **Custom risk dimensions** — define your own risk dimensions beyond the four built-in ones using `custom_dimension()`. Custom dimensions work everywhere built-in dimensions do: routing tables, dashboards, serialization, web UI, and escalation policies.
- **Web dashboard** — browser-based Flask UI for managing governance status interactively:
  - Portfolio overview with risk heatmap, blocker list, and KPI cards
  - Per-use-case score reports with composite risk bars
  - Reviewer workload view grouped by assignee
  - Flag management actions (add, resolve, accept risk, begin review)
  - Escalation alerts for stale flags
  - Seed demo data for quick evaluation
- **Python sync hooks** — subscribe to web dashboard events (`flag_resolved`, `flag_added`, etc.) from Python with `on()` / `off()`.
- **Programmatic web integration** — `create_app()`, `get_dashboard()`, `set_dashboard()` for embedding the dashboard in other Flask apps.

### Changed

- **Python version requirement lowered to 3.9+** (previously 3.10+). All modules use `from __future__ import annotations` for forward-compatible type syntax.

## [1.0.0] - 2025-02-26

### Added

- **Core governance framework** — `UseCaseContext`, `RiskFlag`, `RiskDimension`, `RiskLevel`, `ReviewStatus` classes for flag/route/block workflows.
- **Four built-in risk dimensions** — Legal/IP, Ethical/Bias/Safety, Communications/Public Perception, Technical Feasibility/Quality.
- **Five severity levels** — NONE, LOW, MEDIUM, HIGH, CRITICAL with automatic blocking behavior at HIGH and above.
- **Auto-routing** — risk flags are automatically assigned reviewers based on dimension and severity via configurable routing tables.
- **Flag lifecycle** — transitions through OPEN, IN_REVIEW, RESOLVED, ACCEPTED, BLOCKED states.
- **Portfolio dashboard** — `GovernanceDashboard` for aggregating governance status across multiple use cases.
- **Escalation policy** — `EscalationPolicy` with configurable time-based thresholds for auto-escalating stale flags.
- **Serialization** — `to_json()`/`from_json()` and `to_dict()`/`from_dict()` for persistence and API integration.
- **Examples** — runnable demos for basic usage, portfolio dashboard, escalation, and serialization.
- **157 tests** covering core classes, dashboard aggregation, escalation policies, serialization round-trips, web dashboard, and event hooks.
