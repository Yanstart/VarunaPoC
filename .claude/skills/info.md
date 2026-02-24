# .claude/skills

## But
Skills reutilisables pour automatiser des taches recurrentes dans VarunaPoC.

## Pourquoi
Chaque skill encapsule un protocole specifique (documenter une API, valider des coordonnees, nettoyer la VM...). Invocables via `/skill-name` dans Claude Code. Evite de reimplementer les memes procedures.

## Comment
Chaque sous-dossier contient un `SKILL.md` avec le nom, la description de declenchement, et les instructions detaillees du skill. Claude Code les decouvre automatiquement.

## Structure
```
skills/
  api-documenter/            # Documenter les endpoints FastAPI
  coordinate-validator/      # Valider le mapping coordonnees OSD/OpenSlide
  error-documenter/          # Documenter les erreurs non-triviales
  manual-updater/            # Mettre a jour le manuel utilisateur
  orchestration-validator/   # Valider l'orchestration des composants
  slide-tester/              # Tester les features sur tous les formats de lames
  vm-cleanup/                # Nettoyer l'espace disque de la VM
```
