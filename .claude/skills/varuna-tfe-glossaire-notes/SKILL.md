---
name: varuna-tfe-glossaire-notes
description: Gère les notes de bas de page, définitions inline, glossaire, acronymes et explications techniques destinées à rendre le rapport accessible sans sacrifier la rigueur.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Glossaire et notes — protocole

## Principe

> **Un TFE doit être lisible par un évaluateur qui n'est pas du domaine, sans appauvrir le contenu pour l'évaluateur qui l'est.**

Trois leviers complémentaires :
1. **Vocabulaire accessible** dans le corps du texte (l'intro pose les bases)
2. **Notes de bas de page** pour les précisions techniques sans interrompre la lecture
3. **Glossaire** en annexe pour les termes récurrents
4. **Liste d'acronymes** générée automatiquement

## Quand utiliser quoi ?

### Définition inline (corps du texte)
Pour un terme **central au propos** :
> Le \emph{Whole Slide Imaging} (WSI) désigne la technologie permettant de
> numériser une lame histologique complète en une image numérique de très
> haute résolution \cite{farahani2015}.

### Note de bas de page
Pour une **précision technique** qui interromprait la lecture :
> Le format pyramidal\footnote{Le format pyramidal stocke l'image à plusieurs
> niveaux de résolution successifs, permettant au viewer de ne charger que la
> tuile nécessaire au zoom courant. Une lame typique pèse 250~MB à plusieurs
> dizaines de GB.} permet une navigation virtuelle fluide.

### Glossaire (annexe)
Pour les **termes récurrents** définis une fois mais utilisés partout :
- WSI, LIS, RIS, PACS, MLOps, RCP, H&E, IHC, FHIR, DICOM, RGPD, AI Act, ACI...

### Acronymes (liste automatique)
Le package `acronym` ou `glossaries-extra` gère :
- Première occurrence : forme complète + acronyme
- Occurrences suivantes : acronyme seul
- Liste en annexe

## Mise en œuvre LaTeX

### Option 1 — Acronymes simples avec `acronym`

À ajouter au `preamble.tex` :
```latex
\usepackage[printonlyused, withpage]{acronym}
```

Définir les acronymes dans `chapters/00-acronymes.tex` ou en début de glossaire :
```latex
\begin{acronym}[FHIR]
  \acro{WSI}{Whole Slide Imaging}
  \acro{LIS}{Laboratory Information System}
  \acro{RIS}{Radiology Information System}
  \acro{PACS}{Picture Archiving and Communication System}
  \acro{MLOps}{Machine Learning Operations}
  \acro{RCP}{Réunion de Concertation Pluridisciplinaire}
  \acro{H\&E}{Hématoxyline-Éosine}
  \acro{IHC}{Immunohistochimie}
  \acro{FHIR}{Fast Healthcare Interoperability Resources}
  \acro{DICOM}{Digital Imaging and Communications in Medicine}
  \acro{RGPD}{Règlement Général sur la Protection des Données}
  \acro{MDR}{Medical Device Regulation}
  \acro{XAI}{eXplainable Artificial Intelligence}
  \acro{ACI}{Accord de Coopération Interuniversitaire}
  \acro{CHU}{Centre Hospitalier Universitaire}
  \acro{CHR}{Centre Hospitalier Régional}
  \acro{DPIA}{Data Protection Impact Assessment}
\end{acronym}
```

Usage dans le texte :
```latex
La technologie de \ac{WSI} permet de numériser...
% Première occurrence -> "La technologie de Whole Slide Imaging (WSI) permet..."
% Occurrences suivantes -> "Le WSI permet..."
```

### Option 2 — Glossaire riche avec `glossaries-extra`

Plus puissant (définitions, descriptions longues), mais plus lourd. À envisager si > 30 entrées.

## Procédure d'application

### Étape 1 — Inventaire des termes techniques

`Grep` sur les fichiers `chapters/` pour identifier :
- Acronymes (suite de 2+ majuscules) : `[A-Z]{2,}`
- Termes anglais probablement à définir : `Whole Slide Imaging`, `domain shift`, `model drift`, `vendor lock-in`...
- Concepts métier : RCP, second avis, immunohistochimie, etc.

### Étape 2 — Classement par stratégie

| Fréquence | Stratégie |
|---|---|
| 1-2 occurrences | Définition inline ou note de bas de page |
| 3+ occurrences | Acronyme dans la liste + définition à la 1ère occurrence |
| Concept central | Définition dans l'intro + entrée glossaire |

### Étape 3 — Ajout au fichier acronymes/glossaire

Maintenir `Report/chapters/00-acronymes.tex` à jour.

### Étape 4 — Réécriture des occurrences

Pour chaque acronyme :
- 1ère occurrence : `\ac{XXX}` (génère "Forme longue (XXX)")
- Suivantes : `\ac{XXX}` (génère juste "XXX")

Pour les notes de bas de page :
```latex
Texte principal\footnote{Précision technique sans interrompre.}.
```

### Étape 5 — Génération de la liste

À placer en début de rapport (après la TOC) ou en annexe :
```latex
\chapter*{Liste des acronymes}
\addcontentsline{toc}{chapter}{Liste des acronymes}
\input{chapters/00-acronymes}
```

## Règles de style

### Ce qu'une note de bas de page **doit** être
- Une **précision** qui clarifie sans alourdir
- Une **référence externe** secondaire (URL d'un outil mentionné, par ex.)
- Une **nuance** qu'on ne veut pas inscrire dans la trame principale

### Ce qu'une note de bas de page **ne doit pas** être
- Un paragraphe de 10 lignes (si c'est long, c'est du corps de texte)
- Une citation académique (utiliser `\cite{}`)
- Un commentaire personnel ironique (registre académique)
- Une digression hors sujet

### Densité acceptable
- Maximum **2 notes de bas de page par page**
- Si plus : signe que la trame principale est mal calibrée pour le lecteur visé

## Liste d'acronymes initiale pour le TFE Varuna

À insérer dans `chapters/00-acronymes.tex` :
- WSI, LIS, RIS, PACS, MLOps, RCP, H&E, IHC, FHIR, DICOM, RGPD, AI Act, MDR, ACI, XAI, DPIA, CHU, CHR, ISO, ML, DL, CNN, IA, CE (marquage), KCE, INAMI, ULiège, EPHEC

## Anti-patterns

- **Note de bas de page dans une note de bas de page** (LaTeX peut le faire, le lecteur souffre)
- **Acronyme défini 3 fois** (incohérence)
- **Acronyme jamais défini** (le lecteur devine)
- **Glossaire qui répète l'intro** (redondance)
- **Vocabulaire technique sans définition dans l'intro** (mépris du lecteur non-spécialiste)
