# Archive CDC v1 - Details pour Rapport TFE

> **Note** : Ce document contient les informations detaillees du cahier des charges original (46 pages) qui n'ont pas ete incluses dans le CDC v2 mais qui sont pertinentes pour le rapport TFE.

---

## 1. Presentation Detaillee du Client

### 1.1 neXat - Positionnement

La societe neXat se positionne comme un acteur majeur dans le domaine des communications par satellite, permettant aux organisations d'operer efficacement dans les regions les plus reculees du monde grace a son infrastructure reseau globale.

### 1.2 Modeles de Service

**Plateforme en tant que Service (PaaS)** :
- neXat opere et maintient l'infrastructure reseau complete
- Les clients se concentrent sur leurs activites metier
- Module de faconnage et routage du trafic integre

**Agregateur de Connectivite** :
- Combine plusieurs fournisseurs de connectivite
- Couverture mondiale et redondance accrue
- Optimisation des couts

**Fournisseur de Connectivite Directe** :
- Solutions adaptees aux besoins specifiques
- Missions critiques avec performances garanties
- Reseaux definis par logiciel (SDN)

### 1.3 Secteurs d'Activite

| Secteur | Besoins |
|---------|---------|
| Operateurs satellites | Optimisation services, maximisation infrastructure |
| FAI | Extension couverture zones difficiles |
| Gouvernements/Entreprises | Communications securisees, environnements exigeants |
| Maritime | Connectivite fiable haute mer |

### 1.4 Cas d'Usage Documentes

- Zones minieres isolees (aucune infrastructure terrestre)
- Operations maritimes internationales
- Missions gouvernementales regions reculees
- Installations petrolieres offshore

---

## 2. Problematique Detaillee TCP sur Satellite

### 2.1 Impact de la Latence

**Satellites geostationnaires (GEO)** :
- Altitude : ~36 000 km
- RTT : 500-600 ms
- Impact : 3+ secondes pour etablir connexion TCP+TLS

**Satellites LEO (Starlink)** :
- Altitude : 400-2000 km
- RTT : 30-50 ms
- Meilleur mais toujours penalisant vs terrestre (~10ms)

### 2.2 Pertes de Paquets

Mesures sur terminaux Starlink :
- Taux de perte normal : 1-2%
- Cause : Facteurs radio, pas congestion reseau

**Comportement TCP** :
- Interprete pertes comme congestion
- Reduit fenetre de congestion
- Sous-utilisation chronique de la bande passante

### 2.3 Head-of-Line Blocking

```
TCP Stream: [Seg1][Seg2][Seg3][Seg4][Seg5]
                   ^
                   Perdu

Resultat: Seg3, Seg4, Seg5 bloques jusqu'a retransmission Seg2
```

Impact particulier sur HTTP/2 et SPDY qui multiplexent sur une connexion TCP.

### 2.4 Chiffres Cles

- Utilisation reelle bande passante : 20-30% du theorique
- Cout economique significatif (infrastructure satellite couteuse)
- Experience utilisateur degradee

---

## 3. Caracteristiques QUIC Detaillees

### 3.1 Etablissement de Connexion

**TCP + TLS 1.2** :
```
Client              Serveur
  |----SYN----------->|        RTT 1
  |<---SYN-ACK--------|
  |----ACK----------->|        RTT 1.5
  |----ClientHello--->|        RTT 2
  |<---ServerHello----|
  |<---Certificate----|
  |<---ServerKeyExch--|
  |<---ServerHelloDone|
  |----ClientKeyExch->|        RTT 3
  |----ChangeCipher-->|
  |----Finished------>|
  |<---ChangeCipher---|
  |<---Finished-------|
  |====DATA==========>|        RTT 3+
```

**QUIC** :
```
Client              Serveur
  |----Initial------->|        RTT 1
  |    (ClientHello)  |
  |<---Initial--------|
  |    (ServerHello)  |
  |<---Handshake------|
  |====DATA==========>|        RTT 1
```

**QUIC 0-RTT (reconnexion)** :
```
Client              Serveur
  |----Initial------->|        RTT 0
  |    + Early Data   |
  |<---Response-------|
```

### 3.2 Multiplexage QUIC

```
Connection QUIC
  |
  +-- Stream 0 (HTTP GET /index.html)
  |     [Frame1][Frame2][Frame3]
  |
  +-- Stream 2 (HTTP GET /style.css)
  |     [Frame1][Frame2]
  |
  +-- Stream 4 (HTTP GET /script.js)
        [Frame1][Frame2][Frame3][Frame4]

Perte sur Stream 0 n'affecte PAS Streams 2 et 4
```

