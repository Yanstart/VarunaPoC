"""
Plugin Loader - Application Lifecycle Integration

Discovers, loads, and tears down plugins that follow the package convention:

    plugins/
        my_plugin/
            manifest.json   - Plugin metadata (name, version, description, author, type)
            __init__.py     - Must expose setup(app) and optionally teardown()

Each plugin is loaded at application startup via setup(app) and unloaded at
shutdown via teardown().  Plugins that fail to load are logged and skipped so
that a broken plugin never prevents the application from starting.

References:
    - FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/
    - importlib: https://docs.python.org/3/library/importlib.html
"""

import importlib
import importlib.util
import json
import logging
import pathlib
import sys
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Registry: plugin_name -> {"meta": {...}, "module": <module>}
_registry: Dict[str, Dict[str, Any]] = {}


def discover_plugins(plugins_dir: str) -> List[Dict[str, Any]]:
    """Scan a directory for plugin packages and return their manifests.

    A valid plugin package is a subdirectory of plugins_dir that contains
    both a ``manifest.json`` file and an ``__init__.py`` file.

    Args:
        plugins_dir: Absolute or relative path to the plugins directory.

    Returns:
        List of manifest dicts.  Each dict is the raw content of manifest.json
        augmented with a ``"_path"`` key pointing to the plugin directory and a
        ``"_name"`` key set to the directory name (used as the canonical plugin
        name when ``name`` is absent from the manifest).

    Technical Notes:
        - Non-recursive: only top-level subdirectories are scanned.
        - Directories without both manifest.json and __init__.py are silently
          skipped.
        - Malformed manifest.json files are logged as warnings and skipped.
        - The directory does not need to exist; an empty list is returned.

    Examples:
        >>> manifests = discover_plugins("./plugins")
        >>> [m["name"] for m in manifests]
        ['my_plugin', 'another_plugin']
    """
    base = pathlib.Path(plugins_dir)
    if not base.exists():
        logger.info("[plugin_loader] plugins directory not found: %s", base)
        return []

    manifests: List[Dict[str, Any]] = []
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        manifest_path = entry / "manifest.json"
        init_path = entry / "__init__.py"
        if not manifest_path.exists() or not init_path.exists():
            continue
        try:
            with manifest_path.open(encoding="utf-8") as fh:
                meta = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("[plugin_loader] could not read manifest %s: %s", manifest_path, exc)
            continue
        meta["_path"] = str(entry)
        meta.setdefault("_name", entry.name)
        meta.setdefault("name", entry.name)
        manifests.append(meta)
        logger.debug("[plugin_loader] discovered plugin: %s", meta["name"])

    logger.info("[plugin_loader] discovered %d plugin(s) in %s", len(manifests), base)
    return manifests


def load_plugin(name: str, app: Any, meta: Dict[str, Any] | None = None) -> bool:
    """Import a plugin package and call its setup(app) function.

    The plugin package is located by looking up the ``_path`` key that
    discover_plugins() adds to the manifest.  The parent directory is
    temporarily added to sys.path so the package can be imported by its
    directory name.

    Args:
        name: Plugin name (must match a previously discovered manifest, or
              meta must be provided explicitly).
        app: FastAPI application instance passed to the plugin's setup().
        meta: Optional manifest dict.  If None, the registry is searched for
              a previously stored manifest (this allows re-loading a plugin
              after unload_plugins()).

    Returns:
        True if the plugin was loaded successfully, False otherwise.

    Raises:
        Nothing — all exceptions are caught and logged so that a single broken
        plugin does not interrupt the startup sequence.

    Technical Notes:
        - Adds the plugin's parent directory to sys.path only during import;
          it is removed afterwards to avoid polluting the module namespace.
        - The plugin module is stored in _registry under its canonical name.
        - Calling load_plugin() on an already-loaded plugin is a no-op (returns
          True immediately).

    Examples:
        >>> success = load_plugin("my_plugin", app, meta=manifest)
        >>> success
        True
    """
    if name in _registry:
        logger.debug("[plugin_loader] plugin already loaded: %s", name)
        return True

    if meta is None:
        logger.error("[plugin_loader] no manifest provided for plugin: %s", name)
        return False

    plugin_path = pathlib.Path(meta.get("_path", ""))
    parent_dir = str(plugin_path.parent)

    # Temporarily add parent directory to sys.path so the package is importable
    added_to_path = False
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        added_to_path = True

    try:
        module = importlib.import_module(plugin_path.name)
    except Exception as exc:
        logger.error("[plugin_loader] failed to import plugin %s: %s", name, exc)
        return False
    finally:
        if added_to_path and parent_dir in sys.path:
            sys.path.remove(parent_dir)

    setup_fn = getattr(module, "setup", None)
    if setup_fn is None:
        logger.warning("[plugin_loader] plugin %s has no setup() function — skipping", name)
        return False

    try:
        setup_fn(app)
    except Exception as exc:
        logger.error("[plugin_loader] setup() failed for plugin %s: %s", name, exc)
        return False

    _registry[name] = {"meta": meta, "module": module}
    logger.info(
        "[plugin_loader] loaded plugin: %s v%s",
        name,
        meta.get("version", "unknown"),
    )
    return True


def unload_plugins() -> None:
    """Call teardown() on every loaded plugin and clear the registry.

    Plugins that do not expose a teardown() function are unregistered without
    error.  Exceptions raised by teardown() are caught and logged so that a
    single broken plugin does not prevent the remaining plugins from being
    cleaned up.

    Technical Notes:
        - Teardown is performed in reverse registration order to respect
          potential inter-plugin dependencies.
        - The global registry is cleared regardless of individual teardown
          failures.

    Examples:
        >>> unload_plugins()  # called during application shutdown
    """
    names = list(reversed(list(_registry.keys())))
    for name in names:
        entry = _registry.get(name)
        if entry is None:
            continue
        module = entry.get("module")
        teardown_fn = getattr(module, "teardown", None)
        if teardown_fn is not None:
            try:
                teardown_fn()
                logger.info("[plugin_loader] unloaded plugin: %s", name)
            except Exception as exc:
                logger.error("[plugin_loader] teardown() failed for plugin %s: %s", name, exc)
        else:
            logger.debug("[plugin_loader] plugin %s has no teardown() — skipping", name)

    _registry.clear()
    logger.info("[plugin_loader] all plugins unloaded")


def get_plugin_registry() -> Dict[str, Dict[str, Any]]:
    """Return a copy of the loaded plugin registry.

    Each key is the canonical plugin name.  Each value is a dict with:

    - ``meta``: the manifest dict (as returned by discover_plugins(), minus
      the ``_path`` and ``_name`` private keys)
    - ``loaded``: True (all entries in the registry are loaded by definition)

    Returns:
        Dict mapping plugin name to its public metadata.

    Technical Notes:
        - Returns a snapshot; modifications to the returned dict do not affect
          the internal registry.
        - Private manifest keys (prefixed with ``_``) are stripped from the
          returned metadata to avoid leaking filesystem paths.

    Examples:
        >>> registry = get_plugin_registry()
        >>> list(registry.keys())
        ['my_plugin']
    """
    result: Dict[str, Dict[str, Any]] = {}
    for name, entry in _registry.items():
        meta = {k: v for k, v in entry["meta"].items() if not k.startswith("_")}
        result[name] = {"meta": meta, "loaded": True}
    return result
