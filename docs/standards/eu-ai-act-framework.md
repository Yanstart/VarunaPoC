# EU AI Act Compliance Framework for VarunaPoC

**Document Version:** 1.0
**Date:** 2026-02-18
**Classification:** Regulatory Planning (Documentation Only)
**Applicable Regulation:** Regulation (EU) 2024/1689 (EU AI Act)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [EU AI Act Overview](#2-eu-ai-act-overview)
3. [VarunaPoC Risk Classification](#3-varunapoc-risk-classification)
4. [Technical Documentation Requirements (Article 11)](#4-technical-documentation-requirements-article-11)
5. [Conformity Assessment Path (Article 43)](#5-conformity-assessment-path-article-43)
6. [Post-Market Monitoring Obligations](#6-post-market-monitoring-obligations)
7. [Enforcement Timeline](#7-enforcement-timeline)
8. [Gap Analysis: VarunaPoC Current State](#8-gap-analysis-varunapoc-current-state)
9. [Recommendations and Action Plan](#9-recommendations-and-action-plan)
10. [References](#10-references)

---

## 1. Executive Summary

The EU AI Act (Regulation 2024/1689) establishes a comprehensive legal framework for artificial
intelligence systems within the European Union. As VarunaPoC incorporates ML-based inference
capabilities (detection, classification, cell counting) for histopathology analysis, and is
developed in collaboration with CHU UCL Namur (Belgium), the system falls squarely within the
scope of this regulation.

**Key finding:** VarunaPoC's AI components are classified as **HIGH-RISK** under the AI Act
because they constitute AI systems intended for use as safety components of medical devices
falling under IVDR (EU 2017/746). This classification triggers significant technical
documentation, conformity assessment, and post-market monitoring obligations.

**Current mitigation:** VarunaPoC currently operates in **mock inference mode** for research
and teaching purposes. The AI Act obligations become binding only when the system is placed
on the market or put into service with real AI inference capabilities. This provides a window
to build compliance into the development process proactively.

---

## 2. EU AI Act Overview

### 2.1 Scope and Purpose

The AI Act applies to providers, deployers, importers, and distributors of AI systems within
the EU. It classifies AI systems into risk categories and imposes requirements proportional
to risk level.

### 2.2 Risk Classification Tiers

| Risk Level | Description | Examples | Obligations |
|------------|-------------|----------|-------------|
| **Unacceptable** | AI practices that are prohibited | Social scoring, real-time biometric identification (with exceptions) | Banned (Article 5) |
| **High-Risk** | AI in safety-critical or rights-impacting domains | Medical device AI, critical infrastructure AI | Full compliance regime (Articles 6-51) |
| **Limited Risk** | AI requiring transparency | Chatbots, deepfakes, emotion recognition | Transparency obligations (Article 50) |
| **Minimal Risk** | All other AI systems | Spam filters, video game AI | Voluntary codes of practice |

### 2.3 Definition of AI System (Article 3(1))

The AI Act defines an AI system as "a machine-based system that is designed to operate with
varying levels of autonomy and that may exhibit adaptiveness after deployment and that, for
explicit or implicit objectives, infers, from the input it receives, how to generate outputs
such as predictions, content, recommendations, or decisions that can influence physical or
virtual environments."

VarunaPoC's ML pipeline (Slideflow + Phikon-v2 foundation model for heatmap generation,
detection, and classification) meets this definition.

---

## 3. VarunaPoC Risk Classification

### 3.1 Classification Analysis

**Article 6(1):** An AI system is high-risk if it is:
- (a) intended to be used as a safety component of a product covered by EU harmonisation
  legislation listed in Annex I, OR
- (b) the AI system is itself such a product

AND the product is required to undergo third-party conformity assessment.

**Annex I, Section A, Row 10:** Lists Regulation (EU) 2017/746 (IVDR) as covered legislation.

**Annex III, Point 1(a):** AI systems intended for use as safety components in the management
and operation of medical devices.

### 3.2 Classification Decision Tree for VarunaPoC

```
Is VarunaPoC an AI system? (Article 3(1))
  YES - ML inference for detection, classification, cell counting
  |
  v
Is it intended for use with a product listed in Annex I?
  YES - Medical device software under IVDR (EU 2017/746)
  |
  v
Does the product require third-party conformity assessment?
  +-- If IVDR Class A (research/teaching): NO third-party assessment required
  |     => NOT high-risk under Article 6(1) currently
  |
  +-- If IVDR Class C (diagnostic use): YES
        => HIGH-RISK AI system
```

### 3.3 Classification Summary

| VarunaPoC Use Phase | IVDR Class | AI Act Classification | Rationale |
|---------------------|------------|----------------------|-----------|
| Research/teaching (current) | Class A | **Not high-risk** (Article 6(1) exemption) | No third-party conformity assessment required for IVDR Class A |
| Consultative decision support | Likely exempt from IVDR | **Potentially high-risk** (Annex III assessment needed) | Must evaluate under Article 6(2) and Annex III |
| Primary diagnostic tool (future) | Class C | **HIGH-RISK** | Third-party conformity assessment required under IVDR |

**Important note:** Even though VarunaPoC is currently not classified as high-risk, the
AI Act encourages voluntary adoption of the requirements (Article 95). Building compliance
proactively is strongly recommended given the project's trajectory toward clinical use.

### 3.4 General-Purpose AI (GPAI) Considerations

The Phikon-v2 foundation model used in VarunaPoC's ML pipeline may be considered a
general-purpose AI model under Article 51. If so, the model provider (not VarunaPoC as
downstream deployer) bears the GPAI compliance obligations. VarunaPoC's obligations relate
to the specific high-risk application of the model.

---

## 4. Technical Documentation Requirements (Article 11)

When VarunaPoC's AI components are classified as high-risk, Article 11 and Annex IV
mandate comprehensive technical documentation. The following sections map these requirements
to VarunaPoC's architecture.

### 4.1 General Description (Annex IV, Section 1)

| Requirement | VarunaPoC Status | Gap |
|-------------|-----------------|-----|
| Intended purpose of the AI system | Partially documented (PROPOSAL_VARUNA_v2.md Section 3) | Needs formal intended use statement per AI Act format |
| Name and contact of the provider | Not formalized | Must designate legal entity as provider |
| Interaction with hardware/software | Documented (architecture docs) | Needs update to reference AI Act terminology |
| Versions of relevant software/firmware | Git-versioned, CI/CD in place | Needs formal version control policy for AI components |

### 4.2 Training Data Description (Annex IV, Section 2)

**Required documentation:**

- **Data sources:** Origin, collection methodology, geographic/demographic representation
- **Data preprocessing:** Cleaning, labeling methodology, quality control measures
- **Labeling methodology:** Who labeled, inter-annotator agreement metrics, adjudication
- **Data splits:** Training/validation/test split rationale and methodology
- **Known gaps and biases:** Analysis of representativeness

**VarunaPoC current state:** The ML pipeline currently operates in mock mode. No training
data documentation exists because no model training has been performed on VarunaPoC-specific
data. The Phikon-v2 foundation model was pre-trained externally.

**Action required:** When real inference is deployed:
1. Document Phikon-v2's training data provenance (rely on model card from provider)
2. Document any fine-tuning data collected through VarunaPoC's feedback loop
3. Implement annotation quality metrics (kappa inter-annotator, planned for MVP)
4. Create a data governance framework for pathology images used in training

### 4.3 Model Architecture and Performance (Annex IV, Section 3)

**Required documentation:**

| Element | Description | VarunaPoC Applicability |
|---------|-------------|------------------------|
| Model architecture | Network topology, layers, parameters | Document Phikon-v2 architecture + VarunaPoC's inference pipeline |
| Design choices | Why this model/approach was selected | Document in ADR (Architecture Decision Records) |
| Training procedure | Hyperparameters, optimization, stopping criteria | Applicable when fine-tuning is implemented |
| Performance metrics | Accuracy, precision, recall, F1, AUC-ROC | Must be computed on representative clinical dataset |
| Computational requirements | Hardware, inference time, resource consumption | Document GPU requirements, tile processing time |

**Performance metrics to collect (per AI function):**

```
Detection Pipeline:
  - Sensitivity (true positive rate) per tissue type
  - Specificity (true negative rate)
  - Positive predictive value
  - Mean Average Precision (mAP) at IoU thresholds

Classification Pipeline:
  - Top-1 and Top-5 accuracy
  - Per-class precision, recall, F1
  - Confusion matrix
  - Calibration curve (predicted probability vs. observed frequency)

Cell Counting:
  - Mean absolute error vs. manual count
  - Correlation coefficient (Pearson's r)
  - Bland-Altman analysis
```

### 4.4 Accuracy, Robustness, and Cybersecurity Testing (Annex IV, Section 4)

**Accuracy testing requirements:**

- Validated on datasets representative of target population
- Sub-group analysis (tissue types, stain types, scanner manufacturers)
- Comparison against clinical gold standard (pathologist consensus)

**Robustness testing requirements:**

- Performance under input variations (stain variability, focus quality, scanner calibration)
- Adversarial robustness assessment
- Out-of-distribution detection capability
- Graceful degradation behavior

**Cybersecurity requirements (aligned with ENISA guidelines):**

- Model integrity protection (prevent tampering)
- Input validation (reject malformed or adversarial inputs)
- Inference endpoint access control (VarunaPoC has RBAC via Keycloak)
- Audit logging of AI predictions (VarunaPoC has audit trail system)

### 4.5 Human Oversight Mechanisms (Article 14)

**Required capabilities:**

| Oversight Mechanism | VarunaPoC Implementation | Status |
|--------------------|-------------------------|--------|
| Ability to understand AI output | Heatmap visualization overlay on WSI | Implemented |
| Ability to disregard AI output | AI is advisory only; pathologist makes diagnosis | By design |
| Ability to interrupt AI operation | ML inference is on-demand (user-triggered) | Implemented |
| Monitoring of AI behavior | Audit logs capture AI predictions and user actions | Implemented |
| Feedback mechanism | ML feedback API (POST /api/ml/feedback) planned | Planned (Phase 2.2) |

**VarunaPoC's human-in-the-loop design** is a significant strength. The system is explicitly
designed as a decision-support tool where the pathologist retains full diagnostic authority.

### 4.6 Data Governance Procedures (Article 10)

**Required data governance measures:**

1. **Relevance assessment:** Ensure training data reflects real-world deployment conditions
2. **Completeness analysis:** Identify gaps in data coverage
3. **Bias examination:** Statistical analysis of data distribution vs. target population
4. **Annotation quality:** Documented inter-annotator agreement (VarunaPoC plans kappa metrics)
5. **Data protection:** Pseudonymization of patient data (VarunaPoC: on-premise deployment,
   RGPD-compliant design)
6. **Data retention:** Clear policy on training data lifecycle

---

## 5. Conformity Assessment Path (Article 43)

### 5.1 Assessment Options

For medical device AI under IVDR, the conformity assessment follows the IVDR pathway
(Article 43(1)):

| IVDR Class | Conformity Route | Third-Party Required | Estimated Cost |
|------------|-----------------|---------------------|----------------|
| Class A | Self-declaration (Annex II IVDR) | No | EUR 10,000-30,000 (internal) |
| Class B | Notified Body (Annex IX/XI IVDR) | Yes | EUR 50,000-150,000 |
| Class C | Notified Body (Annex IX IVDR) | Yes | EUR 200,000-500,000 |

### 5.2 AI Act Additional Requirements

Beyond the IVDR conformity assessment, high-risk AI systems must also:

1. Establish a **Quality Management System** (Article 17)
2. Maintain **technical documentation** (Article 11, Annex IV)
3. Implement **automatic logging** (Article 12) -- VarunaPoC has audit logging
4. Ensure **transparency** to deployers (Article 13)
5. Conduct **fundamental rights impact assessment** for public deployers (Article 27)

### 5.3 CE Marking Process

```
Step 1: Classify under IVDR + AI Act
         |
Step 2: Prepare technical documentation (Annex IV)
         |
Step 3: Implement Quality Management System (Article 17)
         |
Step 4: Conduct conformity assessment (IVDR pathway)
         |
Step 5: Register in EU AI database (Article 49)
         |
Step 6: Affix CE marking
         |
Step 7: Post-market monitoring (Article 72)
```

---

## 6. Post-Market Monitoring Obligations

### 6.1 Post-Market Monitoring System (Article 72)

High-risk AI system providers must establish a post-market monitoring system that:

- Actively and systematically collects data on AI system performance
- Evaluates continued compliance with requirements
- Identifies risks that were not anticipated

### 6.2 Serious Incident Reporting (Article 73)

Providers must report to national authorities any serious incident within **15 days** of
becoming aware of it. Serious incidents include:
- Death or serious damage to health
- Serious and irreversible disruption of critical infrastructure
- Breach of fundamental rights obligations

### 6.3 Monitoring Plan for VarunaPoC

| Monitoring Area | Method | Frequency | Responsible |
|----------------|--------|-----------|-------------|
| Model performance drift | Compare predictions vs. validated outcomes | Continuous (planned Phase 3.0) | ML Engineer |
| User feedback on AI accuracy | Feedback loop API | Per-prediction (planned Phase 2.2) |  Pathologist + ML Engineer |
| Adverse event tracking | Audit log analysis | Monthly review | Quality Manager |
| Data distribution shift | Statistical comparison of input data | Quarterly | Data Scientist |
| Cybersecurity vulnerabilities | Dependency scanning (Trivy, Bandit in CI) | Per-commit | DevOps |

---

## 7. Enforcement Timeline

### 7.1 AI Act Key Dates

| Date | Milestone | VarunaPoC Impact |
|------|-----------|-----------------|
| **1 August 2024** | AI Act entered into force | Awareness phase begins |
| **2 February 2025** | Prohibited AI practices (Article 5) apply | No impact (VarunaPoC does not use prohibited practices) |
| **2 August 2025** | GPAI model obligations (Chapter V) apply | Phikon-v2 provider must comply; monitor for model cards |
| **2 August 2026** | **High-risk AI obligations apply** | All Article 6-51 requirements become enforceable |
| **2 August 2027** | High-risk AI in Annex I (including medical devices) -- extended deadline | Final deadline for medical device AI compliance |

### 7.2 VarunaPoC-Specific Timeline

```
2026 Q1 (NOW)     Gap analysis and documentation planning (this document)
2026 Q2-Q3        Implement logging, transparency, and oversight mechanisms
2026 Q4            Prepare technical documentation skeleton (Annex IV)
2027 Q1            Complete QMS documentation
2027 Q2            Internal conformity assessment readiness review
2027 H2            Formal conformity assessment (if pursuing IVDR Class C)
```

---

## 8. Gap Analysis: VarunaPoC Current State

### 8.1 Compliance Status Matrix

| AI Act Requirement | Article | Current Status | Priority |
|--------------------|---------|---------------|----------|
| Risk classification performed | Art. 6 | Done (this document) | Complete |
| Technical documentation | Art. 11, Annex IV | Not started | High |
| Automatic logging | Art. 12 | Partial (audit logs exist) | Medium |
| Transparency to deployers | Art. 13 | Not formalized | Medium |
| Human oversight design | Art. 14 | Strong (human-in-the-loop by design) | Low |
| Accuracy and robustness | Art. 15 | Not tested (mock mode) | High (when real AI) |
| Quality Management System | Art. 17 | Not established | High |
| EU database registration | Art. 49 | Not applicable yet | Low |
| Post-market monitoring | Art. 72 | Planned (Phase 3.0 drift detection) | Medium |
| Serious incident reporting | Art. 73 | No procedure established | Medium |

### 8.2 Strengths

1. **Human-in-the-loop design:** The pathologist retains diagnostic authority. AI outputs
   are advisory overlays (heatmaps, detections) that the user can accept or dismiss.
2. **Audit trail:** The existing audit logging system captures user actions and can be
   extended to log AI predictions.
3. **On-premise deployment:** Data stays within hospital infrastructure, simplifying
   data governance requirements.
4. **Modular architecture:** The ML pipeline is isolated from the core viewer, enabling
   independent compliance assessment of AI components.
5. **Open-source transparency:** Code is publicly available on GitHub for inspection.

### 8.3 Critical Gaps

1. **No formal QMS:** A quality management system must be established covering AI lifecycle.
2. **No performance validation:** Real clinical validation data does not exist (mock mode).
3. **No data governance framework:** Training data policies are not defined.
4. **No designated provider entity:** A legal entity must be designated as the AI system provider.
5. **No conformity assessment plan:** Timeline and budget for assessment not established.

---

## 9. Recommendations and Action Plan

### 9.1 Immediate Actions (2026 Q1-Q2)

1. **Formalize intended use statement** per AI Act terminology in project documentation
2. **Extend audit logging** to capture all AI inference requests, inputs, outputs, and
   confidence scores (Article 12 compliance)
3. **Create transparency documentation** (Article 13): user-facing description of AI
   capabilities, limitations, and known failure modes
4. **Begin ADR documentation** for AI-related design decisions

### 9.2 Medium-Term Actions (2026 Q3-Q4)

1. **Establish QMS framework** (Article 17) with procedures for:
   - AI model version control (MLflow registry planned)
   - Training data management
   - Change management for AI components
   - Complaint handling and incident reporting
2. **Design clinical validation protocol** for when real inference is deployed
3. **Implement drift detection** (Evidently AI, planned for Phase 3.0)
4. **Create risk management file** per ISO 14971 (aligned with IVDR and AI Act)

### 9.3 Long-Term Actions (2027+)

1. **Conduct clinical validation study** on representative patient cohort
2. **Complete Annex IV technical documentation** package
3. **Engage Notified Body** for conformity assessment (if pursuing IVDR Class C)
4. **Register in EU AI database** (Article 49)
5. **Establish post-market monitoring system** (Article 72)

### 9.4 Cost Estimate

| Activity | Estimated Cost | Timeline |
|----------|---------------|----------|
| QMS establishment | EUR 20,000-50,000 | 6-12 months |
| Clinical validation study | EUR 100,000-300,000 | 12-24 months |
| Notified Body conformity assessment | EUR 200,000-500,000 | 18-36 months |
| Technical documentation preparation | EUR 30,000-80,000 | 6-12 months |
| Post-market monitoring infrastructure | EUR 15,000-30,000/year | Ongoing |
| **Total (high-risk pathway)** | **EUR 365,000-960,000** | **3-5 years** |

---

## 10. References

1. **Regulation (EU) 2024/1689** -- EU AI Act.
   Official Journal of the European Union, L 2024/1689.
   https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32024R1689

2. **Regulation (EU) 2017/746** -- IVDR (In Vitro Diagnostic Regulation).
   https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32017R0746

3. **MDCG 2021-24** -- Guidance on classification of IVD medical devices.
   https://health.ec.europa.eu/medical-devices-sector/new-regulations/guidance-mdcg-endorsed-documents_en

4. **ISO 14971:2019** -- Medical devices: Application of risk management to medical devices.

5. **ISO/IEC 42001:2023** -- Information technology: Artificial intelligence management system.

6. **ENISA** -- Cybersecurity of AI and standardisation. 2023.
   https://www.enisa.europa.eu/publications/cybersecurity-of-ai-and-standardisation

7. **VarunaPoC Proposal v2** -- PROPOSAL_VARUNA_v2.md, Section 7 (Cadre Reglementaire).

8. **VarunaPoC Architecture v3** -- docs/architecture/README.md (Standards et Conformite).

---

*This document is for regulatory planning purposes only and does not constitute legal advice.
Consult with a qualified regulatory affairs professional before making compliance decisions.*

*Last updated: 2026-02-18*