### 3.3 Algorithme BBR

**Principe** :
- Estime bande passante disponible (BtlBw)
- Estime RTT minimum (RTprop)
- Ajuste taux d'envoi : rate = BtlBw, cwnd = BtlBw x RTprop

**Phases** :
1. **STARTUP** : Croissance exponentielle jusqu'a saturation
2. **DRAIN** : Vide les files d'attente
3. **PROBE_BW** : Etat stable, sonde periodiquement
4. **PROBE_RTT** : Mesure RTT minimum periodiquement

**Avantage sur CUBIC** :
- Ne reduit pas drastiquement sur perte
- Maintient debit proche de l'optimal
- Adapte aux liens haute latence

---

## 4. Calculs BDP Detailles

### 4.1 Formule

```
BDP (bytes) = Bandwidth (bytes/s) x RTT (s)
```

### 4.2 Exemples par Profil Satellite

| Profil | RTT | Bandwidth | BDP | Fenetre Recommandee |
|--------|-----|-----------|-----|---------------------|
| LEO (Starlink) | 40ms | 100 Mbps (12.5 MB/s) | 500 KB | 1 MB |
| MEO | 120ms | 50 Mbps (6.25 MB/s) | 750 KB | 1.5 MB |
| GEO | 600ms | 10 Mbps (1.25 MB/s) | 750 KB | 1.5 MB |
| GEO Haut Debit | 600ms | 100 Mbps (12.5 MB/s) | 7.5 MB | 15 MB |

### 4.3 Probleme TCP

Fenetre TCP par defaut : 64 KB
BDP GEO 100 Mbps : 7.5 MB

```
Utilisation = min(Window, BDP) / BDP
           = min(64KB, 7.5MB) / 7.5MB
           = 64KB / 7.5MB
           = 0.83%
```

Meme avec window scaling (max 1 GB theorique), les implementations limitent souvent a 4-16 MB.

---

## 5. Parametres QUIC Exhaustifs

### 5.1 Transport Parameters (RFC 9000)

| Parametre | ID | Description | Defaut |
|-----------|-----|-------------|--------|
| max_idle_timeout | 0x01 | Timeout inactivite | 30s |
| max_udp_payload_size | 0x03 | Taille max datagramme | 1200 |
| initial_max_data | 0x04 | Fenetre connexion initiale | 64KB |
| initial_max_stream_data_bidi_local | 0x05 | Fenetre stream local | 32KB |
| initial_max_stream_data_bidi_remote | 0x06 | Fenetre stream remote | 32KB |
| initial_max_stream_data_uni | 0x07 | Fenetre stream uni | 32KB |
| initial_max_streams_bidi | 0x08 | Max streams bidi | 100 |
| initial_max_streams_uni | 0x09 | Max streams uni | 100 |
| ack_delay_exponent | 0x0a | Exposant delai ACK | 3 |
| max_ack_delay | 0x0b | Delai ACK max | 25ms |
| active_connection_id_limit | 0x0e | Limite CID actifs | 2 |

### 5.2 Parametres BBR

| Parametre | Description | Valeur Typique |
|-----------|-------------|----------------|
| startup_gain | Gain phase startup | 2.89 |
| drain_gain | Gain phase drain | 0.35 |
| probe_bw_gain | Gain phase probe | 1.0 |
| probe_rtt_duration | Duree probe RTT | 200ms |
| min_cwnd | Fenetre minimum | 4 packets |
| loss_threshold | Seuil perte | 2% |

### 5.3 Recommandations Satellite

**LEO (Starlink)** :
```yaml
initial_rtt: 50ms
max_idle_timeout: 60s
initial_max_data: 2MB
initial_max_stream_data: 512KB
algorithm: bbr2
```

**GEO** :
```yaml
initial_rtt: 700ms
max_idle_timeout: 120s
initial_max_data: 16MB
initial_max_stream_data: 4MB
algorithm: bbr2
min_rto: 600ms
```

---

## 6. Schema Base de Donnees Metadonnees

### 6.1 Table FLOW_METADATA (Hypertable TimescaleDB)

