# Visualisation des Lames

**Statut:** En cours de developpement
**Derniere mise a jour:** 2026-02-17
**Fonctionnalite:** Visionneuse interactive de lames histologiques

---

## Vue d'Ensemble

VarunaPoC propose une visionneuse web interactive qui permet d'examiner des lames histologiques numerisees avec une precision allant jusqu'au niveau cellulaire. La navigation est similaire a Google Maps : zoom fluide, deplacement par glisser-deposer et chargement progressif des tuiles.

---

## Ouvrir une Lame

### Depuis l'Explorateur

1. Naviguez dans vos dossiers via la page d'accueil
2. Cliquez sur la tuile d'une lame (affichee avec un apercu miniature)
3. La visionneuse s'ouvre automatiquement en plein ecran

### Informations Affichees

Lorsque la lame est chargee, un panneau d'informations affiche :

- **Nom du fichier** et format detecte
- **Dimensions** en pixels (largeur x hauteur)
- **Nombre de niveaux** de la pyramide
- **Fabricant** du scanner (si disponible dans les metadonnees)
- **Grossissement** optique (ex : 20x, 40x)

---

## Zoom et Navigation

### Controles de Zoom

| Action | Methode |
|--------|---------|
| Zoom avant | Molette souris vers le haut OU bouton `+` |
| Zoom arriere | Molette souris vers le bas OU bouton `-` |
| Zoom sur zone | Double-clic sur la zone souhaitee |
| Reinitialiser le zoom | Bouton "Vue d'ensemble" |

### Deplacement (Pan)

- **Souris :** Cliquez et maintenez le bouton gauche, puis deplacez la souris
- **Tactile :** Glissez avec un doigt sur ecran tactile

### Barre de Grossissement

La barre de grossissement en bas de l'ecran indique le niveau de zoom actuel par rapport au grossissement optique reel de la lame. Par exemple :

```
|----[====]-------|
 1x    10x    40x
```

Ce repere vous aide a retrouver la meme echelle qu'au microscope optique.

### Mini-Carte (Navigator)

La mini-carte en bas a droite montre votre position actuelle sur la lame entiere :

- Le **rectangle colore** indique la zone visible a l'ecran
- Cliquez directement sur la mini-carte pour vous deplacer rapidement

---

## Mode Comparaison

Le mode comparaison permet d'afficher deux lames cote a cote pour comparer des coupes successives, des colorations differentes ou des cas similaires.

### Activer la Comparaison

1. Ouvrez une premiere lame dans la visionneuse
2. Cliquez sur le bouton **"Comparer"** dans la barre d'outils
3. Selectionnez la deuxieme lame dans la liste proposee
4. Les deux lames s'affichent cote a cote

### Navigation Synchronisee

En mode comparaison, les mouvements de zoom et de deplacement sont synchronises entre les deux vues. Deplacez-vous sur une lame et l'autre suit automatiquement.

**Note :** Cette fonctionnalite est en cours de developpement et peut ne pas etre disponible dans toutes les versions.

---

## Outils de Dessin

VarunaPoC propose des outils de dessin pour annoter directement sur la lame. Ces annotations sont enregistrees et peuvent etre partagees avec vos collegues.

### Outils Disponibles

| Outil | Description |
|-------|-------------|
| **Polygone** | Tracez un contour libre autour d'une region |
| **Rectangle** | Dessinez un rectangle de selection |
| **Cercle** | Placez un cercle sur une zone d'interet |
| **Fleche** | Pointez vers un element specifique |
| **Texte** | Ajoutez une note textuelle |

### Comment Dessiner

1. Selectionnez un outil dans la barre laterale
2. Cliquez sur la lame pour commencer le trace
3. Deplacez la souris pour definir la forme
4. Cliquez une deuxieme fois pour terminer (ou double-cliquez pour les polygones)
5. Ajoutez un libelle ou une etiquette si souhaite

### Enregistrer les Annotations

Les annotations sont sauvegardees automatiquement sur le serveur. Vous pouvez les retrouver lors de votre prochaine visite.

Pour plus de details sur les annotations, consultez [06-ANNOTATIONS.md](./06-ANNOTATIONS.md).

---

## Raccourcis Utiles

| Raccourci | Action |
|-----------|--------|
| Molette souris | Zoom avant/arriere |
| Double-clic | Zoom sur la position du curseur |
| Clic + glisser | Deplacement dans la lame |
| `Echap` | Quitter la visionneuse et revenir a la liste |

---

## Depannage

### La lame ne se charge pas

**Causes possibles :**
- Le fichier est corrompu ou incomplet
- Le format n'est pas supporte (consultez [04-FORMATS_SUPPORTES.md](./04-FORMATS_SUPPORTES.md))
- Les fichiers compagnons sont manquants (pour les formats MRXS, VMS)

**Solution :**
1. Verifiez que le fichier apparait avec un statut vert dans l'explorateur
2. Essayez de rafraichir la page (F5)
3. Contactez le support technique avec le message d'erreur

### Le zoom est saccade

**Cause probable :** Connexion reseau lente ou carte graphique non acceleree

**Solution :**
- Verifiez votre connexion reseau (minimum 10 Mbps recommande)
- Activez l'acceleration materielle dans les parametres de votre navigateur
- Utilisez Chrome ou Edge pour de meilleures performances

---

## Prochaines Etapes

- **[06-ANNOTATIONS.md](./06-ANNOTATIONS.md)** : Apprenez a annoter vos lames
- **[07-ML_FEATURES.md](./07-ML_FEATURES.md)** : Decouvrez les fonctionnalites d'intelligence artificielle
- **[99-FAQ.md](./99-FAQ.md)** : Questions frequentes

---

**Version:** 1.0
**Derniere revision:** 2026-02-17
**Auteur:** Equipe VarunaPoC
