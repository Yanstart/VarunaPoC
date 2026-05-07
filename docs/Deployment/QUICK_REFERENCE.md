# VarunaPoC - Quick Reference Card

**Version:** 2.0 | **Date:** 2025-12-03 | **Phase:** 2.1 and 2.2

---

## Emergency Contacts

| Issue | Contact |
|-------|---------|
| VarunaPoC Application | [your-email@chu-ucl.be] |
| Network/Firewall | CHU IT Network Team |
| Storage/Infrastructure | CHU IT Infrastructure Team |
| Telemis PACS | Telemis Support |

---

## Quick Commands

### Check Deployment Status

```bash
# Check containers
docker ps | grep varuna

# Check health
curl http://localhost:8000/api/v1/health
curl http://varun-p-01:8000/api/v1/health

# View logs
docker logs varuna-backend-phase2.X
docker logs varuna-frontend-phase2.X
```

### Deploy Phase 2.1 (Network + Local Slides)

```bash
cd /path/to/VarunaPoC
./Scripts/Deployment/deploy-phase2.1.sh
```

### Deploy Phase 2.2 (Network + CHU Infrastructure)

```bash
# 1. Mount network share
sudo mkdir -p /mnt/chu-slides
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# 2. Verify
ls -la /mnt/chu-slides

# 3. Deploy
cd /path/to/VarunaPoC
./Scripts/Deployment/deploy-phase2.2.sh
```

### Stop Deployment

```bash
./Scripts/Deployment/stop-phase2.1.sh  # Phase 2.1
./Scripts/Deployment/stop-phase2.2.sh  # Phase 2.2
```

---

## Quick Diagnostics

### From PC Client

```cmd
REM Test DNS
ping varun-p-01

REM Test ports
telnet varun-p-01 80
telnet varun-p-01 8000

REM Test API
curl http://varun-p-01:8000/api/v1/health

REM Open in browser
start http://varun-p-01
```

### From Server

```bash
# Test localhost
curl http://localhost:8000/api/v1/health

# Test network hostname
curl http://varun-p-01:8000/api/v1/health

# Check containers
docker ps

# Check firewall
sudo ufw status
sudo firewall-cmd --list-all

# Check network share (Phase 2.2)
mount | grep chu-slides
ls /mnt/chu-slides
```

---

## Common Fixes

### Cannot resolve varun-p-01

**Add to hosts file:**

**Windows:** `C:\Windows\System32\drivers\etc\hosts`
```
10.10.5.100  varun-p-01
```

**Linux:** `/etc/hosts`
```
10.10.5.100  varun-p-01
```

**Then flush DNS:**
```cmd
ipconfig /flushdns  # Windows
```

### Firewall blocking ports

**Ubuntu/Debian:**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw reload
```

**CentOS/RHEL:**
```bash
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### Network share not mounting (Phase 2.2)

```bash
# Install cifs-utils
sudo apt install cifs-utils -y

# Create credentials
sudo nano /root/.smbcredentials
# Add:
# username=USER
# password=PASS
# domain=DOMAIN

sudo chmod 600 /root/.smbcredentials

# Mount
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# Verify
ls -la /mnt/chu-slides
```

### CORS errors in browser

**Edit `backend/.env.phase2.X`:**
```env
CORS_ORIGINS=http://varun-p-01,http://localhost
```

**Restart:**
```bash
./Scripts/Deployment/stop-phase2.X.sh
./Scripts/Deployment/deploy-phase2.X.sh
```

---

## URLs and Endpoints

| Service | URL | Expected Response |
|---------|-----|-------------------|
| Frontend | http://varun-p-01 | VarunaPoC homepage |
| Backend API | http://varun-p-01:8000 | JSON with endpoints |
| Health Check | http://varun-p-01:8000/api/v1/health | {"status":"ok"} |
| API Docs | http://varun-p-01:8000/docs | Swagger UI |
| Slides List | http://varun-p-01:8000/api/slides/ | JSON array of slides |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.phase2.1.yml` | Phase 2.1 container orchestration |
| `docker-compose.phase2.2.yml` | Phase 2.2 container orchestration |
| `backend/.env.phase2.1` | Phase 2.1 backend config |
| `backend/.env.phase2.2` | Phase 2.2 backend config |
| `frontend/.env.phase2.1` | Phase 2.1 frontend config |
| `frontend/.env.phase2.2` | Phase 2.2 frontend config |

---

## Key Variables

### Phase 2.1

| Variable | Value |
|----------|-------|
| Server hostname | varun-p-01 |
| Frontend port | 80 |
| Backend port | 8000 |
| Slides path (host) | /local/slides |
| Slides path (container) | /slides |

### Phase 2.2

| Variable | Value |
|----------|-------|
| Server hostname | varun-p-01 |
| Storage server | imgsv-01-p |
| Network share | \\imgsv-01-p\anapath_storage_nimble |
| Mount point | /mnt/chu-slides |
| Frontend port | 80 |
| Backend port | 8000 |
| SMB port | 445 |

---

## Telemis Integration

**Plugin file:** `C:\Program Files\Telemis\Plugins\anapath_viewer.plugin.varuna.phase2.cfg`

**Key configuration:**
```ini
[VARUNA_VIEWER]
thirdPartySoftware = "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://varun-p-01/slide/{$study.examindex$}"
thirdPartySoftwareName = VarunaPoC - WSI Viewer
```

**Testing:**
1. Right-click slide in Telemis
2. Select "Open with VarunaPoC"
3. Chrome opens with slide

---

## Ports Reference

| Port | Service | Protocol | Direction |
|------|---------|----------|-----------|
| 80 | Frontend (HTTP) | TCP | Inbound |
| 8000 | Backend API | TCP | Inbound |
| 445 | SMB/CIFS (Phase 2.2) | TCP | Outbound |

---

## Verification Checklist

### Phase 2.1

- [ ] `ping varun-p-01` succeeds
- [ ] `telnet varun-p-01 80` connects
- [ ] `telnet varun-p-01 8000` connects
- [ ] `curl http://varun-p-01:8000/api/v1/health` returns {"status":"ok"}
- [ ] Browser: http://varun-p-01 loads frontend
- [ ] Slide list appears
- [ ] Can open and navigate a slide

### Phase 2.2

- [ ] All Phase 2.1 checks pass
- [ ] `ping imgsv-01-p` succeeds
- [ ] `mount | grep chu-slides` shows mounted share
- [ ] `ls /mnt/chu-slides` shows slides
- [ ] `docker exec varuna-backend-phase2.2 ls /slides` shows slides
- [ ] API returns slides from network share

---

## Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| Ping latency | < 10ms | < 50ms |
| Tile load time (2.1) | < 100ms | < 200ms |
| Tile load time (2.2) | < 200ms | < 500ms |
| Page load time | < 2s | < 5s |
| API response | < 100ms | < 500ms |

---

## Full Documentation

For detailed documentation, see:
- [docs/Deployment/PHASE2_NETWORK_INTEGRATION.md](./PHASE2_NETWORK_INTEGRATION.md)
- [docs/Deployment/TELEMIS_INTEGRATION_GUIDE.md](./TELEMIS_INTEGRATION_GUIDE.md)
- [docs/Deployment/NETWORK_TROUBLESHOOTING.md](./NETWORK_TROUBLESHOOTING.md)

---

**Print this card and keep it handy during on-site deployment!**
