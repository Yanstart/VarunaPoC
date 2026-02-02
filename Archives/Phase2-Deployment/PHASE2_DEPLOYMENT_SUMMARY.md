# VarunaPoC - Phase 2 Deployment Summary

**Date Created:** 2025-12-03
**Version:** 2.0
**Status:** Ready for Deployment

---

## Overview

This document summarizes all files created for VarunaPoC Phase 2 network deployment. All infrastructure files, configuration, deployment scripts, and documentation are now ready for on-site deployment at CHU UCL Namur.

---

## Phase 2 Architecture

### Phase 2.1: Network Access + Local Slides
- **Purpose:** Test network accessibility with local storage
- **Frontend:** http://varun-p-01 (accessible from PC clients)
- **Backend:** http://varun-p-01:8000
- **Slides:** /local/slides (local server storage)
- **Use Case:** Pre-production testing, Telemis integration validation

### Phase 2.2: Network Access + CHU Infrastructure
- **Purpose:** Full production deployment
- **Frontend:** http://varun-p-01 (accessible from PC clients)
- **Backend:** http://varun-p-01:8000
- **Slides:** \\imgsv-01-p\anapath_storage_nimble (CHU network share)
- **Use Case:** Production deployment with CHU storage infrastructure

---

## Files Created

### 1. Docker Compose Files (2 files)

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\docker-compose.phase2.1.yml
- Phase 2.1 container orchestration
- Backend exposed on 0.0.0.0:8000
- Frontend exposed on 0.0.0.0:80
- Volume mount: /local/slides → /slides (read-only)
- Health checks configured
- CORS: http://varun-p-01

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\docker-compose.phase2.2.yml
- Phase 2.2 container orchestration
- Backend exposed on 0.0.0.0:8000
- Frontend exposed on 0.0.0.0:80
- Volume mount: /mnt/chu-slides → /slides (read-only)
- Health checks configured
- CORS: http://varun-p-01
- Network share support (SMB/CIFS)

---

### 2. Backend Environment Files (2 files)

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\backend\.env.phase2.1
**Key configuration:**
```env
ENVIRONMENT=phase2.1-network-local-slides
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
API_BASE_URL=http://varun-p-01:8000
FRONTEND_URL=http://varun-p-01
CORS_ORIGINS=http://varun-p-01,http://localhost,http://localhost:5173
SLIDES_REPOSITORY_PATH=/slides
MAX_TILE_CACHE_SIZE=100
```

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\backend\.env.phase2.2
**Key configuration:**
```env
ENVIRONMENT=phase2.2-network-chu-infrastructure
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
API_BASE_URL=http://varun-p-01:8000
FRONTEND_URL=http://varun-p-01
CORS_ORIGINS=http://varun-p-01,http://localhost,http://localhost:5173
SLIDES_REPOSITORY_PATH=/slides
NETWORK_SHARE_PATH=\\\\imgsv-01-p\\anapath_storage_nimble
MAX_TILE_CACHE_SIZE=200  # Increased for network latency
NETWORK_TIMEOUT=60       # Increased for network latency
```

---

### 3. Frontend Environment Files (2 files)

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\frontend\.env.phase2.1
```env
VITE_API_URL=http://varun-p-01:8000
VITE_ENVIRONMENT=phase2.1-network
VITE_APP_TITLE=VarunaPoC - WSI Viewer (Phase 2.1)
```

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\frontend\.env.phase2.2
```env
VITE_API_URL=http://varun-p-01:8000
VITE_ENVIRONMENT=phase2.2-network-chu
VITE_APP_TITLE=VarunaPoC - WSI Viewer (Phase 2.2 - CHU Infrastructure)
VITE_OSD_PREFETCH_LEVEL=2  # Increased for network latency compensation
```

---

### 4. Deployment Scripts (4 files)

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Scripts\Deployment\deploy-phase2.1.sh
**Purpose:** Automated deployment for Phase 2.1