```sql
CREATE TABLE flow_metadata (
    timestamp       TIMESTAMPTZ NOT NULL,
    flow_id         BIGSERIAL,
    session_id      TEXT,
    app_id          TEXT,
    service_name    TEXT,

    -- HTTP
    method          TEXT,
    host            TEXT,
    path            TEXT,
    status_code     INTEGER,
    content_type    TEXT,
    content_length  BIGINT,
    user_agent      TEXT,
    referer         TEXT,

    -- Auth (anonymise)
    auth_type       TEXT,
    token_hash      TEXT,

    -- Cache
    cache_control   TEXT,
    if_modified     TIMESTAMPTZ,
    etag            TEXT,

    -- Transport
    stream_id       BIGINT,
    bytes_sent      BIGINT,
    bytes_received  BIGINT,
    rtt_ms          INTEGER,
    packet_loss     REAL,
    retransmissions INTEGER,

    PRIMARY KEY (timestamp, flow_id)
);

SELECT create_hypertable('flow_metadata', 'timestamp');
```

### 6.2 Table FLOW_STATISTICS (Agregation)

```sql
CREATE TABLE flow_statistics (
    bucket          TIMESTAMPTZ NOT NULL,
    app_id          TEXT NOT NULL,
    service_name    TEXT NOT NULL,

    request_count   BIGINT,
    total_bytes     BIGINT,
    avg_rtt         NUMERIC,
    avg_loss        NUMERIC,
    p50_latency     NUMERIC,
    p95_latency     NUMERIC,
    p99_latency     NUMERIC,

    PRIMARY KEY (bucket, app_id, service_name)
);
```

### 6.3 Index Recommandes

```sql
CREATE INDEX idx_flow_app ON flow_metadata (app_id, timestamp DESC);
CREATE INDEX idx_flow_service ON flow_metadata (service_name, timestamp DESC);
CREATE INDEX idx_flow_method ON flow_metadata (method) WHERE method IS NOT NULL;
```

---

## 7. Protocole de Test Detaille Phase 1

### 7.1 Infrastructure Docker

```yaml
version: '3.8'
services:
  client:
    image: quick-test-client
    networks:
      - test-net

  entry-proxy:
    image: quick-
    command: --mode entry --listen :8080 --remote exit-proxy:4433
    networks:
      - test-net
    cap_add:
      - NET_ADMIN  # Pour tc/netem

  exit-proxy:
    image: quick-
    command: --mode exit --listen :4433
    networks:
      - test-net

  server:
    image: nginx
    networks:
      - test-net

  timescaledb:
    image: timescale/timescaledb:latest-pg15
    networks:
      - test-net

networks:
  test-net:
    driver: bridge
```

### 7.2 Simulation Conditions Satellite

```bash
# Sur container entry-proxy
# Simulation GEO : 300ms latence chaque direction, 1% perte
tc qdisc add dev eth0 root netem delay 300ms loss 1%

# Simulation LEO : 25ms latence, 0.5% perte
tc qdisc add dev eth0 root netem delay 25ms loss 0.5%

# Variation de latence (jitter)
tc qdisc add dev eth0 root netem delay 300ms 50ms distribution normal loss 1%
```

### 7.3 Scripts de Test

**T1.1 - Connectivite** :
```bash
#!/bin/bash
for i in {1..100}; do
    curl -s -o /dev/null -w "%{time_total}\n" http://entry-proxy:8080/ping
done | awk '{sum+=$1} END {print "Avg:", sum/NR, "s"}'
```

**T1.4 - Gros Fichier** :
```bash
#!/bin/bash
# Generer fichier 10MB
dd if=/dev/urandom of=/tmp/test10mb bs=1M count=10

# Calculer checksum original
ORIG_MD5=$(md5sum /tmp/test10mb | cut -d' ' -f1)

# Transferer via tunnel
curl -X POST -F "file=@/tmp/test10mb" http://entry-proxy:8080/upload -o /tmp/received

# Verifier checksum
RECV_MD5=$(md5sum /tmp/received | cut -d' ' -f1)

if [ "$ORIG_MD5" == "$RECV_MD5" ]; then
    echo "PASS: Checksum match"
else
    echo "FAIL: Checksum mismatch"
fi
```

---

## 8. Analyse Statistique Benchmarks

### 8.1 Methodologie

- Minimum 30 echantillons par condition
- Test t de Student pour comparaison moyennes
- Niveau de confiance : 95%
- Report : moyenne, ecart-type, IC 95%, p-value

### 8.2 Format Resultats

