# Cahier des Charges - QUICK-

**Accelerateur QUIC pour Communications Satellites**

| | |
|---|---|
| **Client** | neXat |
| **Programme** | Bachelier en Informatique - EPHEC |
| **Version** | 2.0 |

---

## 1. Resume

**QUICK-** est un accelerateur de trafic transparent qui remplace TCP par QUIC/UDP sur les liaisons satellites. L'objectif est d'eliminer les limitations inherentes de TCP (latence d'etablissement, sensibilite aux pertes, head-of-line blocking) en exploitant les caracteristiques du protocole QUIC.

| Probleme TCP | Solution QUIC |
|--------------|---------------|
| 3 RTT pour etablir connexion + TLS | 1 RTT (0 RTT en reconnexion) |
| Pertes = reduction fenetre congestion | BBR : estimation bande passante, tolerant aux pertes |
| Head-of-line blocking | Flux independants multiplexes |
| Fenetres inadaptees aux hauts BDP | Fenetres configurables selon profil satellite |

---

## 2. Contexte

### 2.1 Client

**neXat** : Fournisseur de solutions de connectivite satellite. Opere une plateforme de services pour clients dans les secteurs maritime, minier, gouvernemental et petrolier.

### 2.2 Problematique

Les liaisons satellites souffrent de :

| Caracteristique | LEO (Starlink) | MEO | GEO |
|-----------------|----------------|-----|-----|
| RTT typique | 30-50 ms | 120 ms | 500-600 ms |
| Taux de perte | 1-2% | 1-2% | 1-2% |
| Bande passante | 50-200 Mbps | 10-50 Mbps | 1-20 Mbps |

**Impact sur TCP** :
- Sous-utilisation de la bande passante (20-30% du theorique)
- Latence percue elevee (multiples RTT pour etablir connexion)
- Degradation severe en cas de pertes (interpretation comme congestion)

### 2.3 Solution

Un tunnel transparent QUIC/UDP entre deux points :

```
[Applications]          [Applications]
     |                       ^
     v (TCP)                 | (TCP)
+-----------+           +-----------+
|  QUICK-   |==QUIC/UDP=|  QUICK-   |
|  (entry)  |  satellite |  (exit)   |
+-----------+           +-----------+
```

**Principe** : Les applications communiquent en TCP local. QUICK- intercepte ce trafic et le transporte via QUIC sur UDP a travers la liaison satellite, eliminant completement TCP du chemin satellite.

---

## 3. Objectifs et Metriques

### 3.1 Objectif Principal

Demontrer une amelioration mesurable des performances sur liaison satellite par rapport a TCP standard.

### 3.2 Metriques de Succes

| Metrique | Definition | Objectif | Justification |
|----------|------------|----------|---------------|
| **Latence etablissement** | Temps jusqu'a premiere donnee applicative | **-66%** | TCP+TLS: 3 RTT, QUIC: 1 RTT |
| **Debit effectif** | Throughput sur transfert 100 MB | **x2** | Fenetres adaptees au BDP, BBR |
| **Recovery time** | Temps de recuperation apres perte 2% | **-40%** | Retransmission selective vs Go-Back-N |

### 3.3 Calcul des Objectifs

**Latence etablissement** :
```
TCP + TLS 1.2 : SYN + SYN-ACK + ACK + ClientHello + ServerHello + ... = ~3 RTT
QUIC         : ClientHello + ServerHello (combines) = 1 RTT
Gain theorique : (3-1)/3 = 66%
Objectif conservateur : 30% minimum
```

**Debit (BDP - Bandwidth Delay Product)** :
```
BDP = Bandwidth x RTT
Exemple GEO : 100 Mbps x 0.6s = 60 Mbit = 7.5 MB
TCP default window : 64 KB << 7.5 MB -> sous-utilisation
QUIC window configurable : jusqu'a 16 MB -> utilisation optimale
```

**Recovery** :
```
TCP : Go-Back-N, retransmet depuis le segment perdu
QUIC : Selective ACK, retransmet uniquement les segments perdus
Gain depend du pattern de perte, 40% est une estimation conservative
```

### 3.4 Criteres d'Acceptation

| Critere | Obligatoire | Mesure |
|---------|-------------|--------|
| Tunnel fonctionnel sans perte de donnees | Oui | Tests d'integrite (checksum) |
| Amelioration latence >= 30% | Oui | Benchmark vs TCP direct |
| Amelioration debit >= x1.5 | Oui | Benchmark vs TCP direct |
| Stabilite (pas de crash sur 1h de test) | Oui | Tests de charge |
| Transparence applicative | Oui | Apps non modifiees |

**Note** : Si les objectifs chiffres ne sont pas atteints, le projet reste valide si l'analyse explique les causes (limitations de l'implementation, conditions de test, etc.).

