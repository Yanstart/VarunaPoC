# US TEFCA/QHIN Participation Exploration for VarunaPoC

**Document Version:** 1.0
**Date:** 2026-02-18
**Classification:** Regulatory Exploration (Documentation Only)
**Applicable Framework:** TEFCA (Trusted Exchange Framework and Common Agreement)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [TEFCA Overview](#2-tefca-overview)
3. [QHIN Participation Requirements](#3-qhin-participation-requirements)
4. [Relevance to VarunaPoC](#4-relevance-to-varunapoc)
5. [Technical Requirements](#5-technical-requirements)
6. [Designated QHINs Landscape](#6-designated-qhins-landscape)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Gap Analysis vs Current VarunaPoC Capabilities](#8-gap-analysis-vs-current-varunapoc-capabilities)
9. [Cost and Resource Estimate](#9-cost-and-resource-estimate)
10. [Recommendations](#10-recommendations)
11. [References](#11-references)

---

## 1. Executive Summary

TEFCA (Trusted Exchange Framework and Common Agreement) is the US federal initiative to
establish a universal floor for interoperability across health information networks. It
enables organizations to exchange health information at a national scale through Qualified
Health Information Networks (QHINs).

**Relevance to VarunaPoC:** If VarunaPoC is deployed in US healthcare settings, TEFCA
participation would enable standardized exchange of pathology reports, diagnostic imaging
references, and AI-assisted findings with other healthcare organizations nationwide. This
aligns with VarunaPoC's existing FHIR R4 stub and interoperability goals.

**Key finding:** VarunaPoC would not become a QHIN itself (the requirements are substantial
and designed for health information networks, not individual applications). Instead, VarunaPoC
would participate as a **Participant** or **Sub-Participant** of an existing QHIN, using the
QHIN's infrastructure for nationwide health information exchange.

**Current readiness:** Low. VarunaPoC has a FHIR R4 stub but lacks the full FHIR server
implementation, US Core IG conformance, SMART on FHIR authorization, and patient matching
capabilities required for TEFCA participation. This document provides a roadmap for closing
these gaps.

---

## 2. TEFCA Overview

### 2.1 Background

TEFCA was mandated by the 21st Century Cures Act (2016) and is managed by the Sequoia
Project as the Recognized Coordinating Entity (RCE). It establishes:

- A **Common Agreement** that QHINs sign, creating a trust framework
- **Standard Operating Procedures (SOPs)** for exchange
- **QTFs (QHIN Technical Framework)** specifying technical requirements
- A governance structure for dispute resolution and compliance

### 2.2 Architecture

```
+----------------------------------------------------+
|                  TEFCA ECOSYSTEM                    |
|                                                     |
|  +----------+    +----------+    +----------+      |
|  |  QHIN A  |<-->|  QHIN B  |<-->|  QHIN C  |     |
|  |eHealth   |    |CommonWell|    | Kno2     |      |
|  |Exchange  |    |          |    |          |      |
|  +----+-----+    +----+-----+    +----+-----+     |
|       |               |               |            |
|  +----+-----+    +----+-----+    +----+-----+     |
|  |Participant|   |Participant|   |Participant|     |
|  | (EHR A)  |    | (EHR B)  |    | (Lab C)  |     |
|  +----+-----+    +----+-----+    +----+-----+     |
|       |               |               |            |
|  +----+-----+    +----+-----+    +----+-----+     |
|  |Sub-Part. |    |Sub-Part. |    |Sub-Part. |     |
|  |(Clinic)  |    |(Hospital)|    |(VarunaPoC|     |
|  |          |    |          |    |  <here)  |     |
|  +----------+    +----------+    +----------+     |
+----------------------------------------------------+
```

### 2.3 Exchange Purposes (EPs)

TEFCA defines specific Exchange Purposes that govern when and why data can be exchanged:

| Exchange Purpose | Description | VarunaPoC Applicability |
|-----------------|-------------|----------------------|
| **Treatment** | Direct patient care | Primary: sharing pathology reports with treating providers |
| **Payment** | Claims and reimbursement | Secondary: pathology service billing context |
| **Healthcare Operations** | Quality improvement, care coordination | Relevant for pathology quality programs |
| **Public Health** | Disease reporting, surveillance | Cancer registry reporting via pathology |
| **Individual Access Services (IAS)** | Patient access to their own data | Patient access to pathology results |
| **Government Benefits Determination** | Disability, benefits assessment | Not primary use case |

---

## 3. QHIN Participation Requirements

### 3.1 Levels of Participation

| Level | Entity | Requirements | VarunaPoC Path |
|-------|--------|-------------|---------------|
| **QHIN** | Health Information Network | Extensive technical, legal, financial requirements; RCE designation | Not suitable for VarunaPoC |
| **Participant** | Organization connected to a QHIN | Agreement with QHIN; technical connectivity | Possible if VarunaPoC operator joins a QHIN |
| **Sub-Participant** | Organization connected through a Participant | Agreement with Participant; may use Participant's infrastructure | Most likely path for VarunaPoC |

### 3.2 QHIN Requirements (for context)

While VarunaPoC would not become a QHIN, understanding these requirements provides context
for what is expected in the ecosystem:

- Minimum $5M in cyber liability insurance
- SOC 2 Type II certification
- 24/7 operations capability
- Patient matching service with >95% precision and recall
- Full FHIR R4 and HL7v2 support
- USCDI (United States Core Data for Interoperability) support
- Connectivity to other QHINs via QHIN Technical Framework

### 3.3 Participant/Sub-Participant Requirements

| Requirement Category | Details |
|---------------------|---------|
| **Legal** | Sign Participant Agreement (PA) or Sub-Participant Agreement |
| **Technical** | Implement QHIN Technical Framework (QTF) connectivity |
| **Security** | Comply with TEFCA Security Requirements (based on NIST CSF) |
| **Privacy** | Adhere to TEFCA privacy requirements (aligned with HIPAA minimum necessary) |
| **Identity Proofing** | Users must be identity-proofed per NIST SP 800-63 IAL2 |
| **Patient Matching** | Implement or use QHIN's patient matching algorithm |
| **FHIR Capability** | FHIR R4 endpoint supporting USCDI data elements |

---

## 4. Relevance to VarunaPoC

### 4.1 Pathology Report Exchange

The primary use case for VarunaPoC's TEFCA participation would be the exchange of
**pathology reports** as structured FHIR resources:

| FHIR Resource | Pathology Use | USCDI Category |
|--------------|--------------|----------------|
| DiagnosticReport | Pathology report (final diagnosis, staging) | Clinical Notes / Diagnostic Imaging |
| Observation | Individual findings, measurements, tumor markers | Laboratory |
| Specimen | Specimen type, collection, handling | Not in USCDI v3 core |
| ImagingStudy | Reference to WSI images | Diagnostic Imaging |
| ServiceRequest | Pathology order/request | Not in USCDI v3 core |
| Practitioner | Pathologist identity | Provenance |
| Patient | Patient demographics for matching | Demographics |

### 4.2 Value Proposition

| Benefit | Description |
|---------|-------------|
| **Second opinion workflow** | Pathologist at Hospital A can request review from specialist at Hospital B via TEFCA |
| **Cancer registry reporting** | Structured pathology data can flow to state/national registries |
| **Treatment coordination** | Oncologist receives pathology results through TEFCA for treatment planning |
| **Patient access** | Patients can access their pathology reports through any TEFCA-connected portal |
| **Research networks** | De-identified pathology data can support multi-site research |

### 4.3 Limitations

- **WSI image exchange** is not well-supported by TEFCA currently (focus is on structured data)
- **AI inference results** have no standardized FHIR representation in USCDI
- **Annotation data** (GeoJSON regions) is VarunaPoC-specific and not interoperable via TEFCA

---

## 5. Technical Requirements

### 5.1 FHIR R4 Endpoint Capability

VarunaPoC must expose a FHIR R4-compliant endpoint that supports:

**Required interactions:**

| Interaction | FHIR Operation | VarunaPoC Implementation |
|------------|---------------|------------------------|
| Search | GET /DiagnosticReport?patient=... | Must implement |
| Read | GET /DiagnosticReport/[id] | Must implement |
| Create | POST /DiagnosticReport | Must implement |
| Capability Statement | GET /metadata | Must implement |

**FHIR server requirements:**

```
VarunaPoC FHIR Endpoint Architecture:

+----------------+     +-----------------+     +----------------+
| QHIN Gateway   |---->| VarunaPoC FHIR  |---->| VarunaPoC      |
| (Participant's)|     | Facade (new)    |     | Core Backend   |
| infrastructure |     |                 |     | (FastAPI)      |
+----------------+     +---------+-------+     +--------+-------+
                                 |                      |
                         +-------+-------+       +------+------+
                         | FHIR Resource |       | PostgreSQL  |
                         | Mapping Layer |       | (existing)  |
                         +---------------+       +-------------+
```

### 5.2 US Core Implementation Guide Conformance

The US Core IG defines minimum conformance requirements for FHIR resources exchanged
in the US healthcare system. VarunaPoC must conform to:

| US Core Profile | Version | Pathology Relevance |
|----------------|---------|-------------------|
| US Core DiagnosticReport Profile | 6.1.0 | Primary: pathology reports |
| US Core Laboratory Result Observation | 6.1.0 | Individual pathology findings |
| US Core Patient | 6.1.0 | Patient demographics for matching |
| US Core Practitioner | 6.1.0 | Pathologist identity |
| US Core Organization | 6.1.0 | Hospital/lab identity |
| US Core Encounter | 6.1.0 | Clinical context |

**Key conformance requirements:**

- Must-support elements must be populated when available
- Terminology bindings (SNOMED CT, LOINC, ICD-10-CM) must be used
- Search parameters defined in US Core must be supported
- Capability Statement must advertise supported profiles

### 5.3 Security: OAuth 2.0 + SMART on FHIR

TEFCA requires robust authorization mechanisms:

**SMART on FHIR implementation:**

| Component | Description | VarunaPoC Status |
|-----------|-------------|-----------------|
| OAuth 2.0 Authorization Server | Issues access tokens | Keycloak (existing) |
| SMART App Launch | Standardized app authorization | Not implemented |
| Scopes | patient/*.read, user/*.read | Must be configured |
| Token introspection | Validate tokens from external systems | Keycloak supports this |
| Backend services auth | Client credentials for server-to-server | Must be configured |

**SMART on FHIR authorization flow:**

```
1. QHIN system discovers VarunaPoC's authorization endpoints
   GET /.well-known/smart-configuration

2. QHIN system requests authorization
   POST /auth/token (client_credentials for backend services)

3. VarunaPoC validates the request against TEFCA policies
   - Verify QHIN identity
   - Validate exchange purpose
   - Apply minimum necessary rules

4. VarunaPoC issues scoped access token
   - Limited to specific FHIR resources
   - Time-limited

5. QHIN system accesses FHIR resources
   GET /fhir/DiagnosticReport?patient=...
   Authorization: Bearer <token>
```

### 5.4 Patient Matching

TEFCA requires robust patient matching to ensure records are associated with the correct
patient across organizations:

| Matching Element | USCDI Data Element | Reliability |
|-----------------|-------------------|-------------|
| First name + Last name | Patient.name | Medium (variants, errors) |
| Date of birth | Patient.birthDate | High |
| Sex | Patient.gender | Medium |
| Address | Patient.address | Medium (changes) |
| Phone number | Patient.telecom | Medium (changes) |
| SSN (last 4) | Patient.identifier | High (when available) |
| MRN | Patient.identifier | High (within same system) |

**Patient matching approaches:**

1. **Probabilistic matching** -- weighted scoring of demographic elements
2. **Referential matching** -- using a master patient index (MPI)
3. **QHIN matching service** -- leverage the QHIN's built-in matching capability

**Recommendation for VarunaPoC:** Use the QHIN's patient matching service rather than
building a custom matching algorithm. VarunaPoC should provide the required demographic
data elements to enable matching.

---

## 6. Designated QHINs Landscape

### 6.1 Current and Prospective QHINs (as of February 2026)

| QHIN | Type | Focus | Potential Fit for VarunaPoC |
|------|------|-------|---------------------------|
| **eHealth Exchange** | Health information exchange | Hospital and health system connectivity | Good -- large hospital network |
| **CommonWell Health Alliance** | Health data utility | EHR vendor-neutral exchange | Good -- broad reach |
| **Kno2** | Direct messaging network | Secure messaging, document exchange | Fair -- report exchange |
| **KONZA** | Health information exchange | Rural and underserved areas | Niche |
| **Epic Carequality** | EHR-centric network | Epic ecosystem | Good if deployed alongside Epic |
| **MedAllies** | Health information exchange | Provider-focused exchange | Fair |
| **Rhapsody / Corepoint** | Integration engine | Technical connectivity | Infrastructure option |

### 6.2 QHIN Selection Criteria for VarunaPoC

| Criterion | Weight | Consideration |
|-----------|--------|--------------|
| Pathology lab connectivity | High | Does the QHIN have pathology labs as participants? |
| Hospital network coverage | High | Are target deployment hospitals already participants? |
| FHIR R4 maturity | High | Does the QHIN have mature FHIR infrastructure? |
| Onboarding complexity | Medium | How complex is the participant onboarding process? |
| Cost | Medium | Annual fees, per-transaction costs |
| International support | Low | Does the QHIN support cross-border exchange? |

### 6.3 Recommended Path

**Primary recommendation:** Join as a Sub-Participant through an existing Participant
(likely the hospital or health system where VarunaPoC is deployed). This is the simplest
path because:

1. The hospital may already be a QHIN Participant
2. VarunaPoC inherits the hospital's TEFCA legal agreements
3. VarunaPoC uses the hospital's patient matching infrastructure
4. Lower technical and financial burden on VarunaPoC

---

## 7. Implementation Roadmap

### 7.1 Phase 1: Foundation (6-9 months)

**Objective:** Build FHIR R4 server capability within VarunaPoC.

| Task | Description | Effort |
|------|-------------|--------|
| FHIR server integration | Implement FHIR R4 facade over existing API | 3-4 months |
| US Core IG conformance | Map pathology data to US Core profiles | 2-3 months |
| Terminology binding | SNOMED CT, LOINC mapping for pathology concepts | 1-2 months |
| FHIR validation | HL7 FHIR Validator integration for resource validation | 1 month |

**Key deliverables:**
- `/fhir/metadata` endpoint returning CapabilityStatement
- `/fhir/DiagnosticReport` CRUD operations
- `/fhir/Observation` for pathology findings
- US Core conformance for all exposed resources

### 7.2 Phase 2: Security and Authorization (3-6 months)

**Objective:** Implement SMART on FHIR authorization.

| Task | Description | Effort |
|------|-------------|--------|
| SMART configuration | Publish `.well-known/smart-configuration` | 1 month |
| Backend services auth | Client credentials flow for server-to-server | 1-2 months |
| Scope enforcement | Implement FHIR resource-level scope checking | 1-2 months |
| Security hardening | NIST CSF alignment, penetration testing | 2-3 months |

### 7.3 Phase 3: TEFCA Onboarding (6-12 months)

**Objective:** Complete TEFCA Participant/Sub-Participant onboarding.

| Task | Description | Effort |
|------|-------------|--------|
| QHIN selection | Evaluate and select QHIN partner | 1-2 months |
| Legal agreements | Negotiate and sign Participant/Sub-Participant agreement | 2-3 months |
| Technical connectivity | Implement QHIN-specific connectivity requirements | 2-3 months |
| Testing and certification | Complete QHIN onboarding testing | 2-3 months |
| Production go-live | Enable TEFCA exchange in production | 1 month |

### 7.4 Total Timeline

```
Year 1 (Months 1-12)
  Q1-Q2: FHIR R4 server implementation
  Q3: US Core IG conformance
  Q4: SMART on FHIR implementation

Year 2 (Months 13-24)
  Q1: Security hardening and testing
  Q2: QHIN selection and legal negotiation
  Q3: Technical connectivity and testing
  Q4: Production onboarding
```

---

## 8. Gap Analysis vs Current VarunaPoC Capabilities

### 8.1 Detailed Gap Assessment

| Capability | Required for TEFCA | VarunaPoC Current State | Gap Severity |
|-----------|-------------------|------------------------|-------------|
| FHIR R4 server | Full FHIR R4 endpoint | Stub only (no real implementation) | **Critical** |
| US Core IG profiles | DiagnosticReport, Observation, Patient | Not implemented | **Critical** |
| SMART on FHIR | OAuth 2.0 + SMART scopes | Keycloak OIDC (no SMART) | **High** |
| Patient matching | Demographics-based matching | No patient management | **High** |
| Terminology (SNOMED/LOINC) | Coded pathology concepts | Not implemented | **High** |
| USCDI data elements | v3 data elements supported | Not mapped | **High** |
| Audit logging | FHIR AuditEvent resources | Existing audit system (not FHIR format) | **Medium** |
| HIPAA compliance | Full HIPAA safeguards | Partial (RBAC, audit) | **Medium** |
| HL7v2 support | ADT, ORM/OBR messages | Not implemented | **Medium** |
| Security certification | SOC 2 or equivalent | Not certified | **Medium** |
| Uptime SLA | 99.9%+ availability | No SLA defined | **Low** |

### 8.2 Strengths to Leverage

1. **Keycloak as OAuth 2.0 server** -- foundation for SMART on FHIR
2. **REST API architecture** -- FastAPI can expose FHIR endpoints
3. **Audit logging** -- existing system can be extended to FHIR AuditEvent
4. **PostgreSQL** -- can store FHIR resources
5. **On-premise deployment** -- simplifies HIPAA physical safeguard compliance
6. **Open-source** -- transparency supports trust framework participation

### 8.3 Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| FHIR implementation complexity exceeds estimates | High | High | Consider using existing FHIR server (HAPI FHIR) as backend |
| TEFCA framework evolves during implementation | Medium | Medium | Track RCE announcements; design for flexibility |
| No QHIN willing to onboard a non-US entity | Medium | High | Partner with US-based healthcare system for deployment |
| Pathology-specific FHIR profiles immature | Medium | Medium | Engage with HL7 AP (Anatomic Pathology) work group |
| Cost exceeds available budget | High | High | Prioritize FHIR capability (useful beyond TEFCA) |

---

## 9. Cost and Resource Estimate

### 9.1 Development Costs

| Phase | Effort (Person-Months) | Cost Estimate (USD) |
|-------|----------------------|-------------------|
| FHIR R4 server implementation | 6-9 PM | $90,000-135,000 |
| US Core IG conformance | 3-4 PM | $45,000-60,000 |
| SMART on FHIR | 2-3 PM | $30,000-45,000 |
| Security hardening | 2-3 PM | $30,000-45,000 |
| TEFCA onboarding | 3-4 PM | $45,000-60,000 |
| **Total development** | **16-23 PM** | **$240,000-345,000** |

### 9.2 Ongoing Costs

| Item | Annual Cost (USD) |
|------|------------------|
| QHIN Participant/Sub-Participant fees | $10,000-50,000 |
| FHIR server maintenance | $20,000-40,000 |
| Security monitoring and compliance | $15,000-30,000 |
| Terminology license (SNOMED CT US edition) | $0 (free for US entities) |
| **Total annual** | **$45,000-120,000** |

---

## 10. Recommendations

### 10.1 Strategic Recommendation

**Build FHIR R4 capability first, TEFCA second.**

The FHIR R4 server capability is valuable independent of TEFCA participation. It enables:
- Integration with any FHIR-capable EHR (Epic, Cerner, etc.)
- EHDS compliance in the EU (which also mandates FHIR)
- HL7 IPS (International Patient Summary) support
- IHE (Integrating the Healthcare Enterprise) profile conformance

TEFCA participation can then be layered on top of the FHIR foundation.

### 10.2 Short-Term Actions (2026)

1. **Complete FHIR R4 stub** into a functional FHIR server for DiagnosticReport
2. **Map VarunaPoC pathology data model** to US Core DiagnosticReport profile
3. **Engage with HL7 AP work group** to understand pathology-specific FHIR profiling
4. **Monitor TEFCA evolution** -- track new QHIN designations and policy updates

### 10.3 Medium-Term Actions (2027)

1. **Implement SMART on FHIR** authorization in Keycloak
2. **Add SNOMED CT / LOINC terminology** binding for pathology concepts
3. **Identify target QHIN** based on deployment site's existing network
4. **Begin Participant onboarding** discussions with selected QHIN

### 10.4 Decision Points

| Decision | When | Criteria |
|----------|------|----------|
| Proceed with FHIR implementation? | Now | Aligns with EHDS roadmap; low regret |
| Proceed with SMART on FHIR? | After FHIR server complete | Needed for any US deployment |
| Pursue TEFCA participation? | After US deployment confirmed | Only if US market is target |
| Build vs. buy FHIR server? | During Phase 1 | HAPI FHIR (Java) vs. custom FastAPI |

---

## 11. References

1. **Trusted Exchange Framework and Common Agreement (TEFCA)**.
   The Sequoia Project (RCE).
   https://rce.sequoiaproject.org/tefca/

2. **QHIN Technical Framework (QTF)**.
   https://rce.sequoiaproject.org/qhin-technical-framework/

3. **21st Century Cures Act**.
   Public Law 114-255. 2016.

4. **HL7 FHIR R4** -- Fast Healthcare Interoperability Resources.
   https://hl7.org/fhir/R4/

5. **US Core Implementation Guide 6.1.0**.
   https://hl7.org/fhir/us/core/

6. **SMART on FHIR** -- Authorization specification.
   https://smarthealthit.org/

7. **USCDI v3** -- United States Core Data for Interoperability.
   https://www.healthit.gov/isa/united-states-core-data-interoperability-uscdi

8. **NIST SP 800-63** -- Digital Identity Guidelines.
   https://pages.nist.gov/800-63-3/

9. **NIST Cybersecurity Framework (CSF) 2.0**.
   https://www.nist.gov/cyberframework

10. **HL7 Anatomic Pathology Work Group**.
    https://www.hl7.org/Special/committees/anatomicpath/

11. **VarunaPoC Architecture** -- docs/architecture/ARCHITECTURE_V3.md (FHIR R4 reference).

12. **VarunaPoC Proposal v2** -- Section 7.2 (FDA/HIPAA context).

---

*This document is for strategic exploration purposes only. TEFCA participation requires
US-based legal entity status, which VarunaPoC (developed in Belgium) would need to establish
through a US partner or subsidiary. The technical requirements described here are accurate
as of February 2026 but TEFCA is actively evolving.*

*Last updated: 2026-02-18*