```markdown
## Benchmark B1 : Latence HTTP GET

### Conditions
- RTT simule : 600ms
- Perte : 1%
- Fichier : 1KB

### Resultats

| Protocole | n | Moyenne | Ecart-type | IC 95% |
|-----------|---|---------|------------|--------|
| TCP | 100 | 2847ms | 234ms | [2801, 2893] |
| QUIC | 100 | 1923ms | 187ms | [1886, 1960] |

### Analyse
- Difference : -924ms (-32.5%)
- t-statistic : 31.2
- p-value : < 0.001
- **Conclusion** : Amelioration significative
```

### 8.3 Graphiques Requis

1. Box plots comparatifs TCP vs QUIC par metrique
2. Courbe debit instantane pendant transfert
3. Distribution des latences (histogramme)
4. Evolution RTT mesure pendant test
5. Matrice : conditions (RTT x Perte) vs gain observe

---

## 9. Procedure Starlink Detaillee

### 9.1 Checklist Pre-Test

- [ ] Phases 1 et 2 validees a 100%
- [ ] Approbation ecrite responsable neXat
- [ ] Fenetre de test confirmee
- [ ] Contact technique disponible
- [ ] Plan rollback valide
- [ ] Scripts de test verifies
- [ ] Systeme de backup logs operationnel

### 9.2 Deroulement

**J-1** :
- Gel du code
- Verification finale scripts
- Preparation materiel

**J (Test)** :

| Heure | Etape | Duree | Action |
|-------|-------|-------|--------|
| H+0 | Baseline | 30min | Mesures TCP direct |
| H+0:30 | Deploy | 15min | Installation QUICK- |
| H+0:45 | Smoke | 15min | Tests basiques |
| H+1:00 | Benchmarks | 2h | B1-B4 complets |
| H+3:00 | Cleanup | 15min | Arret, verification |
| H+3:15 | Debrief | 30min | Analyse preliminaire |

### 9.3 Criteres Arret Immediat

- Erreur critique dans logs
- Degradation > 30% vs baseline
- Timeout repetes (> 5 consecutifs)
- Crash du programme
- Demande responsable neXat

### 9.4 Rollback

```bash
# 1. Arreter QUICK-
quick- stop

# 2. Verifier connectivite directe
ping -c 10 8.8.8.8

# 3. Sauvegarder logs
tar -czf logs-$(date +%Y%m%d-%H%M).tar.gz /var/log/quick/

# 4. Notifier equipe
# Email/Teams avec resume incident
```

---

## 10. Planning Original (Reference)

> Note : Ce planning etait base sur une periode Oct 2025 - Jan 2026. A adapter selon avancement reel.

| Semaine | Focus | Livrables |
|---------|-------|-----------|
| 1 | Setup, Architecture | Env dev, specs validees |
| 2 | Entry proxy | Proxy TCP->QUIC |
| 3 | Exit proxy | Proxy QUIC->TCP |
| 4 | Metadonnees | Capture + TimescaleDB |
| 5 | Tests Phase 1 | Validation fonctionnelle |
| 6 | Optimisations | BBR, multiplexage |
| 7 | Benchmarks Phase 2 | Resultats comparatifs |
| 8 | Prep Starlink | Scripts, procedures |
| 9 | Buffer/Vacances | - |
| 10 | Tests Starlink | Validation terrain |
| 11 | Redaction | Documentation, rapport |
| 12 | Finalisation | Soutenance |

---

## 11. Budget Horaire Original

| Phase | Heures | % |
|-------|--------|---|
| Setup & Architecture | 40h | 13% |
| Developpement Core | 80h | 27% |
| Systeme Metadonnees | 35h | 12% |
| Optimisations | 30h | 10% |
| Tests & Validation | 70h | 23% |
| Documentation | 60h | 20% |
| Presentation | 25h | 8% |
| **Total** | **340h** | - |

---

## 12. Contacts et Ressources

### Contacts Projet

| Role | Nom | Contact |
|------|-----|---------|
| Client (CTO) | Fulvio Sansone | fulvio.sansone@nexat.be |
| Client (Tech) | Ahmad Othman | ahmad.othman@nexat.be |
| Superviseur EPHEC | M. SCHALKWIJK Laurent | - |

### Ressources Techniques

- Documentation QUIC : https://quicwg.org
- RFC 9000-9002 : https://www.rfc-editor.org
- TimescaleDB : https://docs.timescale.com
- neXat : https://www.nexat.be

---

*Archive CDC v1 - Pour reference rapport TFE*