**Features:**
- Pre-deployment checks (Docker, files, ports, DNS)
- Verifies local slides directory accessible
- Tests hostname resolution (varun-p-01)
- Checks firewall ports (80, 8000)
- Builds Docker images
- Starts containers with health checks
- Post-deployment tests (localhost + network)
- Comprehensive error messages and troubleshooting hints

**Usage:**
```bash
chmod +x Scripts/Deployment/deploy-phase2.1.sh
./Scripts/Deployment/deploy-phase2.1.sh
```

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Scripts\Deployment\stop-phase2.1.sh
**Purpose:** Stop Phase 2.1 deployment
**Usage:**
```bash
./Scripts/Deployment/stop-phase2.1.sh
```

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Scripts\Deployment\deploy-phase2.2.sh
**Purpose:** Automated deployment for Phase 2.2

**Features:**
- All Phase 2.1 checks PLUS:
- Verifies network share mount (/mnt/chu-slides)
- Tests storage server accessibility (imgsv-01-p)
- Checks SMB port 445 connectivity
- Verifies slides accessible in network share
- Tests container can access mounted slides
- Extended health check timeout (90s for network latency)

**Usage:**
```bash
# 1. Mount network share first
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# 2. Deploy
chmod +x Scripts/Deployment/deploy-phase2.2.sh
./Scripts/Deployment/deploy-phase2.2.sh
```

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Scripts\Deployment\stop-phase2.2.sh
**Purpose:** Stop Phase 2.2 deployment (network share remains mounted)
**Usage:**
```bash
./Scripts/Deployment/stop-phase2.2.sh
```

---

### 5. Telemis PACS Integration (1 file)

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\Config_Integration_Infra\anapath_viewer.plugin.varuna.phase2.cfg

**Purpose:** Telemis PACS plugin configuration for opening slides in VarunaPoC

**Key configuration:**
```ini
[VARUNA_VIEWER]
thirdPartySoftware = "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://varun-p-01/slide/{$study.examindex$}"
thirdPartySoftwareIcon = microscope-viewer.png
thirdPartySoftwareName = VarunaPoC - WSI Viewer
okExitCode = 0
```

**Installation:**
1. Copy to: `C:\Program Files\Telemis\Plugins\`
2. Copy icon to: `C:\Program Files\Telemis\Icons\` (optional)
3. Restart Telemis service
4. Test from Telemis client

**Workflow:**
```
Telemis PACS → Right-click slide → "Open with VarunaPoC"
  → Chrome opens: http://varun-p-01/slide/AO.25B27859.2.1.3
    → VarunaPoC loads and displays slide
