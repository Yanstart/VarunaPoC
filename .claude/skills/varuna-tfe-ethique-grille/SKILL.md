---
name: varuna-tfe-ethique-grille
description: Grille d'analyse éthique multi-couches (cadre réglementaire, responsabilité médicale, biais algorithmique, souveraineté) appliquée au TFE Varuna. Structure faits/tensions/actions pour chaque couche.
allowed-tools: Read, Write, Edit, WebFetch, WebSearch
---

# Grille éthique — protocole d'analyse multi-couches

## Postulat

> **L'éthique en santé numérique n'est ni un chapeau moralisateur, ni un argument marketing. C'est une lecture en filigrane de ce qui est en jeu pour les personnes, les institutions, et la société.**

Cette grille structure une analyse éthique **dense et ancrée**, qui refuse l'abstraction et le moralisme.

## Les 4 couches

### Couche 1 — Cadre réglementaire applicable

Ce que dit la loi.

| Texte | Périmètre Varuna |
|---|---|
| **RGPD** (UE 2016/679) | Données de santé (art. 9), base légale (art. 6), DPIA (art. 35), droits des personnes (chap. III) |
| **AI Act** (UE 2024/1689) | Classification haut risque (Annexe III §5 dispositifs médicaux), obligations (titre III), supervision humaine (art. 14), transparence (art. 13) |
| **MDR** (UE 2017/745) | Logiciel comme dispositif médical (règle 11), classification, marquage CE |
| **ISO 15189:2022** | Accréditation laboratoire, traçabilité des analyses |
| **Loi belge du 22/08/2002** | Droits du patient (consentement, accès au dossier) |
| **Code de déontologie médicale belge** | Article sur IA et responsabilité médicale (Ordre des médecins) |

### Couche 2 — Responsabilité médicale et IA d'aide à la décision

Qui répond de quoi ?

| Niveau | Acteur | Responsabilité |
|---|---|---|
| Développement | Auteurs Varuna / éditeur | Conformité technique, documentation, validation |
| Déploiement | Établissement hospitalier | Choix d'usage, formation, gouvernance |
| Usage | Praticien | Décision médicale finale, supervision, traçabilité |

**Distinctions clés** :
- IA comme **outil d'aide** ≠ IA comme **décideur autonome** (Varuna se positionne strictement comme aide)
- Responsabilité **n'est jamais déléguable** au logiciel (cadre belge clair)
- Question de la **responsabilité partagée** en cas d'erreur

Verbatims à mobiliser : P2 (« si l'IA dit bénin et que c'est malin... »), P4 (« je veux qu'elle soit transparente »).

### Couche 3 — Biais algorithmique et équité diagnostique

Qui est défavorisé par les angles morts du système ?

| Type de biais | Manifestation en pathologie | Risque éthique |
|---|---|---|
| Sélection des données | Modèles entraînés sur centres US/asiatiques | Moins performant sur populations européennes / non blanches |
| Domain shift | Performance varie selon scanner/coloration | Inégalité d'accès au diagnostic selon l'établissement |
| Biais d'amplification | Le modèle apprend des biais des annotateurs | Reproduit les inégalités historiques |
| Biais de représentation | Sous-représentation des cas rares | Faux négatifs sur pathologies orphelines |

**Lien éthique** : un biais technique en santé n'est pas qu'un problème de performance, c'est une **question d'équité d'accès aux soins**.

Architecture MLOps de Varuna = réponse partielle (apprentissage local pallie le domain shift), mais ne résout pas les biais historiques.

### Couche 4 — Souveraineté des données et modèle économique

Qui contrôle les données et l'outil ?

| Dimension | Question éthique |
|---|---|
| Stockage | Local vs cloud ? Si cloud, dans quelle juridiction (RGPD chap. V) ? |
| Auditabilité | Le code est-il vérifiable (open source) ou opaque (propriétaire) ? |
| Pérennité | Que se passe-t-il si l'éditeur disparaît ou est racheté ? |
| Financement | Public, privé, hybride ? Risque de capture ? |
| Réutilisation des données | Les corrections du pathologiste alimentent-elles uniquement l'établissement, ou un modèle central appartenant à un tiers ? |

**Ancrage verbatim L2** : « pas par une grande entreprise qui vend une licence à prix prohibitif » — angle souveraineté et modèle économique éthique.

## Structure d'analyse pour chaque couche

Format imposé : **Faits → Tensions → Actions**.

### Faits
- Ce que dit le droit
- Ce qui est observé sur le terrain (entretiens, doc CHU)
- Ce que fait techniquement la solution

### Tensions
- Quelles valeurs s'opposent ?
- Exemples typiques :
  - Sécurité ↔ Accessibilité
  - Autonomie patient ↔ Efficacité diagnostique
  - Innovation ↔ Précaution
  - Souveraineté nationale ↔ Coopération internationale
  - Performance globale ↔ Équité locale

### Actions
- Ce que Varuna **fait déjà** pour répondre à cette couche
- Ce qu'il **reste à faire** (renvoi explicite à R8, R9, R10 du ch. 7)
- Ce qui dépasse le cadre de Varuna (recommandations systémiques)

## Boîtes LaTeX à utiliser

Dans les chapitres concernés, marquer les points clés :

```latex
\begin{pointvigilance}[RGPD — base légale de traitement]
Les données traitées par Varuna sont des \emph{données de santé} au sens
de l'article 9 du RGPD. Le traitement requiert une base légale spécifique :
mission d'intérêt public (art. 9.2.h) ou consentement explicite (art. 9.2.a),
selon le contexte de déploiement.
\end{pointvigilance}
```

## Anti-patterns

- « L'éthique est importante » → vide
- « Notre solution est éthique » → marketing
- « Les questions éthiques sont complexes » → fuite
- Citation d'un philosophe sans application concrète → décoratif
- Liste de principes (autonomie, bienfaisance...) sans ancrage → catéchisme

## Output attendu

- **Chapitre 6 (Éthique)** : 4 sections (une par couche), structure Faits/Tensions/Actions
- **Section éthique de la méthodologie (ch. 3)** : consentement, anonymisation, droit de retrait
- **Boîtes pointvigilance** dispersées dans les chapitres concernés (intro, discussion)
- **Recommandations R8, R9, R10** dans le chapitre 7
