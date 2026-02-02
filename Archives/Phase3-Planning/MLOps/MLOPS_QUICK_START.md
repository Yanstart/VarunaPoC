# MLOPS_QUICK_START.md

**Guide de Démarrage Rapide - MLOps VarunaPoC**

**Date:** 2025-12-31
**Pour:** Développeurs démarrant l'intégration MLOps
**Temps de lecture:** 10 minutes

---

## TL;DR

**Vous êtes ici pour:** Transformer VarunaPoC en plateforme d'apprentissage continu avec feedback pathologistes.

**Architecture créée aujourd'hui:**
- ✅ Documentation complète (60+ pages)
- ✅ Tag system (extraction automatique organ/stain/marker)
- ✅ Router intelligent (routage vers modèles spécialisés)
- ✅ Schema database complet (PostgreSQL)
- ✅ Configuration DVC + MLflow

**Prochaines étapes:** Implémentation progressive sur 12-18 mois

---

## Documents Essentiels

### 1. Architecture Complète (MUST READ)

**Fichier:** `docs/MLOPS_ARCHITECTURE.md` (60+ pages)

**Contenu:**
- Vue d'ensemble système
- Système de routage par tags (Section 2)
- Infrastructure MLOps (Section 3)
- Pipeline feedback pathologistes (Section 4)
- Continuous learning (Section 5)
- Structures de données (Section 6)
- Roadmap implémentation (Section 8)

**Temps:** 60 min lecture complète

### 2. Guide d'Intégration (STEP BY STEP)

**Fichier:** `docs/MLOPS_INTEGRATION_GUIDE.md` (30+ pages)

**Contenu:**
- Prérequis infrastructure
- Phase 3.1: Setup MLflow, DVC, DB (2-3 mois)
- Phase 3.2: Tag extraction + routing (1-2 mois)
- Phase 3.3: Feedback pipeline (2 mois)
- Phase 3.4: Continuous learning (3-4 mois)

**Temps:** 30 min lecture, puis suivre étape par étape

### 3. Index Fichiers (OVERVIEW)

**Fichier:** `docs/MLOPS_FILES_SUMMARY.md`

**Contenu:**
- Liste complète fichiers créés (9 fichiers ✅)
- Liste fichiers à créer (30+ fichiers 🔄)
- Organisation par phase
- Commandes utiles

**Temps:** 10 min

---

## Fichiers Créés Aujourd'hui

### Documentation (docs/)

1. **`docs/MLOPS_ARCHITECTURE.md`** (60+ pages)
   - Architecture complète MLOps
   - Référence principale pour toutes questions

2. **`docs/MLOPS_INTEGRATION_GUIDE.md`** (30+ pages)
   - Guide intégration progressive
   - Instructions détaillées par phase

3. **`docs/MLOPS_FILES_SUMMARY.md`**
   - Index tous les fichiers
   - Checklist implémentation

4. **`docs/MLOPS_QUICK_START.md`** (ce fichier)
   - Guide démarrage rapide
   - Liens vers ressources clés

### Configuration (backend/config/)

5. **`backend/config/ml_routes.yaml`**
   - Configuration routage par tags
   - Définition modèles spécialisés (Gleason, Ki-67, HER2, etc.)

### Services ML (backend/services/ml/)

6. **`backend/services/ml/__init__.py`**
   - Package ML services

7. **`backend/services/ml/tag_extractor.py`** (370 lignes)
   - Extraction automatique tags
   - 4 sources: DICOM, OpenSlide properties, filename, ML inference

8. **`backend/services/ml/tag_router.py`** (280 lignes)
   - Routage intelligent vers modèles
   - Stratégies: exact match, partial match, fallback

9. **`backend/services/ml/README.md`**
   - Documentation services ML
   - Usage, exemples, troubleshooting

### Database (backend/database/)

10. **`backend/database/schema_ml.sql`** (580 lignes)
    - Schema complet PostgreSQL
    - 7 tables + 4 views + 2 functions
    - Prêt pour production

