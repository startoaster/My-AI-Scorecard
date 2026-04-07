# Governance, Provenance, and Vendor Scorecard Guide

> Usage documentation for the three governance modules added in alignment
> with 2025 best practices for AI governance frameworks, data provenance
> standards, and vendor scorecard methodologies.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [1. Compliance Standards Module](#1-compliance-standards-module)
- [2. Data Provenance Module](#2-data-provenance-module)
- [3. Vendor Scorecard Module](#3-vendor-scorecard-module)
- [4. End-to-End Workflow](#4-end-to-end-workflow)
- [5. Integration Patterns](#5-integration-patterns)
- [6. Quick Reference](#6-quick-reference)

---

## Architecture Overview

The three new modules extend the core governance framework. Each evaluates
a different aspect of AI risk and feeds results into `UseCaseContext` as
risk flags.

```mermaid
flowchart TB
    subgraph New Modules
        COM[compliance.py<br/>Standards Alignment]
        PRV[provenance.py<br/>Data Lineage]
        VSC[vendor_scorecard.py<br/>Vendor Scoring]
    end

    subgraph Core Framework
        CTX[UseCaseContext]
        RF[RiskFlag]
        DASH[GovernanceDashboard]
        ESC[EscalationPolicy]
    end

    subgraph Enterprise Integration
        SEC[SecurityProfile<br/>TPN / VFX / Enterprise]
        HOOK[GovernanceHooks<br/>Audit / Compliance / Notify]
        SER[Serialization<br/>JSON round-trip]
    end

    COM -->|evaluate_compliance| CR[ComplianceResult]
    PRV -->|evaluate_provenance| PR[ProvenanceResult]
    VSC -->|evaluate_vendor| VR[VendorResult]

    CR -->|gaps become| RF
    PR -->|gaps become| RF
    VR -->|gaps become| RF

    RF --> CTX
    CTX --> DASH
    CTX --> ESC
    CTX --> SER
    SEC --> CTX
    HOOK --> CTX
```

### Data Flow

```mermaid
flowchart LR
    A[Assess Standards] --> B[Evaluate Provenance]
    B --> C[Score Vendor]
    C --> D[Generate Risk Flags]
    D --> E{Blocked?}
    E -->|Yes| F[Route to Reviewers]
    E -->|No| G[Clear to Proceed]
    F --> H[Resolve / Accept]
    H --> E
```

---

## 1. Compliance Standards Module

**Module:** `ai_use_case_context/compliance.py`

Evaluates alignment with four international standards through a single
`ComplianceProfile` that aggregates all assessments.

```mermaid
flowchart TB
    subgraph Standards
        ISO[ISO/IEC 42001:2023<br/>AI Management System]
        NIST[NIST AI RMF 1.0<br/>+ AI 600-1 GenAI]
        EU[EU AI Act<br/>Effective Aug 2025]
        OMC[MovieLabs OMC<br/>2030 Vision]
    end

    ISO --> CP[ComplianceProfile]
    NIST --> CP
    EU --> CP
    OMC --> CP

    CP -->|evaluate_compliance| CR[ComplianceResult]

    CR --> SC[section_scores]
    CR --> GA[gaps]
    CR --> RE[recommendations]
    CR --> OV[overall_score 0-100]
```

### 1.1 ISO/IEC 42001:2023 -- AI Management System

The international benchmark for AI management. Uses a Plan-Do-Check-Act
methodology with 38 Annex A controls.

```mermaid
flowchart LR
    subgraph PDCA Cycle
        P[PLAN<br/>Establish AIMS<br/>Risk assessment<br/>Impact assessment]
        D[DO<br/>Implement controls<br/>Deploy safeguards<br/>Train staff]
        C[CHECK<br/>Monitor metrics<br/>Audit controls<br/>Review incidents]
        A[ACT<br/>Improve processes<br/>Update policies<br/>Recertify]
    end

    P --> D --> C --> A --> P
```

**Annex A Control Categories:**

| Category | Controls | Scope |
|----------|----------|-------|
| A.2 | AI Policy | Organizational policies and responsibilities |
| A.3 | Risk Management | Risk assessment and treatment |
| A.4 | System Lifecycle | Impact assessment, testing, deployment, monitoring |
| A.5 | Ethics | Bias/fairness, transparency, accountability, privacy |
| A.6 | Data Governance | Provenance, quality management |
| A.7 | Supply Chain | Third-party components, AI supply chain security |
| A.8 | Security | System security, model protection |
| A.9 | Communication | Stakeholder communication, documentation |
| A.10 | Improvement | Continual improvement of AI systems |

**Code example:**

```python
from ai_use_case_context.compliance import (
    ISO42001Assessment, AIMSMaturity,
    iso42001_annex_a_controls,
)
from datetime import date

# Load blank Annex A controls and mark some as implemented
controls = iso42001_annex_a_controls()
for ctrl in controls[:18]:
    ctrl.implemented = True
    ctrl.evidence = "Verified via audit package"

assessment = ISO42001Assessment(
    aims_documented=True,
    risk_assessment_process=True,
    ai_impact_assessment=True,
    continuous_improvement_cycle=True,
    maturity=AIMSMaturity.DEFINED,
    certification_body="BSI Group",
    certification_date=date(2025, 11, 15),
    annex_a_controls=controls,
)

print(f"Score: {assessment.score:.1f}/100")
print(f"Controls: {assessment.controls_implemented}/{assessment.controls_total}")
```

### 1.2 NIST AI Risk Management Framework

Organized around four core functions. NIST AI 600-1 (2025) adds 200+
actions specific to generative AI risks.

```mermaid
flowchart TB
    subgraph GOVERN -- 30% weight
        GV1[Policies established]
        GV2[Roles defined]
        GV3[Cross-functional committee]
        GV4[Risk tolerance set]
    end

    subgraph MAP -- 25% weight
        MP1[Context documented]
        MP2[Risks categorized]
        MP3[Third-party risks mapped]
        MP4[Community impacts mapped]
    end

    subgraph MEASURE -- 25% weight
        MS1[Performance metrics]
        MS2[Fairness/bias metrics]
        MS3[Reliability testing]
        MS4[Security testing]
    end

    subgraph MANAGE -- 20% weight
        MG1[Response strategies]
        MG2[Incident tracking]
        MG3[Drift monitoring]
        MG4[Decommissioning procedures]
    end

    GV1 & GV2 & GV3 & GV4 --> CS[composite_score]
    MP1 & MP2 & MP3 & MP4 --> CS
    MS1 & MS2 & MS3 & MS4 --> CS
    MG1 & MG2 & MG3 & MG4 --> CS
```

**Code example:**

```python
from ai_use_case_context.compliance import NISTAIRMFMapping

nist = NISTAIRMFMapping(
    govern_score=85,
    map_score=70,
    measure_score=60,
    manage_score=55,
    governance_committee_established=True,
    committee_roles=["VP Legal", "CTO", "Ethics Officer"],
    gen_ai_supplement_addressed=True,
    incident_response_procedures=True,
)

print(f"Composite: {nist.composite_score:.1f}/100")
# -> 85*0.30 + 70*0.25 + 60*0.25 + 55*0.20 = 69.0
```

### 1.3 EU AI Act

Risk-tiered regulation for AI systems with European distribution.

```mermaid
flowchart TB
    UA[Unacceptable Risk<br/>BANNED<br/>Social scoring, manipulative AI]
    HR[High Risk<br/>STRICT OBLIGATIONS<br/>Safety, fundamental rights]
    LR[Limited Risk<br/>TRANSPARENCY REQUIRED<br/>Chatbots, deepfakes, GenAI]
    MR[Minimal Risk<br/>NO OBLIGATIONS<br/>Spam filters, games]

    UA ~~~ HR ~~~ LR ~~~ MR

    HR --> C1[Conformity assessment]
    HR --> C2[Fundamental rights impact]
    HR --> C3[Human oversight mechanisms]

    LR --> T1[Training data summary]
    LR --> T2[Copyright opt-out policy]
    LR --> T3[Transparency obligations]

    style UA fill:#ff4444,color:#fff
    style HR fill:#ff8800,color:#fff
    style LR fill:#ffcc00,color:#000
    style MR fill:#44cc44,color:#fff
```

**Penalty:** Up to 15M EUR or 3% of global annual revenue.

**Code example:**

```python
from ai_use_case_context.compliance import (
    EUAIActChecklist, RiskClassification,
)

eu = EUAIActChecklist(
    risk_classification=RiskClassification.LIMITED,
    eu_distribution_planned=True,
    training_data_summary_published=True,
    copyright_opt_out_policy=True,
    transparency_obligations=True,
)

print(f"Applicable: {eu.applicable}")   # True
print(f"Compliant: {eu.compliant}")     # True
print(f"Gaps: {eu.gaps}")               # []
```

### 1.4 MovieLabs OMC 2030 Vision

Cloud-native, software-defined production workflows.

```mermaid
flowchart LR
    subgraph OMC Principles
        SW[Software-Defined<br/>Workflow]
        CN[Cloud-Native<br/>Architecture]
        ID[Interoperable<br/>Data Model]
        SF[Security-First<br/>Design]
        AP[Asset Provenance<br/>Tracking]
        CB[Component-Based<br/>Pipeline]
        OA[Open API<br/>Interfaces]
        RM[Rights<br/>Management]
    end

    SW & CN & ID & SF & AP & CB & OA & RM --> S[score 0-100]
```

### 1.5 Composite Evaluation

```python
from ai_use_case_context.compliance import (
    ComplianceProfile, evaluate_compliance,
)

profile = ComplianceProfile(
    iso42001=iso_assessment,
    nist_ai_rmf=nist_mapping,
    eu_ai_act=eu_checklist,
    movielabs_omc=omc_alignment,
    assessor="AI Governance Board",
)

result = evaluate_compliance(profile)
print(f"Overall: {result.overall_score:.1f}/100")
for section, score in result.section_scores.items():
    print(f"  {section}: {score:.1f}")
for gap in result.gaps:
    print(f"  GAP: {gap}")
```

---

## 2. Data Provenance Module

**Module:** `ai_use_case_context/provenance.py`

Tracks data lineage from source through transformation to versioned
dataset, with model collapse prevention guards.

### 2.1 Lineage Data Model

```mermaid
flowchart TB
    subgraph Source Layer
        DS1[DataSource<br/>name, URL, license<br/>capture method<br/>copyright holder]
        DS2[DataSource]
        DS3[DataSource]
    end

    subgraph Transformation Layer
        TR1[TransformationRecord<br/>type: dedup/clean/OCR<br/>input_hash, output_hash<br/>applied_by, parameters]
        TR2[TransformationRecord]
    end

    subgraph Version Layer
        DV[DatasetVersion<br/>version_id, checksum<br/>valid_from / valid_to<br/>recorded_at<br/>parent_version_id]
    end

    subgraph Provenance Card
        PC[ProvenanceCard<br/>generation_flag + confidence<br/>synthetic_percentage<br/>license_summary<br/>lawful_basis]
    end

    DS1 & DS2 & DS3 --> PC
    TR1 & TR2 --> PC
    DV --> PC
    PC -->|evaluate_provenance| PR[ProvenanceResult<br/>score, gaps, recommendations]
```

### 2.2 Generation Flag Classification

Content origin is classified with a confidence score rather than a
binary tag, acknowledging real-world ambiguity.

```mermaid
flowchart LR
    H[HUMAN_ORIGIN<br/>Manually created<br/>by human artists]
    HY[HYBRID<br/>Human + machine<br/>collaboration]
    M[MACHINE_ORIGIN<br/>Fully AI<br/>generated]
    U[UNKNOWN<br/>Origin not<br/>determined]

    H -->|augmented by AI| HY
    HY -->|fully automated| M
    M -->|provenance lost| U

    style H fill:#44cc44,color:#fff
    style HY fill:#ffcc00,color:#000
    style M fill:#ff8800,color:#fff
    style U fill:#ff4444,color:#fff
```

Each flag includes a `generation_confidence` score (0.0-1.0). Provenance
is considered incomplete if the flag is `UNKNOWN` with confidence below 0.8.

### 2.3 Capture Methods

| Method | Enum | Description |
|--------|------|-------------|
| Motion capture | `MOTION_CAPTURE` | MoCap suit/stage recordings |
| LIDAR | `LIDAR` | Laser scanning point clouds |
| Volumetric | `VOLUMETRIC` | Multi-camera volumetric capture |
| FACS | `FACS` | Facial Action Coding System |
| Photogrammetry | `PHOTOGRAMMETRY` | Photo-based 3D reconstruction |
| Web crawl | `CRAWL` | Scraped from web sources |
| Partner feed | `PARTNER_FEED` | Licensed partner data feed |
| Sensor | `SENSOR` | IoT / physical sensor data |
| Manual creation | `MANUAL_CREATION` | Hand-crafted by artists |
| Licensed dataset | `LICENSED_DATASET` | Purchased / licensed datasets |
| API | `API` | Retrieved via API |
| Synthetic | `SYNTHETIC` | AI-generated synthetic data |
| User submission | `USER_SUBMISSION` | User-uploaded content |

### 2.4 Bi-Temporal Lineage

Bi-temporal lineage allows reconstructing the dataset state at any
historical moment for audit purposes.

```mermaid
gantt
    title Bi-Temporal Dataset Versioning
    dateFormat YYYY-MM
    axisFormat %Y-%m

    section Valid Time
    v1.0 active     :v1, 2024-01, 2024-06
    v2.0 active     :v2, 2024-06, 2025-01
    v2.1 current    :v3, 2025-01, 2025-12

    section Recorded Time
    v1.0 recorded   :r1, 2024-01, 2024-02
    v2.0 recorded   :r2, 2024-05, 2024-06
    v2.1 recorded   :r3, 2024-12, 2025-01
```

- **valid_from / valid_to**: when this version was the active dataset version
- **recorded_at**: when the version record was created in the system
- **parent_version_id**: links to the predecessor for full lineage chain

### 2.5 Model Collapse Prevention

Model collapse occurs when AI trains on outputs from other AI models,
causing quality degradation over generations.

```mermaid
flowchart TB
    subgraph ModelCollapseGuard
        CAP[max_synthetic_percentage]
        ACT[actual_synthetic_percentage]
        DIS[vendor_disclosure_received]
        HS[high_stakes_domain]
    end

    ACT -->|exceeds?| CAP
    CAP --> CHK{Within Limits?}
    CHK -->|Yes| PASS[PASS]
    CHK -->|No| FAIL[FAIL:<br/>Synthetic content<br/>exceeds cap]

    DIS -->|missing?| V1[VIOLATION:<br/>No vendor disclosure]
    HS -->|true + no disclosure| V2[VIOLATION:<br/>High-stakes domain<br/>requires disclosure]

    style PASS fill:#44cc44,color:#fff
    style FAIL fill:#ff4444,color:#fff
    style V1 fill:#ff8800,color:#fff
    style V2 fill:#ff8800,color:#fff
```

### 2.6 Provenance Scoring Breakdown

`evaluate_provenance()` scores on a 0-100 scale across six areas:

| Area | Weight | What is measured |
|------|--------|-----------------|
| Source metadata | 30 pts | Name, license, capture method, collection date, compliance status |
| License compliance | 20 pts | Percentage of sources with `VERIFIED` license compliance |
| Generation flags | 15 pts | Origin classified (10 pts) + confidence >= 0.8 (5 pts) |
| Transformation logs | 15 pts | At least one transformation recorded |
| Dataset versioning | 10 pts | At least one version with bi-temporal fields |
| Opt-out compliance | 10 pts | All copyright holders' opt-out requests honored |

### 2.7 Code Example

```python
from ai_use_case_context.provenance import (
    DataSource, CaptureMethod, LicenseCompliance,
    GenerationFlag, TransformationRecord, TransformationType,
    DatasetVersion, ProvenanceCard, ModelCollapseGuard,
    evaluate_provenance,
)
from datetime import datetime

# Define sources
source = DataSource(
    name="Licensed MoCap Library",
    license_type="Commercial Perpetual",
    license_compliance=LicenseCompliance.VERIFIED,
    capture_method=CaptureMethod.MOTION_CAPTURE,
    collection_date=datetime(2024, 6, 15),
    copyright_holder="Studio X",
    opt_out_honored=True,
)

# Build provenance card
card = ProvenanceCard(
    dataset_name="Hero Character MoCap v2",
    sources=[source],
    generation_flag=GenerationFlag.HUMAN_ORIGIN,
    generation_confidence=0.98,
    transformations=[
        TransformationRecord(
            TransformationType.CLEANING, "Removed noise",
            input_hash="sha256:abc", output_hash="sha256:def",
        ),
    ],
    versions=[
        DatasetVersion("v2.0", "Hero MoCap", record_count=15000),
    ],
    synthetic_percentage=0.0,
)

# Evaluate with model collapse guard
guard = ModelCollapseGuard(
    max_synthetic_percentage=20.0,
    actual_synthetic_percentage=0.0,
    vendor_disclosure_received=True,
)

result = evaluate_provenance(card, guard)
print(f"Score: {result.score:.1f}/100")
print(f"Licenses OK: {card.all_licenses_verified}")
print(f"Collapse guard: {'PASS' if guard.within_limits else 'FAIL'}")
```

---

## 3. Vendor Scorecard Module

**Module:** `ai_use_case_context/vendor_scorecard.py`

Six-dimension weighted scoring framework for AI vendor evaluation, with
KBYUTS criteria and post-Thomson Reuters copyright risk assessment.

### 3.1 Evaluation Pipeline

```mermaid
flowchart LR
    subgraph Input
        DS[DimensionScores<br/>6 dimensions]
        KB[KBYUTSScores<br/>5 criteria]
        CR[CopyrightAssessment<br/>8 risk factors]
        VQ[VendorQuestions<br/>15 essential questions]
    end

    DS & KB & CR & VQ --> SC[VendorScorecard]
    SC -->|evaluate_vendor| VR[VendorResult]

    VR --> OV[overall_score]
    VR --> TI[tier]
    VR --> GP[gaps]
    VR --> RC[recommendations]
    VR --> CK[copyright_risk]
```

### 3.2 Six Scoring Dimensions

```mermaid
pie title Vendor Scorecard Dimension Weights
    "Data & Provenance" : 25
    "Governance & Security" : 20
    "Ethics & Compliance" : 20
    "Technical Fit" : 15
    "Commercial Terms" : 10
    "Operating Model" : 10
```

| Dimension | Weight | Key Evaluation Criteria |
|-----------|--------|------------------------|
| **Data & Provenance** | 25% | Training data transparency, lineage documentation, license compliance, consent mechanisms |
| **Governance & Security** | 20% | ISO 42001 certification, SOC 2 Type II, data isolation, incident response SLAs |
| **Ethics & Compliance** | 20% | Bias mitigation processes, ethics board, NIST AI RMF alignment, labor/talent protections |
| **Technical Fit** | 15% | Integration capabilities, API maturity, production readiness, version control |
| **Commercial Terms** | 10% | IP ownership clarity, termination rights, data portability, output ownership |
| **Operating Model** | 10% | Support model, implementation timeline, training provided, continuous monitoring |

### 3.3 Vendor Tier Classification

```mermaid
flowchart TB
    SC[Overall Score] --> P{>= 80?}
    P -->|Yes| PREF[PREFERRED<br/>Full engagement approved]
    P -->|No| A{>= 60?}
    A -->|Yes| APPR[APPROVED<br/>Standard engagement]
    A -->|No| C{>= 40?}
    C -->|Yes| COND[CONDITIONAL<br/>Requires remediation plan]
    C -->|No| NA[NOT APPROVED<br/>Do not engage]

    style PREF fill:#44cc44,color:#fff
    style APPR fill:#88cc44,color:#fff
    style COND fill:#ffcc00,color:#000
    style NA fill:#ff4444,color:#fff
```

### 3.4 KBYUTS Scoring (Know Before You Use Their Stuff)

Five quantitative criteria, each scored 0-100:

```mermaid
flowchart TB
    subgraph KBYUTS Criteria
        TDT[Training Data<br/>Transparency<br/>25% weight]
        CPT[Creative Professional<br/>Treatment<br/>20% weight]
        GVM[Governance<br/>Maturity<br/>20% weight]
        OAT[Output<br/>Attribution<br/>20% weight]
        LGR[Legal<br/>Risk<br/>15% weight]
    end

    TDT & CPT & GVM & OAT & LGR --> CS[composite_score 0-100]
```

| Criterion | What it measures |
|-----------|-----------------|
| Training Data Transparency | Dataset cards, provenance docs, license clarity |
| Creative Professional Treatment | Opt-out mechanisms, consent processes, compensation |
| Governance Maturity | Certifications (ISO 42001, SOC 2), documented policies |
| Output Attribution | Ability to trace outputs to training data, audit trails |
| Legal Risk | Pending litigation, regulatory compliance, contractual protections |

### 3.5 Copyright Risk Assessment

Post-Thomson Reuters v. ROSS Intelligence (Feb 2025) decision tree:

```mermaid
flowchart TB
    START[Assess Copyright Risk] --> LIT{Pending<br/>litigation?}
    LIT -->|Yes| CRIT1[CRITICAL]
    LIT -->|No| COMP{Competes with<br/>training sources<br/>AND unlawful data?}
    COMP -->|Yes| CRIT2[CRITICAL]
    COMP -->|No| UNL{Training data<br/>not lawfully obtained<br/>AND no license docs?}
    UNL -->|Yes| HIGH[HIGH]
    UNL -->|No| OPT{Opt-out process<br/>AND indemnification?}
    OPT -->|Both missing| MED[MEDIUM]
    OPT -->|At least one| LOW[LOW]

    style CRIT1 fill:#ff4444,color:#fff
    style CRIT2 fill:#ff4444,color:#fff
    style HIGH fill:#ff8800,color:#fff
    style MED fill:#ffcc00,color:#000
    style LOW fill:#44cc44,color:#fff
```

**Key factors assessed:**

- `training_data_lawfully_obtained` -- data obtained with appropriate licenses
- `license_verification_documented` -- evidence of license verification
- `opt_out_compliance_process` -- honors rights holder opt-outs (EU DSM Directive Art. 4)
- `indemnification_for_ai_outputs` -- vendor indemnifies for copyright claims
- `competes_with_training_sources` -- Thomson Reuters competitive use risk
- `pending_litigation` -- vendor has active copyright lawsuits
- `eu_dsm_article4_compliance` -- EU Digital Single Market compliance
- `eu_training_data_summary_published` -- EU AI Act GPAI summary published

### 3.6 Essential Vendor Questions

The framework includes 15 pre-built questions based on the AI Vendor
Security and Safety Assessment Guide. Loaded via `essential_vendor_questions()`:

| ID | Dimension | Question |
|----|-----------|----------|
| VQ-001 | Governance & Security | Encryption standards for data at rest and in transit? |
| VQ-002 | Governance & Security | ISO 42001 or NIST AI RMF adoption and certification? |
| VQ-003 | Governance & Security | Model testing and validation documentation? |
| VQ-004 | Ethics & Compliance | Frameworks for addressing AI bias? |
| VQ-005 | Data & Provenance | Field-level data lineage capabilities? |
| VQ-006 | Data & Provenance | Policy on using client data for model training? |
| VQ-007 | Technical Fit | Model drift monitoring and retraining policy? |
| VQ-008 | Data & Provenance | Synthetic data percentage and provenance tracking? |
| VQ-009 | Commercial Terms | Indemnification for copyright claims from AI outputs? |
| VQ-010 | Data & Provenance | Lawful acquisition of training data with licenses? |
| VQ-011 | Ethics & Compliance | Processes for honoring rights holder opt-outs? |
| VQ-012 | Commercial Terms | Does the AI compete with training data sources? |
| VQ-013 | Operating Model | Incident response SLA for AI system failures? |
| VQ-014 | Commercial Terms | Data portability upon contract termination? |
| VQ-015 | Ethics & Compliance | Training data summary per EU AI Act for GPAI? |

### 3.7 Code Example

```python
from ai_use_case_context.vendor_scorecard import (
    VendorScorecard, DimensionScore,
    KBYUTSScores, CopyrightAssessment,
    evaluate_vendor, essential_vendor_questions,
)

scorecard = VendorScorecard(
    vendor_name="NeuralForge Studio AI",
    data_provenance=DimensionScore(score=75, evidence="Dataset cards available"),
    governance_security=DimensionScore(score=82, evidence="ISO 42001 certified"),
    ethics_compliance=DimensionScore(score=68, gaps="Opt-out process immature"),
    technical_fit=DimensionScore(score=88),
    commercial_terms=DimensionScore(score=65, gaps="Indemnification capped"),
    operating_model=DimensionScore(score=78),
    kbyuts=KBYUTSScores(
        training_data_transparency=70,
        creative_professional_treatment=55,
        governance_maturity=80,
        output_attribution=45,
        legal_risk=60,
    ),
    copyright=CopyrightAssessment(
        training_data_lawfully_obtained=True,
        license_verification_documented=True,
        opt_out_compliance_process=True,
        indemnification_for_ai_outputs=True,
    ),
)

result = evaluate_vendor(scorecard)
print(f"Score: {result.overall_score:.1f}/100")
print(f"Tier: {result.tier.value}")          # -> approved
print(f"Copyright: {result.copyright_risk}") # -> low
```

---

## 4. End-to-End Workflow

A complete vendor engagement review follows seven steps. See
`examples/vendor_engagement_review.py` for a runnable implementation.

```mermaid
sequenceDiagram
    participant GOV as Governance Board
    participant COM as compliance.py
    participant PRV as provenance.py
    participant VSC as vendor_scorecard.py
    participant CTX as UseCaseContext
    participant REV as Reviewers

    GOV->>CTX: 1. Create use case + apply security profiles
    GOV->>COM: 2. Assess ISO 42001, NIST, EU AI Act, OMC
    COM-->>GOV: ComplianceResult (score, gaps)
    GOV->>PRV: 3. Build provenance card + collapse guard
    PRV-->>GOV: ProvenanceResult (score, gaps)
    GOV->>VSC: 4. Score vendor across 6 dimensions
    VSC-->>GOV: VendorResult (tier, copyright risk)
    GOV->>CTX: 5. Convert gaps to risk flags
    CTX-->>GOV: is_blocked() / get_blockers()
    GOV->>GOV: 6. Governance decision (go / no-go)
    GOV->>REV: 7. Route blockers to reviewers
    REV-->>CTX: Resolve / Accept flags
```

### Decision Tree

```mermaid
flowchart TB
    START[Start Review] --> S1[Compliance >= 70?]
    S1 -->|No| FLAG1[Flag: LEGAL_IP HIGH]
    S1 -->|Yes| S2

    S2[All licenses verified?]
    S2 -->|No| FLAG2[Flag: LEGAL_IP HIGH]
    S2 -->|Yes| S3

    S3[Opt-outs honored?]
    S3 -->|No| FLAG3[Flag: LEGAL_IP MEDIUM]
    S3 -->|Yes| S4

    S4[Synthetic within cap?]
    S4 -->|No| FLAG4[Flag: SECURITY HIGH]
    S4 -->|Yes| S5

    S5[Vendor tier?]
    S5 -->|NOT_APPROVED| FLAG5[Flag: LEGAL_IP CRITICAL]
    S5 -->|CONDITIONAL+| S6

    S6[Copyright risk?]
    S6 -->|high/critical| FLAG6[Flag: LEGAL_IP CRITICAL]
    S6 -->|low/medium| S7[Check for blockers]

    FLAG1 & FLAG2 & FLAG3 & FLAG4 & FLAG5 & FLAG6 --> S7

    S7 --> BLK{Any blocking flags?}
    BLK -->|Yes| BLOCK[BLOCKED<br/>Route to reviewers<br/>Set remediation timeline]
    BLK -->|No| CLEAR[APPROVED<br/>Proceed with monitoring]

    style BLOCK fill:#ff4444,color:#fff
    style CLEAR fill:#44cc44,color:#fff
```

---

## 5. Integration Patterns

### 5.1 Connecting Results to Risk Flags

```python
from ai_use_case_context import UseCaseContext, RiskDimension, RiskLevel

ctx = UseCaseContext(name="AI Character Tool", workflow_phase="Asset Creation")

# From compliance evaluation
if compliance_result.overall_score < 70:
    ctx.flag_risk(
        RiskDimension.LEGAL_IP, RiskLevel.HIGH,
        f"Compliance score {compliance_result.overall_score:.0f}/100 below threshold",
    )

# From provenance evaluation
if not card.all_licenses_verified:
    ctx.flag_risk(
        RiskDimension.LEGAL_IP, RiskLevel.HIGH,
        "Training data includes sources with unverified licenses",
    )

# From vendor scorecard
if vendor_result.copyright_risk in ("high", "critical"):
    ctx.flag_risk(
        RiskDimension.LEGAL_IP, RiskLevel.CRITICAL,
        f"Vendor copyright risk: {vendor_result.copyright_risk}",
    )

# Check decision
if ctx.is_blocked():
    print(f"BLOCKED: {len(ctx.get_blockers())} issues")
    print(f"Reviewers needed: {ctx.get_reviewers_needed()}")
```

### 5.2 Audit Logging with GovernanceHooks

```python
from ai_use_case_context import (
    register_hook, AuditLogger, emit_governance_event,
    GovernanceEvent, GovernanceEventType,
)

logger = AuditLogger()
register_hook(logger)

# Emit custom events for governance review milestones
emit_governance_event(GovernanceEvent(
    event_type=GovernanceEventType.COMPLIANCE_CHECK,
    use_case_name="AI Character Tool",
    description=f"Compliance evaluation: {compliance_result.overall_score:.0f}/100",
    metadata=compliance_result.to_dict(),
))

# Query the audit log
entries = logger.query(event_type=GovernanceEventType.COMPLIANCE_CHECK)
```

### 5.3 Combining with Security Profiles

```python
from ai_use_case_context.security import security_profile, apply_security_profile

# Apply TPN + VFX security to the use case
profile = security_profile("tpn", "vfx")
apply_security_profile(ctx, profile)

# Now vendor security flags route to the correct reviewers
ctx.flag_risk(
    VFX_VENDOR_SECURITY, RiskLevel.HIGH,
    "Vendor data isolation controls unverified",
)
# -> Routed to: VP Procurement + CISO
```

### 5.4 JSON Serialization

All new dataclasses support `to_dict()` / `from_dict()` round-trip:

```python
import json

# Serialize review artifacts
artifacts = {
    "compliance": compliance_result.to_dict(),
    "provenance": provenance_result.to_dict(),
    "vendor": vendor_result.to_dict(),
    "provenance_card": card.to_dict(),
    "scorecard": scorecard.to_dict(),
}

# Write to file
with open("review_artifacts.json", "w") as f:
    json.dump(artifacts, f, indent=2)

# Reconstruct from JSON
from ai_use_case_context.compliance import ComplianceResult
from ai_use_case_context.vendor_scorecard import VendorResult

restored_compliance = ComplianceResult.from_dict(artifacts["compliance"])
restored_vendor = VendorResult.from_dict(artifacts["vendor"])
```

### 5.5 Portfolio Dashboard

```python
from ai_use_case_context import GovernanceDashboard

dashboard = GovernanceDashboard()
dashboard.register(ctx)

# Portfolio-level views
for name, scores in dashboard.portfolio_risk_scores().items():
    print(f"{name}: {scores}")

# Reviewer workload
for reviewer, flags in dashboard.reviewer_workload().items():
    print(f"{reviewer}: {len(flags)} flags")
```

---

## 6. Quick Reference

### Classes

| Class | Module | Purpose |
|-------|--------|---------|
| `ISO42001Assessment` | compliance | ISO 42001 AIMS assessment with Annex A controls |
| `ISO42001Control` | compliance | Single Annex A control checklist item |
| `NISTAIRMFMapping` | compliance | NIST AI RMF four-function alignment |
| `NISTSubcategory` | compliance | Single NIST subcategory assessment |
| `EUAIActChecklist` | compliance | EU AI Act compliance checklist |
| `MovieLabsOMCAlignment` | compliance | MovieLabs OMC 2030 alignment |
| `ComplianceProfile` | compliance | Composite profile aggregating all standards |
| `ComplianceResult` | compliance | Scored evaluation output |
| `DataSource` | provenance | Source-level metadata (URL, license, capture method) |
| `TransformationRecord` | provenance | Single data transformation log entry |
| `DatasetVersion` | provenance | Bi-temporal versioned dataset snapshot |
| `ProvenanceCard` | provenance | Human-readable provenance summary |
| `ModelCollapseGuard` | provenance | Synthetic data cap enforcement |
| `ProvenanceResult` | provenance | Scored provenance evaluation output |
| `VendorScorecard` | vendor_scorecard | Complete vendor evaluation document |
| `DimensionScore` | vendor_scorecard | Single dimension score (0-100) |
| `KBYUTSScores` | vendor_scorecard | Five KBYUTS quantitative criteria |
| `CopyrightAssessment` | vendor_scorecard | Copyright risk evaluation |
| `VendorQuestion` | vendor_scorecard | Single vendor assessment question |
| `VendorResult` | vendor_scorecard | Scored vendor evaluation output |

### Evaluation Functions

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `evaluate_compliance()` | `ComplianceProfile` | `ComplianceResult` | Scores all standards, identifies gaps |
| `evaluate_provenance()` | `ProvenanceCard`, `ModelCollapseGuard?` | `ProvenanceResult` | Scores lineage completeness |
| `evaluate_vendor()` | `VendorScorecard`, weights?, thresholds? | `VendorResult` | Weighted scoring with tier assignment |

### Template Helpers

| Function | Returns | Description |
|----------|---------|-------------|
| `iso42001_annex_a_controls()` | `list[ISO42001Control]` | 25 blank Annex A control templates |
| `nist_ai_rmf_subcategories()` | `list[NISTSubcategory]` | 19 NIST subcategory templates (GV/MP/MS/MG) |
| `essential_vendor_questions()` | `list[VendorQuestion]` | 15 essential vendor assessment questions |

### Enums

| Enum | Values |
|------|--------|
| `RiskClassification` | `UNACCEPTABLE`, `HIGH`, `LIMITED`, `MINIMAL` |
| `AIMSMaturity` | `INITIAL`, `MANAGED`, `DEFINED`, `QUANTITATIVELY_MANAGED`, `OPTIMIZING` |
| `NISTFunction` | `GOVERN`, `MAP`, `MEASURE`, `MANAGE` |
| `OMCWorkflowPhase` | `CONCEPT`, `PRE_PRODUCTION`, `PRODUCTION`, `POST_PRODUCTION`, `DISTRIBUTION`, `ARCHIVE` |
| `GenerationFlag` | `HUMAN_ORIGIN`, `MACHINE_ORIGIN`, `HYBRID`, `UNKNOWN` |
| `CaptureMethod` | `CRAWL`, `PARTNER_FEED`, `MOTION_CAPTURE`, `LIDAR`, `FACS`, `PHOTOGRAMMETRY`, ... |
| `TransformationType` | `DEDUPLICATION`, `CLEANING`, `OCR`, `TRANSLATION`, `AUGMENTATION`, ... |
| `LicenseCompliance` | `VERIFIED`, `PENDING_REVIEW`, `NON_COMPLIANT`, `UNKNOWN`, `NOT_APPLICABLE` |
| `ScorecardDimension` | `DATA_PROVENANCE`, `GOVERNANCE_SECURITY`, `ETHICS_COMPLIANCE`, `TECHNICAL_FIT`, `COMMERCIAL_TERMS`, `OPERATING_MODEL` |
| `VendorTier` | `PREFERRED` (>=80), `APPROVED` (>=60), `CONDITIONAL` (>=40), `NOT_APPROVED` (<40) |
