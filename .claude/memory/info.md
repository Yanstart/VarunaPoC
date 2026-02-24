# .claude/memory

## But
Memoire persistante du projet entre les sessions Claude Code.

## Pourquoi
Conserve les decisions, learnings, etat du projet et roadmap pour que chaque nouvelle session reprenne la ou la precedente s'est arretee. Evite de redetecter les memes problemes ou de prendre des decisions contradictoires.

## Comment
Fichiers Markdown mis a jour via le Brain Sync Protocol apres chaque tache completee. Chaque fichier couvre un aspect specifique de la memoire projet.

## Structure
```
memory/
  DECISIONS.md       # Decisions architecturales et techniques
  LEARNINGS.md       # Apprentissages (patterns, gotchas, fixes)
  PROJECT_STATE.md   # Etat courant du projet (milestones, issues)
  README.md          # Doc d'utilisation de la memoire
  ROADMAP.md         # Roadmap et prochaines etapes
  SOURCES.md         # Sources de reference (docs, articles)
```
