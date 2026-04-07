## What's New in v2.0.0-alpha.2

This release adds three major governance modules aligned with 2025 international best practices for AI governance frameworks, data provenance standards, copyright compliance, and vendor evaluation methodologies. All new modules use open-schema dataclasses with full JSON round-trip support for interoperability.

### Compliance Standards Alignment (`compliance.py`)

The framework now provides explicit alignment with four international standards through a single `ComplianceProfile` that aggregates assessments and produces a scored `ComplianceResult` with identified gaps and actionable recommendations.

- **ISO/IEC 42001:2023** — AI Management System (AIMS) assessment with Plan-Do-Check-Act methodology, five maturity levels, and 25 Annex A control templates covering bias, transparency, accountability, data governance, and supply chain security. `iso42001_annex_a_controls()` provides a ready-to-use checklist.
- **NIST AI RMF 1.0 + AI 600-1** — Four-function mapping (Govern 30%, Map 25%, Measure 25%, Manage 20%) with composite scoring, governance committee tracking, and generative AI supplement coverage including training data poisoning and bias detection controls. `nist_ai_rmf_subcategories()` provides 19 subcategory templates.
- **EU AI Act** — Compliance checklist for GPAI provider obligations effective August 2, 2025. Risk classification tiers (Unacceptable/High/Limited/Minimal), training data summary requirements, copyright opt-out policy (DSM Directive Article 4), conformity assessment for high-risk systems, and automated gap identification.
- **MovieLabs OMC 2030 Vision** — Alignment scoring across eight principles: software-defined workflows, cloud-native architecture, interoperable data models, security-first design, asset provenance tracking, component-based pipelines, open API interfaces, and rights management.

### Data Provenance and Lineage Tracking (`provenance.py`)

Full data lineage tracking aligned with 2025 provenance standards including the MIT Data Provenance Initiative.

- **Source-level metadata** — `DataSource` captures URL, collection date, license type, compliance status, capture method (MoCap, LIDAR, FACS, volumetric, photogrammetry, and 9 more), copyright holder, opt-out compliance, and consent documentation.
- **Generation flags** — Content classified as `HUMAN_ORIGIN`, `MACHINE_ORIGIN`, `HYBRID`, or `UNKNOWN` with confidence scores (0.0-1.0) rather than binary tags.
- **Transformation logs** — Ordered `TransformationRecord` entries (deduplication, cleaning, OCR, translation, augmentation, etc.) with input/output hashes for reproducibility.
- **Bi-temporal lineage** — `DatasetVersion` with `valid_from`/`valid_to` and `recorded_at` timestamps, enabling reconstruction of dataset state at any historical moment for audit.
- **Provenance cards** — `ProvenanceCard` aggregates sources, transformations, versions, and compliance metadata into a human-readable, auditable document.
- **Model collapse prevention** — `ModelCollapseGuard` enforces synthetic data caps, requires vendor disclosure of synthetic data percentages, and applies stricter rules for high-stakes domains.
- **Scoring** — `evaluate_provenance()` produces a 0-100 score across six weighted areas: source metadata (30%), license compliance (20%), generation flags (15%), transformation logs (15%), versioning (10%), and opt-out compliance (10%).

### AI Vendor Scorecard Framework (`vendor_scorecard.py`)

Six-dimension weighted scoring framework for evaluating AI vendors, with KBYUTS criteria and post-Thomson Reuters copyright risk assessment.

- **Six scoring dimensions** — Data & Provenance (25%), Governance & Security (20%), Ethics & Compliance (20%), Technical Fit (15%), Commercial Terms (10%), Operating Model (10%). Weights are customizable per organization.
- **Vendor tier classification** — Preferred (>=80), Approved (>=60), Conditional (>=40), Not Approved (<40) with custom threshold support.
- **KBYUTS scoring** (Know Before You Use Their Stuff) — Five quantitative criteria: Training Data Transparency, Creative Professional Treatment, Governance Maturity, Output Attribution, and Legal Risk, each scored 0-100.
- **Copyright risk assessment** — Post-Thomson Reuters v. ROSS Intelligence (Feb 2025) evaluation covering lawful data acquisition, license verification, opt-out compliance, indemnification, competitive use risk, and pending litigation. Produces risk levels: low/medium/high/critical.
- **Essential vendor questions** — 15 pre-built assessment questions based on the AI Vendor Security and Safety Assessment Guide and ISO 42001 requirements, spanning all six scoring dimensions.
- **Scoring** — `evaluate_vendor()` produces a `VendorResult` with overall score, tier, per-dimension breakdown, identified gaps, recommendations, and copyright risk level.

### Documentation

- **Usage guide** (`docs/governance-provenance-vendor-guide.md`) — 960-line comprehensive guide with 18 Mermaid diagrams covering architecture, data flow, all three modules, end-to-end workflow sequence diagrams, integration patterns, and quick reference tables.

### Examples

- **`examples/governance_review.py`** — Module overview demonstrating each new module independently.
- **`examples/vendor_engagement_review.py`** — End-to-end production scenario: a VFX studio evaluates a GenAI vendor for a feature film across all three modules, integrated with TPN/VFX security profiles and the core governance framework. Produces a go/no-go decision with remediation steps.

### Testing

- **81 new tests** (319 total) covering compliance standards, provenance tracking, model collapse guards, vendor scorecard evaluation, KBYUTS scoring, copyright risk assessment, tier classification, serialization round-trips, and template helpers.

### Design Principles

- **Open schema** — All new structures are plain Python dataclasses with `to_dict()` / `from_dict()` round-trip support for JSON/YAML interoperability. No proprietary dependencies.
- **Modular adoption** — Each module works independently. Use only the standards that apply to your organization.
- **Framework integration** — Evaluation results connect directly to `UseCaseContext` risk flags, `GovernanceHooks` for audit logging, and `GovernanceDashboard` for portfolio tracking.

> **Note:** This is a pre-release. APIs may change before 2.0.0 stable.
