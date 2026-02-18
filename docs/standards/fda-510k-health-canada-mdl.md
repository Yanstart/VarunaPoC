# FDA 510(k) and Health Canada MDL Regulatory Planning

**Document Version:** 1.0
**Date:** 2026-02-18
**Classification:** Regulatory Planning (Documentation Only)
**Applicable Regulations:** 21 CFR Part 864 (FDA), CMDR SOR/98-282 (Health Canada)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [FDA 510(k) Pathway Analysis](#2-fda-510k-pathway-analysis)
3. [Product Classification](#3-product-classification)
4. [Predicate Device Analysis](#4-predicate-device-analysis)
5. [Substantial Equivalence Argument](#5-substantial-equivalence-argument)
6. [Performance Testing Requirements](#6-performance-testing-requirements)
7. [510(k) Submission Content Outline](#7-510k-submission-content-outline)
8. [De Novo Pathway Alternative](#8-de-novo-pathway-alternative)
9. [Health Canada MDL Requirements](#9-health-canada-mdl-requirements)
10. [Timeline and Cost Estimates](#10-timeline-and-cost-estimates)
11. [Recommended Strategy](#11-recommended-strategy)
12. [Gap Analysis](#12-gap-analysis)
13. [References](#13-references)

---

## 1. Executive Summary

This document analyzes the regulatory pathways for VarunaPoC to enter the US market (FDA)
and Canadian market (Health Canada) as a medical device. VarunaPoC is a web-based
histopathology slide viewer with AI-assisted analysis capabilities, developed for
CHU UCL Namur (Belgium).

**Current regulatory position** (from PROPOSAL_VARUNA_v2.md Section 7):
- IVDR Class A (research/teaching tool)
- FDA Exempt (viewer without diagnostic AI)

**Target regulatory position for North American market entry:**

| Market | Pathway | Classification | Timeline | Estimated Cost |
|--------|---------|---------------|----------|---------------|
| US (FDA) | 510(k) | Class II (QAS) | 12-18 months | $150,000-350,000 |
| US (FDA) | De Novo | Class II (new) | 18-24 months | $300,000-600,000 |
| Canada | MDL Class II | Class II | 12-18 months | CAD 100,000-250,000 |
| Canada | MDL Class III (AI) | Class III | 18-24 months | CAD 200,000-500,000 |

**Recommended strategy:** Maintain FDA Exempt status for the WSI viewer component. Pursue
510(k) clearance for the AI-assisted analysis functions when clinical validation is complete.
Leverage MDSAP for simultaneous FDA and Health Canada compliance.

---

## 2. FDA 510(k) Pathway Analysis

### 2.1 Regulatory Framework

The FDA regulates medical device software (SaMD) under 21 CFR Parts 800-898. Digital
pathology systems fall under:

- **21 CFR 864.3600** -- Microscopes and accessories (Class I exempt for optical viewing)
- **21 CFR 864.3700** -- Whole slide imaging system (Class II with special controls)
- **Product Code QAS** -- Digital pathology system, whole slide imaging

### 2.2 510(k) Pathway Applicability

A 510(k) submission is required when:
1. The device is Class II (or Class III with an existing 510(k) pathway)
2. A legally marketed predicate device exists
3. The new device is substantially equivalent to the predicate

**For VarunaPoC:**

| Component | Classification | 510(k) Required? |
|-----------|---------------|------------------|
| WSI viewer (display only) | Class I Exempt (21 CFR 864.3600) | No |
| WSI viewer for primary diagnosis | Class II (Product Code QAS) | Yes |
| AI-assisted detection/classification | Class II (Product Code QPN/QAS) | Yes |
| AI autonomous diagnosis | Class II/III (De Novo or PMA) | Yes (De Novo likely) |

### 2.3 Regulatory Pathway Decision Tree

```
Is VarunaPoC a viewer only (no AI, no diagnosis)?
  |
  +-- YES --> Class I Exempt (no 510(k) needed)
  |            Current state: VarunaPoC viewer without AI
  |
  +-- NO --> Does it include AI-assisted features?
              |
              +-- YES --> Is there a predicate device?
              |            |
              |            +-- YES --> 510(k) pathway
              |            |           (Philips K172655, Leica K240315)
              |            |
              |            +-- NO --> De Novo pathway
              |                       (Paige DEN200080 precedent)
              |
              +-- NO (primary diagnosis only) --> 510(k) with QAS predicate
```

---

## 3. Product Classification

### 3.1 FDA Product Classification

| Product Code | Device Name | Regulation | Class | Panel |
|-------------|-------------|-----------|-------|-------|
| **QAS** | Whole slide imaging system, digital pathology, primary diagnosis | 21 CFR 864.3700 | II | 64 (Pathology) |
| **QPN** | Software, AI/ML-based, pathology | 21 CFR 864 (varies) | II | 64 (Pathology) |
| **PZZ** | Software, digital pathology, display | Exempt | I | 64 (Pathology) |

### 3.2 VarunaPoC Product Code Determination

**Primary product code: QAS** (Whole slide imaging system for primary diagnosis)

This classification applies because VarunaPoC:
- Displays digitized pathology slides for review
- Provides AI-assisted analysis overlays (heatmaps, detections)
- Is intended to be used in the clinical pathology workflow

**Special controls for QAS (per FDA guidance):**

1. Software validation (IEC 62304 compliance)
2. Display performance testing (color accuracy, resolution adequacy)
3. Clinical performance testing (non-inferiority to microscope)
4. Labeling (intended use, limitations, training requirements)
5. Cybersecurity documentation (per FDA premarket cybersecurity guidance)

---

## 4. Predicate Device Analysis

### 4.1 Key Predicate Devices

| Device | Company | 510(k)/De Novo | Date | Product Code | Key Features |
|--------|---------|---------------|------|-------------|-------------|
| **IntelliSite Pathology Solution** | Philips | K172655 | 2017 | QAS | First FDA-cleared WSI for primary diagnosis (surgical pathology, non-quantitative) |
| **Aperio GT 450 DX** | Leica | K240315 | 2024 | QAS | WSI system for primary diagnosis, 40x scanning |
| **VENTANA DP 200** | Roche | K202270 | 2021 | QAS | WSI system for primary diagnosis in surgical pathology |
| **Paige Prostate** | Paige AI | DEN200080 | 2021 | QPN | AI-based detection of areas suspicious for cancer (De Novo) |
| **Paige Breast** | Paige AI | K231495 | 2024 | QPN | AI-assisted detection in breast biopsy slides |
| **Proscia Concentriq Dx** | Proscia | K240414 | 2024 | QAS | Digital pathology platform for primary diagnosis |

### 4.2 Predicate Selection for VarunaPoC

**Recommended primary predicate:** Philips IntelliSite (K172655)

| Comparison Element | IntelliSite (K172655) | VarunaPoC |
|-------------------|----------------------|-----------|
| Intended use | Display of digitized surgical pathology slides for primary diagnosis | Display of digitized pathology slides with AI-assisted analysis |
| Technology | Proprietary viewer, iSyntax format | Open-source viewer (OpenSeadragon), multi-format (OpenSlide) |
| Slide formats | Philips iSyntax (.isyntax) | SVS, NDPI, MRXS, BIF, TIFF, CZI, DICOM WSI |
| Display resolution | 40x equivalent | Up to 40x (scanner-dependent) |
| AI features | None (viewer only) | Heatmap overlay, detection, classification |
| Deployment | On-premise (Windows) | On-premise (Linux/Docker), web-based |

**Secondary predicate (for AI features):** Paige Prostate (DEN200080)

The AI-assisted features may require a split predicate approach:
- QAS predicate (IntelliSite) for the viewer/display function
- QPN reference (Paige) for the AI-assisted analysis function

---

## 5. Substantial Equivalence Argument

### 5.1 Argument Structure

The substantial equivalence (SE) argument must demonstrate that VarunaPoC has:
1. The **same intended use** as the predicate device, AND
2. Either the **same technological characteristics** OR different characteristics that
   do not raise new questions of safety and effectiveness

### 5.2 Intended Use Comparison

| Element | Predicate (IntelliSite K172655) | VarunaPoC | Assessment |
|---------|-------------------------------|-----------|-----------|
| Primary function | Display of scanned surgical pathology slides | Display of scanned pathology slides | Equivalent |
| Target user | Pathologists | Pathologists | Equivalent |
| Clinical setting | Pathology laboratory | Pathology laboratory | Equivalent |
| Specimen types | Surgical pathology (formalin-fixed, H&E stained) | Surgical pathology (multiple stains) | Broader -- must address |
| Diagnostic context | Primary diagnosis | Primary diagnosis with AI assistance | Different -- must address |

### 5.3 Technological Characteristics Comparison

| Characteristic | Predicate | VarunaPoC | SE Impact |
|---------------|-----------|-----------|-----------|
| Image rendering | Proprietary renderer | OpenSeadragon (open-source, WebGL) | Different but functionally equivalent |
| File format support | Single (iSyntax) | Multiple (via OpenSlide) | Broader -- advantage, but must validate each format |
| Tiling approach | Proprietary | DZI protocol | Different but functionally equivalent |
| Color management | ICC profile-based | Browser-native color rendering | Must validate equivalence |
| AI overlay | Not present | Present (optional) | New feature -- requires safety/effectiveness data |
| Deployment | Desktop application | Web application (browser-based) | Different -- must validate display fidelity |

### 5.4 Points Requiring Special Attention

1. **Web-based display:** Must demonstrate that browser rendering provides equivalent
   image quality to dedicated desktop applications (color accuracy, resolution, latency)
2. **Multi-format support:** Each file format must be validated for accurate display
3. **AI overlay interaction:** Must demonstrate that AI overlays do not interfere with
   primary diagnostic viewing (can be toggled off, do not obscure tissue)
4. **Open-source components:** Must demonstrate software quality equivalent to proprietary
   systems (testing, validation, change control)

---

## 6. Performance Testing Requirements

### 6.1 Analytical Performance Testing

**Display quality validation:**

| Test | Method | Acceptance Criteria |
|------|--------|-------------------|
| Spatial resolution | USAF 1951 resolution target | Resolve Group 7, Element 6 at 40x |
| Color accuracy | Macbeth ColorChecker, ICC profile | Delta E (CIE2000) < 2.0 for all patches |
| Dynamic range | Grayscale step wedge | Distinguish all 20 steps |
| Tile stitching | Visual inspection of known patterns | No visible seams at tile boundaries |
| Rendering latency | Tile load time measurement | P95 < 200ms for tile delivery |
| Format fidelity | Compare rendered output vs. reference images | SSIM > 0.99 for each format |

**AI performance validation (if AI features included in submission):**

| Test | Dataset | Metrics |
|------|---------|---------|
| Detection sensitivity | 200+ positive slides from 3+ sites | Sensitivity >= 96% (per CAP guidelines) |
| Detection specificity | 200+ negative slides from 3+ sites | Specificity >= 93% |
| Classification accuracy | Stratified by tissue type (500+ slides) | Overall accuracy >= 90%, per-class >= 85% |
| Reproducibility | Same slides run 3x each | CV < 5% for continuous metrics |
| Scanner robustness | Images from 3+ scanner manufacturers | Performance within 5% across scanners |
| Stain variability | H&E, IHC, special stains | Performance within 10% across stain types |

### 6.2 Clinical Performance Testing

**Study design for 510(k):**

| Parameter | Requirement |
|-----------|------------|
| Study type | Multi-site, multi-reader, non-inferiority |
| Sites | Minimum 3 geographically diverse US sites |
| Readers | Minimum 6 board-certified pathologists per site |
| Cases | Minimum 300 surgical pathology cases (stratified by tissue type) |
| Comparator | Conventional light microscopy |
| Primary endpoint | Major diagnostic discordance rate |
| Non-inferiority margin | Delta = 4% (per Philips IntelliSite study design) |
| Secondary endpoints | Minor discordance rate, diagnostic confidence, reading time |

**Study cost estimate:** $200,000-500,000 (varies by scope and number of sites)

### 6.3 Software Validation (IEC 62304)

| Activity | Description | VarunaPoC Status |
|----------|-------------|-----------------|
| Software development plan | Lifecycle model, activities, deliverables | Not formalized per IEC 62304 |
| Software requirements | Functional, performance, interface requirements | Partially documented |
| Software architecture | Module design, interfaces, data flows | Documented (architecture docs) |
| Unit testing | Per-module test coverage >= 80% | 94 tests exist, coverage not measured |
| Integration testing | End-to-end workflow validation | E2E tests exist (Playwright) |
| System testing | Full system validation against requirements | Not formalized |
| Risk analysis | Software-specific risk analysis (IEC 62304 Class B/C) | Not performed |

---

## 7. 510(k) Submission Content Outline

### 7.1 Submission Sections

| Section | Content | VarunaPoC Readiness |
|---------|---------|-------------------|
| **Cover letter** | Submission type, device name, applicant info | Ready (template) |
| **CDRH Premarket Review Submission Cover Sheet (FDA 3514)** | Administrative information | Ready (template) |
| **Indications for Use (FDA 3881)** | Intended use statement | Must draft |
| **510(k) Summary or Statement** | Public summary of SE determination | Must prepare |
| **Truthful and Accuracy Statement** | Signed declaration | Prepared at submission |
| **Class III Certification** | Not applicable (Class II device) | N/A |
| **Financial Certification** | Clinical investigator financial interests | Required if clinical study done |
| **Declarations of Conformity** | Standards compliance (IEC 62304, etc.) | Not ready |
| **Device Description** | Detailed technical description | Architecture docs can be adapted |
| **Substantial Equivalence Comparison** | Comparison to predicate device(s) | Section 5 of this document (draft) |
| **Performance Testing** | Analytical and clinical data | Not yet conducted |
| **Software Documentation** | Per FDA software guidance | Partially ready (needs IEC 62304 alignment) |
| **Cybersecurity Documentation** | Per FDA premarket cybersecurity guidance | Partially ready (SBOM, CI security scans) |
| **Labeling** | Instructions for use, labeling text | Must draft |
| **Biocompatibility** | Not applicable (no body contact) | N/A |
| **Electromagnetic Compatibility** | Not applicable (software only) | N/A |

### 7.2 Estimated Preparation Time

| Section | Effort (Weeks) | Dependencies |
|---------|---------------|-------------|
| Device description and intended use | 2-3 | None |
| SE comparison | 2-3 | Predicate device analysis |
| Software documentation (IEC 62304) | 8-12 | Code review, formal documentation |
| Cybersecurity documentation | 4-6 | Threat modeling, SBOM |
| Analytical testing | 8-12 | Test equipment, datasets |
| Clinical study | 24-36 | IRB approval, site recruitment, case collection |
| Submission assembly and QA | 4-6 | All sections complete |
| **Total** | **52-78 weeks** | (~12-18 months) |

---

## 8. De Novo Pathway Alternative

### 8.1 When De Novo Is Appropriate

The De Novo pathway (21 CFR 860.260) is used when:
- No legally marketed predicate device exists for the intended use
- The device is low-to-moderate risk (Class I or II classification)
- A new product code and classification regulation are needed

### 8.2 Paige Prostate Precedent (DEN200080)

Paige AI's prostate cancer detection software received De Novo authorization in 2021,
establishing a precedent for AI-based pathology tools:

| Attribute | Paige Prostate (DEN200080) | VarunaPoC (Hypothetical De Novo) |
|-----------|--------------------------|--------------------------------|
| Intended use | Identify areas of interest on prostate biopsy slides | Identify areas of interest on pathology slides (multi-tissue) |
| AI function | Highlight regions suspicious for cancer | Heatmap overlay, detection, classification |
| Risk class | Class II (special controls) | Likely Class II |
| Clinical study | Multi-site, multi-reader | Required |
| Special controls | Software validation, clinical performance, labeling | Similar expected |

### 8.3 De Novo vs. 510(k) Comparison

| Factor | 510(k) | De Novo |
|--------|--------|---------|
| Predicate needed | Yes | No |
| Review time (FDA) | 90 days (MDUFA goal) | 150 days (MDUFA goal) |
| User fee (FY2026) | ~$22,000 | ~$130,000 |
| Complexity | Moderate | High |
| Duration (total) | 12-18 months | 18-24 months |
| Total cost | $150,000-350,000 | $300,000-600,000 |
| Advantage | Faster, cheaper, well-understood | Creates new classification; no predicate needed |

### 8.4 Recommendation

**Pursue 510(k) as primary pathway.** The existence of cleared WSI systems (K172655,
K240315) and AI pathology tools (K231495) provides sufficient predicate basis. Reserve
De Novo for features that have no cleared predicate (e.g., novel multi-tissue AI analysis).

---

## 9. Health Canada MDL Requirements

### 9.1 Medical Device Licence (MDL) Overview

Health Canada regulates medical devices under the **Canadian Medical Devices Regulations
(CMDR, SOR/98-282)**. VarunaPoC would require a Medical Device Licence to be marketed
in Canada.

### 9.2 Risk Classification

| Health Canada Class | Risk | Examples | Application Route |
|--------------------|------|---------|------------------|
| Class I | Low | Non-diagnostic viewers | Establishment Licence only |
| **Class II** | Low-moderate | WSI viewer for primary diagnosis | MDL application |
| **Class III** | Moderate-high | AI-assisted diagnostic software | MDL application + more data |
| Class IV | High | Life-sustaining devices | Full MDL with clinical data |

**VarunaPoC classification:**

| VarunaPoC Mode | Health Canada Class | Rationale |
|----------------|-------------------|-----------|
| Viewer only (no diagnostic claim) | Class I | Display tool, no diagnostic intent |
| Viewer for primary diagnosis | Class II | Diagnostic display device |
| AI-assisted analysis | Class II or III | Depends on autonomy level and clinical risk |

### 9.3 CMDR Requirements for Class II/III

| Requirement | Class II | Class III | VarunaPoC Status |
|-------------|---------|-----------|-----------------|
| Quality Management System (ISO 13485) | Required | Required | Not certified |
| Device description | Required | Required | Architecture documented |
| Intended use statement | Required | Required | Must formalize |
| Safety and effectiveness summary | Required | Required | Not prepared |
| Risk management (ISO 14971) | Required | Required | Partially documented |
| Software lifecycle (IEC 62304) | Required | Required | Not formalized |
| Clinical evidence | Summary of literature | Clinical investigation data | Not available |
| Labeling | Canadian requirements (bilingual EN/FR) | Same | Must prepare |
| MDL application fee | CAD 4,590 (Class II) | CAD 11,313 (Class III) | Budget |
| Annual licence fee | CAD 5,345 (Class II) | CAD 7,745 (Class III) | Budget |

### 9.4 MDSAP Alignment

The **Medical Device Single Audit Program (MDSAP)** allows a single audit to satisfy
the quality management system requirements of multiple regulatory authorities:

| MDSAP Participating Authority | Coverage |
|------------------------------|---------|
| FDA (US) | 21 CFR Part 820 (Quality System Regulation) |
| Health Canada | CMDR SOR/98-282 |
| ANVISA (Brazil) | RDC 665/2022 |
| TGA (Australia) | TG Act 1989 |
| MHLW/PMDA (Japan) | MHLW Ministerial Ordinance 169 |

**MDSAP advantage for VarunaPoC:** A single MDSAP-certified audit satisfies both FDA
and Health Canada QMS requirements, reducing duplicate audit costs and timelines.

### 9.5 Health Canada AI/ML Guidance

Health Canada, together with FDA and UK MHRA, has published joint guidance on AI/ML-based
SaMD through the **Good Machine Learning Practice (GMLP)** principles:

| GMLP Principle | Description | VarunaPoC Applicability |
|---------------|-------------|----------------------|
| Multi-disciplinary expertise | Clinical + technical team | Pathologist collaboration in place |
| Good software engineering | Software validation practices | CI/CD in place, IEC 62304 formalization needed |
| Representative data | Training data reflects target population | Must document (when real AI deployed) |
| Independent test sets | Separate validation data | Must implement |
| Reference datasets | Clinically relevant benchmarks | Must identify/create |
| Model design fit for purpose | Architecture appropriate for clinical task | Documented in architecture docs |
| Focus on performance in relevant populations | Sub-group analysis | Must implement |
| Testing demonstrates real-world performance | Clinical validation | Must conduct |
| Security and maintenance | Ongoing monitoring and updates | CI security scanning in place |
| Transparency | Clear communication of limitations | Must formalize |

### 9.6 Clinical Evidence for Health Canada

**Class II (viewer for primary diagnosis):**

A literature review and comparative data may suffice:
- Reference published clinical studies for cleared WSI systems
- Provide bench testing data for display equivalence
- Limited reader study (smaller than FDA requirement) may be accepted

**Class III (AI-assisted):**

Clinical investigation data is typically required:
- Prospective or retrospective study demonstrating clinical performance
- Study population should include Canadian demographic representation
- Health Canada may accept FDA clinical data with Canadian site addendum

---

## 10. Timeline and Cost Estimates

### 10.1 FDA 510(k) Timeline

```
Month 1-3:    Regulatory strategy finalization
              Pre-submission (Q-Sub) meeting with FDA
Month 4-9:    IEC 62304 software documentation
              Analytical testing (display validation)
              Cybersecurity documentation
Month 6-15:   Clinical study (if required)
              Site setup: 2 months
              Case collection: 4-6 months
              Data analysis: 2 months
Month 12-15:  510(k) submission preparation and QA
Month 15-18:  FDA review (90-day MDUFA goal + RFI)
Month 18:     510(k) clearance (if successful)
```

### 10.2 Health Canada MDL Timeline

```
Month 1-3:    Regulatory strategy (parallel with FDA)
              MDSAP audit planning
Month 4-9:    ISO 13485 QMS implementation
              MDSAP audit (covers FDA + HC requirements)
Month 10-12:  MDL application preparation
              Bilingual labeling (EN/FR)
Month 12-15:  MDL submission to Health Canada
Month 15-18:  Health Canada review (target: 60 days Class II)
Month 18:     MDL issuance (if successful)
```

### 10.3 Cost Breakdown

**FDA 510(k):**

| Cost Category | Low Estimate (USD) | High Estimate (USD) |
|--------------|-------------------|-------------------|
| Regulatory consulting | $30,000 | $80,000 |
| Pre-submission meeting (Q-Sub) | $5,000 | $10,000 |
| IEC 62304 documentation | $20,000 | $50,000 |
| Analytical testing | $30,000 | $80,000 |
| Clinical study | $100,000 | $300,000 |
| 510(k) user fee | $22,000 | $22,000 |
| Submission preparation | $20,000 | $40,000 |
| FDA interaction/RFI responses | $10,000 | $30,000 |
| **Total FDA 510(k)** | **$237,000** | **$612,000** |

**Health Canada MDL:**

| Cost Category | Low Estimate (CAD) | High Estimate (CAD) |
|--------------|-------------------|-------------------|
| ISO 13485 implementation | $30,000 | $80,000 |
| MDSAP audit | $15,000 | $30,000 |
| Regulatory consulting | $20,000 | $50,000 |
| Clinical evidence compilation | $10,000 | $50,000 |
| MDL application fee | $4,590 | $11,313 |
| Bilingual labeling | $5,000 | $15,000 |
| **Total Health Canada MDL** | **CAD 84,590** | **CAD 236,313** |

### 10.4 Combined Strategy (MDSAP)

Using MDSAP for a combined FDA + Health Canada strategy saves approximately 20-30% compared
to separate regulatory programs, primarily through:
- Single QMS audit
- Shared clinical evidence package
- Parallel submission preparation

---

## 11. Recommended Strategy

### 11.1 Phased Approach

```
PHASE 0 (Current): FDA Exempt / Research Tool
  - WSI viewer without diagnostic claims
  - AI in mock/research mode only
  - No regulatory submission required
  - Duration: Ongoing

PHASE 1: FDA 510(k) for WSI Viewer (Primary Diagnosis)
  - Submit for QAS classification (viewer only, no AI claims)
  - Predicate: Philips IntelliSite K172655
  - Lower risk, established pathway
  - Duration: 12-18 months
  - Cost: $150,000-250,000

PHASE 2: FDA 510(k) Supplement for AI Features
  - Add AI-assisted analysis (heatmap, detection) to cleared device
  - Predicate: Paige Breast K231495 or Proscia K240414
  - Requires AI-specific performance data
  - Duration: 12-18 months (after Phase 1)
  - Cost: $150,000-350,000

PHASE 3: Health Canada MDL (Parallel with Phase 2)
  - Leverage FDA clinical data for HC submission
  - MDSAP audit covers both jurisdictions
  - Duration: 12-18 months
  - Cost: CAD 85,000-240,000
```

### 11.2 Key Decision Points

| Decision | Trigger | Options |
|----------|---------|---------|
| Proceed beyond Phase 0? | Commercial interest in US market confirmed | Phase 1 vs. remain research-only |
| Include AI in initial 510(k)? | AI validation data available | Phase 1 (viewer only) vs. Phase 1+2 combined |
| De Novo instead of 510(k)? | Novel AI claims without predicate | De Novo ($300-600K) vs. 510(k) ($150-350K) |
| MDSAP for dual market? | Both US and Canada targeted | MDSAP (savings) vs. separate submissions |
| EU IVDR in parallel? | European market expansion | Coordinate with AI Act compliance timeline |

### 11.3 Pre-Submission (Q-Sub) Recommendation

Before investing in a 510(k) submission, request a **Pre-Submission (Q-Sub)** meeting
with FDA to:
1. Confirm product classification and product code
2. Validate predicate device selection
3. Discuss clinical study design and endpoint acceptance
4. Clarify software documentation expectations
5. Understand AI-specific requirements

**Q-Sub timeline:** FDA typically responds within 75 days of submission. Cost is minimal
(no user fee for Q-Sub; consulting fees for preparation ~$5,000-10,000).

---

## 12. Gap Analysis

### 12.1 FDA 510(k) Readiness

| Requirement | Status | Priority | Action Needed |
|-------------|--------|----------|--------------|
| Product classification determined | Done (this document) | N/A | Confirm with FDA via Q-Sub |
| Intended use statement drafted | Not done | High | Draft formal intended use per FDA format |
| Predicate device identified | Done (this document) | N/A | Validate with FDA via Q-Sub |
| IEC 62304 software lifecycle | Not formalized | Critical | Document SDP, SRS, architecture, testing |
| ISO 14971 risk management | Partially documented | High | Complete risk management file |
| ISO 13485 QMS | Not certified | Critical | Implement QMS or engage contract QMS |
| Analytical testing data | Not collected | High | Design and execute display validation |
| Clinical study data | Not available | Critical | Design study, obtain IRB, recruit sites |
| Cybersecurity documentation | Partial (CI scans) | High | SBOM, threat model, security architecture |
| Labeling | Not drafted | Medium | Draft IFU, quick start guide |
| Establishment registration | Not done | Medium | Register with FDA as device establishment |
| US Agent | Not designated | High | Required for non-US manufacturers |

### 12.2 Health Canada MDL Readiness

| Requirement | Status | Priority | Action Needed |
|-------------|--------|----------|--------------|
| ISO 13485 QMS | Not certified | Critical | Same as FDA (MDSAP) |
| CMDR compliance | Not assessed | High | Review CMDR requirements |
| Bilingual labeling (EN/FR) | Partial (docs in French exist) | Medium | Translate to standard Canadian format |
| Canadian clinical data | Not available | Medium | May leverage FDA data |
| MDL application | Not started | Low | After QMS certification |
| Medical Device Establishment Licence (MDEL) | Not obtained | High | Required before MDL |

### 12.3 Critical Path

The **critical path** to FDA 510(k) clearance is:

1. **QMS establishment** (ISO 13485) -- 6-9 months
2. **Clinical study** (if required) -- 8-12 months
3. **Submission preparation and review** -- 6-9 months

Total critical path: **20-30 months** from decision to proceed.

With MDSAP, Health Canada MDL can run in parallel and add only 3-6 months.

---

## 13. References

1. **21 CFR 864.3600** -- Microscopes and accessories.
   https://www.ecfr.gov/current/title-21/chapter-I/subchapter-H/part-864/subpart-D/section-864.3600

2. **21 CFR 864.3700** -- Whole slide imaging system.
   https://www.ecfr.gov/current/title-21/chapter-I/subchapter-H/part-864

3. **FDA 510(k) K172655** -- Philips IntelliSite Pathology Solution.
   https://www.accessdata.fda.gov/cdrh_docs/pdf17/K172655.pdf

4. **FDA 510(k) K240315** -- Leica Aperio GT 450 DX.
   https://www.accessdata.fda.gov/cdrh_docs/pdf24/K240315.pdf

5. **FDA De Novo DEN200080** -- Paige Prostate.
   https://www.accessdata.fda.gov/cdrh_docs/pdf20/DEN200080.pdf

6. **FDA Software as a Medical Device (SaMD) Guidance**.
   https://www.fda.gov/medical-devices/digital-health-center-excellence/software-medical-device-samd

7. **FDA Premarket Cybersecurity Guidance** (2023).
   https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cybersecurity-medical-devices-quality-system-considerations-and-content-premarket-submissions

8. **IEC 62304:2006/AMD1:2015** -- Medical device software lifecycle processes.

9. **ISO 13485:2016** -- Medical devices quality management systems.

10. **ISO 14971:2019** -- Application of risk management to medical devices.

11. **Canadian Medical Devices Regulations (CMDR)** -- SOR/98-282.
    https://laws-lois.justice.gc.ca/eng/regulations/SOR-98-282/

12. **MDSAP** -- Medical Device Single Audit Program.
    https://www.fda.gov/medical-devices/cdrh-international-programs/medical-device-single-audit-program-mdsap

13. **Good Machine Learning Practice (GMLP)** -- FDA, Health Canada, MHRA joint statement.
    https://www.fda.gov/medical-devices/software-medical-device-samd/good-machine-learning-practice-medical-device-development-guiding-principles

14. **VarunaPoC Proposal v2** -- Section 7 (Cadre Reglementaire, FDA precedents).

---

*This document is for regulatory planning purposes only and does not constitute regulatory
advice. Engagement with qualified regulatory affairs consultants and legal counsel is
required before pursuing any regulatory submission. FDA and Health Canada requirements
are subject to change; verify current guidance before acting on this document.*

*Last updated: 2026-02-18*
