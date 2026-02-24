# .claude/skills/slide-tester

## But
Tester systematiquement les features sur tous les formats de lames supportes (.mrxs, .bif, .tif).

## Pourquoi
Chaque format de lame a une structure differente (vendor-specific). Un test qui passe sur .mrxs peut echouer sur .bif.

## Comment
Invoque via `/slide-tester`. Valide la structure des fichiers, la compatibilite OpenSlide et l'integration viewer pour chaque format.

## Structure
```
slide-tester/
  SKILL.md    # Definition et instructions du skill
```