---

## 4. Specifications Fonctionnelles

### 4.1 Architecture

**Programme unique symetrique** : Un seul binaire `quick-` configurable en mode entry ou exit.

```
quick- --mode entry --listen 0.0.0.0:8080 --remote exit.example.com:4433
quick- --mode exit --listen 0.0.0.0:4433
```

### 4.2 Exigences Fonctionnelles

| ID | Exigence | Priorite |
|----|----------|----------|
| F01 | Accepter connexions TCP entrantes | Obligatoire |
| F02 | Encapsuler flux TCP dans QUIC | Obligatoire |
| F03 | Transmettre via UDP sur le lien satellite | Obligatoire |
| F04 | Desencapsuler et retablir connexion TCP | Obligatoire |
| F05 | Supporter TLS 1.3 obligatoire | Obligatoire |
| F06 | Multiplexer plusieurs flux TCP dans un tunnel QUIC | Obligatoire |
| F07 | Capturer metadonnees applicatives (headers HTTP, etc.) | Obligatoire |
| F08 | Stocker metadonnees dans TimescaleDB | Obligatoire |
| F09 | Configuration par fichier YAML | Obligatoire |
| F10 | Configuration par arguments CLI | Obligatoire |
| F11 | Logs detailles (configurable verbosity) | Obligatoire |
| F12 | Reconnexion 0-RTT | Souhaitable |
| F13 | Migration de connexion | Optionnel |

### 4.3 Parametres Configurables

#### Controle de Congestion

| Parametre | Description | Valeurs | Defaut |
|-----------|-------------|---------|--------|
| `algorithm` | Algorithme de congestion | `bbr`, `bbr2`, `cubic` | `bbr2` |
| `initial_cwnd` | Fenetre de congestion initiale (segments) | 10-64 | 32 |
| `max_cwnd` | Fenetre maximale | 64KB-16MB | 8MB |

#### Timing

| Parametre | Description | Valeurs | Defaut |
|-----------|-------------|---------|--------|
| `initial_rtt` | RTT initial estime | 10ms-1000ms | 100ms |
| `idle_timeout` | Timeout inactivite | 10s-300s | 90s |
| `handshake_timeout` | Timeout etablissement | 5s-60s | 15s |
| `keep_alive` | Intervalle keep-alive | 0-60s | 30s |

#### Flux

| Parametre | Description | Valeurs | Defaut |
|-----------|-------------|---------|--------|
| `max_streams` | Nombre max de flux simultanes | 8-256 | 100 |
| `stream_window` | Fenetre par flux | 64KB-4MB | 1MB |
| `connection_window` | Fenetre connexion globale | 1MB-16MB | 8MB |

#### Securite

| Parametre | Description | Valeurs | Defaut |
|-----------|-------------|---------|--------|
| `cert_file` | Certificat TLS | chemin | requis |
| `key_file` | Cle privee TLS | chemin | requis |
| `verify_peer` | Verification certificat peer | true/false | true |

### 4.4 Capture de Metadonnees

**Objectif** : Analyse de trafic pour optimisation et debugging.

**Donnees capturees** (couche applicative) :

| Categorie | Champs |
|-----------|--------|
| Identification | `flow_id`, `timestamp`, `stream_id` |
| HTTP | `method`, `host`, `path`, `status_code`, `content_type`, `content_length` |
| Session | `session_id`, `user_agent`, `referer` |
| Performance | `request_time`, `response_time`, `bytes_sent`, `bytes_received` |
| Transport | `rtt_ms`, `packet_loss_rate`, `retransmissions` |

**Stockage** : TimescaleDB (hypertable partitionnee par temps)

**Contrainte** : Insertion asynchrone, impact < 1ms sur latence du tunnel.

### 4.5 Interface CLI

```bash
# Demarrage
quick- start --config /etc/quick/config.yaml
quick- start --mode entry --listen :8080 --remote server:4433

# Status
quick- status                    # Etat general
quick- status --streams          # Flux actifs
quick- status --metrics          # Metriques temps reel

# Configuration runtime
quick- config set idle_timeout 120s
quick- config get algorithm

# Logs
quick- logs                      # Derniers logs
quick- logs --follow             # Temps reel
quick- logs --level debug        # Filtrer par niveau
```

---

## 5. Specifications Non-Fonctionnelles

