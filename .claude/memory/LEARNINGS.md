# Learnings - VarunaPoC

**But:** Capitaliser les decouvertes et eviter de repeter les erreurs.

---

## 2025-10-21 - BIF Direction LEFT Non Supporte

**Contexte:** Tentative d'ouvrir des lames Ventana BIF
**Probleme:** OpenSlide 4.0.0 echoue avec `Bad direction attribute "LEFT"`
**Solution:** Detection en amont, marquage `is_supported=False`, badge UI
**A Retenir:** Certains formats Ventana ont des variantes non standard. Toujours tester avec fichiers reels du CHU.
**Fichiers:** `backend/services/format_detector.py`, `docs/ERROR_BIF_DIRECTION_LEFT.md`

---

## 2025-10-21 - Emojis dans Logs Python

**Contexte:** Logs avec emojis pour lisibilite
**Probleme:** `UnicodeEncodeError` sur Windows (console cp1252)
**Solution:** Interdire les emojis dans print()/logging Python
**A Retenir:** Windows console ne supporte pas UTF-8 par defaut. Utiliser [OK], [FAIL] au lieu de emojis.
**Fichiers:** `CLAUDE.md` (regle ajoutee)

---

## 2025-10-28 - Structure MRXS Companion Directory

**Contexte:** Detection des lames 3DHistech
**Probleme:** `.mrxs` seul ne suffit pas, OpenSlide echoue silencieusement
**Solution:** Verifier existence du repertoire companion `slide_name/` avec `Slidedat.ini`
**A Retenir:** MRXS n'est PAS un fichier unique. C'est un index + repertoire de donnees.
**Fichiers:** `backend/services/format_detector.py` (fonction `_detect_mirax`)

---

## 2025-12-30 - OpenSeadragon Coordonnees Normalisees

**Contexte:** Implementation du SyncController pour multi-viewer
**Probleme:** Confusion entre coordonnees OSD (normalisees) et OpenSlide (pixels)
**Solution:** OSD utilise toujours width=1.0, height=aspect_ratio. Pas besoin de normaliser.
**A Retenir:**
- OSD: (0.0, 0.0) = coin haut-gauche, (1.0, height_ratio) = coin bas-droit
- OpenSlide: (0, 0) = coin haut-gauche, (width_px, height_px) = dimensions niveau 0
- Conversion: `pixel_x = osd_x * slide_width_level0`
**Fichiers:** `frontend/src/viewers/SyncController.js`, `frontend/src/utils/coordinates.js`

---

## 2025-12-30 - Event Suppression pour Eviter Boucles Infinies

**Contexte:** Synchronisation pan/zoom entre viewers
**Probleme:** Viewer A change → notifie B → B change → notifie A → boucle infinie
**Solution:** Flag `suppressViewportEvents` + lock dans SyncController
**A Retenir:** Tout systeme de sync bidirectionnel necessite un mecanisme de lock.
**Fichiers:** `frontend/src/viewers/ViewerInstance.js`, `frontend/src/viewers/SyncController.js`

---

## 2025-12-31 - OpenSlide Niveau Pyramide Inversion

**Contexte:** Tile serving pour OpenSeadragon
**Probleme:** OSD level 0 = lowest res, OpenSlide level 0 = highest res
**Solution:** Inversion: `openslide_level = max_level - osd_level`
**A Retenir:** Toujours verifier la convention de numerotation des niveaux pyramidaux.
**Fichiers:** `backend/services/tile_server.py`, `frontend/src/viewers/ViewerInstance.js`

---

## 2026-01-29 - Analyse Complete du Projet (Session Initiale)

**Contexte:** Creation du Cerveau d'Orchestration
**Decouvertes:**
1. **806 lignes non commitees** - Risque de perte de travail
2. **Securite score 0/10** - Aucune auth, critique pour production
3. **40+ fichiers documentation** - Bien documente mais a maintenir synchronise
4. **MLOps code pret** - `tag_extractor.py`, `tag_router.py` existent mais non connectes
5. **Design patterns solides** - Factory, Singleton, Observer, Mediator implementes

