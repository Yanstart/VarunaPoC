---
name: varuna-tfe-transitions
description: Génère intros, conclusions et transitions de sections/chapitres pour garantir un fil conducteur fluide. Évite les transitions creuses ("Dans ce chapitre, nous allons...").
allowed-tools: Read, Write, Edit
---

# Transitions — protocole de génération

## Principe

> **Une transition réussie fait sentir au lecteur que ce qu'il vient de lire et ce qu'il va lire sont reliés par une nécessité, pas par un sommaire.**

Trois rôles distincts :

| Type | Position | Rôle |
|---|---|---|
| **Chapeau** | Début de chapitre/section | Pose ce qu'on va faire et pourquoi maintenant |
| **Transition** | Fin d'une section, début de la suivante | Articule la nécessité du passage |
| **Conclusion** | Fin de chapitre | Synthétise + annonce le chapitre suivant |

## Chapeaux — anatomie

Un chapeau de chapitre ou de section :
- Fait **2 à 4 lignes maximum**
- Annonce **ce qu'on va faire** (action) sans annoncer **comment** (le détail vient après)
- **Relie au précédent** (sans répéter) et **prépare le suivant** (sans le résumer)

### Exemples ✓

> Les angles morts identifiés au chapitre précédent appellent une lecture
> qualitative du terrain. Nous décrivons ici les six entretiens menés en
> région liégeoise, la méthode de codage retenue, et la posture éthique
> dans laquelle s'inscrit cette enquête.

> Si la fluidité de navigation et la transparence du raisonnement IA
> ont été plébiscitées, trois éléments inattendus émergent des entretiens.
> Cette section les expose et les met en perspective avec la littérature.

### Exemples ✗

> Dans ce chapitre, nous allons présenter la méthodologie.
> *(creux, descriptif)*

> Ce chapitre traite de la méthodologie, qui est très importante.
> *(commentaire méta, sans valeur)*

> Comme nous l'avons vu, et comme nous le verrons, la méthodologie est
> essentielle pour notre étude.
> *(redondance et auto-référence)*

## Transitions inter-sections

Position : dernier paragraphe d'une section, qui prépare la suivante.

### Patterns efficaces

**1. Le « si A, alors B se pose »**
> Si l'accessibilité technique semble acquise, la question de la confiance
> envers l'IA reste entière. C'est ce que nous abordons à présent.

**2. Le « les uns ont dit X, mais d'autres pensent Y »**
> Quatre participants pointent ce frein. Reste à comprendre pourquoi les
> deux autres ne l'évoquent pas — ce que la section suivante éclaire.

**3. Le « ce constat appelle une analyse plus profonde »**
> Ces réactions positives doivent être lues à la lumière du contexte de
> démonstration, ce qui constitue notre prochaine étape.

**4. Le « passons du quoi au pourquoi »** (ou inverse)
> Ces résultats étant établis, leur interprétation reste à construire.

### À éviter

- « Passons maintenant à... »
- « Voyons à présent... »
- « Le chapitre suivant traite de... »
- « Comme expliqué précédemment... »

## Conclusions de chapitre

Format en 3 mouvements (3-5 lignes max) :

1. **Le bilan** : qu'avons-nous établi dans ce chapitre ?
2. **La tension non résolue** : qu'est-ce qui reste ouvert ?
3. **L'annonce** : à quoi cela conduit-il dans la suite ?

### Exemple

> Le matériau d'entretien atteste un intérêt fort pour Varuna et identifie
> trois leviers d'adoption et trois freins. Mais ce premier inventaire ne
> dit rien encore de la portée de ces signaux ni de leur lien avec ce que
> la littérature internationale documente. La discussion qui suit comble
> cet écart.

## Génération pour un fichier .tex

Quand on te demande de produire chapeaux/transitions/conclusions :

1. **Lire** le fichier `.tex` cible
2. **Identifier** :
   - Le chapitre/section précédent (ou la dernière chose dite avant cette section)
   - Le chapitre/section suivant
   - Le rôle de la section actuelle dans le fil conducteur (cf. BOARD.md)
3. **Produire** les 3 éléments (chapeau, transitions inter-sections, conclusion) en respectant les règles ci-dessus
4. **Insérer** aux bons endroits dans le fichier `.tex` (ou les proposer au rédacteur si ce n'est pas le rôle de l'agent appelant)

## Anti-patterns à refuser

- **Transition tautologique** : "Cette section traite de la méthodologie, qui sera traitée dans cette section"
- **Transition décorative** : ajouter une transition là où le passage est déjà évident
- **Conclusion-résumé** : reprendre les sous-titres en disant "Nous avons vu A, puis B, puis C"
- **Chapeau-sommaire** : annoncer toutes les sections du chapitre une par une
- **Transition sans nécessité** : pourquoi B suit A doit être *visible*, pas seulement *annoncé*
