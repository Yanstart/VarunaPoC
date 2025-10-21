# Navigation dans les Dossiers de Lames

**Statut:** ✅ Validé et prêt à l'emploi
**Dernière mise à jour:** 2025-10-21
**Fonctionnalité:** Explorateur de fichiers hiérarchique intégré

---

## Vue d'Ensemble

VarunaPoC intègre un **explorateur de fichiers** permettant de naviguer dans vos dossiers de lames histologiques de manière intuitive, similaire à l'explorateur Windows ou macOS.

### Concept Clé: Racine des Slides

Tous vos fichiers de lames sont stockés dans un **répertoire racine**:

```
C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Slides
```

**Sécurité:** Vous ne pouvez **pas** remonter au-delà de cette racine (protection contre accès non autorisés).

---

## Interface de Navigation

### Page d'Accueil

Lorsque vous accédez à VarunaPoC, vous voyez:

```
┌─────────────────────────────────────────────────────┐
│  VarunaPoC - Histological Slide Viewer              │
├─────────────────────────────────────────────────────┤
│  [🔍 Rechercher une lame...]  [📂 Ouvrir fichier]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  📁 3DHistech/          (12 items)                   │
│  📁 ROCHE/              (8 items)                    │
│  📁 projects/           (25 items)                   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Éléments de l'Interface

1. **Barre de recherche:** Filtrer les lames par nom
2. **Bouton "Ouvrir fichier":** Sélectionner un fichier depuis votre ordinateur (fonctionnalité future)
3. **Liste de dossiers:** Dossiers disponibles à la racine
4. **Compteur d'items:** Nombre de fichiers/sous-dossiers dans chaque dossier

---

## Naviguer dans les Dossiers

### Ouvrir un Dossier

**Action:** Cliquez sur un dossier

**Résultat:** Le contenu du dossier s'affiche

**Exemple:**
```
Avant (racine "/"):
  📁 3DHistech/
  📁 ROCHE/
  📁 projects/

Après clic sur "3DHistech":
  🏠 / > 3DHistech

  📁 kidney_samples/
  📁 liver_samples/
  🔬 sample_001.mrxs  [MIRAX - 3DHistech]
  🔬 sample_002.mrxs  [MIRAX - 3DHistech]
```

### Fil d'Ariane (Breadcrumb)

Le **fil d'Ariane** affiche votre position actuelle:

```
🏠 / > 3DHistech > kidney_samples > batch_2024
     ↑      ↑            ↑              ↑
   Racine  Dossier   Sous-dossier   Sous-sous-dossier
```

**Navigation rapide:** Cliquez sur n'importe quel segment pour y revenir directement.

**Exemples:**
- Cliquer sur `/` → Retour à la racine
- Cliquer sur `3DHistech` → Retour au dossier 3DHistech
- Cliquer sur `kidney_samples` → Retour au sous-dossier kidney_samples

### Remonter au Dossier Parent

**Méthode 1:** Cliquez sur le segment parent dans le fil d'Ariane

**Méthode 2:** Bouton "⬆️ Dossier parent" (si disponible)

**Limitation:** Vous ne pouvez **pas** remonter au-delà de la racine `/Slides`.

---

## Affichage du Contenu

### Types d'Items Affichés

Chaque dossier peut contenir:

1. **📁 Sous-dossiers**
2. **🔬 Lames histologiques** (fichiers supportés)
3. **📄 Fichiers non-slides** (fichiers non reconnus)

### Lames Histologiques (Tuiles)

Les lames sont affichées sous forme de **tuiles** avec informations détaillées:

```
┌─────────────────────────────────┐
│  [Aperçu miniature]             │
│                                  │
│  sample_kidney_001.mrxs         │
│  Format: MIRAX                   │
│  Structure: Avec dossier comp.  │
│  Dimensions: 80,000 x 60,000    │
│  ✅ Prêt à ouvrir                │
└─────────────────────────────────┘
```

**Informations affichées:**
- **Nom du fichier**
- **Format détecté** (ex: MIRAX, Aperio SVS, etc.)
- **Type de structure** (fichier unique, multi-fichiers, companion)
- **Dimensions** (si disponible)
- **Statut:** ✅ Prêt / ⚠️ Avertissement / ❌ Non supporté

### Fichiers Non Supportés

Si un fichier est détecté mais non ouvrable:

```
┌─────────────────────────────────┐
│  sample_unknown.scn              │
│  ❌ Non supporté                  │
│  Raison: Format en cours de test │
└─────────────────────────────────┘
```

**Actions possibles:**
- Consulter la [FAQ](./99-FAQ.md)
- Contacter le support technique
- Vérifier que les fichiers companions sont présents (voir [03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md))

---

## Recherche de Lames

### Barre de Recherche

La barre de recherche en haut de page permet de **filtrer** les lames par nom:

**Exemple:**
```
[🔍 Rechercher: "kidney"]

