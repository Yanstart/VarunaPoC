# Audit — Modèle de données Annotations (revue prod-grade)

**Date :** 2026-05-27
**Niveau d'analyse :** Production en pathologie numérique (cadre EU MDR / EU AI Act / FDA 21 CFR 11)
**Auteur :** Revue collaborative menée pendant la consolidation `fix/auth-infra-hardening`
**Statut :** Audit figé — issues GitHub ouvertes en réponse

---

## 1. Objectif

Évaluer si la modélisation actuelle des **annotations**, **corrections** et de leur lien avec les **modèles d'IA** est suffisante pour :

1. **Persister efficacement** les annotations cliniques (geometry, label, statut, audit)
2. **Manipuler les annotations** en lecture batch, en export training-ready, en bulk import
3. **Alimenter un pipeline d'entraînement continu** : chaque correction humaine sur une prédiction IA doit pouvoir nourrir la prochaine version du modèle de manière **traçable** et **reproductible**
4. **Tenir les exigences réglementaires** : auditabilité, immutabilité du log, traçabilité des décisions algorithmiques, isolation multi-tenant garantie au niveau base de données

Cet audit **précède** toute implémentation de fonctionnalité dépendante (recherche de similarité, dashboards qualité, fine-tuning automatisé). Il est explicitement référencé par les issues GitHub en réponse.

---

## 2. Ce que le schéma actuel fait bien

| Élément | Pertinence prod |
|---|---|
| `annotations.geometry` PostGIS + index GIST | ✅ Requêtes spatiales O(log n) |
| `tenant_id` sur chaque table + index composites | ✅ Multi-établissement préparé applicativement |
| `annotation_type` (manual / auto / auto_confirmed) | ✅ Distingue origine humaine et IA validée |
| Table `corrections` séparée | ✅ Décorrèle l'acte de correction de l'objet corrigé |
| `correction_type` (confirmed / rejected / refined / relabeled) | ✅ Sémantique exploitable |
| `rejection_reason` énuméré en 5 catégories typées | ✅ Signal de drift / training catégorisable |
| `model_name + model_version` sur Correction | ✅ Audit possible par version de modèle |
| `confidence` (float) sur Annotation | ✅ Permet sélection par seuil pour training |
| `JSONB properties / metadata_extra` | ⚠️ Extensible mais sans validation de schéma |
| `status` (pending / validated / rejected) + `validated_by`, `validated_at` | ✅ Workflow basique tracé |

---

## 3. Gap analysis — 12 problèmes structurels (G1 → G12)

Classés par criticité métier.

### Critique pour l'entraînement continu

| ID | Problème | Impact |
|---|---|---|
| **G1** | Annotations `auto` / `auto_confirmed` ne mémorisent **pas** quel modèle les a produites | Impossible de reconstituer le training set d'une future version du modèle. Bloque #340, #341, #346, #347. |
| ~~**G2**~~ ✅ **RESOLVED** par #370 | ~~Pas de registre `ml_models`~~ — table `ml_models` créée (migration 010), 8 endpoints CRUD (dont `/global` séparé pour ADMIN), seeder Phikon-v2, audit hooks. Couverture schémas Pydantic 100 % (22 unit tests). Tests d'intégration livrés mais hang dans le container backend à cause de la conftest, suivi par #371. Voir `docs/Admin/services/ml-models-registry.md`. | Ambiguïtés (`"resnet50"` vs `"ResNet50"`), pas de FK, pas de hash de checkpoint |
| **G3** | Pas de snapshot du training dataset | Impossible de figer « voici les N annotations utilisées pour entraîner v2.3 ». Non reproductible. |
| **G4** | Pas d'événement explicite déclenchant le retraining | Le pipeline « M corrections sur modèle X → retrain » n'est pas modélisé |
| **G10** | Pas de référence aux **tiles** que le modèle a utilisées pour produire son score | Manque pour l'explicabilité AI Act (« pourquoi le modèle a-t-il marqué cette région ? ») |

### Critique pour la conformité réglementaire

