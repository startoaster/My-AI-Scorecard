## What's New

This is the first alpha of the v2 governance framework, introducing security presets, a governance hook protocol, and a restructured risk dimension model.

### Breaking Changes

- **Core dimensions expanded from 4 to 6** — `ETHICAL` split into `BIAS` and `SAFETY`; `TECHNICAL` split into `FEASIBILITY` and `QUALITY`; `COMMS` replaced by `SECURITY`. Default routing table updated with 24 entries.

### Added

- **Security dimension presets** — composable TPN, VFX, and Enterprise security profiles via `security_profile()` and `apply_security_profile()`. Custom presets via `register_preset()`.
- **Governance hook protocol** — `GovernanceHook` base class with `AuditLogger`, `ComplianceGate`, and `NotificationBridge` implementations. Subscribe to governance events for audit logging, policy enforcement, and notifications.
- **Web security page** — `/security` route for applying/clearing security profiles.
- **Governance events from web** — resolve, accept, add-flag, and review actions emit governance hook events.
- **Seed confirmation page** — `/seed` now shows a confirmation before seeding demo data.

### Fixed

- Score calculation uses `uc.dimensions()` instead of `len(RiskDimension)` to correctly account for custom dimensions.
- Removed unused imports from `serialization.py` and `escalation.py`.

### Testing

- **246 tests** (up from 157) covering security presets, governance hooks, custom dimensions, and web integration.

### Migration from 1.x

- Replace `RiskDimension.ETHICAL` → `.BIAS` or `.SAFETY`
- Replace `RiskDimension.COMMS` → `.SECURITY`
- Replace `RiskDimension.TECHNICAL` → `.FEASIBILITY` or `.QUALITY`
- Replace `len(RiskDimension)` → `ctx.dimensions()` for score normalization

> **Note:** This is a pre-release. APIs may change before 2.0.0 stable.
