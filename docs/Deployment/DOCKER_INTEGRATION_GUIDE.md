# Docker Integration Guide for VarunaPoC

This guide explains how to integrate the Docker infrastructure with your existing codebase.

## Overview

The Docker infrastructure has been created for **Phase 1 local validation**. All files are ready to use, but you need to make one small change to the backend code to support both Windows development and Docker deployment.

## Files Created

### Docker Configuration
- `docker-compose.phase1.yml` - Main orchestration file
- `backend/Dockerfile` - Backend container definition
- `backend/.dockerignore` - Files to exclude from backend build
- `backend/.env.phase1` - Backend environment variables
- `backend/config_openslide_auto.py` - **NEW** Auto-detection for OpenSlide
- `frontend/Dockerfile` - Frontend multi-stage build
- `frontend/nginx.conf` - Nginx web server configuration
- `frontend/.dockerignore` - Files to exclude from frontend build
- `frontend/.env.phase1` - Frontend environment variables

### Deployment Scripts
- `Scripts/Deployment/deploy-phase1.sh` - Automated deployment script
- `Scripts/Deployment/stop-phase1.sh` - Clean shutdown script
- `Scripts/Deployment/README.md` - Complete deployment documentation

## Required Code Change

### Backend: Update OpenSlide Configuration Import

**File:** `backend/main.py`

**Current code (line 21-22):**
```python
# IMPORTANT: Configure OpenSlide DLL path AVANT tout import
# (Nécessaire sur Windows pour trouver libopenslide-0.dll)
import config_openslide
```

**Change to:**
```python
# IMPORTANT: Configure OpenSlide DLL path AVANT tout import
# Auto-detects Windows (MSYS2) vs Docker (apt packages)
import config_openslide_auto
```

**Why this change?**
- `config_openslide.py` is hardcoded for Windows MSYS2 paths
- `config_openslide_auto.py` auto-detects environment (Windows/Docker/Linux)
- Uses `DOCKER_CONTAINER` env var (set in Dockerfile) to determine context
- Windows development: uses `C:\msys64\ucrt64\bin`
- Docker deployment: uses system packages from apt-get
- No other code changes needed!

### Alternative: Keep Both Files

If you prefer not to modify main.py yet, you can:

1. Keep `import config_openslide` for local Windows development
2. Before deploying to Docker, manually change to `import config_openslide_auto`
3. Or use environment-based conditional import:

```python
import os
if os.environ.get('DOCKER_CONTAINER') == 'true':
    import config_openslide_auto
else:
    import config_openslide
```

## How It Works

### Development Workflow (Windows)

```bash
# 1. Normal development (no Docker)
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Uses config_openslide.py (MSYS2 paths)
```

### Deployment Workflow (Docker)

```bash
# 1. Deploy to Docker
./Scripts/Deployment/deploy-phase1.sh

# Backend Dockerfile installs OpenSlide via apt-get:
# - libopenslide0 (runtime library)
# - openslide-tools (command-line tools)

# Backend uses config_openslide_auto.py which detects Docker
# - Checks DOCKER_CONTAINER=true env var
# - Uses system library paths (/usr/lib/*)

# 2. Access application
# Frontend: http://localhost
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs

# 3. Stop when done
./Scripts/Deployment/stop-phase1.sh
```

## Configuration Files Explained

### `docker-compose.phase1.yml`

Defines two services:

**Backend Service:**
- Builds from `./backend/Dockerfile`
- Exposes port 8000
- Mounts `/local/slides` as `/slides` (read-only)
- Uses environment variables from `backend/.env.phase1`
- Health check: `GET /api/v1/health` (retries 5 times)

**Frontend Service:**
- Builds from `./frontend/Dockerfile` (multi-stage: Node build + Nginx serve)
- Exposes port 80
- Depends on backend (waits for backend to be healthy)
- Uses environment variables from `frontend/.env.phase1`
- Health check: `GET /` (retries 3 times)

### `backend/Dockerfile`

**Base Image:** `python:3.11-slim`

**System Dependencies:**
- `openslide-tools` - OpenSlide command-line utilities
- `libopenslide0` - OpenSlide runtime library
- `curl` - For health checks

