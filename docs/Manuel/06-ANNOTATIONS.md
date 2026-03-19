# Annotations

**Statut:** Fonctionnel
**Derniere mise a jour:** 2026-03-19
**Fonctionnalite:** Annotations, etiquettes, notes, correction IA, quiz mode

---

## Vue d'Ensemble

Le module d'annotations permet aux pathologistes de dessiner directement sur les lames numerisees pour marquer des regions d'interet, ajouter des diagnostics et fournir un retour sur les predictions de l'intelligence artificielle. Toutes les annotations sont enregistrees au format GeoJSON et associees a la lame correspondante.

---

## Raccourcis Clavier

Tous les raccourcis fonctionnent globalement (pas besoin de cliquer dans un panneau). Ils sont desactives automatiquement quand vous tapez dans un champ texte.

### Outils de dessin

| Touche | Outil | Description |
|--------|-------|-------------|
| **D** | Dessin libre | Tracez a main levee, fermeture automatique |
| **F** | Fleche + texte | Clic debut, clic fin, tapez votre texte |
| **R** | Rectangle | Cliquez et glissez |
| **P** | Polygone | Cliquez pour placer des points, double-cliquez pour fermer |
| **M** | Point (marqueur) | Simple clic |
| **C** | Cercle | Cliquez au centre puis au bord |
| **L** | Regle (mesure) | Cliquez sur le point de depart puis sur le point d'arrivee |
| **S** | Selection | Revenir au mode de selection |

### Actions

| Touche | Action |
|--------|--------|
| **Ctrl+Z** | Annuler la derniere action (50 niveaux) |
| **Ctrl+Y** | Refaire |
| **Suppr** / **Retour arriere** | Supprimer l'annotation selectionnee |
| **Echap** | Annuler le dessin en cours et revenir en selection |

### Correction IA

| Touche | Action |
|--------|--------|
| **V** | Valider la detection IA courante |
| **X** | Rejeter la detection (triage rapide, pas de motif) |
| **Shift+X** | Rejeter avec motif (selecteur de raison) |
| **Tab** | Passer a la detection suivante (saute les traitees) |

### Affichage

| Touche | Action |
|--------|--------|
| **H** | Masquer/afficher toutes les annotations et overlays |
| **Q** | Activer/desactiver le mode quiz (formation) |
| **1-5** | Zoom predefini (objectifs microscope : 2x, 5x, 10x, 20x, 40x) |

---

## Dessiner des Annotations

### Acceder aux Outils

1. Ouvrez une lame dans la visionneuse
2. La barre d'outils d'annotation est a gauche de la lame
3. Selectionnez l'outil ou utilisez le raccourci clavier

### Types de Traces

| Type | Raccourci | Usage | Comment |
|------|-----------|-------|---------|
| **Dessin libre** | D | Entourer rapidement une zone (60% des annotations) | Cliquez-glissez, relacher ferme |
| **Fleche + texte** | F | Pointer un detail avec un label | Clic debut, clic fin, tapez le texte |
| **Polygone** | P | Contour precis pour mesure de surface | Cliquez pour placer des points, double-cliquez pour fermer |
| **Rectangle** | R | Zone rectangulaire | Cliquez et glissez |
| **Point** | M | Marquer une cellule ou un element precis | Simple clic |
| **Cercle** | C | Zone circulaire | Cliquez au centre puis au bord |
| **Regle** | L | Mesurer une distance en mm | Cliquez depart et arrivee (non sauvegarde) |

### Outil Fleche avec Textes Pre-definis

Quand vous placez une fleche (touche F), un champ de saisie avec suggestions apparait :

- **Termes pre-definis** : Mitose, Mitose atypique, Invasion vasculaire, Invasion perineurale, Bordure de resection, Necrose, Inflammation, Artefact, A discuter en RCP
- **Historique recent** : vos termes les plus utilises apparaissent en premier
- Tapez pour filtrer, Entree pour valider, Echap pour annuler

### Annuler / Refaire

- **Ctrl+Z** annule la derniere annotation (creation, suppression ou modification)
- **Ctrl+Y** refait l'action annulee
- L'historique conserve les 50 dernieres actions
- L'historique est persiste au backend (les modifications sont reversibles)

---

## Notes et Tracabilite

### Ajouter des Notes a une Annotation

1. Cliquez sur une annotation sur la lame (ou via le hit-testing OSD)
2. Un **popover** apparait en bas a gauche avec :
   - Badge de type (IA / manuel)
   - Pourcentage de confiance (pour les detections IA)
   - Statut : en attente / valide / rejete (badge colore)
   - Label et couleur
   - Auteur et date de creation
   - Validateur et date de validation (si applicable)
3. Tapez vos notes dans le champ texte
4. Les notes sont **sauvegardees automatiquement** quand vous cliquez ailleurs (blur) ou Ctrl+Entree

### Valider ou Rejeter depuis le Popover

- Boutons **Valider** et **Rejeter** visibles uniquement pour les annotations en attente
- Chaque validation/rejet est trace (qui, quand) pour l'audit medicolegal
- Les corrections sur les detections IA alimentent le pipeline de re-entrainement du modele

---

## Etiquettes

### Etiquettes Pre-definies

