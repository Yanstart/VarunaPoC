# VarunaPoC - Documentation des Erreurs et Limitations

Ce dossier contient la documentation détaillée de toutes les erreurs, limitations et problèmes rencontrés durant le développement de VarunaPoC.

## Objectif

**Documenter systématiquement** chaque erreur non triviale pour:
1. Comprendre la cause racine
2. Archiver les recherches effectuées
3. Faciliter le debugging futur
4. Aider les futurs développeurs/mainteneurs
5. Éviter de refaire les mêmes recherches

## Structure des Documents

Chaque erreur est documentée dans un fichier `ERROR_[NOM_COURT].md` suivant le template `ERROR_TEMPLATE.md`.

### Sections Obligatoires

- **Description du Problème**: Quoi, où, quand
- **Analyse Technique**: Pourquoi, comment
- **Recherches Effectuées**: Ce qui a été testé
- **Solutions Envisagées**: Options possibles
- **Solution Implémentée**: Ce qui a été fait
- **Tests de Reproduction**: Script pour reproduire
- **Références Externes**: Issues, docs, forums

## Liste des Erreurs Documentées

### Erreurs Actives (Non Résolues)

| Fichier | Titre | Impact | Date | Status |
|---------|-------|--------|------|--------|
| [ERROR_BIF_DIRECTION_LEFT.md](ERROR_BIF_DIRECTION_LEFT.md) | BIF "Bad direction attribute LEFT" | Certains fichiers BIF ne s'ouvrent pas | 2025-10-21 | Contourné |

### Erreurs Résolues

| Fichier | Titre | Solution | Date Résolution |
|---------|-------|----------|-----------------|
| _(Aucune pour l'instant)_ | - | - | - |

### Limitations Connues

| Fichier | Titre | Workaround | Date |
|---------|-------|------------|------|
| [ERROR_BIF_DIRECTION_LEFT.md](ERROR_BIF_DIRECTION_LEFT.md) | OpenSlide ne supporte pas direction LEFT | Gestion d'erreur gracieuse | 2025-10-21 |

## Quand Créer un Document d'Erreur ?

**OUI** - Créer un document si:
- ✅ L'erreur persiste après plusieurs tentatives de résolution
- ✅ L'erreur nécessite des recherches approfondies (docs, GitHub issues, forums)
- ✅ L'erreur est liée à une limitation externe (bibliothèque, format, OS)
- ✅ La solution n'est pas évidente et nécessite un workaround
- ✅ L'erreur pourrait se reproduire avec d'autres fichiers/cas

**NON** - Ne pas créer de document si:
- ❌ Simple typo ou bug évident corrigé immédiatement
- ❌ Erreur de configuration avec solution standard
- ❌ Problème utilisateur (mauvais usage de l'API)

## Comment Utiliser le Template

1. Copier `ERROR_TEMPLATE.md`
2. Renommer en `ERROR_[NOM_DESCRIPTIF].md`
3. Remplir toutes les sections obligatoires
4. Ajouter à la liste ci-dessus
5. Commiter avec le code qui implémente la solution

### Exemple de Nommage

- ✅ `ERROR_BIF_DIRECTION_LEFT.md`
- ✅ `ERROR_OPENSLIDE_JPEG_CORRUPTION.md`
- ✅ `ERROR_CORS_LOCALHOST_BLOCKED.md`
- ❌ `error1.md` (pas descriptif)
- ❌ `BUG.md` (trop générique)
- ❌ `ventana_fix.md` (pas de préfixe ERROR_)

## Convention de Nommage

```
ERROR_[COMPOSANT]_[DESCRIPTION_COURTE].md
```

**Exemples**:
- `ERROR_OPENSLIDE_UNSUPPORTED_FORMAT.md`
- `ERROR_FASTAPI_CORS_POLICY.md`
- `ERROR_VITE_MODULE_NOT_FOUND.md`
- `ERROR_WINDOWS_OPENSLIDE_DLL.md`

## Intégration avec le Code

Quand un workaround est implémenté, ajouter un commentaire dans le code:

```python
# Workaround pour ERROR_BIF_DIRECTION_LEFT.md
# OpenSlide ne supporte pas direction="LEFT" dans les BIF
try:
    slide = openslide.OpenSlide(path)
except openslide.OpenSlideError as e:
    if "Bad direction attribute" in str(e):
        # Voir docs/ERROR_BIF_DIRECTION_LEFT.md pour détails
        return {"is_supported": False, "notes": "BIF LEFT direction"}
```

## Règles de Rédaction

### ✅ FAIRE
- Écrire en français (langue du projet)
- Inclure des exemples de code concrets
- Citer les sources (GitHub issues, docs officielles)
- Expliquer le "pourquoi" pas juste le "quoi"
- Mettre à jour la date de dernière révision
- Lier vers le code implémenté

### ❌ NE PAS FAIRE
- **Utiliser des emojis dans les logs Python** (cause des erreurs d'encodage)
- Copier-coller sans comprendre
- Laisser des sections vides (mettre "N/A" si non applicable)
- Oublier de tester le script de reproduction
- Négliger les métadonnées (date, version, auteur)

## Maintenance

### Révision Trimestrielle
- Vérifier si les erreurs sont toujours d'actualité
- Mettre à jour les versions des bibliothèques testées
- Ajouter de nouvelles solutions si découvertes

### Avant Release en Production
- Revoir toutes les erreurs "Non Résolues"
- Vérifier si des fixes officiels existent
- Mettre à jour les workarounds si nécessaire

## Contribution

Si vous découvrez une nouvelle erreur nécessitant documentation:

1. Créer le fichier `ERROR_[NOM].md` basé sur le template
2. Remplir toutes les sections
3. Ajouter à la liste dans ce README
4. Commiter avec le code de workaround
5. Mentionner le fichier dans la PR/commit message

## Ressources Externes Utiles

### OpenSlide
- [GitHub Issues](https://github.com/openslide/openslide/issues)
- [Formats Documentation](https://openslide.org/formats/)
- [API Python Docs](https://openslide.org/api/python/)

### FastAPI
- [GitHub Issues](https://github.com/tiangolo/fastapi/issues)
- [Documentation](https://fastapi.tiangolo.com/)

### Forums
- [Image.sc (digital pathology)](https://forum.image.sc/)
- [Stack Overflow - OpenSlide tag](https://stackoverflow.com/questions/tagged/openslide)

---

**Dernière mise à jour**: 2025-10-21
**Maintenu par**: Équipe VarunaPoC
**Contact**: [Référence projet ou équipe]
