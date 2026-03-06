# Navigation cas : Skip slides non supportees

## Probleme

Quand un utilisateur navigue vers un cas (ex: "Ventana BIF - 3 slides"),
le code prenait systematiquement la premiere slide du tableau :

```js
const firstSlide = caseData.slides[0];
```

Si cette slide est marquee `is_supported === false` (ex: BIF avec direction=LEFT
avant le patch), le viewer crashait avec "Error opening slide".

## Solution

Selectionner la premiere slide **supportee** du cas :

```js
const firstSlide = caseData.slides.find(s => s.is_supported !== false)
    || caseData.slides[0];
```

Si aucune slide n'est supportee, on prend la premiere quand meme (l'erreur
sera affichee proprement dans le panneau info).

## Fichier modifie

- `frontend/src/main.js` — fonction `handleCaseSelect()`

## Correctif associe

La route `/api/slides/{id}/info` renvoyait HTTP 500 au lieu de 422 pour
les slides non-ouvrables. Cause : `get_slide_metadata()` dans `slide_loader.py`
wrappait `OpenSlideError` en `RuntimeError`, ce qui bypassait le catch
specifique dans la route.

Fix : laisser `OpenSlideError` se propager directement (`raise` sans re-wrap).

- `backend/services/slide_loader.py` — `get_slide_metadata()`