**Python Dependencies:**
- Installs from `requirements.txt`
- Uses `--no-cache-dir` to minimize image size

**Security:**
- Creates non-root user `varuna` (UID 1000)
- Runs application as `varuna` (not root)

**Startup:**
- Command: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`
- `--host 0.0.0.0` required for Docker (listens on all interfaces)

### `frontend/Dockerfile`

**Multi-stage build:**

**Stage 1: Builder**
- Base: `node:20-alpine`
- Installs npm dependencies: `npm ci --only=production`
- Builds Vite for production: `npm run build`
- Output: `dist/` directory with static files

**Stage 2: Nginx**
- Base: `nginx:alpine`
- Copies `dist/` from builder stage
- Copies custom `nginx.conf`
- Installs `curl` for health checks
- Serves static files on port 80

### Environment Variables

**Backend (`.env.phase1`):**
- `SLIDES_REPOSITORY_PATH=/slides` - Path inside container (mapped from `/local/slides`)
- `API_BASE_URL=http://localhost:8000` - Backend's own URL
- `FRONTEND_URL=http://localhost` - Frontend URL (for CORS)
- `ENVIRONMENT=phase1-local` - Deployment phase identifier
- `LOG_LEVEL=DEBUG` - Verbose logging for testing
- `CORS_ORIGINS=http://localhost,http://localhost:80` - Allowed origins

**Frontend (`.env.phase1`):**
- `VITE_API_URL=http://localhost:8000` - Backend API URL (accessed from browser)
- `VITE_ENVIRONMENT=phase1-local` - Environment identifier

## Prerequisites for Deployment

### 1. Docker Installation

**Windows:**
```powershell
# Install Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Verify installation
docker --version
docker-compose --version
```

**Linux:**
```bash
# Install Docker Engine
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

### 2. Slides Directory

**Create and populate:**
```bash
# Create directory
sudo mkdir -p /local/slides

# Set permissions (Linux)
sudo chown -R $USER:docker /local/slides

# Windows: Create C:\local\slides and share in Docker Desktop settings
# Docker Desktop -> Settings -> Resources -> File Sharing -> Add C:\local\slides

# Copy test slides
cp /path/to/test/slides/*.mrxs /local/slides/
cp -r /path/to/test/slides/*/ /local/slides/  # Companion directories
```

**Required structure for .mrxs files:**
```
/local/slides/
├── sample1.mrxs                  ← Main file
├── sample1/                      ← Companion directory (REQUIRED)
│   ├── Slidedat.ini
│   ├── Data0000.dat
│   ├── Data0001.dat
│   └── Index.dat
├── sample2.bif                   ← BIF file (single file)
└── sample3.tif                   ← TIFF file (single file)
```

## Deployment Steps

### First-Time Deployment

```bash
# 1. Navigate to project root
cd C:/Users/junio/Desktop/CHU-UCL/VarunaPoC

# 2. Update main.py (see "Required Code Change" above)
# Change: import config_openslide
# To: import config_openslide_auto

# 3. Ensure slides directory exists
ls /local/slides  # Should show .mrxs, .bif, or .tif files

# 4. Run deployment script
./Scripts/Deployment/deploy-phase1.sh

# Script will:
# - Validate Docker and slides directory
# - Build images (2-3 minutes first time)
# - Start containers
# - Wait for health checks
# - Run smoke tests
# - Display access URLs

# 5. Access application
# Open browser: http://localhost
```

### Subsequent Deployments

```bash
# After making code changes:

# 1. Stop running containers
./Scripts/Deployment/stop-phase1.sh

# 2. Make your code changes in backend/ or frontend/

# 3. Rebuild and redeploy
./Scripts/Deployment/deploy-phase1.sh

# Docker layer caching makes rebuilds faster (30s instead of 3min)
```

### Clean Shutdown

```bash
# Stop containers only (keeps images for next deployment)
./Scripts/Deployment/stop-phase1.sh

# Stop and remove images (full cleanup)
./Scripts/Deployment/stop-phase1.sh --clean

