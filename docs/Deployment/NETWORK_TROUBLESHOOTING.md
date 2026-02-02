# VarunaPoC - Network Troubleshooting Guide

**Version:** 2.0
**Last Updated:** 2025-12-03
**Status:** Production Ready
**Phase:** 2.1 and 2.2 Network Deployment

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Diagnostics](#quick-diagnostics)
3. [DNS Resolution Issues](#dns-resolution-issues)
4. [Firewall Issues](#firewall-issues)
5. [Network Share Issues (Phase 2.2)](#network-share-issues-phase-22)
6. [CORS and Browser Issues](#cors-and-browser-issues)
7. [Performance Issues](#performance-issues)
8. [VLAN Configuration Issues](#vlan-configuration-issues)
9. [Diagnostic Tools](#diagnostic-tools)
10. [Contact and Escalation](#contact-and-escalation)

---

## Overview

This guide covers network-related troubleshooting for VarunaPoC Phase 2 deployments. Use this guide when:

- PC clients cannot access http://varun-p-01
- Network share mounting fails (Phase 2.2)
- Slow tile loading or timeouts
- CORS errors in browser console
- Firewall blocking connections

---

## Quick Diagnostics

### 5-Minute Diagnostic Checklist

Run these commands to quickly identify the problem area:

**From PC Client (PACS Workstation):**
```cmd
REM 1. Test hostname resolution
ping varun-p-01

REM 2. Test TCP connectivity (ports 80 and 8000)
telnet varun-p-01 80
telnet varun-p-01 8000

REM 3. Test HTTP access
curl http://varun-p-01:8000/api/health

REM 4. Test in browser
start http://varun-p-01
```

**From VarunaPoC Server:**
```bash
# 1. Check containers running
docker ps | grep varuna

# 2. Check services listening on network interfaces
sudo netstat -tulnp | grep :80
sudo netstat -tulnp | grep :8000

# 3. Test localhost access
curl http://localhost:8000/api/health

# 4. Test network hostname access
curl http://varun-p-01:8000/api/health

# 5. Check firewall status
sudo ufw status  # Ubuntu/Debian
sudo firewall-cmd --list-all  # CentOS/RHEL
```

### Interpret Results

| Test | Success | Failure Indicates |
|------|---------|-------------------|
| `ping varun-p-01` | Replies received | DNS resolution issue |
| `telnet varun-p-01 80` | Connected | Firewall blocking port |
| `curl ...api/health` | {"status":"ok"} | Backend not running |
| Browser access | Page loads | Browser/CORS issue |

---

## DNS Resolution Issues

### Problem: Cannot Resolve Hostname varun-p-01

**Symptoms:**
```cmd
C:\> ping varun-p-01
Ping request could not find host varun-p-01. Please check the name and try again.
```

**Diagnosis:**
```cmd
REM Check if hostname resolves to IP
nslookup varun-p-01

REM Check with IP directly
ping <SERVER_IP>
```

### Solution 1: Add to Hosts File (Quick Fix)

**On PC Client (PACS Workstation):**

**Windows:**
```cmd
REM Open Notepad as Administrator
notepad C:\Windows\System32\drivers\etc\hosts

REM Add line (replace <SERVER_IP> with actual IP):
<SERVER_IP>  varun-p-01

REM Example:
10.10.5.100  varun-p-01

REM Save and close

REM Flush DNS cache
ipconfig /flushdns

REM Test
ping varun-p-01
```

**Linux:**
```bash
# Open hosts file as root
sudo nano /etc/hosts

# Add line:
<SERVER_IP>  varun-p-01

# Save (Ctrl+O, Enter, Ctrl+X)

# Test
ping varun-p-01
```

**Important:** Add this entry to **ALL PC clients** that need to access VarunaPoC.

### Solution 2: Configure DNS Server (Production)

**On DNS Server (Windows Server):**

1. Open DNS Manager: `Start → Administrative Tools → DNS`
2. Expand server → Forward Lookup Zones → Select your domain
3. Right-click → New Host (A or AAAA)
4. Name: `varun-p-01`
5. IP address: `<SERVER_IP>`
6. Click "Add Host"
7. Test from client: `nslookup varun-p-01`

**On DNS Server (Linux - BIND):**
```bash
# Edit zone file
sudo nano /etc/bind/zones/db.yourdomain.com

# Add A record:
varun-p-01    IN    A    <SERVER_IP>

# Reload BIND
sudo systemctl reload bind9

# Test
nslookup varun-p-01
```

### Solution 3: Configure Server Hostname

**On VarunaPoC Server:**
```bash
# Set hostname
sudo hostnamectl set-hostname varun-p-01

# Verify
hostname

# Add to /etc/hosts
sudo nano /etc/hosts
# Add:
127.0.0.1  varun-p-01
<SERVER_IP>  varun-p-01

# Test
ping varun-p-01
```

### Verification

**After applying solution:**
```cmd
REM 1. Test hostname resolution
ping varun-p-01

REM 2. Test reverse lookup
nslookup <SERVER_IP>
REM Should return: varun-p-01

REM 3. Test from multiple clients
REM Run ping varun-p-01 from different workstations
```

---

## Firewall Issues

### Problem: Ports 80 or 8000 Blocked

**Symptoms:**
```cmd
C:\> telnet varun-p-01 80
Connecting To varun-p-01...Could not open connection to the host, on port 80: Connect failed

C:\> curl http://varun-p-01:8000/api/health
Failed to connect to varun-p-01 port 8000: Timed out
```

**But ping works:**
```cmd
C:\> ping varun-p-01
Reply from 10.10.5.100: bytes=32 time=1ms TTL=64
```

**Diagnosis:**
```bash
# On VarunaPoC server, check if services listening
sudo netstat -tulnp | grep :80
# Should show: tcp 0.0.0.0:80 LISTEN

sudo netstat -tulnp | grep :8000
# Should show: tcp 0.0.0.0:8000 LISTEN

# Check Docker containers
docker ps | grep varuna
# Should show containers with ports 0.0.0.0:80->80 and 0.0.0.0:8000->8000
```

If services are listening but client cannot connect → **Firewall issue**

### Solution 1: Configure Server Firewall (Linux)

**Ubuntu/Debian (UFW):**
```bash
# Check firewall status
sudo ufw status verbose

# Allow ports 80 and 8000
sudo ufw allow 80/tcp comment 'VarunaPoC Frontend'
sudo ufw allow 8000/tcp comment 'VarunaPoC Backend API'

# Reload firewall
sudo ufw reload

# Verify rules
sudo ufw status numbered
```

**CentOS/RHEL (firewalld):**
```bash
# Check firewall status
sudo firewall-cmd --state
sudo firewall-cmd --list-all

# Allow ports 80 and 8000
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp

# Or use predefined service (for port 80)
sudo firewall-cmd --permanent --add-service=http

# Reload firewall
sudo firewall-cmd --reload

# Verify rules
sudo firewall-cmd --list-ports
sudo firewall-cmd --list-services
```

**iptables (if UFW/firewalld not used):**
```bash
# Check current rules
sudo iptables -L -n -v

# Allow ports 80 and 8000
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# Save rules (Ubuntu/Debian)
sudo netfilter-persistent save

# Save rules (CentOS/RHEL)
sudo service iptables save
```

### Solution 2: Configure Server Firewall (Windows Server)

**Windows Firewall:**
```cmd
REM Open Command Prompt as Administrator

REM Add rule for port 80
netsh advfirewall firewall add rule name="VarunaPoC Frontend (HTTP)" dir=in action=allow protocol=TCP localport=80

REM Add rule for port 8000
netsh advfirewall firewall add rule="VarunaPoC Backend API" dir=in action=allow protocol=TCP localport=8000

REM Verify rules
netsh advfirewall firewall show rule name=all | findstr VarunaPoC
```

**Windows Firewall GUI:**
1. Open: `Control Panel → System and Security → Windows Defender Firewall → Advanced settings`
2. Click "Inbound Rules"
3. Click "New Rule..."
4. Rule Type: Port → Next
5. Protocol: TCP, Specific local ports: 80,8000 → Next
6. Action: Allow the connection → Next
7. Profile: Check all (Domain, Private, Public) → Next
8. Name: VarunaPoC Ports → Finish

### Solution 3: Check Network Firewall (VLAN/Router)

If server firewall is configured but clients still cannot connect:

**Check intermediate network devices:**
- Hospital network firewall
- VLAN ACLs
- Router filtering
- Proxy servers

**Contact network administrator:**
- Provide server IP: `<SERVER_IP>`
- Ports required: 80 (TCP) and 8000 (TCP)
- Source: PACS workstation VLAN
- Destination: VarunaPoC server

### Solution 4: Disable Firewall (Temporary Testing Only)

**CAUTION:** Only for testing. DO NOT leave firewall disabled in production.

**Ubuntu/Debian:**
```bash
sudo ufw disable
# Test connectivity
# Re-enable after testing:
sudo ufw enable
```

**CentOS/RHEL:**
```bash
sudo systemctl stop firewalld
# Test connectivity
# Re-enable after testing:
sudo systemctl start firewalld
```

**Windows Server:**
```cmd
REM Disable firewall (GUI)
REM Control Panel → Windows Defender Firewall → Turn Windows Defender Firewall on or off
REM Select "Turn off" for all profiles
REM Test connectivity
REM Re-enable after testing
```

### Verification

**After applying solution:**
```bash
# From PC client
telnet varun-p-01 80
# Should connect (press Ctrl+], then type quit)

telnet varun-p-01 8000
# Should connect

curl http://varun-p-01:8000/api/health
# Should return: {"status":"ok"}

# Test in browser
http://varun-p-01
```

---

## Network Share Issues (Phase 2.2)

### Problem: Cannot Mount Network Share

**Symptoms:**
```bash
$ sudo mount -t cifs //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides
mount error(13): Permission denied
```

Or:
```bash
$ ls /mnt/chu-slides
ls: cannot access '/mnt/chu-slides': No such file or directory
```

**Diagnosis:**
```bash
# 1. Test storage server connectivity
ping imgsv-01-p

# 2. Test SMB connectivity (port 445)
telnet imgsv-01-p 445
# Or:
nc -zv imgsv-01-p 445

# 3. List available shares (requires smbclient)
smbclient -L //imgsv-01-p -U USERNAME
# Should list: anapath_storage_nimble

# 4. Test credentials
smbclient //imgsv-01-p/anapath_storage_nimble -U DOMAIN\\USERNAME
# Should prompt for password and connect
```

### Solution 1: Check Storage Server Accessibility

**Test storage server:**
```bash
# Ping storage server
ping imgsv-01-p

# If fails, add to hosts file
sudo nano /etc/hosts
# Add:
<STORAGE_IP>  imgsv-01-p

# Or check DNS
nslookup imgsv-01-p
```

**Test SMB port:**
```bash
# Install netcat if needed
sudo apt install netcat -y

# Test SMB port 445
nc -zv imgsv-01-p 445
# Should output: Connection to imgsv-01-p 445 port [tcp/microsoft-ds] succeeded!
```

### Solution 2: Correct Credentials

**Create credentials file:**
```bash
# Create credentials file (secure location)
sudo nano /root/.smbcredentials

# Add credentials:
username=YOUR_USERNAME
password=YOUR_PASSWORD
domain=YOUR_DOMAIN

# Save and secure
sudo chmod 600 /root/.smbcredentials

# Test mount with credentials
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# Verify
ls -la /mnt/chu-slides
```

**If credentials are incorrect:**
- Contact CHU IT to verify username, password, domain
- Ensure user has read access to `\\imgsv-01-p\anapath_storage_nimble`
- Test credentials on Windows PC: `net use Z: \\imgsv-01-p\anapath_storage_nimble /user:DOMAIN\USERNAME`

### Solution 3: Correct Mount Options

**Try different SMB versions:**
```bash
# Try SMB 3.0 (recommended)
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# If fails, try SMB 2.1
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=2.1,uid=1000,gid=1000 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# If fails, try SMB 1.0 (not recommended, security risk)
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=1.0,uid=1000,gid=1000 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides
```

**Try additional mount options:**
```bash
# Add sec=ntlmssp for NTLM authentication
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,sec=ntlmssp,uid=1000,gid=1000 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# Or sec=krb5 for Kerberos (if domain-joined)
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,sec=krb5,uid=1000,gid=1000 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides
```

### Solution 4: Install cifs-utils

**If mount fails with "unknown filesystem type 'cifs'":**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install cifs-utils -y

# CentOS/RHEL
sudo yum install cifs-utils -y

# Verify installation
mount.cifs --version
```

### Solution 5: Firewall Allowing SMB

**Ensure SMB port 445 is allowed:**
```bash
# Ubuntu/Debian (UFW)
sudo ufw allow out 445/tcp comment 'SMB client'

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=samba-client
sudo firewall-cmd --reload
```

### Solution 6: Persistent Mount (fstab)

**After successful manual mount, make it persistent:**
```bash
# Edit fstab
sudo nano /etc/fstab

# Add line:
//imgsv-01-p/anapath_storage_nimble /mnt/chu-slides cifs credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,iocharset=utf8 0 0

# Test mount from fstab
sudo mount -a

# Verify
mount | grep chu-slides
ls -la /mnt/chu-slides
```

### Problem: Network Share Mounted but No Files Visible

**Symptoms:**
```bash
$ mount | grep chu-slides
//imgsv-01-p/anapath_storage_nimble on /mnt/chu-slides type cifs (...)

$ ls -la /mnt/chu-slides
total 0
# Empty or permission denied
```

**Diagnosis:**
```bash
# Check mount options
mount | grep chu-slides

# Check permissions
ls -ld /mnt/chu-slides

# Check from Windows (if accessible)
# On Windows PC:
net use Z: \\imgsv-01-p\anapath_storage_nimble /user:DOMAIN\USERNAME
dir Z:\
```

**Solutions:**

1. **Check uid/gid in mount options:**
   ```bash
   # Remount with correct uid/gid (1000 = your user)
   sudo umount /mnt/chu-slides
   sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000 \
     //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides
   ```

2. **Check share permissions on storage server:**
   - Contact CHU IT
   - Verify user has Read permission on share
   - Verify user has List/Read permissions on folders

3. **Test with different user:**
   - Try domain administrator account (temporary test)
   - Helps identify if it's a permission issue

### Verification

**After successful mount:**
```bash
# 1. Check mount
mount | grep chu-slides
# Should show: //imgsv-01-p/anapath_storage_nimble on /mnt/chu-slides type cifs (...)

# 2. List files
ls -la /mnt/chu-slides
# Should show folders/files

# 3. Count slides
find /mnt/chu-slides -name "*.mrxs" -o -name "*.bif" -o -name "*.tif" | wc -l
# Should show number of slides

# 4. Test read access
head /mnt/chu-slides/some-file.txt
# Should read file without permission denied

# 5. Verify in Docker container
docker exec varuna-backend-phase2.2 ls -la /slides
# Should show same files as /mnt/chu-slides
```

---

## CORS and Browser Issues

### Problem: CORS Errors in Browser Console

**Symptoms:**

Browser console (F12):
```
Access to fetch at 'http://varun-p-01:8000/api/slides' from origin 'http://varun-p-01'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present...
```

**Diagnosis:**
```bash
# Check backend CORS configuration
docker exec varuna-backend-phase2.X cat /app/.env | grep CORS_ORIGINS

# Test CORS with curl
curl -H "Origin: http://varun-p-01" -I http://varun-p-01:8000/api/health
# Should include header: Access-Control-Allow-Origin: http://varun-p-01
```

### Solution 1: Update Backend CORS Configuration

**Edit backend/.env.phase2.X:**
```bash
cd /path/to/VarunaPoC

# Edit .env file
nano backend/.env.phase2.X

# Ensure CORS_ORIGINS includes all necessary origins:
CORS_ORIGINS=http://varun-p-01,http://localhost,http://localhost:5173

# If using IP address, add it too:
CORS_ORIGINS=http://varun-p-01,http://10.10.5.100,http://localhost,http://localhost:5173

# Save and restart containers
./Scripts/Deployment/stop-phase2.X.sh
./Scripts/Deployment/deploy-phase2.X.sh
```

### Solution 2: Check Frontend Configuration

**Verify frontend calls correct API URL:**
```bash
# Check frontend .env
cat frontend/.env.phase2.X
# Should have: VITE_API_URL=http://varun-p-01:8000

# Check browser Network tab (F12)
# API calls should go to: http://varun-p-01:8000/api/...
# NOT: http://localhost:8000/api/... (unless on server)
```

### Solution 3: Browser Cache Issues

**Clear browser cache:**
```
1. Open browser (Chrome)
2. Press Ctrl+Shift+Delete
3. Select "Cached images and files"
4. Select "All time"
5. Click "Clear data"
6. Reload page (Ctrl+F5)
```

**Or use Incognito/Private mode:**
```
Chrome: Ctrl+Shift+N
Firefox: Ctrl+Shift+P
Edge: Ctrl+Shift+N
```

### Problem: Mixed Content (HTTP/HTTPS)

**Symptoms:**
```
Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an
insecure resource 'http://varun-p-01:8000/...'. This request has been blocked...
```

**Cause:** Frontend loaded over HTTPS, but API called over HTTP.

**Solutions:**

1. **Use HTTP for both (Phase 2 - acceptable):**
   - Access frontend via: `http://varun-p-01` (not https://)

2. **Use HTTPS for both (Future - recommended):**
   - Configure SSL/TLS certificates
   - Update nginx to serve HTTPS
   - Update backend .env: `API_BASE_URL=https://varun-p-01:8000`

---

## Performance Issues

### Problem: Slow Tile Loading

**Symptoms:**
- Tiles take > 1 second to load
- Viewer feels sluggish when panning/zooming
- Network tab shows slow response times

**Diagnosis:**
```bash
# 1. Measure network latency
ping -c 10 varun-p-01
# Average should be < 50ms for local network

# 2. Measure tile response time
time curl -o /dev/null -s http://varun-p-01:8000/api/slides/{slide_id}/tile/0/0/0/256/256
# Should be < 500ms for Phase 2.1, < 1s for Phase 2.2

# 3. Check server load
ssh user@varun-p-01
docker stats varuna-backend-phase2.X
# CPU should be < 80%, Memory < 80%

# 4. Check network bandwidth (if available)
iperf3 -c varun-p-01
# Should be > 100 Mbps
```

### Solution 1: Optimize Backend Cache (Phase 2.2)

**Increase cache sizes for network latency:**
```bash
# Edit backend/.env.phase2.2
nano backend/.env.phase2.2

# Increase cache sizes:
MAX_TILE_CACHE_SIZE=500  # Default: 200
MAX_SLIDE_CACHE_SIZE=30   # Default: 20
NETWORK_TIMEOUT=120       # Default: 60

# Restart containers
./Scripts/Deployment/stop-phase2.2.sh
./Scripts/Deployment/deploy-phase2.2.sh
```

### Solution 2: Optimize Network Share Mount

**Add cache options to SMB mount:**
```bash
# Unmount current
sudo umount /mnt/chu-slides

# Remount with cache options
sudo mount -t cifs -o credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,cache=strict,actimeo=60 \
  //imgsv-01-p/anapath_storage_nimble /mnt/chu-slides

# Update /etc/fstab for persistence
sudo nano /etc/fstab
# Update line:
//imgsv-01-p/anapath_storage_nimble /mnt/chu-slides cifs credentials=/root/.smbcredentials,vers=3.0,uid=1000,gid=1000,cache=strict,actimeo=60 0 0
```

### Solution 3: Check Network Path

**Ensure optimal network routing:**
```bash
# Trace route to storage server
traceroute imgsv-01-p

# Should show minimal hops (ideally 1-2)
# If many hops, contact network admin to optimize routing
```

**Check VLAN configuration:**
- VarunaPoC server and storage server should be on same VLAN (if possible)
- Avoid routing through slow network segments

### Solution 4: Optimize OpenSeadragon (Frontend)

**Reduce tile prefetching:**
```bash
# Edit frontend/.env.phase2.2
nano frontend/.env.phase2.2

# Reduce prefetch level:
VITE_OSD_PREFETCH_LEVEL=1  # Default: 2

# Rebuild frontend
docker-compose -f docker-compose.phase2.2.yml build frontend
docker-compose -f docker-compose.phase2.2.yml up -d frontend
```

### Solution 5: Increase Server Resources

**If server is under heavy load:**
```bash
# Check resource usage
docker stats

# If CPU/Memory maxed out:
# - Increase server resources (more CPU, more RAM)
# - Limit concurrent users
# - Deploy multiple VarunaPoC instances (load balancing)
```

---

## VLAN Configuration Issues

### Problem: Cannot Access from Specific VLAN

**Symptoms:**
- Access works from server's VLAN
- Access fails from PACS workstation VLAN
- ping works, but HTTP doesn't

**Diagnosis:**
```bash
# From PACS workstation, check route to server
tracert varun-p-01

# From server, check VLAN interfaces
ip addr show

# Check routing table
ip route show
```

### Solution: Configure VLAN Routing

**Contact network administrator to:**

1. **Identify VLANs:**
   - VarunaPoC server VLAN: `VLAN_SERVER_ID`
   - PACS workstation VLAN: `VLAN_PACS_ID`

2. **Configure routing between VLANs:**
   - Allow TCP ports 80 and 8000 from VLAN_PACS to VLAN_SERVER
   - Allow established connections back

3. **Verify ACLs:**
   - Ensure no ACLs blocking HTTP traffic between VLANs

4. **Test from multiple workstations:**
   - Test from VLAN_PACS: Should work
   - Test from VLAN_SERVER: Should work
   - Test from other VLANs: Configure as needed

---

## Diagnostic Tools

### Essential Tools

**On VarunaPoC Server (Linux):**
```bash
# Install diagnostic tools
sudo apt install net-tools curl netcat telnet nmap iperf3 traceroute dnsutils -y
```

**On PC Client (Windows):**
```cmd
REM Most tools built-in (ping, tracert, telnet, nslookup)
REM Optional: Install curl for Windows
REM https://curl.se/windows/
```

### Network Diagnostic Commands

**Test connectivity:**
```bash
# Ping (ICMP)
ping varun-p-01

# Traceroute (path to host)
traceroute varun-p-01  # Linux
tracert varun-p-01     # Windows

# Test TCP port
telnet varun-p-01 80
nc -zv varun-p-01 80  # Linux alternative

# Port scan (check all open ports)
nmap varun-p-01

# Test HTTP
curl -v http://varun-p-01:8000/api/health
```

**Test DNS:**
```bash
# Resolve hostname
nslookup varun-p-01

# Query specific DNS server
nslookup varun-p-01 8.8.8.8

# Reverse lookup
nslookup <SERVER_IP>

# Detailed DNS query
dig varun-p-01  # Linux
```

**Test bandwidth:**
```bash
# Install iperf3 on both server and client

# On server:
iperf3 -s

# On client:
iperf3 -c varun-p-01

# Should show bandwidth (target: > 100 Mbps for good performance)
```

### Docker Diagnostic Commands

**Check containers:**
```bash
# List running containers
docker ps

# View container logs
docker logs varuna-backend-phase2.X
docker logs varuna-frontend-phase2.X

# Follow logs (real-time)
docker logs -f varuna-backend-phase2.X

# Inspect container
docker inspect varuna-backend-phase2.X

# Execute command in container
docker exec varuna-backend-phase2.X ls /slides

# Check container network
docker inspect varuna-backend-phase2.X | grep IPAddress
```

**Check Docker networking:**
```bash
# List Docker networks
docker network ls

# Inspect network
docker network inspect varuna-network

# Test container connectivity
docker exec varuna-backend-phase2.X ping google.com
docker exec varuna-backend-phase2.X curl http://varun-p-01:8000/api/health
```

### Browser Developer Tools

**Chrome/Firefox DevTools (F12):**

1. **Console tab:**
   - Look for JavaScript errors
   - CORS errors appear here

2. **Network tab:**
   - View all HTTP requests
   - Check request/response times
   - Check status codes (200, 404, 500, etc.)
   - Inspect request/response headers

3. **Application tab (Chrome):**
   - Check Local Storage
   - Check Service Workers (if used)

4. **Performance tab:**
   - Record page load
   - Identify bottlenecks

---

## Contact and Escalation

### Internal Support Levels

**Level 1: Application Support**
- VarunaPoC deployment issues
- Container problems
- Slide loading issues
- Contact: VarunaPoC Development Team

**Level 2: Network Support**
- DNS resolution issues
- Firewall configuration
- VLAN routing
- Network share mounting
- Contact: CHU IT Network Team

**Level 3: Infrastructure Support**
- Storage server issues
- PACS workstation problems
- Telemis PACS integration
- Contact: CHU IT Infrastructure Team

### Information to Provide When Escalating

**For VarunaPoC Issues:**
- [ ] VarunaPoC version/phase (2.1 or 2.2)
- [ ] Error messages (from logs, browser console)
- [ ] Steps to reproduce
- [ ] Docker container status (`docker ps`)
- [ ] Logs (`docker logs varuna-backend-phase2.X`)

**For Network Issues:**
- [ ] Source (PC client IP, VLAN)
- [ ] Destination (varun-p-01 IP)
- [ ] Ports affected (80, 8000, 445)
- [ ] Diagnostic results (ping, telnet, traceroute)
- [ ] Firewall rules in effect

**For Storage Issues (Phase 2.2):**
- [ ] Storage server (imgsv-01-p IP)
- [ ] Share path (\\imgsv-01-p\anapath_storage_nimble)
- [ ] User credentials used
- [ ] Mount command and output
- [ ] SMB version tested

### Emergency Contact

**Critical Production Issue:**
- [ ] Service completely down
- [ ] Multiple users affected
- [ ] Patient care impacted

**Contact:**
- VarunaPoC On-Call: [phone/email]
- CHU IT On-Call: [phone/email]

---

**Document Version:** 2.0
**Last Updated:** 2025-12-03
**Authors:** VarunaPoC Development Team
**Contact:** [your-email@chu-ucl.be]
