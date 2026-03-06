# ML : Fallback MPP invalide pour Slideflow

## Probleme

Slideflow a besoin du MPP (microns-per-pixel) pour extraire les features.
Certaines slides ont un MPP absent ou invalide :

| Slide | MPP | Cause |
|-------|-----|-------|
| Generic-TIFF/CMU-1.tiff | 1000 | Resolution TIFF = 10 px/cm → OpenSlide convertit en 1000 µm/px |
| Zeiss SlidePreview-*.czi | 35.89 | Previews basse resolution, pas des vrais scans |
| Slides sans metadata | null | Aucune info de resolution dans le fichier |

Plage valide pour l'histologie : **0.1 - 5.0 µm/px** (10x a 100x).

## Erreur avant fix

```
Could not detect microns-per-pixel for slide: .../CMU-1.tiff
```

Slideflow refusait d'ouvrir le WSI et toute la chaine ML echouait.

## Solution

Dans `services/ml/providers/slideflow_provider.py`, methode `_open_wsi()` :

### Strategie en 3 etapes

1. **Magnification directe** : essaye `10x`, `20x`, `5x`, `40x` — fonctionne si Slideflow detecte le MPP automatiquement
2. **Lecture manuelle MPP via OpenSlide** :
   - **MPP valide (0.1-5.0)** : conversion en magnification (`round(10.0/mpp)`)
   - **MPP invalide (>5.0 ou <0.1)** : force `mpp=0.5` (~20x) avec `tile_um=256`
3. **Pas de MPP du tout** : force `mpp=0.5` avec `tile_um=256` au lieu de crasher

### Iteration 1 — `tile_um=256` seul (insuffisant)

```python
# ECHEC : Slideflow valide le MPP en interne AVANT d'utiliser tile_um
wsi = sf.WSI(slide_path, tile_px=tile_size, tile_um=256)
# → "Could not detect microns-per-pixel" persiste
```

Slideflow appelle `slide.mpp` durant l'initialisation du WSI, meme avec `tile_um` en pixels.
Si le MPP est invalide, il refuse d'ouvrir le slide.

### Iteration 2 — `mpp=0.5` force (necessaire mais insuffisant)

```python
DEFAULT_MPP = 0.5  # ~20x, safe default for histology
wsi = sf.WSI(slide_path, tile_px=tile_size, tile_um=256, mpp=DEFAULT_MPP)
```

Le parametre `mpp` de `sf.WSI()` **ecrase** la detection automatique.
Slideflow accepte la valeur sans la valider contre les metadonnees du slide.

### Iteration 3 — string matching corrige (solution finale)

Le fallback `mpp=0.5` n'etait jamais atteint. La boucle de magnification
capturait l'erreur mais le filtre string ne matchait pas :

```python
# ECHEC : "microns-per-pixel" ne contient PAS "mpp" !
if "magnification" in err or "mpp" in err:
    continue  # jamais execute pour SlideMissingMPPError
raise  # → exception propagee, fallback jamais atteint
```

Slideflow 4.0 leve `SlideMissingMPPError` avec le message
`"Could not detect microns-per-pixel for slide: ..."`.
Le mot "mpp" n'apparait PAS dans ce message.

Fix :
```python
err_msg = str(e).lower()
if "magnification" in err_msg or "mpp" in err_msg or "microns-per-pixel" in err_msg:
    continue
raise
```

## Compromis

Avec `mpp=0.5` force, Slideflow traite le slide comme du ~20x.
Les features sont moins precises (pas de normalisation par resolution reelle)
mais le ML fonctionne quand meme. C'est preferable a un crash complet.

**Pourquoi 0.5 µm/px ?** C'est ~20x, la magnification la plus courante en
histopathologie de routine. Les features extraites seront raisonnables meme
si la resolution reelle est differente.

## Slides impactees

Sur le jeu de test actuel (~60 slides) :
- 1 Generic TIFF (MPP=1000)
- 2 Zeiss SlidePreview (MPP=35.89)
- Toutes les autres slides ont un MPP valide et ne sont pas affectees

## Fichier modifie

- `backend/services/ml/providers/slideflow_provider.py` — `_open_wsi()`
