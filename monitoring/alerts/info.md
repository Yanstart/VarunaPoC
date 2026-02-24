# alerts

## But
Regles d'alerte Prometheus pour surveiller la performance, la disponibilite et les ressources de la plateforme VarunaPoC.

## Pourquoi
Detecter proactivement les violations de SLA (latence tuiles >2s, disponibilite <99.5%, taux erreur >1%) et les problemes de ressources avant qu'ils n'impactent les utilisateurs.

## Structure
- `varuna-alerts.yml` : 4 groupes de regles Prometheus (performance : latence, erreurs, cache ; disponibilite : backend, Redis, outage ; ressources : memoire, CPU, stockage ; capacite : sessions, requetes)
