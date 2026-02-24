# .claude/skills/vm-cleanup/scripts

## But
Scripts shell pour le skill vm-cleanup.

## Pourquoi
Separe la logique executable du skill definition (SKILL.md).

## Comment
`disk-report.sh` analyse l'espace disque par repertoire et identifie les candidats au nettoyage.

## Structure
```
scripts/
  disk-report.sh    # Rapport d'utilisation disque avec recommandations
```
