# QUIC Satellite Parameter Tuning - Audit complet

> Analyse exhaustive des leviers QUIC pour maximiser le throughput sur liens satellite.
> Projet: QUICK- (TCP-over-QUIC accelerator)
> Date: 2026-02-10
> Backend: quiche-cloudflare 0.22.0

## 1. Vue d'ensemble

```text
                    QUICK- Transport Stack
+--------------------------------------------------+
|  APPLICATION (entry/exit tunnel)                  |
|  - Buffer sizes (4 MB TCP/QUIC)                  |
|  - POLLS_PER_RETRY (8)                           |
|  - Multi-stream per TCP (a implementer)          |
+--------------------------------------------------+
|  QUIC CONFIG (build_quiche_config)                |
|  - 29 methodes appelees sur 39 disponibles       |
|  - 3 methodes utiles non appelees (quick wins)   |
+--------------------------------------------------+
|  QUICHE INTERNALS (hardcode, intouchable)         |
|  - packet_threshold = 3 (loss detection)         |
|  - time_threshold = 9/8 RTT                      |
|  - PTO probes = 2                                |
|  - BBR pacing_gain, cwnd_gain                    |
|  - ACK Frequency (RFC 9330 - pas implemente)     |
+--------------------------------------------------+
```

## 2. Les 14 parametres QUIC et leur statut

### 2.1 Parametres implementes (Phase 1+2 terminee)

| # | Parametre | Valeur | Justification satellite |
|---|-----------|--------|------------------------|
| 1 | `congestion_control` | BBR2 | Meilleur pour liens a haut BDP (refs: QPEP, StarQUIC) |
| 2 | `initial_congestion_window` | 3x BDP packets | Remplir le pipe des le depart. GEO@10Gbps: ~1.7M pkts |
| 3 | `max_udp_payload_size` | 1350 bytes | MTU-safe, PMTU discovery active pour trouver mieux |
| 4 | `initial_rtt` | LEO:50ms MEO:120ms GEO:600ms | Point de depart pour BBR2, se recalibre automatiquement |
| 5 | `max_ack_delay` | LEO:10ms MEO:25ms GEO:50ms | Proportionnel au RTT, evite ACK prematures |
| 6 | `ack_delay_exponent` | 3 (8us base) | Standard RFC 9000 |
| 7 | `max_data` | 4 GB cap (16x BDP) | 10 Gbps@600ms = 750 MB BDP, 16x = 12 GB, cap 4 GB |
| 8 | `max_stream_data` | = max_data | Stream unique par TCP, pas de raison de limiter |
| 9 | `max_streams_bidi` | 10,000 | Largement suffisant pour concurrence |
| 10 | `max_idle_timeout` | 120s | Evite timeout sur liaisons intermittentes |
| 11 | `keepalive_interval` | LEO:10s MEO:15s GEO:30s | Proportionnel au RTT, previent idle timeout |
| 12 | `enable_0rtt` | false (configurable) | Desactive par defaut (securite replay attack) |
| 13 | `handshake_timeout` | LEO:5s MEO:10s GEO:30s | ~5x RTT pour les round-trips handshake |
| 14 | `enable_datagrams` | true | RFC 9221, utilise pour signaling FEC |
| 15 | `disable_active_migration` | LEO:false GEO:true | LEO a besoin de migration pour handovers Starlink |
| 16 | `active_connection_id_limit` | LEO:4 MEO:3 GEO:2 | Plus de CIDs = plus de paths pour migration |
| 17 | `enable_pacing` | true | Requis par BBR2 |
| 18 | `enable_hystart` | true | HyStart++ pour slow-start adaptatif |
| 19 | `discover_pmtu` | true | Trouver le MTU optimal du path |
| 20 | `grease` | true | RFC 8701 anti-ossification |
| 21 | `max_pacing_rate` | 0 (unlimited) | BBR2 s'auto-regule |
| 22 | `max_connection_window` | 8 GB cap (4x max_data) | Flow control window growth |
| 23 | `max_stream_window` | = connection window | Pas de raison de limiter |

### 2.2 Quick wins implementes (Phase 3)

| # | Parametre | Avant | Apres | Impact |
|---|-----------|-------|-------|--------|
| 24 | `max_amplification_factor` | 3 (default) | LEO/MEO/GEO: 10 | Handshake 3x plus rapide sur GEO |
| 25 | `path_challenge_recv_max_queue_len` | 3 (default) | LEO:16 MEO:8 GEO:4 | Absorbe rafales PATH_CHALLENGE pendant handovers |

