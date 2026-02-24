# ml

## But
Services MLOps pour l'inference, le routage intelligent, le monitoring et le re-entrainement des modeles ML.

## Pourquoi
L'apprentissage continu en pathologie numerique necessite un pipeline complet : extraction de tags, routage vers le bon modele, detection de drift, feedback et re-entrainement.

## Structure
- `__init__.py` -- Package ML ; expose TagExtractor, TagRouter, ModelRoute.
- `tag_extractor.py` -- Extraction automatique de tags (organe, coloration, marqueur) depuis les metadonnees des lames.
- `tag_router.py` -- Routage vers les modeles ML specialises selon les tags extraits et la configuration YAML.
- `counting.py` -- Comptage cellulaire automatise (Ki-67/IHC) avec mode mock et mode reel.
- `similarity_index.py` -- Index vectoriel FAISS pour la recherche de lames similaires par embeddings.
- `clustering.py` -- Clustering morphologique des embeddings de lames via KMeans.
- `drift.py` -- Detection de drift des donnees et predictions par comparaison de distributions.
- `quality.py` -- Evaluation automatique de la qualite des lames (artefacts : plis, flou, bulles).
- `retraining.py` -- Pipeline de re-entrainement : versionnage DVC, entrainement Slideflow, tracking MLflow.
- `providers/` -- Implementations concretes de l'interface MLProvider.
