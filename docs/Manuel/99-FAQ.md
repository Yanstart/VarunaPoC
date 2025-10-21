# Questions Fréquentes (FAQ)

**Dernière mise à jour:** 2025-10-21
**Version:** 1.0

---

## Navigation et Interface

### Q: Comment revenir à la page d'accueil depuis la visionneuse?

**R:** Deux méthodes:
1. Cliquez sur le bouton **"← Retour"** en haut à gauche
2. Cliquez sur le **logo VarunaPoC**

### Q: Je ne trouve pas ma lame dans la liste, que faire?

**R:** Vérifiez les points suivants:

1. **Vérifiez le dossier actuel:**
   - Regardez le fil d'Ariane en haut (ex: 🏠 / > 3DHistech)
   - Votre lame est peut-être dans un autre dossier

2. **Utilisez la recherche:**
   - Tapez une partie du nom dans la barre de recherche
   - La recherche fonctionne uniquement dans le dossier actuel

3. **Vérifiez la structure des fichiers:**
   - Certains formats nécessitent des fichiers companions (voir [03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md))
   - Rafraîchissez la page (F5) après avoir ajouté/déplacé des fichiers

### Q: Pourquoi certaines lames sont marquées "Non supporté"?

**R:** Plusieurs raisons possibles:

1. **Format non reconnu:**
   - Extension inconnue
   - Voir [04-FORMATS_SUPPORTES.md](./04-FORMATS_SUPPORTES.md) pour la liste complète

2. **Fichiers companions manquants:**
   - Exemple: Fichier `.mrxs` sans son dossier companion
   - Voir section "Dépendances" dans [03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md)

3. **Format en développement:**
   - Certains formats sont détectés mais pas encore complètement supportés
   - Ex: `.scn` (Leica SCN) en cours de validation

4. **Fichier corrompu:**
   - Le fichier existe mais ne peut pas être lu
   - Contactez le support technique

---

## Formats de Fichiers

### Q: Quels formats de lames sont supportés?

**R:** Formats validés et prêts à l'emploi:

- ✅ **Aperio SVS** (`.svs`) - Leica/Aperio
- ✅ **Hamamatsu NDPI** (`.ndpi`) - Hamamatsu
- ✅ **Ventana BIF** (`.bif`) - Roche/Ventana (patch appliqué)
- ✅ **MIRAX** (`.mrxs`) - 3DHistech
- ✅ **Generic TIFF** (`.tif`, `.tiff`) - Divers fabricants

Formats en cours de validation:
- ⚠️ **Leica SCN** (`.scn`) - Tests en cours
- 🔄 **DICOM** (`.dcm`) - En développement

Voir [04-FORMATS_SUPPORTES.md](./04-FORMATS_SUPPORTES.md) pour détails.

### Q: Mon fichier .mrxs ne s'ouvre pas, pourquoi?

**R:** Les fichiers `.mrxs` (3DHistech MIRAX) nécessitent **obligatoirement** un dossier companion.

**Structure requise:**
```
sample.mrxs              ← Fichier principal
sample/                  ← Dossier companion (même nom sans extension!)
  ├── Slidedat.ini       ← REQUIS
  ├── Data0000.dat
  ├── Data0001.dat
  └── Index.dat
```

**Erreurs courantes:**

❌ **Mauvais nom de dossier:**
```
sample.mrxs
sample_data/  ← Nom différent, ne marche PAS!
```

❌ **Dossier manquant:**
```
sample.mrxs
(pas de dossier)  ← Lame non ouvrable!
```

✅ **Correct:**
```
sample.mrxs
sample/  ← Nom identique, fonctionne!
```

