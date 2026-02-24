# Scripts

## But
Scripts operationnels: gestion du fork OpenSlide et deploiement Docker par phase.

## Pourquoi
Automatiser les operations repetitives et risquees (rebase fork upstream, deploiement multi-phase, firewall). Chaque script est idempotent et documente.

## Structure
```
Scripts/
  README.md                    # Guide complet de gestion du fork (619 lignes)
  01_setup_fork.sh             # Setup initial: configure remotes, cree branches
  02_update_from_upstream.sh   # Sync depuis OpenSlide upstream officiel
  03_add_new_patch.sh          # Appliquer un nouveau patch
  04_rebuild_openslide.sh      # Compiler et installer OpenSlide patche
  verify-ci-setup.sh           # Verifier la configuration CI
  Deployment/
    deploy-phase1.sh           # Deploiement Phase 1 (localhost)
    deploy-phase2.1.sh         # Deploiement Phase 2.1 (reseau)
    deploy-phase2.2.sh         # Deploiement Phase 2.2
    deploy-production.sh       # Deploiement production
    stop-phase*.sh             # Arret propre par phase
    switch-to-network.sh       # Basculement reseau
    test-connectivity.sh       # Validation connectivite
    firewall-host.sh           # Configuration firewall
    docker-compose.yml         # Orchestration deploiement
```
