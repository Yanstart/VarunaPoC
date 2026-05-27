# Fonctionnalites d'Intelligence Artificielle

**Statut:** Fonctionnel
**Derniere mise a jour:** 2026-03-19
**Fonctionnalite:** Panneau ML, detection, focus assist, auto-tag, comptage cellulaire, recherche de similarite

---

## Vue d'Ensemble

VarunaPoC integre des outils d'intelligence artificielle (IA) concu pour assister les pathologistes dans leur travail quotidien. Ces outils ne remplacent pas le diagnostic humain : ils servent d'aide a la decision en mettant en evidence des regions d'interet, en automatisant des taches repetitives et en accelerant l'analyse.

**Important :** Toutes les predictions de l'IA doivent etre validees par un pathologiste qualifie avant toute utilisation clinique.

---

## Panneau ML

### Acceder au Panneau

1. Ouvrez une lame dans la visionneuse
2. Cliquez sur l'icone **"IA"** dans la barre laterale droite
3. Le panneau ML s'ouvre avec les outils disponibles

### Contenu du Panneau

Le panneau ML regroupe tous les outils d'intelligence artificielle :

| Outil | Description |
|-------|-------------|
| **Detection** | Detecte automatiquement les regions d'interet |
| **Focus Assist** | Identifie les zones les plus pertinentes |
| **Auto-Tag** | Classifie automatiquement l'organe et la coloration |
| **Comptage Cellulaire** | Compte les cellules positives/negatives |
| **Similarite** | Recherche des lames similaires |
| **Heatmap** | Affiche une carte de chaleur d'attention |

---

## Detection Automatique

### Principe

La detection automatique analyse la lame entiere et identifie les regions susceptibles de contenir du tissu tumoral ou des zones d'interet. Les regions detectees sont affichees sous forme de contours colores superposes a la lame.

### Comment l'Utiliser

1. Dans le panneau ML, cliquez sur **"Lancer la detection"**
2. L'analyse commence (quelques secondes a quelques minutes selon la taille)
3. Les regions detectees apparaissent en surbrillance sur la lame
4. Pour chaque region, vous pouvez :
   - **Confirmer** : La detection est correcte
   - **Rejeter** : Faux positif a ignorer
   - **Corriger** : Modifier le contour ou l'etiquette

### Parametres

| Parametre | Description | Valeur par defaut |
|-----------|-------------|-------------------|
| **Seuil de confiance** | Score minimum pour afficher une detection | 0.5 |
| **Surface minimale** | Taille minimale des regions (pixels carre) | 100 |
| **Classe cible** | Type de tissu recherche | "tissue" |

---

## Focus Assist

### Principe

Focus Assist identifie les N zones les plus interessantes d'une lame et vous y amene directement. Cela evite de parcourir manuellement toute la surface pour trouver les zones significatives.

### Comment l'Utiliser

1. Cliquez sur **"Focus Assist"** dans le panneau ML
2. Une liste de zones apparait, classees par score d'interet
3. Cliquez sur une zone pour y naviguer instantanement
4. Examinez la zone et passez a la suivante

### Informations Affichees

Pour chaque zone, le panneau affiche :

- **Rang** : Position dans le classement (1 = plus interessant)
- **Score** : Niveau de confiance (0 a 1)
- **Localisation** : Coordonnees sur la lame
- **Surface** : Taille de la zone en pixels carre

---

## Auto-Tag

### Principe

L'Auto-Tag analyse les metadonnees et le contenu de la lame pour identifier automatiquement :

- **L'organe** : Sein, colon, prostate, rein, foie, poumon, etc.
- **La coloration** : HE (Hematoxiline-Eosine), IHC, PAS, etc.
- **Le marqueur** : Ki-67, CD3, CD20, etc. (pour les lames IHC)

### Comment l'Utiliser

1. L'Auto-Tag s'execute automatiquement a l'ouverture de la lame
2. Les tags detectes apparaissent dans le panneau d'informations
3. Vous pouvez corriger les tags si necessaire

### Utilite

Les tags sont utilises pour :
- **Router automatiquement** la lame vers le modele d'IA adapte
- **Organiser** les lames dans la base de donnees
- **Filtrer** les lames lors de la recherche

---

## Comptage Cellulaire

### Principe

Le comptage cellulaire automatise l'evaluation des index immunohistochimiques (ex : Ki-67, index mitotique). L'outil identifie les cellules positives et negatives et calcule le ratio.

### Comment l'Utiliser

1. Ouvrez une lame IHC dans la visionneuse
2. Cliquez sur **"Comptage Cellulaire"** dans le panneau ML
3. Selectionnez le marqueur (par defaut : Ki-67)
4. Optionnellement, dessinez une region pour limiter le comptage
5. Lancez l'analyse