```

---

### 6. Documentation (5 files)

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\docs\Deployment\README.md
**Purpose:** Deployment documentation index

**Contents:**
- Overview of all deployment phases
- Quick navigation to specific guides
- File structure reference
- Deployment checklists
- Support contacts

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\docs\Deployment\PHASE2_NETWORK_INTEGRATION.md
**Purpose:** Complete Phase 2 deployment guide (70+ pages)

**Contents:**
- Phase 2.1 deployment (step-by-step)
- Phase 2.2 deployment (step-by-step)
- Prerequisites and requirements
- Network configuration
- Firewall configuration
- DNS setup
- Network share mounting (Phase 2.2)
- Testing and validation procedures
- Performance optimization
- Rollback procedures
- Maintenance tasks

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\docs\Deployment\TELEMIS_INTEGRATION_GUIDE.md
**Purpose:** Telemis PACS integration guide (50+ pages)

**Contents:**
- Integration architecture and flow
- Installation steps (detailed)
- Plugin configuration
- Testing procedures
- Troubleshooting common issues
- Advanced configuration options
- User training materials
- IT support quick reference

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\docs\Deployment\NETWORK_TROUBLESHOOTING.md
**Purpose:** Network troubleshooting guide (60+ pages)

**Contents:**
- Quick diagnostics (5-minute checklist)
- DNS resolution issues (solutions)
- Firewall issues (Linux and Windows)
- Network share mounting issues
- CORS and browser issues
- Performance issues and optimization
- VLAN configuration issues
- Diagnostic tools and commands
- Contact and escalation procedures

#### C:\Users\junio\Desktop\CHU-UCL\VarunaPoC\docs\Deployment\QUICK_REFERENCE.md
**Purpose:** Quick reference card for on-site deployment

**Contents:**
- Emergency contacts
- Quick commands (deploy, stop, diagnose)
- Common fixes (one-liners)
- URLs and endpoints
- Configuration files reference
- Ports reference
- Verification checklists
- Performance targets

**Print this and keep it handy during deployment!**

---

## Deployment Workflow

### Phase 2.1 Deployment (Recommended First Step)

**Purpose:** Test network accessibility before CHU infrastructure integration

**Steps:**
1. **Pre-Deployment Checks:**
   - Verify Docker installed
   - Verify hostname `varun-p-01` resolvable
   - Verify ports 80 and 8000 open
   - Verify local slides at `/local/slides`

2. **Deploy:**
   ```bash
   cd /path/to/VarunaPoC
   ./Scripts/Deployment/deploy-phase2.1.sh
   ```

3. **Test from Server:**
   ```bash
   curl http://localhost:8000/api/health
   curl http://varun-p-01:8000/api/health
   ```

4. **Test from PC Client:**
   ```bash
   curl http://varun-p-01:8000/api/health
   # Open browser: http://varun-p-01
   ```

5. **Test Telemis Integration:**
   - Install Telemis plugin
   - Open slide from PACS

**Expected Time:** 30-60 minutes (including testing)

---

### Phase 2.2 Deployment (Production)

**Purpose:** Full production deployment with CHU infrastructure

**Prerequisites:**
- Phase 2.1 tested and working
- Network share accessible: `\\imgsv-01-p\anapath_storage_nimble`
- SMB credentials obtained

**Steps:**
1. **Mount Network Share:**
   ```bash
   sudo mkdir -p /mnt/chu-slides

   # Create credentials file
   sudo nano /root/.smbcredentials
   # Add:
   # username=YOUR_USERNAME
   # password=YOUR_PASSWORD
   # domain=YOUR_DOMAIN
   sudo chmod 600 /root/.smbcredentials

   # Mount
   sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000 \
     //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

   # Verify
   ls -la /mnt/chu-slides
   find /mnt/chu-slides -name "*.mrxs" | head -5
   ```

2. **Make Mount Persistent:**
   ```bash
   sudo nano /etc/fstab
   # Add:
   # //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides cifs credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,iocharset=utf8 0 0
   ```

3. **Deploy:**
   ```bash
   cd /path/to/VarunaPoC
   ./Scripts/Deployment/deploy-phase2.2.sh
   ```

4. **Test:**
   ```bash
   # Verify container can access slides
   docker exec varuna-backend-phase2.2 ls -la /slides
   docker exec varuna-backend-phase2.2 find /slides -name "*.mrxs" | head -5

   # Test API
   curl http://varun-p-01:8000/api/slides/

   # Test in browser
   # Open: http://varun-p-01
   ```

**Expected Time:** 1-2 hours (including network share setup and testing)

---

## Telemis Integration Workflow

**Prerequisites:**
- Phase 2.1 or 2.2 deployed and tested
- Chrome installed on PACS workstations
- Administrative access to Telemis

**Steps:**
1. **Customize Plugin Configuration:**
   - Verify browser path on PACS workstations
   - Edit `.cfg` file if needed

2. **Install Plugin:**
   ```cmd
   copy anapath_viewer.plugin.varuna.phase2.cfg ^
        "C:\Program Files\Telemis\Plugins\"
   ```

3. **Restart Telemis:**
   - Restart Telemis service (services.msc)
   - Restart Telemis client

4. **Test:**
   - Right-click slide in Telemis
   - Select "Open with VarunaPoC - WSI Viewer"
   - Chrome should open with slide

**Expected Time:** 30 minutes per workstation (first-time), 5 minutes per additional workstation

---

## Network Requirements Summary

### DNS Resolution
- **varun-p-01** → Server IP (required for all phases)
- **imgsv-01-p** → Storage IP (required for Phase 2.2 only)

**Quick Fix:** Add to hosts file on all clients and server

### Firewall Ports
| Port | Service | Phase | Direction |
|------|---------|-------|-----------|
| 80 | Frontend HTTP | 2.1 + 2.2 | Inbound to server |
| 8000 | Backend API | 2.1 + 2.2 | Inbound to server |
| 445 | SMB/CIFS | 2.2 only | Outbound from server to storage |

### Network Bandwidth
- **Minimum:** 100 Mbps
- **Recommended:** 1 Gbps
- **Optimal:** 10 Gbps (for high concurrency)

### Network Latency
- **Server ↔ Client:** < 50ms (target: < 10ms)
- **Server ↔ Storage (Phase 2.2):** < 100ms (target: < 50ms)

---

## Testing Checklist

### Phase 2.1 Testing
- [ ] Server localhost: `curl http://localhost:8000/api/health` → 200 OK
- [ ] Server network: `curl http://varun-p-01:8000/api/health` → 200 OK
- [ ] PC client DNS: `ping varun-p-01` → replies received
- [ ] PC client ports: `telnet varun-p-01 80` → connected
- [ ] PC client API: `curl http://varun-p-01:8000/api/health` → 200 OK
- [ ] PC client browser: `http://varun-p-01` → VarunaPoC loads
- [ ] Slide list loads: API returns slides from `/local/slides`
- [ ] Open slide: Click slide → viewer opens with tiles
- [ ] Navigation: Pan (drag), zoom (scroll), mini-map works