### 2.3 Parametres NON exposables (hardcodes dans quiche)

| Parametre | Valeur hardcodee | Valeur ideale satellite | Fichier source |
|-----------|-----------------|------------------------|----------------|
| `INITIAL_PACKET_THRESHOLD` | 3 | 6-10 | `recovery/mod.rs:54` |
| `INITIAL_TIME_THRESHOLD` | 9/8 (1.125x RTT) | 2.0x RTT | `recovery/mod.rs:58` |
| `GRANULARITY` | 1ms | 1ms (ok) | `recovery/mod.rs:60` |
| `MAX_PTO_PROBES_COUNT` | 2 | 3-4 | `recovery/mod.rs:62` |
| `LOSS_REDUCTION_FACTOR` | 0.5 | 0.7 | `recovery/mod.rs:66` |
| `MINIMUM_WINDOW_PACKETS` | 2 | 4 | `recovery/mod.rs:64` |

**Pourquoi ces valeurs sont problematiques pour satellite:**

`packet_threshold = 3` : Si paquet N+3 arrive mais pas N, N est declare perdu. Sur
satellite le reordonnancement est frequent (jitter 5-15ms sur Starlink). Un paquet
legerement retarde declenche une fausse perte, CWND reduit de 50%, throughput
s'effondre. Avec `packet_threshold = 6-10` on tolere le jitter sans fausse retransmission.

`LOSS_REDUCTION_FACTOR = 0.5` : Sur fausse perte (jitter satellite), le CWND est
divise par 2. Avec 0.7, on perd seulement 30% au lieu de 50%, recovery plus rapide.

### 2.4 ACK Frequency (RFC 9330) - La piece manquante majeure

**Statut**: Non implemente dans quiche 0.22.0

Sur un lien satellite asymetrique (downlink 100 Mbps, uplink 5 Mbps), chaque ACK
consomme de la bande passante uplink. Par defaut QUIC envoie un ACK tous les 2
paquets. A 100 Mbps ca fait ~37,000 ACKs/seconde sur le uplink.

Avec RFC 9330, on pourrait dire "ACK tous les 10 paquets" et reduire le trafic
ACK de 80%. C'est specifiquement concu pour les liens asymetriques (DOCSIS, LTE,
satellite).

References:
- RFC 9330: QUIC Acknowledgment Frequency
- Satellite ACK Frequency: doi.org/10.1002/sat.1466

### 2.5 BBR2 Internals (non exposables)

| Parametre interne | Valeur quiche | Ideal satellite | Pourquoi |
|-------------------|--------------|-----------------|----------|
| `pacing_gain` (ProbeBW) | ~1.25 | 1.5-2.0 | Probe plus agressivement sur high-BDP |
| `cwnd_gain` | 2.0 | 3.0 | Maintenir plus de buffer pendant probing |
| `ProbeRTT` duration | 200ms | 500ms+ | GEO RTT=600ms, ProbeRTT trop court |

## 3. Strategies creatives au niveau applicatif

### 3.1 Multi-stream par connexion TCP (a implementer)

```text
  TCP Client          QUICK- Entry              QUICK- Exit           TCP Server
  =========          ===========              ==========           ==========
      |                   |                       |                     |
      |---TCP data------->|                       |                     |
      |                   |--Stream 0 (chunk 0)-->|                     |
      |                   |--Stream 1 (chunk 1)-->|                     |
      |                   |--Stream 2 (chunk 2)-->|                     |
      |                   |--Stream 3 (chunk 3)-->|                     |
      |                   |                       |--reassemble-------->|
      |                   |                       |---TCP data--------->|
```

Avantages:
- Chaque stream a son propre flow control
- Perte sur stream 0 ne bloque pas streams 1-3 (pas de head-of-line blocking)
- Debit total = N x debit par stream
- BBR2 envoie N fois plus de paquets par RTT

### 3.2 Pre-echauffement CWND

Envoyer des padding frames sur la connexion pool au demarrage pour que BBR2
monte en regime avant le premier vrai trafic. Sur GEO, BBR2 met ~5 RTT (3s)
pour trouver le debit optimal.

### 3.3 Adaptation dynamique des profils

Mesurer RTT reel et loss rate, basculer automatiquement entre profils transport
(deja partiellement implemente via `ProtocolSwitcher` pour QUIC/KCP).

