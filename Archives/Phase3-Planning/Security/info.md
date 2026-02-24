# Security

## But
Definir l'architecture de securite et la conformite RGPD pour le deploiement de VarunaPoC en environnement hospitalier (CHU UCL Namur).

## Pourquoi
Le PoC initial avait un score securite de 3.1/10 (aucune authentification, aucun chiffrement) et necessitait une feuille de route de securisation avant tout deploiement production.

## Structure
- `SECURITY_ARCHITECTURE.md` - Architecture securite complete : conformite reglementaire, modele de menaces, authentification, chiffrement, audit trail, securite MLOps et PACS.
- `SECURITY_EXECUTIVE_SUMMARY.md` - Resume executif pour la direction : etat critique, risques RGPD, actions requises immediatement.
- `SECURITY_PHASE1_IMPLEMENTATION.md` - Guide d'implementation Phase 1 securite (1-2 semaines) : authentification HTTP Basic, HTTPS, audit trail, headers.
