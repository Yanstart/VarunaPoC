# Cahier des Charges - QUICK-

**Accelerateur QUIC pour Communications Satellites**

| Projet | QUICK- (TFE Bachelier Informatique - EPHEC) |
|--------|---------------------------------------------|
| Client | neXat |
| Version | 2.0 |
| Implementation | Google QUICHE (C++) |

---

## 1. Contexte et Probleme

### 1.1 Liens Satellites

Les communications satellite presentent des caracteristiques qui penalisent TCP :

| Type | Altitude | RTT | Perte Typique |
|------|----------|-----|---------------|
| LEO (Starlink) | 400-2000 km | 30-50 ms | 1-2% |
| MEO | ~20000 km | 120 ms | 1-2% |
| GEO | ~36000 km | 500-600 ms | 1-2% |

### 1.2 Limitations TCP

**Etablissement de connexion** : TCP + TLS 1.2 necessite 3 RTT minimum avant d'envoyer des donnees applicatives. Sur GEO, cela represente ~1.8 secondes.

**Interpretation des pertes** : TCP interprete toute perte comme un signal de congestion et reduit sa fenetre de congestion. Sur satellite, les pertes sont majoritairement radio (non-congestion).

**Head-of-Line Blocking** : Une perte sur un segment TCP bloque tous les segments suivants jusqu'a retransmission, meme s'ils sont arrives.

**Bandwidth-Delay Product** :
```
BDP = Bandwidth x RTT
```
Exemple GEO 100 Mbps : `100 Mbps x 600ms = 7.5 MB`

La fenetre TCP par defaut (64 KB) ne peut utiliser que 0.83% de cette capacite.

### 1.3 Solution QUIC

QUIC (RFC 9000) resout ces problemes :

| Probleme TCP | Solution QUIC |
|--------------|---------------|
| 3 RTT etablissement | 1 RTT (0-RTT en reconnexion) |
| Pertes = congestion | BBR estime la bande passante, tolerant aux pertes |
| Head-of-line blocking | Streams independants multiplexes |
| Fenetres fixes | Fenetres configurables selon BDP |
| TLS separe | TLS 1.3 integre au protocole |

---

## 2. Architecture

### 2.1 Principe

Un tunnel transparent ou les applications communiquent en TCP local, tandis que QUICK- transporte les donnees via QUIC/UDP sur le lien satellite.

```
[Client TCP] --> [Entry Proxy] ==QUIC/UDP== [Exit Proxy] --> [Serveur TCP]
                      |         satellite         |
                      +---------------------------+
                           Tunnel QUIC optimise
```

### 2.2 Composants

**Entry Proxy (Ingress)** :
- Accepte connexions TCP entrantes
- Encapsule dans streams QUIC
- Multiplexe vers Exit Proxy

**Exit Proxy (Egress)** :
- Termine le tunnel QUIC
- Retablit connexions TCP vers destinations
- Expose API de controle et metriques

### 2.3 Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Langage | C++ (C++17/C++20) |
| QUIC | Google QUICHE |
| Build | Bazel |
| Crypto | BoringSSL |
| Utils | Abseil |
| Tests | Google Test |
| DB | TimescaleDB |
| Monitoring | Prometheus + Grafana |

**Justification QUICHE** : Contrairement a quic-go, QUICHE expose l'interface `SendAlgorithm` permettant de configurer BBR/BBR2/BBR3 avec leurs parametres internes.

---

## 3. Specifications Techniques

### 3.1 Handshake QUIC (RFC 9000/9001)

**1-RTT Initial** :
```
Client                           Serveur
   |---- Initial[CRYPTO] -------->|    ClientHello
   |<--- Initial[CRYPTO] ---------|    ServerHello
   |<--- Handshake[CRYPTO] -------|    Certificate, CertVerify, Finished
   |---- Handshake[CRYPTO] ------>|    Finished
   |==== 1-RTT Data =============>|
```

**0-RTT Reconnexion** : Le client reutilise un ticket de session pour envoyer des donnees immediatement. Limite aux requetes idempotentes (risque replay).

### 3.2 Congestion Control

QUICHE supporte trois variantes de BBR :

**BBR (v1)** - RFC draft-cardwell-iccrg-bbr :
- Modele : `rate = BtlBw`, `cwnd = BtlBw x RTprop`
- Phases : STARTUP, DRAIN, PROBE_BW, PROBE_RTT
- Parametres cles :
  - `startup_gain` : 2.89 (croissance exponentielle)
  - `drain_gain` : 0.35 (vidange files)
  - `probe_bw_gain` : 1.0 (etat stable)
  - `probe_rtt_duration` : 200ms

