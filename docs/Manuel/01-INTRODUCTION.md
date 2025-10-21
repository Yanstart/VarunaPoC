# Introduction à VarunaPoC

**Statut:** ✅ Validé et prêt à l'emploi
**Dernière mise à jour:** 2025-10-21

---

## Qu'est-ce que VarunaPoC?

VarunaPoC est une **visionneuse web de lames histologiques** développée spécifiquement pour le CHU UCL Namur. Elle permet de visualiser des lames numérisées haute résolution (gigapixels) directement dans votre navigateur web, sans installation de logiciel supplémentaire.

### Pourquoi VarunaPoC?

**Avantages:**
- ✅ Accès via navigateur web (pas d'installation)
- ✅ Compatible tous fabricants (vendor-neutral)
- ✅ Navigation fluide type Google Maps
- ✅ Sécurisé et conforme aux normes médicales
- ✅ Performances optimisées (streaming de tuiles)

**Cas d'usage:**
- Diagnostic anatomopathologique
- Revue de cas entre collègues
- Enseignement et formation
- Recherche et archivage numérique

---

## Prérequis Système

### Navigateur Web

VarunaPoC fonctionne avec les navigateurs modernes:

| Navigateur | Version Minimale | Statut |
|------------|------------------|--------|
| Google Chrome | 90+ | ✅ Recommandé |
| Microsoft Edge | 90+ | ✅ Recommandé |
| Mozilla Firefox | 88+ | ✅ Supporté |
| Safari | 14+ | ⚠️ Non testé |

**Recommandation:** Utilisez Chrome ou Edge pour une expérience optimale.

### Configuration Minimale

**Pour visualisation basique:**
- Processeur: Intel Core i3 ou équivalent
- RAM: 4 GB
- Connexion réseau: 10 Mbps

**Pour visualisation optimale:**
- Processeur: Intel Core i5 ou supérieur
- RAM: 8 GB ou plus
- Connexion réseau: 100 Mbps ou plus
- Carte graphique: GPU avec accélération matérielle

---

## Premiers Pas

### 1. Accéder à l'Application

Ouvrez votre navigateur et accédez à l'URL fournie par votre administrateur système:

```
http://localhost:5173  (environnement de développement)
ou
http://[adresse-serveur]:[port]  (environnement de production)
```

### 2. Interface Principale

L'interface se compose de deux zones principales:

**A. Page d'Accueil (Home)**
- Explorateur de dossiers
- Liste des lames disponibles
- Barre de recherche
- Bouton "Ouvrir fichier local"

**B. Visionneuse (Viewer)**
- Zone de visualisation principale
- Contrôles de zoom (+/-)
- Mini-carte de navigation
- Informations sur la lame

### 3. Navigation Basique

**Ouvrir une lame:**
1. Naviguez dans vos dossiers
2. Cliquez sur une lame (tuile avec aperçu)
3. La visionneuse s'ouvre automatiquement

**Naviguer dans une lame:**
- **Zoom in:** Molette souris vers le haut OU bouton `+`
- **Zoom out:** Molette souris vers le bas OU bouton `-`
- **Déplacement:** Cliquez-glissez avec la souris
- **Retour accueil:** Bouton "Retour" ou logo VarunaPoC

---

## Concepts Clés

### Lames Numériques Pyramidales

Les lames histologiques numérisées sont stockées en **format pyramidal**:

```
Niveau 0 (max résolution): 100,000 x 80,000 pixels
Niveau 1 (2x réduit):       50,000 x 40,000 pixels
Niveau 2 (4x réduit):       25,000 x 20,000 pixels
Niveau 3 (8x réduit):       12,500 x 10,000 pixels
...
Niveau N (min résolution):   1,000 x 800 pixels
```

**Avantage:** VarunaPoC charge uniquement les parties visibles au niveau de zoom approprié → performances optimales.

### Streaming de Tuiles

Au lieu de charger l'image complète (plusieurs gigaoctets), VarunaPoC charge des **tuiles** (carrés de 256x256 pixels) à la demande:

```
[Zoom faible] → Charge tuiles niveau 5 (petite taille)
[Zoom moyen]  → Charge tuiles niveau 2 (taille moyenne)
[Zoom max]    → Charge tuiles niveau 0 (haute résolution)
```

**Résultat:** Navigation fluide même sur connexions modestes.

### Fichiers Companions

Certains formats nécessitent plusieurs fichiers:

**Exemple MIRAX (.mrxs):**
```
sample.mrxs           ← Fichier principal (petit)
sample/               ← Dossier companion (REQUIS!)
  ├── Slidedat.ini    ← Métadonnées
  ├── Data0000.dat    ← Données image
  └── Index.dat       ← Index des tuiles
```

⚠️ **Important:** Ne déplacez JAMAIS un fichier `.mrxs` sans son dossier companion!

Voir [03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md) pour plus de détails.

---

## Fonctionnalités Disponibles (Phase Actuelle)

### ✅ Fonctionnalités Validées

1. **Navigation Dossiers**
   - Explorateur de fichiers hiérarchique
   - Recherche par nom de lame
   - Détection automatique des formats

2. **Visualisation Lames**
   - Zoom fluide (10+ niveaux)
   - Déplacement par glisser-déposer
   - Mini-carte de localisation
   - Chargement progressif des tuiles

3. **Formats Supportés**
   - Aperio SVS (`.svs`)
   - Hamamatsu NDPI (`.ndpi`)
   - Ventana BIF (`.bif`) - patch appliqué
   - MIRAX (`.mrxs`)
   - Generic TIFF (`.tif`, `.tiff`)

### 🔄 Fonctionnalités en Développement

- Annotations et mesures
- Export d'images
- Intégration PACS
- Comparaison de lames côte-à-côte
- Recherche par métadonnées (patient, date, diagnostic)

---

## Limitations Actuelles

### Phase PoC (Proof of Concept)

VarunaPoC est actuellement en phase de **validation de concept**. Certaines fonctionnalités avancées ne sont pas encore disponibles:

❌ **Non supporté actuellement:**
- Annotations/dessins sur les lames
- Mesures de distance/surface
- Authentification utilisateur (sécurité basique uniquement)
- Collaboration multi-utilisateurs
- Applications mobiles natives

### Formats en Cours de Validation

Certains formats sont détectés mais peuvent ne pas s'ouvrir:

- **Leica SCN (`.scn`):** Support partiel, tests en cours
- **DICOM (`.dcm`):** Développement en cours
- **Carl Zeiss CZI (`.czi`):** Planifié pour phase 2

Si un fichier est détecté mais marqué "Non supporté", consultez la [FAQ](./99-FAQ.md).

---

## Sécurité et Confidentialité

### Protection des Données Médicales

VarunaPoC respecte les normes de sécurité médicales:

- ✅ Accès limité au répertoire `/Slides` uniquement
- ✅ Pas de téléchargement de données sensibles dans les logs
- ✅ Path traversal bloqué (sécurité contre accès non autorisés)
- ✅ Authentification (à configurer en production)

### Bonnes Pratiques

1. **Ne partagez jamais** l'URL de l'application en dehors du réseau sécurisé
2. **Fermez votre navigateur** après utilisation
3. **Vérifiez** que les données patients sont anonymisées si nécessaire
4. **Contactez l'administrateur** en cas de comportement suspect

---

## Support et Ressources

### Documentation Complémentaire

- **[Manuel Utilisateur](./README.md):** Index de tous les documents
- **[Navigation Dossiers](./02-NAVIGATION_DOSSIERS.md):** Guide détaillé de l'explorateur
- **[Organisation Lames](./03-ORGANISATION_LAMES.md):** Comment structurer vos fichiers
- **[Formats Supportés](./04-FORMATS_SUPPORTES.md):** Liste complète et particularités
- **[FAQ](./99-FAQ.md):** Questions fréquentes et dépannage

### Contact Support

**En cas de problème:**
1. Consultez la FAQ
2. Vérifiez les logs d'erreur (si affiché à l'écran)
3. Contactez votre support technique avec:
   - Description du problème
   - Navigateur utilisé (Chrome/Firefox/Edge + version)
   - Type de fichier concerné
   - Message d'erreur (capture d'écran si possible)

---

## Prochaines Étapes

Une fois familiarisé avec l'interface, consultez:

1. **[02-NAVIGATION_DOSSIERS.md](./02-NAVIGATION_DOSSIERS.md)**
   Apprenez à naviguer efficacement dans vos dossiers de lames

2. **[03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md)**
   Comprenez comment organiser vos fichiers pour une détection optimale

3. **[05-VISUALISATION_LAMES.md](./05-VISUALISATION_LAMES.md)**
   Maîtrisez les fonctions avancées de visualisation

---

**Version:** 1.0
**Dernière révision:** 2025-10-21
**Auteur:** Équipe VarunaPoC
