# VarunaPoC - Guide Monitoring Prometheus (Simple)

**Objectif:** Collecter et visualiser les m�triques de performance pour comparer VarunaPoC aux solutions concurrentes WSI (3DHistech, Roche, Philips).

**Approche:** Monitoring simple centr� sur l'**exp�rience utilisateur** (UX), sans complexit� excessive.

---

## =� Vue d'Ensemble

### Qu'est-ce que Prometheus?

Prometheus est un syst�me de monitoring open-source qui collecte des **m�triques** (donn�es chiffr�es) en temps r�el depuis VarunaPoC.

**M�triques collect�es:**

- Temps de chargement des tuiles (tile load time)
- Temps jusqu'� la premi�re tuile (time to first tile)
- Nombre de requ�tes HTTP
- Latence des endpoints API

**Pourquoi c'est important:**
Ces m�triques permettent de **mesurer objectivement** si VarunaPoC est aussi rapide (ou plus rapide) que les solutions concurrentes du march�.

---

## =� D�marrage Rapide

### 1. Acc�der � Prometheus

**Phase 1 (localhost):**

```
http://localhost:9090
```

**Phase 2.1 (r�seau):**

```
http://varun-p-01:9090
```

(Remplacer `varun-p-01` par l'IP du serveur si n�cessaire)

### 2. V�rifier que Prometheus collecte des donn�es

1. Aller dans **Status** � **Targets**
2. V�rifier que `varuna-backend` est **UP** (vert)
3. Si DOWN (rouge), voir section Troubleshooting

### 3. Tester une requ�te simple

1. Aller dans **Graph** (onglet principal)
2. Dans le champ de recherche, taper: `varuna_http_requests_total`
3. Cliquer **Execute**
4. Onglet **Graph**: Voir courbe d'�volution
5. Onglet **Table**: Voir valeurs actuelles

**Interpr�tation:**

- Si des valeurs apparaissent, Prometheus collecte correctement
- Si vide, naviguer dans VarunaPoC pour g�n�rer des donn�es

---

## =� M�triques Cl�s (UX-Focused)

### 1. Tile Load Time (M�TRIQUE CRITIQUE)

**Qu'est-ce que c'est?**
Le temps en millisecondes pour charger une tuile d'image. C'est la m�trique **la plus importante** pour l'exp�rience utilisateur.

**Pourquoi c'est crucial?**

- Chargement rapide = Navigation fluide, sensation de r�activit�
- Chargement lent = Saccades, frustration utilisateur

**Objectifs de performance:**
| Percentile | Excellent | Acceptable | Probl�matique |
|------------|-----------|------------|---------------|
| **P50** (m�diane) | < 50ms | < 100ms | > 100ms |
| **P95** (95e percentile) | < 150ms | < 250ms | > 250ms |
| **P99** (99e percentile) | < 300ms | < 500ms | > 500ms |

**Requ�tes Prometheus:**

```promql
# P50 (temps m�dian de chargement)
histogram_quantile(0.5, rate(varuna_tile_load_seconds_bucket[5m]))

# P95 (95% des tuiles chargent en moins de X ms)
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket[5m]))

# P99 (99% des tuiles chargent en moins de X ms)
histogram_quantile(0.99, rate(varuna_tile_load_seconds_bucket[5m]))
```

**Interpr�tation des r�sultats:**

- **P50 = 0.045 (45ms):** Excellent! La moiti� des tuiles chargent en moins de 45ms
- **P95 = 0.12 (120ms):** Bon, 95% des tuiles < 120ms
- **P99 = 0.3 (300ms):** Acceptable, quelques tuiles mettent jusqu'� 300ms

**Par format de slide:**

```promql
# Comparer .mrxs vs .bif vs .tif
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket{format="mrxs"}[5m]))
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket{format="bif"}[5m]))
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket{format="tif"}[5m]))
```

### 2. Time to First Tile (TTFT)

**Qu'est-ce que c'est?**
Le temps entre l'ouverture d'une slide et l'affichage de la premi�re tuile. C'est la "premi�re impression" de l'utilisateur.

**Objectifs:**

- **< 1 seconde:** Excellent (impression instantan�e)
- **< 2 secondes:** Acceptable
- **> 2 secondes:** Probl�matique (utilisateur per�oit la lenteur)

**Requ�tes Prometheus:**

```promql
# P50 TTFT
histogram_quantile(0.5, rate(varuna_time_to_first_tile_seconds_bucket[5m]))

# P95 TTFT
histogram_quantile(0.95, rate(varuna_time_to_first_tile_seconds_bucket[5m]))
```

**Interpr�tation:**

- **P50 = 0.8 (800ms):** Excellent, ouverture quasi-instantan�e
- **P95 = 1.5 (1.5s):** Bon, la plupart des slides ouvrent rapidement
- **P99 = 2.8 (2.8s):** Acceptable mais certaines slides sont lentes

### 3. HTTP Request Duration

**Qu'est-ce que c'est?**
Temps de r�ponse des endpoints API backend (liste slides, m�tadonn�es, etc.).

**Objectif:**

- **< 200ms:** Acceptable pour API
- **> 500ms:** Probl�matique

**Requ�tes Prometheus:**

```promql
# Latence P95 de tous les endpoints
histogram_quantile(0.95, rate(varuna_http_request_duration_seconds_bucket[5m]))

# Latence par endpoint sp�cifique
histogram_quantile(0.95, rate(varuna_http_request_duration_seconds_bucket{endpoint="/api/slides/"}[5m]))
histogram_quantile(0.95, rate(varuna_http_request_duration_seconds_bucket{endpoint=~"/api/slides/.*/info"}[5m]))
```

### 4. Slides Opened (Compteur)

**Qu'est-ce que c'est?**
Nombre total de slides ouvertes, par format et vendor.

**Utilit�:**

- V�rifier que tous les formats fonctionnent (`.mrxs`, `.bif`, `.tif`)
- Identifier les formats les plus utilis�s

**Requ�tes Prometheus:**

```promql
# Total slides ouvertes
sum(varuna_slides_opened_total)

# Par format
sum by (format) (varuna_slides_opened_total)

# Par vendor
sum by (vendor) (varuna_slides_opened_total)
```

**Exemple de r�sultat:**

```
format="mrxs" � 15 slides
format="bif"  � 8 slides
format="tif"  � 5 slides
```

---

## =� Sc�narios d'Utilisation

### Sc�nario 1: Benchmark Initial (Baseline)

**Objectif:** �tablir les performances de r�f�rence de VarunaPoC.

**�tapes:**

1. D�marrer Phase 1 (localhost) avec monitoring
2. Ouvrir 10-15 slides repr�sentatives (mix `.mrxs`, `.bif`, `.tif`)
3. Naviguer dans chaque slide (zoom in/out, pan)
4. Laisser Prometheus collecter pendant 10-15 minutes
5. Noter les m�triques P50, P95, P99

**Requ�tes � ex�cuter:**

```promql
# Tile Load Time P50, P95, P99
histogram_quantile(0.5, rate(varuna_tile_load_seconds_bucket[10m]))
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket[10m]))
histogram_quantile(0.99, rate(varuna_tile_load_seconds_bucket[10m]))

# TTFT P50, P95
histogram_quantile(0.5, rate(varuna_time_to_first_tile_seconds_bucket[10m]))
histogram_quantile(0.95, rate(varuna_time_to_first_tile_seconds_bucket[10m]))
```

**Template de r�sultats:**

```
BASELINE VARUNA POC (Phase 1 - localhost)
Date: __________
Dur�e: 10 minutes
Slides test�es: 15 (5 mrxs, 5 bif, 5 tif)

Tile Load Time:
- P50: ____ ms
- P95: ____ ms
- P99: ____ ms

TTFT:
- P50: ____ ms
- P95: ____ ms

Conclusion: [Performances acceptables / N�cessite optimisation]
```

### Sc�nario 2: Comparaison Phase 1 vs Phase 2.1

**Objectif:** Mesurer l'impact du r�seau sur les performances.

**�tapes:**

1. Collecter m�triques Phase 1 (baseline)
2. D�ployer Phase 2.1 (r�seau)
3. R�p�ter tests identiques depuis PC client
4. Comparer m�triques

**Requ�tes comparatives:**

```promql
# Phase 1 (localhost)
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket[10m]))

# Phase 2.1 (r�seau) - m�me requ�te, nouvelle p�riode
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket[10m]))
```

**Template de comparaison:**

```
COMPARAISON PHASE 1 vs PHASE 2.1

Tile Load P95:
- Phase 1 (local): ____ ms
- Phase 2.1 (r�seau): ____ ms
- Diff�rence: ____ ms
- Impact r�seau: [N�gligeable < 20ms / Mod�r� 20-50ms / Important > 50ms]

TTFT P95:
- Phase 1: ____ ms
- Phase 2.1: ____ ms
- Diff�rence: ____ ms

Conclusion:
- R�seau ajoute ____ ms de latence
- Performance UX: [Identique / L�g�rement d�grad�e / Nettement d�grad�e]
- Acceptable pour production: [Oui / Non]
```

### Sc�nario 3: Comparaison avec Concurrents

**Objectif:** Positionner VarunaPoC par rapport aux solutions du march�.

**Donn�es concurrentes (� obtenir du CHU ou litt�rature):**

- **3DHistech CaseViewer:** Tile load P95 = ??? ms
- **Roche PathViewer:** Tile load P95 = ??? ms
- **Philips IMS:** Tile load P95 = ??? ms

**Template de benchmark:**

```
BENCHMARK VARUNA POC vs CONCURRENTS

Solution              | Tile Load P95 | TTFT P95  | Notes
----------------------|---------------|-----------|----------------
VarunaPoC (Phase 2.1) | ____ ms       | ____ ms   | Open-source
3DHistech CaseViewer  | ____ ms       | ____ ms   | Commercial
Roche PathViewer      | ____ ms       | ____ ms   | Commercial
Philips IMS           | ____ ms       | ____ ms   | Commercial

Classement (du plus rapide au plus lent):
1. __________________
2. __________________
3. __________________
4. __________________

Conclusion:
VarunaPoC est [plus rapide / comparable / plus lent] que la moyenne du march�.
```

---

## =� Requ�tes Prometheus Utiles

### Requ�tes Simples (Copy-Paste)

**1. V�rifier que m�triques sont collect�es:**

```promql
up{job="varuna-backend"}
```

R�sultat attendu: `1` (si `0`, backend down)

**2. Nombre total de requ�tes HTTP:**

```promql
sum(varuna_http_requests_total)
```

**3. Taux de requ�tes par seconde (QPS):**

```promql
rate(varuna_http_requests_total[1m])
```

**4. R�partition des requ�tes par endpoint:**

```promql
sum by (endpoint) (varuna_http_requests_total)
```

**5. Moyenne de chargement des tuiles (toutes confondues):**

```promql
rate(varuna_tile_load_seconds_sum[5m]) / rate(varuna_tile_load_seconds_count[5m])
```

**6. Slides ouvertes par format:**

```promql
sum by (format) (varuna_slides_opened_total)
```

### Requ�tes Avanc�es (Pour Analyse D�taill�e)

**1. Comparer performance par niveau pyramidal:**

```promql
# P95 pour level 0 (pleine r�solution)
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket{level="0"}[5m]))

# P95 pour level 5 (overview)
histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket{level="5"}[5m]))
```

**2. D�tecter anomalies (pics de latence):**

```promql
# Identifier moments o� P99 d�passe 500ms
histogram_quantile(0.99, rate(varuna_tile_load_seconds_bucket[1m])) > 0.5
```

**3. Calculer % de tuiles charg�es en < 100ms:**

```promql
sum(rate(varuna_tile_load_seconds_bucket{le="0.1"}[5m])) /
sum(rate(varuna_tile_load_seconds_count[5m])) * 100
```

---

## =� Guide Utilisateur Prometheus (Rapide)

### Interface Prometheus

**Onglets principaux:**

1. **Graph:**

   - Zone de requ�tes (saisir requ�tes PromQL)
   - Bouton "Execute" pour lancer
   - Onglet "Graph" pour courbes temporelles
   - Onglet "Table" pour valeurs actuelles

2. **Alerts:** (Non configur� pour Phase 1/2.1)

3. **Status � Targets:**

   - Voir si `varuna-backend` est UP/DOWN
   - Derni�re scrape time
   - Erreurs de collecte

4. **Status � Configuration:**
   - Voir configuration Prometheus compl�te

### Astuces d'Utilisation

**1. Changer l'intervalle de temps:**

- En haut � droite: S�lectionner "5m", "15m", "1h", etc.
- Pour baseline: Utiliser "10m" ou "15m"
- Pour trend long-terme: "1h" ou "6h"

**2. Rafra�chir automatiquement:**

- Cliquer sur ic�ne de refresh (�)
- D�finir intervalle (ex: ever60s0s)

**3. Sauvegarder une requ�te:**

- Copier-coller requ�te dans document externe
- Pas de sauvegarde int�gr�e dans Prometheus (n�cessiterait Grafana)

**4. Exporter donn�es (pour rapports):**

- Onglet **Table** � Copier valeurs
- Coller dans Excel/Google Sheets
- Cr�er graphiques manuellement

---

## =� Troubleshooting

### Probl�me: Target "varuna-backend" est DOWN

**Sympt�mes:**

- Dans **Status � Targets**, `varuna-backend` affiche rouge "DOWN"
- Erreur: "Get http://backend:8000/metrics: context deadline exceeded"

**Solutions:**

1. **V�rifier que backend est d�marr�:**

   ```bash
   docker ps | grep varuna-backend
   # Doit afficher conteneur en cours
   ```

2. **V�rifier endpoint /metrics:**

   ```bash
   curl http://localhost:8000/metrics
   # Doit retourner m�triques Prometheus (format texte)
   ```

3. **V�rifier configuration Prometheus:**

   ```bash
   # �diter monitoring/prometheus.yml
   # V�rifier:
   scrape_configs:
     - job_name: 'varuna-backend'
       static_configs:
         - targets: ['backend:8000']  # Nom du service Docker
   ```

4. **Red�marrer Prometheus:**
   ```bash
   docker-compose -f docker-compose.phase2.1.yml restart prometheus
   ```

### Probl�me: M�triques vides (pas de donn�es)

**Sympt�mes:**

- Requ�tes retournent "No data"
- Graphs vides

**Solutions:**

1. **G�n�rer du trafic:**

   - Naviguer dans VarunaPoC (ouvrir slides, zoomer, etc.)
   - Attendre 15-30 secondes (intervalle de scrape)
   - R�ex�cuter requ�te

2. **V�rifier que metrics sont expos�es:**

   ```bash
   curl http://localhost:8000/metrics | grep varuna
   # Doit afficher lignes comme:
   # varuna_tile_load_seconds_bucket{...} 5
   # varuna_http_requests_total{...} 12
   ```

3. **V�rifier intervalle de temps:**
   - En haut � droite, changer de "5m" � "1h"
   - Donn�es peuvent �tre en dehors de la fen�tre de temps

### Probl�me: Requ�te PromQL retourne erreur

**Erreurs courantes:**

1. **"parse error: unexpected ..."**

   - Syntaxe incorrecte
   - V�rifier parenth�ses, accolades, guillemets

2. **"invalid quantile 0.95: quantile value should be in range [0, 1]"**

   - `histogram_quantile` doit avoir valeur entre 0 et 1
   - 0.95 = OK, 95 = NON

3. **"vector cannot contain metrics with the same labelset"**
   - Besoin d'agr�gation (`sum`, `avg`, etc.)
   - Ajouter `by (label)` pour grouper

**Solution g�n�rale:**

- Copier-coller requ�tes de ce document (test�es)
- Si erreur persiste, simplifier requ�te progressivement

---

## =� Export de Donn�es (Pour Rapports)

### M�thode 1: Copier-Coller Manuel

1. Ex�cuter requ�te dans Prometheus
2. Onglet **Table**
3. S�lectionner valeurs � Copier
4. Coller dans Excel/Google Sheets
5. Cr�er graphiques manuellement

**Avantages:** Simple, pas d'installation
**Inconv�nients:** Manuel, pas de graphs automatiques

### M�thode 2: API Prometheus (Pour Scripts)

**Exemple avec curl:**

```bash
# R�cup�rer P95 tile load time
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(varuna_tile_load_seconds_bucket[5m]))'
```

R�sultat JSON � parser avec script Python/Node.js.

### M�thode 3: Grafana (Optionnel - Future Phase)

Si besoin de dashboards automatiques, installer Grafana (non inclus Phase 1/2.1).

---

## =� Ressources Compl�mentaires

### Documentation Officielle

- **Prometheus Docs:** https://prometheus.io/docs/
- **PromQL (Query Language):** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Histograms & Percentiles:** https://prometheus.io/docs/practices/histograms/

### Fichiers Projet

- **Configuration Prometheus:** `monitoring/prometheus.yml`
- **Instrumentation backend:** `backend/monitoring.py`
- **M�triques dans code:** `backend/main.py` (middleware)

### Logs Prometheus

```bash
# Voir logs Prometheus (si probl�me)
docker-compose -f docker-compose.phase2.1.yml logs -f prometheus
```

---

##  Checklist Utilisation Monitoring

### Avant Tests

- [ ] Prometheus accessible (port 9090)
- [ ] Target `varuna-backend` UP (vert)
- [ ] Endpoint `/metrics` retourne donn�es

### Pendant Tests

- [ ] Naviguer dans VarunaPoC (g�n�rer trafic)
- [ ] Attendre 15-30 sec entre actions
- [ ] V�rifier m�triques apparaissent dans Prometheus

### Apr�s Tests

- [ ] Ex�cuter requ�tes P50, P95, P99
- [ ] Noter r�sultats dans rapport (voir checklist validation)
- [ ] Comparer avec objectifs (voir section M�triques Cl�s)
- [ ] Export donn�es si n�cessaire

---

## <� R�sum� Ex�cutif (TL;DR)

**3 M�triques � Surveiller:**

1. **Tile Load Time P95:** < 250ms (objectif)

   ```promql
   histogram_quantile(0.95, rate(varuna_tile_load_seconds_bucket[5m]))
   ```

2. **TTFT P95:** < 2s (objectif)

   ```promql
   histogram_quantile(0.95, rate(varuna_time_to_first_tile_seconds_bucket[5m]))
   ```

3. **Slides Opened:** Tous formats fonctionnels
   ```promql
   sum by (format) (varuna_slides_opened_total)
   ```

**Workflow:**

1. Acc�der Prometheus: `http://localhost:9090`
2. V�rifier target UP: **Status � Targets**
3. Ex�cuter requ�tes: Copier-coller depuis ce document
4. Noter r�sultats: Remplir template dans ONSITE_VALIDATION_CHECKLIST.md

**En cas de probl�me:** Voir section Troubleshooting

---

**Version:** 1.0
**Derni�re mise � jour:** 2025-12-04
**Auteur:** �quipe VarunaPoC
**Contexte:** Monitoring simple UX-focused pour benchmarking WSI