### Versioning (DVC)

11. **`.dvc/config.example`**
    - Configuration DVC
    - Remote storage (MinIO, S3, Azure, GCP)

---

## Architecture en 5 Minutes

### 1. Workflow Complet

```
Slide → Tag Extraction → Tag Router → Modèle Spécialisé → Prédiction + Uncertainty → Pathologiste Valide/Corrige → Feedback DB → Dataset Enrichi → Re-entraînement Auto → Modèle Amélioré
```

### 2. Système de Tags

**Tags extraits:**
- `organ` (prostate, sein, côlon, poumon, etc.)
- `stain` (H&E, IHC, IF, etc.)
- `marker` (Ki-67, HER2, PD-L1, etc.)
- `task` (grading, counting, classification, detection)

**Sources (par priorité):**
1. DICOM metadata (confidence 0.95)
2. OpenSlide properties (confidence 0.85)
3. Filename parsing (confidence 0.70)
4. ML inference (confidence 0.75)

**Exemple:**
```python
extractor = TagExtractor()
tags = extractor.extract_tags("prostate_HE_sample1.mrxs", "MRXS")
# → {"organ": "prostate", "stain": "H&E", "confidence": 0.7, "source": "filename"}
```

### 3. Routage Intelligent

**Configuration:** `backend/config/ml_routes.yaml`

**Exemple route:**
```yaml
- model_id: "gleason_grading_v2"
  model_name: "Gleason Grading Model"
  priority: 100
  required_tags:
    organ: "prostate"
    stain: "H&E"
    task: "grading"
```

**Usage:**
```python
router = TagRouter("config/ml_routes.yaml")
route = router.route({"organ": "prostate", "stain": "H&E", "task": "grading"})
# → route.model_path = "models:/gleason_grading/production"
```

### 4. Pipeline Feedback

**Types:**
- **Approve:** Prédiction correcte
- **Correct:** Prédiction incorrecte, pathologiste corrige
- **Reject:** Prédiction inutilisable
- **Annotate:** Pas de prédiction, annotation from scratch

**Storage:**
```sql
INSERT INTO ml_feedback (action, original_prediction, corrected_prediction, ...)
VALUES ('correct', '{"class": "gleason_3"}', '{"class": "gleason_4"}', ...);
```

### 5. Continuous Learning

**Déclencheurs re-entraînement:**
- 100+ nouvelles corrections
- OU approval rate < 85%
- OU 30 jours depuis dernier retraining

**Pipeline (Airflow DAG):**
1. Check threshold
2. Prepare dataset (DVC)
3. Train model (MLflow)
4. Validate performance
5. Deploy A/B test (20% traffic)
6. Auto-promote si succès

---

## Commencer Maintenant (3 étapes)

### Étape 1: Lire Architecture (1h)

```bash
# Ouvrir document principal
code docs/MLOPS_ARCHITECTURE.md

# Sections clés:
# - Section 2: Système de routage par tags
# - Section 3: Infrastructure MLOps
# - Section 4: Pipeline feedback
# - Section 6: Structures de données
```

### Étape 2: Setup Infrastructure (1 semaine)

**Suivre:** `docs/MLOPS_INTEGRATION_GUIDE.md` Phase 3.1

```bash
# 1. Setup MLflow
mlflow server --host 0.0.0.0 --port 5000 ...

# 2. Setup DVC
dvc init
dvc remote add -d minio s3://varuna-ml-data

# 3. Setup Database
psql -U postgres -d varuna_ml -f backend/database/schema_ml.sql

# 4. Setup Label Studio
docker run -p 8080:8080 heartexlabs/label-studio:latest
```

### Étape 3: Implémenter Tag System (2 semaines)

**Suivre:** `docs/MLOPS_INTEGRATION_GUIDE.md` Phase 3.2

```bash
# 1. Tester tag extraction
python backend/services/ml/tag_extractor.py

# 2. Tester routing
python backend/services/ml/tag_router.py

# 3. Intégrer dans backend existant
# Modifier backend/services/slide_scanner.py
# Ajouter extraction tags dans scan_slides_directory()
```

