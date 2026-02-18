# Annotations

**Statut:** En cours de developpement
**Derniere mise a jour:** 2026-02-17
**Fonctionnalite:** Annotations, etiquettes et retour utilisateur

---

## Vue d'Ensemble

Le module d'annotations permet aux pathologistes de dessiner directement sur les lames numerisees pour marquer des regions d'interet, ajouter des diagnostics et fournir un retour sur les predictions de l'intelligence artificielle. Toutes les annotations sont enregistrees au format GeoJSON et associees a la lame correspondante.

---

## Dessiner des Annotations

### Acceder aux Outils

1. Ouvrez une lame dans la visionneuse
2. Le panneau d'annotations est accessible via le bouton **"Annoter"** dans la barre laterale
3. Selectionnez l'outil de dessin souhaite

### Types de Traces

| Type | Usage | Comment |
|------|-------|---------|
| **Polygone** | Entourer une tumeur, une zone de necrose | Cliquez pour placer des points, double-cliquez pour fermer |
| **Rectangle** | Selectionner une zone rectangulaire | Cliquez et glissez |
| **Point** | Marquer une cellule ou un element precis | Simple clic |
| **Ligne** | Mesurer une distance | Cliquez sur le point de depart puis sur le point d'arrivee |

### Modifier une Annotation

- **Deplacer :** Cliquez sur l'annotation, maintenez et deplacez
- **Redimensionner :** Utilisez les poignees aux coins de la selection
- **Supprimer :** Selectionnez l'annotation puis appuyez sur la touche `Suppr`

---

## Etiquettes et Presets

### Attribuer une Etiquette

Apres avoir dessine une annotation, une fenetre contextuelle vous propose d'attribuer une etiquette parmi les presets disponibles :

| Etiquette | Couleur | Description |
|-----------|---------|-------------|
| **Tumeur** | Rouge | Zone tumorale identifiee |
| **Necrose** | Jaune | Zone de necrose |
| **Stroma** | Bleu | Tissu stromal |
| **Normal** | Vert | Tissu sain |
| **Artefact** | Gris | Zone de mauvaise qualite (pli, bulle) |
| **Autre** | Violet | Classification libre |

### Presets Personnalises

Les administrateurs peuvent configurer des presets d'etiquettes supplementaires adaptes aux besoins specifiques de votre laboratoire (par exemple : Gleason 3, Gleason 4, Gleason 5 pour la prostate).

---

## Boutons de Retour (Feedback)

Lorsque l'intelligence artificielle propose une detection automatique (voir [07-ML_FEATURES.md](./07-ML_FEATURES.md)), des boutons de retour apparaissent pour chaque region detectee :

| Bouton | Action | Signification |
|--------|--------|---------------|
| **Confirmer** | Valide la detection | La prediction est correcte |
| **Rejeter** | Supprime la detection | Faux positif |
| **Corriger** | Modifie le contour ou l'etiquette | La detection est partiellement correcte |
| **Re-etiqueter** | Change la classe attribuee | La region est correcte mais mal classee |

### Pourquoi le Retour est Important

Chaque correction fournie par le pathologiste est enregistree et utilisee pour :

1. **Ameliorer le modele** : Les corrections alimentent le pipeline de re-entrainement
2. **Suivre la qualite** : Le taux de rejet est surveille pour detecter une derive du modele
3. **Documenter les decisions** : Chaque correction est tracee pour l'audit

---

## Exporter les Annotations

### Formats d'Export

Les annotations peuvent etre exportees dans les formats suivants :

| Format | Extension | Usage |
|--------|-----------|-------|
| **GeoJSON** | `.geojson` | Standard geographique, compatible avec la plupart des outils |
| **CSV** | `.csv` | Tableau simple pour analyse statistique |

### Comment Exporter

1. Ouvrez la lame contenant les annotations
2. Cliquez sur le bouton **"Exporter"** dans le panneau d'annotations
3. Selectionnez le format souhaite
4. Le fichier est telecharge automatiquement dans votre dossier de telechargements

### Contenu de l'Export

L'export contient pour chaque annotation :

- **Identifiant unique** de l'annotation
- **Coordonnees** du trace (en pixels de la lame)
- **Etiquette** attribuee
- **Auteur** de l'annotation
- **Date et heure** de creation
- **Commentaires** eventuels

---

## Bonnes Pratiques

### Pour les Pathologistes

- Utilisez les **etiquettes standardisees** pour faciliter l'analyse ulterieure
- Fournissez un **retour systematique** sur les detections automatiques
- Ajoutez des **commentaires** lorsque le cas est ambigu
- Exportez regulierement vos annotations pour sauvegarde

### Pour les Administrateurs

- Configurez des **presets d'etiquettes** adaptes a chaque type d'etude
- Surveillez les **statistiques de retour** pour evaluer la qualite des modeles
- Planifiez des **exports reguliers** pour alimenter les jeux de donnees d'entrainement

---

## Depannage

### Les annotations ne s'enregistrent pas

**Causes possibles :**
- La base de donnees n'est pas configuree
- Probleme de connexion reseau

**Solution :**
1. Verifiez l'icone de connexion dans la barre d'etat
2. Rafraichissez la page et reessayez
3. Contactez l'administrateur si le probleme persiste

### Les etiquettes ne s'affichent pas

**Cause probable :** Les presets d'etiquettes ne sont pas charges

**Solution :**
- Verifiez la configuration des presets dans les parametres d'administration
- Rafraichissez la page

---

## Prochaines Etapes

- **[07-ML_FEATURES.md](./07-ML_FEATURES.md)** : Decouvrez les detections automatiques
- **[08-QUALITE.md](./08-QUALITE.md)** : Comprenez le controle qualite
- **[05-VISUALISATION_LAMES.md](./05-VISUALISATION_LAMES.md)** : Revenez aux bases de la visualisation

---

**Version:** 1.0
**Derniere revision:** 2026-02-17
**Auteur:** Equipe VarunaPoC