## 4. Matrice effort/impact

| Strategie | Effort | Impact throughput | Priorite |
|-----------|--------|-------------------|----------|
| Quick wins (amplification, path_challenge) | Faible | +5-15% handshake | P1 DONE |
| Multi-stream (4 streams/TCP) | Moyen | +50-200% | P1 (concu) |
| Pre-echauffement CWND | Faible | +10-20% premiere requete | P2 |
| Fork quiche: packet_threshold | Eleve | +20-40% sur liens lossy | P2 |
| Fork quiche: ACK frequency | Eleve | +10-30% sur liens asymetriques | P3 |
| Fork quiche: BBR gains | Eleve | +5-15% | P3 |

## 5. Architecture multi-stream detaillee

### 5.1 Probleme

Actuellement, 1 connexion TCP = 1 stream QUIC. Le stream QUIC a son propre flow control
(`max_stream_data`), et une perte de paquet sur ce stream bloque TOUTE la livraison
(head-of-line blocking au niveau stream). QUIC elimine le HoL blocking entre streams
differents, mais pas DANS un meme stream.

Sur satellite avec 0.5-2% de pertes, un seul stream QUIC plafonne a:

```text
Throughput = max_stream_data / RTT_effectif
Avec retransmissions: RTT_effectif = RTT + (loss_rate * RTT) = RTT * (1 + loss)
GEO 1% loss: throughput = 4GB / (0.6s * 1.01) ~ 6.6 Gbps theorique
                    Mais en pratique, BBR reduit CWND de 50% a chaque perte detectee
                    Resultat reel: ~30-50% du throughput theorique
```

### 5.2 Solution: N streams par connexion TCP

```text
TCP Client          QUICK- Entry              QUICK- Exit           TCP Server
=========          ===========              ==========           ==========
    |                   |                       |                     |
    |---TCP data------->|                       |                     |
    |   (chunk 0-3)     |--Stream 0: header---->|                     |
    |                   |--Stream 1: chunk 0--->|                     |
    |                   |--Stream 2: chunk 1--->|                     |
    |                   |--Stream 3: chunk 2--->|                     |
    |                   |--Stream 4: chunk 3--->|                     |
    |                   |                       |--reassemble-------->|
    |                   |                       |---TCP data--------->|
```

### 5.3 Protocole de chunks

Chaque chunk transporte un en-tete de 12 octets:

```text
+--------+--------+--------+--------+
| Magic (2B)      | Version (1B)    |
+--------+--------+--------+--------+
| Flags  | Stream Count (1B)        |
+--------+--------+--------+--------+
| Sequence Number (4B, big-endian)  |
+--------+--------+--------+--------+
| Payload Length (2B, big-endian)    |
+--------+--------+--------+--------+
| Payload (variable)                |
+--------+--------+--------+--------+
```

- **Magic**: `0x4D53` ("MS" pour MultiStream)
- **Version**: `0x01`
- **Flags**: bit 0 = FIN (dernier chunk du transfert), bits 1-7 reserves
- **Stream Count**: nombre total de streams de donnees (N)
- **Sequence Number**: compteur monotone croissant, global
- **Payload Length**: taille des donnees utiles (0 a 65535)

### 5.4 Flux de controle

**Entry (emetteur):**

1. Ouvre N+1 streams QUIC: stream 0 = controle, streams 1..N = donnees
2. Envoie StreamHeader existant sur stream 0 (compatible avec exit actuel)
3. Ajoute un `MultiStreamHeader` sur stream 0 apres le StreamHeader:
   - `stream_count: u8` (N)
   - `chunk_size: u32` (taille cible des chunks, ex: 64 KB)
   - `stream_ids: Vec<u64>` (IDs des N streams de donnees)
4. Boucle de relay:
   - Lit chunk depuis TCP (taille = chunk_size)
   - Assigne `seq_number` (atomique, monotone)
   - Envoie sur stream `(seq_number % N) + 1` avec en-tete chunk
   - Avance le round-robin

**Exit (recepteur):**

1. Recoit StreamHeader sur stream 0 (comme avant)
2. Lit MultiStreamHeader pour connaitre N et les stream IDs
3. Lance N taches de reception, une par stream de donnees
4. Chaque tache:
   - Lit les chunks avec en-tete
   - Envoie (seq_number, payload) dans un canal MPSC vers le reassembleur
