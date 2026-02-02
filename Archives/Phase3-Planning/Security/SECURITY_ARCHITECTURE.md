# SECURITY_ARCHITECTURE.md

**VarunaPoC Security Architecture & Compliance Framework**

**Document Version:** 1.0
**Date:** 2025-12-31
**Status:** Security Architecture Proposal for MLOps-Ready Platform
**Author:** Security Architect Agent (Bruce Schneier + Eugene Spafford personas)
**Context:** TFE CHU UCL Namur - Transition PoC vers Plateforme MLOps Anatomie Pathologique

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Regulatory Compliance Overview](#2-regulatory-compliance-overview)
3. [Current Security Analysis (Phase 1 PoC)](#3-current-security-analysis-phase-1-poc)
4. [Threat Model](#4-threat-model)
5. [Proposed Security Architecture](#5-proposed-security-architecture)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [Data Protection & Encryption](#7-data-protection--encryption)
8. [Audit Trail & Monitoring](#8-audit-trail--monitoring)
9. [MLOps Security Considerations](#9-mlops-security-considerations)
10. [PACS Integration Security](#10-pacs-integration-security)
11. [Implementation Roadmap](#11-implementation-roadmap)
12. [Security Testing & Validation](#12-security-testing--validation)
13. [References & Standards](#13-references--standards)

---

## 1. Executive Summary

### Current State (Phase 1 PoC)
VarunaPoC est une visionneuse web de lames histologiques haute résolution développée pour le CHU UCL Namur. Actuellement en phase PoC (Proof of Concept), le système présente des **vulnérabilités critiques** qui DOIVENT être corrigées avant toute mise en production.

### Future State (MLOps-Ready Platform)
L'évolution vers une plateforme MLOps pour anatomie pathologique introduit des exigences réglementaires strictes (RGPD, MDR 2017/745, AI Act 2024/1689) et nécessite une refonte complète de l'architecture de sécurité selon le principe **"Security by Design"**.

### Key Findings

**VULNERABILITIES CRITIQUES IDENTIFIÉES:**

1. **AUCUNE AUTHENTIFICATION** - L'API backend est TOTALEMENT OUVERTE
2. **AUCUNE AUTORISATION** - Pas de contrôle d'accès par rôle (RBAC)
3. **AUCUN CHIFFREMENT** - HTTP en clair (pas de TLS)
4. **AUCUN AUDIT TRAIL** - Pas de journalisation des accès PHI
5. **AUCUNE VALIDATION D'ENTRÉE** - Vulnérable aux injections
6. **SECRETS EN CLAIR** - Fichiers .env commités (risque élevé)
7. **CORS TROP PERMISSIF** - Accepte localhost sans restriction IP
8. **DÉPENDANCES OBSOLÈTES** - Versions non patchées (CVE potentiels)

**COMPLIANCE STATUS:**

| Réglementation | Statut Actuel | Exigences Manquantes |
|----------------|---------------|----------------------|
| **RGPD** | NON CONFORME | Pseudonymisation, AIPD, consentement, audit trail, droit à l'oubli |
| **HIPAA** | NON APPLICABLE (UE) | Équivalent RGPD requis |
| **MDR 2017/745** | NON CONFORME | Classification dispositif, audit trail, gestion risques |
| **AI Act 2024/1689** | NON APPLICABLE (PoC) | Requis si IA médicale ajoutée (système haut risque) |
| **ISO 15189** | NON CONFORME | Traçabilité, accréditation, contrôle qualité |

### Risk Assessment

**IMPACT:** CRITIQUE
**PROBABILITÉ:** TRÈS ÉLEVÉE (système ouvert sans authentification)
**RISQUE GLOBAL:** **INACCEPTABLE POUR PRODUCTION**

---

## 2. Regulatory Compliance Overview

### 2.1 RGPD (Règlement Général sur la Protection des Données)

**Applicabilité:** OBLIGATOIRE (données de santé = catégorie spéciale Article 9)

**Exigences clés pour VarunaPoC:**

1. **Base légale (Art. 6 & 9):**
   - Consentement explicite du patient OU
   - Intérêt légitime (recherche médicale, soins) avec AIPD obligatoire

2. **Pseudonymisation (Art. 32):**
   - Séparation identité patient ↔ données cliniques
   - Hash cryptographique (SHA-256 minimum) pour identifiants
   - Stockage mapping dans base sécurisée séparée

3. **Sécurité technique (Art. 32):**
   - Chiffrement at rest (AES-256)
   - Chiffrement in transit (TLS 1.3)
   - Contrôle d'accès strict (RBAC)
   - Journalisation complète (qui, quoi, quand)

4. **Droits des personnes:**
   - **Droit d'accès** (Art. 15) - Patient peut demander ses données
   - **Droit de rectification** (Art. 16) - Correction erreurs
   - **Droit à l'effacement** (Art. 17) - "Droit à l'oubli" (30 jours max)
   - **Droit à la portabilité** (Art. 20) - Export format structuré

5. **Analyse d'Impact (AIPD - Art. 35):**
   - OBLIGATOIRE pour traitement à grande échelle de données de santé
   - Évaluation risques avant mise en production
   - Voir: https://www.cnil.fr/fr/AIPD

6. **Notification violation (Art. 33-34):**
   - CNIL sous 72h en cas de breach
   - Patients concernés si risque élevé

**Sanctions:** Jusqu'à 20M€ ou 4% CA mondial (le plus élevé)

---

### 2.2 MDR 2017/745 (Medical Device Regulation)

**Applicabilité:** Dépend de la classification du dispositif

**Classification VarunaPoC:**

| Fonctionnalité | Classe MDR | Justification |
|----------------|------------|---------------|
| **Visionneuse simple** (affichage WSI) | **Classe I** | Pas de fonction diagnostique active |
| **Avec IA diagnostique** (détection, classification) | **Classe IIa/IIb** | Support décision médicale |
| **Avec IA automatique** (diagnostic sans validation humaine) | **Classe III** | Décision médicale critique |

**Pour Classe I (visionneuse actuelle):**
- Auto-certification suffisante
- Déclaration de conformité UE
- Marquage CE obligatoire
- Audit trail recommandé (pas obligatoire)

**Pour Classe IIa/IIb (avec IA):**
- Organisme notifié requis
- Audit trail OBLIGATOIRE
- Gestion des risques (ISO 14971)
- Documentation technique complète
- Post-market surveillance

**Exigences techniques (Annexe I):**

1. **Sécurité et performance (§1-8):**
   - Minimiser risques pour patient
   - Conception robuste (fail-safe)
   - Validation clinique si IA

2. **Cybersécurité (§17.2):**
   - Protection contre accès non autorisé
   - Chiffrement des données sensibles
   - Authentification forte

3. **Traçabilité (§23):**
   - UDI (Unique Device Identifier)
   - Journalisation complète des opérations
   - Historique des versions

**Ressources:**
- Texte MDR: https://eur-lex.europa.eu/eli/reg/2017/745/oj
- Guide MDCG: https://health.ec.europa.eu/medical-devices-sector/guidance-documents_en

---

### 2.3 AI Act 2024/1689

**Applicabilité:** Si IA pour diagnostic médical → **Système à Haut Risque** (Annexe III, §5)

**Exigences pour systèmes IA haut risque:**

1. **Gestion des risques (Art. 9):**
   - Identification risques (biais, erreurs, adversarial attacks)
   - Mesures d'atténuation
   - Testing continu

2. **Qualité des données (Art. 10):**
   - Datasets représentatifs (pas de biais)
   - Traçabilité provenance données
   - Anonymisation/pseudonymisation

3. **Documentation technique (Art. 11):**
   - Architecture modèle IA
   - Données d'entraînement (métadonnées)
   - Performances (métriques validées cliniquement)

4. **Transparence (Art. 13):**
   - Instructions d'utilisation claires
   - Limitations connues
   - Niveau de précision attendu

5. **Surveillance humaine (Art. 14):**
   - Pathologiste DOIT valider diagnostic IA
   - Interface permettant override

6. **Robustesse & Cybersécurité (Art. 15):**
   - Résistance attaques adversariales
   - Tests de sécurité réguliers
   - Protection contre data poisoning

**Sanctions:** Jusqu'à 35M€ ou 7% CA mondial

**Ressources:**
- AI Act: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206
- Guidelines MDCG: https://health.ec.europa.eu/md_topics/md_sector/ai_en

---

### 2.4 ISO 15189 (Accréditation Laboratoires)

**Applicabilité:** CHU UCL = laboratoire médical accrédité

**Exigences pertinentes pour VarunaPoC:**

1. **Traçabilité (§5.10):**
   - Enregistrement complet des examens
   - Identification unique échantillons
   - Lien patient-échantillon-résultat sécurisé

2. **Gestion informatique (§5.11):**
   - Validation logiciel médical
   - Contrôle accès (rôles définis)
   - Sauvegardes régulières
   - Audit trail (qui a fait quoi, quand)

3. **Confidentialité (§4.2):**
   - Accès limité au personnel autorisé
   - Protection données patient

4. **Contrôle qualité (§5.6):**
   - Tests de validation (précision IA)
   - Surveillance continue performances

**Ressources:**
- ISO 15189:2022: https://www.iso.org/standard/76677.html

---

## 3. Current Security Analysis (Phase 1 PoC)

### 3.1 OWASP Top 10 Vulnerability Assessment

Analyse du code actuel selon **OWASP Top 10 2021** (https://owasp.org/Top10/):

#### A01:2021 – Broken Access Control

**STATUS: CRITIQUE - TOTALEMENT VULNÉRABLE**

**Findings:**

1. **AUCUNE AUTHENTIFICATION:**
```python
# backend/main.py - LIGNE 114-145
@app.get("/", tags=["health"])
async def root():
    return {...}  # ACCESSIBLE SANS AUTH

@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "healthy"}  # ACCESSIBLE SANS AUTH
```

2. **AUCUNE AUTORISATION (RBAC):**
```python
# backend/routes/slides.py - LIGNE 23-49
@router.get("/", tags=["navigation"])
async def list_slides():
    # AUCUN contrôle: n'importe qui peut lister TOUTES les lames
    slides = scan_slides_directory()
    return {"count": len(slides), "slides": slides}

@router.get("/{slide_id}/info", tags=["visualization"])
async def get_slide_info(slide_id: str):
    # AUCUN contrôle: n'importe qui peut accéder à N'IMPORTE QUELLE lame
    slide_path = get_slide_path_by_id(slide_id)
    # ... pas de vérification user.can_access_slide(slide_id)
```

3. **Path Traversal Partiel (mitigé mais incomplet):**
```python
# backend/services/folder_browser.py - LIGNE 55-86
def is_safe_path(requested_path: str) -> bool:
    # GOOD: Vérifie path traversal
    full_path = (SLIDES_ROOT / normalized_path.lstrip("/")).resolve()
    return full_path.is_relative_to(SLIDES_ROOT.resolve())

# MAIS: Pas de vérification que l'utilisateur a LE DROIT d'accéder à ce dossier
# Un utilisateur lambda peut naviguer dans TOUT /Slides
```

**IMPACT:** Un attaquant peut:
- Lister TOUTES les lames du système
- Télécharger N'IMPORTE QUELLE lame (données patient)
- Naviguer dans TOUTE l'arborescence /Slides
- Accéder aux métadonnées (vendor, dimensions) sans restriction

**REMEDIATION (Phase 2+):**
```python
# Exemple avec RBAC
from fastapi import Depends, HTTPException
from auth import get_current_user, Role

@router.get("/{slide_id}/info", tags=["visualization"])
async def get_slide_info(
    slide_id: str,
    current_user: User = Depends(get_current_user)  # REQUIS
):
    # Vérifier permission
    if not current_user.can_access_slide(slide_id):
        raise HTTPException(403, "Access denied")

    slide_path = get_slide_path_by_id(slide_id)
    # ... continue
```

---

#### A02:2021 – Cryptographic Failures

**STATUS: CRITIQUE - AUCUN CHIFFREMENT**

**Findings:**

1. **HTTP en clair (pas de TLS):**
```python
# backend/main.py - LIGNE 84-104
# CORS configuration
allow_origins = [
    "http://localhost:5173",  # HTTP (pas HTTPS)
    "http://localhost:8080",  # HTTP (pas HTTPS)
]
# Données patient transitent EN CLAIR sur le réseau
```

2. **Aucun chiffrement at rest:**
```bash
# /Slides/ contient des fichiers WSI avec métadonnées patient
# Stockés EN CLAIR sur disque (pas de LUKS, VeraCrypt, etc.)
```

3. **Secrets potentiellement exposés:**
```bash
# .gitignore - LIGNE 42
.env  # Ignoré MAIS...

# Fichiers .env.example, .env.phase1, etc. COMMITÉS dans le repo
# Risque: credentials de test peuvent fuiter si réutilisés en prod
```

**IMPACT:**
- **Man-in-the-Middle** (MITM) possible → interception données patient
- **Vol de disque/backup** → données patient lisibles
- **Secrets exposés** → accès non autorisé si réutilisés

**REMEDIATION:**
```nginx
# Phase 2: TLS 1.3 obligatoire
server {
    listen 443 ssl http2;
    ssl_protocols TLSv1.3;
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';

    ssl_certificate /etc/ssl/certs/varuna.crt;
    ssl_certificate_key /etc/ssl/private/varuna.key;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}
```

```bash
# Phase 3: Chiffrement at rest avec LUKS
cryptsetup luksFormat /dev/sdb1
cryptsetup luksOpen /dev/sdb1 slides_encrypted
mount /dev/mapper/slides_encrypted /Slides
```

---

#### A03:2021 – Injection

**STATUS: MOYEN - Path Traversal Mitigé, SQL Injection N/A**

**Findings:**

1. **Path Traversal Prevention (GOOD):**
```python
# backend/services/folder_browser.py - LIGNE 55-86
def is_safe_path(requested_path: str) -> bool:
    # GOOD: Normalisation et vérification
    full_path = (SLIDES_ROOT / normalized_path.lstrip("/")).resolve()
    return full_path.is_relative_to(SLIDES_ROOT.resolve())
```

2. **Pas de SQL (N/A):**
   - Pas de base de données actuellement
   - Pas de requêtes SQL → Pas de risque SQLi direct

3. **MAIS: Pas de validation d'entrée stricte:**
```python
# backend/routes/slides.py - LIGNE 230-275
@router.get("/{slide_id}/tiles/{level}/{col}_{row}.jpg")
async def get_tile(slide_id: str, level: int, col: int, row: int):
    # MANQUE: Validation explicite des paramètres
    # - slide_id format (MD5 hash 12 chars hex?)
    # - level range (0 <= level < max_level?)
    # - col/row range (>= 0?)

    # Confiance implicite dans FastAPI type coercion
    slide_path = get_slide_path_by_id(slide_id)
    tile_bytes = tile_server.get_tile(slide_path, level, col, row, tile_size=256)
```

**IMPACT:** Risque moyen (erreurs possibles, pas de failles critiques)

**REMEDIATION:**
```python
from pydantic import BaseModel, Field, validator

class TileRequest(BaseModel):
    slide_id: str = Field(..., regex=r'^[a-f0-9]{12}$')  # MD5 hash
    level: int = Field(..., ge=0, le=20)  # 0-20
    col: int = Field(..., ge=0)
    row: int = Field(..., ge=0)

    @validator('level')
    def validate_level(cls, v, values):
        # Vérifier niveau existe pour cette slide
        # (nécessite accès métadonnées)
        return v
```

---

#### A04:2021 – Insecure Design

**STATUS: CRITIQUE - Pas de Security by Design**

**Findings:**

1. **Pas de threat modeling:**
   - Aucune analyse STRIDE documentée
   - Pas d'évaluation attack surface
   - Pas d'AIPD (RGPD Art. 35)

2. **Principe de moindre privilège non appliqué:**
   - Tous les utilisateurs (si auth existait) auraient mêmes droits
   - Pas de séparation rôles (admin/clinicien/chercheur)

3. **Pas de fail-safe:**
   - Si erreur OpenSlide → 500 générique (fuite info?)
   - Pas de rate limiting → DoS facile
   - Pas de circuit breaker → cascading failures

4. **Logging insuffisant:**
```python
# backend/main.py - Pas d'audit trail HIPAA-compliant
# Manque:
# - Qui a accédé à quelle lame?
# - Quand?
# - Depuis quelle IP?
# - Quelle action (view/download/delete)?
```

**IMPACT:** Architecture non sécurisable sans refonte partielle

**REMEDIATION:** Voir Section 5 (Proposed Security Architecture)

---

#### A05:2021 – Security Misconfiguration

**STATUS: ÉLEVÉ - Multiples Erreurs de Configuration**

**Findings:**

1. **CORS trop permissif:**
```python
# backend/main.py - LIGNE 98-104
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,  # OK: liste restrictive
    allow_credentials=True,  # OK
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # MAUVAIS
    allow_headers=["*"],  # MAUVAIS (trop permissif)
)
# Phase 1 PoC: allow_methods devrait être ["GET"] uniquement
# PUT/DELETE non implémentés mais autorisés
```

2. **Pas de security headers:**
```python
# Manque (devrait être dans middleware):
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - X-XSS-Protection: 1; mode=block
# - Content-Security-Policy
# - Referrer-Policy: strict-origin-when-cross-origin
```

3. **Logs en console (pas de fichier sécurisé):**
```python
# backend/services/folder_browser.py - LIGNE 26-52
print(f"[SLIDES] Using env SLIDES_REPOSITORY_PATH: {env_path}")
# PROBLÈME: print() va en console, pas dans /var/log sécurisé
# Pas de rotation logs
# Pas de protection contre lecture non autorisée
```

4. **Dépendances non vérifiées:**
```txt
# backend/requirements.txt - LIGNE 1-6
fastapi==0.109.0      # Jan 2024 - OK mais vérifier CVE
uvicorn[standard]==0.27.0  # Jan 2024
openslide-python==1.3.1    # Août 2023 - ANCIEN
Pillow==10.2.0        # Jan 2024 - OK
# Manque: safety check / pip-audit
```

**IMPACT:**
- XSS possible (pas de CSP)
- Clickjacking possible (pas de X-Frame-Options)
- Dépendances vulnérables potentielles

**REMEDIATION:**
```python
# Middleware security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "  # OpenSeadragon nécessite inline CSS
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    return response
```

```bash
# Scan dépendances
pip install safety pip-audit
safety check -r requirements.txt
pip-audit -r requirements.txt
```

---

#### A06:2021 – Vulnerable and Outdated Components

**STATUS: MOYEN - Dépendances Potentiellement Obsolètes**

**Findings:**

1. **openslide-python 1.3.1 (Août 2023):**
   - Dernière version: 1.3.1 (pas de mise à jour récente)
   - Dépendance C (libopenslide-0.dll) - vérifier CVE
   - Forks appliqués (Ventana LEFT patch) - risque si non maintenu

2. **Pas de scan automatique:**
   - Pas de GitHub Dependabot configuré
   - Pas de CI/CD avec `safety` ou `pip-audit`
   - Pas de monitoring CVE

3. **Frontend (npm):**
```json
// frontend/package.json - À vérifier
// openseadragon: version? Dernière maj?
// Autres dépendances npm à auditer
```

**IMPACT:** Exploitation CVE possible si vulnérabilités découvertes

**REMEDIATION:**
```bash
# CI/CD pipeline (GitHub Actions)
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Safety
        run: |
          pip install safety
          safety check -r backend/requirements.txt --json
      - name: Run npm audit
        run: |
          cd frontend
          npm audit --production
```

---

#### A07:2021 – Identification and Authentication Failures

**STATUS: CRITIQUE - AUCUNE AUTHENTIFICATION**

**Déjà couvert en A01. Résumé:**
- Pas d'authentification
- Pas de session management
- Pas de MFA
- Pas de password policy
- Pas de rate limiting login

---

#### A08:2021 – Software and Data Integrity Failures

**STATUS: MOYEN - Risques Supply Chain**

**Findings:**

1. **Pas de vérification intégrité dépendances:**
```bash
# requirements.txt - pas de hash
fastapi==0.109.0  # Devrait être:
# fastapi==0.109.0 \
#     --hash=sha256:abc123...
```

2. **Patch OpenSlide manuel (Ventana LEFT):**
```
# openslide-patch/openslide/ - fork non officiel
# Risque: modification malveillante si repo compromis
# Solution: fork CHU UCL contrôlé + review code
```

3. **Pas de signature release:**
   - Pas de GPG signing commits
   - Pas de checksum Docker images

**IMPACT:** Supply chain attack possible (dépendance compromise)

**REMEDIATION:**
```bash
# pip-tools avec hashes
pip install pip-tools
pip-compile --generate-hashes requirements.in -o requirements.txt

# Docker image scanning
docker scan varuna-backend:latest
trivy image varuna-backend:latest
```

---

#### A09:2021 – Security Logging and Monitoring Failures

**STATUS: CRITIQUE - Aucun Audit Trail**

**Findings:**

1. **Pas de logging HIPAA-compliant:**
```python
# backend/routes/slides.py - LIGNE 119-154
@router.get("/{slide_id}/info", tags=["visualization"])
async def get_slide_info(slide_id: str):
    # MANQUE: Audit log
    # Qui a accédé? Quand? Quelle IP? Autorisation?
    slide_path = get_slide_path_by_id(slide_id)
    metadata = get_slide_metadata(slide_path)
    return metadata
```

2. **Logs en console (pas fichier):**
   - `print()` au lieu de `logging` module
   - Pas de rotation logs
   - Pas de centralisation (Elasticsearch, Splunk)

3. **Pas de monitoring:**
   - Pas d'alertes sécurité
   - Pas de détection anomalies
   - Prometheus metrics (backend/monitoring.py) mais pas de logs sécurité

**IMPACT:**
- Impossible de détecter breach
- Pas de traçabilité pour audit (ISO 15189)
- Non-conformité RGPD Art. 32 (audit trail)

**REMEDIATION:**
```python
# HIPAA-compliant audit logger
import logging
from datetime import datetime

audit_logger = logging.getLogger('hipaa_audit')
audit_logger.setLevel(logging.INFO)
handler = logging.FileHandler('/var/log/varuna/audit.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S UTC'
))
audit_logger.addHandler(handler)

@router.get("/{slide_id}/info", tags=["visualization"])
async def get_slide_info(
    slide_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # LOG AVANT accès
    audit_logger.info(
        f"SLIDE_ACCESS | user={current_user.username} | "
        f"slide_id={slide_id} | ip={request.client.host} | "
        f"action=view_info"
    )

    slide_path = get_slide_path_by_id(slide_id)
    metadata = get_slide_metadata(slide_path)

    return metadata
```

---

#### A10:2021 – Server-Side Request Forgery (SSRF)

**STATUS: FAIBLE - Pas de Requêtes Externes**

**Findings:**
- Pas de fonctionnalité fetch() externe
- Pas de webhook/callback
- Risque SSRF très faible

**IMPACT:** Négligeable pour Phase 1

---

### 3.2 Additional Security Issues

#### 1. Secrets Management

**PROBLÈME:**
```bash
# .gitignore - LIGNE 42
.env  # Ignoré

# MAIS fichiers .env.phase1, .env.phase2.1, etc. PRÉSENTS dans repo
# Risque: credentials de test peuvent fuiter
```

**REMEDIATION:**
```bash
# Ajouter à .gitignore
.env*
!.env.example  # Seulement template

# Secrets Vault (Phase 2+)
# - HashiCorp Vault
# - AWS Secrets Manager
# - Azure Key Vault
```

---

#### 2. Docker Security

**PROBLÈME (si Dockerfiles existent):**
```dockerfile
# Risques potentiels:
# - Exécution en root
# - Image de base non vérifiée
# - Pas de healthcheck
# - Pas de USER non-root
```

**REMEDIATION:**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Créer utilisateur non-root
RUN groupadd -r varuna && useradd -r -g varuna varuna

# Installer dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier code
COPY --chown=varuna:varuna . /app
WORKDIR /app

# Switch to non-root
USER varuna

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

#### 3. Frontend Security (XSS)

**PROBLÈME:**
```javascript
// frontend/src/main.js - LIGNE 187-198
app.innerHTML = `
    <h1>${slide.name}</h1>  // POTENTIEL XSS si slide.name contient HTML
    <p>${slide.format}</p>
`;
```

**IMPACT:** XSS si nom de fichier malveillant (ex: `<script>alert(1)</script>.mrxs`)

**REMEDIATION:**
```javascript
// Utiliser textContent au lieu de innerHTML
const title = document.createElement('h1');
title.textContent = slide.name;  // Échappe automatiquement HTML

// OU sanitizer
import DOMPurify from 'dompurify';
app.innerHTML = DOMPurify.sanitize(`<h1>${slide.name}</h1>`);
```

---

### 3.3 Security Score Summary

| Catégorie OWASP | Sévérité | Score (/10) | Commentaire |
|-----------------|----------|-------------|-------------|
| A01: Access Control | CRITIQUE | 0/10 | Aucune auth/authz |
| A02: Cryptography | CRITIQUE | 0/10 | HTTP + stockage clair |
| A03: Injection | MOYEN | 6/10 | Path traversal mitigé |
| A04: Insecure Design | CRITIQUE | 2/10 | Pas de threat model |
| A05: Misconfiguration | ÉLEVÉ | 3/10 | CORS, headers, logs |
| A06: Outdated Components | MOYEN | 5/10 | Dépendances à vérifier |
| A07: Auth Failures | CRITIQUE | 0/10 | Pas d'auth |
| A08: Integrity | MOYEN | 5/10 | Supply chain à sécuriser |
| A09: Logging | CRITIQUE | 1/10 | Pas d'audit trail |
| A10: SSRF | FAIBLE | 9/10 | Pas de risque |

**SCORE GLOBAL:** **3.1 / 10** → **INACCEPTABLE POUR PRODUCTION**

---

## 4. Threat Model

### 4.1 STRIDE Analysis

**Système:** VarunaPoC - Visionneuse WSI avec données patient (PHI)

| Menace | Description | Impact | Probabilité | Risque | Mitigation |
|--------|-------------|--------|-------------|--------|------------|
| **Spoofing** | Attaquant se fait passer pour clinicien autorisé | Vol PHI | TRÈS ÉLEVÉE (pas d'auth) | CRITIQUE | OAuth2 + MFA |
| **Tampering** | Modification lames/métadonnées | Diagnostic erroné → patient harm | ÉLEVÉE (fichiers non chiffrés) | CRITIQUE | Chiffrement at rest + checksums |
| **Repudiation** | Utilisateur nie avoir accédé à une lame | Responsabilité légale floue | ÉLEVÉE (pas d'audit trail) | ÉLEVÉ | Audit trail HIPAA |
| **Information Disclosure** | Fuite données patient (RGPD breach) | Amende CNIL + réputation | TRÈS ÉLEVÉE (HTTP, pas auth) | CRITIQUE | TLS 1.3 + RBAC |
| **Denial of Service** | Surcharge serveur → indisponibilité | Blocage workflow hôpital | MOYENNE (pas de rate limit) | MOYEN | Rate limiting + CDN |
| **Elevation of Privilege** | Utilisateur lambda obtient droits admin | Accès toutes lames | ÉLEVÉE (pas de RBAC) | ÉLEVÉ | RBAC strict |

**Threat Actors:**

1. **Attaquant externe (internet):**
   - Motivations: Vol PHI pour revente, ransomware
   - Vecteur: Port 8000 exposé sans auth (si déployé)
   - Capacité: Moyenne (scripts automatisés)

2. **Attaquant interne (personnel hôpital):**
   - Motivations: Curiosité (célébrité), vengeance
   - Vecteur: Réseau interne CHU
   - Capacité: Élevée (accès physique, connaissance système)

3. **Supply chain attack:**
   - Motivations: Espionnage, sabotage
   - Vecteur: Dépendance compromise (npm, PyPI)
   - Capacité: Très élevée (APT, nation-state)

---

### 4.2 Attack Surface

**Entry Points:**

1. **REST API (Backend):**
   - `/api/slides/` → Liste toutes lames (PHI)
   - `/api/slides/{id}/info` → Métadonnées lame
   - `/api/slides/{id}/tiles/{level}/{col}_{row}.jpg` → Image streaming
   - `/api/slides/browse?path=...` → Navigation filesystem

2. **Frontend (Web UI):**
   - `frontend/src/main.js` → XSS possible
   - CORS → CSRF potentiel
   - WebSockets (si ajouté) → Hijacking

3. **Filesystem:**
   - `/Slides/` → Lecture directe si accès serveur
   - Backup non chiffré → Vol disque

4. **Dépendances:**
   - openslide-python, FastAPI, OpenSeadragon
   - Forks non officiels (Ventana LEFT patch)

**Trust Boundaries:**

```
[Utilisateur navigateur]  ←→  [Frontend Vite]  ←→  [Backend FastAPI]  ←→  [Filesystem /Slides]
     UNTRUSTED                  UNTRUSTED            TRUSTED               TRUSTED

Boundary 1: User ↔ Frontend (XSS, CSRF)
Boundary 2: Frontend ↔ Backend (auth requis ici)
Boundary 3: Backend ↔ Filesystem (ACL OS)
```

**Assets & Classification:**

| Asset | Type | Classification | Protection Actuelle | Protection Requise |
|-------|------|----------------|---------------------|-------------------|
| **Données patient (PHI)** | Métadonnées DICOM, images WSI | CRITIQUE | AUCUNE | Chiffrement + RBAC + Audit |
| **Credentials utilisateur** | Mots de passe, tokens | CRITIQUE | N/A (pas d'auth) | Bcrypt + Vault |
| **Code source** | Propriété intellectuelle | MOYEN | Git privé | Code review + SAST |
| **Logs système** | Audit trail | ÉLEVÉ | N/A (pas de logs) | Rotation + chiffrement |
| **Modèles IA** (futur) | Algorithmes diagnostiques | CRITIQUE | N/A | Chiffrement + versioning |

---

### 4.3 Attack Scenarios

#### Scénario 1: Vol de Données Patient (Data Breach)

**Attaquant:** Externe (script kiddie)
**Cible:** Toutes les lames avec métadonnées patient
**Vecteur:** API ouverte sans authentification

**Steps:**

1. Scanner internet trouve `http://chu-ucl-varuna.be:8000`
2. `GET /api/slides/` → Liste complète des lames (IDs, noms, formats)
3. Pour chaque lame:
   - `GET /api/slides/{id}/info` → Métadonnées (vendor, dimensions)
   - `GET /api/slides/{id}/overview` → Image overview JPEG
4. Scraping automatisé → base de données PHI
5. Revente sur dark web OU publication (extorsion)

**Impact:**
- RGPD breach → notification CNIL sous 72h
- Patients concernés notifiés (Art. 34)
- Amende potentielle: plusieurs millions €
- Réputation CHU détruite

**Probabilité:** 95% si système exposé internet sans auth

**Mitigation:**
- OAuth2 + JWT obligatoire
- Rate limiting (max 100 req/min/IP)
- WAF (Web Application Firewall)
- Monitoring + alertes anomalies

---

#### Scénario 2: Ransomware sur Images WSI

**Attaquant:** Groupe ransomware (APT)
**Cible:** Filesystem `/Slides/`
**Vecteur:** RDP compromise OU phishing personnel hôpital

**Steps:**

1. Attaquant obtient accès serveur (RDP, SSH, ou exploit)
2. Accède `/Slides/` (pas de chiffrement at rest)
3. Chiffre tous les fichiers .mrxs, .bif avec clé attaquant
4. Demande rançon pour déchiffrement
5. CHU paralysé (pas d'accès lames pour diagnostics)

**Impact:**
- Service anatomie pathologique ARRÊTÉ
- Diagnostics retardés → risque patient
- Coût: 100k-500k€ rançon + recovery
- Réputation + légal

**Probabilité:** 30% (ransomware hospitalier en hausse)

**Mitigation:**
- Chiffrement at rest (LUKS/VeraCrypt) avec clé hospital-controlled
- Backups offline (3-2-1 rule)
- Network segmentation (VLAN anatomie patho)
- EDR (Endpoint Detection & Response)

---

#### Scénario 3: Insider Threat - Accès Non Autorisé

**Attaquant:** Personnel hôpital (curieux)
**Cible:** Dossier VIP (politique, célébrité)
**Vecteur:** Réseau interne CHU

**Steps:**

1. Employé (non autorisé) accède `http://varuna.chu.local:8000`
2. `GET /api/slides/browse?path=/VIP/` → Liste lames sensibles
3. Ouvre lame → consultation non autorisée
4. **AUCUN LOG** → action non détectée

**Impact:**
- Violation confidentialité patient
- RGPD breach (accès non autorisé)
- Poursuite légale employé
- Responsabilité CHU

**Probabilité:** 60% (curiosité humaine)

**Mitigation:**
- RBAC strict (principe moindre privilège)
- Audit trail complet (qui, quoi, quand, IP)
- Alertes accès anormal (ex: secrétaire accède lame oncologie)
- Formation personnel (RGPD awareness)

---

## 5. Proposed Security Architecture

### 5.1 Security by Design Principles

**Principes fondamentaux (OWASP SAMM):**

1. **Defense in Depth (Défense en profondeur):**
   - Multiples couches de sécurité (auth + authz + chiffrement + audit)
   - Si une couche échoue, les autres protègent

2. **Least Privilege (Moindre privilège):**
   - Utilisateur a SEULEMENT les droits nécessaires à son rôle
   - Pas de "admin pour tous"

3. **Fail Secure (Échec sécurisé):**
   - Si erreur → DENY par défaut (pas ALLOW)
   - Ex: Erreur auth → 401 (pas accès)

4. **Separation of Duties (Séparation des tâches):**
   - Admin système ≠ Admin données patient
   - Code review requis (pas de commit direct)

5. **Privacy by Design (Vie privée dès la conception):**
   - Pseudonymisation par défaut
   - Minimisation données collectées
   - Droit à l'oubli implémenté

6. **Zero Trust Architecture:**
   - "Never trust, always verify"
   - Chaque requête est authentifiée/autorisée
   - Pas de confiance implicite réseau interne

---

### 5.2 Target Architecture (Phase 2-3)

```
┌────────────────────────────────────────────────────────────────┐
│                         INTERNET / CHU NETWORK                  │
└─────────────────────────┬──────────────────────────────────────┘
                          │
                    ┌─────▼─────┐
                    │  Firewall  │ (UFW/iptables)
                    │  + WAF     │ (ModSecurity)
                    └─────┬─────┘
                          │
              ┌───────────▼───────────┐
              │   Nginx Reverse Proxy  │
              │   - TLS 1.3 termination│
              │   - Rate limiting      │
              │   - Security headers   │
              └───────────┬───────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                     │
┌───────▼────────┐                  ┌────────▼────────┐
│  Frontend      │                  │  Backend        │
│  (Vite + OSD)  │                  │  (FastAPI)      │
│                │◄────HTTPS────────┤                 │
│  - CSP headers │                  │  - OAuth2       │
│  - XSS prevent │                  │  - JWT verify   │
└────────────────┘                  │  - RBAC         │
                                    │  - Audit log    │
                                    └────────┬────────┘
                                             │
                          ┌──────────────────┴──────────────────┐
                          │                                     │
                  ┌───────▼────────┐                  ┌─────────▼────────┐
                  │  Auth Service   │                  │  Slide Service   │
                  │  (Keycloak OU   │                  │  (OpenSlide)     │
                  │   CHU AD/LDAP)  │                  │                  │
                  │                 │                  │  - Tile server   │
                  │  - SSO          │                  │  - Metadata API  │
                  │  - MFA          │                  └─────────┬────────┘
                  │  - User mgmt    │                            │
                  └─────────────────┘                            │
                                                        ┌────────▼────────┐
                                                        │  Encrypted      │
                                                        │  Filesystem     │
                                                        │  /Slides/       │
                                                        │  (LUKS)         │
                                                        └─────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                     SUPPORTING SERVICES                           │
├──────────────────────────────────────────────────────────────────┤
│  - PostgreSQL (users, roles, permissions, audit logs)            │
│  - Redis (session cache, rate limiting)                          │
│  - Elasticsearch (centralized logging - SIEM)                    │
│  - Prometheus + Grafana (monitoring + alerting)                  │
│  - HashiCorp Vault (secrets management)                          │
└──────────────────────────────────────────────────────────────────┘
```

**Network Segmentation:**

```
VLAN 10: Frontend (DMZ)          → 10.0.10.0/24
VLAN 20: Backend API             → 10.0.20.0/24
VLAN 30: Database                → 10.0.30.0/24
VLAN 40: Storage (Slides)        → 10.0.40.0/24
VLAN 50: Admin/Monitoring        → 10.0.50.0/24

Firewall rules:
- Frontend → Backend: 443 (HTTPS)
- Backend → Database: 5432 (PostgreSQL)
- Backend → Storage: NFS/SMB (authentifié)
- Admin → ALL: 22 (SSH), monitoring ports
- Internet → Frontend: 443 (HTTPS) only
```

---

## 6. Authentication & Authorization

### 6.1 Authentication Strategy

**Phase 1 (PoC - URGENT):** HTTP Basic Auth (temporaire)

```python
# backend/auth/basic.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os

security = HTTPBasic()

def authenticate_basic(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Authentification Basic temporaire (Phase 1 uniquement).

    IMPORTANT: Utiliser HTTPS obligatoire (pas HTTP).
    """
    correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        os.getenv("API_USERNAME", "").encode("utf8")
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        os.getenv("API_PASSWORD", "").encode("utf8")
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
```

**Phase 2:** OAuth2 + JWT (OpenID Connect)

**Providers possibles:**

1. **Keycloak** (open-source, self-hosted)
   - Intégration AD/LDAP CHU
   - SSO (Single Sign-On)
   - MFA natif
   - Conforme RGPD (hébergement EU)

2. **Azure AD** (si CHU utilise Microsoft)
   - SSO institutionnel
   - MFA intégré
   - Gestion centralisée

3. **CHU AD/LDAP direct** (si infrastructure existante)
   - Réutilise comptes existants
   - Pas de nouveau mot de passe

**Implémentation OAuth2 + JWT:**

```python
# backend/auth/oauth2.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # 256-bit random (générer avec: openssl rand -hex 32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Crée un JWT access token.

    Refs:
    - RFC 7519: JSON Web Token
    - OWASP JWT Cheat Sheet
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Extrait et valide JWT, retourne utilisateur.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Vérifier expiration (automatique dans jwt.decode)

    except JWTError:
        raise credentials_exception

    # Charger utilisateur depuis DB
    user = await get_user_from_db(username)
    if user is None:
        raise credentials_exception

    return user
```

**MFA (Multi-Factor Authentication):**

```python
# backend/auth/mfa.py
import pyotp
import qrcode

def generate_mfa_secret(user: User) -> str:
    """
    Génère secret TOTP pour Google Authenticator.
    """
    secret = pyotp.random_base32()

    # Sauvegarder dans DB (chiffré)
    save_mfa_secret(user.id, secret)

    # Générer QR code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="VarunaPoC CHU UCL"
    )

    img = qrcode.make(totp_uri)
    return img

def verify_mfa_code(user: User, code: str) -> bool:
    """
    Vérifie code TOTP (6 digits).
    """
    secret = get_mfa_secret(user.id)
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # Allow 30s window
```

---

### 6.2 Authorization (RBAC)

**Rôles Proposés:**

| Rôle | Permissions | Use Case |
|------|-------------|----------|
| **ADMIN** | Toutes (CRUD users, config) | Administrateur système |
| **PATHOLOGIST** | Read/Write lames, annotations | Pathologiste confirmé |
| **RESIDENT** | Read lames (formation) | Interne en formation |
| **RESEARCHER** | Read lames anonymisées | Chercheur (pas PHI) |
| **TECHNICIAN** | Upload/scan lames | Technicien laboratoire |
| **GUEST** | Read lames (demo mode) | Demo/formation |

**Implémentation RBAC:**

```python
# backend/auth/rbac.py
from enum import Enum
from fastapi import Depends, HTTPException

class Role(str, Enum):
    ADMIN = "admin"
    PATHOLOGIST = "pathologist"
    RESIDENT = "resident"
    RESEARCHER = "researcher"
    TECHNICIAN = "technician"
    GUEST = "guest"

class Permission(str, Enum):
    # Slides
    SLIDE_READ = "slide:read"
    SLIDE_WRITE = "slide:write"
    SLIDE_DELETE = "slide:delete"

    # Annotations
    ANNOTATION_CREATE = "annotation:create"
    ANNOTATION_EDIT = "annotation:edit"

    # Users
    USER_MANAGE = "user:manage"

    # PHI
    PHI_ACCESS = "phi:access"  # Accès données non pseudonymisées

# Matrice permissions
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.SLIDE_READ,
        Permission.SLIDE_WRITE,
        Permission.SLIDE_DELETE,
        Permission.ANNOTATION_CREATE,
        Permission.ANNOTATION_EDIT,
        Permission.USER_MANAGE,
        Permission.PHI_ACCESS,
    ],
    Role.PATHOLOGIST: [
        Permission.SLIDE_READ,
        Permission.ANNOTATION_CREATE,
        Permission.ANNOTATION_EDIT,
        Permission.PHI_ACCESS,
    ],
    Role.RESIDENT: [
        Permission.SLIDE_READ,
        # Pas PHI_ACCESS (formation anonymisée)
    ],
    Role.RESEARCHER: [
        Permission.SLIDE_READ,
        # Pas PHI_ACCESS (données pseudonymisées)
    ],
    Role.TECHNICIAN: [
        Permission.SLIDE_WRITE,  # Upload uniquement
    ],
    Role.GUEST: [
        Permission.SLIDE_READ,  # Lecture seule (demo)
    ],
}

def require_permission(required_permission: Permission):
    """
    Decorator pour vérifier permission.
    """
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, [])

            if required_permission not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {required_permission} required"
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@router.get("/{slide_id}/info", tags=["visualization"])
@require_permission(Permission.SLIDE_READ)
async def get_slide_info(
    slide_id: str,
    current_user: User = Depends(get_current_user)
):
    # Vérifier accès spécifique à cette lame
    if not current_user.can_access_slide(slide_id):
        raise HTTPException(403, "Access denied to this slide")

    # ... logique
```

**Contexte de Sécurité (Security Context):**

```python
# backend/auth/context.py
from contextvars import ContextVar

# Context pour propagation user dans logs
current_user_ctx: ContextVar[User] = ContextVar('current_user', default=None)

@app.middleware("http")
async def security_context_middleware(request: Request, call_next):
    """
    Injecte utilisateur courant dans contexte.
    """
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    if token:
        try:
            user = await get_current_user(token)
            current_user_ctx.set(user)
        except:
            pass  # Anonymous

    response = await call_next(request)
    return response

# Usage dans logs
audit_logger.info(
    f"SLIDE_ACCESS | user={current_user_ctx.get().username} | ..."
)
```

---

### 6.3 Session Management

**Recommandations:**

1. **Token Expiration:**
   - Access token: 30 minutes (court)
   - Refresh token: 7 jours (stocké HttpOnly cookie)
   - Renouvellement automatique (refresh flow)

2. **Token Revocation:**
   - Blacklist tokens révoqués (Redis)
   - Logout → invalide token + refresh

3. **Concurrent Sessions:**
   - Limiter à 3 sessions simultanées par user
   - Afficher sessions actives (IP, device, last activity)
   - Bouton "Logout all sessions"

```python
# backend/auth/session.py
import redis
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

def revoke_token(token: str):
    """
    Révoque un token (logout).
    """
    # Décoder pour obtenir expiration
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp = payload.get("exp")

    # Ajouter à blacklist (expire automatiquement)
    ttl = exp - datetime.utcnow().timestamp()
    redis_client.setex(f"blacklist:{token}", int(ttl), "revoked")

def is_token_revoked(token: str) -> bool:
    """
    Vérifie si token est révoqué.
    """
    return redis_client.exists(f"blacklist:{token}") > 0

# Modifier get_current_user pour vérifier blacklist
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    if is_token_revoked(token):
        raise HTTPException(401, "Token has been revoked")

    # ... reste du code
```

---

## 7. Data Protection & Encryption

### 7.1 Encryption in Transit (TLS/HTTPS)

**Configuration Nginx (Reverse Proxy):**

```nginx
# /etc/nginx/sites-available/varuna.conf

server {
    listen 80;
    server_name varuna.chu-ucl.be;

    # Redirect HTTP → HTTPS (OBLIGATOIRE)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name varuna.chu-ucl.be;

    # TLS 1.3 UNIQUEMENT (plus sécurisé)
    ssl_protocols TLSv1.3;

    # Ciphers modernes (Mozilla Modern config)
    # Voir: https://ssl-config.mozilla.org/
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
    ssl_prefer_server_ciphers off;

    # Certificat (Let's Encrypt OU CA CHU)
    ssl_certificate /etc/ssl/certs/varuna.chu-ucl.be.crt;
    ssl_certificate_key /etc/ssl/private/varuna.chu-ucl.be.key;

    # OCSP Stapling (performance + privacy)
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/ssl/certs/ca-chain.crt;

    # HSTS (HTTP Strict Transport Security)
    # Force HTTPS pour 1 an (incluant sous-domaines)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # CSP (Content Security Policy)
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'" always;

    # Rate limiting (anti-DoS)
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req zone=api burst=20 nodelay;

    # Backend proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts (slides WSI peuvent être lentes)
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;  # 5 min max
    }

    # Frontend static files
    location / {
        root /var/www/varuna/frontend/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

**Vérification TLS:**

```bash
# Test avec SSL Labs
# https://www.ssllabs.com/ssltest/analyze.html?d=varuna.chu-ucl.be

# Test local
openssl s_client -connect varuna.chu-ucl.be:443 -tls1_3

# Vérifier cipher
nmap --script ssl-enum-ciphers -p 443 varuna.chu-ucl.be
```

---

### 7.2 Encryption at Rest

**Option 1: LUKS (Linux Unified Key Setup) - Recommandé**

```bash
# Chiffrer partition /Slides

# 1. Créer partition chiffrée
cryptsetup luksFormat /dev/sdb1
# Passphrase: STRONG (20+ caractères)

# 2. Ouvrir partition
cryptsetup luksOpen /dev/sdb1 slides_encrypted

# 3. Formater
mkfs.ext4 /dev/mapper/slides_encrypted

# 4. Monter
mount /dev/mapper/slides_encrypted /Slides

# 5. Auto-mount au boot (avec keyfile sécurisé)
dd if=/dev/urandom of=/root/slides.key bs=512 count=8
chmod 000 /root/slides.key
cryptsetup luksAddKey /dev/sdb1 /root/slides.key

# /etc/crypttab
slides_encrypted /dev/sdb1 /root/slides.key luks

# /etc/fstab
/dev/mapper/slides_encrypted /Slides ext4 defaults 0 2
```

**Option 2: VeraCrypt (Cross-platform, GUI)**

- Télécharger: https://www.veracrypt.fr/
- Créer volume chiffré (AES-256)
- Monter au boot avec script

**Option 3: Cloud Provider Encryption**

- **AWS:** EBS encryption (KMS managed keys)
- **Azure:** Disk encryption (Azure Key Vault)
- **GCP:** Persistent Disk encryption

**IMPORTANT - Key Management:**

1. **Clé LUKS/VeraCrypt:**
   - Stockée dans HSM (Hardware Security Module) OU
   - Keyfile protégé (chmod 000, root only) OU
   - HashiCorp Vault (auto-unseal)

2. **Backup clé:**
   - Escrowed backup (sealed envelope, safe physique)
   - Procédure recovery si serveur crash

3. **Rotation clés:**
   - Tous les 12 mois minimum
   - Après départ employé avec accès

---

### 7.3 Pseudonymization (RGPD Art. 32)

**Objectif:** Séparer identité patient ↔ données cliniques

**Architecture:**

```
┌──────────────────┐          ┌──────────────────┐
│  Patient DB      │          │  Slide DB        │
│                  │          │                  │
│  patient_id (PK) │          │  slide_id (PK)   │
│  nom             │          │  pseudonym_id ───┼──┐
│  prenom          │          │  path            │  │
│  date_naissance  │          │  format          │  │
│  ...             │          │  metadata        │  │
└──────────────────┘          └──────────────────┘  │
        │                                             │
        │                                             │
        ▼                                             │
┌──────────────────┐                                 │
│  Mapping Table   │◄────────────────────────────────┘
│  (ENCRYPTED)     │
│                  │
│  pseudonym_id    │ (hash SHA-256)
│  patient_id      │ (FK vers Patient DB)
│  created_at      │
│  created_by      │
└──────────────────┘
```

**Implémentation:**

```python
# backend/services/pseudonymization.py
import hashlib
import secrets
from cryptography.fernet import Fernet
import os

# Clé de chiffrement (stockée dans Vault)
ENCRYPTION_KEY = os.getenv("PSEUDONYM_ENCRYPTION_KEY")  # Fernet key
cipher = Fernet(ENCRYPTION_KEY)

def generate_pseudonym(patient_id: str, salt: str = None) -> str:
    """
    Génère pseudonyme pour un patient.

    Args:
        patient_id: ID patient réel (INAMI, dossier CHU, etc.)
        salt: Salt optionnel (stocké avec pseudonym)

    Returns:
        Pseudonyme (hash SHA-256 tronqué)

    RGPD:
        - Pseudonyme != anonymat (réversible avec table mapping)
        - Accès table mapping = ADMIN uniquement
        - Logs accès table mapping obligatoires
    """
    if not salt:
        salt = secrets.token_hex(16)

    # Hash avec salt
    pseudonym = hashlib.sha256(f"{patient_id}{salt}".encode()).hexdigest()[:16]

    # Stocker mapping (chiffré)
    store_pseudonym_mapping(pseudonym, patient_id, salt)

    return pseudonym

def store_pseudonym_mapping(pseudonym: str, patient_id: str, salt: str):
    """
    Stocke mapping pseudonyme → patient (chiffré).
    """
    # Chiffrer patient_id
    encrypted_patient_id = cipher.encrypt(patient_id.encode())

    # INSERT dans DB
    db.execute(
        "INSERT INTO pseudonym_mapping (pseudonym, encrypted_patient_id, salt) VALUES (?, ?, ?)",
        (pseudonym, encrypted_patient_id, salt)
    )

def resolve_pseudonym(pseudonym: str, current_user: User) -> str:
    """
    Résout pseudonyme → patient_id.

    SÉCURITÉ:
        - ADMIN uniquement (Permission.PHI_ACCESS)
        - LOG systématique (audit trail)
    """
    if Permission.PHI_ACCESS not in current_user.permissions:
        raise HTTPException(403, "Access denied: PHI_ACCESS required")

    # LOG AVANT accès
    audit_logger.warning(
        f"PSEUDONYM_RESOLVE | user={current_user.username} | "
        f"pseudonym={pseudonym} | ip={request.client.host}"
    )

    # Récupérer mapping
    row = db.execute(
        "SELECT encrypted_patient_id FROM pseudonym_mapping WHERE pseudonym = ?",
        (pseudonym,)
    ).fetchone()

    if not row:
        raise HTTPException(404, "Pseudonym not found")

    # Déchiffrer
    patient_id = cipher.decrypt(row["encrypted_patient_id"]).decode()

    return patient_id
```

**Usage dans API:**

```python
# backend/routes/slides.py

@router.get("/{slide_id}/info", tags=["visualization"])
async def get_slide_info(
    slide_id: str,
    current_user: User = Depends(get_current_user)
):
    slide = get_slide_by_id(slide_id)

    # Si utilisateur n'a PAS PHI_ACCESS (ex: chercheur)
    if Permission.PHI_ACCESS not in current_user.permissions:
        # Retourner version pseudonymisée
        return {
            "pseudonym_id": slide.pseudonym_id,  # Hash
            "format": slide.format,
            "dimensions": slide.dimensions,
            # PAS de nom patient, date naissance, etc.
        }

    # Si PHI_ACCESS (pathologiste, admin)
    else:
        patient_id = resolve_pseudonym(slide.pseudonym_id, current_user)
        patient = get_patient(patient_id)

        return {
            "patient": {
                "nom": patient.nom,
                "prenom": patient.prenom,
                "date_naissance": patient.date_naissance,
            },
            "slide": {
                "format": slide.format,
                "dimensions": slide.dimensions,
            }
        }
```

---

### 7.4 Data Minimization (RGPD Art. 5)

**Principe:** Collecter SEULEMENT les données nécessaires

**Exemple - Métadonnées DICOM:**

```python
# backend/services/dicom_sanitizer.py
import pydicom

# Tags DICOM contenant PHI (DICOM PS3.15 Table E.1-1)
PHI_TAGS = [
    (0x0010, 0x0010),  # Patient Name
    (0x0010, 0x0020),  # Patient ID
    (0x0010, 0x0030),  # Patient Birth Date
    (0x0010, 0x0040),  # Patient Sex
    (0x0010, 0x1010),  # Patient Age
    (0x0010, 0x1030),  # Patient Weight
    (0x0008, 0x0080),  # Institution Name
    (0x0008, 0x0090),  # Referring Physician Name
    (0x0008, 0x1048),  # Physician(s) of Record
    # ... liste complète: https://dicom.nema.org/medical/dicom/current/output/chtml/part15/chapter_E.html
]

def sanitize_dicom_metadata(slide_path: Path, role: Role) -> dict:
    """
    Sanitize DICOM metadata selon rôle utilisateur.
    """
    slide = openslide.OpenSlide(slide_path)
    metadata = dict(slide.properties)

    # Si utilisateur n'a PAS PHI_ACCESS
    if role not in [Role.ADMIN, Role.PATHOLOGIST]:
        # Supprimer tags PHI
        for tag_name in metadata.keys():
            if "patient" in tag_name.lower() or "physician" in tag_name.lower():
                del metadata[tag_name]

    return metadata
```

---

## 8. Audit Trail & Monitoring

### 8.1 HIPAA/RGPD Audit Requirements

**Exigences:**

1. **Qui?** Utilisateur (username, role)
2. **Quoi?** Action (view_slide, download, annotate, delete)
3. **Quand?** Timestamp (UTC, ISO 8601)
4. **Où?** IP address, device, geolocation (optionnel)
5. **Résultat?** Success/failure (HTTP status)
6. **Données?** Slide ID, patient pseudonym

**Rétention:** Minimum 6 ans (HIPAA) / 3-5 ans (RGPD selon AIPD)

---

### 8.2 Audit Trail Implementation

```python
# backend/services/audit.py
import logging
from datetime import datetime
from enum import Enum
from contextvars import ContextVar

# Logger dédié audit (séparé des logs système)
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# Handler vers fichier sécurisé
handler = logging.FileHandler('/var/log/varuna/audit.log')
handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S.%fZ'  # ISO 8601 UTC
))
audit_logger.addHandler(handler)

class AuditAction(str, Enum):
    # Authentification
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    MFA_ENABLED = "auth.mfa.enabled"

    # Slides
    SLIDE_VIEW = "slide.view"
    SLIDE_DOWNLOAD = "slide.download"
    SLIDE_UPLOAD = "slide.upload"
    SLIDE_DELETE = "slide.delete"

    # Annotations
    ANNOTATION_CREATE = "annotation.create"
    ANNOTATION_EDIT = "annotation.edit"
    ANNOTATION_DELETE = "annotation.delete"

    # PHI Access
    PHI_ACCESS = "phi.access"
    PSEUDONYM_RESOLVE = "pseudonym.resolve"

    # Administration
    USER_CREATE = "user.create"
    USER_DELETE = "user.delete"
    ROLE_CHANGE = "user.role.change"
    CONFIG_CHANGE = "config.change"

class AuditEvent:
    """
    Structured audit event (JSON-compatible).
    """
    def __init__(
        self,
        action: AuditAction,
        user: User,
        ip_address: str,
        resource_type: str = None,
        resource_id: str = None,
        status: str = "success",
        details: dict = None
    ):
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.action = action.value
        self.user_id = user.id
        self.username = user.username
        self.role = user.role.value
        self.ip_address = ip_address
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.status = status
        self.details = details or {}

    def to_log_message(self) -> str:
        """
        Format pour log structuré (parsable).
        """
        parts = [
            f"action={self.action}",
            f"user={self.username}",
            f"role={self.role}",
            f"ip={self.ip_address}",
            f"status={self.status}",
        ]

        if self.resource_type:
            parts.append(f"resource_type={self.resource_type}")
        if self.resource_id:
            parts.append(f"resource_id={self.resource_id}")

        # Details (JSON)
        if self.details:
            import json
            parts.append(f"details={json.dumps(self.details)}")

        return " | ".join(parts)

    def log(self):
        """
        Écrit dans audit log.
        """
        audit_logger.info(self.to_log_message())

# Contexte request (pour récupérer IP)
current_request: ContextVar[Request] = ContextVar('current_request', default=None)

@app.middleware("http")
async def audit_context_middleware(request: Request, call_next):
    """
    Injecte request dans contexte pour audit.
    """
    current_request.set(request)
    response = await call_next(request)
    return response

def audit_log(
    action: AuditAction,
    resource_type: str = None,
    resource_id: str = None,
    status: str = "success",
    details: dict = None
):
    """
    Helper pour logger action.
    """
    user = current_user_ctx.get()
    request = current_request.get()

    if not user or not request:
        # Fallback (ne devrait pas arriver)
        audit_logger.warning(f"Audit log without context: action={action}")
        return

    event = AuditEvent(
        action=action,
        user=user,
        ip_address=request.client.host,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
        details=details
    )
    event.log()
```

**Usage dans endpoints:**

```python
# backend/routes/slides.py

@router.get("/{slide_id}/info", tags=["visualization"])
async def get_slide_info(
    slide_id: str,
    current_user: User = Depends(get_current_user)
):
    # Audit AVANT accès
    audit_log(
        action=AuditAction.SLIDE_VIEW,
        resource_type="slide",
        resource_id=slide_id
    )

    slide_path = get_slide_path_by_id(slide_id)
    metadata = get_slide_metadata(slide_path)

    return metadata

@router.delete("/{slide_id}", tags=["admin"])
@require_permission(Permission.SLIDE_DELETE)
async def delete_slide(
    slide_id: str,
    current_user: User = Depends(get_current_user)
):
    # Audit CRITIQUE (suppression)
    audit_log(
        action=AuditAction.SLIDE_DELETE,
        resource_type="slide",
        resource_id=slide_id,
        details={"reason": "user_request"}
    )

    # ... suppression
```

---

### 8.3 Log Format & Storage

**Format Recommandé:** JSON Lines (JSONL)

```json
{"timestamp": "2025-12-31T10:30:45.123Z", "action": "slide.view", "user": "dr.smith", "role": "pathologist", "ip": "10.0.20.45", "resource_type": "slide", "resource_id": "a1b2c3d4e5f6", "status": "success", "details": {}}
{"timestamp": "2025-12-31T10:31:02.456Z", "action": "pseudonym.resolve", "user": "admin", "role": "admin", "ip": "10.0.50.10", "resource_type": "pseudonym", "resource_id": "abc123def456", "status": "success", "details": {"reason": "patient_inquiry"}}
{"timestamp": "2025-12-31T10:32:15.789Z", "action": "slide.delete", "user": "admin", "role": "admin", "ip": "10.0.50.10", "resource_type": "slide", "resource_id": "x9y8z7w6v5u4", "status": "success", "details": {"reason": "data_retention_policy"}}
```

**Storage:**

1. **Fichier local:** `/var/log/varuna/audit.log`
   - Rotation quotidienne (logrotate)
   - Compression après 7 jours
   - Archivage après 90 jours (cold storage)

2. **SIEM (Security Information and Event Management):**
   - Elasticsearch + Kibana (ELK Stack)
   - Splunk (commercial)
   - Graylog (open-source)

**Logrotate configuration:**

```bash
# /etc/logrotate.d/varuna-audit
/var/log/varuna/audit.log {
    daily
    rotate 2555  # 7 ans (2555 jours)
    compress
    delaycompress
    notifempty
    create 0600 varuna varuna
    missingok
    sharedscripts
    postrotate
        # Reopen log file
        systemctl reload varuna-backend
    endscript
}
```

---

### 8.4 Monitoring & Alerting

**Métriques Clés (Prometheus):**

```python
# backend/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Compteurs
auth_attempts_total = Counter(
    'varuna_auth_attempts_total',
    'Total authentication attempts',
    ['status']  # success/failed
)

slide_access_total = Counter(
    'varuna_slide_access_total',
    'Total slide accesses',
    ['action', 'role']  # view/download, pathologist/researcher
)

phi_access_total = Counter(
    'varuna_phi_access_total',
    'PHI accesses (pseudonym resolves)',
    ['user', 'role']
)

# Histogrammes (latence)
slide_load_duration = Histogram(
    'varuna_slide_load_duration_seconds',
    'Slide loading duration',
    ['format']  # mrxs/bif/svs
)

# Gauges (état)
active_sessions = Gauge(
    'varuna_active_sessions',
    'Number of active user sessions'
)

# Usage
@router.post("/api/auth/login")
async def login(credentials: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate(credentials.username, credentials.password)
        auth_attempts_total.labels(status='success').inc()
        active_sessions.inc()
        return create_access_token(user)
    except:
        auth_attempts_total.labels(status='failed').inc()
        raise HTTPException(401, "Invalid credentials")
```

**Alertes Critiques (Prometheus Alertmanager):**

```yaml
# prometheus/alerts.yml
groups:
  - name: varuna_security
    interval: 1m
    rules:
      # Alerte: Tentatives login échouées (brute force)
      - alert: HighFailedLoginRate
        expr: rate(varuna_auth_attempts_total{status="failed"}[5m]) > 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High failed login rate detected"
          description: "{{ $value }} failed login attempts/s in last 5 min"

      # Alerte: Accès PHI anormal
      - alert: UnusualPHIAccess
        expr: rate(varuna_phi_access_total[1h]) > 50
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Unusual PHI access pattern"
          description: "{{ $value }} PHI accesses in last hour (normal: <10)"

      # Alerte: Slide supprimées
      - alert: SlideDeleted
        expr: increase(varuna_slide_access_total{action="delete"}[5m]) > 0
        labels:
          severity: warning
        annotations:
          summary: "Slide deletion detected"
          description: "{{ $value }} slides deleted in last 5 min"

      # Alerte: Backend down
      - alert: BackendDown
        expr: up{job="varuna-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Varuna backend is down"
```

**Notifications:**

- **Email:** Équipe sécurité CHU
- **Slack/Teams:** Canal #varuna-security
- **PagerDuty:** Astreinte si critique (hors heures)

---

## 9. MLOps Security Considerations

### 9.1 ML Pipeline Threat Model

**Pipeline MLOps Typique:**

```
[Données Patient WSI] → [Annotation Pathologiste] → [Dataset Entraînement]
                                                            ↓
                                                    [Entraînement Modèle]
                                                            ↓
                                                    [Validation Clinique]
                                                            ↓
                                                    [Déploiement Production]
                                                            ↓
                                                    [Inférence sur Nouvelles Lames]
```

**Menaces Spécifiques ML:**

| Menace | Description | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Data Poisoning** | Attaquant injecte annotations malveillantes | Modèle apprend erreurs → diagnostic faux | Validation annotations multi-pathologistes |
| **Model Extraction** | Vol modèle propriétaire via API | Perte IP, concurrence | Rate limiting, watermarking modèle |
| **Adversarial Examples** | Images perturbées pour tromper IA | Faux négatif cancer → patient harm | Adversarial training, détection anomalies |
| **Membership Inference** | Inférer si patient dans dataset | Fuite PHI (RGPD breach) | Differential privacy, agrégation |
| **Model Inversion** | Reconstruire données training depuis modèle | Fuite images patient | Federated learning, homomorphic encryption |

---

### 9.2 Secure ML Development

**Recommandations:**

1. **Isolation Environnements:**
```
VLAN 60: ML Training (offline, pas internet)
VLAN 70: ML Inference (production, accès API)
```

2. **Dataset Pseudonymisé:**
```python
# ml/data_pipeline.py
def prepare_training_dataset(slides: List[Slide]) -> Dataset:
    """
    Prépare dataset pour entraînement (pseudonymisé).
    """
    dataset = []

    for slide in slides:
        # Extraire image + annotations
        image = load_slide_image(slide.path)
        annotations = get_annotations(slide.id)

        # Pseudonymiser
        dataset.append({
            "image": image,
            "annotations": annotations,
            "pseudonym_id": slide.pseudonym_id,  # PAS patient_id
            "metadata": {
                "format": slide.format,
                "scanner_vendor": slide.vendor,
                # PAS nom/date naissance/médecin
            }
        })

    return dataset
```

3. **Model Versioning & Lineage:**
```python
# ml/model_registry.py
from mlflow import log_model, log_params, log_metrics

def train_model(dataset: Dataset) -> Model:
    """
    Entraîne modèle avec tracking complet.
    """
    with mlflow.start_run():
        # Log hyperparams
        mlflow.log_params({
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100,
        })

        # Log dataset metadata (PAS les images)
        mlflow.log_params({
            "dataset_size": len(dataset),
            "dataset_hash": hash_dataset(dataset),  # Reproductibilité
            "annotation_source": "pathologist_consensus",
        })

        # Entraînement
        model = train(dataset)

        # Log metrics
        mlflow.log_metrics({
            "accuracy": 0.95,
            "precision": 0.93,
            "recall": 0.97,
            "f1_score": 0.95,
        })

        # Log modèle (chiffré)
        mlflow.log_model(model, "model", signature=signature)

    return model
```

4. **Adversarial Robustness:**
```python
# ml/adversarial_defense.py
from art.attacks.evasion import FastGradientMethod
from art.estimators.classification import PyTorchClassifier

def adversarial_training(model, dataset):
    """
    Entraîne avec adversarial examples.

    Refs:
    - Adversarial Robustness Toolbox (ART)
    - https://github.com/Trusted-AI/adversarial-robustness-toolbox
    """
    classifier = PyTorchClassifier(model=model)

    # Générer adversarial examples (FGSM)
    attack = FastGradientMethod(estimator=classifier, eps=0.01)
    adversarial_dataset = attack.generate(x=dataset.images)

    # Entraîner sur mix original + adversarial
    combined_dataset = dataset + adversarial_dataset
    model.fit(combined_dataset)

    return model
```

5. **Differential Privacy:**
```python
# ml/privacy.py
from opacus import PrivacyEngine

def train_with_dp(model, dataset, epsilon=1.0, delta=1e-5):
    """
    Entraîne avec Differential Privacy (DP-SGD).

    Refs:
    - Opacus (PyTorch DP library)
    - https://opacus.ai/

    Args:
        epsilon: Privacy budget (plus petit = plus privé, mais accuracy baisse)
        delta: Probability of privacy leak (typiquement 1/dataset_size)
    """
    privacy_engine = PrivacyEngine()

    model, optimizer, data_loader = privacy_engine.make_private(
        module=model,
        optimizer=optimizer,
        data_loader=data_loader,
        noise_multiplier=1.1,
        max_grad_norm=1.0,
    )

    # Entraînement normal (gradients sont bruités)
    model.fit(data_loader)

    # Vérifier privacy spent
    epsilon_spent = privacy_engine.get_epsilon(delta=delta)
    print(f"Privacy budget spent: ε={epsilon_spent} (target: {epsilon})")

    return model
```

---

### 9.3 Model Deployment Security

**Production Inference API:**

```python
# ml/inference_api.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import torch

router = APIRouter(prefix="/api/ml")

class InferenceRequest(BaseModel):
    slide_id: str
    model_version: str = "latest"

class InferenceResponse(BaseModel):
    prediction: str  # "benign" / "malignant"
    confidence: float  # 0.0-1.0
    model_version: str
    timestamp: str

@router.post("/predict", response_model=InferenceResponse)
@require_permission(Permission.SLIDE_READ)
async def predict(
    request: InferenceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Prédiction IA sur une lame.

    IMPORTANT:
        - Résultat DOIT être validé par pathologiste (MDR 2017/745)
        - Audit trail complet (qui a demandé prédiction, quand, résultat)
        - Rate limiting (max 100 prédictions/jour/user pour éviter model extraction)
    """
    # Audit log
    audit_log(
        action=AuditAction.ML_INFERENCE,
        resource_type="slide",
        resource_id=request.slide_id,
        details={"model_version": request.model_version}
    )

    # Rate limiting (anti-model extraction)
    if get_inference_count_today(current_user.id) > 100:
        raise HTTPException(429, "Daily inference quota exceeded")

    # Charger modèle (cached)
    model = load_model(request.model_version)

    # Charger slide
    slide = load_slide_image(request.slide_id)

    # Inférence
    with torch.no_grad():
        prediction = model(slide)

    # Interpréter
    result = interpret_prediction(prediction)

    # Sauvegarder résultat (pour audit + feedback loop)
    save_inference_result(
        slide_id=request.slide_id,
        user_id=current_user.id,
        prediction=result["class"],
        confidence=result["confidence"],
        model_version=request.model_version,
    )

    return InferenceResponse(
        prediction=result["class"],
        confidence=result["confidence"],
        model_version=request.model_version,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )
```

**Model Watermarking (Anti-Vol):**

```python
# ml/watermarking.py
def embed_watermark(model: torch.nn.Module, watermark_key: str) -> torch.nn.Module:
    """
    Embed watermark dans modèle (pour détecter vol).

    Refs:
    - "Protecting Intellectual Property of Deep Neural Networks with Watermarking"
    - https://arxiv.org/abs/1802.03582
    """
    # Générer trigger set (images spécifiques → prédiction spécifique)
    trigger_images = generate_trigger_set(watermark_key)

    # Fine-tune modèle pour mémoriser trigger set
    model.train()
    for trigger_img, trigger_label in trigger_images:
        output = model(trigger_img)
        loss = criterion(output, trigger_label)
        loss.backward()
        optimizer.step()

    return model

def verify_watermark(model: torch.nn.Module, watermark_key: str) -> bool:
    """
    Vérifie si modèle contient watermark (détection vol).
    """
    trigger_images = generate_trigger_set(watermark_key)

    # Tester trigger set
    correct = 0
    for trigger_img, trigger_label in trigger_images:
        output = model(trigger_img)
        if output.argmax() == trigger_label:
            correct += 1

    # Si > 95% correct → modèle volé
    return correct / len(trigger_images) > 0.95
```

---

## 10. PACS Integration Security

### 10.1 DICOM Security (PS3.15)

**DICOM Standard Security Profile:**

- **TLS:** Communication chiffrée (DICOM over TLS)
- **Application Entity (AE) Authentication:** Whitelisting AE Titles
- **Audit Trail:** DICOM Audit Message (ATNA profile)

**Implémentation:**

```python
# integrations/pacs/dicom_client.py
from pynetdicom import AE, evt, StoragePresentationContexts
from pynetdicom.sop_class import VerificationSOPClass
import ssl

# Configuration PACS Telemis
PACS_HOST = os.getenv("PACS_HOST", "pacs.chu-ucl.be")
PACS_PORT = int(os.getenv("PACS_PORT", "11112"))
PACS_AE_TITLE = os.getenv("PACS_AE_TITLE", "TELEMIS")
VARUNA_AE_TITLE = "VARUNA_POC"

# TLS Context
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(
    certfile="/etc/varuna/certs/varuna-dicom.crt",
    keyfile="/etc/varuna/certs/varuna-dicom.key"
)
ssl_context.load_verify_locations(cafile="/etc/varuna/certs/pacs-ca.crt")

# Application Entity
ae = AE(ae_title=VARUNA_AE_TITLE)
ae.add_requested_context(VerificationSOPClass)
ae.requested_contexts = StoragePresentationContexts

def query_pacs(patient_id: str, current_user: User) -> List[Study]:
    """
    Query PACS pour études d'un patient.

    Security:
        - TLS obligatoire
        - AE Title whitelisté dans PACS
        - Audit log (ATNA)
    """
    # Audit log
    audit_log(
        action=AuditAction.PACS_QUERY,
        resource_type="patient",
        resource_id=patient_id,
        details={"pacs_host": PACS_HOST}
    )

    # Connexion PACS (avec TLS)
    assoc = ae.associate(
        PACS_HOST,
        PACS_PORT,
        ae_title=PACS_AE_TITLE,
        tls_args=(ssl_context, None)  # TLS client context
    )

    if not assoc.is_established:
        raise HTTPException(503, "PACS connection failed")

    # C-FIND query
    from pydicom.dataset import Dataset
    ds = Dataset()
    ds.PatientID = patient_id
    ds.QueryRetrieveLevel = "STUDY"

    responses = assoc.send_c_find(ds, VerificationSOPClass)

    studies = []
    for (status, identifier) in responses:
        if status and status.Status == 0xFF00:  # Pending
            studies.append(identifier)

    assoc.release()

    return studies
```

**DICOM Audit Message (ATNA):**

```xml
<!-- DICOM Audit Message Format -->
<AuditMessage>
    <EventIdentification EventActionCode="R" EventDateTime="2025-12-31T10:30:45Z" EventOutcomeIndicator="0">
        <EventID csd-code="110112" codeSystemName="DCM" originalText="Query"/>
    </EventIdentification>
    <ActiveParticipant UserID="dr.smith" UserIsRequestor="true" NetworkAccessPointID="10.0.20.45">
        <RoleIDCode csd-code="110153" codeSystemName="DCM" originalText="Source"/>
    </ActiveParticipant>
    <ActiveParticipant UserID="TELEMIS" UserIsRequestor="false" NetworkAccessPointID="pacs.chu-ucl.be">
        <RoleIDCode csd-code="110152" codeSystemName="DCM" originalText="Destination"/>
    </ActiveParticipant>
    <AuditSourceIdentification AuditSourceID="VARUNA_POC"/>
    <ParticipantObjectIdentification ParticipantObjectID="123456789" ParticipantObjectTypeCode="1" ParticipantObjectTypeCodeRole="1">
        <ParticipantObjectIDTypeCode csd-code="2" codeSystemName="RFC-3881" originalText="Patient Number"/>
    </ParticipantObjectIdentification>
</AuditMessage>
```

---

### 10.2 HL7 FHIR API Security

**FHIR (Fast Healthcare Interoperability Resources):**

- **OAuth2 SMART-on-FHIR:** Standard auth healthcare
- **HTTPS:** Obligatoire (TLS 1.3)
- **Scopes:** Fine-grained permissions (patient/*.read, user/Observation.write)

**Exemple Client FHIR:**

```python
# integrations/fhir/client.py
from fhirclient import client
from fhirclient.models.patient import Patient
from fhirclient.models.observation import Observation

# Configuration FHIR server CHU
FHIR_BASE_URL = "https://fhir.chu-ucl.be/api/v4"
CLIENT_ID = os.getenv("FHIR_CLIENT_ID")
CLIENT_SECRET = os.getenv("FHIR_CLIENT_SECRET")

# SMART-on-FHIR settings
smart_settings = {
    'app_id': CLIENT_ID,
    'app_secret': CLIENT_SECRET,
    'api_base': FHIR_BASE_URL,
    'redirect_uri': 'https://varuna.chu-ucl.be/fhir/callback',
    'scope': 'patient/*.read user/Observation.write',
}

smart_client = client.FHIRClient(settings=smart_settings)

def get_patient_data(patient_id: str, current_user: User) -> Patient:
    """
    Récupère données patient depuis FHIR.

    Security:
        - OAuth2 SMART-on-FHIR
        - Scope patient/*.read requis
        - Audit log
    """
    # Audit log
    audit_log(
        action=AuditAction.FHIR_QUERY,
        resource_type="patient",
        resource_id=patient_id
    )

    # Autoriser smart_client (OAuth2 flow)
    if not smart_client.ready:
        smart_client.authorize()

    # Query patient
    patient = Patient.read(patient_id, smart_client.server)

    return patient
```

---

## 11. Implementation Roadmap

### Phase 1: URGENT (1-2 semaines) - Sécurité Minimale PoC

**Objectif:** Rendre PoC utilisable en environnement CHU interne (réseau isolé)

**Tasks:**

- [ ] **Auth Basic** (temporaire)
  - Implémenter HTTP Basic Auth
  - Variables env (.env) pour credentials
  - HTTPS local (certificat self-signed)

- [ ] **Logs Audit** (minimal)
  - Logger tous accès slides (user, slide_id, timestamp, IP)
  - Fichier `/var/log/varuna/audit.log`
  - Rotation logrotate

- [ ] **Security Headers**
  - Middleware FastAPI (X-Frame-Options, CSP, etc.)
  - CORS strict (localhost uniquement)

- [ ] **Input Validation**
  - Pydantic models pour paramètres API
  - Validation slide_id, level, col, row

- [ ] **Scan Vulnérabilités**
  - `safety check` sur requirements.txt
  - `npm audit` sur frontend
  - Corriger CVE critiques

**Livrable:** PoC sécurisé pour tests internes CHU (pas internet)

---

### Phase 2: Court Terme (1-2 mois) - OAuth2 + RBAC

**Objectif:** Authentification production-ready + contrôle accès

**Tasks:**

- [ ] **OAuth2 + JWT**
  - Intégration Keycloak OU Azure AD
  - SSO avec comptes CHU existants
  - JWT avec expiration 30 min

- [ ] **RBAC**
  - Définir rôles (admin, pathologist, resident, researcher)
  - Matrice permissions
  - Middleware require_permission()

- [ ] **MFA**
  - TOTP (Google Authenticator)
  - Obligatoire pour admins

- [ ] **TLS/HTTPS**
  - Certificat Let's Encrypt OU CA CHU
  - Nginx reverse proxy
  - HSTS headers

- [ ] **Pseudonymisation**
  - Hash patient_id → pseudonym
  - Table mapping chiffrée
  - API resolve_pseudonym (admin only)

**Livrable:** Système déployable en production interne CHU

---

### Phase 3: Moyen Terme (3-6 mois) - Chiffrement + SIEM

**Objectif:** Conformité RGPD complète + monitoring

**Tasks:**

- [ ] **Chiffrement at Rest**
  - LUKS sur partition /Slides
  - Key management (Vault)
  - Backups chiffrés

- [ ] **SIEM**
  - Elasticsearch + Kibana
  - Centralisation logs (audit + système)
  - Dashboards sécurité

- [ ] **Alerting**
  - Prometheus + Alertmanager
  - Alertes: failed login, PHI access anormal, slides deleted
  - Notifications Email/Slack

- [ ] **AIPD (RGPD Art. 35)**
  - Document analyse impact
  - Validation DPO CHU
  - Mesures d'atténuation risques

- [ ] **Secrets Management**
  - HashiCorp Vault
  - Rotation automatique secrets
  - Pas de .env en clair

**Livrable:** Conformité RGPD + ISO 15189

---

### Phase 4: Long Terme (6-12 mois) - MLOps Security

**Objectif:** Infrastructure ML sécurisée

**Tasks:**

- [ ] **ML Pipeline Isolation**
  - VLAN séparé training (offline)
  - VLAN inférence (production)
  - Network policies Kubernetes

- [ ] **Dataset Pseudonymisé**
  - Pipeline automatique pseudonymisation
  - Validation annotations multi-pathologistes
  - Versioning datasets (DVC)

- [ ] **Model Security**
  - Adversarial training (robustesse)
  - Differential Privacy (DP-SGD)
  - Model watermarking (anti-vol)

- [ ] **Federated Learning** (optionnel)
  - Entraînement distribué sans partager données
  - Collaboration multi-centres (UCL + autres hôpitaux)

- [ ] **Conformité AI Act**
  - Documentation technique modèle
  - Validation clinique
  - Surveillance humaine (pathologiste override)

**Livrable:** Plateforme MLOps conforme réglementations

---

## 12. Security Testing & Validation

### 12.1 Penetration Testing

**Scopes:**

1. **External Pentest** (depuis internet):
   - Scan ports (nmap, masscan)
   - Exploitation CVE connus (Metasploit)
   - Brute force login
   - SQL injection, XSS, CSRF
   - Path traversal

2. **Internal Pentest** (réseau CHU):
   - Lateral movement (depuis poste compromis)
   - Privilege escalation
   - Accès non autorisé slides

3. **Physical Security** (optionnel):
   - Accès physique serveur
   - USB attack (BadUSB)
   - Social engineering (phishing personnel)

**Fréquence:**
- Avant mise en production (obligatoire)
- Annuel (minimum)
- Après changements majeurs (architecture, auth)

**Providers:**
- **Interne:** Équipe sécurité CHU
- **Externe:** Cabinet spécialisé healthcare (ex: TrustedSec, Synack)

---

### 12.2 Vulnerability Scanning

**Outils:**

1. **SAST (Static Application Security Testing):**
```bash
# Bandit (Python)
bandit -r backend/ -f json -o security-report.json

# Semgrep (multi-language)
semgrep --config=auto backend/
```

2. **DAST (Dynamic Application Security Testing):**
```bash
# OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py \
    -t https://varuna.chu-ucl.be \
    -r zap-report.html

# Nikto (web scanner)
nikto -h https://varuna.chu-ucl.be -ssl
```

3. **Dependency Scanning:**
```bash
# Python
pip-audit -r backend/requirements.txt

# npm
cd frontend && npm audit --production

# Docker
trivy image varuna-backend:latest
```

4. **Infrastructure Scanning:**
```bash
# Nmap
nmap -sV -sC -p- varuna.chu-ucl.be

# Lynis (system hardening)
lynis audit system
```

**CI/CD Integration:**

```yaml
# .github/workflows/security-scan.yml
name: Security Scan
on: [push, pull_request]

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r backend/ -f json -o bandit-report.json

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: auto

      - name: Upload Reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
            semgrep-report.json

  dependency:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Python Dependencies
        run: |
          pip install pip-audit
          pip-audit -r backend/requirements.txt

      - name: npm Dependencies
        run: |
          cd frontend
          npm audit --production
```

---

### 12.3 Compliance Audits

**RGPD Audit:**
- DPO CHU review
- Vérification droits des personnes (accès, effacement, portabilité)
- Test notification breach (72h)
- Revue contrats sous-traitants (cloud providers)

**ISO 15189 Audit:**
- Traçabilité complète (qui a accédé quoi)
- Validation logiciel (test acceptance)
- Contrôle qualité (precision metrics)
- Accréditation (BELAC/COFRAC)

**MDR Audit (si IA diagnostique):**
- Organisme notifié (TÜV, BSI, etc.)
- Documentation technique complète
- Gestion risques (ISO 14971)
- Post-market surveillance (incidents reportés)

**AI Act Audit (si IA haut risque):**
- Qualité datasets (représentativité, biais)
- Robustesse modèle (adversarial testing)
- Surveillance humaine (pathologiste override)
- Transparence (documentation utilisateur)

---

## 13. References & Standards

### 13.1 Security Standards

**OWASP (Open Web Application Security Project):**
- Top 10: https://owasp.org/Top10/
- ASVS (Application Security Verification Standard): https://owasp.org/www-project-application-security-verification-standard/
- SAMM (Software Assurance Maturity Model): https://owaspsamm.org/
- Cheat Sheets: https://cheatsheetseries.owasp.org/

**NIST (National Institute of Standards and Technology):**
- Cybersecurity Framework: https://www.nist.gov/cyberframework
- SP 800-53 (Security Controls): https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- SP 800-63B (Digital Identity): https://pages.nist.gov/800-63-3/sp800-63b.html
- SP 800-52 (TLS Guidelines): https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final

**CIS (Center for Internet Security):**
- CIS Controls: https://www.cisecurity.org/controls
- Benchmarks: https://www.cisecurity.org/cis-benchmarks

**ISO/IEC:**
- ISO 27001 (Information Security Management): https://www.iso.org/standard/27001
- ISO 27799 (Health Informatics Security): https://www.iso.org/standard/62777.html

---

### 13.2 Healthcare Regulations

**RGPD (EU):**
- Texte officiel: https://gdpr.eu/
- CNIL (France): https://www.cnil.fr/
- APD (Belgique): https://www.autoriteprotectiondonnees.be/

**HIPAA (US - pour référence):**
- Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/index.html
- Breach Notification: https://www.hhs.gov/hipaa/for-professionals/breach-notification/index.html

**MDR 2017/745:**
- Texte: https://eur-lex.europa.eu/eli/reg/2017/745/oj
- MDCG Guidance: https://health.ec.europa.eu/medical-devices-sector/guidance-documents_en

**AI Act 2024/1689:**
- Texte: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:52021PC0206
- AI in Healthcare: https://health.ec.europa.eu/md_topics/md_sector/ai_en

**ISO 15189:**
- Standard: https://www.iso.org/standard/76677.html

---

### 13.3 Technical References

**Cryptography:**
- TLS 1.3: https://datatracker.ietf.org/doc/html/rfc8446
- JWT: https://datatracker.ietf.org/doc/html/rfc7519
- OAuth2: https://datatracker.ietf.org/doc/html/rfc6749
- TOTP: https://datatracker.ietf.org/doc/html/rfc6238

**Authentication:**
- OAuth2 for Medical Devices: https://www.hl7.org/fhir/smart-app-launch/
- SMART-on-FHIR: https://smarthealthit.org/

**DICOM Security:**
- DICOM PS3.15: https://dicom.nema.org/medical/dicom/current/output/chtml/part15/PS3.15.html
- IHE ATNA: https://wiki.ihe.net/index.php/Audit_Trail_and_Node_Authentication

**ML Security:**
- Adversarial Robustness Toolbox: https://github.com/Trusted-AI/adversarial-robustness-toolbox
- Opacus (Differential Privacy): https://opacus.ai/
- MLflow (Model Registry): https://mlflow.org/

---

### 13.4 Books & Publications

**Security Engineering:**
- "Security Engineering" by Ross Anderson: https://www.cl.cam.ac.uk/~rja14/book.html
- "Cryptography Engineering" by Schneier, Ferguson, Kohno
- "The Web Application Hacker's Handbook" by Stuttard, Pinto

**Healthcare Security:**
- "Healthcare Information Security and Privacy" by Murphy
- "HIPAA Security Rule Handbook" by Beaver

**Machine Learning Security:**
- "Adversarial Robustness for Machine Learning" by Goldblum et al.
- "Privacy-Preserving Machine Learning" by Xiong et al.

---

## Annexes

### Annexe A: Security Checklist (Pre-Production)

**Authentication & Authorization:**
- [ ] OAuth2 + JWT implémenté
- [ ] MFA activé pour admins
- [ ] RBAC configuré (tous rôles définis)
- [ ] Session timeout configuré (30 min max)
- [ ] Password policy (12+ chars, complexité)
- [ ] Rate limiting login (max 5/min/IP)

**Encryption:**
- [ ] TLS 1.3 configuré (certificat valide)
- [ ] HSTS header activé
- [ ] Chiffrement at rest (LUKS sur /Slides)
- [ ] Secrets dans Vault (pas .env)

**Data Protection:**
- [ ] Pseudonymisation implémentée
- [ ] AIPD complétée et validée
- [ ] Droits RGPD implémentés (accès, effacement, portabilité)
- [ ] Procédure breach notification testée

**Audit & Monitoring:**
- [ ] Audit trail complet (tous endpoints sensibles)
- [ ] Logs centralisés (SIEM)
- [ ] Alertes configurées (failed login, PHI access)
- [ ] Rétention logs 6+ ans
- [ ] Dashboards sécurité (Grafana)

**Testing:**
- [ ] Pentest externe réalisé (rapport validé)
- [ ] Scan vulnérabilités (SAST, DAST, dépendances)
- [ ] Load testing (1000 users simultanés)
- [ ] Disaster recovery testé (backup restore)

**Compliance:**
- [ ] DPO CHU approuvé
- [ ] ISO 15189 accréditation obtenue
- [ ] MDR conformité (si IA diagnostique)
- [ ] Documentation technique complète
- [ ] Formation utilisateurs (sécurité RGPD)

---

### Annexe B: Incident Response Plan

**Phase 1: Detection (0-15 min)**

1. **Alerte reçue** (monitoring, user report, pentest)
2. **Vérification** (faux positif?)
3. **Escalade** si confirmé → Incident Response Team

**Phase 2: Containment (15-60 min)**

1. **Isoler système** (firewall rules, déconnexion réseau si nécessaire)
2. **Identifier scope** (quels systèmes affectés? quelles données?)
3. **Préserver preuves** (snapshots, logs)

**Phase 3: Eradication (1-24h)**

1. **Identifier cause racine** (vulnérabilité, attaque, erreur config?)
2. **Patcher vulnérabilité**
3. **Changer credentials** (si compromise)
4. **Scan complet** (malware, backdoors)

**Phase 4: Recovery (1-7 jours)**

1. **Restaurer depuis backup** (si nécessaire)
2. **Vérifier intégrité** (checksums, validation)
3. **Retour production** (progressif, monitoring renforcé)

**Phase 5: Post-Incident (7-30 jours)**

1. **Rapport incident** (timeline, impact, lessons learned)
2. **Notification CNIL** (si RGPD breach, sous 72h)
3. **Notification patients** (si risque élevé)
4. **Amélioration sécurité** (patch gaps identifiés)

**Contacts Urgence:**
- DPO CHU: dpo@chu-ucl.be
- CIRT (Computer Incident Response Team): cirt@chu-ucl.be
- CNIL (si breach): https://www.cnil.fr/fr/notifier-une-violation-de-donnees-personnelles
- Équipe DevOps: devops@chu-ucl.be

---

### Annexe C: Glossary

**AIPD:** Analyse d'Impact relative à la Protection des Données (RGPD Art. 35)
**ATNA:** Audit Trail and Node Authentication (IHE profile)
**CVE:** Common Vulnerabilities and Exposures
**DPO:** Data Protection Officer (Délégué à la Protection des Données)
**FHIR:** Fast Healthcare Interoperability Resources
**HIPAA:** Health Insurance Portability and Accountability Act (US)
**LUKS:** Linux Unified Key Setup (chiffrement disque)
**MDR:** Medical Device Regulation (EU 2017/745)
**MFA:** Multi-Factor Authentication
**PHI:** Protected Health Information
**RBAC:** Role-Based Access Control
**RGPD:** Règlement Général sur la Protection des Données (EU)
**SIEM:** Security Information and Event Management
**STRIDE:** Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege
**TLS:** Transport Layer Security
**WSI:** Whole Slide Imaging

---

**END OF DOCUMENT**

**Next Steps:**
1. Review with CHU security team
2. Obtain DPO approval
3. Implement Phase 1 (urgent security fixes)
4. Schedule external pentest
5. Update AIPD

**Document maintained by:** Security Architect Team
**Review cycle:** Quarterly (or after major changes)
**Classification:** CONFIDENTIAL - Internal CHU only