Résultats affichés:
  🔬 sample_kidney_001.mrxs
  🔬 sample_kidney_002.mrxs
  🔬 patient_kidney_tumor.svs

Masqués:
  sample_liver_001.mrxs  (ne contient pas "kidney")
  sample_brain_001.ndpi  (ne contient pas "kidney")
```

**Fonctionnement:**
- **Temps réel:** Les résultats se mettent à jour pendant la frappe
- **Non sensible à la casse:** "Kidney" = "kidney" = "KIDNEY"
- **Recherche partielle:** "kid" trouve "kidney"
- **Portée:** Recherche uniquement dans le **dossier actuel** (non récursif)

### Recherche dans Tous les Dossiers

**Méthode:** Utilisez la recherche depuis la **racine** (`/`)

```
Position: 🏠 /
Recherche: "patient"

Résultats:
  📁 projects/ > patients_2024/
  🔬 ROCHE/ > patient_001.bif
  🔬 3DHistech/ > patient_kidney.mrxs
```

---

## Ouvrir une Lame

### Depuis la Liste

**Action:** Cliquez sur une tuile de lame

**Résultat:** La visionneuse s'ouvre en plein écran

**Transition:**
```
Page d'Accueil (Home)
         ↓
    [Clic sur lame]
         ↓
 Visionneuse (Viewer)
```

### Informations Pré-Ouverture

Avant d'ouvrir, vous voyez:
- ✅ **Statut "Prêt à ouvrir":** La lame va s'ouvrir correctement
- ⚠️ **Avertissement:** Lame ouvrable mais avec limitations
- ❌ **Non supporté:** Lame non ouvrable (erreur si vous cliquez)

### Retour à la Liste

**Depuis la visionneuse:**
- Cliquez sur **"← Retour"** en haut à gauche
- Ou cliquez sur le **logo VarunaPoC**

**Résultat:** Vous revenez au dossier où vous étiez (position conservée).

---

## Organisation Recommandée

### Structure Suggérée

Pour une navigation optimale, organisez vos lames par:

**Option A: Par Projet**
```
Slides/
├── project_lung_cancer_2024/
│   ├── patients/
│   │   ├── patient_001.svs
│   │   └── patient_002.svs
│   └── controls/
│       └── control_001.ndpi
└── project_kidney_study_2025/
    └── ...
```

**Option B: Par Fabricant**
```
Slides/
├── aperio/
│   ├── case_001.svs
│   └── case_002.svs
├── hamamatsu/
│   └── slide_001.ndpi
└── 3dhistech/
    ├── sample_001.mrxs
    └── sample_001/  ← Companion directory
```

**Option C: Par Date**
```
Slides/
├── 2024/
│   ├── 01-janvier/
│   └── 02-fevrier/
└── 2025/
    └── 01-janvier/
