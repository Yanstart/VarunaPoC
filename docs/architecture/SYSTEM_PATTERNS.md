# VarunaPoC - Patterns Architecturaux & Concepts Systeme

**Version:** 2.0 (Post-Phase 3.1)
**Date:** 2026-02-10
**Objectif:** Reference architecturale pour l'implementation des features futures:
versioning d'annotations, demande d'expertise croisee, commentaires, collaboration.

---

## Table des Matieres

1. [Vue d'Ensemble du Systeme](#1-vue-densemble)
2. [Patterns Backend](#2-patterns-backend)
3. [Patterns Frontend](#3-patterns-frontend)
4. [Modele de Donnees](#4-modele-de-donnees)
5. [Authentification & Autorisation](#5-authentification--autorisation)
6. [Audit Trail](#6-audit-trail)
7. [Communication Inter-Composants](#7-communication-inter-composants)
8. [Guide d'Extension](#8-guide-dextension)

---

## 1. Vue d'Ensemble

### 1.1 Architecture Globale

```
Browser (SPA)                    Backend (FastAPI)               Data
+-------------------+           +-------------------+          +-----------+
| Vite + Vanilla JS |  HTTP/    | FastAPI            |          | PostgreSQL|
| OpenSeadragon     | <------> | OpenSlide          | <------> | + PostGIS |
| EventBus          |  REST    | SQLAlchemy (async) |          | + JSONB   |
| OIDC PKCE         |  Bearer  | JWT Validation     |          |           |
+-------------------+  JWT     +-------------------+          +-----------+
                                       |
                               +-------v--------+
                               | Keycloak (dev)  |
                               | Azure AD (prod) |
                               +-----------------+
```

### 1.2 Principes Directeurs

1. **Modularite avec imports optionnels**: Chaque feature (annotations, auth, fhir, ml)
   est un module isole. Si ses dependances ne sont pas installees, le systeme demarre
   quand meme sans cette feature.

2. **Claims-based RBAC**: Les roles viennent du JWT (pas d'une table roles locale).
   Le backend valide les claims, jamais de logique metier sur les roles en DB.

3. **Event-driven frontend**: Tous les composants communiquent via un EventBus singleton.
   Aucun composant n'a de reference directe a un autre.

4. **Backward compatibility par defaut**: Toute nouvelle feature doit fonctionner en mode
   degrade quand sa config est absente (`AUTH_ENABLED=false`, `FHIR_ENABLED=false`, etc.).

---

## 2. Patterns Backend

### 2.1 Module Optionnel (Pattern Central)

Chaque module suit le meme pattern dans `main.py`:

```python
# Pattern: import optionnel avec flag
try:
    from auth import AUTH_ENABLED
    from auth import routes as auth_routes
    print(f"[INFO] Auth module loaded (AUTH_ENABLED={AUTH_ENABLED})")
except ImportError:
    AUTH_ENABLED = False
    auth_routes = None
    print("[INFO] Auth module disabled")

# ... plus tard ...
if auth_routes is not None:
    app.include_router(auth_routes.router)
```

**Modules suivant ce pattern:** annotations, auth, fhir, monitoring.

**Pour ajouter un nouveau module** (ex: comments, versioning, expertise):
1. Creer `backend/<module>/__init__.py` avec un flag `<MODULE>_ENABLED`
2. Creer `backend/<module>/routes.py` avec un `router = APIRouter(prefix="/api/<module>")`
3. Ajouter le try/except dans `main.py`
4. Ajouter le flag dans `.env.example`

### 2.2 Protection des Routes (FastAPI Depends)

Deux niveaux de protection:

```python
from auth.dependencies import get_current_user, require_role

# Niveau 1: Authentification (qui es-tu?)
@router.get("/slides/")
def list_slides(current_user: CurrentUser = Depends(get_current_user)):
    # current_user.sub, current_user.username, current_user.roles disponibles
    pass

# Niveau 2: Autorisation (as-tu le droit?)
@router.post("/annotations/")
async def create(
    current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE"))
):
    # Uniquement MEDECIN ou ADMIN_TECHNIQUE peuvent creer
    pass
```

**Comportement en mode anonyme (`AUTH_ENABLED=false`):**
- `get_current_user()` retourne `CurrentUser(sub="anonymous", roles=["ADMIN_TECHNIQUE"])`
- `require_role()` passe toujours (anonymous a ADMIN_TECHNIQUE)
- Tous les tests existants passent sans modification

**Break-glass:** Un user avec `break_glass_active=True` bypass la verification de role.
C'est un acces d'urgence limite a 30 minutes, logue en CRITICAL.

### 2.3 Extraction des Roles depuis JWT Claims

Le systeme supporte plusieurs formats de claims IdP via path dot-notation:

```python
def _extract_roles(claims: dict, role_claim: str) -> List[str]:
    # Keycloak: "realm_access.roles" → claims["realm_access"]["roles"]
    # Azure AD: "roles" → claims["roles"]
    parts = role_claim.split(".")
    value = claims
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, [])
        else:
            return []
    # Filtrage: seuls les 4 roles connus sont acceptes
    valid = {"LECTURE_SEULE", "INFIRMIER", "MEDECIN", "ADMIN_TECHNIQUE"}
    return [r for r in value if r in valid]
```

**Pour ajouter un nouveau role** (ex: REVIEWER, EXPERT):
1. Ajouter dans le set `valid` dans `dependencies.py`
2. Ajouter dans `role_priority` dans `schemas.py` > `CurrentUser.primary_role`
3. Ajouter dans le realm Keycloak (`realm-export.json`)
4. Ajouter dans le frontend `AuthService.js` > `primaryRole` getter

### 2.4 Service Layer Pattern

Les routes delegent la logique metier aux services:

```
routes/annotations.py       → annotations_service.py (CRUD)
routes/ml.py                → services/detection/ (pipeline)
routes/slides.py            → slide_scanner, tile_server, slide_loader
auth/routes.py              → break_glass, session_roaming, audit
```

**Convention:** Les routes sont minces. Elles valident les parametres (Pydantic),
appellent le service, et retournent la reponse. La logique metier est dans les services.

### 2.5 Database Pattern

```python
# ORM: SQLAlchemy 2.0 async + mapped_column
class Annotation(Base):
    __tablename__ = "annotations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    slide_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    geometry: Mapped[str] = mapped_column(Geometry(srid=0))  # PostGIS, pixels
    created_by: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=...)
    properties: Mapped[dict | None] = mapped_column(JSONB)  # Extensible

# Migrations: Alembic
# backend/alembic/versions/001_annotations.py
# backend/alembic/versions/002_auth_and_audit.py
```

**PostGIS avec SRID=0**: On utilise des coordonnees en pixels (pas geographiques).
SRID=0 indique que les coordonnees ne sont pas projetees.

**JSONB pour extensibilite**: Le champ `properties` (annotations) et `details` (audit)
stockent des donnees semi-structurees. C'est le point d'extension principal.

### 2.6 Schemas Pydantic (Validation)

Trois schemas par entite:
```python
class AnnotationCreate(BaseModel):   # Input creation
    geometry: GeoJSONGeometry
    label_id: UUID | None = None
    created_by: str | None = None

class AnnotationUpdate(BaseModel):   # Input modification (tout optionnel)
    geometry: GeoJSONGeometry | None = None
    label_id: UUID | None = None

class AnnotationResponse(BaseModel): # Output (from_attributes = True)
    id: UUID
    slide_id: str
    # ... tous les champs
    model_config = {"from_attributes": True}
```

---

## 3. Patterns Frontend

### 3.1 Singleton Pattern (Services)

Tous les services sont des singletons:

```javascript
let instance = null;

class AnnotationStore {
    constructor() {
        if (instance) return instance;
        this.annotations = new Map();
        instance = this;
    }
    static getInstance() {
        if (!instance) instance = new AnnotationStore();
        return instance;
    }
}

export const annotationStore = AnnotationStore.getInstance();
```

**Services singletons:** EventBus, ApiService, AuthService, AnnotationStore, ViewerManager.

### 3.2 EventBus (Observer/Pub-Sub)

Communication decouplees entre composants:

```javascript
// EventBus singleton - core/EventBus.js
const eventBus = EventBus.getInstance();

// Souscrire (retourne une fonction unsubscribe)
const unsub = eventBus.on(Events.ANNOTATION_CREATED, ({ annotation }) => {
    this._renderAnnotation(annotation);
});

// Emettre
eventBus.emit(Events.ANNOTATION_CREATED, { annotation });

// Desouscrire (CRITIQUE: stocker la ref pour cleanup)
unsub(); // ou: eventBus.off(Events.ANNOTATION_CREATED, callbackRef);
```

**Evenements definis dans `Constants.js`**, namespaces par domaine:
- `viewer:*` — lifecycle et navigation du viewer
- `slide:*` — chargement de lames
- `sync:*` — synchronisation multi-viewer
- `annotation:*` — CRUD annotations
- `tool:*` — outils de dessin
- `layer:*` — visibilite/opacite
- `detection:*` — pipeline ML detection
- `ml:*` — heatmap et predictions ML
- `auth:*` — login, logout, token refresh
- `ui:*` — navigation pages

### 3.3 Component Lifecycle (Create/Destroy)

Chaque composant suit ce pattern:

```javascript
class MyComponent {
    constructor(container, options) {
        this.element = document.createElement('div');
        container.appendChild(this.element);

        // IMPORTANT: stocker les unsubscribers pour cleanup
        this._unsubscribers = [];
        this._unsubscribers.push(
            eventBus.on(Events.SOME_EVENT, this._handleEvent.bind(this))
        );
    }

    destroy() {
        // 1. Retirer les event listeners
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];

        // 2. Retirer le DOM
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
        this.element = null;
    }
}
```

**Bug connu evite**: `eventBus.off(event)` sans callback est un no-op.
Il faut la reference exacte du callback. D'ou le pattern `_unsubscribers[]`.

### 3.4 State Management (appState)

L'etat global est dans `main.js`:

```javascript
const appState = {
    currentPage: Pages.HOME,     // Navigation
    selectedSlide: null,          // Slide en cours
    viewer: null,                 // Ref viewer OSD
    annotationLayer: null,        // SVG overlay
    drawingTools: null,           // Toolbar dessin
    mlPanel: null,                // Panneau ML
    // etc.
};
```

**cleanup()**: A chaque changement de page, on detruit explicitement tous les composants.
Les composants ne survivent pas entre les pages.

### 3.5 Role-Based UI Visibility

```javascript
function _applyRoleVisibility() {
    const canAnnotate = authService.hasRole('MEDECIN', 'ADMIN_TECHNIQUE');
    const canML = authService.hasRole('MEDECIN', 'ADMIN_TECHNIQUE');

    if (!canAnnotate && appState.drawingTools) {
        appState.drawingTools.element.style.display = 'none';
    }
    if (!canML) {
        const mlBtn = document.querySelector('#ml-btn');
        if (mlBtn) mlBtn.style.display = 'none';
    }
}
```

**Pattern**: Les composants sont crees pour tous les roles, mais masques
via `display: none` pour les roles qui n'y ont pas acces. Cela simplifie le code
(pas de branches conditionnelles a la creation).

### 3.6 Auth Flow (OIDC PKCE)

```
  Browser                  Backend               Keycloak
     |                        |                      |
     |-- init() ------------>|                      |
     |   GET /api/auth/me    |                      |
     |<-- {auth_enabled}-----|                      |
     |                        |                      |
     |-- login() ------------|--------------------->|
     |   redirect to /auth   |   Authorization      |
     |<--  code + state -----|<--  callback --------|
     |                        |                      |
     |-- _handleCallback() --|                      |
     |   POST /token         |   code + verifier    |
     |<-- access_token ------|<-- tokens ------------|
     |                        |                      |
     |-- API calls -----------|                      |
     |   Bearer: <token>     |                      |
     |                        |                      |
     |-- refreshTokenSilently()                     |
     |   (60s before expiry)  |                      |
```

**Tokens en localStorage** (pas sessionStorage): persistent entre onglets.
Refresh timer automatique 60 secondes avant expiration.

---

## 4. Modele de Donnees

### 4.1 Entites Actuelles

```
                                +-----------------+
                                |    users        |
                                | (synced IdP)    |
                                | sub (unique)    |
                                | username        |
                                | primary_role    |
                                | preferences {}  |
                                +--------+--------+
                                         |
              +--------------------------+---------------------------+
              |                          |                           |
   +----------v----------+   +----------v----------+   +------------v-----------+
   | annotations         |   | audit_events        |   | session_states         |
   | slide_id (indexed)  |   | timestamp (indexed) |   | user_sub (unique)      |
   | geometry (PostGIS)  |   | event_type (indexed)|   | state_data (JSONB)     |
   | annotation_type     |   | user_sub (indexed)  |   | saved_at               |
   | label_id (FK)       |   | level               |   +------------------------+
   | confidence          |   | action              |
   | properties (JSONB)  |   | details (JSONB)     |   +------------------------+
   | created_by          |   | ip_address          |   | break_glass_logs       |
   | created_at          |   | user_agent          |   | user_sub               |
   | updated_at          |   +---------------------+   | reason                 |
   +----------+----------+                              | expires_at             |
              |                                         | reviewed_by            |
   +----------v----------+                              +------------------------+
   | annotation_labels   |
   | name                |
   | color               |
   | category            |
   +---------------------+
```

### 4.2 Convention de Nommage

| Concept | Convention | Exemple |
|---------|-----------|---------|
| Table | `snake_case` pluriel | `annotations`, `audit_events` |
| Colonne | `snake_case` | `created_by`, `slide_id` |
| PK | UUID v4 | `id: UUID(as_uuid=True)` |
| FK | `<entite>_id` | `label_id`, `user_sub` |
| Timestamp | `DateTime(timezone=True)` | `created_at`, `updated_at` |
| Extensible | `JSONB` | `properties`, `details`, `preferences` |
| Geometrie | `Geometry(srid=0)` | PostGIS pixel coords |

### 4.3 JSONB comme Point d'Extension

Le pattern `JSONB` est crucial pour l'extensibilite sans migration:

```python
# Annotation.properties peut contenir n'importe quoi:
{
    "source": "ml_detection",
    "model": "phikon-v2",
    "uncertainty": 0.12,
    "review_status": "pending",      # futur: workflow review
    "version": 3,                     # futur: versioning
    "parent_id": "uuid-of-previous", # futur: historique
    "comments": [                     # futur: commentaires inline
        {"user": "dr.martin", "text": "A verifier", "at": "2026-02-10T10:00:00Z"}
    ]
}

# AuditEvent.details peut contenir le contexte:
{
    "reason": "Emergency patient access",
    "previous_role": "INFIRMIER",
    "slide_name": "patient_123_biopsy.svs"
}
```

---

## 5. Authentification & Autorisation

### 5.1 Les 4 Roles

| Role | Priorite | Slides | Annotations | ML | Admin |
|------|----------|--------|-------------|-----|-------|
| LECTURE_SEULE | 1 | View | View | - | - |
| INFIRMIER | 2 | View | View | - | - |
| MEDECIN | 3 | View | CRUD | Full | - |
| ADMIN_TECHNIQUE | 4 | View | CRUD | Full | Full |

**primary_role**: Quand un user a plusieurs roles, le plus haut en priorite est utilise
pour l'affichage. La verification (`has_role()`) teste toujours TOUS les roles.

### 5.2 CurrentUser Schema

```python
class CurrentUser(BaseModel):
    sub: str          # ID unique depuis IdP
    username: str     # Nom affiche
    email: str | None
    roles: List[str]  # Depuis JWT claims
    is_anonymous: bool = False
    break_glass_active: bool = False

    @property
    def primary_role(self) -> str:
        """Role de plus haute priorite."""

    def has_role(self, *roles: str) -> bool:
        """True si l'utilisateur a au moins un des roles specifies."""
```

### 5.3 Break-Glass (Acces d'Urgence)

```
Medecin a besoin d'un acces eleve pour une urgence patient:

1. POST /api/auth/break-glass {reason: "Urgence patient...", duration_minutes: 30}
2. Backend verifie: user est MEDECIN ou ADMIN_TECHNIQUE
3. Session in-memory creee (_active_sessions dict, PAS en DB)
4. Audit event CRITICAL logue
5. Pendant 30 min: break_glass_active=True bypass les checks de role
6. Apres expiration: session auto-nettoyee
7. ADMIN_TECHNIQUE peut GET /api/auth/break-glass pour voir les sessions actives
8. ADMIN_TECHNIQUE peut DELETE /api/auth/break-glass/{sub} pour revoquer
```

**Design intentionnel**: Sessions in-memory = perdues au restart du serveur.
C'est une feature de securite (pas un bug). En production, un restart revoque
tous les acces d'urgence.

---

## 6. Audit Trail

### 6.1 Structure WHO/WHAT/WHEN/WHERE/WHY

Chaque action significative est loguee:

| Dimension | Champ | Source |
|-----------|-------|--------|
| **WHO** | user_sub, username, user_role | JWT claims |
| **WHAT** | event_type, action, resource_type, resource_id | Route handler |
| **WHEN** | timestamp | datetime.now(UTC) |
| **WHERE** | ip_address, user_agent | Request headers |
| **WHY** | details (JSONB) | Contexte specifique |

### 6.2 Niveaux

| Niveau | Usage | Exemples |
|--------|-------|----------|
| INFO | Operations normales | Voir slide, creer annotation |
| WARNING | Operations suspectes | Auth echouee, role refuse |
| CRITICAL | Actions d'urgence | Break-glass, override admin |

### 6.3 Dual Persistence

```python
async def log_audit_event(...):
    event = {id, timestamp, level, event_type, user_sub, ...}

    # 1. DB PostgreSQL (primary, queryable)
    await _persist_to_db(event)

    # 2. JSON Lines file (fallback si DB indisponible)
    _persist_to_json(event)  # backend/logs/audit.jsonl
```

**Retention**: 6+ ans pour conformite clinique (HIPAA, RGPD).

### 6.4 Types d'Evenements

Definis dans `audit.py > AuditEvents`:

```python
# Auth:     LOGIN, LOGOUT, AUTH_FAILED, ROLE_DENIED
# Slides:   SLIDE_VIEWED, SLIDE_LISTED
# Annots:   ANNOTATION_CREATED, _UPDATED, _DELETED, _BATCH_CREATED
# ML:       ML_PREDICTION, ML_HEATMAP, ML_DETECTION
# Emergency: BREAK_GLASS_ACTIVATED, _EXPIRED, _REVIEWED
# Admin:    LABEL_CREATED, _UPDATED, _DELETED
# Session:  SESSION_SAVED, SESSION_RESTORED
```

---

## 7. Communication Inter-Composants

### 7.1 Frontend: EventBus

```
     +------------------+
     |    EventBus      |  (Singleton, core/EventBus.js)
     +--------+---------+
              |
    +---------+---------+---------+---------+
    |         |         |         |         |
AnnotLayer DrawTools  MLPanel   LayerMgr  CountPanel
    |         |         |         |         |
    v         v         v         v         v
  annotation:* tool:*  ml:*    layer:*   annotation:statsUpdated
```

**Regles:**
- Les composants ne s'importent jamais entre eux
- Toute communication passe par EventBus
- Les unsubscribers sont stockes et appeles dans `destroy()`
- Events.* sont typees dans Constants.js (pas de magic strings)

### 7.2 Frontend → Backend: ApiService

```javascript
// ApiService singleton injecte automatiquement le Bearer token
class ApiService {
    async _fetch(url) {
        const headers = {};
        this._injectAuthHeader(headers);  // Authorization: Bearer <token>
        const response = await fetch(url, { headers });

        if (response.status === 401) {
            // Tentative de refresh silencieux
            const refreshed = await authService.refreshTokenSilently();
            if (refreshed) {
                // Retry avec nouveau token
                this._injectAuthHeader(headers);
                return fetch(url, { headers });
            }
            // Redirect vers login
            window.location.href = '/';
        }
        return response;
    }
}
```

### 7.3 Backend: Depends() Injection

```
Request → FastAPI Router → Depends(get_current_user) → Route Handler
                               |
                               v
                        AUTH_ENABLED ?
                        /           \
                    false           true
                      |               |
                Anonymous User    JWT Validation
                (ADMIN_TECHNIQUE)  → OIDC Discovery
                                   → JWKS Cache
                                   → Role Extraction
                                   → Break-Glass Check
```

---

## 8. Guide d'Extension (Features Futures)

### 8.1 Versioning d'Annotations

**Objectif**: Garder l'historique complet de chaque modification d'annotation.

**Approche recommandee** (Event Sourcing leger):

```python
# Nouvelle table: annotation_versions
class AnnotationVersion(Base):
    __tablename__ = "annotation_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    annotation_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("annotations.id"))
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry: Mapped[str] = mapped_column(Geometry(srid=0))  # Snapshot
    properties: Mapped[dict | None] = mapped_column(JSONB)   # Snapshot
    changed_by: Mapped[str] = mapped_column(String(200))     # user_sub
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    change_type: Mapped[str] = mapped_column(String(20))     # create, update, delete
    change_details: Mapped[dict | None] = mapped_column(JSONB)  # Diff ou raison

    annotation = relationship("Annotation", backref="versions")
```

**Points d'integration:**
- `routes/annotations.py > create_annotation`: Creer version 1
- `routes/annotations.py > update_annotation`: Creer version N+1 avec snapshot avant
- `routes/annotations.py > delete_annotation`: Creer version "delete" (soft delete)
- Nouveau endpoint: `GET /api/annotations/{slide_id}/{annotation_id}/history`
- Frontend: Timeline dans le panneau info de l'annotation selectionnee

**Audit**: Chaque version genere un `ANNOTATION_UPDATED` ou `ANNOTATION_CREATED` audit event.
Le champ `details` de l'audit peut contenir le diff.

### 8.2 Demande d'Expertise Croisee

**Objectif**: Un medecin peut demander l'avis d'un specialiste sur une annotation
ou une region de la lame.

**Modele de donnees:**

```python
class ExpertiseRequest(Base):
    __tablename__ = "expertise_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    slide_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    annotation_id: Mapped[uuid.UUID | None] = mapped_column(UUID, nullable=True)
    requester_sub: Mapped[str] = mapped_column(String(500), nullable=False)
    expert_sub: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Null = any expert
    status: Mapped[str] = mapped_column(String(20), default="pending")
      # pending → assigned → in_review → completed → archived
    priority: Mapped[str] = mapped_column(String(20), default="normal")
      # normal, urgent, critical
    question: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    viewport_state: Mapped[dict | None] = mapped_column(JSONB)  # Snapshot position viewer
    created_at: Mapped[datetime]
    responded_at: Mapped[datetime | None]
    details: Mapped[dict | None] = mapped_column(JSONB)  # Extensible
```

**Points d'integration:**
- Nouveau module `backend/expertise/` (meme pattern que `auth/`)
- Routes: `POST /api/expertise/request`, `GET /api/expertise/pending`,
  `PUT /api/expertise/{id}/respond`, `GET /api/expertise/{id}`
- Protection: `require_role("MEDECIN", "ADMIN_TECHNIQUE")` pour creer/repondre
- `viewport_state`: Sauvegarde la position exacte du viewer (zoom, centre) pour
  que l'expert voie exactement la meme region que le demandeur.
  Meme structure que `SessionStateData` dans `auth/schemas.py`.
- Audit events: `EXPERTISE_REQUESTED`, `EXPERTISE_RESPONDED`, `EXPERTISE_ASSIGNED`
- Frontend: Bouton "Demander un avis" dans le menu contextuel d'une annotation
  ou dans la toolbar. Panneau "Avis en attente" dans le sidebar.

**Notifications** (futur): Quand l'expert repond, notifier le demandeur.
Peut commencer par polling (`GET /api/expertise/pending?for_user=me`),
evoluer vers WebSocket plus tard.

### 8.3 Commentaires (sur Annotations)

**Objectif**: Discussion collaborative sur une annotation specifique.

**Approche 1 (rapide, JSONB):**
Stocker les commentaires dans `annotation.properties.comments`:

```json
{
    "comments": [
        {
            "id": "uuid",
            "user_sub": "dr.martin",
            "username": "Dr. Martin",
            "text": "Cette zone merite une biopsie complementaire",
            "created_at": "2026-02-10T10:00:00Z",
            "edited_at": null
        }
    ]
}
```

**Avantage**: Zero migration, zero nouvelle table.
**Limite**: Pas de requetes SQL sur les commentaires, pas d'index.

**Approche 2 (robuste, table dediee):**

```python
class AnnotationComment(Base):
    __tablename__ = "annotation_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True)
    annotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID, ForeignKey("annotations.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID, nullable=True)  # Thread
    user_sub: Mapped[str] = mapped_column(String(500), nullable=False)
    username: Mapped[str] = mapped_column(String(200), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime]
    edited_at: Mapped[datetime | None]
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    annotation = relationship("Annotation", backref="comments")
```

**Recommandation**: Commencer par Approche 1 (JSONB) pour le PoC. Migrer vers
Approche 2 quand le volume de commentaires justifie l'indexation.

**Points d'integration:**
- Routes: `POST /api/annotations/{slide_id}/{id}/comments`,
  `GET /api/annotations/{slide_id}/{id}/comments`,
  `PUT /api/annotations/{slide_id}/{id}/comments/{comment_id}`
- Frontend: Panneau commentaires dans le detail d'une annotation selectionnee
- Nouvel event: `Events.COMMENT_ADDED = 'comment:added'`
- Audit: `COMMENT_CREATED`, `COMMENT_EDITED`

### 8.4 Checklist pour Toute Nouvelle Feature

1. **Backend module** (si significatif):
   - [ ] `backend/<module>/__init__.py` avec `<MODULE>_ENABLED` flag
   - [ ] `backend/<module>/routes.py` avec `APIRouter(prefix="/api/<module>")`
   - [ ] `backend/<module>/schemas.py` (Pydantic Create/Update/Response)
   - [ ] Import optionnel dans `main.py` (try/except)
   - [ ] `.env.example` mis a jour

2. **Database** (si persistent):
   - [ ] Model ORM dans `backend/<module>/models.py` ou `backend/models/`
   - [ ] Migration Alembic `backend/alembic/versions/00X_<feature>.py`
   - [ ] Import optionnel dans `backend/models/__init__.py`
   - [ ] JSONB pour champs extensibles

3. **Auth** (si protege):
   - [ ] `Depends(get_current_user)` sur toutes les routes
   - [ ] `Depends(require_role(...))` sur les routes en ecriture
   - [ ] Verifier backward compat: tests passent avec `AUTH_ENABLED=false`

4. **Audit** (si significatif):
   - [ ] Nouveaux event types dans `AuditEvents`
   - [ ] `await log_audit_event(...)` dans les handlers critiques
   - [ ] Niveau correct: INFO (normal), WARNING (suspect), CRITICAL (urgence)

5. **Frontend** (si visible):
   - [ ] Composant avec pattern constructor/destroy
   - [ ] Events dans `Constants.js`
   - [ ] Unsubscribers stockes dans `_unsubscribers[]`
   - [ ] Role-based visibility dans `_applyRoleVisibility()`
   - [ ] Cleanup dans `main.js > cleanup()`

6. **Tests**:
   - [ ] Tests unitaires du module (pytest)
   - [ ] Verifier 125+ tests existants passent toujours
   - [ ] Test avec `AUTH_ENABLED=false` et `AUTH_ENABLED=true`

---

## Annexe A: Fichiers Cles par Couche

### Backend Core
| Fichier | Role |
|---------|------|
| `backend/main.py` | Entry point, imports optionnels, lifespan, CORS |
| `backend/core/database.py` | SQLAlchemy async engine, sessions |
| `backend/routes/slides.py` | 6 routes slides (sync def, pas async) |
| `backend/routes/annotations.py` | CRUD annotations + labels |
| `backend/routes/ml.py` | Predict, heatmap, detect, batch |

### Backend Auth
| Fichier | Role |
|---------|------|
| `backend/auth/__init__.py` | `AUTH_ENABLED` flag |
| `backend/auth/dependencies.py` | `get_current_user()`, `require_role()` |
| `backend/auth/jwt_validator.py` | JWT decode + verify |
| `backend/auth/oidc.py` | JWKS cache, OIDC discovery |
| `backend/auth/audit.py` | Dual DB+JSON audit logging |
| `backend/auth/break_glass.py` | Emergency in-memory sessions |
| `backend/auth/session_roaming.py` | Cross-workstation state |

### Frontend Core
| Fichier | Role |
|---------|------|
| `frontend/src/main.js` | Entry point, pages, appState, cleanup |
| `frontend/src/core/EventBus.js` | Singleton pub/sub |
| `frontend/src/core/Constants.js` | Events, API, Pages, Config |
| `frontend/src/services/ApiService.js` | HTTP client + Bearer injection |
| `frontend/src/services/AuthService.js` | OIDC PKCE flow |
| `frontend/src/services/AnnotationStore.js` | Client-side annotation state |

### Frontend Components
| Fichier | Role |
|---------|------|
| `frontend/src/components/AnnotationLayer.js` | SVG overlay sur OSD |
| `frontend/src/components/DrawingTools.js` | Rectangle, Polygon, etc. |
| `frontend/src/components/LayerManager.js` | Visibility/opacity toggles |
| `frontend/src/components/DetectionPanel.js` | ML detection workflow |
| `frontend/src/components/CountingPanel.js` | Annotation statistics |
| `frontend/src/components/MLPanel.js` | Predict, heatmap controls |
| `frontend/src/components/HeatmapOverlay.js` | Canvas overlay sur OSD |
| `frontend/src/components/LoginPage.js` | OIDC login redirect |
| `frontend/src/components/UserMenu.js` | User dropdown + actions |

---

## Annexe B: Conventions de Code

### Backend
- **Python 3.12+**, type hints partout
- **Routes sync** pour I/O OpenSlide (threadpool FastAPI), **async** pour DB
- **Imports optionnels** pour nouvelles deps
- **filterwarnings** dans `pyproject.toml` pour scipy/numpy compat

### Frontend
- **Vanilla JS** (pas de framework), ES6+ modules
- **Singleton** pour les services, **Factory** pour les viewers
- **CSS custom properties** (dark theme: `--color-bg-base`, `--color-primary`, etc.)
- **No emojis** sauf demande explicite utilisateur

### Git
- Branch `feature/slideflow-integration` (dev principal)
- Branch `main` pour les releases
- Commit messages: `feat(scope):`, `fix(scope):`, `docs:`, `test:`
