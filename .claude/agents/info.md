# .claude/agents

## But
Agents Claude Code specialises par domaine pour le projet VarunaPoC.

## Pourquoi
Chaque agent possede un system prompt taille pour son domaine d'expertise. Permet de deleguer des taches complexes a un agent qui connait le contexte specifique (backend, frontend, infra, ML, securite, etc.).

## Comment
Chaque fichier `.md` definit un agent avec son role, ses outils disponibles, et ses instructions specifiques. Le `chief-architect` orchestre les autres agents.

## Structure
```
agents/
  chief-architect.md          # Orchestrateur principal
  backend-tech-lead.md        # FastAPI, OpenSlide, tiles
  frontend-tech-lead.md       # Vite, Vanilla JS, OpenSeadragon
  infrastructure-architect.md # Docker, CI/CD, deploiement
  integration-engineer.md     # PACS, DICOM, HL7, interoperabilite
  lead-architecte.md          # Architecture systeme globale
  ml-architect.md             # IA/ML pour imagerie medicale
  performance-engineer.md     # Optimisation, coordonnees, cache
  security-architect.md       # HIPAA/GDPR, authentification, chiffrement
```
