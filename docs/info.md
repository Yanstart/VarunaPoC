# docs

## But
Documentation technique et utilisateur du projet VarunaPoC. Index central pour l'architecture, le deploiement, les standards, et le manuel utilisateur.

## Pourquoi
Centraliser toute la documentation active (vs Archives/ pour les documents historiques). Permet l'onboarding rapide et la reference quotidienne.

## Structure
```
docs/
  README.md                    # Index de navigation de toute la doc
  PROPOSAL_VARUNA_v2.md        # Vision projet v2.0 (47K, document de reference)
  ARCHITECTURE.md              # Analyse architecturale systeme
  ML_INTEGRATION.md            # Architecture ML (inference, heatmaps, embeddings)
  FORMATS_SUPPORTED.md         # Liste complete des formats supportes
  ECOSYSTEM_MAP.md             # Cartographie vendeurs et solutions existantes
  PROTOCOLE.md                 # Protocole de validation clinique
  architecture/                # C4 diagrams, module contracts, refactoring plan, reader system
  Deployment/                  # Guides deploiement (Docker, CHU, Telemis, monitoring, Windows)
  Infrastructure/              # CI/CD guides, pipeline documentation
  Manuel/                      # Manuel utilisateur FR (9 chapitres: navigation, annotations, ML, qualite)
  plans/                       # Plans d'implementation par waves (Wave 1-4) + CI/CD design
  standards/                   # Compliance reglementaire (EU AI Act, FDA 510k, HIPAA, GDPR, TEFCA)
```

## Points cles
- `Manuel/` = 9 chapitres en francais, de l'introduction au FAQ
- `standards/` = couverture multi-juridiction (EU, US, CA, CN, BE)
- `Deployment/` = checklists operationnelles validees en CHU
