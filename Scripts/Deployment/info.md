# Deployment

## But
Scripts automatises pour le deploiement, la configuration reseau et les tests de connectivite de VarunaPoC.

## Pourquoi
Automatiser le passage de Phase 1 (localhost) a Phase 2.1 (reseau), la configuration firewall et les verifications de connectivite pour un deploiement reproductible.

## Structure
- `deploy-phase1.sh` : deploiement automatique Phase 1 (localhost)
- `deploy-phase2.1.sh` : deploiement automatique Phase 2.1 (reseau)
- `deploy-phase2.2.sh` : deploiement Phase 2.2
- `deploy-production.sh` : deploiement production
- `stop-phase1.sh` : arret propre Phase 1
- `stop-phase2.1.sh` : arret propre Phase 2.1
- `stop-phase2.2.sh` : arret propre Phase 2.2
- `firewall-host.sh` : configuration firewall serveur (UFW/iptables/Windows Defender)
- `switch-to-network.sh` : transition localhost vers IP reseau dans les fichiers de config
- `test-connectivity.sh` : test de connectivite client vers serveur (ping, ports, endpoints)
- `docker-compose.yml` : manifest de deploiement Docker (images GHCR)
- `README.md` : documentation complete des scripts et workflows de deploiement
