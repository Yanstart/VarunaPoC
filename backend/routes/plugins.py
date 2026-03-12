"""
Plugin Routes - API Endpoints for Plugin Management

Endpoints:
- GET  /api/plugins/         - List registered plugins
- POST /api/plugins/{name}/activate   - Activate a plugin
- POST /api/plugins/{name}/deactivate - Deactivate a plugin
- GET  /api/plugins/discover - Discover available plugins from directory
- GET  /api/plugins/registry - Return plugins loaded by the application lifecycle

References:
- FastAPI: https://fastapi.tiangolo.com/
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from core.plugin_loader import get_plugin_registry
from services.plugin_manager import PluginManager, PluginType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["plugins"])

# Singleton plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create the singleton PluginManager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


@router.get("/")
async def list_plugins(
    plugin_type: Optional[str] = None,
    _current_user: CurrentUser = Depends(get_current_user),
):
    """List all registered plugins, optionally filtered by type.

    Args:
        plugin_type: Filter by plugin type (reader, viewer, analysis, export).

    Returns:
        List of plugin info dicts.
    """
    manager = get_plugin_manager()

    pt = None
    if plugin_type:
        try:
            pt = PluginType(plugin_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid plugin type: {plugin_type}. "
                f"Valid types: {[t.value for t in PluginType]}",
            )

    plugins = manager.list_plugins(plugin_type=pt)
    return {
        "plugins": [
            {
                "name": p.name,
                "version": p.version,
                "type": p.plugin_type.value,
                "description": p.description,
                "author": p.author,
                "enabled": p.enabled,
            }
            for p in plugins
        ],
        "total": len(plugins),
    }


@router.post("/{name}/activate")
async def activate_plugin(
    name: str,
    _current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """Activate a registered plugin by name.

    Args:
        name: Plugin name.

    Returns:
        Activation status.

    Raises:
        404: Plugin not found.
        500: Activation failed.
    """
    manager = get_plugin_manager()

    plugin = manager.get_plugin(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    success = manager.activate(name)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to activate plugin '{name}'")

    return {"status": "activated", "name": name}


@router.post("/{name}/deactivate")
async def deactivate_plugin(
    name: str,
    _current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
):
    """Deactivate a registered plugin by name.

    Args:
        name: Plugin name.

    Returns:
        Deactivation status.

    Raises:
        404: Plugin not found.
        500: Deactivation failed.
    """
    manager = get_plugin_manager()

    plugin = manager.get_plugin(name)
    if plugin is None:
        raise HTTPException(status_code=404, detail=f"Plugin '{name}' not found")

    success = manager.deactivate(name)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate plugin '{name}'")

    return {"status": "deactivated", "name": name}


@router.get("/discover")
async def discover_plugins_endpoint(
    _current_user: CurrentUser = Depends(get_current_user),
):
    """Discover available plugins from the plugins directory.

    Scans the plugins directory for subdirectories containing
    a ``plugin.yaml`` manifest file.

    Returns:
        List of discovered plugin info dicts.
    """
    manager = get_plugin_manager()
    discovered = manager.discover()
    return {
        "discovered": [
            {
                "name": p.name,
                "version": p.version,
                "type": p.plugin_type.value,
                "description": p.description,
                "author": p.author,
            }
            for p in discovered
        ],
        "total": len(discovered),
    }


@router.get("/registry", tags=["plugins"])
async def list_registry(
    _current_user: CurrentUser = Depends(get_current_user),
):
    """Return plugins loaded by the application lifecycle.

    These are plugins discovered from the PLUGINS_DIR directory at startup
    that implement the manifest.json + setup(app) convention (as opposed to
    the legacy plugin.yaml + PluginBase convention).

    Args:
        None.

    Returns:
        Registry dict:
        ```json
        {
            "plugins": {
                "my_plugin": {
                    "meta": {
                        "name": "my_plugin",
                        "version": "1.0.0",
                        "description": "...",
                        "author": "...",
                        "type": "analysis"
                    },
                    "loaded": true
                }
            },
            "total": 1
        }
        ```

    Technical Notes:
        - The registry is populated during application startup via
          core.plugin_loader.discover_plugins() and load_plugin().
        - Plugins that failed to load (missing setup(), import error, etc.)
          are not included.
        - This endpoint reflects the live state: if unload_plugins() was
          called (e.g., during shutdown), the registry will be empty.

    Examples:
        ```
        GET /api/plugins/registry

        Response:
        {
            "plugins": {},
            "total": 0
        }
        ```
    """
    registry = get_plugin_registry()
    return {"plugins": registry, "total": len(registry)}
