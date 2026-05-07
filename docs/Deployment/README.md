# VarunaPoC - Deployment Documentation Index

**Version:** 2.1
**Last Updated:** 2026-05-07
**Status:** Production Ready

> **Pour le déploiement standard (compose unifié, profils Docker)**, la doc
> canonique est [`docs/Admin/`](../Admin/) — topologie réseau, matrice
> ports/rôles, profils, fiches par service.
>
> **Cette page (`Deployment/`)** garde les guides spécifiques à l'environnement
> CHU UCL Namur : phases historiques de mise en production réseau, intégration
> Telemis PACS, secrets management, breakglass, scénarios réseau hospitaliers.
> Les fichiers `docker-compose.phase{1,2.1,2.2}.yml` mentionnés ci-dessous ont
> été remplacés par le `docker-compose.yml` unifié à la racine ; les scripts
> `Scripts/Deployment/deploy-phase*.sh` et les `.env.phase*` existent toujours
> mais sont à considérer comme historiques (utiles pour comprendre la
> chronologie de l'intégration au CHU).

---

## Overview

This directory contains all deployment documentation for VarunaPoC, from local development (Phase 1) to production network deployment (Phase 2).

---

## Quick Navigation

### Getting Started
- **New to VarunaPoC?** Start with [PHASE2_NETWORK_INTEGRATION.md](./PHASE2_NETWORK_INTEGRATION.md)
- **Deploying Phase 2.1?** Jump to [Phase 2.1 Deployment Steps](#phase-21-deployment)
- **Deploying Phase 2.2?** Jump to [Phase 2.2 Deployment Steps](#phase-22-deployment)
- **Integrating with Telemis?** See [TELEMIS_INTEGRATION_GUIDE.md](./TELEMIS_INTEGRATION_GUIDE.md)
- **Network issues?** Check [NETWORK_TROUBLESHOOTING.md](./NETWORK_TROUBLESHOOTING.md)

### Quick Links
| Document | Purpose | Audience |
|----------|---------|----------|
| [PHASE2_NETWORK_INTEGRATION.md](./PHASE2_NETWORK_INTEGRATION.md) | Complete Phase 2 deployment guide | DevOps, IT |
| [TELEMIS_INTEGRATION_GUIDE.md](./TELEMIS_INTEGRATION_GUIDE.md) | Telemis PACS integration | PACS Admin, IT |
| [NETWORK_TROUBLESHOOTING.md](./NETWORK_TROUBLESHOOTING.md) | Network issues and solutions | IT Support |

---

## Deployment Phases

### Phase 1: Localhost Development (DONE ✅)

**Purpose:** Local development and testing

**Access:**
- Frontend: http://localhost
- Backend: http://localhost:8000
- Slides: `/local/slides` (local storage)

**Status:** Completed, working in production on localhost

**Files:**
- `docker-compose.phase1.yml`
- `backend/.env.phase1`
- `frontend/.env.phase1`
- `Scripts/Deployment/deploy-phase1.sh`
- `Scripts/Deployment/stop-phase1.sh`

---

### Phase 2.1: Network Access + Local Slides

**Purpose:** Network deployment with local storage (pre-production testing)

**Access:**
- Frontend: http://varun-p-01
- Backend: http://varun-p-01:8000
- Slides: `/local/slides` (local storage)

**Use Cases:**
- Test network accessibility from PACS workstations
- Validate Telemis PACS integration
- Performance baseline (no network share latency)
- Firewall and DNS configuration testing

**Requirements:**
- Server accessible via `varun-p-01` hostname
- Ports 80 and 8000 open in firewall
- Slides stored locally on server

**Files:**
- `docker-compose.phase2.1.yml`
- `backend/.env.phase2.1`
- `frontend/.env.phase2.1`
- `Scripts/Deployment/deploy-phase2.1.sh`
- `Scripts/Deployment/stop-phase2.1.sh`

**Deployment:**
```bash
cd /path/to/VarunaPoC
./Scripts/Deployment/deploy-phase2.1.sh
```

**See:** [PHASE2_NETWORK_INTEGRATION.md - Phase 2.1](./PHASE2_NETWORK_INTEGRATION.md#phase-21-network-access--local-slides)

---

### Phase 2.2: Network Access + CHU Infrastructure Slides

**Purpose:** Full production deployment with CHU storage infrastructure

**Access:**
- Frontend: http://varun-p-01
- Backend: http://varun-p-01:8000
- Slides: `\\imgsv-01-p\anapath_storage_nimble` (CHU network share)

**Use Cases:**
- Production deployment
- Access to all CHU histological slides
- Integration with existing storage infrastructure
- PACS workflow integration

**Requirements:**
- Server accessible via `varun-p-01` hostname
- Ports 80, 8000, and 445 (SMB) open in firewall
- Network share mounted: `\\imgsv-01-p\anapath_storage_nimble` → `/mnt/chu-slides`
- SMB/CIFS credentials configured

**Files:**
- `docker-compose.phase2.2.yml`
- `backend/.env.phase2.2`
- `frontend/.env.phase2.2`
- `Scripts/Deployment/deploy-phase2.2.sh`
- `Scripts/Deployment/stop-phase2.2.sh`

**Deployment:**
```bash
# 1. Mount network share FIRST
sudo mkdir -p /mnt/chu-slides
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# 2. Verify mount
ls -la /mnt/chu-slides

# 3. Deploy VarunaPoC
cd /path/to/VarunaPoC
./Scripts/Deployment/deploy-phase2.2.sh
```

**See:** [PHASE2_NETWORK_INTEGRATION.md - Phase 2.2](./PHASE2_NETWORK_INTEGRATION.md#phase-22-network-access--chu-infrastructure)

---

## Telemis PACS Integration

**Purpose:** Enable opening slides directly from Telemis PACS workstations

**Flow:**
```
Telemis PACS → Right-click on slide → "Open with VarunaPoC"
  → Chrome opens: http://varun-p-01/slide/{slide_id}
    → VarunaPoC loads slide in web viewer
```

**Requirements:**
- Phase 2.1 or 2.2 deployed and accessible
- Telemis plugin configuration file installed
- Chrome (or other browser) installed on PACS workstations

**Files:**
- `Config_Integration_Infra/anapath_viewer.plugin.varuna.phase2.cfg`

**Installation Steps:**
1. Copy `.cfg` file to: `C:\Program Files\Telemis\Plugins\`
2. Copy icon (optional) to: `C:\Program Files\Telemis\Icons\`
3. Restart Telemis service
4. Test from Telemis client

**See:** [TELEMIS_INTEGRATION_GUIDE.md](./TELEMIS_INTEGRATION_GUIDE.md)

---

## Network Troubleshooting

**Common Issues:**

| Issue | Quick Fix | See |
|-------|-----------|-----|
| Cannot resolve `varun-p-01` | Add to hosts file | [DNS Resolution](./NETWORK_TROUBLESHOOTING.md#dns-resolution-issues) |
| Ports 80/8000 blocked | Configure firewall | [Firewall Issues](./NETWORK_TROUBLESHOOTING.md#firewall-issues) |
| Network share mount fails | Check credentials, SMB version | [Network Share](./NETWORK_TROUBLESHOOTING.md#network-share-issues-phase-22) |
| CORS errors | Update backend .env CORS_ORIGINS | [CORS Issues](./NETWORK_TROUBLESHOOTING.md#cors-and-browser-issues) |
| Slow tile loading | Increase cache, optimize network | [Performance](./NETWORK_TROUBLESHOOTING.md#performance-issues) |

**See:** [NETWORK_TROUBLESHOOTING.md](./NETWORK_TROUBLESHOOTING.md)

---

## Deployment Checklist

### Phase 2.1 Deployment Checklist

**Pre-Deployment:**
- [ ] Docker and Docker Compose installed on server
- [ ] Server hostname `varun-p-01` resolvable (DNS or hosts file)
- [ ] Firewall ports 80 and 8000 open
- [ ] Local slides directory exists and populated: `/local/slides`
- [ ] Configuration files reviewed: `backend/.env.phase2.1`, `frontend/.env.phase2.1`

**Deployment:**
- [ ] Run: `./Scripts/Deployment/deploy-phase2.1.sh`
- [ ] Verify: Deployment script completes successfully
- [ ] Check: `docker ps` shows running containers

**Post-Deployment:**
- [ ] Test from server: `curl http://localhost:8000/api/v1/health`
- [ ] Test from server: `curl http://varun-p-01:8000/api/v1/health`
- [ ] Test from PC client: `curl http://varun-p-01:8000/api/v1/health`
- [ ] Test from PC client browser: `http://varun-p-01`
- [ ] Verify slide list loads
- [ ] Open a slide and verify navigation works

### Phase 2.2 Deployment Checklist

**Pre-Deployment:**
- [ ] All Phase 2.1 pre-deployment checks
- [ ] Storage server `imgsv-01-p` resolvable and accessible
- [ ] SMB/CIFS credentials obtained
- [ ] Network share mount point created: `/mnt/chu-slides`
- [ ] Network share mounted successfully
- [ ] Slides visible in mount: `ls /mnt/chu-slides`
- [ ] Port 445 (SMB) accessible to storage server

**Deployment:**
- [ ] Verify network share: `ls -la /mnt/chu-slides`
- [ ] Count slides: `find /mnt/chu-slides -name "*.mrxs" | wc -l`
- [ ] Run: `./Scripts/Deployment/deploy-phase2.2.sh`
- [ ] Verify: Deployment script completes successfully
- [ ] Check: `docker ps` shows running containers

**Post-Deployment:**
- [ ] All Phase 2.1 post-deployment tests
- [ ] Verify container can access slides: `docker exec varuna-backend-phase2.2 ls /slides`
- [ ] Verify API returns slides from network share
- [ ] Test opening slide from network share

### Telemis Integration Checklist

**Installation:**
- [ ] Phase 2.1 or 2.2 deployed and tested
- [ ] Plugin configuration file customized: `anapath_viewer.plugin.varuna.phase2.cfg`
- [ ] Browser path verified on PACS workstations
- [ ] Plugin .cfg copied to: `C:\Program Files\Telemis\Plugins\`
- [ ] Icon copied to: `C:\Program Files\Telemis\Icons\` (optional)
- [ ] Telemis service restarted
- [ ] Telemis client restarted

**Testing:**
- [ ] Plugin appears in Telemis UI: "Open with VarunaPoC"
- [ ] Clicking plugin opens browser
- [ ] Browser URL correct: `http://varun-p-01/slide/{slide_id}`
- [ ] VarunaPoC loads slide successfully
- [ ] Navigation works (pan, zoom, mini-map)
- [ ] Test from multiple PACS workstations

---

## File Structure Reference

```
VarunaPoC/
├── docker-compose.phase1.yml        ← Phase 1 (localhost)
├── docker-compose.phase2.1.yml      ← Phase 2.1 (network + local)
├── docker-compose.phase2.2.yml      ← Phase 2.2 (network + CHU infra)
│
├── backend/
│   ├── .env.phase1                  ← Phase 1 backend config
│   ├── .env.phase2.1                ← Phase 2.1 backend config
│   └── .env.phase2.2                ← Phase 2.2 backend config
│
├── frontend/
│   ├── .env.phase1                  ← Phase 1 frontend config
│   ├── .env.phase2.1                ← Phase 2.1 frontend config
│   └── .env.phase2.2                ← Phase 2.2 frontend config
│
├── Scripts/
│   └── Deployment/
│       ├── deploy-phase1.sh         ← Deploy Phase 1
│       ├── stop-phase1.sh           ← Stop Phase 1
│       ├── deploy-phase2.1.sh       ← Deploy Phase 2.1
│       ├── stop-phase2.1.sh         ← Stop Phase 2.1
│       ├── deploy-phase2.2.sh       ← Deploy Phase 2.2
│       └── stop-phase2.2.sh         ← Stop Phase 2.2
│
├── Config_Integration_Infra/
│   └── anapath_viewer.plugin.varuna.phase2.cfg  ← Telemis plugin
│
└── docs/
    └── Deployment/
        ├── README.md                            ← This file
        ├── PHASE2_NETWORK_INTEGRATION.md        ← Complete Phase 2 guide
        ├── TELEMIS_INTEGRATION_GUIDE.md         ← Telemis integration
        └── NETWORK_TROUBLESHOOTING.md           ← Network troubleshooting
```

---

## Support and Contact

### For Deployment Issues

**VarunaPoC Application:**
- Container problems
- Slide loading issues
- API errors
- Contact: VarunaPoC Development Team

**Network Issues:**
- DNS resolution
- Firewall configuration
- VLAN routing
- Contact: CHU IT Network Team

**Infrastructure Issues:**
- Storage server
- PACS workstations
- Telemis integration
- Contact: CHU IT Infrastructure Team

### Documentation Updates

If you find errors or have suggestions for improving this documentation:

1. Document the issue/suggestion
2. Contact: VarunaPoC Development Team
3. Or: Create issue in repository (if applicable)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2025-12-03 | Phase 2 documentation complete (2.1 and 2.2) |
| 1.5 | 2025-11-20 | Added Telemis integration guide |
| 1.0 | 2025-11-01 | Initial Phase 1 documentation |

---

## Additional Resources

### Internal Documentation
- [Main Project README](../../README.md)
- [CLAUDE.md](../../CLAUDE.md) - Development guidelines
- [User Manual](../Manuel/README.md) - End-user documentation
- [Error Documentation](../README.md) - Known issues and workarounds

### External Documentation
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [OpenSlide Documentation](https://openslide.org/)
- [OpenSeadragon Documentation](https://openseadragon.github.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Document Version:** 2.0
**Last Updated:** 2025-12-03
**Authors:** VarunaPoC Development Team
**Contact:** [your-email@chu-ucl.be]
