# Exploration : Deleguer l'inference ML a une VM avec GPU

## Contexte

- Le serveur actuel (Intel i7-9700T, 19GB RAM, pas de GPU) tourne Slideflow + Phikon-v2 en CPU-only
- L'inference sur une lame 3Dhistech (109K x 220K px) bloque completement le backend (single-worker uvicorn)
- Meme les petites lames prennent plusieurs minutes en CPU
- En production, le ML doit etre non-bloquant et raisonnablement rapide

## Probleme a resoudre

Trouver un moyen d'executer l'inference ML (feature extraction, heatmaps, predictions) sur du materiel GPU sans acheter de carte graphique pour le serveur principal.

## Pistes a explorer

### 1. VM cloud avec GPU (a la demande)
- **GCP**: Compute Engine avec NVIDIA T4/L4 (~0.35-0.75 EUR/h)
- **AWS**: EC2 g4dn.xlarge avec T4 (~0.53 USD/h)
- **Azure**: NC-series avec T4
- **OVH / Scaleway**: GPU instances (plus proches, RGPD-friendly)
- Avantage: pas de cout fixe, allumer/eteindre selon la charge
- A evaluer: latence reseau pour transferer les tuiles

### 2. GPU emule / acceleration logicielle
- **Intel OpenVINO**: optimisation CPU pour modeles PyTorch (pas un vrai GPU mais 2-5x speedup)
- **ONNX Runtime**: convertir Phikon en ONNX, inference optimisee CPU
- **Intel Arc GPU** (si budget): GPUs Intel avec support PyTorch via XPU
- A evaluer: compatibilite avec Slideflow et les extracteurs de features

### 3. Architecture worker distant
- Le backend Varuna envoie les jobs ML a un worker distant (Celery + Redis/RabbitMQ)
- Le worker tourne sur la VM GPU
- Le backend poll le resultat ou recoit un callback
- Avantage: decouple completement le viewer du ML
- Pattern: API backend -> queue -> GPU worker -> resultat en DB/cache

### 4. Service ML as-a-Service (auto-heberge)
- Deployer un micro-service FastAPI sur la VM GPU (ex: Triton Inference Server, TorchServe, ou simple FastAPI)
- Le backend Varuna fait des appels HTTP au service ML
- Plus simple que Celery, meme isolation
- A evaluer: serialisation des tuiles, taille des payloads

### 5. Google Colab / Kaggle (prototypage)
- Pour tester rapidement si un GPU accelere suffisamment
- Pas viable en production mais utile pour benchmarker

## Questions ouvertes

- Quel budget mensuel pour le GPU ? (cloud a la demande vs machine dediee)
- Quelle latence ML est acceptable ? (temps reel vs batch overnight)
- Faut-il pre-calculer les features pour toutes les lames ou a la demande ?
- Contraintes RGPD : les images de lames peuvent-elles quitter le reseau du CHU ?
- Volume : combien de lames/jour a traiter ?

## Prochaines etapes

1. Benchmarker l'inference Phikon-v2 sur Google Colab (GPU T4 gratuit) pour avoir un baseline GPU vs CPU
2. Evaluer OpenVINO / ONNX Runtime comme quick-win CPU sans changer l'infra
3. Si GPU necessaire : chiffrer le cout cloud mensuel selon le volume estime
4. Prototyper l'architecture worker distant (meme en local, pour valider le pattern)