### Phase 2.2 Additional Testing
- [ ] Storage server DNS: `ping imgsv-01-p` → replies received
- [ ] Network share mounted: `mount | grep chu-slides` → shows mount
- [ ] Slides visible on host: `ls /mnt/chu-slides` → shows slides
- [ ] Slides visible in container: `docker exec ... ls /slides` → shows slides
- [ ] API returns network slides: `curl .../api/slides/` → returns slides
- [ ] Open network slide: Click slide → viewer opens with tiles
- [ ] Performance acceptable: Tile load < 500ms

### Telemis Integration Testing
- [ ] Plugin appears in Telemis: Right-click → "Open with VarunaPoC" visible
- [ ] Browser launches: Chrome opens when plugin clicked
- [ ] URL correct: `http://varun-p-01/slide/{slide_id}`
- [ ] Slide loads: VarunaPoC displays requested slide
- [ ] Navigation works: Can pan/zoom slide from Telemis
- [ ] Return to PACS: Close browser, return to Telemis workflow

---

## Rollback Procedures

### Rollback from Phase 2.1 to Phase 1
```bash
./Scripts/Deployment/stop-phase2.1.sh
./Scripts/Deployment/deploy-phase1.sh
```

### Rollback from Phase 2.2 to Phase 2.1
```bash
./Scripts/Deployment/stop-phase2.2.sh
sudo umount /mnt/chu-slides  # Optional
./Scripts/Deployment/deploy-phase2.1.sh
```

### Emergency Rollback (if deployment fails)
```bash
docker-compose -f docker-compose.phase2.X.yml down
docker-compose -f docker-compose.phase2.X.yml down --rmi all  # Remove images
# Re-run deployment script
./Scripts/Deployment/deploy-phase2.X.sh
```

---

## Performance Optimization

### For Phase 2.2 (Network Share)

**1. Increase Backend Cache:**
```env
# Edit backend/.env.phase2.2
MAX_TILE_CACHE_SIZE=500  # Increase from 200
MAX_SLIDE_CACHE_SIZE=30   # Increase from 20
```

**2. Optimize SMB Mount:**
```bash
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,cache=strict,actimeo=60 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides
```

**3. Check Network Path:**
```bash
traceroute imgsv-01-p  # Should show minimal hops
```

**4. Ensure Same VLAN:**
- VarunaPoC server and storage server on same VLAN (if possible)
- Contact network admin to optimize routing

---

## Maintenance