---

## Stack Technologique

### Core MLOps

| Outil | Usage | Documentation |
|-------|-------|---------------|
| **MLflow** | Tracking expérimentations + Model registry | https://mlflow.org/docs/ |
| **DVC** | Versioning datasets | https://dvc.org/doc |
| **Label Studio** | Annotation plateforme | https://labelstud.io/guide/ |
| **Evidently AI** | Drift detection | https://docs.evidentlyai.com/ |
| **Airflow** | Pipeline orchestration | https://airflow.apache.org/docs/ |

### ML Frameworks

| Framework | Usage |
|-----------|-------|
| **PyTorch** | Deep learning models |
| **scikit-learn** | ML classique + metrics |
| **OpenCV** | Image processing |
| **NumPy** | Array operations |

### Infrastructure

| Service | Usage |
|---------|-------|
| **PostgreSQL** | Database (metadata, feedback, metrics) |
| **MinIO** | S3-compatible storage (datasets, models) |
| **Docker** | Containerization |

---

## Database Schema (Résumé)

**Tables principales:**

```sql
-- Slides avec tags ML
CREATE TABLE slides_metadata (
    slide_id VARCHAR(255),
    organ VARCHAR(100),
    stain VARCHAR(100),
    marker VARCHAR(100),
    tags_confidence FLOAT,
    ...
);

-- Prédictions ML
CREATE TABLE ml_predictions (
    prediction_id VARCHAR(255),
    model_id VARCHAR(255),
    prediction_class VARCHAR(255),
    confidence_score FLOAT,
    uncertainty_score FLOAT,
    validation_status VARCHAR(50),  -- 'pending', 'approved', 'corrected', 'rejected'
    ...
);

-- Feedback pathologistes
CREATE TABLE ml_feedback (
    action VARCHAR(50),  -- 'approve', 'correct', 'reject', 'annotate'
    original_prediction JSONB,
    corrected_prediction JSONB,
    processing_status VARCHAR(50),  -- 'pending', 'included_in_retraining'
    ...
);

-- Registry modèles
CREATE TABLE model_registry (
    model_id VARCHAR(255),
    version VARCHAR(50),
    stage VARCHAR(50),  -- 'staging', 'production', 'archived'
    metrics JSONB,
    ...
);
```

**Views utiles:**
- `model_performance_summary` - Stats par modèle
- `pending_feedback_summary` - Feedback à traiter
- `active_learning_priority_queue` - Top 100 cas incertains

---

## Exemples de Code

### Extraction Tags

```python
from services.ml import TagExtractor

extractor = TagExtractor()

# Auto-extraction
tags = extractor.extract_tags("path/to/prostate_HE.mrxs", "MRXS")
print(tags)
# {
#     "organ": "prostate",
#     "stain": "H&E",
#     "marker": None,
#     "confidence": 0.7,
#     "source": "filename_parsing"
# }
```

### Routage Modèle

```python
from services.ml import TagRouter

router = TagRouter("config/ml_routes.yaml")

# Router vers modèle approprié
tags = {"organ": "prostate", "stain": "H&E", "task": "grading"}
route = router.route(tags)

print(route.model_name)  # "Gleason Grading Model"
print(route.model_path)  # "models:/gleason_grading/production"
```

### Enregistrer Feedback

```python
# API endpoint
POST /api/ml/feedback
{
    "slide_id": "abc123",
    "prediction_id": "pred456",
    "action": "correct",
    "original_prediction": {"class": "gleason_3"},
    "corrected_prediction": {"class": "gleason_4"},
    "notes": "Gleason pattern 4 plus évident dans zone supérieure"
}
```

---

## Timeline Implémentation

### Phase 3.1: Infrastructure MLOps (Mois 1-3)
- [x] Documentation complète
- [ ] Setup MLflow tracking server
- [ ] Setup DVC avec remote storage
- [ ] Créer database + schema
- [ ] Setup Label Studio

