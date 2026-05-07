# orthanc — PACS DICOM (sandbox)

## Rôle

Serveur PACS DICOM utilisé en **dev/test uniquement** comme cible du
`PACSWorkflowHook`. En production hospitalière, ne PAS activer ce profil :
on pointe `PACS_HOST` vers le PACS de l'hôpital (Telemis, Carestream,
GE Centricity, etc.).

Sert deux protocoles :

- **DICOM 4242** : C-FIND, C-STORE, C-ECHO (worklists, échange d'images)
- **HTTP 8042** : REST API, fallback pour `update_worklist`
  (DIMSE-C n'a pas d'équivalent natif)

## Conteneur

| | |
|---|---|
| Image | `orthancteam/orthanc:24.7.3` |
| Profils | `pacs`, `dev` |
| Ports hôte | `4242` (DICOM), `8042` (HTTP) |
| Volume | `varuna-orthanc-data` 🟡 sandbox |
| Healthcheck | `Orthanc --version` (image distroless, pas de shell) |

## Variables d'env

| Variable                   | Défaut          | Rôle                                       |
|----------------------------|-----------------|--------------------------------------------|
| `ORTHANC_USER`             | `varuna`        | User HTTP Basic                            |
| `ORTHANC_PASSWORD`         | `varuna_dev`    | Mot de passe                               |
| `PACS_AET_LOCAL`           | `VARUNA_SCU`    | AET du backend (côté SCU)                  |
| `PACS_AET_REMOTE`          | `ORTHANC`       | AET annoncé par Orthanc                    |
| `ORTHANC_DICOM_HOST_PORT`  | `4242`          | Port DICOM mappé                           |
| `ORTHANC_HTTP_HOST_PORT`   | `8042`          | Port HTTP mappé                            |

Variables côté backend :

| Variable             | Effet                                           |
|----------------------|-------------------------------------------------|
| `PACS_ENABLED`       | `true` active `PACSWorkflowHook` dans le compose |
| `PACS_HOST`          | `orthanc` en sandbox ; FQDN du vrai PACS en prod |
| `PACS_DICOM_PORT`    | `4242` par défaut                                |
| `PACS_HTTP_URL`      | `http://orthanc:8042` en sandbox                 |
| `PACS_HTTP_USER`/`PACS_HTTP_PASSWORD` | Doivent matcher `ORTHANC_USER`/`ORTHANC_PASSWORD` |

## Vérifications

```bash
# UI Orthanc
xdg-open http://localhost:8042
# Login: varuna / varuna_dev (ou ce qui est dans .env)

# C-ECHO depuis le backend
docker compose exec backend python -c "
from pynetdicom import AE, debug_logger
ae = AE(ae_title='VARUNA_SCU')
ae.add_requested_context('1.2.840.10008.1.1')  # Verification SOP Class
assoc = ae.associate('orthanc', 4242, ae_title='ORTHANC')
print('echo:', assoc.send_c_echo() if assoc.is_established else 'FAIL')
assoc.release()
"
```

## Charger des DICOM de test

```bash
# Via REST
curl -u varuna:varuna_dev -X POST \
  -H 'Content-Type: application/dicom' \
  --data-binary @sample.dcm \
  http://localhost:8042/instances

# Via DICOM C-STORE depuis l'hôte (storescu de dcmtk)
storescu -aec ORTHANC localhost 4242 sample.dcm
```

## Production : ne PAS activer ce profil

En CHU, configurer dans `.env.prod` :

```env
PACS_ENABLED=true
PACS_HOST=pacs.chu-namur.example
PACS_DICOM_PORT=104
PACS_HTTP_URL=https://pacs.chu-namur.example/wado-rs
PACS_AET_LOCAL=VARUNA   # AET enregistré dans l'allow-list du PACS hôpital
PACS_AET_REMOTE=TELEMIS_AET
PACS_HTTP_USER=varuna_service
PACS_HTTP_PASSWORD=...
```

Et lancer SANS `--profile pacs`.

## Liens

- [Orthanc Book](https://book.orthanc-server.com/)
- `backend/services/workflow/pacs_hook.py` — implémentation côté Varuna
- [docs/Deployment/TELEMIS_INTEGRATION_GUIDE.md](../../Deployment/TELEMIS_INTEGRATION_GUIDE.md)
