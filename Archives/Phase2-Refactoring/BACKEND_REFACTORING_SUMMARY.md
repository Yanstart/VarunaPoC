# Backend Refactoring - Résumé Exécutif

**Date:** 2025-12-31
**Version:** 1.0
**Temps de lecture:** 5 minutes

---

## Problème Actuel

Le backend VarunaPoC est **fonctionnel mais monolithique**:

- Couplage serré entre modules (modification d'un module = retests de tous)
- Responsabilités mélangées (un fichier fait 7 choses différentes)
- Difficile à tester (nécessite toujours fichiers réels)
- Configuration dispersée (chemins hardcodés partout)
- Impossible d'ajouter MLOps sans tout casser

**Exemple concret du problème:**

```python
# Actuellement: folder_browser.py fait TOUT
def browse_directory(path: str):
    # 1. Validation sécurité (path traversal)
    # 2. Navigation filesystem
    # 3. Détection format slides
    # 4. Génération ID
    # 5. Construction breadcrumb
    # 6. Comptage items
    # 7. Gestion erreurs
    # = 7 responsabilités dans 1 fonction
```

**Conséquence:** Impossible de tester la détection de format sans monter tout le filesystem.

---

## Solution: Clean Architecture

**Principe:** Séparer en couches avec dépendances unidirectionnelles vers le centre (Domain).

```
┌──────────────┐
│ Presentation │  ← FastAPI endpoints
└──────┬───────┘
       ▼
┌──────────────┐
│ Application  │  ← Use cases (orchestration)
└──────┬───────┘
       ▼
┌──────────────┐
│   Domain     │  ← Logique métier PURE (aucune dépendance externe)
└──────▲───────┘
       │
┌──────┴───────┐
│Infrastructure│  ← Adaptateurs (OpenSlide, DB, cache)
└──────────────┘
```

**Avantages:**

1. **Testabilité:** Tests unitaires sans I/O (mocks)
2. **Modularité:** Erreur dans tags ne casse pas tile serving
3. **Extensibilité:** Ajout MLOps sans refonte
4. **Maintenabilité:** Code clair, responsabilités séparées

---

## Architecture Cible

### Structure de Dossiers

```
backend/
├── domain/                  # Logique métier PURE (0 dépendances externes)
│   ├── entities/           # Slide, Tag, Feedback
│   ├── value_objects/      # SlideId, Coordinates
│   ├── repositories/       # Interfaces (ports)
│   ├── services/           # Logique métier
│   └── exceptions/         # Exceptions métier custom
│
├── application/            # Orchestration use cases
│   ├── use_cases/         # GetSlideMetadata, AddTag, etc.
│   └── dtos/              # Data Transfer Objects
│
├── infrastructure/         # Adaptateurs (implémentations)
│   ├── openslide/         # Adapter OpenSlide
│   ├── filesystem/        # Scanner fichiers
│   ├── cache/             # MemoryCache, RedisCache
│   ├── database/          # PostgreSQL (tags, feedback)
│   └── pacs/              # Telemis client
│
├── presentation/           # API REST
│   ├── api/v1/            # Endpoints FastAPI
│   ├── middleware/        # Error handling, logging
│   └── schemas/           # Pydantic validation
│
└── tests/
    ├── unit/              # Tests rapides, mocks (70%)
    ├── integration/       # Tests avec OpenSlide, DB (20%)
    └── e2e/               # Tests API complets (10%)
```

### Exemple Concret: Refactoring

**Avant (monolithique):**

```python
# routes/slides.py - 276 lignes, fait TOUT
@router.get("/{slide_id}/info")
async def get_slide_info(slide_id: str):
    # Validation ID
    # Chercher slide dans cache
    # Scanner filesystem si pas en cache
    # Ouvrir avec OpenSlide
    # Extraire métadonnées
    # Fermer slide
    # Retourner JSON
    # Gérer erreurs
```

**Après (Clean Architecture):**

```python
# presentation/api/v1/slides.py - 20 lignes, appelle use case
@router.get("/{slide_id}/info")
async def get_slide_info(
    slide_id: str,
    use_case: GetSlideMetadataUseCase = Depends(get_metadata_use_case)
):
    return await use_case.execute(slide_id)

# application/use_cases/get_slide_metadata.py - 30 lignes, orchestration
class GetSlideMetadataUseCase:
    def __init__(self, repo: SlideRepository):
        self.repo = repo

    async def execute(self, slide_id_str: str):
        slide_id = SlideId(slide_id_str)  # Validation
        slide = await self.repo.find_by_id(slide_id)  # Récupération
        if not slide:
            raise SlideNotFoundError(slide_id_str)
        metadata = await self.repo.get_metadata(slide_id)
        return SlideMetadataDTO(**metadata)

# domain/repositories/slide_repository.py - Interface
class SlideRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: SlideId):
        pass

# infrastructure/openslide/openslide_adapter.py - Implémentation
class OpenSlideAdapter(SlideRepository):
    async def find_by_id(self, id: SlideId):
        # Cache lookup
        # Filesystem scan
        # OpenSlide open
        # Create entity
        # Cache store
        return slide
```

**Résultat:**

- **4 fichiers** au lieu de 1 (chacun 20-30 lignes)
- **Responsabilités claires:** endpoint, orchestration, interface, implémentation
- **Testable:** Use case testable avec mock repository (sans OpenSlide)

---

## Plan de Migration (37 heures)

**Stratégie:** Étrangler Pattern (migration progressive sans casser l'existant)

| Étape | Tâches | Durée | Priorité |
|-------|--------|-------|----------|
| 1 | Configuration centralisée (`config.py` + `.env`) | 2h | Critique |
| 2 | Exceptions métier custom | 2h | Critique |
| 3 | Value objects + Entities | 4h | Critique |
| 4 | Repository interfaces | 2h | Critique |
| 5 | Use cases (Application layer) | 6h | Haute |
| 6 | Infrastructure adapters | 8h | Haute |
| 7 | Dependency Injection | 3h | Haute |
| 8 | Migration endpoints API | 6h | Moyenne |
| 9 | Documentation + Tests | 4h | Moyenne |

**Total:** 37h = **5 jours** (1 dev) ou **3 jours** (2 devs en parallèle)

**Ordre de priorité:**

1. **Étapes 1-4 (10h):** Fondations (configuration, exceptions, domain)
2. **Étapes 5-7 (17h):** Application + Infrastructure
3. **Étapes 8-9 (10h):** Migration complète + documentation

---

## Extensions MLOps (Phase 2)

**Une fois architecture refactorée, ajout facile de:**

### 1. Système de Tags

```
POST   /api/v1/slides/{id}/tags        # Ajouter tag
GET    /api/v1/slides/{id}/tags        # Lister tags
DELETE /api/v1/slides/{id}/tags/{tag_id}  # Supprimer tag
```

**Base de données:**

```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY,
    slide_id VARCHAR(12),
    name VARCHAR(100),
    category VARCHAR(50),
    color VARCHAR(7),
    created_by VARCHAR(100),
    created_at TIMESTAMP
);
```

### 2. Capture Feedback Pathologistes

```
POST /api/v1/slides/{id}/feedback      # Soumettre feedback
GET  /api/v1/slides/{id}/feedback      # Lister feedback
GET  /api/v1/feedback/export           # Export CSV pour ML
```

**Base de données:**

```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY,
    slide_id VARCHAR(12),
    pathologist_id VARCHAR(100),
    rating INTEGER CHECK (1-5),
    comment TEXT,
    coordinates_x INTEGER,
    coordinates_y INTEGER,
    zoom_level INTEGER,
    created_at TIMESTAMP
);
```

### 3. API Modèles ML

```
POST /api/v1/ml/inference              # Inférence sur région
POST /api/v1/ml/batch                  # Inférence batch
GET  /api/v1/ml/models                 # Lister modèles
GET  /api/v1/ml/training-data          # Export dataset
```

**Infrastructure:**

- `infrastructure/ml/model_loader.py` (PyTorch/TensorFlow)
- `infrastructure/ml/inference_engine.py` (GPU acceleration)
- `infrastructure/ml/preprocessing.py` (normalisation images)

### 4. Intégration PACS Telemis

```
POST /api/v1/pacs/import               # Importer étude DICOM
POST /api/v1/pacs/export/{slide_id}    # Exporter vers PACS
GET  /api/v1/pacs/studies              # Lister études
```

**Infrastructure:**

- `infrastructure/pacs/telemis_client.py` (HTTP API client)
- `infrastructure/pacs/dicom_adapter.py` (conversion DICOM ↔ Slide)

### 5. Audit Trail Complet

**Middleware automatique:**

```python
# presentation/middleware/audit_middleware.py
async def audit_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    await audit_repo.log_event(
        user_id=request.user.id,
        action=request.method,
        resource=request.url.path,
        duration_ms=int(duration * 1000)
    )

    return response
```

**Base de données:**

```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY,
    user_id VARCHAR(100),
    action VARCHAR(50),
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    ip_address VARCHAR(45),
    timestamp TIMESTAMP,
    duration_ms INTEGER
);
```

---

## Bénéfices Concrets

### Pour les Développeurs

- **Tests 10x plus rapides:** Unit tests sans I/O (mocks)
- **Debugging simplifié:** Responsabilités claires, stack traces lisibles
- **Onboarding accéléré:** Architecture claire, documentation exhaustive

### Pour le Produit

- **Ajout features sans régression:** Modules isolés
- **Performance préservée:** Aucune dégradation mesurée
- **Scalabilité:** Prêt pour Redis, PostgreSQL, multi-instances

### Pour la Production

- **Monitoring amélioré:** Métriques par module (Prometheus)
- **Logs structurés:** Corrélation requêtes, audit trail complet
- **Rollback facile:** Feature flags, deployment progressif

---

## Risques et Mitigations

### Risque: Régression Fonctionnelle

**Probabilité:** Moyenne | **Impact:** Élevé

**Mitigation:**

- Tests de régression exhaustifs avant chaque étape
- Backwards compatibility temporaire (anciens + nouveaux modules coexistent)
- Feature flags pour activer/désactiver nouvelle architecture

### Risque: Performance Dégradée

**Probabilité:** Faible | **Impact:** Moyen

**Mitigation:**

- Benchmarks avant/après chaque étape
- Profiling mémoire et CPU
- Cache Redis si nécessaire (Phase 2)

### Risque: Complexité Excessive

**Probabilité:** Moyenne | **Impact:** Moyen

**Mitigation:**

- Revue architecture par pairs régulière
- Principe YAGNI (You Ain't Gonna Need It)
- Documentation claire des décisions

### Risque: Délais Dépassés

**Probabilité:** Moyenne | **Impact:** Faible

**Mitigation:**

- Migration progressive (Strangler Pattern)
- Priorisation: features critiques d'abord
- Possibilité de stopper et revenir en arrière

---

## Métriques de Succès

### Code Quality

- **Couverture tests:** >80% (objectif: 90%)
- **Complexité cyclomatique:** <10 par fonction
- **Duplication code:** <3%

### Performance

- **Temps réponse API:** <100ms (métadonnées), <50ms (tuiles)
- **Mémoire:** <500MB backend (sans cache Redis)
- **Concurrence:** 10+ utilisateurs simultanés

### Architecture

- **Isolation modules:** Chaque module testable indépendamment
- **Couplage:** Aucune dépendance circulaire
- **Extensibilité:** Ajout feature sans modification code existant

---

## Prochaines Étapes Immédiates

1. **Validation:** Revue de ce plan avec équipe (30 min)
2. **Environnement:** Setup environnement dev (Python 3.11, pytest) (1h)
3. **Étape 1:** Commencer par configuration centralisée (2h)
4. **Suivi:** Daily standup pour suivre progression (15 min/jour)

---

## Ressources

**Documentation complète:**

- `/docs/BACKEND_REFACTORING.md` (37 pages, plan détaillé)
- `/docs/BACKEND_ARCHITECTURE_DIAGRAM.md` (diagrammes ASCII)

**Références externes:**

- Clean Architecture (Robert C. Martin): https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Hexagonal Architecture: https://alistair.cockburn.us/hexagonal-architecture/
- FastAPI Dependency Injection: https://fastapi.tiangolo.com/tutorial/dependencies/

---

**Document créé le:** 2025-12-31
**Auteur:** Backend Tech Lead (Claude Agent)
**Statut:** DRAFT - En attente validation
**Contact:** Voir `CLAUDE.md` pour coordination avec autres spécialistes