| Categorie | Exigence | Seuil |
|-----------|----------|-------|
| **Performance** | Latence ajoutee par le proxy | < 5ms (hors RTT satellite) |
| **Performance** | Debit supporte | >= 100 Mbps |
| **Performance** | Connexions simultanees | >= 100 |
| **Ressources** | CPU (a 50 Mbps) | < 50% d'un coeur |
| **Ressources** | Memoire | < 512 MB |
| **Securite** | Chiffrement | TLS 1.3 obligatoire |
| **Securite** | Pas de downgrade TLS | Obligatoire |
| **Fiabilite** | Disponibilite en test | 99% sur 24h |
| **Portabilite** | OS | Linux x86_64 (prioritaire) |
| **Maintenabilite** | Couverture tests | >= 60% |

---

## 6. Strategie de Validation

### 6.1 Phase 1 : Tests Fonctionnels (Environnement Simule)

**Environnement** : Docker + netem (simulation latence/pertes)

| Test | Description | Critere |
|------|-------------|---------|
| T1.1 | Connectivite basique | Ping 100 paquets, 0% perte |
| T1.2 | Transfert HTTP | Page 1KB, integrite OK |
| T1.3 | Transfert HTTPS | TLS valide, contenu OK |
| T1.4 | Gros fichier | 10MB, checksum OK |
| T1.5 | Multiplexage | 3 transferts paralleles OK |
| T1.6 | Resilience pertes | Transfert OK avec 5% perte |
| T1.7 | Metadonnees | Donnees presentes dans TimescaleDB |

### 6.2 Phase 2 : Benchmarks Comparatifs

**Protocole** :
1. Etablir baseline TCP (memes conditions simulees)
2. Executer tests QUIC
3. Comparer statistiquement (min 30 echantillons)

| Benchmark | Mesure | Outil |
|-----------|--------|-------|
| B1 | Latence HTTP GET | curl timing x100 |
| B2 | Debit download | iperf3, fichier 100MB x5 |
| B3 | Recovery apres perte | Transfert 10MB @ 2% perte x10 |
| B4 | Temps etablissement | Wireshark, analyse paquets |

**Conditions simulees** :
- RTT : 600ms (GEO), 50ms (LEO)
- Perte : 0%, 1%, 2%, 5%
- Bande passante : 10 Mbps, 50 Mbps, 100 Mbps

### 6.3 Phase 3 : Validation Starlink

**Prerequis** : Phases 1 et 2 reussies a 100%

**Responsable** : Etudiant, planification par neXat

**Procedure** :
1. Mesurer baseline TCP sur Starlink
2. Deployer QUICK-
3. Executer benchmarks B1-B4
4. Collecter metriques et logs
5. Analyser resultats

**Critere de succes** : Amelioration demontrable sur au moins 2 des 3 metriques principales (latence, debit, recovery).

---

## 7. Livrables

| Livrable | Format | Description |
|----------|--------|-------------|
| Code source | Git repository | Code complet, compile, teste |
| README | Markdown | Installation rapide, demarrage |
| Guide d'installation | Markdown | Prerequis, compilation, configuration |
| Manuel utilisateur | Markdown | Commandes CLI, parametres |
| Guide d'exploitation | Markdown | Logs, maintenance, troubleshooting |
| Documentation architecture | Markdown + UML | Diagrammes, decisions techniques |
| Rapport benchmark | Markdown | Resultats, analyse statistique |
| Rapport TFE | PDF | Document academique complet |

---

## 8. Risques

| Risque | Impact | Probabilite | Mitigation |
|--------|--------|-------------|------------|
| Performances insuffisantes | Eleve | Faible | Tests iteratifs, analyse des causes |
| Acces Starlink retarde | Moyen | Moyen | Validation en simulation acceptable |
| Bugs critiques tardifs | Moyen | Moyen | Tests continus, marge planning |
| Incompatibilite Starlink | Eleve | Faible | Tests exhaustifs en simulation |

---

## 9. Glossaire

| Terme | Definition |
|-------|------------|
| **BBR** | Bottleneck Bandwidth and RTT - Algorithme de congestion Google |
| **BDP** | Bandwidth Delay Product - Produit bande passante x RTT |
| **Head-of-line blocking** | Blocage ou la perte d'un paquet bloque tous les suivants |
| **QUIC** | Quick UDP Internet Connections - Protocole transport RFC 9000 |
| **RTT** | Round-Trip Time - Temps aller-retour d'un paquet |
| **0-RTT** | Etablissement connexion sans aller-retour (reconnexion) |
| **Selective ACK** | Acquittement selectif des paquets recus |

---

## 10. References

- RFC 9000 - QUIC: A UDP-Based Multiplexed and Secure Transport
- RFC 9001 - Using TLS to Secure QUIC
- RFC 9002 - QUIC Loss Detection and Congestion Control
- draft-ietf-ccwg-bbr - BBR Congestion Control

---

*Version 2.0 - Decembre 2024*
