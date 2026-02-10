# Memoire Persistante - VarunaPoC

**But:** Conserver le contexte entre sessions Claude Code pour economiser les tokens et eviter les erreurs repetees.

---

## Fichiers de Memoire

| Fichier | But | Quand Mettre a Jour |
|---------|-----|---------------------|
| **LEARNINGS.md** | Erreurs et solutions | Apres resolution d'un probleme non trivial |
| **DECISIONS.md** | Architecture Decision Records (20 ADRs) | Apres toute decision technique significative |
| **SOURCES.md** | References officielles | Quand on decouvre une nouvelle source utile |
| **PROJECT_STATE.md** | Etat actuel du projet | Debut de chaque session / apres changement majeur |
| **ROADMAP.md** | Plan MVP 15 semaines | Apres completion phase ou changement plan |

---

## Workflow de Consultation

### Au Debut d'une Session

```
1. Lire PROJECT_STATE.md
   → Comprendre ou en est le projet (v1.7.0, Phase 2 complete)
   → Voir les fichiers non commites
   → Connaitre les priorites

2. Si le probleme semble familier:
   → Chercher dans LEARNINGS.md (20+ entrees)
   → Eviter de refaire les memes erreurs

3. Si une decision technique est necessaire:
   → Verifier DECISIONS.md (20 ADRs)
   → Voir si un ADR existe deja
```

### Apres une Decouverte

```
1. Probleme resolu avec difficulte?
   → Ajouter entree dans LEARNINGS.md

2. Decision architecturale prise?
   → Ajouter ADR dans DECISIONS.md

3. Nouvelle source officielle utile?
   → Ajouter dans SOURCES.md
```

---

## Format des Entrees

### LEARNINGS.md

```markdown
## [DATE] - [SUJET]

**Contexte:** [Ce qu'on essayait de faire]
**Probleme:** [Ce qui n'a pas marche]
**Solution:** [Ce qui a marche]
**A Retenir:** [Lecon pour le futur]
**Fichiers:** [Liste des fichiers concernes]
```

### DECISIONS.md

```markdown
## ADR-[NNN]: [TITRE]

**Date:** YYYY-MM-DD
**Statut:** Propose | Accepte | Rejete | Obsolete
**Contexte:** [Pourquoi cette decision est necessaire]
**Decision:** [Ce qui a ete decide]
**Consequences:**
- (+) [Avantage 1]
- (-) [Inconvenient 1]
**Alternatives Rejetees:**
- [Option A]: [Raison du rejet]
**Validation Admin:** [Oui/Non/En attente]
```

### SOURCES.md

```markdown
### [Nom de l'Outil/Standard]
- **Site:** [URL principale]
- **Documentation:** [URL docs]
- **Usage:** [A quoi ca sert dans le projet]
```

---

## Regles d'Or

1. **Toujours consulter avant d'agir** - La memoire evite le travail redondant
2. **Toujours documenter les decouvertes** - Ce qui n'est pas ecrit est perdu
3. **Garder les entrees concises** - Juste assez de details pour etre utile
4. **Mettre a jour PROJECT_STATE.md** - Le snapshot doit rester actuel

---

## Index Rapide

### Par Domaine

**Backend:**
- Learnings: BIF Direction, MRXS Companion, Port 5433, dotenv Alembic, async→sync routes, scan_slides cache, detect_format vs open
- Decisions: ADR-002 (OpenSlide), ADR-003 (DZI), ADR-008 (MD5 Hash), ADR-009 (LRU Cache), ADR-016 (PostGIS), ADR-019 (sync def), ADR-020 (Slideflow+Phikon-v2)

**Frontend:**
- Learnings: OSD Coordonnees, Event Suppression, Event Listener Leaks, HeatmapOverlay cache, ViewerPanel double SLIDE_LOADED
- Decisions: ADR-001 (Vanilla JS), ADR-004 (EventBus), ADR-005 (Factory), ADR-006 (State), ADR-007 (SyncController), ADR-017 (Unsubscribe Pattern), ADR-018 (SVG Overlay)

**Securite:**
- Decisions: ADR-011 (RBAC + JWT) [propose]

**MLOps:**
- Decisions: ADR-012 (Tag Routing) [propose], ADR-020 (Slideflow+Phikon-v2) [accepte]

**Architecture:**
- Decisions: ADR-014 (Multi-Reader Scoring), ADR-015 (Specialistes)

**Orchestration:**
- Decisions: ADR-010 (Cerveau d'Orchestration)

**Organisation:**
- Decisions: ADR-013 (Archives/)
- Learnings: Contenu hors contexte, Documentation drift

---

**Derniere mise a jour:** 2026-02-08
