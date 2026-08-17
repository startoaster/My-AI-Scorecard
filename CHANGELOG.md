# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Authority weighting** (`authority.py`) — `Authority` precedence enum (statute → binding contract → regulatory guidance → technical standard → advocacy → emerging) and `AuthoritySource` attribution, so a binding agreement term and a voluntary standard no longer read the same. `UseCaseContext.get_enforceable_flags()` and `max_authority()` query it.
- **Term lexicon and conflict detection** — `Lexicon` holds multiple definitions per term rather than resolving to one, and `conflicts()` reports terms whose definitions differ across bodies. Starter set in `default_lexicon()` covers terms that recur in production AI governance.
- **Capability classification** (`capability.py`) — two independent ordered dimensions, `TransformationClass` and `ControlMode`, plus `FinalPixelRole` and `LikenessPresence`. Classification is **per region** via `RegionProfile`, so one frame can carry several governance cases. `CapabilityProfile.derive_flags()` raises flags from the classification using `DEFAULT_CAPABILITY_RULES`, which are data and can be inspected, reordered, or replaced.
- **Pipeline signal derivation** (`pipeline_signals.py`) — `GuidanceSignal` and `PipelineRecord` convert recorded pipeline values into a capability profile, so governance metadata is emitted by the workflow rather than typed into a form. Cut points are configurable via `DerivationThresholds` and travel with the record.
- **Authorship evidence records** (`authorship.py`) — `AuthorshipRecord` documents human contribution per region without determining sufficiency, since no source supplies that threshold. Reports undocumented and sparsely documented generative regions.
- **External vocabulary mapping** (`vocabulary.py`) — `VocabularyMapping` crosswalks the classification enums onto any external vocabulary without changes to rules, routing, or storage. Unmapped members translate to `None` rather than falling back to our own names.
- **Use case intake** (`intake.py`) — the facts an approval rests on, as structured fields across business context, approval context, inputs, and outputs. `DEFAULT_INTAKE_RULES` key on *combinations* (restricted input plus public-facing output; licensed music plus a capability that introduces new content; fine-tuning plus restricted material) rather than on a severity someone typed. `IPClass` is unordered by design, with `RESTRICTED_IP_CLASSES` carrying the organization's judgment.
- **Approval decisions** — `ApprovalSubject` (tool / model / workflow / fine-tuning workflow) and `ApprovalDecision` (approved / approved with constraints / approved for internal testing only / rejected), distinct from per-flag `ReviewStatus`. `record_decision()` records the outcome together with `open_findings_at_decision`, and `decision_was_contested()` reports an approval taken over an open enforceable finding.
- **Operational characteristics** (`operations.py`) — deployment host, region and update control; data residency and custodian; collection policy and retention; customer model refinement. Rules key on the pairing of an operational fact with material sensitivity, and stay silent when sensitivity is unknown rather than assuming it.
- **Tool and model sourcing** (`sourcing.py`) — vendor profile and AI posture, packaging and separability, model provisioning and origin, training-data source types and commitment period. Recorded as facts with rules, not scored dimensions.
- **Software licensing of the implementation** (`sourcing.py`) — `CodeLicensing` and `ImplementationSource` record the rights attached to the *code*, which come apart from the rights attached to the weights: a permissive model is routinely published with a reference implementation carrying no licence at all. Copyleft and restricted-use terms are separate classes because they fail differently — copyleft is an obligation attaching on distribution, a field-of-use clause is a prohibition biting on use. Four rules cover unlicensed code, copyleft held internally, copyleft redistributed, and use-restricted terms.
- **Vendor findings reach the engine** — `VendorScorecard.derive_flags()` turns recorded copyright facts and unsatisfactory questionnaire responses into authority-carrying flags. `tier_from_flags()` classifies a vendor non-compensatorily from live flag state, reading authority and severity together.
- **Provenance findings reach the engine** — `ProvenanceCard.derive_flags()` covers licence status, rights-holder reservations, unclassified origin, and synthetic share against the model collapse guard.
- **Governance events fire from the core API.** `flag_risk()`, `resolve()`, `accept_risk()`, and `begin_review()` emit `GovernanceEvent`s, so hooks see changes regardless of entry point. Previously only `web.py` emitted, which meant the derivation path — now the main way flags are created — bypassed `AuditLogger` and `ComplianceGate` entirely. All four take an `actor` argument; `web.py` passes `"web_dashboard"` and its duplicate emissions are removed, so each action fires exactly once.
- **`UseCaseContext.get_unattributed_acceptances()`** — enforceable findings accepted without naming anyone. Findable rather than forbidden.
- **`RiskFlag.is_attributed`** and **`RiskFlag.use_case_name`**, the latter carried into emitted events and serialization.
- **280 new tests** (607 total, up from 327).

