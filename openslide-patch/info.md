# openslide-patch

## But
Fork patche d'OpenSlide 4.0.0 pour supporter les formats non-standard rencontres en clinique (ex: Ventana BIF direction LEFT).

## Pourquoi
OpenSlide upstream ne supporte pas certaines variantes vendeur. Plutot que de contourner dans le backend, on patche la librairie C directement pour une correction au bon niveau d'abstraction.

## Comment
- Git submodule vers `Yanstart/openslide` branche `varuna-patches`
- Patch applique via fichier `.patch` standard (diff unifie)
- Build: script MSYS2 UCRT64 pour Windows, meson pour Linux

## Structure
```
openslide-patch/
  README.md                      # Doc complete du patch (219 lignes, troubleshooting)
  ventana-left-direction.patch   # Patch unique: support BIF LEFT direction
  build-openslide.sh             # Script de compilation (MSYS2 UCRT64)
  openslide/                     # Submodule: fork complet OpenSlide (~2000 fichiers C)
```

## Points cles
- Un seul patch actif pour l'instant (`ventana-left-direction.patch`)
- Si nouveaux patchs necessaires, les ajouter ici avec un `.patch` par fix
- Doc erreur associee: `docs/ERROR_BIF_DIRECTION_LEFT.md`
