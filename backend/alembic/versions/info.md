# versions

## But
Scripts de migration sequentiels definissant l'evolution du schema de la base de donnees.

## Pourquoi
Chaque migration represente un changement atomique du schema, permettant de reproduire l'etat exact de la base a tout moment.

## Structure
- `001_initial_annotations.py` -- Tables initiales annotations et labels avec PostGIS.
- `002_auth_and_audit.py` -- Tables users, audit_events, session_states, break_glass_logs.
- `003_quality_reports.py` -- Table cache pour les rapports de metriques de qualite.
- `004_seed_pathology_labels.py` -- Insertion des labels de pathologie predefinies (Tumeur, Necrose, etc.).
- `005_corrections.py` -- Table corrections pour le feedback loop ML (confirmed, rejected, refined, relabeled).
