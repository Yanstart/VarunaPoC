# docs

## But
Documentation technique et utilisateur du projet VarunaPoC. Index central pour
l'architecture, le deploiement, les standards, et le manuel utilisateur.

## Pourquoi
Centraliser toute la documentation active (vs Archives/ pour les documents
historiques). Permet l'onboarding rapide et la reference quotidienne.

## Doc canonique
- Architecture : `architecture/MODULAR_ARCHITECTURE.md`
- Admin/Operations : `Admin/`
- Utilisateur clinicien : `Manuel/`

## Structure
```
docs/
  README.md                    # Index de navigation de toute la doc
  Admin/                       # Manuel administrateur (topologie, profils, ops, fiches services)
  architecture/                # Architecture technique (canonique : MODULAR_ARCHITECTURE.md)
  Manuel/                      # Manuel utilisateur clinicien FR (8 chapitres + FAQ)
  Deployment/                  # Guides specifiques CHU (secrets, breakglass, network, Telemis)
  Infrastructure/              # CI/CD GitHub Actions, runner self-hosted
  adr/                         # Architecture Decision Records
  implementation/              # Notes patches/fixes (BIF, OIDC token, MPP fallback, ...)
  operations/                  # Procedures ops (chiffrement, ...)
  research/                    # Notes d'enquetes (interviews pathologistes)
  standards/                   # Conformite reglementaire (EU AI Act, FDA, TEFCA, eHealth)
  plans/                       # Plans actifs uniquement (closed plans -> Archives/plans-historiques/)
  PROPOSAL_VARUNA_v2.md        # Vision projet v2 (document de reference)
  PROTOCOLE.md                 # Protocole hopital (Telemis, eHealth)
  ML_INTEGRATION.md            # Architecture ML/Slideflow
  ML_COMPATIBILITY.md          # Compatibilite ML par format
  FORMATS_SUPPORTED.md         # 10 formats supportes
  ECOSYSTEM_MAP.md             # Cartographie ecosysteme WSI
  ANALYSE_DIRECTION_PROJET.md  # Strategie long-terme
  ETUDE_SOLUTIONS_EXISTANTES.md # Analyse Cytomine/DSA/QuPath
  ERROR_BIF_DIRECTION_LEFT.md  # Bug OpenSlide Ventana documente
  ERROR_TEMPLATE.md            # Template documentation d'erreur
```

## Points cles
- `Manuel/` = 8 chapitres + FAQ en francais (introduction, navigation, annotations, IA, qualite)
- `standards/` = couverture multi-juridiction (EU, US, CA, CN, BE)
- `Deployment/` = checklists operationnelles validees en CHU
- `Admin/` = manuel admin pour deployer le compose unifie sur n'importe quel hote
