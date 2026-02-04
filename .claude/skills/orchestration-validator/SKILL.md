# Skill: Orchestration Validator

**But:** Valider et challenger toute proposition avant implementation.

---

## Quand Invoquer ce Skill

- Avant toute modification de code significative
- Avant creation de nouveaux fichiers
- Avant decisions architecturales
- Quand une proposition semble "trop simple" ou "trop complexe"
- Quand plusieurs approches sont possibles

---

## Processus de Validation

### Etape 1: Analyse de la Proposition

Repondre a ces questions:

```
1. PERTINENCE
   - La proposition repond-elle au besoin exprime?
   - Est-ce dans le scope du PoC?
   - Resout-elle le bon probleme?

2. SIMPLICITE
   - Est-ce la solution la plus simple possible?
   - Y a-t-il une alternative avec moins de code?
   - Pourrait-on utiliser une librairie existante?

3. COHERENCE
   - S'integre-t-elle avec l'architecture existante?
   - Respecte-t-elle les patterns etablis (ADR)?
   - Est-elle conforme a CLAUDE.md?

4. SOURCES
   - Est-elle validee par la documentation officielle?
   - Y a-t-il des exemples similaires dans .claude/memory/LEARNINGS.md?
   - Avons-nous deja pris une decision a ce sujet (DECISIONS.md)?
```

### Etape 2: Grille de Scoring

| Critere | Question | Score (0-3) |
|---------|----------|-------------|
| Pertinence | Repond au besoin? | |
| Simplicite | Solution minimale? | |
| Coherence | S'integre bien? | |
| Maintenabilite | Facile a maintenir? | |
| Performance | Impact acceptable? | |
| Securite | Pas de vulnerabilites? | |
| Testabilite | Peut etre teste? | |

**Interpretation:**
- **Score < 14:** REJETER - Revoir la proposition
- **Score 14-18:** ACCEPTABLE AVEC RESERVES - Documenter les reserves
- **Score > 18:** APPROUVER - Proceeder

### Etape 3: Questions de Challenge

Poser systematiquement:

1. **"Pourquoi pas plus simple?"**
   - Peut-on faire ca en moins de lignes?
   - Existe-t-il une fonction native qui fait deja ca?

2. **"Qu'existait-il avant?"**
   - Comment ce probleme etait-il gere avant?
   - Y a-t-il du code similaire dans le projet?

3. **"Que dit la doc officielle?"**
   - OpenSlide/OpenSeadragon ont-ils une solution?
   - Y a-t-il un pattern recommande?

4. **"Quel est le cas d'echec?"**
   - Que se passe-t-il si ca ne marche pas?
   - Comment detecte-t-on l'echec?
   - Peut-on rollback?

5. **"Qui va maintenir ca?"**
   - Un autre dev comprendrait-il ce code?
   - Y a-t-il assez de commentaires?
   - La decision est-elle documentee?

### Etape 4: Decision

Format de sortie:

```markdown
## Validation de Proposition

**Proposition:** [Description courte]

### Scoring
| Critere | Score | Justification |
|---------|-------|---------------|
| Pertinence | X/3 | ... |
| Simplicite | X/3 | ... |
| Coherence | X/3 | ... |
| Maintenabilite | X/3 | ... |
| Performance | X/3 | ... |
| Securite | X/3 | ... |
| Testabilite | X/3 | ... |
| **TOTAL** | **XX/21** | |

### Challenges Poses
1. [Question 1] → [Reponse]
2. [Question 2] → [Reponse]

### Sources Consultees
- [Source 1]: [Ce qu'elle dit]
- [Source 2]: [Ce qu'elle dit]

### Decision
**[APPROUVER / REJETER / MODIFIER]**

**Raison:** [Explication]

**Reserves:** [Si applicable]

**Actions requises:** [Si applicable]
```

---

## Integration avec le Workflow

### Avant Implementation

```
1. Recevoir proposition (de l'utilisateur ou d'un agent)
2. Invoquer orchestration-validator
3. Si REJETER → Proposer alternative
4. Si MODIFIER → Ajuster et re-valider
5. Si APPROUVER → Documenter dans DECISIONS.md si significatif
6. Proceeder a l'implementation
```

### Apres Implementation

```
1. Verifier que l'implementation correspond a la proposition validee
2. Si divergence → Re-valider
3. Mettre a jour LEARNINGS.md si nouvelle decouverte
```

---

## Exemples

### Exemple 1: Proposition Simple (APPROUVER)

**Proposition:** "Ajouter un bouton Reset Zoom"

**Validation:**
- Pertinence: 3/3 - Feature demandee
- Simplicite: 3/3 - OSD a `viewer.viewport.goHome()`
- Coherence: 3/3 - S'integre dans ViewerPanel existant
- Total: 21/21

**Decision:** APPROUVER

---

### Exemple 2: Proposition Complexe (MODIFIER)

**Proposition:** "Implementer un systeme de cache distribue avec Redis"

**Validation:**
- Pertinence: 2/3 - Utile mais pas urgent pour PoC
- Simplicite: 1/3 - Complexite elevee
- Coherence: 2/3 - Necessite infrastructure supplementaire
- Total: 12/21

**Decision:** MODIFIER
- Commencer par cache local ameliore
- Redis prevu pour Phase 2.5+

---

### Exemple 3: Proposition Risquee (REJETER)

**Proposition:** "Réécrire le backend en Go pour la performance"

**Validation:**
- Pertinence: 1/3 - Performance pas le bottleneck actuel
- Simplicite: 0/3 - Reecriture complete
- Coherence: 0/3 - Rompt avec stack existante
- Total: 5/21

**Decision:** REJETER
- OpenSlide n'a pas de binding Go
- Performance actuelle acceptable
- Focus sur features, pas sur stack

---

## Fichiers Concernes

- `.claude/BRAIN.md` - Processus global
- `.claude/memory/DECISIONS.md` - Enregistrement des decisions
- `.claude/memory/LEARNINGS.md` - Apprentissages
- `.claude/memory/SOURCES.md` - References pour validation

---

**Version:** 1.0
**Auteur:** Cerveau d'Orchestration VarunaPoC
