# Docker Phase 1 Deployment Checklist

Quick reference checklist for deploying VarunaPoC Phase 1 at CHU on-site.

## Pre-Deployment (At Home - BEFORE Going to CHU)

### Code Preparation
- [ ] Update `backend/main.py` line 22: Change `import config_openslide` to `import config_openslide_auto`
- [ ] Commit all changes to git
- [ ] Test locally if possible (optional)
- [ ] Push to repository (so you can pull on CHU server)

### Docker Files Verification
- [ ] `docker-compose.phase1.yml` exists in project root
- [ ] `backend/Dockerfile` exists
- [ ] `backend/.env.phase1` exists
- [ ] `frontend/Dockerfile` exists
- [ ] `frontend/nginx.conf` exists
- [ ] `frontend/.env.phase1` exists
- [ ] `Scripts/Deployment/deploy-phase1.sh` is executable
- [ ] `Scripts/Deployment/stop-phase1.sh` is executable

### Documentation
- [ ] Read `DOCKER_INTEGRATION_GUIDE.md` thoroughly
- [ ] Read `Scripts/Deployment/README.md`
- [ ] Understand troubleshooting steps

## On-Site Deployment (At CHU - Limited Time!)

### Environment Setup (5 minutes)
- [ ] Docker is installed and running: `docker info`
- [ ] Slides directory exists: `ls /local/slides`
- [ ] Slides directory has test files: `ls /local/slides/*.mrxs`
- [ ] Git repo is up-to-date: `git pull`

### Deployment (3-5 minutes)
- [ ] Navigate to project: `cd VarunaPoC`
- [ ] Run deploy script: `./Scripts/Deployment/deploy-phase1.sh`
- [ ] Wait for "Deployment Successful!" message
- [ ] Note any errors (check logs if needed)

### Validation (5 minutes)
- [ ] Frontend loads: Open `http://localhost` in browser
- [ ] Backend responds: `curl http://localhost:8000/api/health`
- [ ] API docs load: Open `http://localhost:8000/docs`
- [ ] Slides detected: Check frontend file browser
- [ ] Can open a slide: Click on a .mrxs file
- [ ] Viewer works: Pan, zoom, minimap visible

### Testing (10-15 minutes)
- [ ] Test with different slide formats (.mrxs, .bif, .tif)
- [ ] Test navigation (breadcrumb, folder browsing)
- [ ] Test zoom levels (check all pyramid levels)
- [ ] Check performance (tile loading speed)
- [ ] Look for errors in browser console (F12)
- [ ] Check backend logs: `docker-compose -f docker-compose.phase1.yml logs backend`

### Documentation (5 minutes)
- [ ] Take screenshots of working application
- [ ] Note any issues encountered
- [ ] Record performance metrics (if time allows)
- [ ] List slides tested successfully
- [ ] Document any workarounds needed

### Clean Shutdown
- [ ] Stop containers: `./Scripts/Deployment/stop-phase1.sh`
- [ ] Verify stopped: `docker ps` (should show no varuna containers)
- [ ] (Optional) Remove images: `./Scripts/Deployment/stop-phase1.sh --clean`

## Emergency Troubleshooting Commands

### If deployment script fails:
```bash
# Check Docker daemon
docker info

# Check if containers already running
docker ps -a | grep varuna

# Stop any existing containers
docker stop varuna-backend-phase1 varuna-frontend-phase1
docker rm varuna-backend-phase1 varuna-frontend-phase1

# Remove old images if corrupted
docker rmi varunapoc-backend varunapoc-frontend

# Try deployment again
./Scripts/Deployment/deploy-phase1.sh
```

### If backend fails:
```bash
# Check backend logs
docker-compose -f docker-compose.phase1.yml logs backend

# Common issues:
# - OpenSlide not installed: Rebuild with --no-cache
# - Port 8000 in use: netstat -ano | findstr :8000
# - Volume not mounted: docker exec -it varuna-backend-phase1 ls /slides
```

### If frontend fails:
```bash
# Check frontend logs
docker-compose -f docker-compose.phase1.yml logs frontend

# Common issues:
# - Vite build failed: Check package.json dependencies
# - Port 80 in use: Stop IIS or Apache first
# - Cannot reach backend: Check VITE_API_URL in .env.phase1
```

### Nuclear option (if everything is broken):
```bash
# Stop everything
docker-compose -f docker-compose.phase1.yml down -v

# Remove all VarunaPoC images
docker rmi $(docker images -q varunapoc*)

# Clean Docker system (careful!)
docker system prune -a

# Start fresh
./Scripts/Deployment/deploy-phase1.sh
```

## Success Criteria

Phase 1 is successful if:
- ✅ Both containers start and stay healthy
- ✅ Frontend loads in browser
- ✅ API documentation is accessible
- ✅ At least one slide is detected and opens
- ✅ Viewer allows pan, zoom, and navigation
- ✅ No critical errors in logs

## What to Bring Back (Post-Deployment)

### Required:
- Deployment logs (success or failure)
- Screenshots of working application
- List of tested slide formats
- Any error messages encountered

### Optional:
- Performance metrics (tile load times)
- Docker resource usage (RAM, CPU)
- Notes on CHU network configuration
- Ideas for Phase 2 improvements

## Time Budget

**Total on-site time: ~30-45 minutes**
- Environment setup: 5 min
- Deployment: 3-5 min
- Validation: 5 min
- Testing: 10-15 min
- Documentation: 5 min
- Troubleshooting buffer: 5-10 min

**If you have more time:**
- Test edge cases (very large slides)
- Test concurrent access (multiple browsers)
- Benchmark performance
- Explore monitoring options

**If you're running out of time:**
- Focus on validation checklist only
- Take screenshots of working state
- Get logs: `docker-compose logs > deployment.log`
- Clean shutdown and leave

## Contact Info (If Needed)

**Docker Support:**
- Docker Desktop Issues: https://docs.docker.com/desktop/troubleshoot/
- Docker Compose: https://docs.docker.com/compose/

**VarunaPoC Docs:**
- `DOCKER_INTEGRATION_GUIDE.md` (comprehensive guide)
- `Scripts/Deployment/README.md` (deployment reference)
- `docs/Manuel/` (user manual)

---

**Good Luck! You've got this!** 🚀

Everything is prepared. Just run the deploy script and validate. If something breaks, check logs and troubleshooting steps. You have all the tools you need.