### Resultat

| Champ | Description |
|-------|-------------|
| **Cellules totales** | Nombre total de cellules detectees |
| **Positives** | Nombre de cellules marquees positivement |
| **Negatives** | Nombre de cellules negatives |
| **Ratio** | Positives / Totales |
| **Pourcentage** | Ratio exprime en pourcentage |

---

## Recherche de Similarite

### Principe

La recherche de lames similaires est **multi-critere** : l'utilisateur compose lui-meme sa requete en cochant les dimensions de similarite qui l'interessent (technique, apparence visuelle, semantique, workflow clinique). Aucune definition unique n'est imposee — le pathologiste sait ce qu'il cherche.

> **Conception detaillee :** voir [`docs/architecture/SIMILARITY_DESIGN.md`](../architecture/SIMILARITY_DESIGN.md) — categories de criteres, flow, contrat API, strategie de cache et hors-scope.

### Comment l'Utiliser

1. Ouvrez une lame dans la visionneuse
2. Cliquez sur **"Lames similaires"** dans le panneau ML (accordeon)
3. Cochez les criteres de comparaison parmi les 4 categories disponibles
4. Cliquez sur **"Rechercher"**
5. Les lames les plus similaires s'affichent avec leur score global et le detail par critere (au survol)
6. Cliquez sur une vignette pour ouvrir la lame correspondante

### Cas d'Usage

- Retrouver des cas similaires pour comparaison diagnostique (criteres semantique + workflow)
- Identifier des groupes de lames morphologiquement proches (criteres apparence visuelle)
- Recherche dans les archives par contenu visuel (criteres apparence + technique)
- Audit des lames analysees par un meme modele AI (criteres workflow)

---

## Heatmap d'Attention

### Principe

La heatmap superpose une carte de chaleur semi-transparente sur la lame. Les zones chaudes (rouges) correspondent aux regions ou le modele d'IA porte le plus d'attention, tandis que les zones froides (bleues) sont considerees comme moins pertinentes.

### Interpretation

- **Rouge / jaune :** Region a forte activite, probablement pertinente
- **Vert :** Region a activite moderee
- **Bleu / transparent :** Region a faible activite, probablement du fond ou du tissu normal

**Attention :** La heatmap est un outil de visualisation. Elle ne constitue pas un diagnostic.

---

## Modeles d'Embeddings Disponibles

VarunaPoC supporte plusieurs modeles de fondation pour l'extraction d'embeddings :

| Modele | Dimensions | Description |
|--------|------------|-------------|
| **UNI** | 1024 | Harvard -- Modele de reference en pathologie |
| **Phikon** | 768 | Owkin -- Base DINOv2 pour la pathologie |
| **Virchow** | 1280 | Paige/Microsoft -- Grand modele pathologie |
| **CTransPath** | 768 | Swin Transformer pour la pathologie |

Le modele par defaut est **UNI**, qui offre actuellement les meilleures performances generales.

---

## Selection du Device (GPU/CPU)

Le panneau ML inclut un selecteur de device :

- **Auto** : detecte automatiquement le GPU (recommande)
- **GPU (CUDA)** : force l'utilisation du GPU pour des analyses plus rapides et precises
- **CPU** : utilise le processeur (plus lent mais fonctionne partout)

Le statut du GPU est affiche a cote du selecteur (nom de la carte graphique si detectee).

**Note :** Le changement de device relance le worker ML. Les analyses en cours sont interrompues.

---

## Depannage

### L'IA ne se lance pas

**Causes possibles :**
- Les services ML ne sont pas actifs sur le serveur
- La lame utilise un format non supporte pour l'analyse ML (ex : DICOM)

**Solution :**
1. Verifiez que le panneau ML affiche "Service disponible"
2. Consultez l'administrateur pour verifier la configuration du serveur

### Les detections semblent incorrectes

**Cela peut arriver dans les cas suivants :**
- Coloration inhabituelle ou mal standardisee
- Artefacts importants sur la lame (plis, bulles, zones floues)
- Type de tissu non couvert par le modele d'entrainement

**Solution :**
1. Utilisez les boutons de retour pour corriger les detections
2. Ajustez le seuil de confiance (augmentez-le pour moins de faux positifs)
3. Signalez les cas problematiques a l'equipe technique

---

## Prochaines Etapes

- **[06-ANNOTATIONS.md](./06-ANNOTATIONS.md)** : Annotez et corrigez les detections
- **[08-QUALITE.md](./08-QUALITE.md)** : Comprenez le controle qualite des lames et des modeles
- **[99-FAQ.md](./99-FAQ.md)** : Questions frequentes

---

**Version:** 2.0
**Derniere revision:** 2026-03-19
**Auteur:** Equipe VarunaPoC
