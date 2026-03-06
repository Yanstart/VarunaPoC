# Auth : Injection Bearer Token dans OpenSeadragon

## Probleme

Quand `AUTH_ENABLED=true`, les endpoints backend sont proteges par OIDC.
Le `ApiService` injecte correctement le Bearer token pour ses propres requetes,
mais `ViewerInstance.js` faisait 2 types de fetch **sans token** :

1. **DZI metadata** : `fetch(/api/slides/{id}/dzi.json)` — fetch brut ligne 279
2. **Tiles** : OpenSeadragon fait ses propres requetes HTTP internes

Resultat : `401 Unauthorized` sur toutes les tiles et metadata.

## Solution

### 1. Import authService dans ViewerInstance

```js
import { authService } from '../services/AuthService.js';
```

### 2. Activer loadTilesWithAjax dans la config OSD

```js
this._osdViewer = OpenSeadragon({
    // ...
    loadTilesWithAjax: true,
    ajaxHeaders: authService.accessToken
        ? { 'Authorization': `Bearer ${authService.accessToken}` }
        : {},
    // ...
});
```

### 3. Injecter le token sur le fetch DZI

```js
const headers = {};
if (authService.accessToken) {
    headers['Authorization'] = `Bearer ${authService.accessToken}`;
}
const response = await fetch(`${API.BASE_URL}/api/slides/${slideId}/dzi.json`, { headers });
```

### 4. Mettre a jour ajaxHeaders avant chaque ouverture de slide

```js
if (authService.accessToken) {
    this._osdViewer.ajaxHeaders = {
        'Authorization': `Bearer ${authService.accessToken}`,
    };
}
this._osdViewer.open(tileSource);
```

## Insight

OpenSeadragon fait ses propres requetes HTTP pour les tiles — il n'utilise pas
l'ApiService du projet. Par defaut, `loadTilesWithAjax` est `false` et OSD
utilise des `<img>` tags (qui ne supportent pas les headers custom).
Avec `loadTilesWithAjax: true`, OSD utilise `XMLHttpRequest` et accepte
les `ajaxHeaders`.

## Fichiers modifies

- `frontend/src/viewers/ViewerInstance.js`