**A Retenir:**
- Toujours commiter regulierement
- Securite est le point faible critique
- L'architecture est bien pensee, le code MLOps attend integration
**Fichiers:** Cette session a analyse tout le projet

---

## 2026-01-29 - Pas de Signature Co-Authored-By

**Contexte:** Commit du Cerveau d'Orchestration
**Probleme:** Signature `Co-Authored-By` ajoutee automatiquement par Claude Code
**Solution:** L'admin ne veut PAS de cette signature dans les commits
**A Retenir:** **NE JAMAIS ajouter `Co-Authored-By` dans les messages de commit.** L'admin prefere des commits sans attribution a Claude.
**Fichiers:** Tous les commits futurs

---

## 2026-02-02 - Contenu Hors Contexte Archive par Erreur

**Contexte:** Restructuration du repository, archivage des fichiers Phase 2+
**Probleme:** Un dossier `Quick-restructure/` contenant un projet QUIC-Go (tunneling reseau, 74 fichiers, 58 Mo) a ete archive dans VarunaPoC sans questionnement
**Erreur:** Ce projet n'a AUCUN lien avec VarunaPoC (visualisation de lames histologiques). Technologies differentes (Go vs Python/JS), domaine different (reseau vs imagerie medicale).
**Solution:**
1. Supprimer le contenu hors contexte
2. Ajouter regle de validation dans BRAIN.md: "Detection des Actions Illogiques"
3. Toujours verifier la coherence thematique avant d'archiver/commiter
**A Retenir:**
- **TOUJOURS questionner** si un contenu semble hors sujet
- Verifier: "Ce fichier/dossier a-t-il un lien avec WSI/OpenSlide/imagerie medicale?"
- Si non, demander justification AVANT d'agir
- Un dossier dans le repertoire de travail n'appartient pas forcement au projet
**Fichiers:** `.claude/BRAIN.md` (nouvelle section "Detection des Actions Illogiques")

---

## 2026-02-05 - Port PostgreSQL 5433 (pas 5432)

**Contexte:** Installation PostgreSQL + PostGIS pour annotations
**Probleme:** Port 5432 deja occupe par TimescaleDB existant
**Solution:** Utiliser port 5433 partout: docker-compose.dev.yml, .env, .env.example, .env.phase1, alembic.ini, core/database.py (default fallback)
**A Retenir:** Toujours verifier les ports disponibles. Mettre a jour TOUS les fichiers de config si on change un port.
**Fichiers:** `docker-compose.dev.yml`, `.env*`, `backend/alembic.ini`, `backend/core/database.py`

---

## 2026-02-05 - dotenv dans alembic/env.py

**Contexte:** Alembic ne trouvait pas la bonne database URL
**Probleme:** `load_dotenv()` manquant dans `alembic/env.py` → fallback port 5432 au lieu de 5433
**Solution:** Ajouter `from dotenv import load_dotenv; load_dotenv()` en haut de `alembic/env.py`
**A Retenir:** Alembic ne charge PAS automatiquement .env. Il faut le faire explicitement.
**Fichiers:** `backend/alembic/env.py`

---

## 2026-02-05 - GeoAlchemy2 Auto-Index

**Contexte:** Migration 001 creait un index spatial
**Probleme:** GeoAlchemy2 cree automatiquement un index spatial sur les colonnes `Geometry`. Notre migration le creait aussi → index en double → erreur
**Solution:** Supprimer le `create_index` explicite de la migration
**A Retenir:** GeoAlchemy2 gere les index spatiaux automatiquement via le type `Geometry()`.
**Fichiers:** `backend/alembic/versions/001_create_annotations.py`

---

## 2026-02-05 - ForeignKey manquant sur label_id

