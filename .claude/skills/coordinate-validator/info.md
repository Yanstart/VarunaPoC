# .claude/skills/coordinate-validator

## But
Valider la precision du mapping de coordonnees entre OpenSeadragon (normalise 0.0-1.0) et OpenSlide (pixels absolus).

## Pourquoi
La transformation de coordonnees est critique pour les annotations sur les lames numerisees. Une erreur de mapping = annotation au mauvais endroit.

## Comment
Invoque via `/coordinate-validator`. Verifie la precision mathematique des transformations.

## Structure
```
coordinate-validator/
  SKILL.md    # Definition et instructions du skill
```