**BBR2** - Ameliorations :
- Meilleure equite avec les flux CUBIC
- Reaction plus conservative aux pertes ECN
- `loss_threshold` ajuste pour eviter sur-reaction

**BBR3** - En cours de standardisation :
- Algorithme de sondage ameliore
- Meilleure gestion des liens asymetriques

**Selection via QUICHE** :
```cpp
// quiche/quic/core/quic_connection.cc
config.SetCongestionControlType(kBBRv2);

// Options de connexion pour paramètres BBR
// TBBR - Active BBR
// B2ON - Active BBRv2
```

### 3.3 Flow Control (RFC 9000 Section 4)

QUIC utilise un controle de flux a deux niveaux :

| Niveau | Parametre | Description |
|--------|-----------|-------------|
| Connexion | `initial_max_data` | Credits globaux |
| Stream | `initial_max_stream_data_*` | Credits par stream |

**Frames de controle** :
- `MAX_DATA` : Augmente limite connexion
- `MAX_STREAM_DATA` : Augmente limite stream
- `DATA_BLOCKED` : Signale blocage connexion
- `STREAM_DATA_BLOCKED` : Signale blocage stream

### 3.4 Multiplexage de Streams

Chaque connexion TCP entrante devient un stream QUIC bidirectionnel :

```
Connection QUIC
  |
  +-- Stream 0 : TCP conn 1 (SSH)
  +-- Stream 4 : TCP conn 2 (HTTP)
  +-- Stream 8 : TCP conn 3 (HTTP)
```

Les streams pairs sont inities par le client, impairs par le serveur.

Une perte sur Stream 0 n'affecte pas les donnees de Stream 4 ou 8.

### 3.5 Transport Parameters

Parametres negocies au handshake (RFC 9000 Section 18) :

| ID | Parametre | Valeur Satellite |
|----|-----------|------------------|
| 0x01 | max_idle_timeout | 90s (GEO), 60s (LEO) |
| 0x04 | initial_max_data | 8 MB |
| 0x05 | initial_max_stream_data_bidi_local | 1 MB |
| 0x06 | initial_max_stream_data_bidi_remote | 1 MB |
| 0x08 | initial_max_streams_bidi | 100 |
| 0x0b | max_ack_delay | 50ms |

### 3.6 Securite TLS 1.3

QUIC integre TLS 1.3 (RFC 8446) directement :

- Cipher suites : `TLS_AES_128_GCM_SHA256`, `TLS_AES_256_GCM_SHA384`, `TLS_CHACHA20_POLY1305_SHA256`
- Key derivation : HKDF avec labels specifiques QUIC
- Header protection : Masquage des numeros de paquet
- 0-RTT : Limite aux requetes idempotentes, tickets rotatifs

---

## 4. Parametres Configurables

### 4.1 Configuration YAML

```yaml
mode: entry  # ou exit

listen:
  address: "0.0.0.0"
  port: 8080

remote:  # mode entry seulement
  address: "exit.example.com"
  port: 4433

quic:
  congestion_control: bbr2  # bbr, bbr2, cubic
  initial_cwnd: 32          # segments
  max_cwnd: 8388608         # 8 MB
  initial_rtt_ms: 100

  connection:
    max_idle_timeout_ms: 90000
    handshake_timeout_ms: 15000
    keep_alive_ms: 30000

  streams:
    max_concurrent: 100
    stream_window: 1048576   # 1 MB
    connection_window: 8388608  # 8 MB

tls:
  cert_file: "/etc/quick/server.crt"
  key_file: "/etc/quick/server.key"
  verify_peer: true

database:
  enabled: true
  host: "timescaledb"
  port: 5432
  name: "quick_metrics"

logging:
  level: INFO  # DEBUG, INFO, WARN, ERROR
```

### 4.2 Profils Satellite Pre-configures

**LEO (Starlink)** :
```yaml
quic:
  initial_rtt_ms: 50
  congestion_control: bbr2
  connection:
    max_idle_timeout_ms: 60000
  streams:
    stream_window: 524288      # 512 KB
    connection_window: 2097152 # 2 MB
```

**GEO** :
```yaml
quic:
  initial_rtt_ms: 700
  congestion_control: bbr2
  connection:
    max_idle_timeout_ms: 120000
  streams:
    stream_window: 4194304      # 4 MB
    connection_window: 16777216 # 16 MB
```

---

## 5. Exigences

### 5.1 Fonctionnelles

