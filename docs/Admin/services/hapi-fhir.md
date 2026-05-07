# hapi-fhir — Sandbox FHIR R4

## Rôle

Serveur FHIR R4 (HAPI FHIR JPA) utilisé en **dev/test uniquement** comme
cible du `FHIRWorkflowHook`. En production, ne PAS activer ce profil :
on pointe `FHIR_BASE_URL` vers le serveur FHIR de l'hôpital (DPI).

Reçoit principalement des `DiagnosticReport` quand un rapport est signé
(événement `REPORT_SIGNED` du `WorkflowHook`).

## Conteneur

| | |
|---|---|
| Image | `hapiproject/hapi:v7.4.0` |
| Profils | `fhir`, `dev` |
| Port hôte | `8090` (mappé sur 8080 interne) |
| Volume | `varuna-hapi-data` 🟡 sandbox (H2 embedded) |
| Healthcheck | **désactivé** — image distroless, pas de shell ; sonder depuis l'hôte |
| User | `0:0` (root, pour permissions /data) |

Cold start ~30–45 s (Spring Boot + H2).

## Variables d'env

| Variable          | Défaut    | Rôle                                |
|-------------------|-----------|-------------------------------------|
| `FHIR_HOST_PORT`  | `8090`    | Port mappé sur l'hôte               |

Variables côté backend :

| Variable                 | Effet                                            |
|--------------------------|--------------------------------------------------|
| `FHIR_ENABLED`           | `true` active `FHIRWorkflowHook`                 |
| `FHIR_BASE_URL`          | `http://hapi-fhir:8080/fhir` en sandbox          |
| `FHIR_AUTH_TOKEN`        | (vide en sandbox)                                |
| `FHIR_TIMEOUT_SECONDS`   | `10`                                             |
| `FHIR_RETRY_MAX_ATTEMPTS`| `3` (back-off exponentiel)                       |

## Vérifications

```bash
# CapabilityStatement (le serveur est up et expose FHIR R4)
curl -fsS http://localhost:8090/fhir/metadata | jq '.fhirVersion'
# attendu : "4.0.1"

# Lister les DiagnosticReports
curl -fsS http://localhost:8090/fhir/DiagnosticReport | jq '.entry | length'

# UI HAPI
xdg-open http://localhost:8090/
```

## Désactiver complètement

```env
# .env
FHIR_ENABLED=false
```

Et lancer sans `--profile fhir`. Le `WorkflowHook` utilise alors juste
`PACSWorkflowHook` + `WebSocketWorkflowHook` (et `NoOpWorkflowHook` si
tout est désactivé).

## Production hôpital

```env
FHIR_ENABLED=true
FHIR_BASE_URL=https://fhir.chu-namur.example/fhir
FHIR_AUTH_TOKEN=<bearer-token-issued-by-hospital>
```

Lancer sans `--profile fhir`. Le `FHIRWorkflowHook` enverra les
`DiagnosticReport` au serveur hospitalier (DPI). Vérifier au préalable :

- Endpoint accessible depuis l'hôte (`curl ${FHIR_BASE_URL}/metadata`)
- TLS valide
- Token bearer non expiré
- Schéma FHIR accepté (R4) — voir `backend/fhir/resources.py`

## Notes techniques

- Stockage embedded **H2** : suffisant pour la sandbox dev, pas pour
  la prod. Pour un test de charge, switcher sur HAPI + Postgres en
  ajoutant un service `hapi-fhir-db` (template dans `Archives/Phase2-Deployment/`).
- `query_worklist` et `update_worklist` du Protocol `WorkflowHook` :
  `FHIRWorkflowHook` ne les implémente pas (raise `NotImplementedError`),
  car FHIR `Task` n'est pas encore supporté côté builder. À la place,
  c'est `PACSWorkflowHook` qui couvre ces appels.

## Liens

- [HAPI FHIR docs](https://hapifhir.io/hapi-fhir/docs/)
- `backend/services/workflow/fhir_hook.py`
- `backend/fhir/resources.py` — DiagnosticReport builder
