---
name: varuna-tfe-abstraction-visuel
description: Protocole en 4 étapes pour transformer un screenshot brut (interface Varuna, capture d'écran de viewer concurrent) en figure TikZ abstraite, intuitive et académiquement propre.
allowed-tools: Read, Write, Edit, Bash
---

# Abstraction visuelle — protocole en 4 étapes

## Principe fondateur

> **Un screenshot brut, même très lisible, n'est pas une figure de TFE. C'est une preuve d'existence de produit. Une figure de TFE doit clarifier un concept.**

L'abstraction permet de :
1. **Garder l'essentiel** (le concept, l'agencement, le flux)
2. **Évacuer le bruit** (texte UI illisible imprimé, éléments décoratifs)
3. **Mettre en relief** ce qui importe pour le propos
4. **Rester vectoriel et noir/blanc-friendly** (impression PDF)

## Procédure en 4 étapes

### Étape 1 — Extraire le concept

Avant de toucher à TikZ, écrire en 2 phrases :
- **Que montre cette interface ?** (description littérale)
- **Que doit retenir le lecteur ?** (intention narrative)

Exemple :
> Que montre : un viewer histologique avec une lame H&E zoomée à 20x, un panneau latéral d'annotations et un overlay heatmap rouge/jaune/vert sur une zone tumorale.
> Intention : montrer que la superposition heatmap **n'est pas un verdict**, c'est une **cartographie de l'incertitude** que le pathologiste peut confronter à sa lecture.

L'intention détermine le niveau d'abstraction.

### Étape 2 — Simplifier les formes

Réduction à des primitives géométriques :
- Fenêtre du viewer → rectangle arrondi
- Lame WSI → rectangle texturé (motif tissu schématisé) OU image PNG **partielle** (cas où le contenu clinique doit rester reconnaissable)
- Panneau latéral → rectangle subdivisé avec sections
- Boutons → cercles ou rectangles arrondis avec icône stylisée
- Heatmap → zones colorées avec dégradé simple (3-4 couleurs max)

**Règle d'or** : un élément ≠ une preuve. Inutile de dessiner 12 boutons fidèlement si seuls 2 servent le propos.

### Étape 3 — Annoter l'intention

Ajouter sur la figure :
- **Étiquettes numérotées** ① ② ③ pour les éléments-clés (max 5)
- **Légende des numéros** dans la `\caption` ou sous la figure
- **Flèches sémantiques** : annotation → élément, ou élément → conséquence
- **Distinction visuelle** : ce qui est dans le scope du propos (couleur primaire) vs reste (gris/atténué)

Exemple de pattern :
```latex
\begin{figure}[ht]
\centering
\begin{tikzpicture}[font=\small, every node/.style={align=center}]
  % Cadre du viewer
  \draw[rounded corners, fill=varunaBg, draw=varunaMuted, thick]
    (0,0) rectangle (10,6);

  % Zone lame
  \draw[fill=white, draw=varunaMuted]
    (0.3,0.3) rectangle (7,5.7);

  % Heatmap overlay (zones colorées translucides)
  \fill[varunaSuccess, opacity=0.4] (1.5,2) rectangle (3,4);
  \fill[yellow!70, opacity=0.5]    (3,1) rectangle (5,3.5);
  \fill[varunaAccent, opacity=0.5] (5,3) rectangle (6.5,5);

  % Annotations numérotées
  \node[circle, fill=varunaPrimary, text=white, inner sep=2pt]
    (a1) at (2.2,3) {\textbf{1}};
  \node[circle, fill=varunaPrimary, text=white, inner sep=2pt]
    (a2) at (4,2.2) {\textbf{2}};
  \node[circle, fill=varunaPrimary, text=white, inner sep=2pt]
    (a3) at (5.7,4) {\textbf{3}};

  % Panneau latéral
  \draw[fill=varunaBg, draw=varunaMuted]
    (7.2,0.3) rectangle (9.7,5.7);
  \node[anchor=north] at (8.4,5.5) {\textbf{Annotations}};

\end{tikzpicture}
\caption[Heatmap de confiance superposé]{Heatmap de confiance superposé à
une lame H\&E (lame stylisée). ① Zone de \emph{forte confiance} (vert) :
le modèle estime la prédiction certaine. ② Zone d'\emph{incertitude}
(jaune) : à examiner en priorité. ③ Zone de \emph{désaccord potentiel}
(rouge) : le modèle hésite, intervention humaine requise.}
\label{fig:heatmap-stylise}
\end{figure}
```

### Étape 4 — Tester le « test du voisin »

Montre la figure (mentalement ou réellement) à quelqu'un qui :
- N'a jamais vu l'application
- N'a pas lu le chapitre

Cette personne peut-elle décrire **en 1 phrase** ce que la figure montre ?
- OUI → figure réussie
- NON → revenir à l'étape 1 (intention pas claire)

## Cas particuliers

### Cas où le screenshot brut est tolérable

**Exceptionnellement**, on accepte un screenshot encapsulé dans une figure TikZ annotée :
- L'authenticité visuelle est essentielle (ex: comparaison Varuna vs viewer concurrent où l'esthétique différenciante est le propos)
- Le contenu clinique doit rester reconnaissable pour la crédibilité (ex: heatmap réel sur une lame réelle pour montrer qu'il fonctionne)

Dans ce cas :
- Placer le PNG dans `Report/figures/pdf/`
- L'inclure avec `\includegraphics` dans un `tikzpicture` qui le surplombe d'annotations
- **Justifier en commentaire** pourquoi l'abstraction n'a pas été poussée plus loin

### Cas du diagramme de flux pur

Pour les workflows (du prélèvement au diagnostic, ou cycle MLOps), pas besoin de screenshot. TikZ direct avec `arrows.meta` + `positioning`.

## Outputs attendus

Fichier `.tex` autonome dans `Report/figures/tikz/<slug>.tex`, inclus via :
```latex
\input{figures/tikz/<slug>}
```

Le `\begin{figure}` et `\caption` sont **dans le fichier de la figure**, pas dans le chapitre.

## Anti-patterns à refuser

- Screenshot collé brut avec juste un `\caption` → REFUS
- Figure de plus de 5 éléments numérotés → simplifier
- Couleurs hors palette (`varunaPrimary`, `varunaAccent`, `varunaMuted`, `varunaBg`, `varunaSuccess`) → corriger
- Police trop petite (< `\footnotesize`)
- Aspect non vectoriel quand alternative TikZ existe