| ID | Problème | Impact |
|---|---|---|
| **G5** | Pas d'historique shadow des annotations (`updated_at` seul) | Une modification écrase l'état précédent. EU MDR Annexe VIII et FDA 21 CFR 11 demandent un historique inviolable. |
| **G6** | Audit log éditable par un DBA avec les bons droits | Pas immuable. Standard prod = append-only WORM + chaîne de hashes signés. |
| **G7** | Filtre `tenant_id` uniquement applicatif | Un dev oublie un `WHERE`, un hôpital voit les données d'un autre. PostgreSQL RLS = garde-fou DB-side. |
| **D4** | Champ `notes` (String 2000) accepte du PII en clair | Risque RGPD : « Patient X, suspicion lymphome » en clair dans la DB. Pas de chiffrement, pas de filtre. |

### Important pour la qualité diagnostique

| ID | Problème | Impact |
|---|---|---|
| **G8** | Pas de modèle multi-rater explicite (session, tâche, consensus) | Le module `quality/` calcule des kappa mais sans structure de session |
| **G9** | `properties` et `metadata_extra` JSONB sans validation de schéma | Drift de structure inéluctable au fil du temps |

### Manipulation / efficacité

| ID | Problème | Impact |
|---|---|---|
| **G11** | Pas d'export training-ready (COCO / GeoJSON / Pascal VOC) | Impossible de passer le dataset à un pipeline Slideflow / MONAI sans réécriture manuelle |
| **G12** | Pas d'endpoint bulk insert / COPY | Ingestion par REST = O(1 row = 1 HTTP), inefficace pour ré-importer un export QuPath |

---

## 4. Décisions structurantes (D1-D4)

Choix qui dépendent du métier, pas de la technique :

| ID | Décision à prendre |
|---|---|
| **D1** | Granularité de l'audit immuable (toutes actions / annotations seulement / annotations + lectures sensibles) |
| **D2** | Politique de retraining (seuil de drift, taux de rejet, décision manuelle) |
| **D3** | Mode multi-rater (parallèle indépendant, double validation séquentielle, arbitrage à 3) |
| **D4** | Traitement du PII dans `notes` (interdiction + filtre, chiffrement at-rest, externalisation FHIR) |

Ces décisions structurent les implémentations. Elles **doivent** être prises avant le code, et documentées dans l'ADR correspondant.

---

## 5. Mapping vers le backlog GitHub

L'audit a été comparé aux issues ouvertes au 2026-05-27. La majorité des gaps est déjà cartographiée.

| Gap | Issue existante | Issue nouvelle |
|---|---|---|
| G1 — Provenance modèle sur annotations IA | ❌ | **N1** (cette série) |
| G2 — Registre `ml_models` | #346 | — |
| G3 — Dataset snapshots reproductibles | Partiel #347 | **N3** (clarification + figement) |
| G4 — Pipeline retraining auto | #339, #340, #341 | — |
| G5 — History shadow annotations | #331, #337 | — |
| G6 — Audit immuable WORM | Partiel #349 | **N6** (implémentation explicite) |
| G7 — RLS PostgreSQL | #354 | — |
| G8 — Multi-rater workflow | #336 | — |
| G9 — Pydantic schema sur properties JSONB | ❌ | **N2** |
| G10 — `source_tile_refs` | ❌ | Fusionné dans N1 |
| G11 — Export training-ready | ❌ | **N3** |
| G12 — Bulk import annotations | ❌ | **N4** |
| D4 — PII protection `notes` | ❌ | **N5** |

**Six issues nouvelles** (N1 → N6) ouvertes en réponse à cet audit.

---

## 6. Schéma cible (production-grade)