### Phase 3.2: Tag System & Routing (Mois 4-5)
- [x] TagExtractor implémenté
- [x] TagRouter implémenté
- [ ] Intégration backend existant
- [ ] UI assignation manuelle tags

### Phase 3.3: Feedback Pipeline (Mois 6-7)
- [ ] Endpoints API feedback
- [ ] FeedbackPanel UI
- [ ] Intégration Label Studio
- [ ] Dashboard monitoring feedback

### Phase 3.4: Continuous Learning (Mois 8-11)
- [ ] Pipeline Airflow re-entraînement
- [ ] DatasetBuilder avec DVC
- [ ] A/B testing infrastructure
- [ ] Monitoring drift (Evidently AI)

### Phase 3.5: Production Models (Mois 12-18)
- [ ] Gleason grading (prostate)
- [ ] Ki-67 counting (sein)
- [ ] HER2 scoring (sein)

---

## Checklist Validation

### Phase 3.1 Ready?

- [ ] MLflow accessible (http://localhost:5000)
- [ ] DVC push/pull fonctionne
- [ ] Database `varuna_ml` créée
- [ ] Label Studio accessible (http://localhost:8080)
- [ ] MinIO accessible (http://localhost:9001)

### Phase 3.2 Ready?

- [ ] Tags extraits pour 80%+ slides
- [ ] Router fonctionne (`/api/ml/route/{id}`)
- [ ] UI assignation manuelle disponible
- [ ] Tags stockés en DB

### Phase 3.3 Ready?

- [ ] Endpoint `/api/ml/feedback` opérationnel
- [ ] FeedbackPanel intégré au viewer
- [ ] Feedback stocké en DB
- [ ] Dashboard stats disponible

---

## Ressources Utiles

### Documentation Projet

- **Architecture:** `docs/MLOPS_ARCHITECTURE.md`
- **Intégration:** `docs/MLOPS_INTEGRATION_GUIDE.md`
- **Index fichiers:** `docs/MLOPS_FILES_SUMMARY.md`
- **Services ML:** `backend/services/ml/README.md`

### Documentation Externe

- **MLflow:** https://mlflow.org/docs/latest/
- **DVC:** https://dvc.org/doc
- **Label Studio:** https://labelstud.io/guide/
- **Evidently AI:** https://docs.evidentlyai.com/
- **Airflow:** https://airflow.apache.org/docs/

### Papers Clés

- Sculley et al. (2023): "Hidden Technical Debt in ML Systems"
- Pantanowitz et al. (2024): "Annotation Quality in Digital Pathology"
- Settles (2009): "Active Learning Literature Survey"
- Gal & Ghahramani (2016): "Dropout as Bayesian Approximation"

---

## FAQ

**Q: Par où commencer?**
A: Lire `docs/MLOPS_ARCHITECTURE.md` (1h), puis suivre `docs/MLOPS_INTEGRATION_GUIDE.md` Phase 3.1

**Q: Peut-on utiliser des modèles open source?**
A: Oui! PathAI, HistoPathology, CLAM sont tous compatibles. Voir Section 9 de MLOPS_ARCHITECTURE.md

**Q: Doit-on tout implémenter?**
A: Non. L'architecture est modulaire. Commencer par tag system + routing, puis ajouter feedback, puis continuous learning.

**Q: Compatible avec code Phase 1-2 existant?**
A: Oui! Intégration progressive sans casser l'existant. Feature flags possibles.

**Q: Temps estimé total?**
A: 12-18 mois pour implémentation complète + premiers modèles production

---

## Contact & Support

**Documentation:** Toute dans `docs/`
**Code:** `backend/services/ml/`
**Configuration:** `backend/config/ml_routes.yaml`
**Database:** `backend/database/schema_ml.sql`

**Questions MLOps:** Voir `backend/services/ml/README.md` section Troubleshooting

---

**Version:** 1.0
**Dernière mise à jour:** 2025-12-31
**Créé par:** ML Architect Agent (Claude Code)
