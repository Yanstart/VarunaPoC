# workflows

## But
Workflows GitHub Actions pour l'integration continue, le deploiement continu et l'analyse de securite du projet.

## Pourquoi
Automatiser les verifications de qualite (lint, tests, build Docker), le deploiement (images GHCR, releases, manifests) et les scans de securite (Trivy, Bandit, Gitleaks, conformite HIPAA/RGPD).

## Structure
- `ci.yml` : integration continue (lint backend/frontend, tests pytest, build Docker, integration)
- `cd.yml` : deploiement continu (build/push images GHCR, releases, mise a jour manifests)
- `security.yml` : scans de securite (vulnerabilites, SAST, secrets, conformite medicale)
- `update-project.yml` : mise a jour automatique du GitHub Project board
- `notify-failure.yml` : notifications en cas d'echec de pipeline
- `README.md` : documentation complete des 3 workflows principaux
