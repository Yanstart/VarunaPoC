# China Data Localization Architecture for VarunaPoC

**Document Version:** 1.0
**Date:** 2026-02-18
**Classification:** Regulatory Architecture Planning (Documentation Only)
**Applicable Regulations:** PIPL, NMPA, Cybersecurity Law, Data Security Law

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Regulatory Landscape](#2-regulatory-landscape)
3. [NMPA Requirements for Medical Device Software](#3-nmpa-requirements-for-medical-device-software)
4. [PIPL Data Localization Mandate](#4-pipl-data-localization-mandate)
5. [On-Premise Deployment Architecture](#5-on-premise-deployment-architecture)
6. [Data Classification and Handling](#6-data-classification-and-handling)
7. [Local Storage Infrastructure](#7-local-storage-infrastructure)
8. [Air-Gapped ML Model Deployment](#8-air-gapped-ml-model-deployment)
9. [GB/T Standards Compliance](#9-gbt-standards-compliance)
10. [ICP Filing and MLPS Requirements](#10-icp-filing-and-mlps-requirements)
11. [Gap Analysis: VarunaPoC Readiness](#11-gap-analysis-varunapoc-readiness)
12. [Implementation Roadmap](#12-implementation-roadmap)
13. [References](#13-references)

---

## 1. Executive Summary

Deploying VarunaPoC in Chinese hospitals requires compliance with a comprehensive set of
data localization, cybersecurity, and medical device regulations that are among the most
stringent in the world. This document outlines the architectural requirements for an
on-premise, air-gapped deployment model that satisfies these obligations.

**Key constraints:**

- **No cross-border data transfer** of personal health information without explicit government
  approval (PIPL Article 38-39, Data Security Law Article 31)
- **NMPA registration** required for medical device software (separate from EU IVDR/FDA)
- **Data must reside on Chinese soil** in infrastructure controlled by a local entity
- **Cybersecurity grading** under the Multi-Level Protection Scheme (MLPS 2.0) is mandatory
- **ICP filing** required for any internet-facing services

**Recommended deployment model:** Fully on-premise within the hospital's isolated network
segment, with no external connectivity for clinical data pathways. Software updates and
model updates delivered via secure offline transfer.

---

## 2. Regulatory Landscape

### 2.1 Key Regulations

| Regulation | Enacted | Scope | Impact on VarunaPoC |
|------------|---------|-------|-------------------|
| **Cybersecurity Law (CSL)** | June 2017 | Network operators, critical information infrastructure | Network security, data localization |
| **Data Security Law (DSL)** | September 2021 | All data processing activities in China | Data classification, cross-border transfer restrictions |
| **Personal Information Protection Law (PIPL)** | November 2021 | Processing of personal information | Consent, data localization, rights of individuals |
| **NMPA Medical Device Regulations** | June 2021 (revised) | Medical devices including SaMD | Registration, clinical evaluation, post-market surveillance |
| **Regulations on AI (Draft)** | Various 2023-2025 | AI systems, generative AI, deep synthesis | Algorithm filing, transparency, safety assessment |

### 2.2 Regulatory Bodies

| Authority | Abbreviation | Responsibility |
|-----------|-------------|---------------|
| National Medical Products Administration | NMPA | Medical device registration and oversight |
| Cyberspace Administration of China | CAC | Data protection, cross-border transfer, algorithm filing |
| Ministry of Industry and Information Technology | MIIT | ICP filing, network security |
| National Health Commission | NHC | Healthcare data governance, hospital informatization |
| Provincial Medical Products Administration | Provincial MPA | Local medical device supervision |

### 2.3 Enforcement Reality

Chinese data protection enforcement has intensified significantly since 2021. Notable
enforcement actions include multi-million RMB fines for cross-border data transfers and
app store removals for non-compliant health applications. Foreign-origin software faces
additional scrutiny under supply chain security reviews.

---

## 3. NMPA Requirements for Medical Device Software

### 3.1 Classification

NMPA classifies medical device software (SaMD) using a risk-based approach similar to but
distinct from IVDR/FDA:

| NMPA Class | Risk Level | Examples | Registration |
|------------|-----------|---------|--------------|
| Class I | Low risk | Image viewer (display only) | Filing (Beian) with local MPA |
| Class II | Medium risk | AI-assisted analysis (advisory) | Registration with provincial MPA |
| Class III | High risk | AI diagnostic (autonomous) | Registration with NMPA (national) |

**VarunaPoC classification assessment:**

| VarunaPoC Mode | NMPA Class | Rationale |
|----------------|-----------|-----------|
| WSI viewer only (no AI) | Class I | Display and navigation of pathology images |
| AI advisory mode (heatmaps, detection) | Class II | Computer-aided analysis with human oversight |
| AI diagnostic mode (future) | Class III | Autonomous diagnostic capability |

### 3.2 Registration Requirements

**For Class II registration (most likely for VarunaPoC with AI features):**

1. **Quality Management System** -- must comply with GB/T 42062 (ISO 13485 equivalent)
2. **Technical documentation** package including:
   - Product description and intended use
   - Software lifecycle documentation (IEC 62304 equivalent: GB/T 25000.51)
   - Risk management file (GB/T 42062)
   - Clinical evaluation report
   - Cybersecurity documentation
3. **Clinical evaluation** -- typically clinical trials at 2-3 Chinese hospitals
4. **Type testing** by NMPA-designated testing institutions
5. **Chinese language** -- all documentation must be in Mandarin Chinese

### 3.3 Local Representation

Foreign medical device manufacturers must appoint a **Chinese Agent** (registration agent)
who holds legal responsibility for the product within China. This agent:

- Submits the registration application on behalf of the foreign manufacturer
- Handles communication with NMPA
- Is responsible for post-market surveillance reporting
- Must be a legally established Chinese entity

---

## 4. PIPL Data Localization Mandate

### 4.1 Core Requirements

**PIPL Article 40:** Personal information collected and generated by Critical Information
Infrastructure Operators (CIIOs) within China must be stored within China. Hospitals
processing health data are generally classified as CIIOs.

**PIPL Article 38-39:** Cross-border transfer of personal information requires one of:
1. Security assessment by CAC (mandatory for CIIOs and large-scale processors)
2. Personal information protection certification
3. Standard contractual clauses
4. Other conditions provided by laws or regulations

**For health data:** Cross-border transfer of health information is effectively prohibited
without CAC security assessment, which is rarely granted for routine clinical data.

### 4.2 Data Localization Impact on VarunaPoC

| Data Type | Classification | Storage Requirement |
|-----------|---------------|-------------------|
| Patient pathology images (WSI) | Sensitive personal information (health data) | Must remain in China |
| Patient demographic data | Personal information | Must remain in China |
| AI model predictions/reports | Derived personal information | Must remain in China |
| Anonymized research data | May not constitute personal information | Cross-border possible with assessment |
| Software source code | Non-personal data | No localization requirement |
| AI model weights (pre-trained) | Non-personal data | Can be imported freely |

### 4.3 Consent Requirements

PIPL requires **separate consent** for processing sensitive personal information (Article 29),
which includes health data. The consent must be:
- Informed and voluntary
- Specific to the processing purpose
- Easily withdrawable
- Documented

---

## 5. On-Premise Deployment Architecture

### 5.1 Network Architecture

```
+================================================================+
|  HOSPITAL NETWORK                                               |
|                                                                 |
|  +---------------------------+    +-------------------------+   |
|  | CLINICAL ZONE (Isolated)  |    | ADMINISTRATIVE ZONE     |   |
|  |                           |    |                         |   |
|  | +----------+ +---------+ |    | +-----+ +------------+  |   |
|  | | VarunaPoC| |PostgreSQL| |    | | HIS | | LIS        |  |   |
|  | | Backend  | |  Local   | |    | |     | | (Pathology)|  |   |
|  | +----+-----+ +----+----+ |    | +--+--+ +-----+------+  |   |
|  |      |            |      |    |    |          |          |   |
|  | +----+-----+ +----+----+ |    +----+----------+----------+   |
|  | | VarunaPoC| | MinIO   | |         |          |              |
|  | | Frontend | | (Slides)| |    +----+----------+----------+   |
|  | +----------+ +---------+ |    | INTEGRATION ZONE        |   |
|  |                           |    | (HL7/FHIR Gateway)      |   |
|  | +----------+ +---------+ |    +-------------------------+   |
|  | | Keycloak | | ML       | |                                  |
|  | | (Auth)   | | Inference| |    +--------------------------+  |
|  | +----------+ +---------+ |    | DMZ (if needed)          |  |
|  +---------------------------+    | NO patient data exposed  |  |
|                                   +--------------------------+  |
+================================================================+
                  |
                  | Air gap (no direct internet for clinical data)
                  |
         +--------+--------+
         | SOFTWARE UPDATE  |
         | (Offline media)  |
         +-----------------+
```

### 5.2 Network Segmentation Rules

| Source Zone | Destination Zone | Allowed Traffic | Notes |
|------------|-----------------|----------------|-------|
| Clinical Zone | Clinical Zone | All VarunaPoC internal | Internal communication only |
| Clinical Zone | Integration Zone | HL7/FHIR messages | Structured data exchange to HIS/LIS |
| Clinical Zone | Internet | **BLOCKED** | No patient data leaves the zone |
| Administrative Zone | Clinical Zone | Read-only queries | For operational monitoring |
| DMZ | Clinical Zone | **BLOCKED** | Strict isolation |
| Update Server | Clinical Zone | Signed packages only | Via offline media or dedicated channel |

### 5.3 Deployment Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend | FastAPI (Python 3.11) | VarunaPoC API server |
| Frontend | Vite + OpenSeadragon | WSI viewer application |
| Database | PostgreSQL 15+ with PostGIS | Annotations, clinical data, audit logs |
| Object Storage | MinIO (S3-compatible) | WSI slide storage |
| Authentication | Keycloak | OIDC/SAML identity management |
| ML Inference | Slideflow + Phikon-v2 (CPU/GPU) | AI analysis (air-gapped) |
| Reverse Proxy | Nginx | TLS termination, routing |
| Monitoring | Prometheus + Grafana | System health (no external telemetry) |
| Container Runtime | Docker / Podman | Application isolation |

---

## 6. Data Classification and Handling

### 6.1 Data Classification Framework

Per the Data Security Law (DSL) Article 21, data must be classified according to its
importance to the state, economy, and society:

| Classification Level | Definition | VarunaPoC Data Examples |
|---------------------|-----------|----------------------|
| **Core Data** | Threatens national security if compromised | Not applicable |
| **Important Data** | Threatens public interest if compromised | Aggregated population health statistics |
| **General Data** | All other data | Individual patient images, annotations, reports |

**Health data** is separately classified as **sensitive personal information** under PIPL,
requiring enhanced protection regardless of DSL classification.

### 6.2 Data Handling Procedures

| Data Category | Encryption at Rest | Encryption in Transit | Access Control | Retention |
|--------------|-------------------|---------------------|---------------|-----------|
| Patient WSI images | AES-256 | TLS 1.2+ | Role-based (pathologist) | Per hospital policy (typically 15+ years) |
| Patient demographics | AES-256 | TLS 1.2+ | Role-based (need-to-know) | Per hospital policy |
| Annotations | AES-256 | TLS 1.2+ | Per-slide access control | Linked to WSI retention |
| AI predictions | AES-256 | TLS 1.2+ | Role-based (pathologist) | Linked to WSI retention |
| Audit logs | Integrity-protected | TLS 1.2+ | Admin only | Minimum 6 months (MLPS) |
| System logs | Standard | TLS 1.2+ | Admin only | 6 months minimum |

### 6.3 Pseudonymization Requirements

Patient data within VarunaPoC must be pseudonymized:

- Patient identifier in VarunaPoC is a system-generated UUID, not the hospital ID
- Mapping table (UUID to hospital ID) stored separately with restricted access
- WSI file metadata must be stripped of patient-identifying DICOM tags before ingestion
- AI model training data must be fully anonymized (no link back to patient)

---

## 7. Local Storage Infrastructure

### 7.1 MinIO for WSI Slide Storage

MinIO provides S3-compatible object storage suitable for on-premise deployment:

```
+---------------------------------------------+
| MinIO Cluster (On-Premise)                  |
|                                             |
| +----------+  +----------+  +----------+   |
| | Node 1   |  | Node 2   |  | Node 3   |   |
| | (Drives) |  | (Drives) |  | (Drives) |   |
| +----------+  +----------+  +----------+   |
|                                             |
| Erasure Coding: EC:4 (4 data + 2 parity)   |
| Encryption: SSE-S3 (server-side AES-256)    |
| Capacity: Scalable (start with 10TB)        |
+---------------------------------------------+
```

**Configuration recommendations:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Erasure coding | EC:4 (4+2) minimum | Data protection against drive failure |
| Encryption | SSE-S3 with local KMS | At-rest encryption for PIPL compliance |
| Bucket structure | One bucket per department | Access isolation |
| Versioning | Enabled | Audit trail for data changes |
| Lifecycle policy | No auto-deletion | Medical records retention compliance |
| Backup | Local tape or secondary storage | No cloud backup for patient data |

### 7.2 PostgreSQL for Clinical Data

```
+---------------------------------------------+
| PostgreSQL 15 (Primary-Replica)             |
|                                             |
| Primary: Clinical zone server               |
| Replica: Same zone, synchronous replication |
|                                             |
| Extensions:                                 |
|   - PostGIS (spatial annotations)           |
|   - pgcrypto (column-level encryption)      |
|   - pg_audit (audit logging)                |
|                                             |
| Backup: Local encrypted backup (pg_dump)    |
| No cloud/remote replication                 |
+---------------------------------------------+
```

**Database security configuration:**

| Setting | Value | Purpose |
|---------|-------|---------|
| ssl | on | Encrypted connections |
| password_encryption | scram-sha-256 | Strong password hashing |
| log_connections | on | Audit trail |
| log_disconnections | on | Audit trail |
| pgaudit.log | all | Comprehensive audit logging |
| pg_hba.conf | Restrict to clinical zone IPs | Network-level access control |

### 7.3 Storage Capacity Planning

| Data Type | Size per Unit | Annual Volume (est.) | 3-Year Storage |
|-----------|-------------|---------------------|----------------|
| WSI slides | 0.5-5 GB each | 10,000 slides/year | 15-150 TB |
| Annotations | ~10 KB each | 50,000 annotations/year | ~1.5 GB |
| AI predictions | ~100 KB each | 10,000 predictions/year | ~3 GB |
| Audit logs | ~1 KB each | 1M events/year | ~3 GB |
| Database | Metadata + annotations | Growing | ~50 GB |

**Recommended initial deployment:** 20 TB MinIO + 500 GB PostgreSQL, scalable.

---

## 8. Air-Gapped ML Model Deployment

### 8.1 Challenge

VarunaPoC's ML pipeline (Slideflow + Phikon-v2) requires model weights and inference code
to be deployed without internet connectivity. Model updates must be delivered through secure
offline channels.

### 8.2 Offline Model Delivery Process

```
DEVELOPMENT SITE                     HOSPITAL (AIR-GAPPED)
(Outside China or secure lab)

1. Train/update model  --------->  2. Package as signed artifact
                                       |
                                       v
                                   3. Transfer via encrypted USB
                                      or secure courier
                                       |
                                       v
                                   4. Verify signature
                                       |
                                       v
                                   5. Load into local model registry
                                       |
                                       v
                                   6. Validate on local test set
                                       |
                                       v
                                   7. Deploy to inference service
```

### 8.3 Model Package Format

```
varunapoc-model-v1.2.3.tar.gz.enc
  |
  +-- manifest.json          # Version, hash, dependencies
  +-- model/
  |   +-- phikon-v2/         # Foundation model weights
  |   +-- classifier/        # Fine-tuned classification head
  |   +-- detector/          # Detection model weights
  +-- config/
  |   +-- inference.yaml     # Inference configuration
  |   +-- thresholds.yaml    # Decision thresholds
  +-- validation/
  |   +-- test_images/       # Reference test set
  |   +-- expected_outputs/  # Expected predictions for validation
  +-- SIGNATURE.asc          # GPG signature of manifest
```

### 8.4 Model Validation Protocol

Before deploying a new model version in the hospital environment:

1. **Verify package integrity** -- check GPG signature against known public key
2. **Run reference test set** -- compare predictions against expected outputs
3. **Performance threshold check** -- ensure metrics meet minimum requirements:
   - Sensitivity >= configured threshold
   - Specificity >= configured threshold
   - Mean inference time <= acceptable latency
4. **Canary deployment** -- run new model alongside existing model for 1 week
5. **Full deployment** -- switch to new model after validation

### 8.5 GPU/CPU Considerations

| Deployment Mode | Hardware | Inference Time (est.) | Suitability |
|----------------|----------|---------------------|-------------|
| GPU (NVIDIA A100/V100) | Dedicated GPU server | ~2.5 min per slide heatmap | Recommended for production |
| GPU (NVIDIA T4) | More affordable GPU | ~5 min per slide heatmap | Acceptable |
| CPU only | Standard server | ~30-60 min per slide heatmap | Emergency fallback only |

**Chinese GPU considerations:** Due to US export controls on advanced GPUs, availability
of NVIDIA A100/H100 may be limited. Consider:
- NVIDIA A30/A16 (generally available)
- Huawei Ascend 910B (domestic alternative, requires software adaptation)
- AMD MI250 (subject to availability)

---

## 9. GB/T Standards Compliance

### 9.1 Relevant Standards

| Standard | Title | Equivalent International Standard |
|---------|-------|----------------------------------|
| **GB/T 42062-2022** | Medical devices -- Quality management systems | ISO 13485:2016 |
| **GB/T 25000.51** | Software engineering -- Software quality requirements | ISO/IEC 25051 |
| **GB/T 35273-2020** | Information security -- Personal information security specification | Comparable to GDPR principles |
| **GB/T 22239-2019** | Information security -- Baseline for classified protection of cybersecurity | MLPS 2.0 |
| **GB/T 39335-2020** | Information security -- Personal information de-identification | - |
| **YY/T 0664-2020** | Medical devices -- Software lifecycle processes | IEC 62304:2006 |
| **YY/T 0316-2016** | Medical devices -- Application of risk management | ISO 14971:2007 |

### 9.2 VarunaPoC Compliance Mapping

| GB/T Requirement | VarunaPoC Feature | Status |
|-----------------|-------------------|--------|
| Personal information encryption (GB/T 35273) | TLS in transit, AES at rest | Architecture supports; implementation needed |
| Audit logging (GB/T 22239) | Audit trail system | Implemented |
| Access control (GB/T 22239) | Keycloak RBAC | Implemented |
| Data backup (GB/T 22239) | PostgreSQL backup, MinIO replication | Architecture defined |
| Incident response (GB/T 22239) | Not formalized | Gap |
| Software lifecycle (YY/T 0664) | CI/CD pipeline, tests | Partially compliant |
| Risk management (YY/T 0316) | PROPOSAL_VARUNA_v2.md Section 8 | Partially documented |

---

## 10. ICP Filing and MLPS Requirements

### 10.1 ICP Filing

**ICP (Internet Content Provider) filing** is required for any service accessible over the
internet within China. Since VarunaPoC is deployed on-premise within a hospital intranet,
ICP filing may not be required unless:

- The application is accessible from outside the hospital network
- The hospital provides remote access to pathology services
- A public-facing website exists for the service

**If required:** ICP filing is done through the local Communications Administration Bureau.
The application must be filed by a Chinese entity (the hospital or local partner).

### 10.2 MLPS 2.0 (Multi-Level Protection Scheme)

MLPS 2.0 (GB/T 22239-2019) is China's mandatory cybersecurity grading system. Healthcare
information systems typically require **Level 2 or Level 3** protection.

| MLPS Level | Applicable To | Key Requirements |
|-----------|--------------|-----------------|
| Level 1 | Low-impact systems | Basic security measures |
| **Level 2** | Systems causing damage to organizations | Access control, audit, backup, encryption |
| **Level 3** | Systems causing serious damage to public interest | All Level 2 + intrusion detection, centralized logging, security operations center |
| Level 4 | Systems causing severe damage to national security | Government and military systems |

### 10.3 MLPS Assessment for VarunaPoC

**Recommended level: Level 2** (minimum) or **Level 3** (if processing sensitive health data
at scale).

**MLPS Level 2 requirements mapping:**

| MLPS Category | Requirement | VarunaPoC Compliance |
|--------------|------------|---------------------|
| **Physical Security** | Server room access control, fire protection | Hospital responsibility |
| **Network Security** | Network segmentation, boundary protection | Architecture designed for isolation |
| **Host Security** | OS hardening, malware protection, patching | Docker containers, CI security scanning |
| **Application Security** | Authentication, authorization, input validation | Keycloak, RBAC, API validation |
| **Data Security** | Encryption, backup, integrity checking | TLS, AES-256, PostgreSQL backup |
| **Security Management** | Policies, procedures, incident response | Gaps: formal documentation needed |

### 10.4 MLPS Assessment Process

1. **Self-assessment** -- Grade the system according to GB/T 22240
2. **Filing** -- Submit grading to local public security bureau (PSB)
3. **Third-party assessment** -- Engage a CAC-certified testing institution
4. **Remediation** -- Address findings from the assessment
5. **Compliance confirmation** -- Receive MLPS compliance certificate
6. **Annual review** -- Re-assessment required annually

---

## 11. Gap Analysis: VarunaPoC Readiness

### 11.1 Compliance Readiness Matrix

| Requirement | Ready | Partial | Gap |
|-------------|-------|---------|-----|
| On-premise deployment architecture | | X | Docker Compose exists; China-specific hardening needed |
| Data localization (no cross-border transfer) | X | | By design (on-premise) |
| PostgreSQL local instance | X | | Implemented |
| MinIO local object storage | | | X | Not yet deployed (NAS currently used) |
| Air-gapped ML deployment | | | X | Requires offline model delivery pipeline |
| MLPS Level 2 compliance | | X | Audit logging exists; formal policies needed |
| Chinese language localization | | | X | Interface and documentation in English/French |
| NMPA registration documentation | | | X | Not started |
| GB/T 42062 QMS | | | X | Not established |
| ICP filing (if needed) | | | X | Requires local entity |
| Local Chinese partner/agent | | | X | Not identified |

### 11.2 Critical Path Items

1. **Local partner identification** -- Must establish a Chinese legal entity or partner
   to act as NMPA registration agent and local operator
2. **Chinese language localization** -- UI, documentation, and labeling must be in Mandarin
3. **NMPA clinical evaluation** -- Requires clinical trials at Chinese hospitals
4. **MLPS assessment** -- Requires third-party security assessment

---

## 12. Implementation Roadmap

### 12.1 Phase 1: Foundation (6-12 months)

- Identify and engage Chinese local partner/agent
- Begin NMPA pre-submission consultation
- Adapt deployment architecture for air-gapped operation
- Implement MinIO for local object storage
- Begin Chinese language localization of UI

### 12.2 Phase 2: Compliance Preparation (12-18 months)

- Complete GB/T 42062 QMS documentation
- Prepare NMPA registration dossier (Class II)
- Conduct MLPS self-assessment and grading
- Build offline model delivery pipeline
- Engage MLPS-certified testing institution

### 12.3 Phase 3: Registration and Deployment (18-30 months)

- Submit NMPA Class II registration application
- Complete MLPS third-party assessment
- Conduct clinical evaluation at Chinese hospitals
- Obtain NMPA registration certificate
- Production deployment at pilot hospital

### 12.4 Cost Estimate

| Activity | Estimated Cost (RMB) | Estimated Cost (EUR) |
|----------|---------------------|---------------------|
| Local partner/agent fees | 200,000-500,000/year | 26,000-65,000/year |
| NMPA registration (Class II) | 500,000-1,500,000 | 65,000-195,000 |
| Clinical evaluation | 1,000,000-3,000,000 | 130,000-390,000 |
| MLPS assessment | 100,000-300,000 | 13,000-39,000 |
| Chinese localization | 200,000-500,000 | 26,000-65,000 |
| On-premise hardware (per site) | 300,000-800,000 | 39,000-104,000 |
| **Total (first deployment)** | **2,300,000-6,600,000** | **300,000-860,000** |

---

## 13. References

1. **Personal Information Protection Law (PIPL)**.
   Standing Committee of the National People's Congress, 2021.
   http://www.npc.gov.cn/npc/c30834/202108/a8c4e3672c74491a80b53a172bb753fe.shtml

2. **Data Security Law (DSL)**.
   Standing Committee of the National People's Congress, 2021.

3. **Cybersecurity Law (CSL)**.
   Standing Committee of the National People's Congress, 2017.

4. **Regulations for the Supervision and Administration of Medical Devices**.
   State Council Order No. 739, revised 2021.

5. **GB/T 22239-2019** -- Information security technology -- Baseline for classified
   protection of cybersecurity (MLPS 2.0).

6. **GB/T 35273-2020** -- Information security technology -- Personal information
   security specification.

7. **GB/T 42062-2022** -- Medical devices -- Quality management systems --
   Requirements for regulatory purposes.

8. **YY/T 0664-2020** -- Medical devices -- Software lifecycle processes.

9. **NMPA Technical Review Guidelines for AI Medical Device Software**.
   NMPA Center for Medical Device Evaluation, 2022.

10. **VarunaPoC Architecture** -- docs/architecture/ARCHITECTURE_V3.md

---

*This document is for architectural planning purposes only. Deployment in China requires
engagement with qualified local regulatory consultants, legal counsel familiar with Chinese
data protection law, and a registered Chinese partner entity. Regulatory requirements
in China evolve rapidly; this document reflects the landscape as of February 2026.*

*Last updated: 2026-02-18*
