# Network Deployment Scenarios

Three deployment scenarios for VarunaPoC in hospital environments, plus air-gapped installation procedure.

## Scenario 1: LAN Only (Single Site)

**Use case:** Pathology lab with scanner and viewer on same hospital network. No external access.

### Network Configuration

```
[Scanner] --LAN--> [NAS /Slides] --LAN--> [VarunaPoC Server] <--LAN-- [Workstations]
```

### Nginx

```nginx
server_name varuna.internal.hospital.be;
# No HTTPS needed if network is physically isolated
# Or use self-signed cert for defense-in-depth
listen 443 ssl;
ssl_certificate /etc/nginx/ssl/self-signed.crt;
```

### CORS

```bash
CORS_ORIGINS=http://varuna.internal.hospital.be,https://varuna.internal.hospital.be
```

### Firewall Rules

```bash
# Allow only hospital LAN (example: 10.0.0.0/8)
iptables -A INPUT -s 10.0.0.0/8 -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j DROP
```

### DNS

Add an A record in the hospital DNS server:

```
varuna.internal.hospital.be  A  10.1.2.100
```

---

## Scenario 2: VPN Telepathology (Multi-Site)

**Use case:** Remote pathologists reviewing slides from home or satellite hospitals via VPN.

### Network Configuration

```
[Remote Pathologist] --VPN--> [Hospital Gateway] --LAN--> [VarunaPoC Server]
```

### VPN Setup (WireGuard)

Server (`/etc/wireguard/wg0.conf`):

```ini
[Interface]
Address = 10.200.0.1/24
ListenPort = 51820
PrivateKey = <server-private-key>

[Peer]
# Remote pathologist
PublicKey = <peer-public-key>
AllowedIPs = 10.200.0.2/32
```

Client:

```ini
[Interface]
Address = 10.200.0.2/32
PrivateKey = <client-private-key>
DNS = 10.1.2.1

[Peer]
PublicKey = <server-public-key>
Endpoint = vpn.hospital.be:51820
AllowedIPs = 10.1.2.0/24
```

### Nginx

```nginx
server_name varuna.hospital.be;
listen 443 ssl http2;
# Use hospital CA-signed cert
ssl_certificate /etc/nginx/ssl/varuna.hospital.be.crt;
```

### CORS

```bash
CORS_ORIGINS=https://varuna.hospital.be
```

### Firewall Rules

```bash
# VPN interface
iptables -A INPUT -i wg0 -p tcp --dport 443 -j ACCEPT
# Hospital LAN
iptables -A INPUT -s 10.1.2.0/24 -p tcp --dport 443 -j ACCEPT
# Drop all other
iptables -A INPUT -p tcp --dport 443 -j DROP
```

### Performance Notes

- VPN adds 10-30ms latency; tile prefetching in OpenSeadragon compensates
- Bandwidth: ~2-5 Mbps per active viewer session (256x256 JPEG tiles)
- WireGuard is recommended over OpenVPN (lower overhead, kernel-level)

---

## Scenario 3: Internet Behind WAF (Public Access)

**Use case:** Teaching hospital with public-facing viewer behind a Web Application Firewall.

### Network Configuration

```
[Internet] --> [WAF/CDN] --> [Reverse Proxy] --> [VarunaPoC Server]
```

### WAF Configuration (Cloudflare / Azure Front Door)

- Rate limit: 100 req/min per IP on `/api/` endpoints
- Rate limit: 500 req/min per IP on tile endpoints
- Block requests without valid `Referer` header
- Enable bot protection
- Cache tile responses at CDN edge (24h TTL)

### Nginx

```nginx
server_name pathology.hospital.be;
listen 443 ssl http2;
ssl_certificate /etc/letsencrypt/live/pathology.hospital.be/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/pathology.hospital.be/privkey.pem;

# Trust WAF proxy headers
set_real_ip_from 173.245.48.0/20;  # Cloudflare ranges
real_ip_header CF-Connecting-IP;
```

### CORS

```bash
CORS_ORIGINS=https://pathology.hospital.be
```

### Additional Security

```bash
# Enable auth (mandatory for public access)
AUTH_ENABLED=true
# Restrict slide access to authenticated users only
# OIDC with hospital identity provider
OIDC_ISSUER=https://login.hospital.be/realms/pathology
```

---

## Air-Gapped Installation

For hospitals with no internet access on production servers.

### Step 1: Build Images on Connected Machine

```bash
# On a machine with internet access
cd VarunaPoC
docker compose --profile prod --profile monitoring build

# Save all images to tar archives
docker save varuna-backend:latest | gzip > varuna-backend.tar.gz
docker save varuna-frontend:latest | gzip > varuna-frontend.tar.gz
docker save nginx:alpine | gzip > nginx-alpine.tar.gz
docker save postgres:16-alpine | gzip > postgres-alpine.tar.gz
docker save prom/prometheus:latest | gzip > prometheus.tar.gz
docker save grafana/grafana:latest | gzip > grafana.tar.gz
docker save redis:7-alpine | gzip > redis-alpine.tar.gz
```

### Step 2: Transfer to Air-Gapped Server

```bash
# Copy to USB drive or secure transfer
cp *.tar.gz /media/usb/varuna-images/
cp docker-compose.yml /media/usb/varuna-images/
cp .env.production.example /media/usb/varuna-images/
```

### Step 3: Load Images on Target

```bash
# On the air-gapped server
for img in /media/usb/varuna-images/*.tar.gz; do
    echo "Loading $img..."
    docker load < "$img"
done
```

### Step 4: Deploy

```bash
# Copy compose and config
cp /media/usb/varuna-images/docker-compose.yml .
cp /media/usb/varuna-images/.env.production.example .env

# Edit .env with local values
vi .env

# Start services
docker compose --profile prod --profile monitoring up -d
```

### Update Procedure (Air-Gapped)

1. Build new images on connected machine
2. `docker save` only changed images
3. Transfer via USB
4. `docker load` on target
5. `docker compose pull` (from local) + `docker compose up -d`

### Verification

```bash
# Check all images are loaded
docker images | grep -E "varuna|nginx|postgres|prometheus|grafana|redis"

# Check services are running
docker compose --profile prod --profile monitoring ps

# Test health
curl -k https://localhost/health
```
