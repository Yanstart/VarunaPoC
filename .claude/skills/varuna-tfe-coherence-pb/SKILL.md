---
name: varuna-tfe-coherence-pb
description: Vérifie l'alignement entre problème, problématique, hypothèses, méthodologie, résultats et recommandations. Détecte les sections orphelines et les ruptures de cohérence dans le fil conducteur.
allowed-tools: Read, Glob, Grep
---

# Cohérence problème-contenu — protocole de vérification

## Principe

Un TFE rigoureux a une **chaîne de cohérence intacte** :

```
Tensions identifiées (problème)
   ↓ donnent naissance à
Question centrale + sous-questions (problématique)
   ↓ se déclinent en
Hypothèses testables
   ↓ sont testées par
Méthodologie (qualitative ici)
   ↓ produit
Résultats (organisés par thématique répondant aux sous-questions)
   ↓ sont discutés en
Discussion (confirme/nuance les hypothèses + identifie les découvertes)
   ↓ génère
Recommandations (chaque reco se rattache à une découverte ou hypothèse confirmée)
   ↓ ouvre vers
Conclusion (réponse explicite à la question centrale)
```

Toute rupture dans cette chaîne est une **dette éditoriale** à corriger.

## Procédure (6 étapes)

### Étape 1 — Extraire les éléments clés

Lire et lister :
- **Tensions** (chapitre 2, section "Problème") : T1, T2, T3...
- **Question centrale** (chapitre 2, section "Problématique")
- **Sous-questions** : Q1, Q2, Q3...
- **Hypothèses** : H1, H2, H3...
- **Thématiques de résultats** (chapitre 4) : Th1, Th2, Th3, Th4
- **Sections de discussion** (chapitre 5) : D1, D2, D3...
- **Recommandations** (chapitre 7) : R1..R10

### Étape 2 — Matrice de couverture

Construire un tableau :

| | Th1 | Th2 | Th3 | Th4 |
|---|---|---|---|---|
| H1 | ? | ? | ? | ? |
| H2 | ? | ? | ? | ? |
| H3 | ? | ? | ? | ? |
| Découv. nouvelles | ? | ? | ? | ? |

Chaque cellule : oui/non/partiel. **Objectif** : chaque hypothèse a au moins 2 thématiques qui l'éclairent ; chaque thématique éclaire au moins 1 hypothèse.

### Étape 3 — Vérification recos ← discussion

Pour chaque recommandation R_i :
- À quelle hypothèse confirmée ou découverte se rattache-t-elle ?
- Cette ancrage est-il **explicitement** cité (renvoi `\ref{sec:...}` ou mention) ?

**Détecte** :
- Recos sans ancrage → suspects (peut-être génériques)
- Découvertes sans reco → opportunité manquée

### Étape 4 — Vérification problématique ↔ méthodologie

- La question centrale est-elle **qualitative** (du type "comment perçoivent-ils...", "pourquoi adoptent-ils ou non...") ?
- Si elle est quantitative ("dans quelle mesure", "à quelle fréquence") → la méthodologie qualitative ne peut pas y répondre. **Rupture.**
- Le guide d'entretien (annexe A) couvre-t-il bien les sous-questions ?

### Étape 5 — Détection des sections orphelines

Pour chaque section du rapport :
- À quelle question (Q ou sous-Q) répond-elle ?
- Si à aucune → **section orpheline** : la supprimer ou la rattacher

Liste suspecte typique :
- Sections de "contextualisation" trop longues sans lien direct
- Excursus techniques sans rattachement
- Tableaux/figures isolés

### Étape 6 — Test du chemin court

Synthèse : peut-on tracer **en moins de 3 phrases** le chemin :

> « Nous avons identifié [T1] (problème). Cela soulève [Q1] (sous-question). [H1] (hypothèse) y répondait positivement. Les résultats [Th1] confirment cette hypothèse, en particulier via [verbatim de Pn]. Nous recommandons donc [R_i]. »

Si ce chemin est tortueux ou impossible : **cohérence cassée**.

## Format de rapport

```markdown
# Audit cohérence — <scope>
Date : YYYY-MM-DD

## Éléments extraits
- N tensions, M sous-questions, K hypothèses
- L thématiques résultats, P sections discussion, Q recommandations

## Matrice de couverture
[Tableau]

## Recommandations sans ancrage
- R3 : pas de lien explicite avec une découverte ou H confirmée

## Découvertes sans recommandation
- Découverte X (ch. 5.3) → manque une reco

## Sections orphelines
- chapters/04-resultats.tex section 4.X : ne répond à aucune sous-question

## Verdict global
🟢 / 🟡 / 🔴 + synthèse en 3 lignes

## Actions priorisées
1. [HAUTE] ...
2. [MOYENNE] ...
```
