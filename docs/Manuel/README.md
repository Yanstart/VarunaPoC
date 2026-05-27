# Manuel Utilisateur - VarunaPoC

**Version:** 1.1
**Date de dernière mise à jour:** 2026-05-07
**Public cible:** Utilisateurs finaux (médecins, techniciens de laboratoire, chercheurs)

---

## Bienvenue dans VarunaPoC

VarunaPoC est une visionneuse web de lames histologiques haute résolution développée pour le CHU UCL Namur. Ce manuel vous guide dans l'utilisation de l'application.

---

## Organisation du Manuel

Ce manuel est organisé par fonctionnalité validée et prête à l'emploi:

### 📚 Documents Disponibles

0. **[00-DEMARRAGE_INFRA.md](./00-DEMARRAGE_INFRA.md)**
   Procédure de lancement de la stack Docker complète (dev / démo / captures)

1. **[01-INTRODUCTION.md](./01-INTRODUCTION.md)**
   Présentation générale, prérequis système, premiers pas

2. **[02-NAVIGATION_DOSSIERS.md](./02-NAVIGATION_DOSSIERS.md)**
   Comment naviguer dans vos dossiers de lames (explorateur intégré)

3. **[03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md)**
   Comment organiser vos fichiers de lames sur le disque (structures requises)

4. **[04-FORMATS_SUPPORTES.md](./04-FORMATS_SUPPORTES.md)**
   Liste complète des formats de lames supportés et leurs particularités

5. **[05-VISUALISATION_LAMES.md](./05-VISUALISATION_LAMES.md)**
   Comment ouvrir et naviguer dans une lame (zoom, déplacement, mini-carte)

6. **[06-ANNOTATIONS.md](./06-ANNOTATIONS.md)**
   Création, édition, validation et rejet d'annotations (CRUD + batch)

7. **[07-ML_FEATURES.md](./07-ML_FEATURES.md)**
   Détection, prédiction, heatmap, comptage cellulaire (assistance IA)

8. **[08-QUALITE.md](./08-QUALITE.md)**
   Métriques d'accord inter-annotateurs (kappa de Cohen et Fleiss)

9. **[99-FAQ.md](./99-FAQ.md)**
   Questions fréquentes et dépannage

---

## Démarrage Rapide

### Étape 1: Accéder à l'Application

Ouvrez votre navigateur web et accédez à:
```
http://localhost:5173
```

### Étape 2: Naviguer dans vos Lames

1. La page d'accueil affiche vos dossiers de lames
2. Cliquez sur un dossier pour explorer son contenu
3. Cliquez sur une lame pour l'ouvrir dans la visionneuse

### Étape 3: Visualiser une Lame

- **Zoom:** Molette de la souris ou boutons +/-
- **Déplacement:** Cliquez-glissez avec la souris
- **Vue d'ensemble:** Mini-carte en bas à droite

---

## Formats de Lames Supportés

VarunaPoC supporte les formats suivants:

| Format | Extension | Fabricant | Statut |
|--------|-----------|-----------|--------|
| Aperio SVS | `.svs` | Leica/Aperio | ✅ Validé |
| Hamamatsu NDPI | `.ndpi` | Hamamatsu | ✅ Validé |
| Ventana BIF | `.bif` | Roche/Ventana | ✅ Validé (patch appliqué) |
| MIRAX | `.mrxs` | 3DHistech | ✅ Validé |
| Generic TIFF | `.tif`, `.tiff` | Divers | ✅ Validé |
| Leica SCN | `.scn` | Leica | ⚠️ En cours |
| DICOM | `.dcm` | Standard médical | 🔄 Développement |

**Légende:**
- ✅ Validé: Fonctionnel et testé
- ⚠️ En cours: Support partiel, tests en cours
- 🔄 Développement: Fonctionnalité en cours d'implémentation

---

## Support et Assistance

### Signaler un Problème

Si vous rencontrez un problème:

1. Consultez la [FAQ](./99-FAQ.md)
2. Vérifiez que votre fichier de lame respecte les [règles d'organisation](./03-ORGANISATION_LAMES.md)
3. Contactez le support technique avec:
   - Description du problème
   - Type de fichier (extension)
   - Message d'erreur affiché (si applicable)

### Contact

**Support Technique:** [À définir]
**Documentation Développeur:** Voir `/docs/ERROR_*.md` et `CLAUDE.md`

---

## Mises à Jour du Manuel

Ce manuel est mis à jour automatiquement par l'agent de développement chaque fois qu'une nouvelle fonctionnalité est validée et prête à l'emploi.

**Historique des versions:**
- **v1.0 (2025-10-21):** Version initiale avec navigation dossiers et formats de base
- **v1.1 (2026-05-07):** Index complété avec annotations (06), IA assistance (07) et qualité (08)

---

**Note aux Développeurs:**
Pour mettre à jour ce manuel, voir les instructions dans `CLAUDE.md` section "Protocole de Mise à Jour du Manuel Utilisateur".
