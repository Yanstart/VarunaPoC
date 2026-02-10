"""
Auth Module - OIDC + RBAC + Audit for Hospital-Grade Security

Phase 3.1: Authentication, authorization, and audit trail.

When AUTH_ENABLED=false (default), all routes work as before with an anonymous
admin user. When AUTH_ENABLED=true, JWT tokens from the OIDC provider are required.

Usage in main.py:
    try:
        from auth import routes as auth_routes, AUTH_ENABLED
        app.include_router(auth_routes.router)
    except ImportError:
        AUTH_ENABLED = False
"""

import os

AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"

__all__ = ["AUTH_ENABLED"]
