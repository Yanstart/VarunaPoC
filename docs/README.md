# VarunaPoC — Documentation

Index central de la documentation du projet VarunaPoC.

> Pour démarrer rapidement : voir [`Admin/`](./Admin/) (déploiement) ou
> [`Manuel/`](./Manuel/) (utilisation clinicienne).

---

## Par audience

| Vous êtes... | Commencer par |
|---|---|
| **Clinicien·ne / utilisateur·rice final·e** | [`Manuel/`](./Manuel/) |
| **Administrateur·rice / IT hôpital** | [`Admin/`](./Admin/) |
| **Développeur·euse backend / frontend** | [`architecture/MODULAR_ARCHITECTURE.md`](./architecture/MODULAR_ARCHITECTURE.md) |
| **DevOps / SRE** | [`Admin/INFRASTRUCTURE.md`](./Admin/INFRASTRUCTURE.md) puis [`Deployment/`](./Deployment/) |
| **Auditeur·rice conformité** | [`standards/`](./standards/) |

---

## Index par dossier

### [`Admin/`](./Admin/) — Manuel administrateur
Topologie réseau, profils Compose, fiches par service, opérations courantes.
**Doc canonique pour déployer et opérer.**

| Page | Contenu |
|---|---|
| [README.md](./Admin/README.md) | Index + quickstart dev/prod |
| [INFRASTRUCTURE.md](./Admin/INFRASTRUCTURE.md) | Topologie, ports, volumes, healthchecks, hardware |
| [PROFILES.md](./Admin/PROFILES.md) | Quand activer/désactiver chaque profil Compose |
| [DEPLOYMENT.md](./Admin/DEPLOYMENT.md) | Procédure complète (workstation → prod hôpital) |
| [OPERATIONS.md](./Admin/OPERATIONS.md) | Backup/restore, logs, troubleshooting |
| [services/](./Admin/services/) | Une fiche par conteneur |

### [`architecture/`](./architecture/) — Architecture technique

| Page | Contenu |
|---|---|
| [README.md](./architecture/README.md) | Statut courant + index architecture |
| [MODULAR_ARCHITECTURE.md](./architecture/MODULAR_ARCHITECTURE.md) | **Canonique** — 6 Protocols, Strangler Fig, sprint log |
| [ARCHITECTURE_V3.md](./architecture/ARCHITECTURE_V3.md) | Vision systeme V3 (diagrammes C4) |
| [SYSTEM_PATTERNS.md](./architecture/SYSTEM_PATTERNS.md) | Patterns implémentés (Factory, Strategy, EventBus) |
| [MODULE_CONTRACTS.md](./architecture/MODULE_CONTRACTS.md) | Contrats d'interface entre modules |
| [REFACTORING_PLAN.md](./architecture/REFACTORING_PLAN.md) | Plan migration Clean Architecture |
| [READER_SELECTION_SYSTEM.md](./architecture/READER_SELECTION_SYSTEM.md) | Sélection des lecteurs WSI |
| [QUICK_START_MODULAR.md](./architecture/QUICK_START_MODULAR.md) | Quickstart architecture modulaire |
| [IMPLEMENTATION_REPORT.md](./architecture/IMPLEMENTATION_REPORT.md) | Rapport implémentation pour management |
| [INTEGRATION_SUMMARY.md](./architecture/INTEGRATION_SUMMARY.md) | Résumé intégrations (Slideflow, FHIR, DICOM) |

### [`Manuel/`](./Manuel/) — Manuel utilisateur clinicien
Guides en français pour les utilisateurs finaux (médecins, chercheurs).

01-INTRODUCTION → 08-QUALITE + 99-FAQ. Voir [`Manuel/README.md`](./Manuel/README.md).

### [`Deployment/`](./Deployment/) — Guides spécifiques CHU
Runbooks production, secrets management, breakglass, integration Telemis,
monitoring, scénarios réseau hospitaliers.

### [`Infrastructure/`](./Infrastructure/) — CI/CD
Guides GitHub Actions, runner self-hosted, pipeline.

### [`adr/`](./adr/) — Architecture Decision Records
Décisions techniques majeures (slide ID MD5, modules optionnels, PostGIS, …).

### [`implementation/`](./implementation/) — Notes d'implémentation
Patches et fixes documentés (BIF LEFT, OIDC token injection, MPP fallback, …).

### [`operations/`](./operations/)
Procédures opérationnelles (chiffrement au repos, …).

### [`research/`](./research/)
Notes d'enquêtes (interviews pathologistes, workflows annotation).

### [`standards/`](./standards/) — Conformité réglementaire
EU AI Act, FDA 510(k), Health Canada MDL, US TEFCA, China data localization,
certificats Belgian eHealth.

### [`plans/`](./plans/)
Plans actifs uniquement. Plans clos (Waves 1-4) → `Archives/plans-historiques/`.

---

## Documents racine `docs/`

| Document | Rôle |
|---|---|
| [PROPOSAL_VARUNA_v2.md](./PROPOSAL_VARUNA_v2.md) | Vision projet, analyse marché, roadmap |
| [PROTOCOLE.md](./PROTOCOLE.md) | Spécification protocole hôpital (Telemis, eHealth) |
| [ML_INTEGRATION.md](./ML_INTEGRATION.md) | Architecture ML / Slideflow / Phikon-v2 |
| [ML_COMPATIBILITY.md](./ML_COMPATIBILITY.md) | Compatibilité ML par format WSI |
| [FORMATS_SUPPORTED.md](./FORMATS_SUPPORTED.md) | 10 formats supportés |
| [ECOSYSTEM_MAP.md](./ECOSYSTEM_MAP.md) | Cartographie écosystème WSI |
| [ANALYSE_DIRECTION_PROJET.md](./ANALYSE_DIRECTION_PROJET.md) | Stratégie long-terme |
| [ETUDE_SOLUTIONS_EXISTANTES.md](./ETUDE_SOLUTIONS_EXISTANTES.md) | Analyse Cytomine/DSA/QuPath |
| [ERROR_BIF_DIRECTION_LEFT.md](./ERROR_BIF_DIRECTION_LEFT.md) | Bug OpenSlide BIF Ventana |
| [ERROR_TEMPLATE.md](./ERROR_TEMPLATE.md) | Template documentation d'erreur |

---

## Convention errors documentés

Quand une erreur nécessite recherche + workaround, on crée un `ERROR_[NOM].md`
en suivant [`ERROR_TEMPLATE.md`](./ERROR_TEMPLATE.md). Cible :

- Cause racine documentée
- Recherches effectuées archivées
- Workaround référencé dans le code (commentaire pointant vers le fichier)

Ne pas créer un `ERROR_*.md` pour les bugs triviaux résolus immédiatement.

---

**Dernière mise à jour :** 2026-05-07
