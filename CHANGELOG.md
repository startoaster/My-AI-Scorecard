# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