```

### Règles Importantes

⚠️ **Fichiers Companions:**

Certains formats nécessitent des fichiers/dossiers associés:

```
CORRECT:
  sample.mrxs
  sample/  ← Dossier companion (REQUIS!)

INCORRECT:
  sample.mrxs
  (pas de dossier sample/)  ← Lame non ouvrable!
```

Voir [03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md) pour règles détaillées.

---

## Cas d'Usage Courants

### Cas 1: Ouvrir une Lame Récente

1. Accédez à la racine `/`
2. Naviguez vers le dossier du projet actuel
3. Cliquez sur la lame
4. La visionneuse s'ouvre

### Cas 2: Comparer Plusieurs Lames du Même Patient

1. Naviguez vers le dossier du patient
2. Notez les lames disponibles
3. Ouvrez la première lame
4. Retournez à la liste (bouton "← Retour")
5. Ouvrez la deuxième lame
6. Répétez au besoin

**Note:** Comparaison côte-à-côte non disponible dans cette phase (fonctionnalité future).

### Cas 3: Chercher une Lame par Nom Partiel

1. Allez à la racine `/` (ou dossier parent probable)
2. Tapez dans la recherche: "tumor"
3. Toutes les lames contenant "tumor" s'affichent
4. Cliquez sur celle souhaitée

### Cas 4: Importer de Nouvelles Lames

**Méthode actuelle (Phase PoC):**

1. Copiez manuellement vos fichiers dans `/Slides` (via explorateur Windows)
2. **Important:** Respectez les règles de structure (voir [03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md))
3. Rafraîchissez la page VarunaPoC (F5)
4. Les nouvelles lames apparaissent automatiquement

**Méthode future:**
- Upload via bouton "📂 Ouvrir fichier" (en développement)

---

## Dépannage

### Problème: "Lame non trouvée"

**Causes possibles:**
1. Fichier déplacé/supprimé depuis le dernier scan
2. Permissions insuffisantes sur le dossier
3. Chemin trop long (limitation Windows)

**Solution:**
- Vérifiez que le fichier existe bien dans `/Slides`
- Rafraîchissez la page (F5)
- Contactez l'administrateur si le problème persiste

### Problème: "Non supporté" affiché

**Causes:**
1. Format non reconnu (extension inconnue)
2. Fichiers companions manquants (ex: `.mrxs` sans son dossier)
3. Fichier corrompu
4. Format en cours de développement

**Solution:**
- Vérifiez la structure des fichiers (voir [03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md))
- Consultez [04-FORMATS_SUPPORTES.md](./04-FORMATS_SUPPORTES.md) pour les formats validés
- Contactez le support avec le message d'erreur exact

### Problème: Recherche ne trouve rien

**Causes:**
1. Recherche dans le mauvais dossier (portée locale)
2. Faute de frappe
3. Lame dans un sous-dossier non affiché

**Solution:**
- Remontez à la racine `/` et cherchez depuis là
- Vérifiez l'orthographe
- Naviguez manuellement dans les sous-dossiers

---

## Raccourcis Clavier (Futurs)

**Note:** Ces raccourcis seront implémentés dans les phases futures:

| Raccourci | Action |
|-----------|--------|
| `Ctrl + F` | Focus sur la recherche |
| `Backspace` | Remonter au dossier parent |
| `Enter` | Ouvrir la lame sélectionnée |
| `Échap` | Fermer la visionneuse (retour à la liste) |

---

## Prochaines Étapes

Une fois à l'aise avec la navigation:

1. **[03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md)**
   Comprenez les règles de structure des fichiers

2. **[05-VISUALISATION_LAMES.md](./05-VISUALISATION_LAMES.md)**
   Maîtrisez la visionneuse (zoom, déplacement, etc.)

3. **[99-FAQ.md](./99-FAQ.md)**
   Consultez les questions fréquentes

---

**Version:** 1.0
**Dernière révision:** 2025-10-21
**Auteur:** Équipe VarunaPoC