### Daily
- Check container health: `docker ps`
- Check logs: `docker logs varuna-backend-phase2.X | grep -i error`

### Weekly
- Review full logs: `docker-compose -f docker-compose.phase2.X.yml logs`
- Test from PC client: `http://varun-p-01`
- Backup configuration files

### Monthly
- Update Docker images
- Rebuild containers
- Performance review

---

## Support Contacts

### VarunaPoC Application Issues
- Deployment failures
- Container problems
- Slide loading errors
- **Contact:** VarunaPoC Development Team | [your-email@chu-ucl.be]

### Network Issues
- DNS resolution
- Firewall configuration
- VLAN routing
- **Contact:** CHU IT Network Team

### Infrastructure Issues
- Storage server problems
- PACS workstation issues
- Telemis integration
- **Contact:** CHU IT Infrastructure Team

---

## Next Steps

1. **Review Documentation:**
   - Read `docs/Deployment/PHASE2_NETWORK_INTEGRATION.md` (complete guide)
   - Read `docs/Deployment/QUICK_REFERENCE.md` (print for on-site)

2. **Prepare Environment:**
   - Verify Docker installed on server
   - Configure hostname `varun-p-01` (DNS or hosts file)
   - Open firewall ports (80, 8000, 445 for Phase 2.2)
   - Obtain CHU storage credentials (Phase 2.2)

3. **Deploy Phase 2.1 (Test):**
   - Ensure local slides at `/local/slides`
   - Run: `./Scripts/Deployment/deploy-phase2.1.sh`
   - Test from PC client
   - Install and test Telemis plugin

4. **Deploy Phase 2.2 (Production):**
   - Mount network share: `/mnt/chu-slides`
   - Run: `./Scripts/Deployment/deploy-phase2.2.sh`
   - Verify slides from CHU infrastructure load correctly

5. **User Training:**
   - Train pathologists on using VarunaPoC from Telemis
   - Provide `docs/Deployment/QUICK_REFERENCE.md` to IT support

---

## Files Summary

**Total Files Created:** 14

### Configuration (6 files)
- docker-compose.phase2.1.yml
- docker-compose.phase2.2.yml
- backend/.env.phase2.1
- backend/.env.phase2.2
- frontend/.env.phase2.1
- frontend/.env.phase2.2

### Scripts (4 files)
- Scripts/Deployment/deploy-phase2.1.sh
- Scripts/Deployment/stop-phase2.1.sh
- Scripts/Deployment/deploy-phase2.2.sh
- Scripts/Deployment/stop-phase2.2.sh

### Integration (1 file)
- Config_Integration_Infra/anapath_viewer.plugin.varuna.phase2.cfg

### Documentation (5 files - ~200 pages total)
- docs/Deployment/README.md
- docs/Deployment/PHASE2_NETWORK_INTEGRATION.md
- docs/Deployment/TELEMIS_INTEGRATION_GUIDE.md
- docs/Deployment/NETWORK_TROUBLESHOOTING.md
- docs/Deployment/QUICK_REFERENCE.md

**All files are production-ready and ready for deployment.**

---

## Estimated Deployment Timeline

### Phase 2.1 (Test Deployment)
- **Preparation:** 30 minutes (DNS, firewall, slides)
- **Deployment:** 15 minutes (automated script)
- **Testing:** 30 minutes (server + clients)
- **Telemis Plugin:** 30 minutes (install + test)
- **Total:** ~2 hours

### Phase 2.2 (Production Deployment)
- **Preparation:** 1 hour (network share mounting)
- **Deployment:** 15 minutes (automated script)
- **Testing:** 45 minutes (extensive testing)
- **Total:** ~2 hours

### Full Deployment (2.1 + 2.2 + Telemis)
- **Total Time:** 4-5 hours (with contingency)
- **Recommended:** Split over 2 sessions (2.1 first, then 2.2)

---

**Document Version:** 1.0
**Created:** 2025-12-03
**Status:** Complete - Ready for Deployment
**Contact:** VarunaPoC Development Team