# Nuclear option (removes volumes too)
./Scripts/Deployment/stop-phase1.sh --clean --volumes
```

## Testing Workflow

### 1. Verify Backend

```bash
# Check backend health
curl http://localhost:8000/api/v1/health
# Expected: {"status":"healthy"}

# Check backend root
curl http://localhost:8000/
# Expected: {"service":"VarunaPoC Backend","status":"running",...}

# Check API docs
open http://localhost:8000/docs
# Expected: Swagger UI with all endpoints
```

### 2. Verify Frontend

```bash
# Check frontend loads
curl http://localhost/
# Expected: HTML with <title>VarunaPoC</title>

# Open in browser
open http://localhost
# Expected: Slide viewer interface
```

### 3. Verify Slide Detection

```bash
# Test slide browsing API
curl http://localhost:8000/api/slides/browse?path=/
# Expected: JSON with folders and detected slides

# Or use frontend:
# 1. Open http://localhost
# 2. Browse folders
# 3. Click on a slide
# 4. Should open in viewer
```

### 4. Check Logs

```bash
# All logs (both services)
docker-compose -f docker-compose.phase1.yml logs -f

# Backend logs only
docker-compose -f docker-compose.phase1.yml logs -f backend

# Frontend logs only
docker-compose -f docker-compose.phase1.yml logs -f frontend

# Last 50 lines
docker-compose -f docker-compose.phase1.yml logs --tail=50 backend
```

## Troubleshooting

### Backend Issues

**Problem:** "OpenSlide library not found"
**Solution:** Rebuild backend image (OpenSlide installation may have failed)
```bash
docker-compose -f docker-compose.phase1.yml build --no-cache backend
docker-compose -f docker-compose.phase1.yml up -d backend
```

**Problem:** "No slides found"
**Solution:** Check volume mount
```bash
# Verify volume is mounted
docker exec -it varuna-backend-phase1 ls -la /slides

# Should show contents of /local/slides
# If empty, check that /local/slides has files
ls -la /local/slides
```

**Problem:** "CORS error in browser"
**Solution:** Check CORS_ORIGINS in backend/.env.phase1
```bash
# Should include both:
CORS_ORIGINS=http://localhost,http://localhost:80

# Restart backend after change:
docker-compose -f docker-compose.phase1.yml restart backend
```

### Frontend Issues

**Problem:** "Vite build failed"
**Solution:** Check npm dependencies
```bash
# Rebuild with verbose output
docker-compose -f docker-compose.phase1.yml build --no-cache --progress=plain frontend
```

**Problem:** "API_URL undefined in frontend"
**Solution:** Check .env.phase1 is loaded
```bash
# Verify VITE_API_URL is set during build
# Check frontend Dockerfile ARG and ENV
cat frontend/.env.phase1
```

**Problem:** "Cannot connect to backend from frontend"
**Solution:** Check network connectivity
```bash
# Verify both containers are on same network
docker network inspect varuna-phase1-network

# Should show both containers listed
```

### General Issues

**Problem:** "Port already in use"
**Solution:** Find and stop conflicting process
```bash
# Linux/Mac: Find process on port 80
sudo lsof -i :80

# Windows: Find process on port 80
netstat -ano | findstr :80

# Kill process or change port in docker-compose.phase1.yml
```

**Problem:** "Permission denied"
**Solution:** Fix Docker permissions (Linux)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Fix slides directory permissions
sudo chown -R $USER:docker /local/slides
chmod -R 755 /local/slides
```

## Next Steps

After successful Phase 1 validation:

1. **Document findings** in deployment notes
2. **Test with real slides** from CHU servers
3. **Performance testing** (load times, memory usage)
4. **Plan Phase 2** (external access, HTTPS, authentication)

## Phase 2 Roadmap

Phase 2 will add:
- External access (not just localhost)
- HTTPS with SSL certificates (Let's Encrypt)
- Reverse proxy (Traefik or Nginx Proxy Manager)
- Authentication/authorization
- Production logging (ELK stack or similar)
- Monitoring (Prometheus + Grafana)
- Backup and recovery
- CI/CD pipeline

---

**Version:** 1.0
**Last Updated:** 2025-12-03
**Status:** Ready for Phase 1 deployment
**Maintainer:** VarunaPoC Development Team
