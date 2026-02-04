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
**Probleme:** Signature `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>` ajoutee automatiquement
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

**Derniere mise a jour:** 2026-02-04