**Contexte:** Annotation.label_id n'avait pas de ForeignKey
**Probleme:** SQLAlchemy relationship "label" echouait silencieusement sans `ForeignKey("annotation_labels.id")`
**Solution:** Ajouter ForeignKey + nettoyer __table_args__
**A Retenir:** Toujours verifier que les columns avec relationship ont leur ForeignKey explicite.
**Fichiers:** `backend/models/annotation.py`

---

## 2026-02-05 - async def vs def pour routes OpenSlide (CRITIQUE)

**Contexte:** Routes slides.py avec `async def` + I/O synchrone OpenSlide
**Probleme:** `async def` + code synchrone bloque l'event loop asyncio. 28 tiles prenaient 30s+ au lieu de ~2s.
**Solution:** Changer toutes les 6 routes de `async def` en `def`. FastAPI les execute alors dans le threadpool automatiquement.
**A Retenir:** **REGLE D'OR:** Si une route fait de l'I/O synchrone (OpenSlide, fichiers), utiliser `def` pas `async def`. FastAPI est intelligent et dispatche les `def` routes dans un threadpool.
**Fichiers:** `backend/routes/slides.py` (6 routes)

---

## 2026-02-05 - Keep-Alive TCP Essentiel sur Windows

**Contexte:** Tiles lentes meme apres fix async
**Probleme:** Sans keep-alive, chaque connexion TCP prend ~2s (Windows Defender HTTP inspection)
**Solution:** Browsers utilisent keep-alive par defaut. Premiere connexion lente (~2s), les suivantes en 0-13ms.
**A Retenir:** Ne pas desactiver keep-alive. Si les tiles sont lentes en dev, c'est probablement le premier chargement (cold connection).
**Fichiers:** `backend/routes/slides.py`

---

## 2026-02-05 - scan_slides_directory est Lent

**Contexte:** scan_slides_directory appelee dans les routes
**Probleme:** Prend ~1.5s car scan recursif + FormatDetector. Bloquait chaque requete.
**Solution:** Cacher le resultat dans `_slide_cache` de `get_slide_path_by_id()`. Ne jamais appeler directement dans les routes.
**A Retenir:** Les operations de scan sont couteuses. Toujours cacher les resultats.
**Fichiers:** `backend/routes/slides.py`, `backend/services/slide_scanner.py`

---

## 2026-02-06 - Event Listener Leaks (eventBus.off sans callback)

**Contexte:** Composants frontend detruits mais recevant encore des events
**Probleme:** `eventBus.off(event)` sans reference exacte du callback = no-op. Arrow functions dans `on()` + `off()` sans ref → listener jamais retire → composants morts crashent.
**Solution:** Stocker les unsubscribe functions retournees par `eventBus.on()` dans `this._unsubscribers[]`, appeler chacune dans `destroy()`.
**A Retenir:** **Pattern obligatoire pour tout composant frontend:**
```javascript
constructor() {
    this._unsubscribers = [];
    this._unsubscribers.push(eventBus.on(Events.X, (data) => this._handle(data)));
}
destroy() {
    this._unsubscribers.forEach(unsub => unsub());
}
```
**Fichiers:** LayerManager, AnnotationLayer, DrawingTools, HeatmapOverlay, MLPanel

---

## 2026-02-06 - detect_format() vs OpenSlide Open (Broken Slides)

**Contexte:** Certaines slides detectees par format_detector mais qui plantent a l'ouverture
**Probleme:** `openslide.detect_format()` peut reussir sur des fichiers corrompus (JPEG corrompu, main image manquante, images dissimilaires)
**Solution:** Ajouter helper `_try_open_slide()` dans format_detector.py. Tester l'ouverture reelle, pas juste la detection.
**A Retenir:** **`detect_format() ≠ peut ouvrir`**. Toujours valider avec un vrai `OpenSlide()` constructor.
**Fichiers corrompus decouverts:** Hamamatsu-1.ndpi, Leica-3.scn, Leica-Fluorescence-1.scn
**Fichiers:** `backend/services/format_detector.py`, `backend/routes/slides.py` (catch OpenSlideError → 422)

