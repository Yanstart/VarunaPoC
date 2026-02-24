# .claude

## But
Configuration Claude Code pour le projet VarunaPoC.

## Pourquoi
Centralise les instructions (CLAUDE.md), agents specialises, docs de contexte, memoire projet et skills reutilisables. Permet a Claude Code de naviguer et comprendre le projet sans repeter les memes instructions.

## Comment
- `CLAUDE.md` : instructions principales, regles de commit, workflow git, checklist validation
- `agents/` : 9 agents specialises (backend, frontend, infra, ML, securite...)
- `docs/` : contexte architectural, patterns, contrats modules
- `memory/` : etat du projet, decisions, learnings persistants
- `skills/` : 7 skills reutilisables (api-documenter, slide-tester, vm-cleanup...)

## Structure
```
.claude/
  CLAUDE.md          # Config principale Claude Code
  BRAIN.md           # Synthese brain pour navigation rapide
  README.md          # Doc d'utilisation
  agents/            # Agents specialises (9 profils)
  docs/              # Contexte projet (architecture, patterns, contrats)
  memory/            # Memoire persistante (decisions, learnings, roadmap)
  skills/            # Skills reutilisables (7 skills)
```
