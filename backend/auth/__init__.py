"""
Auth Module - OIDC + RBAC + Audit for Hospital-Grade Security

Phase 3.1: Authentication, authorization, and audit trail.

When AUTH_ENABLED=true (default), JWT tokens from the OIDC provider are required.
Set AUTH_ENABLED=false explicitly to disable auth (dev/testing only).

Usage in main.py:
    try:
        from auth import routes as auth_routes, AUTH_ENABLED
        app.include_router(auth_routes.router)
    except ImportError:
        AUTH_ENABLED = False
"""

import os

AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

__all__ = ["AUTH_ENABLED"]