---

## 2026-02-06 - HeatmapOverlay Image Rechargee en Boucle

**Contexte:** HeatmapOverlay rechargeait l'image a chaque viewport-change
**Probleme:** Performance degradee, flickering
**Solution:** Cacher l'image dans `this._cachedImage`. Coordinate mapping via `tiledImage.getBounds(true)`.
**A Retenir:** Cacher les ressources lourdes (images, data) et ne les recharger que quand la source change.
**Fichiers:** `frontend/src/components/HeatmapOverlay.js`

---

## 2026-02-06 - ViewerPanel Double SLIDE_LOADED

**Contexte:** ViewerPanel.loadSlide() emettait SLIDE_LOADED, mais ViewerInstance aussi
**Probleme:** Double emission → double init des composants → bugs
**Solution:** Retirer l'emission de ViewerPanel, laisser ViewerInstance etre la seule source
**A Retenir:** Un seul composant doit etre la source de verite pour chaque event.
**Fichiers:** `frontend/src/components/ViewerPanel.js`, `frontend/src/viewers/ViewerInstance.js`

---

## 2026-02-08 - Documentation Drift Massive

**Contexte:** Mise a jour repo apres documents strategiques (PROPOSAL_VARUNA_v2, HOSPITAL_DEPLOYMENT_EVALUATION)
**Probleme:** README.md disait v0.1.0 Phase 1 avec 3 formats. Realite: v1.7.0 Phase 2 avec 10 formats, annotations, ML, 94 tests.
**Solution:** Reecriture complete README.md, PROJECT_STATE.md, ROADMAP.md, CONTEXT.md, FILES.md
**A Retenir:** Mettre a jour la documentation EN MEME TEMPS que le code. Ne pas laisser la doc diverger.
**Fichiers:** `README.md`, `.claude/memory/PROJECT_STATE.md`, `.claude/memory/ROADMAP.md`, `.claude/docs/CONTEXT.md`, `.claude/docs/FILES.md`

---

## 2026-02-08 - Processus de Propagation Obligatoire

**Contexte:** Le cerveau (.claude/) etait incoherent car les fichiers satellites n'etaient pas mis a jour apres chaque tache
**Probleme:** BRAIN.md v1.0 n'avait qu'une vague etape "Capitalisation" sans matrice de propagation. Resultat: 10 fichiers incoherents (versions differentes, agents inexistants, compteurs faux)
**Solution:** BRAIN.md v2.1 avec etapes 7 (Capitalisation) + 8 (Propagation), matrice de propagation explicite, carte des fichiers du cerveau, exemples concrets, seuil de declenchement
**A Retenir:** La capitalisation sans propagation = dette documentaire garantie. La matrice de propagation transforme une discipline floue en processus verifiable.
**Fichiers:** `.claude/BRAIN.md`, `MEMORY.md` (auto-memory)

---

## 2026-02-11 - OIDC PKCE Flow Complexity

**Contexte:** Implementation auth OIDC avec Keycloak
**Probleme:** Le flow PKCE necessite gestion de code_verifier, code_challenge, state, nonce, et redirection
**Solution:** AuthService.js encapsule tout le flow: generate PKCE pair, store in sessionStorage, handle callback, token refresh
**A Retenir:** OIDC PKCE est le standard mais la complexite est significative. Toujours utiliser un IdP (Keycloak, Azure AD) plutot que reinventer JWT custom.
**Fichiers:** `frontend/src/services/AuthService.js`, `backend/auth/oidc.py`, `backend/auth/jwt_validator.py`

---

## 2026-02-11 - Backward Compatibility AUTH_ENABLED=false

