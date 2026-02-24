# .claude/skills/vm-cleanup

## But
Nettoyer l'espace disque de la VM de developpement.

## Pourquoi
La VM a un disque root de 92 Go qui peut se remplir rapidement avec Docker, caches npm/pip, et artefacts de build. Declenchement recommande quand l'usage depasse 80%.

## Comment
Invoque via `/vm-cleanup`. Execute le script `scripts/disk-report.sh` pour analyser puis nettoie les caches, images Docker inutilisees, et artefacts temporaires.

## Structure
```
vm-cleanup/
  SKILL.md              # Definition et instructions du skill
  scripts/
    disk-report.sh      # Script d'analyse d'espace disque
```