**Solution:**
1. Vérifiez que le dossier companion existe
2. Vérifiez que son nom correspond exactement (sans l'extension `.mrxs`)
3. Vérifiez que `Slidedat.ini` est présent dans le dossier

### Q: Puis-je utiliser des fichiers DICOM?

**R:** Le support DICOM est **en développement**.

**Statut actuel:**
- ❌ Fichiers `.dcm` individuels: Non supportés
- 🔄 Séries DICOM complètes: En cours d'implémentation

**Prochaine mise à jour:** Phase 2 (date à définir)

### Q: Comment savoir si mon fichier a des fichiers companions?

**R:** Consultez le tableau dans [03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md#formats-supportés).

**Résumé rapide:**
- **Fichier unique:** `.svs`, `.ndpi`, `.tif`, `.bif`, `.scn`
- **Multi-fichiers:** `.vms` (nécessite `.vmu`)
- **Avec dossier companion:** `.mrxs` (nécessite dossier `nom/`)

---

## Organisation des Fichiers

### Q: Où dois-je mettre mes fichiers de lames?

**R:** Tous les fichiers doivent être dans le répertoire:
```
C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Slides
```

Vous pouvez créer des sous-dossiers pour organiser vos lames:
```
Slides/
├── project_2024/
│   ├── patient_001.svs
│   └── patient_002.svs
└── controls/
    └── control_001.ndpi
```

**Important:** Ne placez JAMAIS vos lames en dehors de ce répertoire racine.

### Q: Puis-je renommer mes fichiers de lames?

**R:** Oui, mais avec précautions:

**Fichiers sans companions (.svs, .ndpi, .bif):**
- ✅ Renommage direct possible
- Exemple: `sample.svs` → `patient_001.svs`

**Fichiers avec companions (.mrxs):**
- ⚠️ Renommez **à la fois** le fichier ET le dossier
- Exemple:
  ```
  Avant:
    old_name.mrxs
    old_name/

  Après:
    new_name.mrxs
    new_name/  ← Doit correspondre!
  ```

**Fichiers multi-fichiers (.vms + .vmu):**
- ⚠️ Renommez **les deux fichiers** avec le même nom de base
- Exemple:
  ```
  Avant:
    slide_a.vms
    slide_a.vmu

  Après:
    patient_001.vms
    patient_001.vmu  ← Même nom de base!
  ```

### Q: Comment importer de nouvelles lames?

**R:** **Méthode actuelle (Phase PoC):**

1. Copiez vos fichiers dans `/Slides` (via explorateur Windows)
2. Respectez les règles de structure (voir question précédente)
3. Rafraîchissez la page VarunaPoC (touche F5)
4. Les nouvelles lames apparaissent automatiquement

**Méthode future:**
- Upload via bouton "📂 Ouvrir fichier" (en développement)
- Drag & drop de fichiers (planifié)

---

## Visualisation

### Q: Comment zoomer dans une lame?

**R:** Trois méthodes:

1. **Molette de souris:**
   - Vers le haut = Zoom avant
   - Vers le bas = Zoom arrière

2. **Boutons + et -:**
   - Situés dans la barre d'outils de la visionneuse

3. **Double-clic:** (futur)
   - Double-cliquez sur une zone = Zoom centré

### Q: Comment me déplacer dans une lame?

**R:** Deux méthodes:

1. **Cliquez-glissez:**
   - Maintenez le clic gauche et déplacez la souris
   - Fonctionne comme Google Maps

2. **Mini-carte:**
   - Cliquez sur la mini-carte (coin bas-droite)
   - Le rectangle rouge indique votre position

### Q: La lame se charge lentement, est-ce normal?

**R:** Cela dépend de plusieurs facteurs:

**Chargement initial (2-5 secondes):**
- ✅ Normal - VarunaPoC charge les métadonnées et l'overview

**Chargement des tuiles lors du zoom:**
- ✅ Normal si connexion lente (< 10 Mbps)
- ⚠️ Peut être lent pour très haute résolution (> 100,000 x 100,000 pixels)

**Chargement très lent (> 30 secondes):**
- ❌ Problème possible:
  - Vérifiez votre connexion réseau
  - Vérifiez que le backend est démarré (http://localhost:8000)
  - Contactez le support technique

**Optimisations:**
- Utilisez Chrome ou Edge (meilleurs performances)
- Fermez les autres onglets consommant beaucoup de mémoire
- Connexion réseau stable recommandée (100 Mbps idéal)

### Q: Pourquoi l'image est floue quand je zoome?

**R:** **Comportement normal:**

Lorsque vous zoomez, VarunaPoC charge progressivement les tuiles haute résolution:

1. **Immédiatement:** Affichage des tuiles basse résolution (floues)
2. **Après 1-2 secondes:** Remplacement par tuiles haute résolution (nettes)

**Si l'image reste floue:**
- Attendez quelques secondes (chargement en cours)
- Vérifiez votre connexion réseau
- Vérifiez que le fichier original contient bien des niveaux haute résolution

---

## Problèmes Techniques

### Q: Message d'erreur "Slide not found", que faire?

**R:** **Causes possibles:**

1. **Fichier déplacé/supprimé:**
   - Vérifiez que le fichier existe toujours dans `/Slides`
   - Rafraîchissez la page (F5)

2. **Permissions insuffisantes:**
   - Le backend n'a pas accès au fichier
   - Contactez l'administrateur système

3. **Chemin trop long (Windows):**
   - Limitez la profondeur des sous-dossiers
   - Évitez les noms de fichiers très longs

### Q: Le backend ne démarre pas, que faire?

**R:** **Vérifications:**

1. **Port 8000 occupé:**
   ```bash
   # Vérifier si le port est déjà utilisé
   netstat -ano | findstr :8000
   ```
   - Si occupé, arrêtez l'autre application ou changez de port

2. **Python non installé:**
   - Vérifiez: `python --version`
   - Version minimale: Python 3.10+

3. **Dépendances manquantes:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. **OpenSlide DLL manquante:**
   - Vérifiez que MSYS2 UCRT64 est installé
   - Vérifiez le chemin dans `config_openslide.py`

**Si le problème persiste:**
- Consultez les logs du backend (terminal)
- Contactez le support avec le message d'erreur exact

### Q: Erreur "CORS policy blocked", que faire?

**R:** **Cause:** Le frontend et le backend ne sont pas sur les mêmes domaines/ports autorisés.

**Vérifications:**

1. **URLs correctes:**
   - Frontend: `http://localhost:5173`
   - Backend: `http://localhost:8000`

2. **Configuration CORS (backend):**
   - Vérifiez `main.py` → section `CORSMiddleware`
   - Les origins autorisées doivent inclure `http://localhost:5173`

**Solution temporaire (développement uniquement):**
- Désactivez temporairement CORS dans le navigateur (Chrome: `--disable-web-security`)
- ⚠️ NE JAMAIS faire en production!

### Q: La page est blanche, rien ne s'affiche

**R:** **Vérifications:**

1. **Console navigateur:**
   - Appuyez sur F12 → Onglet "Console"
   - Cherchez des erreurs JavaScript (texte rouge)

2. **Backend démarré:**
   - Accédez à `http://localhost:8000/docs`
   - Vous devriez voir la documentation FastAPI

3. **Vite dev server démarré:**
   ```bash
   cd frontend
   npm run dev
   ```
   - Vérifiez le message "Local: http://localhost:5173"

4. **Cache navigateur:**
   - Videz le cache (Ctrl + Shift + Delete)
   - Rafraîchissez (Ctrl + F5)

---

## Sécurité et Confidentialité

### Q: Mes données patients sont-elles sécurisées?

**R:** **Phase PoC (actuelle):**

✅ **Mesures en place:**
- Accès limité au répertoire `/Slides` uniquement
- Path traversal bloqué (protection contre accès non autorisés)
- Pas de téléchargement de données dans les logs

⚠️ **Limitations actuelles:**
- Authentification basique (pas de gestion utilisateurs avancée)
- Pas de chiffrement des communications (HTTP, pas HTTPS)
- Pas d'audit des accès

**En production (futur):**
- ✅ HTTPS obligatoire
- ✅ Authentification robuste (SSO, LDAP)
- ✅ Audit trail complet
- ✅ Anonymisation des données patients si requis

**Recommandations:**
- Ne jamais exposer VarunaPoC sur Internet en phase PoC
- Utiliser uniquement sur réseau sécurisé interne
- Anonymiser les données patients si possible

### Q: Puis-je partager une lame avec un collègue?

**R:** **Phase PoC:**

❌ **Pas de partage direct** (fonctionnalité non implémentée)

**Solutions temporaires:**
1. Copier le fichier de lame vers le répertoire `/Slides` de votre collègue
2. Donner accès au même répertoire réseau
3. Utiliser un partage réseau Windows (SMB)

**Futur (Phase 2+):**
- ✅ Liens de partage sécurisés
- ✅ Permissions granulaires (lecture seule, annotation, etc.)
- ✅ Expiration automatique des liens

---

## Fonctionnalités Futures

### Q: Puis-je annoter les lames?

**R:** ❌ **Pas encore implémenté** (planifié pour Phase 2)

**Fonctionnalités prévues:**
- Dessins libres (cercle, flèche, polygone)
- Annotations textuelles
- Mesures de distance/surface
- Sauvegarde des annotations
- Export des annotations (JSON, XML)

### Q: Puis-je comparer deux lames côte-à-côte?

**R:** ❌ **Pas encore implémenté** (planifié pour Phase 2)

**Fonctionnalités prévues:**
- Affichage synchronisé (zoom, déplacement)
- Overlay semi-transparent
- Comparaison avant/après traitement

### Q: Puis-je exporter des images?

**R:** ❌ **Pas encore implémenté** (planifié pour Phase 2)

**Fonctionnalités prévues:**
- Export région sélectionnée (PNG, JPEG)
- Export avec annotations
- Export multi-résolution

### Q: Y aura-t-il une application mobile?

**R:** 🔄 **En évaluation** (Phase 3+)

**Défis:**
- Taille des fichiers (gigapixels)
- Bande passante mobile
- Performance sur appareils mobiles

**Solution envisagée:**
- Application web responsive (pas d'app native)
- Interface adaptée tablettes
- Mode "offline" pour régions pré-chargées

---

## Aide et Support

### Q: Comment signaler un bug?

**R:** Contactez le support technique avec:

1. **Description du problème:**
   - Que faisiez-vous?
   - Qu'attendiez-vous?
   - Qu'avez-vous obtenu?

2. **Informations système:**
   - Navigateur (Chrome/Firefox/Edge + version)
   - Système d'exploitation (Windows 10/11, etc.)
   - Version de VarunaPoC (voir page d'accueil)

3. **Captures d'écran:**
   - Message d'erreur (si affiché)
   - Console navigateur (F12 → Console)

4. **Fichier concerné:**
   - Type de fichier (extension)
   - Fabricant (si connu)
   - Taille approximative

### Q: Où trouver plus de documentation?

**R:** **Manuel Utilisateur complet:**
- [01-INTRODUCTION.md](./01-INTRODUCTION.md) - Premiers pas
- [02-NAVIGATION_DOSSIERS.md](./02-NAVIGATION_DOSSIERS.md) - Explorateur
- [03-ORGANISATION_LAMES.md](./03-ORGANISATION_LAMES.md) - Structure fichiers
- [04-FORMATS_SUPPORTES.md](./04-FORMATS_SUPPORTES.md) - Formats validés (à créer)
- [05-VISUALISATION_LAMES.md](./05-VISUALISATION_LAMES.md) - Visionneuse (à créer)

**Documentation Développeur:**
- `/docs/ERROR_*.md` - Erreurs documentées
- `CLAUDE.md` - Guide complet pour développeurs

### Q: Comment suggérer une amélioration?

**R:** Contactez l'équipe de développement avec:

1. **Description de la fonctionnalité souhaitée**
2. **Cas d'usage concret** (pourquoi c'est utile?)
3. **Priorité** (critique / importante / nice-to-have)

Toutes les suggestions sont évaluées et priorisées pour les prochaines phases.

---

**Cette FAQ est mise à jour régulièrement. Si votre question n'apparaît pas, contactez le support technique.**

**Version:** 1.0
**Dernière révision:** 2025-10-21
**Auteur:** Équipe VarunaPoC
