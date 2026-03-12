"""
Capabilities Route - Feature Flag Discovery Endpoint

Exposes which optional features are enabled on this backend instance,
allowing the frontend to adapt its UI accordingly.

Endpoints:
- GET /api/capabilities - Returns all feature flags and their status

References:
- Feature flags pattern: https://martinfowler.com/articles/feature-toggles.html
"""

from fastapi import APIRouter

from core.feature_flags import feature_registry

router = APIRouter(prefix="", tags=["capabilities"])


@router.get("/capabilities")
async def get_capabilities():
    """
    Return all registered feature flags and their enabled/disabled status.

    No authentication required -- capabilities are public so the frontend
    can discover available features before any user interaction.

    Returns:
        Dict of feature names to boolean enabled status.
        Example: {"annotations": true, "auth": false, "fhir": true, ...}
    """
    return feature_registry.get_all()
