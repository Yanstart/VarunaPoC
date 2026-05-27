---
name: varuna-tfe-prelecture-check
description: Audite un chapitre ou le rapport entier selon le critère "lecture sans lire". Vérifie qu'on comprend le sens en ne lisant que titres, sous-titres, légendes de figures/tableaux, chapeaux et premiers paragraphes.
allowed-tools: Read, Glob, Grep
---

# Prélecture-check — protocole d'audit

## Objectif

Un TFE bien écrit doit être **compréhensible en moins de 5 minutes** en ne lisant que :
- Le titre + sous-titre du rapport
- L'executive summary
- La table des matières
- Les titres de chapitres et sections
- Les légendes des figures et tableaux
- Les chapeaux introductifs de chapitres et sections
- Le **premier paragraphe** de chaque section

Si ces éléments ne suffisent pas, **l'architecture éditoriale a échoué**.

## Quand appliquer ce protocole

- Après la rédaction de chaque chapitre
- Avant chaque commit majeur
- Audit global avant compilation finale

## Procédure (5 étapes)

### Étape 1 — Inventaire scannable

Pour le fichier `.tex` ciblé, extraire :
```
\chapter, \chapter*  → titres de chapitres
\section, \section*  → titres de sections
\subsection, \subsubsection → sous-titres
\caption  → légendes figures/tableaux
% [TODO chapeau]  → chapeaux manquants
```

Outils : `Grep` avec patterns ci-dessus.

### Étape 2 — Vérification des chapeaux

Pour chaque `\chapter` et chaque `\section`, vérifier :
- [ ] Présence d'un chapeau introductif de 2-4 lignes **avant** la première sous-section
- [ ] Ce chapeau annonce le contenu sans le résumer (verbe d'action)
- [ ] Le chapeau ne commence pas par "Dans ce chapitre, nous allons..." (verbiage)

### Étape 3 — Vérification du premier paragraphe de section

Pour chaque section, lire **seulement** le premier paragraphe :
- [ ] Donne-t-il l'idée principale de la section ?
- [ ] Pourrait-on supprimer la suite et garder l'essentiel ?
- [ ] Y a-t-il une mise en contexte (pourquoi cette section maintenant) ?

### Étape 4 — Vérification des légendes

Pour chaque `\caption{...}` :
- [ ] La légende a un **format court** ([...]) **et long** ({...})
- [ ] La légende longue **explique l'intention narrative**, pas juste le contenu visuel
- [ ] Format à privilégier : `\caption[Carte des tensions]{Carte des trois tensions structurelles identifiées : adoption WSI, généralisation IA, et acceptation clinique. Chaque tension articule un facteur technique (gauche) et un facteur humain (droite).}`

### Étape 5 — Test de Turing du lecteur pressé

Synthèse : après lecture **uniquement** des éléments listés ci-dessus, peut-on répondre OUI à toutes ces questions ?

- [ ] Comprend-on **dans quel contexte** ce travail s'inscrit ?
- [ ] Identifie-t-on **le problème** traité ?
- [ ] Sait-on **comment** il a été abordé (méthode) ?
- [ ] Connaît-on les **3 résultats principaux** ?
- [ ] Identifie-t-on **les recommandations** clés ?
- [ ] Perçoit-on la **dimension éthique** comme un élément traité (pas survolé) ?

## Format de rapport

```markdown
# Audit prélecture — <chapitre / rapport>
Date : YYYY-MM-DD

## Inventaire
- N chapitres, N sections, N sous-sections
- N figures, N tableaux
- N chapeaux trouvés / N attendus
- N légendes complètes / N total

## Constats par section
### Chapitre X — Section Y
- Chapeau : 🟢 / 🟡 / 🔴 (raison)
- 1er paragraphe : 🟢 / 🟡 / 🔴 (raison)
- Légendes : 🟢 / 🟡 / 🔴 (raison)

## Test du lecteur pressé
- Contexte : OUI/NON (justification)
- Problème : OUI/NON
- Méthode : OUI/NON
- Résultats : OUI/NON
- Recommandations : OUI/NON
- Éthique : OUI/NON

## Actions recommandées (priorisées)
1. [HAUTE] Action concrète
2. ...
```

## Critères de notation

| Score | Signification |
|---|---|
| 🟢 | Conforme — rien à faire |
| 🟡 | Présent mais améliorable (priorité MOYENNE) |
| 🔴 | Manquant ou non conforme (priorité HAUTE) |
