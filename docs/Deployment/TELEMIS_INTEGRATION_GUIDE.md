# VarunaPoC - Telemis PACS Integration Guide

**Version:** 2.0
**Last Updated:** 2025-12-03
**Status:** Production Ready
**Phase:** 2.1 and 2.2 Network Deployment

---

## Table of Contents

1. [Overview](#overview)
2. [Integration Architecture](#integration-architecture)
3. [Prerequisites](#prerequisites)
4. [Installation Steps](#installation-steps)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)
9. [User Training](#user-training)

---

## Overview

This guide explains how to integrate VarunaPoC web-based slide viewer with **Telemis PACS**, enabling radiologists and pathologists to open histological slides directly from the PACS interface.

### Integration Flow

```
Telemis PACS Workstation
    │
    │ User: Right-click on slide study
    │        Select: "Open with VarunaPoC - WSI Viewer"
    │
    ▼
Telemis reads plugin configuration
    │
    │ Extracts: {$study.examindex$} → Slide ID
    │
    ▼
Telemis launches Chrome
    │
    │ URL: http://varun-p-01/slide/AO.25B27859.2.1.3
    │
    ▼
VarunaPoC Frontend
    │
    │ Extracts slide ID from URL path
    │
    ▼
VarunaPoC Backend API
    │
    │ GET /api/slides/by-id/AO.25B27859.2.1.3
    │ Searches in SLIDES_REPOSITORY_PATH
    │
    ▼
OpenSlide opens slide
    │
    ▼
User views slide in browser
```

### Benefits

- **Seamless Workflow:** Open slides directly from PACS (no manual file search)
- **No Installation:** Web-based viewer (no client software to install)
- **Vendor-Neutral:** Supports multiple slide formats (.mrxs, .bif, .tif)
- **Multi-Platform:** Works on any PC with modern browser

---

## Integration Architecture

### Components

1. **Telemis PACS Workstation:** PC running Telemis client software
2. **Plugin Configuration File:** `.cfg` file defining how to launch VarunaPoC
3. **Browser:** Chrome/Firefox/Edge to open VarunaPoC web viewer
4. **VarunaPoC Server:** varun-p-01 hosting the slide viewer

### Data Flow

```
┌─────────────────────────────────────────┐
│ Telemis PACS Workstation                │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Telemis Client UI                   │ │
│ │                                     │ │
│ │ Study: Slide AO.25B27859.2.1.3     │ │
│ │                                     │ │
│ │ [Right-click] → Open with...       │ │
│ │   ├─ DICOM Viewer                  │ │
│ │   ├─ Report Editor                 │ │
│ │   └─ VarunaPoC - WSI Viewer  ← ✓   │ │
│ └─────────────────────────────────────┘ │
│           │                              │
│           │ Reads plugin config:         │
│           │ anapath_viewer.plugin...cfg  │
│           │                              │
│           ▼                              │
│ ┌─────────────────────────────────────┐ │
│ │ Plugin Execution                    │ │
│ │                                     │ │
│ │ thirdPartySoftware=                 │ │
│ │   "chrome.exe"                      │ │
│ │   "http://varun-p-01/slide/         │ │
│ │    {$study.examindex$}"             │ │
│ │                                     │ │
│ │ Replaces: {$study.examindex$}       │ │
│ │   → AO.25B27859.2.1.3               │ │
│ └─────────────────────────────────────┘ │
│           │                              │
│           │ Launches browser             │
│           ▼                              │
│ ┌─────────────────────────────────────┐ │
│ │ Google Chrome                       │ │
│ │                                     │ │
│ │ URL: http://varun-p-01/slide/       │ │
│ │      AO.25B27859.2.1.3              │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
            │
            │ HTTP GET
            ▼
┌─────────────────────────────────────────┐
│ VarunaPoC Server (varun-p-01)           │
│                                         │
│ Frontend: Receives slide ID from URL    │
│           Calls API: GET /api/slides/   │
│           by-id/AO.25B27859.2.1.3       │
│                                         │
│ Backend:  Searches slides repository    │
│           Opens slide with OpenSlide    │
│           Serves tiles to frontend      │
│                                         │
│ User sees: Full slide viewer in browser │
└─────────────────────────────────────────┘
```

---

## Prerequisites

### Telemis PACS Requirements

- **Telemis Version:** Compatible with third-party software plugins
- **Permissions:** Administrative access to install plugin configuration
- **File Access:** Write access to Telemis plugins directory

**Typical Telemis directories:**
```
C:\Program Files\Telemis\
├── Plugins\          ← Plugin .cfg files
├── Icons\            ← Plugin icons
├── Logs\             ← Telemis logs (for debugging)
└── Config\           ← Telemis configuration
```

### VarunaPoC Requirements

- **Phase 2.1 or 2.2 deployed** and accessible from PACS workstations
- **Server hostname resolvable:** varun-p-01 (DNS or hosts file)
- **Network access:** PACS workstations can reach http://varun-p-01

### PC Workstation Requirements

- **Browser:** Google Chrome (recommended), Firefox, or Microsoft Edge
- **Browser Path:** Known installation path (e.g., `C:\Program Files\Google\Chrome\Application\chrome.exe`)
- **Network:** Access to VarunaPoC server (http://varun-p-01)

### DICOM/Slide Naming Requirements

- **Slide ID in DICOM metadata:** `study.examindex` field must contain slide filename
- **Naming convention:** Slide files named consistently with DICOM examindex

**Example mapping:**
```
DICOM Study:
  examindex: "AO.25B27859.2.1.3"

Slide File (on server):
  /slides/2025/12/AO.25B27859.2.1.3.mrxs
  /slides/2025/12/AO.25B27859.2.1.3/  (companion directory)
```

---

## Installation Steps

### Step 1: Prepare Plugin Configuration File

**1.1. Copy template configuration:**
```bash
# From VarunaPoC repository
cd /path/to/VarunaPoC
cp Config_Integration_Infra/anapath_viewer.plugin.varuna.phase2.cfg \
   /tmp/anapath_viewer.plugin.varuna.phase2.cfg
```

**1.2. Review and customize (if needed):**

Open the file and verify:
- Browser path is correct
- Server hostname is correct (varun-p-01)
- Slide ID variable is correct ({$study.examindex$})

Default configuration:
```ini
[VARUNA_VIEWER]
thirdPartySoftware = "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://varun-p-01/slide/{$study.examindex$}"
thirdPartySoftwareIcon = microscope-viewer.png
thirdPartySoftwareName = VarunaPoC - WSI Viewer
okExitCode = 0
```

**1.3. Verify browser path on PACS workstations:**
```cmd
# On PACS workstation, check Chrome path
dir "C:\Program Files\Google\Chrome\Application\chrome.exe"

# If Chrome is elsewhere, update thirdPartySoftware path in .cfg
# Common alternative paths:
#   C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
#   C:\Users\<username>\AppData\Local\Google\Chrome\Application\chrome.exe

# Alternative browsers:
#   Firefox: C:\Program Files\Mozilla Firefox\firefox.exe
#   Edge: C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
```

### Step 2: Copy Plugin Configuration to Telemis

**2.1. Copy .cfg file to Telemis plugins directory:**

**Method A: Manual copy (Windows Explorer)**
1. Open Windows Explorer on PACS workstation
2. Navigate to: `C:\Program Files\Telemis\Plugins\`
3. Copy: `anapath_viewer.plugin.varuna.phase2.cfg` to this directory
4. Verify file permissions (readable by Telemis service)

**Method B: Command line (as Administrator)**
```cmd
# On PACS workstation (as Administrator)
copy \\server\share\anapath_viewer.plugin.varuna.phase2.cfg ^
     "C:\Program Files\Telemis\Plugins\"

# Verify
dir "C:\Program Files\Telemis\Plugins\anapath_viewer.plugin.varuna.phase2.cfg"
```

**2.2. File naming convention:**

Telemis plugin files must follow this pattern:
```
<prefix>.plugin.<name>.<suffix>.cfg
```

Examples:
- `anapath_viewer.plugin.varuna.phase2.cfg` ✓
- `viewer.plugin.varuna.cfg` ✓
- `varuna.cfg` ✗ (missing "plugin" keyword)

### Step 3: Add Plugin Icon (Optional)

**3.1. Prepare icon file:**
- Format: PNG, 32x32 pixels (recommended)
- Name: `microscope-viewer.png` (or as specified in .cfg)
- Transparent background recommended

**3.2. Copy icon to Telemis icons directory:**
```cmd
copy microscope-viewer.png "C:\Program Files\Telemis\Icons\"
```

**3.3. If icon not available:**

Remove or comment out icon line in .cfg:
```ini
# thirdPartySoftwareIcon = microscope-viewer.png
```

Telemis will use a default icon.

### Step 4: Restart Telemis Service

**4.1. Restart Telemis PACS service:**

**Method A: Services console (GUI)**
1. Press `Win + R`, type `services.msc`, press Enter
2. Find "Telemis PACS Service" (or similar name)
3. Right-click → Restart

**Method B: Command line (as Administrator)**
```cmd
# Find Telemis service name
sc query | findstr "Telemis"

# Restart service (replace SERVICE_NAME with actual name)
net stop "Telemis PACS Service"
net start "Telemis PACS Service"

# Or with sc command
sc stop TelemisService
sc start TelemisService
```

**4.2. Restart Telemis client application:**

Close and reopen Telemis client on workstation.

### Step 5: Verify Plugin Installation

**5.1. Check Telemis configuration:**

In Telemis client:
1. Go to: **Tools** → **Options** → **Third Party Software**
2. Look for: "VarunaPoC - WSI Viewer"
3. Verify it appears in the list

**5.2. Check Telemis logs (if plugin not appearing):**
```
C:\Program Files\Telemis\Logs\TelemisClient.log
```

Look for errors related to plugin loading:
```
ERROR: Failed to load plugin: anapath_viewer.plugin.varuna.phase2.cfg
```

---

## Configuration

### Basic Configuration (Default)

The default configuration uses Chrome and examindex as slide ID:

```ini
[VARUNA_VIEWER]
thirdPartySoftware = "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://varun-p-01/slide/{$study.examindex$}"
thirdPartySoftwareIcon = microscope-viewer.png
thirdPartySoftwareName = VarunaPoC - WSI Viewer
okExitCode = 0
```

### Available Telemis Variables

Telemis provides many variables that can be used in the URL. Common ones:

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `{$study.examindex$}` | `AO.25B27859.2.1.3` | Slide ID (most important) |
| `{$study.studyiuid$}` | `1.2.840.113...` | DICOM Study UID |
| `{$study.seriesiuid$}` | `1.2.840.113...` | DICOM Series UID |
| `{$study.accessionNumber$}` | `ACC123456` | Accession number |
| `{$study.acquisitionDate.dateyyyy$}` | `2025` | Year |
| `{$study.acquisitionDate.datemm$}` | `12` | Month |
| `{$study.acquisitionDate.datedd$}` | `03` | Day |
| `{$study.acquisitionDate.dateyyyymmdd$}` | `20251203` | Full date |
| `{$patient.patientID$}` | `PT12345` | Patient ID (anonymized) |

**Full list:** Consult Telemis documentation or contact Telemis support.

### Advanced Configurations

#### Option 1: Use Different Browser

**Firefox:**
```ini
thirdPartySoftware = "C:\Program Files\Mozilla Firefox\firefox.exe" "http://varun-p-01/slide/{$study.examindex$}"
```

**Microsoft Edge:**
```ini
thirdPartySoftware = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" "http://varun-p-01/slide/{$study.examindex$}"
```

#### Option 2: Open in New Tab (if browser already open)

**Chrome with --new-tab:**
```ini
thirdPartySoftware = "C:\Program Files\Google\Chrome\Application\chrome.exe" --new-tab "http://varun-p-01/slide/{$study.examindex$}"
```

#### Option 3: Include Additional Metadata in URL

**Add date to URL:**
```ini
thirdPartySoftware = "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://varun-p-01/slide/{$study.examindex$}?date={$study.acquisitionDate.dateyyyymmdd$}"
```

VarunaPoC frontend can extract query parameters:
```javascript
// In frontend: parse URL query parameters
const urlParams = new URLSearchParams(window.location.search);
const date = urlParams.get('date');  // 20251203
```

#### Option 4: Use Series UID instead of examindex

If your DICOM metadata uses Series UID as primary identifier:
```ini
thirdPartySoftware = "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://varun-p-01/slide/series/{$study.seriesiuid$}"
```

Then update VarunaPoC backend to handle `/slide/series/{series_uid}` route.

#### Option 5: Enable Command Logging (for debugging)

```ini
saveCommandTo = C:\Telemis\Logs\varuna-plugin.log
```

This logs every command executed by the plugin, useful for troubleshooting.

### Custom Plugin Name and Icon

**Change display name:**
```ini
thirdPartySoftwareName = Histology Viewer
# Or
thirdPartySoftwareName = Slide Viewer - CHU UCL
```

**Use custom icon:**
```ini
thirdPartySoftwareIcon = my-custom-icon.png
```

Place `my-custom-icon.png` in `C:\Program Files\Telemis\Icons\`.

---

## Testing

### Test 1: Plugin Appears in Telemis UI

**Steps:**
1. Open Telemis client on PACS workstation
2. Navigate to a histological slide study
3. Right-click on the study
4. Check context menu for: "Open with..." → "VarunaPoC - WSI Viewer"

**Expected Result:** Plugin appears in context menu.

**If plugin doesn't appear:**
- Check .cfg file is in correct directory
- Check .cfg file name follows pattern: `*.plugin.*.cfg`
- Check Telemis service was restarted
- Check Telemis logs for errors

### Test 2: Browser Launches with Correct URL

**Steps:**
1. Right-click on slide study
2. Select: "Open with..." → "VarunaPoC - WSI Viewer"
3. Observe browser window opening

**Expected Result:** Chrome opens with URL: `http://varun-p-01/slide/<SLIDE_ID>`

**Check:**
- Browser opens (not error dialog)
- URL is correct (http://varun-p-01/slide/...)
- Slide ID is extracted correctly from DICOM metadata

**If browser doesn't open:**
- Check browser path in .cfg file (exact path required)
- Check browser is installed on PACS workstation
- Check for error dialog from Telemis

### Test 3: VarunaPoC Loads Slide

**Steps:**
1. After browser opens, observe VarunaPoC frontend loading
2. Frontend should:
   - Extract slide ID from URL
   - Call backend API: `/api/slides/by-id/<SLIDE_ID>`
   - Load slide viewer with OpenSeadragon

**Expected Result:** Slide viewer opens showing the requested slide.

**If slide doesn't load:**
- Check browser console (F12) for JavaScript errors
- Check network tab for API call status
- Verify slide ID matches file naming on server
- Check backend logs for file resolution errors

### Test 4: End-to-End Workflow

**Complete workflow test:**

1. **Open Telemis PACS client**
2. **Navigate to slide study:** AO.25B27859.2.1.3
3. **Right-click → "Open with VarunaPoC - WSI Viewer"**
4. **Chrome opens:** http://varun-p-01/slide/AO.25B27859.2.1.3
5. **VarunaPoC loads:** Slide viewer appears
6. **Slide opens:** Full histological slide visible
7. **Navigate slide:** Pan, zoom, mini-map work correctly
8. **Return to Telemis:** Close browser, return to PACS

**Expected Result:** Seamless workflow with no errors.

### Test 5: Multiple Workstations

**Test on multiple PACS workstations:**

- [ ] Workstation 1: Plugin works
- [ ] Workstation 2: Plugin works
- [ ] Workstation 3: Plugin works

Ensure .cfg file is deployed to **all PACS workstations** (or use network share).

---

## Troubleshooting

### Problem 1: Plugin Not Appearing in Telemis UI

**Symptoms:**
- "Open with..." menu doesn't show VarunaPoC option
- Plugin not visible in Telemis settings

**Diagnosis:**
```cmd
# Check if .cfg file exists
dir "C:\Program Files\Telemis\Plugins\anapath_viewer.plugin.varuna.phase2.cfg"

# Check file name pattern
# Must contain "plugin" keyword: *.plugin.*.cfg

# Check Telemis logs
type "C:\Program Files\Telemis\Logs\TelemisClient.log" | findstr "plugin"
```

**Solutions:**

1. **Verify file location:**
   - Must be in: `C:\Program Files\Telemis\Plugins\`
   - Not in subdirectory

2. **Verify file name:**
   - Must match pattern: `<name>.plugin.<variant>.cfg`
   - Example: `anapath_viewer.plugin.varuna.phase2.cfg`

3. **Check file permissions:**
   - Must be readable by Telemis service user
   - Right-click file → Properties → Security → Verify "Read" is allowed

4. **Verify section header:**
   - Open .cfg file
   - Check first line: `[VARUNA_VIEWER]` (or unique name)
   - Section name must be in square brackets

5. **Restart Telemis:**
   - Restart Telemis service (services.msc)
   - Close and reopen Telemis client

6. **Check Telemis version:**
   - Contact Telemis support to verify plugin support

### Problem 2: Browser Doesn't Open

**Symptoms:**
- Click "Open with VarunaPoC" but nothing happens
- Error dialog: "Cannot find file chrome.exe"

**Diagnosis:**
```cmd
# Verify browser path
dir "C:\Program Files\Google\Chrome\Application\chrome.exe"

# Check command logging (if enabled in .cfg)
type "C:\Telemis\Logs\varuna-plugin.log"
```

**Solutions:**

1. **Verify browser path:**
   ```cmd
   # Find Chrome installation
   where chrome

   # Or check common paths
   dir "C:\Program Files\Google\Chrome\Application\chrome.exe"
   dir "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
   ```

2. **Update .cfg file with correct path:**
   ```ini
   # If Chrome is in Program Files (x86):
   thirdPartySoftware = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" "http://varun-p-01/slide/{$study.examindex$}"
   ```

3. **Use different browser:**
   ```ini
   # Try Firefox
   thirdPartySoftware = "C:\Program Files\Mozilla Firefox\firefox.exe" "http://varun-p-01/slide/{$study.examindex$}"
   ```

4. **Check quotes:**
   - Browser path MUST be in double quotes
   - URL MUST be in separate double quotes

5. **Test command manually:**
   ```cmd
   # Open Command Prompt
   # Run exact command from .cfg
   "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://varun-p-01/slide/TEST123"

   # Should open browser with URL
   ```

### Problem 3: Browser Opens but Shows "Cannot Reach This Page"

**Symptoms:**
- Browser opens successfully
- URL is correct: http://varun-p-01/slide/...
- Page shows: "This site can't be reached"

**Diagnosis:**
```cmd
# From PACS workstation, test connectivity
ping varun-p-01

# Test HTTP access
curl http://varun-p-01:8000/api/health

# Or open in browser manually
http://varun-p-01:8000/api/health
```

**Solutions:**

1. **Add hosts file entry:**
   ```cmd
   # As Administrator
   notepad C:\Windows\System32\drivers\etc\hosts

   # Add line:
   <SERVER_IP>  varun-p-01

   # Example:
   10.10.5.100  varun-p-01

   # Save and close

   # Flush DNS cache
   ipconfig /flushdns
   ```

2. **Check firewall:**
   - Verify PACS workstation can access ports 80 and 8000 on server
   - Test: `telnet varun-p-01 80`

3. **Check VarunaPoC deployment:**
   - Ensure Phase 2.1 or 2.2 is deployed (not Phase 1)
   - On server: `docker ps | grep varuna`
   - Should see containers with `0.0.0.0:80` and `0.0.0.0:8000`

4. **Use IP address (temporary workaround):**
   ```ini
   # In .cfg file, use IP instead of hostname
   thirdPartySoftware = "C:\Program Files\Google\Chrome\Application\chrome.exe" "http://10.10.5.100/slide/{$study.examindex$}"
   ```

See: [NETWORK_TROUBLESHOOTING.md](./NETWORK_TROUBLESHOOTING.md) for detailed network issues.

### Problem 4: Slide Not Found in VarunaPoC

**Symptoms:**
- Browser opens correctly
- VarunaPoC frontend loads
- Error message: "Slide not found" or API returns 404

**Diagnosis:**
```bash
# On VarunaPoC server, check if slide exists
docker exec varuna-backend-phase2.X find /slides -name "*AO.25B27859.2.1.3*"

# Check backend logs
docker logs varuna-backend-phase2.X | grep "AO.25B27859.2.1.3"

# Test API directly
curl http://varun-p-01:8000/api/slides/by-id/AO.25B27859.2.1.3
```

**Solutions:**

1. **Verify slide naming convention:**
   ```
   DICOM examindex: AO.25B27859.2.1.3

   Slide file MUST be named:
   - AO.25B27859.2.1.3.mrxs  OR
   - AO.25B27859.2.1.3.bif   OR
   - AO.25B27859.2.1.3.tif

   With companion directory (for .mrxs):
   - AO.25B27859.2.1.3/
   ```

2. **Check file location:**
   - Slides must be in: `/slides` (inside container)
   - Maps to: `/local/slides` (Phase 2.1) or `/mnt/chu-slides` (Phase 2.2)

3. **Verify slide format supported:**
   - Supported: .mrxs, .bif, .tif/.tiff
   - See: `docs/Manuel/04-FORMATS_SUPPORTES.md`

4. **Check backend API implementation:**
   - Ensure `/api/slides/by-id/{slide_id}` endpoint exists
   - Check `backend/routes/slides.py`

5. **Synchronize DICOM metadata with file naming:**
   - DICOM examindex MUST match slide filename
   - Contact PACS administrator to verify metadata

### Problem 5: Slide Opens Wrong File

**Symptoms:**
- Plugin works, browser opens, slide loads
- But wrong slide is displayed

**Diagnosis:**
```bash
# Check if multiple slides have similar names
docker exec varuna-backend-phase2.X find /slides -name "*AO.25B27859*"

# Check DICOM metadata
# In Telemis, view study details:
#   Study → Properties → examindex field
```

**Solutions:**

1. **Ensure unique slide IDs:**
   - Each slide must have unique examindex in DICOM
   - No duplicate filenames on server

2. **Use more specific matching:**
   - Backend should match EXACT slide ID
   - Not partial match

3. **Verify Telemis variable:**
   - Confirm `{$study.examindex$}` contains correct value
   - Try logging: add `saveCommandTo` in .cfg to see actual values

### Problem 6: Performance Issues from Telemis

**Symptoms:**
- Plugin works but slow to open
- Browser takes long time to launch
- Tiles load slowly

**Diagnosis:**
```cmd
# Test network latency from PACS workstation
ping varun-p-01

# Test API response time
curl -w "Time: %{time_total}s\n" -o NUL -s http://varun-p-01:8000/api/health
```

**Solutions:**

1. **Check network bandwidth:**
   - Ensure PACS workstations and server on same VLAN
   - Avoid routing through slow network segments

2. **Optimize Phase 2.2 (if using CHU infrastructure):**
   - See [PHASE2_NETWORK_INTEGRATION.md](./PHASE2_NETWORK_INTEGRATION.md) for cache optimization

3. **Pre-open browser:**
   - Keep browser window open before launching plugin
   - Use `--new-tab` flag in .cfg

4. **Check server load:**
   ```bash
   # On server
   docker stats varuna-backend-phase2.X
   ```

---

## Advanced Configuration

### Multi-Plugin Setup (Multiple Viewers)

If you have multiple slide viewers, create separate plugin configs:

**VarunaPoC plugin:**
```ini
# File: anapath_viewer.plugin.varuna.cfg
[VARUNA_VIEWER]
thirdPartySoftware = "chrome.exe" "http://varun-p-01/slide/{$study.examindex$}"
thirdPartySoftwareName = VarunaPoC - Web Viewer
```

**Legacy desktop viewer plugin:**
```ini
# File: anapath_viewer.plugin.legacy.cfg
[LEGACY_VIEWER]
thirdPartySoftware = "C:\LegacyViewer\viewer.exe" "{$study.examindex$}"
thirdPartySoftwareName = Desktop Slide Viewer (Legacy)
```

Both plugins will appear in "Open with..." menu.

### Conditional Plugin (based on DICOM attributes)

Some Telemis versions support conditional plugins (check documentation):

```ini
[VARUNA_VIEWER]
thirdPartySoftware = "chrome.exe" "http://varun-p-01/slide/{$study.examindex$}"
thirdPartySoftwareName = VarunaPoC - WSI Viewer

# Only show for specific modalities
applicableModality = SM,OP,OT

# Only show for specific vendors
applicableManufacturer = 3DHISTECH,Ventana,Leica
```

### Centralized Plugin Deployment

**Option 1: Network share (recommended)**
```cmd
# On file server, create share
net share TelemisPlugins=C:\TelemisPlugins /grant:Everyone,READ

# On PACS workstations, use symbolic link
mklink "C:\Program Files\Telemis\Plugins\anapath_viewer.plugin.varuna.phase2.cfg" ^
       "\\fileserver\TelemisPlugins\anapath_viewer.plugin.varuna.phase2.cfg"
```

**Option 2: Group Policy deployment**
- Create GPO to copy .cfg file to all workstations
- Schedule task to copy file on startup

**Option 3: Configuration management**
- Use Ansible, Puppet, or similar to deploy .cfg file

---

## User Training

### Training Checklist

- [ ] Explain plugin purpose (open slides from PACS)
- [ ] Demonstrate: Right-click → "Open with VarunaPoC"
- [ ] Show slide viewer navigation (pan, zoom, mini-map)
- [ ] Explain browser window management (close when done)
- [ ] Troubleshooting: What to do if slide doesn't load

### User Quick Reference

**Opening a Slide:**
1. In Telemis PACS, navigate to histological slide study
2. Right-click on study
3. Select: "Open with..." → "VarunaPoC - WSI Viewer"
4. Chrome opens automatically with slide viewer
5. Navigate slide using mouse (drag to pan, scroll to zoom)

**Closing the Viewer:**
- Simply close the browser tab or window
- Return to Telemis PACS

**If Slide Doesn't Load:**
1. Check browser URL (should be: http://varun-p-01/slide/...)
2. Refresh page (F5)
3. Check network connectivity (can you access other web pages?)
4. Contact IT support if issue persists

### IT Support Quick Reference

**Common Support Requests:**

| Issue | Quick Fix |
|-------|-----------|
| Plugin not appearing | Verify .cfg file in `C:\Program Files\Telemis\Plugins\` |
| Browser doesn't open | Check browser path in .cfg file |
| "Cannot reach page" | Add varun-p-01 to hosts file |
| Slide not found | Verify slide ID in DICOM matches filename |
| Slow loading | Check network connectivity to varun-p-01 |

---

## Additional Resources

- [Phase 2 Network Integration Guide](./PHASE2_NETWORK_INTEGRATION.md)
- [Network Troubleshooting](./NETWORK_TROUBLESHOOTING.md)
- [VarunaPoC API Documentation](http://varun-p-01:8000/docs)
- Telemis Support: [contact-info]

---

**Document Version:** 2.0
**Last Updated:** 2025-12-03
**Authors:** VarunaPoC Development Team
**Contact:** [your-email@chu-ucl.be]
