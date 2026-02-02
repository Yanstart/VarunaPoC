# SECURITY PHASE 1 - IMPLEMENTATION GUIDE

**VarunaPoC - Sécurisation Urgente (1-2 semaines)**

**Objectif:** Rendre le PoC utilisable en environnement CHU interne (réseau isolé) avec sécurité minimale acceptable.

**Date:** 2025-12-31
**Status:** Ready for Implementation
**Prerequisites:** Backend FastAPI + Frontend Vite opérationnels

---

## Table of Contents

1. [Overview](#1-overview)
2. [HTTP Basic Authentication](#2-http-basic-authentication)
3. [HTTPS Local (Self-Signed)](#3-https-local-self-signed)
4. [Audit Trail](#4-audit-trail)
5. [Security Headers](#5-security-headers)
6. [Input Validation](#6-input-validation)
7. [Vulnerability Scanning](#7-vulnerability-scanning)
8. [Testing & Validation](#8-testing--validation)
9. [Deployment Checklist](#9-deployment-checklist)

---

## 1. Overview

### 1.1 Phase 1 Goals

**Sécurité Minimale:**
- Authentification (Basic Auth temporaire)
- Chiffrement in transit (HTTPS local)
- Traçabilité (audit logs)
- Protection XSS/CSRF (security headers)
- Validation entrées (input sanitization)

**NON-GOALS (Phase 2+):**
- OAuth2/JWT (complexe, Phase 2)
- RBAC (nécessite user DB, Phase 2)
- MFA (Phase 2)
- Chiffrement at rest (Phase 3)

---

### 1.2 Architecture Phase 1

```
[Client Browser]
      │ HTTPS (self-signed)
      ▼
[Nginx Reverse Proxy]
      │ HTTP Basic Auth
      ▼
[FastAPI Backend]
      │ Audit Logs
      ▼
[/Slides/ filesystem]
```

**Network:** Réseau interne CHU uniquement (PAS internet)

---

## 2. HTTP Basic Authentication

### 2.1 Backend Implementation

**Créer fichier:** `backend/auth/basic.py`

```python
"""
HTTP Basic Authentication (Phase 1 - TEMPORAIRE)

IMPORTANT:
- Utiliser HTTPS obligatoire (sinon credentials en clair)
- Phase 2: Remplacer par OAuth2 + JWT
- Ne PAS utiliser en production long terme

Refs:
- RFC 7617: The 'Basic' HTTP Authentication Scheme
- https://datatracker.ietf.org/doc/html/rfc7617
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
import logging

security = HTTPBasic()
logger = logging.getLogger(__name__)

# Credentials depuis env (JAMAIS hardcodés)
VALID_USERNAME = os.getenv("API_USERNAME", "")
VALID_PASSWORD = os.getenv("API_PASSWORD", "")

if not VALID_USERNAME or not VALID_PASSWORD:
    raise RuntimeError(
        "API_USERNAME and API_PASSWORD must be set in environment. "
        "See .env.example for details."
    )


def authenticate_basic(
    credentials: HTTPBasicCredentials = Depends(security)
) -> str:
    """
    Vérifie credentials HTTP Basic Auth.

    Args:
        credentials: Username + password depuis header Authorization

    Returns:
        Username si authentification réussie

    Raises:
        401 Unauthorized si credentials invalides

    Security:
        - Utilise secrets.compare_digest (timing-attack resistant)
        - DOIT être utilisé avec HTTPS (sinon credentials en clair)
        - Rate limiting recommandé (Phase 2)
    """
    # Timing-attack resistant comparison
    correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        VALID_USERNAME.encode("utf8")
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        VALID_PASSWORD.encode("utf8")
    )

    if not (correct_username and correct_password):
        # Log failed attempt (pour monitoring)
        logger.warning(
            f"Failed authentication attempt: username={credentials.username}"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Log successful auth
    logger.info(f"Successful authentication: username={credentials.username}")

    return credentials.username
```

---

### 2.2 Protect Endpoints

**Modifier:** `backend/routes/slides.py`

```python
from auth.basic import authenticate_basic

@router.get("/", tags=["navigation"])
async def list_slides(
    username: str = Depends(authenticate_basic)  # REQUIS
):
    """
    Liste toutes les lames (PROTÉGÉ par auth).
    """
    slides = scan_slides_directory()
    return {"count": len(slides), "slides": slides}


@router.get("/{slide_id}/info", tags=["visualization"])
async def get_slide_info(
    slide_id: str,
    username: str = Depends(authenticate_basic)  # REQUIS
):
    """
    Métadonnées lame (PROTÉGÉ par auth).
    """
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(404, f"Slide {slide_id} not found")

    metadata = get_slide_metadata(slide_path)
    return metadata


@router.get("/{slide_id}/overview", tags=["visualization"])
async def get_overview(
    slide_id: str,
    username: str = Depends(authenticate_basic)  # REQUIS
):
    """
    Image overview (PROTÉGÉ par auth).
    """
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(404, f"Slide {slide_id} not found")

    img_bytes = get_slide_overview_bytes(slide_path)
    return Response(content=img_bytes, media_type="image/jpeg")


@router.get("/{slide_id}/tiles/{level}/{col}_{row}.jpg", tags=["visualization"])
async def get_tile(
    slide_id: str,
    level: int,
    col: int,
    row: int,
    username: str = Depends(authenticate_basic)  # REQUIS
):
    """
    Tuile JPEG (PROTÉGÉ par auth).
    """
    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(404, f"Slide {slide_id} not found")

    tile_bytes = tile_server.get_tile(slide_path, level, col, row, tile_size=256)

    if tile_bytes is None:
        raise HTTPException(404, "Tile out of bounds")

    return Response(content=tile_bytes, media_type="image/jpeg")
```

**IMPORTANT:** Appliquer à TOUS les endpoints sensibles (browse, dzi.json, etc.)

---

### 2.3 Environment Variables

**Créer:** `backend/.env` (JAMAIS commité)

```bash
# VarunaPoC - Phase 1 Security Configuration
# IMPORTANT: Ne JAMAIS committer ce fichier (.gitignore)

# API Authentication (HTTP Basic - Phase 1 TEMPORAIRE)
API_USERNAME=admin
API_PASSWORD=VarunaSecure2025!ChangeMeInProduction

# NOTES:
# - Changer API_PASSWORD IMMÉDIATEMENT après premier déploiement
# - Password minimum 16 caractères (complexité: majuscules, chiffres, symboles)
# - Rotation tous les 90 jours (recommandation ANSSI)
# - Phase 2: Migration vers OAuth2 + JWT (ce fichier sera supprimé)
```

**Mettre à jour:** `backend/.env.example`

```bash
# VarunaPoC - Environment Variables Template
# Copy to .env and fill with real values

# API Authentication (Phase 1)
API_USERNAME=admin
API_PASSWORD=CHANGE_ME_IMMEDIATELY

# Slides Directory (Docker)
SLIDES_REPOSITORY_PATH=/slides

# CORS Origins (Phase 1 - localhost only)
CORS_ORIGINS=http://localhost:5173,http://localhost:8080
```

**Vérifier:** `backend/.gitignore`

```bash
# Secrets (CRITICAL - NEVER commit)
.env
.env.*
!.env.example

# Logs
*.log
/var/log/varuna/
```

---

### 2.4 Frontend Authentication

**Modifier:** `frontend/src/services/ApiService.js`

```javascript
/**
 * API Service avec HTTP Basic Auth
 *
 * Phase 1: Basic Auth (credentials stockés en mémoire)
 * Phase 2: OAuth2 + JWT (token refresh)
 */

class ApiService {
    constructor() {
        this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        this.credentials = null;  // {username, password}
    }

    /**
     * Authentifie utilisateur (stocke credentials en mémoire).
     */
    login(username, password) {
        this.credentials = {
            username,
            password
        };

        // Test auth
        return this.isAvailable();
    }

    /**
     * Déconnecte utilisateur.
     */
    logout() {
        this.credentials = null;
    }

    /**
     * Vérifie si authentifié.
     */
    isAuthenticated() {
        return this.credentials !== null;
    }

    /**
     * Fetch avec Basic Auth.
     */
    async _fetch(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        // Ajouter Basic Auth header
        if (this.credentials) {
            const encoded = btoa(`${this.credentials.username}:${this.credentials.password}`);
            options.headers = {
                ...options.headers,
                'Authorization': `Basic ${encoded}`
            };
        }

        const response = await fetch(url, options);

        // Si 401 → déconnexion auto
        if (response.status === 401) {
            this.logout();
            throw new Error('Authentication required');
        }

        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        return response;
    }

    // Existing methods (fetchSlides, getSlideInfo, etc.)
    // Modified to use this._fetch instead of fetch
    async fetchSlides() {
        const response = await this._fetch('/api/slides/');
        return response.json();
    }

    async getSlideInfo(slideId) {
        const response = await this._fetch(`/api/slides/${slideId}/info`);
        return response.json();
    }

    // ... autres méthodes
}

export const apiService = new ApiService();
```

**Créer:** `frontend/src/components/LoginPage.js`

```javascript
/**
 * Login Page (Phase 1 - Basic Auth)
 */

export function createLoginPage(onLoginSuccess) {
    const container = document.createElement('div');
    container.className = 'login-page';

    container.innerHTML = `
        <div class="login-card">
            <h1>VarunaPoC</h1>
            <p class="subtitle">Digital Pathology Viewer</p>

            <form id="login-form" class="login-form">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        required
                        autocomplete="username"
                    />
                </div>

                <div class="form-group">
                    <label for="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        required
                        autocomplete="current-password"
                    />
                </div>

                <button type="submit" class="login-button">
                    Sign In
                </button>

                <div id="error-message" class="error-message" style="display: none;"></div>
            </form>

            <p class="security-notice">
                ⚠️ For internal CHU network use only<br>
                Phase 1 PoC - HTTP Basic Authentication
            </p>
        </div>
    `;

    // Handle form submit
    const form = container.querySelector('#login-form');
    const errorMessage = container.querySelector('#error-message');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = form.username.value;
        const password = form.password.value;

        try {
            errorMessage.style.display = 'none';
            form.querySelector('button').disabled = true;
            form.querySelector('button').textContent = 'Signing in...';

            // Login
            await apiService.login(username, password);

            // Success
            onLoginSuccess();

        } catch (err) {
            errorMessage.textContent = err.message || 'Authentication failed';
            errorMessage.style.display = 'block';
            form.querySelector('button').disabled = false;
            form.querySelector('button').textContent = 'Sign In';
        }
    });

    return container;
}
```

**Modifier:** `frontend/src/main.js`

```javascript
import { createLoginPage } from './components/LoginPage.js';

async function init() {
    try {
        console.log('[App] Initializing VarunaPoC...');

        // Check backend availability
        const isAvailable = await apiService.isAvailable();
        if (!isAvailable) {
            throw new Error('Backend is not available');
        }

        // Check authentication
        if (!apiService.isAuthenticated()) {
            showLoginPage();
            return;
        }

        // Setup event listeners
        setupEventListeners();

        // Show home page
        showHomePage();

        console.log('[App] Initialization complete');

    } catch (err) {
        console.error('[App] Init failed:', err);
        showError(err);
    }
}

function showLoginPage() {
    const app = document.querySelector('#app');
    app.className = 'page-login';
    app.innerHTML = '';

    const loginPage = createLoginPage(() => {
        // Login success → reload app
        init();
    });

    app.appendChild(loginPage);
}

// Rest of code...
```

**Ajouter CSS:** `frontend/src/style.css`

```css
/* Login Page */
.login-page {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
    background: white;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    width: 100%;
    max-width: 400px;
}

.login-card h1 {
    margin: 0 0 8px 0;
    font-size: 32px;
    color: #333;
    text-align: center;
}

.login-card .subtitle {
    margin: 0 0 32px 0;
    font-size: 14px;
    color: #666;
    text-align: center;
}

.login-form {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.form-group label {
    font-size: 14px;
    font-weight: 500;
    color: #333;
}

.form-group input {
    padding: 12px;
    font-size: 14px;
    border: 1px solid #ddd;
    border-radius: 6px;
    transition: border-color 0.2s;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
}

.login-button {
    padding: 14px;
    font-size: 16px;
    font-weight: 500;
    color: white;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
}

.login-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.login-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.error-message {
    padding: 12px;
    background: #fee;
    border: 1px solid #fcc;
    border-radius: 6px;
    color: #c33;
    font-size: 14px;
    text-align: center;
}

.security-notice {
    margin: 24px 0 0 0;
    padding: 12px;
    background: #fef9e7;
    border-left: 4px solid #f39c12;
    font-size: 12px;
    color: #666;
    line-height: 1.6;
}
```

---

## 3. HTTPS Local (Self-Signed)

### 3.1 Generate Self-Signed Certificate

```bash
# Créer répertoire certs
mkdir -p certs
cd certs

# Générer certificat self-signed (valide 365 jours)
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout varuna-local.key \
    -out varuna-local.crt \
    -days 365 \
    -subj "/C=BE/ST=Namur/L=Namur/O=CHU UCL Namur/CN=varuna.chu-ucl.local"

# Permissions restrictives
chmod 600 varuna-local.key
chmod 644 varuna-local.crt

cd ..
```

**Note:** Certificat self-signed → Warning navigateur (normal). Phase 2: Certificat CA CHU OU Let's Encrypt.

---

### 3.2 Configure Nginx Reverse Proxy

**Installer Nginx:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install nginx

# Check version
nginx -v  # Minimum 1.18+
```

**Créer config:** `/etc/nginx/sites-available/varuna`

```nginx
# VarunaPoC - Nginx Configuration (Phase 1 - Local HTTPS)

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name varuna.chu-ucl.local localhost;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name varuna.chu-ucl.local localhost;

    # SSL Certificate (self-signed Phase 1)
    ssl_certificate /path/to/VarunaPoC/certs/varuna-local.crt;
    ssl_certificate_key /path/to/VarunaPoC/certs/varuna-local.key;

    # TLS Configuration (Phase 1 - permissif pour compatibilité)
    # Phase 2: TLS 1.3 uniquement + ciphers modernes
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # Security Headers (Phase 1)
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # CSP (Phase 1 - permissif pour OpenSeadragon)
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'" always;

    # Logs
    access_log /var/log/nginx/varuna-access.log;
    error_log /var/log/nginx/varuna-error.log;

    # Backend API (FastAPI)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts (WSI slides peuvent être lentes)
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;

        # Disable buffering (streaming tiles)
        proxy_buffering off;
    }

    # Frontend (Vite build)
    location / {
        root /path/to/VarunaPoC/frontend/dist;
        try_files $uri $uri/ /index.html;

        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Health check (no auth required)
    location /api/health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;  # Pas de log pour health checks
    }
}
```

**Activer site:**

```bash
# Symlink
sudo ln -s /etc/nginx/sites-available/varuna /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

**Ajouter à `/etc/hosts` (pour test local):**

```
127.0.0.1   varuna.chu-ucl.local
```

---

### 3.3 Update Frontend Config

**Modifier:** `frontend/.env.phase1`

```bash
# Phase 1 - Local HTTPS
VITE_API_URL=https://varuna.chu-ucl.local
```

**Build frontend:**

```bash
cd frontend
npm run build

# Vérifier dist/
ls -lah dist/
```

---

### 3.4 Test HTTPS

```bash
# Test certificat
openssl s_client -connect varuna.chu-ucl.local:443 -servername varuna.chu-ucl.local

# Test endpoint (avec Basic Auth)
curl -k -u admin:password https://varuna.chu-ucl.local/api/health

# Expected: {"status": "healthy"}
```

**Browser:** Naviguer vers `https://varuna.chu-ucl.local`
- Warning certificat self-signed → **EXPECTED** (accepter pour test)
- Login page → Enter credentials
- Home page → Success!

---

## 4. Audit Trail

### 4.1 Audit Logger Setup

**Créer:** `backend/services/audit.py`

```python
"""
Audit Trail - Phase 1

Logs tous les accès aux slides (qui, quoi, quand, IP).

Phase 1:
- Fichier texte simple (/var/log/varuna/audit.log)
- Format structuré (parsable)

Phase 3:
- SIEM (Elasticsearch + Kibana)
- Alerting (Prometheus)
"""

import logging
from datetime import datetime
from pathlib import Path

# Créer logger dédié audit (séparé des logs système)
audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

# Handler vers fichier
log_dir = Path("/var/log/varuna")
log_dir.mkdir(parents=True, exist_ok=True)

handler = logging.FileHandler(log_dir / "audit.log")
handler.setFormatter(logging.Formatter(
    '%(asctime)s | %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S.%fZ'  # ISO 8601 UTC
))
audit_logger.addHandler(handler)

# Aussi vers console (dev)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(message)s'))
audit_logger.addHandler(console_handler)


def audit_log(
    action: str,
    username: str,
    resource_type: str = None,
    resource_id: str = None,
    ip_address: str = None,
    status: str = "success",
    details: str = None
):
    """
    Log action dans audit trail.

    Args:
        action: Action effectuée (ex: "slide_view", "slide_download")
        username: Utilisateur authentifié
        resource_type: Type ressource (ex: "slide")
        resource_id: ID ressource (ex: slide_id)
        ip_address: IP client
        status: "success" ou "failed"
        details: Informations additionnelles

    Format:
        timestamp | action=X | user=Y | ip=Z | resource=type/id | status=S | details=D
    """
    parts = [
        f"action={action}",
        f"user={username}",
    ]

    if ip_address:
        parts.append(f"ip={ip_address}")

    if resource_type and resource_id:
        parts.append(f"resource={resource_type}/{resource_id}")

    parts.append(f"status={status}")

    if details:
        parts.append(f"details={details}")

    log_message = " | ".join(parts)
    audit_logger.info(log_message)
```

---

### 4.2 Integrate Audit Logging

**Modifier:** `backend/routes/slides.py`

```python
from services.audit import audit_log
from fastapi import Request

@router.get("/{slide_id}/info", tags=["visualization"])
async def get_slide_info(
    slide_id: str,
    request: Request,  # Pour IP
    username: str = Depends(authenticate_basic)
):
    """
    Métadonnées lame (avec audit log).
    """
    # Audit AVANT accès
    audit_log(
        action="slide_view_info",
        username=username,
        resource_type="slide",
        resource_id=slide_id,
        ip_address=request.client.host
    )

    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        # Audit échec
        audit_log(
            action="slide_view_info",
            username=username,
            resource_type="slide",
            resource_id=slide_id,
            ip_address=request.client.host,
            status="failed",
            details="slide_not_found"
        )
        raise HTTPException(404, f"Slide {slide_id} not found")

    metadata = get_slide_metadata(slide_path)
    return metadata


@router.get("/{slide_id}/overview", tags=["visualization"])
async def get_overview(
    slide_id: str,
    request: Request,
    username: str = Depends(authenticate_basic)
):
    """
    Image overview (avec audit log).
    """
    audit_log(
        action="slide_view_overview",
        username=username,
        resource_type="slide",
        resource_id=slide_id,
        ip_address=request.client.host
    )

    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        audit_log(
            action="slide_view_overview",
            username=username,
            resource_type="slide",
            resource_id=slide_id,
            ip_address=request.client.host,
            status="failed",
            details="slide_not_found"
        )
        raise HTTPException(404, f"Slide {slide_id} not found")

    img_bytes = get_slide_overview_bytes(slide_path)
    return Response(content=img_bytes, media_type="image/jpeg")


@router.get("/{slide_id}/tiles/{level}/{col}_{row}.jpg", tags=["visualization"])
async def get_tile(
    slide_id: str,
    level: int,
    col: int,
    row: int,
    request: Request,
    username: str = Depends(authenticate_basic)
):
    """
    Tuile JPEG (avec audit log - sampling).

    NOTE: Tiles génèrent BEAUCOUP de logs.
    Phase 1: Log seulement première tile par slide/session.
    Phase 3: Agrégation + dashboards.
    """
    # Log première tile uniquement (éviter spam)
    # Phase 3: Implémenter sampling intelligent
    if level == 0 and col == 0 and row == 0:
        audit_log(
            action="slide_view_tiles",
            username=username,
            resource_type="slide",
            resource_id=slide_id,
            ip_address=request.client.host,
            details=f"level={level}"
        )

    slide_path = get_slide_path_by_id(slide_id)
    if not slide_path:
        raise HTTPException(404, f"Slide {slide_id} not found")

    tile_bytes = tile_server.get_tile(slide_path, level, col, row, tile_size=256)

    if tile_bytes is None:
        raise HTTPException(404, "Tile out of bounds")

    return Response(content=tile_bytes, media_type="image/jpeg")
```

---

### 4.3 Log Rotation

**Créer:** `/etc/logrotate.d/varuna`

```bash
/var/log/varuna/*.log {
    daily
    rotate 90           # Garder 90 jours (Phase 1)
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    missingok
    sharedscripts
    postrotate
        # Reload backend pour réouvrir fichier log
        systemctl reload varuna-backend || true
    endscript
}
```

**Test rotation:**

```bash
sudo logrotate -f /etc/logrotate.d/varuna
ls -lh /var/log/varuna/
```

---

## 5. Security Headers

### 5.1 FastAPI Middleware

**Créer:** `backend/middleware/security_headers.py`

```python
"""
Security Headers Middleware

Ajoute headers de sécurité à toutes les réponses.

Refs:
- OWASP Secure Headers Project
- https://owasp.org/www-project-secure-headers/
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour ajouter security headers.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # X-Content-Type-Options (prevent MIME sniffing)
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options (prevent clickjacking)
        response.headers["X-Frame-Options"] = "DENY"

        # X-XSS-Protection (legacy, mais toujours utile)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy (privacy)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content-Security-Policy (XSS protection)
        # Phase 1: Permissif pour OpenSeadragon (unsafe-eval)
        # Phase 2: Renforcer CSP
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'"
        )

        # Permissions-Policy (disable unused features)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )

        return response
```

**Ajouter à `backend/main.py`:**

```python
from middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI(...)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS (already exists)
app.add_middleware(CORSMiddleware, ...)
```

---

### 5.2 Test Headers

```bash
curl -I -k -u admin:password https://varuna.chu-ucl.local/api/health

# Expected headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Content-Security-Policy: ...
```

**Browser DevTools:**
1. Ouvrir `https://varuna.chu-ucl.local`
2. F12 → Network tab
3. Reload page
4. Vérifier headers response

---

## 6. Input Validation

### 6.1 Pydantic Models

**Créer:** `backend/models/api_models.py`

```python
"""
Pydantic Models for API Input Validation

Phase 1: Basic validation (types, ranges)
Phase 2: Business logic validation (permissions, quotas)
"""

from pydantic import BaseModel, Field, validator
import re


class TileRequest(BaseModel):
    """
    Validation pour requête tile.
    """
    slide_id: str = Field(
        ...,
        min_length=12,
        max_length=12,
        description="MD5 hash (12 hex chars)"
    )
    level: int = Field(..., ge=0, le=20, description="Pyramid level (0-20)")
    col: int = Field(..., ge=0, description="Column index")
    row: int = Field(..., ge=0, description="Row index")

    @validator('slide_id')
    def validate_slide_id(cls, v):
        """Vérifie format MD5 hash."""
        if not re.match(r'^[a-f0-9]{12}$', v):
            raise ValueError('slide_id must be 12 hex characters')
        return v


class BrowseRequest(BaseModel):
    """
    Validation pour navigation dossiers.
    """
    path: str = Field(
        default="/",
        description="Relative path from /Slides"
    )

    @validator('path')
    def validate_path(cls, v):
        """Bloque path traversal."""
        # Bloquer sequences dangereuses
        if '..' in v or v.startswith('~') or '\\' in v:
            raise ValueError('Invalid path: traversal attempt detected')

        # Forcer leading slash
        if not v.startswith('/'):
            v = '/' + v

        return v
```

---

### 6.2 Use Models in Routes

**Modifier:** `backend/routes/slides.py`

```python
from models.api_models import TileRequest, BrowseRequest
from pydantic import ValidationError

@router.get("/browse", tags=["navigation"])
async def browse_slides_directory(
    path: str = Query("/", description="Chemin relatif depuis /Slides"),
    username: str = Depends(authenticate_basic)
):
    """
    Navigation hiérarchique (avec validation).
    """
    # Validate input
    try:
        validated = BrowseRequest(path=path)
        path = validated.path
    except ValidationError as e:
        raise HTTPException(400, f"Invalid path: {e}")

    # ... rest of code
```

---

## 7. Vulnerability Scanning

### 7.1 Python Dependencies

```bash
cd backend

# Install scanners
pip install safety pip-audit bandit

# Safety (known CVEs in requirements.txt)
safety check -r requirements.txt --json -o safety-report.json

# pip-audit (alternative)
pip-audit -r requirements.txt

# Bandit (SAST - static code analysis)
bandit -r . -f json -o bandit-report.json

# Review reports
cat safety-report.json | jq
cat bandit-report.json | jq
```

**Fix vulnerabilities:**
- Si CVE critique → Upgrade version
- Si pas de fix dispo → Mitigation (firewall, WAF)
- Documenter dans `docs/SECURITY_VULNERABILITIES.md`

---

### 7.2 JavaScript Dependencies

```bash
cd frontend

# npm audit
npm audit --production --json > npm-audit-report.json

# Review
cat npm-audit-report.json | jq

# Fix automatiques
npm audit fix

# Si breaking changes
npm audit fix --force  # CAUTION: Test after
```

---

### 7.3 Docker Image Scanning (si utilisé)

```bash
# Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy:latest image varuna-backend:latest

# Grype (alternative)
grype varuna-backend:latest
```

---

## 8. Testing & Validation

### 8.1 Security Tests

**Créer:** `tests/security/test_auth.py`

```python
"""
Security Tests - Phase 1 Authentication
"""

import pytest
import requests

BASE_URL = "https://varuna.chu-ucl.local"


def test_no_auth_rejected():
    """Vérifie que endpoints sans auth sont rejetés."""
    response = requests.get(f"{BASE_URL}/api/slides/", verify=False)
    assert response.status_code == 401


def test_invalid_credentials_rejected():
    """Vérifie que credentials invalides sont rejetés."""
    response = requests.get(
        f"{BASE_URL}/api/slides/",
        auth=("wrong", "wrong"),
        verify=False
    )
    assert response.status_code == 401


def test_valid_credentials_accepted():
    """Vérifie que credentials valides sont acceptés."""
    response = requests.get(
        f"{BASE_URL}/api/health",
        auth=("admin", "password"),  # CHANGE
        verify=False
    )
    assert response.status_code == 200


def test_https_enforced():
    """Vérifie que HTTP redirige vers HTTPS."""
    response = requests.get(
        "http://varuna.chu-ucl.local/api/health",
        allow_redirects=False
    )
    assert response.status_code == 301
    assert response.headers['Location'].startswith('https://')
```

**Run tests:**

```bash
cd backend
pytest tests/security/ -v
```

---

### 8.2 Penetration Testing (Manual)

**Test 1: Path Traversal**

```bash
# Tentative accès fichier système
curl -k -u admin:password \
    "https://varuna.chu-ucl.local/api/slides/browse?path=../../etc/passwd"

# Expected: 400 Bad Request (path traversal blocked)
```

**Test 2: XSS**

```bash
# Upload slide avec nom XSS
# (nécessite upload endpoint - Phase 2)
# Expected: Nom échappé (pas d'exécution script)
```

**Test 3: CSRF**

```bash
# Tentative CSRF depuis autre domaine
# Expected: CORS bloque requête
```

---

## 9. Deployment Checklist

### 9.1 Pre-Deployment

- [ ] `.env` créé avec credentials forts (16+ chars)
- [ ] `.env` ignoré par git (vérifier `.gitignore`)
- [ ] HTTPS configuré (certificat + nginx)
- [ ] Audit logs activés (`/var/log/varuna/`)
- [ ] Security headers middleware activé
- [ ] Input validation implémentée (Pydantic)
- [ ] Scan vulnérabilités OK (safety, npm audit, bandit)
- [ ] Tests sécurité passent (pytest)

---

### 9.2 Deployment

```bash
# 1. Build frontend
cd frontend
npm run build

# 2. Deploy frontend to nginx
sudo cp -r dist/* /var/www/varuna/frontend/dist/

# 3. Start backend
cd backend
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --log-level info

# 4. Reload nginx
sudo systemctl reload nginx

# 5. Test endpoints
curl -k -u admin:password https://varuna.chu-ucl.local/api/health
```

---

### 9.3 Post-Deployment

- [ ] Vérifier logs audit (`tail -f /var/log/varuna/audit.log`)
- [ ] Tester login depuis browser
- [ ] Naviguer slides (vérifier auth + audit)
- [ ] Monitoring (CPU, RAM, disk)
- [ ] Backup configuration (nginx, .env, certs)

---

### 9.4 User Training

**À communiquer aux utilisateurs:**

1. **Credentials:**
   - Username: `admin` (temporaire Phase 1)
   - Password: [fourni séparément - PAS email]
   - Changer après premier login (Phase 2 feature)

2. **Accès:**
   - URL: `https://varuna.chu-ucl.local`
   - Réseau interne CHU uniquement
   - Warning certificat self-signed → Accepter (temporaire)

3. **Sécurité:**
   - Ne PAS partager credentials
   - Se déconnecter après utilisation (bouton logout)
   - Signaler comportement anormal (security@chu-ucl.be)

---

## 10. Troubleshooting

### 10.1 Authentication Issues

**Symptôme:** 401 Unauthorized malgré credentials corrects

**Solutions:**
```bash
# 1. Vérifier .env
cat backend/.env | grep API_

# 2. Vérifier backend logs
tail -f /var/log/varuna/backend.log

# 3. Test direct backend (bypass nginx)
curl -u admin:password http://localhost:8000/api/health
```

---

### 10.2 HTTPS Issues

**Symptôme:** ERR_SSL_PROTOCOL_ERROR

**Solutions:**
```bash
# 1. Vérifier certificat
openssl x509 -in certs/varuna-local.crt -text -noout

# 2. Vérifier nginx config
sudo nginx -t

# 3. Vérifier nginx logs
sudo tail -f /var/log/nginx/varuna-error.log
```

---

### 10.3 Audit Logs Missing

**Symptôme:** Fichier audit.log vide

**Solutions:**
```bash
# 1. Vérifier permissions
ls -l /var/log/varuna/

# 2. Créer directory si manquant
sudo mkdir -p /var/log/varuna
sudo chown www-data:www-data /var/log/varuna

# 3. Vérifier code audit.py importé
python3 -c "from services.audit import audit_log; print('OK')"
```

---

## 11. Next Steps (Phase 2)

Après Phase 1 complétée et validée:

1. **Migration OAuth2 + JWT** (1-2 semaines)
   - Keycloak OU Azure AD
   - SSO avec AD CHU
   - Suppression HTTP Basic Auth

2. **RBAC** (1 semaine)
   - User database (PostgreSQL)
   - Rôles: admin, pathologist, resident, researcher
   - Permissions granulaires

3. **MFA** (3-5 jours)
   - TOTP (Google Authenticator)
   - Obligatoire pour admins

4. **Production TLS** (1-2 jours)
   - Certificat CA CHU OU Let's Encrypt
   - TLS 1.3 uniquement

---

**END OF PHASE 1 GUIDE**

**Questions:** security@chu-ucl.be
**Documentation complète:** `docs/SECURITY_ARCHITECTURE.md`
**Status:** Ready for implementation
