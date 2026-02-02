# VarunaPoC - Phase 2 Network Integration Guide

**Version:** 2.0
**Last Updated:** 2025-12-03
**Status:** Production Ready
**Phase:** 2.1 and 2.2 Network Deployment

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Phase 2.1: Network Access + Local Slides](#phase-21-network-access--local-slides)
4. [Phase 2.2: Network Access + CHU Infrastructure](#phase-22-network-access--chu-infrastructure)
5. [Prerequisites](#prerequisites)
6. [Deployment Steps](#deployment-steps)
7. [Testing and Validation](#testing-and-validation)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)
10. [Maintenance](#maintenance)

---

## Overview

Phase 2 enables **network access** to VarunaPoC, allowing PC clients (including Telemis PACS) to access the web-based slide viewer over the hospital network.

### Phase Evolution

- **Phase 1 (localhost):** Backend and frontend accessible only on server (http://localhost)
- **Phase 2.1 (network + local):** Network access enabled, slides from local server storage
- **Phase 2.2 (network + CHU):** Network access enabled, slides from CHU infrastructure (\\imgsv-01-p\anapath_storage_nimble)

### Key Changes from Phase 1

| Aspect | Phase 1 | Phase 2 |
|--------|---------|---------|
| **Access** | localhost only | Network-wide (http://varun-p-01) |
| **Backend Port** | 127.0.0.1:8000 | 0.0.0.0:8000 |
| **Frontend Port** | 127.0.0.1:80 | 0.0.0.0:80 |
| **CORS** | localhost only | varun-p-01 + localhost |
| **Slides (2.1)** | /local/slides | /local/slides (same) |
| **Slides (2.2)** | /local/slides | /mnt/chu-slides (network share) |

---

## Architecture

### Phase 2.1 Architecture (Local Slides)

```
┌──────────────────┐
│  PC Client       │
│  (Telemis PACS)  │
│                  │
│  Opens Chrome:   │
│  http://varun-   │
│    p-01/slide/ID │
└────────┬─────────┘
         │ HTTP (network)
         │
         ▼
┌──────────────────────────────────────┐
│  Server: varun-p-01                  │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Frontend Container            │ │
│  │  Port: 0.0.0.0:80              │ │
│  │  Serves: index.html + JS       │ │
│  └────────┬───────────────────────┘ │
│           │                          │
│           │ Fetch tiles              │
│           ▼                          │
│  ┌────────────────────────────────┐ │
│  │  Backend Container             │ │
│  │  Port: 0.0.0.0:8000            │ │
│  │  OpenSlide + FastAPI           │ │
│  └────────┬───────────────────────┘ │
│           │                          │
│           │ Read slides              │
│           ▼                          │
│  ┌────────────────────────────────┐ │
│  │  /local/slides                 │ │
│  │  (Local mount on server)       │ │
│  └────────────────────────────────┘ │
└──────────────────────────────────────┘
```

### Phase 2.2 Architecture (CHU Infrastructure)

```
┌──────────────────┐
│  PC Client       │
│  (Telemis PACS)  │
│                  │
│  Opens Chrome:   │
│  http://varun-   │
│    p-01/slide/ID │
└────────┬─────────┘
         │ HTTP (network)
         │
         ▼
┌──────────────────────────────────────┐
│  Server: varun-p-01                  │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Frontend Container            │ │
│  │  Port: 0.0.0.0:80              │ │
│  └────────┬───────────────────────┘ │
│           │                          │
│           │ Fetch tiles              │
│           ▼                          │
│  ┌────────────────────────────────┐ │
│  │  Backend Container             │ │
│  │  Port: 0.0.0.0:8000            │ │
│  └────────┬───────────────────────┘ │
│           │                          │
│           │ Read slides (SMB)        │
│           ▼                          │
│  ┌────────────────────────────────┐ │
│  │  /mnt/chu-slides               │ │
│  │  (Mounted from network share)  │ │
│  └────────┬───────────────────────┘ │
└───────────┼──────────────────────────┘
            │ SMB/CIFS (port 445)
            ▼
┌──────────────────────────────────────┐
│  CHU Storage Infrastructure          │
│  imgsv-01-p                          │
│                                      │
│  \\imgsv-01-p\anapath_storage_nimble │
│  (Network share with all slides)     │
└──────────────────────────────────────┘
```

---

## Phase 2.1: Network Access + Local Slides

### Purpose

Test network accessibility and Telemis integration **without** dependencies on CHU infrastructure. Slides remain on local server storage.

### Use Cases

- Initial network testing
- Firewall and DNS configuration validation
- Telemis PACS integration testing
- Performance baseline (no network latency for slides)

### Requirements

- Server accessible via hostname: `varun-p-01`
- Ports 80 and 8000 open in firewall
- Slides stored locally at `/local/slides`
- DNS or hosts file entry for `varun-p-01`

### Deployment

```bash
# Navigate to project root
cd /path/to/VarunaPoC

# Run deployment script
./Scripts/Deployment/deploy-phase2.1.sh

# Script will:
# - Check prerequisites (Docker, files, ports)
# - Verify local slides directory
# - Test hostname resolution
# - Build Docker images
# - Start containers
# - Run post-deployment tests
```

### Configuration Files

- `docker-compose.phase2.1.yml` - Container orchestration
- `backend/.env.phase2.1` - Backend configuration
- `frontend/.env.phase2.1` - Frontend configuration

### Key Configuration

**Backend** (`backend/.env.phase2.1`):
```env
ENVIRONMENT=phase2.1-network-local-slides
SERVER_HOST=0.0.0.0
API_BASE_URL=http://varun-p-01:8000
CORS_ORIGINS=http://varun-p-01,http://localhost
SLIDES_REPOSITORY_PATH=/slides  # Maps to /local/slides on host
```

**Frontend** (`frontend/.env.phase2.1`):
```env
VITE_API_URL=http://varun-p-01:8000
VITE_ENVIRONMENT=phase2.1-network
```

### Testing Phase 2.1

**From Server:**
```bash
# Health check
curl http://localhost:8000/api/health
curl http://varun-p-01:8000/api/health

# Frontend
curl http://localhost:80
curl http://varun-p-01:80

# Slides API
curl http://localhost:8000/api/slides/
```

**From PC Client:**
```bash
# Health check
curl http://varun-p-01:8000/api/health

# Open browser
http://varun-p-01
```

### Stopping Phase 2.1

```bash
./Scripts/Deployment/stop-phase2.1.sh
```

---

## Phase 2.2: Network Access + CHU Infrastructure

### Purpose

Full production deployment with slides loaded from CHU network infrastructure (\\imgsv-01-p\anapath_storage_nimble).

### Use Cases

- Production deployment
- Access to all CHU histological slides
- Integration with existing CHU storage infrastructure
- PACS workflow integration

### Requirements

- Server accessible via hostname: `varun-p-01`
- Ports 80, 8000, and 445 (SMB) open in firewall
- Network share accessible: `\\imgsv-01-p\anapath_storage_nimble`
- Network share mounted at `/mnt/chu-slides`
- DNS entries for `varun-p-01` and `imgsv-01-p`
- SMB/CIFS credentials (if required)

### Network Share Mounting

**Linux Server:**
```bash
# Create mount point
sudo mkdir -p /mnt/chu-slides

# Mount network share (temporary)
sudo mount -t cifs -o username=USER,password=PASS,vers=3.0,uid=1000,gid=1000 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# Test mount
ls -la /mnt/chu-slides

# Verify slides accessible
find /mnt/chu-slides -name "*.mrxs" -o -name "*.bif" -o -name "*.tif"
```

**Persistent Mount (Linux):**
```bash
# Create credentials file
sudo nano /root/.smbcredentials

# Add credentials:
username=YOUR_USERNAME
password=YOUR_PASSWORD
domain=YOUR_DOMAIN

# Secure credentials file
sudo chmod 600 /root/.smbcredentials

# Add to /etc/fstab for persistent mount
sudo nano /etc/fstab

# Add line:
//imgsv-01-p/anapath_storage_nimble /mnt/chu-slides cifs credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,iocharset=utf8 0 0

# Mount from fstab
sudo mount -a

# Verify
mount | grep chu-slides
```

**Windows Server:**
```cmd
# Mount network share as drive Z:
net use Z: \\imgsv-01-p\anapath_storage_nimble /user:DOMAIN\USERNAME PASSWORD /persistent:yes

# Create symbolic link (for Docker)
mklink /D C:\mnt\chu-slides Z:\

# Test
dir Z:\
dir C:\mnt\chu-slides
```

### Deployment

```bash
# Ensure network share is mounted FIRST
ls -la /mnt/chu-slides

# If not mounted, mount it (see above)

# Navigate to project root
cd /path/to/VarunaPoC

# Run deployment script
./Scripts/Deployment/deploy-phase2.2.sh

# Script will:
# - Check prerequisites (Docker, files, ports)
# - Verify network share mount
# - Test hostname resolution (varun-p-01 and imgsv-01-p)
# - Check storage server accessibility
# - Build Docker images
# - Start containers
# - Run post-deployment tests
```

### Configuration Files

- `docker-compose.phase2.2.yml` - Container orchestration (network share mount)
- `backend/.env.phase2.2` - Backend configuration
- `frontend/.env.phase2.2` - Frontend configuration

### Key Configuration

**Backend** (`backend/.env.phase2.2`):
```env
ENVIRONMENT=phase2.2-network-chu-infrastructure
SERVER_HOST=0.0.0.0
API_BASE_URL=http://varun-p-01:8000
CORS_ORIGINS=http://varun-p-01,http://localhost
SLIDES_REPOSITORY_PATH=/slides  # Maps to /mnt/chu-slides on host
NETWORK_SHARE_PATH=\\\\imgsv-01-p\\anapath_storage_nimble
NETWORK_TIMEOUT=60  # Increased for network latency
MAX_TILE_CACHE_SIZE=200  # Larger cache for network
```

**Docker Compose** (`docker-compose.phase2.2.yml`):
```yaml
volumes:
  - /mnt/chu-slides:/slides:ro  # Network share mount
```

### Testing Phase 2.2

**From Server:**
```bash
# Verify network share mount
ls -la /mnt/chu-slides
find /mnt/chu-slides -name "*.mrxs" | head -5

# Verify container can access slides
docker exec varuna-backend-phase2.2 ls -la /slides
docker exec varuna-backend-phase2.2 find /slides -name "*.mrxs" | head -5

# Health check
curl http://localhost:8000/api/health
curl http://varun-p-01:8000/api/health

# Slides API
curl http://localhost:8000/api/slides/
```

**From PC Client:**
```bash
# Health check
curl http://varun-p-01:8000/api/health

# Open browser
http://varun-p-01

# Test specific slide (if you know a slide ID)
http://varun-p-01/slide/AO.25B27859.2.1.3
```

### Stopping Phase 2.2

```bash
./Scripts/Deployment/stop-phase2.2.sh

# Note: Network share remains mounted after stopping containers
# To unmount (if needed):
sudo umount /mnt/chu-slides  # Linux
net use Z: /delete           # Windows
```

---

## Prerequisites

### Hardware Requirements

- **Server:**
  - CPU: 4+ cores (8+ recommended for production)
  - RAM: 8GB minimum (16GB+ recommended)
  - Storage: 100GB+ for Docker images and logs
  - Network: 1Gbps Ethernet (10Gbps for high concurrency)

- **PC Clients:**
  - Modern browser (Chrome, Firefox, Edge)
  - 1920x1080+ resolution recommended
  - Network access to server

### Software Requirements

**Server:**
- Docker 20.10+ and Docker Compose 1.29+
- Linux (Ubuntu 20.04+, CentOS 8+) or Windows Server 2019+
- OpenSSH (for remote management)
- cifs-utils (Linux, for SMB mounts)

**Network:**
- DNS server or hosts file entries
- Firewall configured (ports 80, 8000, 445)
- VLAN access (if applicable)

### Network Requirements

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **DNS Resolution** | varun-p-01 → server IP | Add to DNS or hosts file |
| **DNS Resolution (2.2)** | imgsv-01-p → storage IP | Required for Phase 2.2 |
| **Firewall - Frontend** | Port 80 TCP (inbound) | HTTP access |
| **Firewall - Backend** | Port 8000 TCP (inbound) | API access |
| **Firewall - SMB (2.2)** | Port 445 TCP (outbound) | Network share access |
| **Bandwidth** | 100Mbps+ per client | Tile streaming |
| **Latency** | < 50ms to server | For smooth navigation |
| **Latency (2.2)** | < 100ms to storage | Network share access |

### Security Requirements

- [ ] Firewall rules configured (principle of least privilege)
- [ ] Network segmentation (VLAN for medical devices)
- [ ] SMB credentials secured (Phase 2.2)
- [ ] HTTPS planned for future phases (not Phase 2)
- [ ] Access logs enabled
- [ ] Regular security updates

---

## Deployment Steps

### Step-by-Step Deployment (Phase 2.1)

**1. Prepare Server**
```bash
# Update system
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
sudo yum update -y                      # CentOS/RHEL

# Install Docker (if not installed)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose (if not installed)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

**2. Configure Hostname Resolution**
```bash
# Add to /etc/hosts (Linux) or C:\Windows\System32\drivers\etc\hosts (Windows)
# On PC clients AND server
<SERVER_IP>  varun-p-01

# Example:
10.10.5.100  varun-p-01

# Test resolution
ping varun-p-01
```

**3. Configure Firewall**
```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# Windows Server
netsh advfirewall firewall add rule name="VarunaPoC HTTP" dir=in action=allow protocol=TCP localport=80
netsh advfirewall firewall add rule name="VarunaPoC API" dir=in action=allow protocol=TCP localport=8000
```

**4. Prepare Slides Directory**
```bash
# Create directory
sudo mkdir -p /local/slides
sudo chmod 755 /local/slides

# Copy slides (example)
sudo cp -r /source/slides/* /local/slides/

# Verify slides
find /local/slides -name "*.mrxs" -o -name "*.bif" -o -name "*.tif"
```

**5. Deploy VarunaPoC**
```bash
# Clone repository (if not already)
cd /opt
sudo git clone <repository-url> VarunaPoC
cd VarunaPoC

# Make scripts executable
chmod +x Scripts/Deployment/*.sh

# Run deployment
./Scripts/Deployment/deploy-phase2.1.sh

# Follow prompts and verify deployment
```

**6. Test from Server**
```bash
# Health check
curl http://localhost:8000/api/health
curl http://varun-p-01:8000/api/health

# Open browser (if GUI available)
xdg-open http://varun-p-01  # Linux with GUI
start http://varun-p-01     # Windows
```

**7. Test from PC Client**
```bash
# Test connectivity
ping varun-p-01
curl http://varun-p-01:8000/api/health

# Open browser
http://varun-p-01
```

### Step-by-Step Deployment (Phase 2.2)

Follow steps 1-3 from Phase 2.1, then:

**4. Mount Network Share**
```bash
# Linux: Install cifs-utils
sudo apt install cifs-utils -y  # Ubuntu/Debian
sudo yum install cifs-utils -y  # CentOS/RHEL

# Create mount point
sudo mkdir -p /mnt/chu-slides

# Create credentials file
sudo nano /root/.smbcredentials
# Add:
# username=YOUR_USERNAME
# password=YOUR_PASSWORD
# domain=YOUR_DOMAIN

sudo chmod 600 /root/.smbcredentials

# Test mount (temporary)
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# Verify mount
ls -la /mnt/chu-slides
find /mnt/chu-slides -name "*.mrxs" | head -5

# If successful, add to /etc/fstab for persistence
sudo nano /etc/fstab
# Add:
# //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides cifs credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,iocharset=utf8 0 0
```

**5. Configure Additional Firewall Rules**
```bash
# Allow outbound SMB (if not already allowed)
# Ubuntu/Debian (UFW)
sudo ufw allow out 445/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=samba-client
sudo firewall-cmd --reload
```

**6. Deploy VarunaPoC Phase 2.2**
```bash
cd /opt/VarunaPoC

# Run deployment
./Scripts/Deployment/deploy-phase2.2.sh

# Script will verify network share mount before deploying
```

**7. Test Network Share Access in Container**
```bash
# Verify container can access slides
docker exec varuna-backend-phase2.2 ls -la /slides
docker exec varuna-backend-phase2.2 find /slides -name "*.mrxs" | head -5

# If no slides found, check volume mount in docker-compose.phase2.2.yml
```

---

## Testing and Validation

### Automated Tests (included in deployment scripts)

Both `deploy-phase2.1.sh` and `deploy-phase2.2.sh` run automated tests:

1. ✅ Backend health check (localhost)
2. ✅ Frontend access (localhost)
3. ✅ Backend health check (network hostname)
4. ✅ Slides API (verify slides accessible)
5. ✅ Container health status

### Manual Testing Checklist

**Phase 2.1 and 2.2:**

- [ ] **Server localhost access**
  - [ ] http://localhost:8000/api/health returns 200 OK
  - [ ] http://localhost:80 serves frontend
  - [ ] http://localhost:8000/api/slides/ returns slides

- [ ] **Server network hostname access**
  - [ ] http://varun-p-01:8000/api/health returns 200 OK
  - [ ] http://varun-p-01 serves frontend

- [ ] **PC client access**
  - [ ] ping varun-p-01 succeeds
  - [ ] http://varun-p-01:8000/api/health accessible
  - [ ] http://varun-p-01 opens frontend
  - [ ] Slide list loads correctly
  - [ ] Clicking a slide opens viewer
  - [ ] Tiles load and navigation is smooth

- [ ] **Slide viewer functionality**
  - [ ] Slide opens at lowest zoom level (full overview)
  - [ ] Pan with mouse drag works
  - [ ] Zoom with scroll wheel works
  - [ ] Mini-map shows current position
  - [ ] Tiles load progressively (no errors in console)

**Phase 2.2 specific:**

- [ ] **Network share access**
  - [ ] ls /mnt/chu-slides shows slides on server
  - [ ] docker exec varuna-backend-phase2.2 ls /slides shows slides in container
  - [ ] API returns slides from network share
  - [ ] Opening slide from network share works

### Performance Testing

**Tile Loading:**
```bash
# Measure tile response time
time curl -o /dev/null -s http://varun-p-01:8000/api/slides/{slide_id}/tile/{level}/{x}/{y}/256/256

# Target: < 200ms for Phase 2.1, < 500ms for Phase 2.2
```

**Concurrent Users:**
```bash
# Use Apache Bench (install: sudo apt install apache2-utils)
ab -n 100 -c 10 http://varun-p-01:8000/api/health

# Target: 100 requests, 10 concurrent, < 1 second average
```

**Browser Developer Tools:**
- Open DevTools (F12) → Network tab
- Reload slide viewer
- Check tile loading times (should be < 500ms per tile)
- Check for errors (should be none)

---

## Troubleshooting

### Common Issues

#### 1. Cannot Access http://varun-p-01

**Symptoms:**
- Browser: "This site can't be reached"
- curl: "Could not resolve host: varun-p-01"

**Diagnosis:**
```bash
# Test DNS resolution
ping varun-p-01
nslookup varun-p-01

# Test with IP directly
ping <SERVER_IP>
curl http://<SERVER_IP>:8000/api/health
```

**Solutions:**

**Option 1: Add to hosts file (quick fix)**
```bash
# Linux/Mac: /etc/hosts
# Windows: C:\Windows\System32\drivers\etc\hosts
<SERVER_IP>  varun-p-01

# Flush DNS cache (Windows)
ipconfig /flushdns
```

**Option 2: Configure DNS server (production)**
- Add A record: varun-p-01 → <SERVER_IP>
- Verify: nslookup varun-p-01

#### 2. Firewall Blocking Ports 80 or 8000

**Symptoms:**
- ping varun-p-01 works
- curl http://varun-p-01 fails or times out

**Diagnosis:**
```bash
# Test port connectivity from client
telnet varun-p-01 80
telnet varun-p-01 8000

# Or with nc (netcat)
nc -zv varun-p-01 80
nc -zv varun-p-01 8000

# Check if ports are listening on server
sudo netstat -tulnp | grep :80
sudo netstat -tulnp | grep :8000
```

**Solutions:**

**Check Docker containers are running:**
```bash
docker ps | grep varuna
# Should see varuna-frontend-phase2.X and varuna-backend-phase2.X
```

**Check firewall rules on server:**
```bash
# Ubuntu/Debian
sudo ufw status verbose

# CentOS/RHEL
sudo firewall-cmd --list-all

# Windows Server
netsh advfirewall firewall show rule name=all
```

**Add firewall rules (if missing):**
```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw reload

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

#### 3. CORS Errors in Browser Console

**Symptoms:**
- Browser console: "Access to fetch at 'http://varun-p-01:8000/...' has been blocked by CORS policy"

**Diagnosis:**
```bash
# Check backend CORS configuration
docker exec varuna-backend-phase2.1 cat /app/.env | grep CORS_ORIGINS
# Should include: http://varun-p-01
```

**Solutions:**

**Verify CORS configuration in backend/.env.phase2.X:**
```env
CORS_ORIGINS=http://varun-p-01,http://localhost,http://localhost:5173
```

**Restart containers to apply changes:**
```bash
./Scripts/Deployment/stop-phase2.X.sh
./Scripts/Deployment/deploy-phase2.X.sh
```

#### 4. Network Share Not Accessible (Phase 2.2)

**Symptoms:**
- Backend logs: "No slides found"
- API returns empty slide list
- docker exec varuna-backend-phase2.2 ls /slides shows empty or error

**Diagnosis:**
```bash
# Check host mount
ls -la /mnt/chu-slides

# Check container mount
docker exec varuna-backend-phase2.2 ls -la /slides

# Check mount status
mount | grep chu-slides

# Test network share connectivity
ping imgsv-01-p
smbclient -L //imgsv-01-p -U USERNAME
```

**Solutions:**

**Re-mount network share:**
```bash
# Unmount if mounted
sudo umount /mnt/chu-slides

# Mount with correct credentials
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# Verify
ls -la /mnt/chu-slides
```

**Check SMB credentials:**
```bash
# Test with smbclient
smbclient //imgsv-01-p/anapath_storage_nimble -U DOMAIN\\USERNAME

# Should prompt for password and list files
```

**Check volume mount in docker-compose.phase2.2.yml:**
```yaml
volumes:
  - /mnt/chu-slides:/slides:ro  # Verify path is correct
```

**Restart containers:**
```bash
./Scripts/Deployment/stop-phase2.2.sh
./Scripts/Deployment/deploy-phase2.2.sh
```

#### 5. Slow Tile Loading (Phase 2.2)

**Symptoms:**
- Tiles take > 1 second to load
- Viewer feels sluggish
- Network share latency issues

**Diagnosis:**
```bash
# Measure network share latency
time ls /mnt/chu-slides

# Measure tile response time
time curl -o /dev/null -s http://varun-p-01:8000/api/slides/{slide_id}/tile/0/0/0/256/256

# Check backend logs for slow queries
docker logs varuna-backend-phase2.2 | grep "slow"
```

**Solutions:**

**Increase cache sizes (backend/.env.phase2.2):**
```env
MAX_TILE_CACHE_SIZE=200  # Increase from default
MAX_SLIDE_CACHE_SIZE=20
NETWORK_TIMEOUT=60
```

**Optimize SMB mount options:**
```bash
# Add cache options to mount
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,cache=strict \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# Or in /etc/fstab:
//imgsv-01-p/anapath_storage_nimble /mnt/chu-slides cifs credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,cache=strict,actimeo=60 0 0
```

**Check network bandwidth:**
```bash
# Install iperf3
sudo apt install iperf3

# Run on storage server (imgsv-01-p):
iperf3 -s

# Run on VarunaPoC server:
iperf3 -c imgsv-01-p

# Target: > 500 Mbps
```

### Log Analysis

**View container logs:**
```bash
# All logs
docker-compose -f docker-compose.phase2.X.yml logs

# Follow logs (real-time)
docker-compose -f docker-compose.phase2.X.yml logs -f

# Backend only
docker logs varuna-backend-phase2.X

# Frontend only
docker logs varuna-frontend-phase2.X

# Last 100 lines
docker logs --tail 100 varuna-backend-phase2.X
```

**Check for errors:**
```bash
# Backend errors
docker logs varuna-backend-phase2.X 2>&1 | grep -i error

# OpenSlide errors
docker logs varuna-backend-phase2.X 2>&1 | grep -i openslide

# CORS errors
docker logs varuna-backend-phase2.X 2>&1 | grep -i cors

# File access errors
docker logs varuna-backend-phase2.X 2>&1 | grep -i "no such file"
```

---

## Rollback Procedures

### Rollback to Phase 1 (localhost only)

**If Phase 2 deployment fails:**
```bash
# Stop Phase 2
./Scripts/Deployment/stop-phase2.X.sh

# Start Phase 1
./Scripts/Deployment/deploy-phase1.sh

# Verify
curl http://localhost:8000/api/health
```

### Rollback from Phase 2.2 to Phase 2.1

**If network share issues in Phase 2.2:**
```bash
# Stop Phase 2.2
./Scripts/Deployment/stop-phase2.2.sh

# Unmount network share (optional)
sudo umount /mnt/chu-slides

# Copy slides to local storage (if needed)
sudo mkdir -p /local/slides
sudo cp -r /mnt/chu-slides/* /local/slides/

# Deploy Phase 2.1
./Scripts/Deployment/deploy-phase2.1.sh
```

### Emergency Rollback

**If deployment script fails mid-deployment:**
```bash
# Stop all containers
docker-compose -f docker-compose.phase2.X.yml down

# Remove partial images (optional)
docker-compose -f docker-compose.phase2.X.yml down --rmi all

# Remove volumes (optional, caution: loses data)
docker-compose -f docker-compose.phase2.X.yml down -v

# Restart from clean state
./Scripts/Deployment/deploy-phase2.X.sh
```

---

## Maintenance

### Regular Maintenance Tasks

**Daily:**
- [ ] Check container health: `docker ps`
- [ ] Monitor disk space: `df -h`
- [ ] Check logs for errors: `docker logs varuna-backend-phase2.X | grep -i error`

**Weekly:**
- [ ] Review logs: `docker-compose -f docker-compose.phase2.X.yml logs --tail 1000`
- [ ] Check network share status (Phase 2.2): `mount | grep chu-slides`
- [ ] Test from PC client: http://varun-p-01
- [ ] Backup configuration files: `tar -czf config-backup-$(date +%F).tar.gz backend/.env* frontend/.env* docker-compose*.yml`

**Monthly:**
- [ ] Update Docker images: `docker pull python:3.11-slim && docker pull nginx:alpine`
- [ ] Rebuild containers: `./Scripts/Deployment/deploy-phase2.X.sh` (after stopping)
- [ ] Review performance metrics
- [ ] Test disaster recovery procedures

### Log Rotation

**Configure log rotation:**
```bash
# Create logrotate config
sudo nano /etc/logrotate.d/varuna

# Add:
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=10M
    missingok
    delaycompress
    copytruncate
}
```

### Backup Procedures

**Configuration backup:**
```bash
# Backup script (run weekly)
#!/bin/bash
BACKUP_DIR="/backup/varuna"
DATE=$(date +%F)

mkdir -p $BACKUP_DIR
cd /opt/VarunaPoC

tar -czf $BACKUP_DIR/varuna-config-$DATE.tar.gz \
  backend/.env* \
  frontend/.env* \
  docker-compose*.yml \
  Scripts/ \
  docs/

# Keep last 4 weeks
find $BACKUP_DIR -name "varuna-config-*.tar.gz" -mtime +28 -delete
```

**Container state backup:**
```bash
# Export container configuration (not data)
docker inspect varuna-backend-phase2.X > backend-config-backup.json
docker inspect varuna-frontend-phase2.X > frontend-config-backup.json
```

### Update Procedures

**Update VarunaPoC code:**
```bash
# Backup current configuration
./Scripts/Deployment/backup-config.sh  # Create this script

# Pull latest code
cd /opt/VarunaPoC
git pull

# Stop containers
./Scripts/Deployment/stop-phase2.X.sh

# Rebuild and restart
./Scripts/Deployment/deploy-phase2.X.sh

# Verify
curl http://varun-p-01:8000/api/health
```

**Update Docker images:**
```bash
# Pull latest base images
docker pull python:3.11-slim
docker pull nginx:alpine

# Rebuild containers (will use new base images)
./Scripts/Deployment/stop-phase2.X.sh
./Scripts/Deployment/deploy-phase2.X.sh
```

### Monitoring

**Health checks:**
```bash
# Automated health check script (run via cron)
#!/bin/bash
ENDPOINT="http://varun-p-01:8000/api/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)

if [ "$RESPONSE" != "200" ]; then
    echo "ALERT: VarunaPoC health check failed (HTTP $RESPONSE)" | mail -s "VarunaPoC Alert" admin@chu-ucl.be
    # Optionally restart containers
    # cd /opt/VarunaPoC && ./Scripts/Deployment/deploy-phase2.X.sh
fi
```

**Performance monitoring:**
```bash
# Monitor container resource usage
docker stats varuna-backend-phase2.X varuna-frontend-phase2.X

# Monitor network share latency (Phase 2.2)
time ls /mnt/chu-slides
```

---

## Additional Resources

- [Telemis Integration Guide](./TELEMIS_INTEGRATION_GUIDE.md)
- [Network Troubleshooting](./NETWORK_TROUBLESHOOTING.md)
- [API Documentation](http://varun-p-01:8000/docs)
- [Project README](../../README.md)
- [CLAUDE.md](../../CLAUDE.md)

---

**Document Version:** 2.0
**Last Updated:** 2025-12-03
**Authors:** VarunaPoC Development Team
**Contact:** [your-email@chu-ucl.be]