| Etiquette | Couleur | Description |
|-----------|---------|-------------|
| **Tumeur** | Rouge | Zone tumorale identifiee |
| **Benin** | Vert | Tissu benin / normal |
| **Necrose** | Gris | Zone de necrose |
| **Inflammation** | Orange | Infiltrat inflammatoire |
| **A confirmer** | Bleu | Zone a discuter |
| **Stroma** | Violet | Tissu stromal |

### Etiquettes Personnalisees

Tapez un nom dans le champ d'etiquette pour creer une etiquette personnalisee a la volee.

---

## Correction des Predictions IA

### Workflow Rapide V/X/Tab

Apres une detection automatique (voir [07-ML_FEATURES.md](./07-ML_FEATURES.md)), les zones detectees apparaissent en pointilles oranges. Utilisez les raccourcis pour les traiter rapidement :

1. **Tab** : naviguer vers la premiere detection non traitee
2. **V** : valider (la zone est correcte) → avance automatiquement
3. **X** : rejeter (faux positif) → avance automatiquement
4. **Shift+X** : rejeter avec motif → selecteur de raison apparait :
   - Artefact
   - Inflammation
   - Contour imprecis
   - Autre
5. Repetez jusqu'au message "Toutes les zones ont ete traitees"

### Pourquoi les Motifs de Rejet Importent

Chaque motif de rejet est enregistre dans la base de donnees et utilise pour :
- **Analyser les faiblesses du modele** : "72% des faux positifs sont des artefacts"
- **Cibler le re-entrainement** : ameliorer specifiquement les cas problematiques
- **Documenter les decisions** : tracabilite complete pour l'audit

---

## Mode Quiz (Formation)

Le mode quiz est concu pour la formation des residents en pathologie.

### Activer le Mode Quiz

1. Appuyez sur **Q** → message "Quiz mode ON"
2. Toutes les annotations deviennent **grises** (couleurs et textes masques)
3. Un compteur apparait en haut a droite : "Quiz: 0/30 (0%)"

### Jouer le Quiz

1. Naviguez sur la lame et identifiez les zones annotees
2. **Cliquez** sur une annotation grise pour la reveler (couleur + label reels)
3. Le compteur se met a jour : "Quiz: 12/30 (40%)"
4. Essayez d'identifier toutes les annotations

### Terminer le Quiz

1. Appuyez sur **Q** pour desactiver
2. Un resume apparait : "Quiz termine : 22/30 (73%)"
3. La liste des annotations non revelees est affichee

### Usage Pedagogique

- Le formateur annote une lame avec des labels diagnostiques
- Le resident active le quiz et tente d'identifier les lesions
- Le score objectif permet de suivre la progression

---

## Panneau de Reporting

Le panneau de reporting (sidebar droite) affiche :

- **Statistiques de validation** : nombre d'annotations en attente, validees, rejetees avec barre de progression
- **Corrections IA** : nombre total de detections IA, pourcentage valide/rejete
- **Contributeurs** : tableau des annotateurs avec nombre d'annotations, validations, rejets
- **Timeline** : les 20 derniers evenements (creation, validation, rejet) avec auteur et date

---

## Dashboard Contributions IA

Le dashboard montre votre impact sur l'amelioration du modele IA :

- Nombre total de detections IA sur la lame courante
- Compteurs de la session : "Vous avez valide X, rejete Y"
- Indicateur de precision IA apres corrections
- Message : "Vos corrections sont enregistrees pour le prochain cycle d'amelioration du modele"

---

## Exporter les Annotations

### Formats d'Export

| Format | Extension | Usage |
|--------|-----------|-------|
| **GeoJSON** | `.geojson` | Standard geographique, compatible avec la plupart des outils |
| **CSV** | `.csv` | Tableau simple pour analyse statistique |

### Contenu de l'Export

L'export contient pour chaque annotation :
- Identifiant unique
- Coordonnees du trace (en pixels de la lame)
- Etiquette attribuee
- Auteur et date
- Statut de validation
- Notes

---

## Depannage

### La navigation est bloquee apres une detection IA

Ce probleme a ete corrige. La navigation (pan/zoom) fonctionne maintenant meme quand les zones de detection couvrent la lame entiere.

### Les raccourcis clavier ne fonctionnent pas

**Causes possibles :**
- Le focus est dans un champ texte (input, textarea) — les raccourcis sont desactives automatiquement
- Cliquez sur la lame pour reprendre le focus

### Les annotations ne s'enregistrent pas

**Causes possibles :**
- La base de donnees n'est pas configuree
- Probleme de connexion reseau

**Solution :**
1. Verifiez l'icone de connexion dans la barre d'etat
2. Rafraichissez la page et reessayez

---

## Prochaines Etapes

- **[07-ML_FEATURES.md](./07-ML_FEATURES.md)** : Decouvrez les detections automatiques
- **[08-QUALITE.md](./08-QUALITE.md)** : Comprenez le controle qualite
- **[05-VISUALISATION_LAMES.md](./05-VISUALISATION_LAMES.md)** : Revenez aux bases de la visualisation

---

**Version:** 2.0
**Derniere revision:** 2026-03-19
**Auteur:** Equipe VarunaPoC