### Changed

- **The framework records; it does not refuse.** An interim version had `accept_risk()` reject an unattributed acceptance of an enforceable finding, and `record_decision()` reject an approval taken over one. Neither shipped in a release, and both are gone: standing comes from an organization's delegation of authority and its identity systems, which a library cannot see, and either check was bypassable by assigning `status` directly. `ClearanceError` and `ApprovalError` do not exist. Enforcement belongs in a `GovernanceHook` — `ComplianceGate` exists for exactly this.
- **`RiskFlag.is_from_enforceable_source`** describes the finding. It replaced a name that implied a rule about who may act on it.
- **An organization's routing table always wins.** `flag_risk()` consults the configured table first and falls back to `suggested_clearance_role()` only where the table has no entry, in place of leaving a flag unassigned.
- **`evaluate_vendor()` is no longer the approval path.** Its weighted composite is compensatory: a vendor in active copyright litigation whose tool competes with its own training sources scored 95 and landed in `PREFERRED`, because `copyright_risk` was computed and never consulted by the tiering logic. It is retained for comparing vendors on documentation quality and documented as unsuitable for approving one. Use `derive_flags()` and `tier_from_flags()`.
- **`evaluate_provenance()` is unchanged and stays.** A coverage score measures how thoroughly lineage is documented, which is objective and separate from risk — `provenance_complete` can be `True` for a dataset whose licence is known to be non-compliant.

### Fixed

- **A single disqualifying copyright fact no longer reports as low risk.** `CopyrightAssessment.risk_level` required *two* of its three high-severity facts before returning `"high"`, and its medium branch tested two entirely different fields — so a vendor whose training data was not confirmed as lawfully obtained, with nothing else wrong, reported `"low"`. Same for undocumented licence verification, and for a tool competing with its own training sources. Each high-severity fact now stands on its own. Monotonicity held throughout and is now pinned by an exhaustive test over all 64 combinations.
- **Two assessment inputs had no effect at all.** `eu_dsm_article4_compliance` and `eu_training_data_summary_published` influenced neither `risk_level` nor `gaps`. They now appear in `gaps`. They deliberately stay out of `risk_level`: whether they matter depends on where the work is exploited, and `CopyrightAssessment` carries no jurisdiction to weigh that against.
- **An empty routing table can now be configured.** `UseCaseContext` used `routing_table or DEFAULT_ROUTING`, so passing `{}` silently fell back to the defaults and there was no way to switch automatic assignment off. It now distinguishes "omitted" from "explicitly empty". `tags` gets the same treatment.
- **Contexts no longer share the global default routing table.** `routing_table` and `tags` are copied on construction, so mutating one context's table no longer reconfigures every other context and `DEFAULT_ROUTING` itself.
- **`evaluate_vendor()` validates its configuration.** Custom weights were documented as needing to sum to 1.0 and never checked — a table summing to 30 returned a composite of 500 on a 0-100 scale. Weights and tier thresholds are both validated now, and an explicitly empty mapping reaches validation instead of being silently swapped for the defaults.
- **`VendorResult.dimension_scores` was documented as weighted contributions** while storing raw scores. The docstring is corrected and the weighted amounts are available as `weighted_contributions`, which sum to `overall_score`.
- **OMC expanded correctly** — `compliance.py` described MovieLabs OMC as "Open Media Cloud"; it is the **Ontology for Media Creation**.

### Documentation

- **User documentation in [`docs/`](docs/index.md)** — getting started, concepts, task-oriented guides by role, customising, integration, and an explicit limitations page covering every boundary and why it is where it is.
- **Reference documentation is generated from the code** by `scripts/gen_reference_docs.py`: all 45 default rules with their authority and severity, and every classification enum with its members. A hand-maintained copy of 45 rules would be wrong within a release.
- **`scripts/check_doc_examples.py`** executes every Python block in the docs the way a reader following along would — each document's blocks share a namespace, in order — so a snippet that depends on something never shown fails in CI rather than in a reader's terminal.

### Notes

- `RiskFlag` gains `authority`, `source`, `cleared_by`, and `use_case_name`. All default to unattributed, so existing flags, stored payloads, and `accept_risk()` calls behave exactly as before.

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
