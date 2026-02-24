# backend/routes

## But
Endpoints HTTP FastAPI. Chaque fichier = un router avec un prefixe d'URL et un tag Swagger.

## Structure
```
routes/
  # --- Coeur ---
  slides.py          # /api/slides/* (browse, info, overview, tiles) - 10 endpoints
  annotations.py     # /api/annotations/* (CRUD + spatial queries) - 13 endpoints
  viewstate.py       # /api/viewstate/* (sauvegarde etat viewer) - 1 endpoint

  # --- ML ---
  ml.py              # /api/ml/* (predictions, heatmaps, features, models) - 29 endpoints [52K lignes]
  processing.py      # /api/processing/* (batch tiles, color norm, outliers) - 3 endpoints
  embeddings.py      # /api/embeddings/* (UNI, Phikon, Virchow) - 3 endpoints

  # --- Standards ---
  dicomweb.py        # /api/dicomweb/* (WADO-RS, STOW-RS, QIDO-RS) - 10 endpoints
  integration.py     # /api/integration/* (eHealth BE, HL7v2, APSR) - 10 endpoints
  regional.py        # /api/regional/* (ABDM, SS-MIX2, i18n) - 15 endpoints
  terminology.py     # /api/terminology/* (SNOMED CT, LOINC) - 8 endpoints

  # --- Fonctionnalites avancees ---
  sharing.py         # /api/sharing/* (tokens, liens publics) - 5 endpoints
  ws.py              # /ws/* (WebSocket collaboration) - 2 endpoints
  exports.py         # /api/exports/* (DICOM export) - 3 endpoints
  plugins.py         # /api/plugins/* (plugin manager) - 5 endpoints
  audit_api.py       # /api/audit/* (recherche audit, registre GDPR) - 2 endpoints
```