5. Reassembleur:
   - Maintient un `BTreeMap<u32, Vec<u8>>` des chunks recus
   - Ecrit les chunks dans l'ordre sequentiel vers TCP
   - Attend les chunks manquants (timeout = 2x RTT, puis passe)

### 5.5 Reorder buffer

```rust
struct ReorderBuffer {
    /// Chunks recus hors-ordre, indexees par sequence number
    pending: BTreeMap<u32, Vec<u8>>,
    /// Prochain sequence number attendu
    next_expected: u32,
    /// Timeout pour chunk manquant (2x RTT estime)
    gap_timeout: Duration,
    /// Timestamp du dernier chunk livre
    last_delivery: Instant,
    /// Taille max du buffer (previent OOM sur bursts)
    max_buffered: usize,
}
```

**Invariant**: On ne livre jamais un chunk sans avoir livre (ou timeout) tous les
precedents. Cela garantit l'ordre TCP.

**Optimisation**: Si tous les chunks arrivent dans l'ordre (0% loss, ideal), le
BTreeMap reste vide et le throughput est identique a sans-reorder.

### 5.6 Dimensionnement

| Parametre | LEO | MEO | GEO | Justification |
|-----------|-----|-----|-----|---------------|
| N (streams) | 4 | 4 | 8 | GEO: plus de HoL, besoin de plus de parallelisme |
| chunk_size | 64 KB | 64 KB | 128 KB | Plus gros chunks sur GEO = moins d'overhead headers |
| reorder_buffer_max | 256 chunks | 256 chunks | 512 chunks | GEO: BDP plus grand, plus de chunks en vol |
| gap_timeout | 100 ms | 240 ms | 1200 ms | ~2x RTT |

### 5.7 Gain attendu

```text
Single-stream:  1 perte = tout le stream bloque pendant 1 RTT
                Debit = Base * (1 - loss_rate * RTT_factor)

Multi-stream N: 1 perte = 1/N des streams bloque, N-1 continuent
                Debit = Base * (1 - loss_rate * RTT_factor / N)

Pour N=4, GEO, 1% loss:
    Single: ~50% throughput effectif
    Multi:  ~87.5% throughput effectif (+75% vs single)

Pour N=8, GEO, 2% loss:
    Single: ~40% throughput effectif
    Multi:  ~82.5% throughput effectif (+106% vs single)
```

### 5.8 Integration avec code existant

**Fichiers a modifier:**

| Fichier | Changement |
|---------|------------|
| `quick-protocol/src/lib.rs` | Ajouter `MultiStreamHeader`, `ChunkHeader` structs |
| `entry/tunnel.rs` | Ajouter `MultiStreamTunnel` qui ouvre N+1 streams |
| `exit/tunnel.rs` | Ajouter reception multi-stream + `ReorderBuffer` |
| `entry/cli.rs` | `--multi-stream N` flag (default 1 = desactive) |
| `exit/cli.rs` | Pas de flag necessaire (auto-detecte via header) |
| `quick-transport` | Pas de changement (streams QUIC sont deja supportes) |

**Retrocompatibilite**: Si `MultiStreamHeader` absent apres StreamHeader,
l'exit fonctionne en mode single-stream (comportement actuel). Le multi-stream
est opt-in cote entry via `--multi-stream N`.

### 5.9 Risques et mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Reorder buffer OOM | Crash exit proxy | Max buffer size (512 chunks x 128 KB = 64 MB) |
| Deadlock: tous les streams bloques | Throughput = 0 | Timeout + fallback single-stream |
| Overhead protocole chunks | -1-2% throughput | Chunks de 64-128 KB, header = 12 octets = 0.02% |
| Complexite debugging | Bugs subtils d'ordre | Extensive tests avec netem (loss, reorder, delay) |

## 6. References

1. Pavur et al., "QPEP: An Actionable Approach to Secure and Performant Broadband
   From Geostationary Orbit", NDSS 2021
2. StarQUIC: Satellite-optimized QUIC, ACM LEONet 2024
3. RFC 9000: QUIC Transport Protocol
4. RFC 9002: QUIC Loss Detection and Congestion Control
5. RFC 9330: QUIC Acknowledgment Frequency
6. RFC 8701: GREASE for QUIC
7. Claypool et al., PAM 2021 / CCNC 2022 - PEP performance analysis
8. ESA QUICoS / QUICOPTSAT projects (2022+)
