# VarunaPoC Claude Code Configuration

This directory contains the **specialized agents and skills** configuration for Claude Code, implementing a professional development workflow where every request is treated as a client demand that goes through:

**Analysis → Design → Planning → Implementation**

---

## CERVEAU D'ORCHESTRATION (NOUVEAU)

**IMPORTANT:** Avant toute action, consulter le **Cerveau d'Orchestration**:

| Document | But | Quand Consulter |
|----------|-----|-----------------|
| **[BRAIN.md](./BRAIN.md)** | Processus obligatoire pour toute demande | TOUJOURS (point d'entree) |
| **[memory/LEARNINGS.md](./memory/LEARNINGS.md)** | Erreurs passees et solutions | Avant d'explorer un probleme |
| **[memory/DECISIONS.md](./memory/DECISIONS.md)** | Decisions architecturales (ADR) | Avant une decision technique |
| **[memory/SOURCES.md](./memory/SOURCES.md)** | References officielles | Pour valider une proposition |
| **[memory/PROJECT_STATE.md](./memory/PROJECT_STATE.md)** | Etat actuel du projet | Debut de session |

### Workflow Obligatoire

```
PROMPT UTILISATEUR
       ↓
[1] Lire PROJECT_STATE.md (contexte actuel)
       ↓
[2] Consulter LEARNINGS.md (eviter erreurs passees)
       ↓
[3] Verifier DECISIONS.md (decisions existantes)
       ↓
[4] Suivre processus BRAIN.md
       ↓
[5] Valider avec orchestration-validator skill
       ↓
[6] DEMANDER VALIDATION ADMIN si modification significative
       ↓
[7] Implementer + Commit + Mettre a jour memory/
```

---

## 📋 Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [The Team](#the-team)
- [Available Agents](#available-agents)
- [Available Skills](#available-skills)
- [Usage Guide](#usage-guide)
- [Creating New Agents/Skills](#creating-new-agentsskills)
- [Best Practices](#best-practices)
- [References](#references)

---

## Overview

### The Professional Approach

Instead of jumping directly to code, this system enforces a **professional software engineering workflow**:

1. **🔍 Analyze** - Understand requirements, clarify ambiguities
2. **🎨 Design** - Choose architecture, technologies, and approach
3. **📝 Plan** - Break down into tasks, assign to specialists
4. **⚙️ Implement** - Delegate to appropriate experts

### The Team Structure

```
┌─────────────────────────────────────────────────────────┐
│              Chief Architect (Orchestrator)              │
│  Analyzes requests, delegates to specialists             │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
    ┌────▼────┐              ┌──────▼──────┐
    │ Agents  │              │   Skills    │
    │ (People)│              │ (Tools)     │
    └────┬────┘              └──────┬──────┘
         │                           │
    ┌────┴─────────────────┐        │
    │                      │        │
    │ Specialized Experts  │   Automated
    │ (Backend, Frontend,  │   Workflows
    │  Performance, etc.)  │   (Documentation,
    └──────────────────────┘    Testing, etc.)
```

---

## How It Works

### Entry Point: Chief Architect

**All requests go through the `chief-architect` agent first.**

```
Your request
    ↓
[chief-architect analyzes]
    ↓
[determines which specialists needed]
    ↓
[delegates to appropriate agents/skills]
    ↓
[monitors progress, coordinates work]
    ↓
Result delivered to you
```

### Automatic Delegation

When you make a request, the chief-architect:

1. **Analyzes** your request (may ask clarifying questions)
2. **Designs** the solution (consults specialists if needed)
3. **Plans** the work (breaks into tasks)
4. **Delegates** to appropriate agents/skills
5. **Monitors** progress (updates you along the way)
6. **Validates** completion (ensures quality)

### Example Flow

**Your request:** "Add a zoom reset button to the viewer"

**Chief Architect's process:**

```
1. ANALYZE
   - Understand: Need UI button to reset zoom to fit-to-screen
   - Scope: Frontend feature, in PoC scope
   - Clarify: Position, icon, keyboard shortcut?

2. DESIGN
   - Component: Frontend only
   - Technology: Vanilla JS + OpenSeadragon API
   - Specialist: frontend-tech-lead

3. PLAN
   Tasks:
   [1] frontend-tech-lead: Implement reset zoom button
   [2] manual-updater: Update user documentation
   [3] Test with all slide formats

4. IMPLEMENT
   - Delegates to frontend-tech-lead
   - Invokes manual-updater skill
   - Validates functionality
   - Delivers result
```

---

## The Team

### Specialized Agents (The Experts)

| Agent | Expertise | When to Use |
|-------|-----------|-------------|
| **chief-architect** | Orchestration, request analysis, delegation | **Default entry point for all requests** |
| **backend-tech-lead** | FastAPI, OpenSlide, tile serving, Python backend | API development, OpenSlide integration, backend features |
| **frontend-tech-lead** | Vite, Vanilla JS, OpenSeadragon, UI/UX | UI development, viewer features, browser optimization |
| **performance-engineer** | Coordinate mapping, caching, profiling, optimization | Performance issues, coordinate validation, memory optimization |
| **ml-architect** | AI/ML, MLOps, annotation quality, explainable AI, federated learning | ML strategy, model architecture, annotation platforms, continuous learning |
| **infrastructure-architect** | Cloud/on-premise, Kubernetes, CI/CD, monitoring, scalability | Deployment strategy, infrastructure design, DevOps automation |
| **lead-architecte** | System architecture, design patterns, medical standards | Architectural decisions, technology choices, system design |
| **security-architect** | HIPAA/GDPR, authentication, encryption, threat modeling | Security reviews, compliance, authentication implementation |
| **integration-engineer** | DICOM, PACS, HL7, vendor interoperability | PACS integration, DICOM questions, vendor format handling |

### Skills (Automated Workflows)

| Skill | Purpose | Invoked By |
|-------|---------|------------|
| **orchestration-validator** | **NOUVEAU:** Valider et challenger propositions avant implementation | chief-architect, tout agent |
| **error-documenter** | Document non-trivial errors following protocol | Any agent encountering complex errors |
| **manual-updater** | Update user documentation when features complete | frontend-tech-lead, chief-architect |
| **api-documenter** | Document FastAPI endpoints with comprehensive docstrings | backend-tech-lead |
| **slide-tester** | Test features across all 10 slide formats (94 lames) | performance-engineer, backend-tech-lead |
| **coordinate-validator** | Validate OSD↔OpenSlide coordinate mapping accuracy | performance-engineer, frontend-tech-lead |

---

## Available Agents

### 🎯 chief-architect

**Role:** Project orchestrator and primary interface

**Responsibilities:**
- Analyze all incoming requests
- Delegate to appropriate specialists
- Coordinate between agents
- Manage workflow (analyze → design → plan → implement)
- Create new agents/skills when needed

**Tools:** Task, Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion, TodoWrite

**File:** `.claude/agents/chief-architect.md`

---

### 🔧 backend-tech-lead

**Role:** Backend development expert

**Expertise:**
- FastAPI application architecture
- OpenSlide Python library integration
- Tile serving and coordinate mapping
- Medical imaging standards (DICOM)
- Performance optimization for gigapixel images

**Skills:** error-documenter, api-documenter

**Key Resources:**
- OpenSlide API: https://openslide.org/api/python/
- FastAPI: https://fastapi.tiangolo.com/
- DICOM Standard: https://www.dicomstandard.org/

**File:** `.claude/agents/backend-tech-lead.md`

---

### 🎨 frontend-tech-lead

**Role:** Frontend development expert

**Expertise:**
- Vite development environment
- Vanilla JavaScript (no heavy frameworks)
- OpenSeadragon integration for gigapixel navigation
- UI/UX for medical imaging viewers
- Coordinate mapping (OSD ↔ Backend API)

**Skills:** manual-updater, coordinate-validator

**Key Resources:**
- OpenSeadragon: https://openseadragon.github.io/
- Vite: https://vitejs.dev/
- MDN Web Docs: https://developer.mozilla.org/

**File:** `.claude/agents/frontend-tech-lead.md`

---

### ⚡ performance-engineer

**Role:** Performance and accuracy expert

**Expertise:**
- Coordinate mapping validation (OpenSeadragon ↔ OpenSlide)
- Tile streaming optimization
- Memory management for gigapixel data
- Frame rate optimization (60fps target)
- Performance profiling and bottleneck identification

**Skills:** coordinate-validator, slide-tester

**Key Resources:**
- Chrome DevTools: https://developer.chrome.com/docs/devtools/
- OpenSeadragon Coordinates: https://openseadragon.github.io/examples/viewport-coordinates/

**File:** `.claude/agents/performance-engineer.md`

---

### 🤖 ml-architect

**Role:** AI/ML and MLOps expert

**Expertise:**
- ML/AI strategy for whole slide imaging (WSI)
- Annotation quality management (inter-annotator agreement, outlier detection)
- MLOps & Continuous Learning (drift detection, feedback loops)
- Explainable AI (confidence mapping, uncertainty quantification)
- Federated Learning (privacy-preserving distributed training)
- Medical imaging AI (tumor detection, segmentation, classification)

**Key Resources:**
- PyTorch: https://pytorch.org/
- TensorFlow: https://www.tensorflow.org/
- MLflow (MLOps): https://mlflow.org/
- Flower (Federated Learning): https://flower.dev/
- Scikit-learn: https://scikit-learn.org/
- CLAM (WSI Analysis): https://github.com/mahmoodlab/CLAM

**File:** `.claude/agents/ml-architect.md`

---

### ☁️ infrastructure-architect

**Role:** Infrastructure and deployment expert

**Expertise:**
- Cloud & On-Premise architecture (AWS, Azure, GCP)
- Containerization & Orchestration (Docker, Kubernetes, Helm)
- CI/CD pipelines (GitHub Actions, GitLab CI)
- Scalability & High Availability (load balancing, auto-scaling)
- Monitoring & Observability (Prometheus, Grafana, ELK)
- Zero-config deployment (Infrastructure as Code)

**Key Resources:**
- Kubernetes: https://kubernetes.io/docs/
- Docker: https://docs.docker.com/
- Terraform: https://www.terraform.io/docs/
- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/
- Helm: https://helm.sh/docs/

**File:** `.claude/agents/infrastructure-architect.md`

---

### 🏛️ lead-architecte

**Role:** System architecture strategist

**Expertise:**
- Overall system architecture
- Medical imaging standards (DICOM, vendor-neutral)
- Design patterns and best practices
- Long-term technical strategy
- Cross-component coordination

**Key Resources:**
- DICOM Standard: https://www.dicomstandard.org/
- Martin Fowler's Architecture: https://martinfowler.com/architecture/

**File:** `.claude/agents/lead-architecte.md`

---

### 🔒 security-architect

**Role:** Security and compliance expert

**Expertise:**
- HIPAA/GDPR compliance for medical data
- Authentication & authorization (OAuth2, JWT)
- Encryption (TLS, data at rest)
- Threat modeling (STRIDE framework)
- Security auditing and penetration testing

**Key Resources:**
- HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- NIST Cybersecurity: https://www.nist.gov/cyberframework

**File:** `.claude/agents/security-architect.md`

---

### 🔌 integration-engineer

**Role:** Healthcare IT integration expert

**Expertise:**
- DICOM protocols (query/retrieve, storage)
- PACS integration (Orthanc, DCM4CHEE)
- HL7 messaging (patient demographics, orders)
- Vendor interoperability (3DHistech, Roche, Philips, etc.)
- Medical imaging workflows

**Key Resources:**
- DICOM Standard: https://www.dicomstandard.org/
- Orthanc PACS: https://www.orthanc-server.com/
- HL7 Standard: https://www.hl7.org/

**File:** `.claude/agents/integration-engineer.md`

---

## Available Skills

### 🧠 orchestration-validator (NOUVEAU)

**Purpose:** Valider et challenger toute proposition avant implementation

**When invoked:**
- Avant modification de code significative
- Avant decisions architecturales
- Quand plusieurs approches sont possibles
- Pour valider une proposition d'agent

**Process:**
1. Scoring (7 criteres: pertinence, simplicite, coherence, maintenabilite, performance, securite, testabilite)
2. Questions de challenge systematiques
3. Verification des sources officielles
4. Decision: APPROUVER / REJETER / MODIFIER

**Output:**
- Grille de scoring detaillee
- Sources consultees
- Decision avec justification
- Actions requises si applicable

**File:** `.claude/skills/orchestration-validator/SKILL.md`

---

### 📝 error-documenter

**Purpose:** Automatically document non-trivial errors

**When invoked:**
- Error persists after initial debugging
- Requires workaround (not straightforward fix)
- Related to external library limitation
- Could recur with other files/scenarios

**Output:**
- Creates `/docs/ERROR_[NAME].md` with full analysis
- Updates `/docs/README.md` index
- Provides code comment template

**File:** `.claude/skills/error-documenter/SKILL.md`

---

### 📚 manual-updater

**Purpose:** Update user documentation in `/docs/Manuel/`

**When invoked:**
- Feature is validated and tested
- UI is finalized (no placeholders)
- Complete user workflow implemented

**Output:**
- Creates/updates `/docs/Manuel/[NN]-[FEATURE].md`
- Updates `/docs/Manuel/README.md` index
- User-friendly language (no technical jargon)

**File:** `.claude/skills/manual-updater/SKILL.md`

---

### 📖 api-documenter

**Purpose:** Document FastAPI endpoints comprehensively

**When invoked:**
- Creating new API endpoint
- Modifying existing endpoint
- Changing response structure

**Output:**
- Complete docstring with Args, Returns, Raises
- FastAPI tags assignment
- Parameter documentation with Query()/Path()
- Swagger UI integration

**File:** `.claude/skills/api-documenter/SKILL.md`

---

### 🧪 slide-tester

**Purpose:** Test features across all slide formats

**When invoked:**
- Implementing new slide handling feature
- Modifying OpenSlide integration
- Before major releases (regression testing)

**Output:**
- Test report with pass/fail status
- Format-specific issues identified
- Performance metrics (tile load times)

**File:** `.claude/skills/slide-tester/SKILL.md`

---

### 📐 coordinate-validator

**Purpose:** Validate coordinate mapping accuracy

**When invoked:**
- After coordinate mapping changes
- When tiles appear misaligned
- When zoom levels seem incorrect
- Before major releases

**Output:**
- Validation report (pixel-perfect accuracy)
- Test results for all zoom levels
- Bidirectional conversion tests

**File:** `.claude/skills/coordinate-validator/SKILL.md`

---

## Usage Guide

### For Users: How to Make Requests

**Simply make your request naturally.** The chief-architect will handle everything.

#### Example 1: Feature Request

**You:** "I want to add a mini-map to the viewer that shows where I am in the slide"

**Chief Architect will:**
1. Analyze your request (may ask for clarification)
2. Design the solution (OpenSeadragon navigator feature)
3. Plan the tasks (frontend implementation, testing, documentation)
4. Delegate to frontend-tech-lead
5. Invoke manual-updater skill when complete
6. Deliver result to you

#### Example 2: Bug Report

**You:** "Tiles are loading very slowly, can we optimize?"

**Chief Architect will:**
1. Analyze the issue (profiling needed)
2. Consult performance-engineer
3. Run slide-tester to identify bottlenecks
4. Implement optimizations
5. Validate performance improvements
6. Document any changes

#### Example 3: Question

**You:** "How do we ensure HIPAA compliance for patient data?"

**Chief Architect will:**
1. Delegate to security-architect
2. Get comprehensive answer with references
3. May suggest implementation steps if needed

### For Developers: Understanding the System

#### Invoking Agents Programmatically

If you're working with Claude Code's Task tool:

```python
# Invoke specific agent
Task(
    subagent_type="backend-tech-lead",
    description="Implement tile caching",
    prompt="Add Redis-based tile caching to the backend..."
)
```

#### Invoking Skills

Skills are invoked by agents automatically, but you can mention them:

**You:** "Use the error-documenter skill to document the BIF direction issue"

#### Creating Custom Workflows

You can create custom multi-agent workflows by requesting them:

**You:** "For this feature, I want backend-tech-lead and frontend-tech-lead to work together, coordinated by performance-engineer for optimization"

---

## Creating New Agents/Skills

### When to Create New Agent

Create a new agent when:
- ✅ Recurring need for specific expertise
- ✅ Complex domain requiring deep knowledge
- ✅ Multiple related tasks in that domain
- ✅ Permanent addition to team makes sense

**Example:** If adding ML features, create `ml-engineer.md`

### When to Create New Skill

Create a new skill when:
- ✅ Repeatable workflow
- ✅ Clear input/output process
- ✅ Can be invoked by multiple agents
- ✅ Automates manual process

**Example:** If frequently converting formats, create `format-converter` skill

### How to Create New Agent

1. **Copy existing agent** as template (e.g., `backend-tech-lead.md`)
2. **Define expertise domain** clearly
3. **Specify when to use** this agent
4. **List required tools** (Read, Write, Bash, etc.)
5. **Document responsibilities** with examples
6. **Add official resource links**
7. **Save to:** `.claude/agents/[agent-name].md`

### How to Create New Skill

1. **Copy existing skill** as template (e.g., `error-documenter/SKILL.md`)
2. **Define purpose** (one clear task)
3. **Specify invocation criteria**
4. **List allowed tools**
5. **Document workflow** step-by-step
6. **Provide templates** and examples
7. **Save to:** `.claude/skills/[skill-name]/SKILL.md`

### Registering New Team Members

**Tell the chief-architect:**

"I've created a new agent/skill called [name] for [purpose]. Please integrate it into your delegation workflow."

The chief-architect will:
- Review the new specialist
- Update internal delegation logic
- Start using it for appropriate requests

---

## Best Practices

### For Making Requests

✅ **DO:**
- Be clear about what you want to achieve
- Provide context (which files, what use case)
- Mention constraints (performance, security, etc.)
- Ask questions if unsure

❌ **DON'T:**
- Assume technical implementation details
- Skip providing context
- Request features outside PoC scope without discussion

### For Working with Agents

✅ **DO:**
- Let chief-architect orchestrate
- Trust specialist expertise
- Provide feedback on results
- Ask for clarification if needed

❌ **DON'T:**
- Micromanage implementation
- Jump directly to code without analysis
- Ignore scope boundaries
- Override security recommendations

### For Documentation

✅ **DO:**
- Follow CLAUDE.md protocols
- Update documentation when features complete
- Document errors systematically
- Use user-friendly language in manuals

❌ **DON'T:**
- Leave code undocumented
- Skip error documentation
- Use technical jargon in user manuals
- Forget to update API documentation

### For Testing

✅ **DO:**
- Test with all 10 supported formats (SVS, NDPI, MRXS, SCN, BIF, TIFF, CZI, DICOM, Sakura, Trestle)
- Validate coordinate accuracy
- Check performance targets (60fps, < 100ms tiles)
- Run regression tests before releases

❌ **DON'T:**
- Test with only one format
- Skip coordinate validation
- Ignore performance metrics
- Deploy without testing

---

## Directory Structure

```
.claude/
├── BRAIN.md                           ← CERVEAU: Processus obligatoire (LIRE EN PREMIER)
├── README.md                          ← This file
│
├── memory/                            ← MEMOIRE PERSISTANTE
│   ├── LEARNINGS.md                   ← Erreurs passees et solutions
│   ├── DECISIONS.md                   ← Architecture Decision Records (ADR)
│   ├── SOURCES.md                     ← References officielles validees
│   └── PROJECT_STATE.md               ← Etat actuel du projet (snapshot)
│
├── agents/                            ← Specialized agents
│   ├── chief-architect.md             ← Orchestrator (entry point)
│   ├── backend-tech-lead.md           ← Backend expert
│   ├── frontend-tech-lead.md          ← Frontend expert
│   ├── performance-engineer.md        ← Performance expert
│   ├── ml-architect.md                ← ML/MLOps expert
│   ├── infrastructure-architect.md    ← DevOps/Cloud expert
│   ├── lead-architecte.md             ← Architecture strategist
│   ├── security-architect.md          ← Security expert
│   └── integration-engineer.md        ← PACS/DICOM expert
│
├── skills/                            ← Automated workflows
│   ├── orchestration-validator/       ← NOUVEAU: Validation des propositions
│   │   └── SKILL.md
│   ├── error-documenter/              ← Error documentation
│   │   └── SKILL.md
│   ├── manual-updater/                ← User manual updates
│   │   └── SKILL.md
│   ├── api-documenter/                ← API documentation
│   │   └── SKILL.md
│   ├── slide-tester/                  ← Multi-format testing
│   │   └── SKILL.md
│   └── coordinate-validator/          ← Coordinate accuracy
│       └── SKILL.md
│
└── docs/                              ← Documentation technique
    ├── CONTEXT.md                     ← Contexte rapide V3
    ├── ARCHITECTURE.md                ← Architecture systeme
    ├── FILES.md                       ← Reference fichiers
    └── PATTERNS.md                    ← Design patterns
```

---

## References

### Project Documentation

- **CLAUDE.md** - Master guidelines and protocols (mandatory reading)
- **/docs/README.md** - Error tracking index
- **/docs/ERROR_*.md** - Documented errors and workarounds
- **/docs/Manuel/** - User documentation
- **backend/README.md** - Backend-specific documentation
- **frontend/README.md** - Frontend-specific documentation

### Claude Code Documentation

- **Official Docs:** https://code.claude.com/docs/
- **Agents (Subagents):** https://code.claude.com/docs/en/subagents
- **Skills:** https://code.claude.com/docs/en/skills
- **Task Tool:** For agent delegation

### Key Technologies

- **OpenSlide:** https://openslide.org/ (whole slide imaging library)
- **OpenSeadragon:** https://openseadragon.github.io/ (viewer library)
- **FastAPI:** https://fastapi.tiangolo.com/ (backend framework)
- **Vite:** https://vitejs.dev/ (frontend build tool)
- **DICOM Standard:** https://www.dicomstandard.org/ (medical imaging protocol)

---

## Philosophy

> **"Every request is a client demand. Analyze before designing. Design before planning. Plan before implementing."**

This system embodies professional software engineering practices:

- **Thoughtful analysis** prevents wasted effort
- **Clear design** prevents architectural mistakes
- **Detailed planning** prevents coordination issues
- **Expert delegation** ensures quality implementation

The team of specialists ensures that every aspect of the system—from backend APIs to frontend UX to security to documentation—is handled by experts with deep domain knowledge and access to official resources.

---

## Documentation Technique (Post-Refactoring 2025-12-30)

Pour la documentation de l'architecture refactorée (multi-viewer), voir:

| Document | Description |
|----------|-------------|
| [**docs/CONTEXT.md**](./docs/CONTEXT.md) | **Reprendre le travail rapidement** |
| [**docs/ARCHITECTURE.md**](./docs/ARCHITECTURE.md) | Architecture système détaillée |
| [**docs/FILES.md**](./docs/FILES.md) | Référence rapide des fichiers |
| [**docs/PATTERNS.md**](./docs/PATTERNS.md) | Design patterns implémentés |

### Résumé Architecture Multi-Viewer

```
main.js → CompareLayout → ViewerPanel[] → ViewerInstance → OpenSeadragon
               │
               └── SyncControls → SyncController → EventBus
```

**Patterns:** Singleton (EventBus, ViewerManager), Factory (ViewerFactory), Observer (EventBus), Mediator (SyncController), State (ViewerState)

---

## Quick Start

**As a user, you only need to know one thing:**

**Make your request naturally.** The chief-architect and the team will handle everything.

**Example:**

```
You: "I need to display slide metadata (dimensions, format, vendor)
     next to the viewer"

Chief Architect: [Analyzes request]
Chief Architect: [Designs solution]
Chief Architect: [Plans tasks]
Chief Architect: [Delegates to backend-tech-lead and frontend-tech-lead]
Chief Architect: [Coordinates implementation]
Chief Architect: [Validates completion]
Chief Architect: "Done! Metadata is now displayed. I've updated the
                  user manual and API documentation."
```

**That's it.** Professional workflow, expert implementation, comprehensive documentation—all automatic.

---

**Version:** 2.0
**Last Updated:** 2026-02-08
**Project Version:** 1.7.0 (Phase 2 complete)
**Maintained by:** Chief Architect + Specialist Team