**Contexte:** L'auth ne doit pas bloquer le dev quand pas de Keycloak
**Probleme:** Si Keycloak down ou absent, impossible de travailler
**Solution:** `AUTH_ENABLED=false` (default) → anonymous ADMIN_TECHNIQUE, toutes les features disponibles. L'auth s'active uniquement via variable d'environnement.
**A Retenir:** Toujours prevoir un mode "sans auth" pour le dev. Les modules optionnels doivent etre opt-in, pas opt-out.
**Fichiers:** `backend/auth/__init__.py`, `backend/auth/dependencies.py`

---

## 2026-02-12 - Cohen's Kappa avec IoU Spatial Matching

**Contexte:** Calcul d'accord inter-annotateur pour annotations spatiales
**Probleme:** Les annotations sont des geometries (polygones, points, cercles), pas des labels simples. Comment associer les annotations de deux annotateurs?
**Solution:** IoU spatial matching via PostGIS: cross-join filtre par ST_Intersects (utilise GIST index), calcul IoU = ST_Area(ST_Intersection)/ST_Area(ST_Union), greedy best-match assignment
**A Retenir:** Pour kappa sur annotations spatiales, il faut d'abord "matcher" les annotations avant de comparer les labels. Le matching est le probleme difficile, pas le kappa.
**Fichiers:** `backend/quality/matching.py`, `backend/quality/metrics.py`

---

## 2026-02-12 - Fleiss' Kappa Uniform Matrix = -0.2

**Contexte:** Test unitaire Fleiss' kappa avec matrice uniforme [2,2,2]
**Probleme:** Attendait kappa=0 (pas d'accord) mais obtient kappa=-0.2
**Solution:** Mathematiquement correct: quand tous les annotateurs se repartissent uniformement entre N categories, c'est pire que le hasard dans le framework de Fleiss (systematic disagreement)
**A Retenir:** Kappa negatif = disagreement systematique, pas une erreur. Kappa=0 = hasard pur. Kappa=-1/(N-1) minimum theorique.
**Fichiers:** `backend/quality/metrics.py`, `backend/tests/test_quality_metrics.py`

---

## 2026-02-12 - Ruff per-file-ignores Glob Doesn't Match Deep Paths

**Contexte:** Ruff B008/ARG001 ignores pour routes FastAPI
**Probleme:** `"routes/**/*.py" = ["B008"]` dans ruff.toml ne couvre PAS `quality/routes.py` ni `auth/routes.py`
**Solution:** Ajouter chaque fichier route explicitement: `"quality/routes.py" = ["B008", "ARG001"]`
**A Retenir:** Les glob patterns ruff.toml sont relatifs au repertoire du fichier toml. `routes/**` ne couvre que le sous-dossier routes/, pas les modules au meme niveau.
**Fichiers:** `backend/ruff.toml`

---

## 2026-02-12 - Pre-commit ruff-format vs Black Formatter Conflict

**Contexte:** Long `# nosec B311 - Mock provider for testing` comments
**Probleme:** ruff-format et Black se battent sur le line-wrapping de ces longues lignes, creant un cycle infini de reformattage
**Solution:** Utiliser des commentaires nosec courts: `# nosec B311` (sans explication). Pour B615, pre-formater le line break manuellement.
**A Retenir:** Les commentaires nosec/noqa doivent etre courts. Si explication necessaire, la mettre sur la ligne precedente en commentaire separe.
**Fichiers:** `backend/services/ml/providers/mock_provider.py`, `backend/services/ml/providers/slideflow_provider.py`

---

## Template pour Nouvelles Entrees

```markdown
## [DATE] - [SUJET]

**Contexte:** [Ce qu'on essayait de faire]
**Probleme:** [Ce qui n'a pas marche]
**Solution:** [Ce qui a marche]
**A Retenir:** [Lecon pour le futur]
**Fichiers:** [Liste des fichiers concernes]
```

---

**Derniere mise a jour:** 2026-02-12