```
┌─ ml_models ──────────────────────────────────────────┐  ← G2 / #346
│  id (uuid, pk)                                       │
│  name, version (text, UNIQUE ensemble)               │
│  checkpoint_hash (text)                              │
│  training_dataset_id (uuid, fk → dataset_snapshots)  │
│  framework, architecture, input_shape, ...           │
│  registered_at, deployed_at, retired_at              │
└──────────────────────────────────────────────────────┘
                  ▲
                  │ FK source_model_id
                  │
┌─ annotations ────────────────────────────────────────┐
│  (existant) +                                        │
│  source_model_id (uuid, fk → ml_models, NULL si      │
│                   manual)            ← G1 / N1       │
│  source_confidence (float)           ← G1 / N1       │
│  source_tile_refs (jsonb, validé)    ← G10 / N1      │
│  properties (jsonb, schéma Pydantic) ← G9 / N2       │
└──────────────────────────────────────────────────────┘
                  ▲
                  │ FK
                  │
┌─ annotation_history ─────────────────────────────────┐  ← G5 / #331, #337
│  annotation_id, version, snapshot (jsonb complet)    │
│  changed_by, changed_at, change_reason               │
│  PK (annotation_id, version)                         │
└──────────────────────────────────────────────────────┘

┌─ corrections ────────────────────────────────────────┐
│  (existant) + model_id (fk → ml_models)              │
│  + chained_correction_id (fk → corrections)          │
└──────────────────────────────────────────────────────┘

┌─ dataset_snapshots ──────────────────────────────────┐  ← G3 / N3
│  id, name, version, created_by, created_at           │
│  filter_criteria (jsonb)                             │
│  sample_count, label_distribution (jsonb)            │
│  storage_uri (s3:// ou local)                        │
└──────────────────────────────────────────────────────┘

┌─ retraining_jobs ────────────────────────────────────┐  ← G4 / #339, #340, #341
│  id, model_id, trigger_reason, status                │
│  trigger_metrics (jsonb)                             │
│  created_at, started_at, completed_at                │
│  new_model_id (fk, NULL until done)                  │
└──────────────────────────────────────────────────────┘

┌─ annotation_sessions ────────────────────────────────┐  ← G8 / #336
│  id, slide_id, assigned_to, task_type                │
│  status, started_at, completed_at                    │
│  consensus_annotation_id (fk, NULL)                  │
└──────────────────────────────────────────────────────┘

audit_log → migration vers table WORM    ← G6 / N6
            (trigger BEFORE UPDATE/DELETE qui RAISE)
            + hash chain par row
            + signature optionnelle

PostgreSQL RLS sur annotations,           ← G7 / #354
              annotation_labels,
              corrections,
              view_history :
  CREATE POLICY tenant_isolation USING (
    tenant_id = current_setting('app.tenant_id')
  );

annotations.notes :                       ← D4 / N5
  - validation Pydantic regex anti-PII
  - chiffrement au repos (FieldEncryptedString)
  - audit access lecture
```

---

## 7. Plan d'évolution en 3 phases

### Phase A — Pipeline ML continu (bloquante)

1. **#346** — Registre `ml_models` (couvert)
2. **N1** — `source_model_id` + `source_confidence` + `source_tile_refs`
3. **N2** — Pydantic schemas pour `properties` / `metadata_extra`
4. **N3** — Export training-ready + `dataset_snapshots`

Sans Phase A complète, toute issue de Wave 10 (foundation models, fine-tuning, drift, active learning) repose sur du sable.

### Phase B — Conformité réglementaire

5. **#331 + #337** — History shadow annotations (à dédupliquer côté GitHub : redondance possible)
6. **N6** — Audit log WORM avec hash chain
7. **#354** — RLS PostgreSQL pour tenant isolation
8. **N5** — Protection PII sur `notes`
9. **N4** — Bulk import (au cas où on doit migrer un dataset existant)

### Phase C — Qualité diagnostique avancée

10. **#336** — Workflow d'adjudication multi-rater
11. **#339 + #340 + #341** — Drift detection + feedback loops + CI/CD champion-challenger

---

## 8. Critères de sortie de l'audit

L'audit est **levé** quand toutes les conditions suivantes sont réunies :

- [ ] Les 6 issues nouvelles (N1-N6) sont créées et liées à leurs waves respectives
- [ ] Les décisions D1-D4 sont actées dans un ADR dédié (`docs/architecture/ADR-XXX-*.md`)
- [ ] Phase A clôturée : pipeline ML continu fonctionnel et testable bout-en-bout
- [ ] Phase B clôturée : un auditeur externe peut consulter l'historique d'une annotation et vérifier l'intégrité de l'audit
- [ ] Tests d'intrusion RLS passants (un user tenant A ne peut PAS lire tenant B même via SQL direct)

---

## 9. Références

- EU AI Act art. 12 — Logging des décisions algorithmiques
- EU AI Act art. 14 — Surveillance humaine
- EU AI Act art. 17 — Système de gestion de la qualité
- EU MDR Annexe VIII — Documentation technique
- EU MDR Annexe XIV §3 — Provenance des données
- FDA 21 CFR 11 — Electronic Records, Electronic Signatures
- FDA 21 CFR 820.30 — Design Controls
- HL7 FHIR Provenance resource (`https://hl7.org/fhir/provenance.html`)
- Schéma actuel : `backend/models/annotation.py`, `backend/models/correction.py`
- Migrations : `backend/alembic/versions/001-009`