| ID | Exigence | Priorite |
|----|----------|----------|
| F01 | Accepter connexions TCP entrantes | P0 |
| F02 | Encapsuler flux TCP dans QUIC | P0 |
| F03 | Transmettre via UDP | P0 |
| F04 | Desencapsuler et retablir TCP | P0 |
| F05 | TLS 1.3 obligatoire | P0 |
| F06 | Multiplexer streams (pas de HOL) | P0 |
| F07 | Configurer BBR/BBR2/BBR3 | P0 |
| F08 | Stocker metriques TimescaleDB | P1 |
| F09 | Configuration YAML + CLI | P1 |
| F10 | API de controle REST | P1 |
| F11 | Metriques Prometheus | P1 |
| F12 | 0-RTT reconnexion | P2 |
| F13 | Migration de connexion | P3 |

### 5.2 Non-Fonctionnelles

| Categorie | Exigence | Seuil |
|-----------|----------|-------|
| Latence | Overhead du proxy | < 5 ms |
| Debit | Throughput supporte | >= 100 Mbps |
| Capacite | Connexions simultanees | >= 100 |
| CPU | Utilisation @ 50 Mbps | < 50% core |
| Memoire | Empreinte | < 512 MB |
| Securite | Chiffrement | TLS 1.3 uniquement |
| Fiabilite | Uptime en test | > 99% sur 24h |
| Tests | Couverture code | >= 60% |

---

## 6. Objectifs de Performance

### 6.1 Metriques Cles

| Metrique | Definition | Objectif | Justification |
|----------|------------|----------|---------------|
| Latence etablissement | Temps avant premiere donnee | -66% | 1 RTT vs 3 RTT |
| Debit effectif | Throughput sur 100 MB | x2 | Fenetres BDP-adaptees |
| Temps recovery | Recuperation apres 2% perte | -40% | SACK selectif |

### 6.2 Calculs Theoriques

**Latence** :
```
TCP + TLS 1.2 : SYN + SYN-ACK + ACK + TLS = ~3 RTT
QUIC         : Initial + Handshake = 1 RTT
Gain = (3-1)/3 = 66%
```

**Debit (GEO 100 Mbps)** :
```
BDP = 100 Mbps x 600ms = 7.5 MB

TCP (64 KB window) : 64 KB / 600ms = ~850 Kbps effectif
QUIC (8 MB window) : 8 MB / 600ms = ~100 Mbps effectif

Ratio theorique : ~100x
Objectif realiste : x2 (overhead, autres facteurs)
```

---

## 7. Validation

### 7.1 Phase 1 : Tests Fonctionnels (Docker + netem)

| Test | Description | Critere |
|------|-------------|---------|
| T1.1 | Connectivite | 100 pings, 0% perte |
| T1.2 | HTTP simple | Page 1 KB, integrite OK |
| T1.3 | HTTPS | TLS valide, contenu OK |
| T1.4 | Gros fichier | 10 MB, checksum OK |
| T1.5 | Multiplexage | 3 transferts paralleles |
| T1.6 | Resilience | Transfert OK @ 5% perte |
| T1.7 | Metriques | Donnees dans TimescaleDB |

### 7.2 Phase 2 : Benchmarks Comparatifs

Protocole :
1. Baseline TCP (memes conditions)
2. Test QUIC
3. Comparaison statistique (n >= 30)

| Benchmark | Mesure | Outil |
|-----------|--------|-------|
| B1 | Latence HTTP GET | curl x100 |
| B2 | Debit download | iperf3, 100 MB x5 |
| B3 | Recovery @ 2% perte | 10 MB x10 |
| B4 | Temps handshake | Wireshark |

**Conditions** :
- RTT : 50ms (LEO), 600ms (GEO)
- Perte : 0%, 1%, 2%, 5%
- Bande passante : 10, 50, 100 Mbps

### 7.3 Phase 3 : Validation Starlink

Prerequis : Phases 1-2 reussies a 100%.

Procedure :
1. Mesurer baseline TCP sur Starlink
2. Deployer QUICK-
3. Executer benchmarks B1-B4
4. Collecter et analyser

Succes : Amelioration demontrable sur >= 2 des 3 metriques principales.

---

## 8. Livrables

| Livrable | Format |
|----------|--------|
| Code source | Git (C++, Bazel) |
| Documentation technique | Markdown |
| Rapport TFE | PDF |
| Resultats benchmarks | Markdown + donnees |

---

## 9. References

- RFC 9000 - QUIC: A UDP-Based Multiplexed and Secure Transport
- RFC 9001 - Using TLS to Secure QUIC
- RFC 9002 - QUIC Loss Detection and Congestion Control
- RFC 8446 - TLS 1.3
- draft-ietf-ccwg-bbr - BBR Congestion Control
- Google QUICHE : https://github.com/google/quiche

---

*Version 2.0 - Decembre 2024 - Implementation Google QUICHE (C++)*
