# Scripts

## But
Scripts operationnels du projet VarunaPoC: gestion du fork OpenSlide, deploiement Docker par phase, sauvegarde/restauration PostgreSQL, rollback, upgrade et monitoring.

## Pourquoi
Automatiser les operations repetitives et risquees (rebase fork upstream, deploiement multi-phase, firewall, sauvegarde DB, retour arriere). Chaque script est idempotent, documente, et utilisable depuis n'importe quel OS via WSL ou bash.

## Comment
- `backup.sh` execute `pg_dump -Fc -Z6` (custom format compresse) via `docker compose exec` sur le conteneur `db` et produit un fichier `.dump` horodate dans `./backups/`
- `restore.sh` source `.env.production`, drop/recreate la base, active PostGIS, execute `pg_restore`, puis valide la sante (matche le format produit par `backup.sh`)
- `rollback.sh` enchaine: arret services -> restore DB optionnel -> pull images version anterieure -> redemarrage -> healthcheck
- Les scripts OpenSlide (01-04) gerent le cycle de patch sur le fork local de la lib
- Les scripts `Deployment/*` orchestrent le deploiement par etapes incrementales (localhost -> reseau -> production)

## Structure
```
Scripts/
  README.md                       # Guide complet de gestion du fork OpenSlide (619 lignes)
  info.md                         # Ce fichier

  # OpenSlide fork management
  01_setup_fork.sh                # Setup initial: configure remotes, cree branches
  02_update_from_upstream.sh      # Sync depuis OpenSlide upstream officiel
  03_add_new_patch.sh             # Appliquer un nouveau patch
  04_rebuild_openslide.sh         # Compiler et installer OpenSlide patche

  # Database operations
  backup.sh                       # Sauvegarde PostgreSQL (pg_dump -Fc) -> ./backups/varuna_TIMESTAMP.dump
  restore.sh                      # Restauration PostgreSQL (pg_restore) avec confirmation et healthcheck

  # Lifecycle / Operations
  rollback.sh                     # Rollback version + restore DB optionnel
  upgrade.sh                      # Upgrade vers nouvelle version avec backup automatique
  watchdog.sh                     # Monitoring uptime externe
  deploy-optimized.sh             # Deploiement avec optimisations docker

  # Security
  setup-encrypted-volume.sh       # Initialiser volume chiffre LUKS pour donnees sensibles

  # CI / Verification
  verify-ci-setup.sh              # Valider la configuration CI/CD
  check-implementation-docs.sh    # Verifier coherence docs <-> implementation

  # Deployment workflow
  Deployment/
    deploy-phase1.sh              # Phase 1: localhost-only
    deploy-phase2.1.sh            # Phase 2.1: reseau interne
    deploy-phase2.2.sh            # Phase 2.2: integration complete
    deploy-production.sh          # Production: deploiement final
    stop-phase*.sh                # Arret propre par phase
    switch-to-network.sh          # Basculement localhost -> reseau
    test-connectivity.sh          # Validation connectivite reseau
    firewall-host.sh              # Configuration firewall hote
    docker-compose.yml            # Orchestration GitOps du deploiement
    README.md                     # Guide deploiement par phases
    info.md                       # Index Deployment/
```

## Convention casse
**Le dossier canonique est `Scripts/` (majuscule).** Le dossier `scripts/` (minuscule) a existe historiquement mais a ete consolide dans `Scripts/` pour eviter les conflits sur les filesystems insensibles a la casse (Windows, macOS APFS par defaut). Voir `.gitattributes` et la regle pre-commit `case-conflict`.
