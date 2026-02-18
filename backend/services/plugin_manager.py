"""
Plugin Manager Service

Manages plugin lifecycle: discovery, registration, activation.

Plugins extend VarunaPoC with custom readers, viewers, analyses, and exports.
Each plugin must extend PluginBase and provide a plugin.yaml manifest.

Architecture:
    PluginManager
      ├── register(plugin)    → Add plugin to registry
      ├── unregister(name)    → Remove and deactivate
      ├── discover()          → Scan plugins directory for plugin.yaml manifests
      ├── activate(name)      → Enable a registered plugin
      ├── deactivate(name)    → Disable a registered plugin
      ├── list_plugins()      → List all (optionally filtered by type)
      └── get_plugin(name)    → Retrieve a plugin instance

References:
    - Plugin pattern: https://refactoring.guru/design-patterns/strategy
    - YAML config: https://yaml.org/spec/1.2/spec.html
"""

import importlib
import logging
import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Type

import yaml

logger = logging.getLogger(__name__)


class PluginType(str, Enum):
    """Supported plugin categories."""

    READER = "reader"
    VIEWER = "viewer"
    ANALYSIS = "analysis"
    EXPORT = "export"


@dataclass
class PluginInfo:
    """Metadata describing a plugin."""

    name: str
    version: str
    plugin_type: PluginType
    description: str = ""
    author: str = ""
    enabled: bool = True
    config: Dict = field(default_factory=dict)


class PluginBase(ABC):
    """Base class all plugins must extend."""

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Return plugin metadata."""
        ...

    @abstractmethod
    def activate(self) -> None:
        """Called when the plugin is activated."""
        ...

    @abstractmethod
    def deactivate(self) -> None:
        """Called when the plugin is deactivated."""
        ...


class PluginManager:
    """Manages plugin lifecycle: discovery, registration, activation."""

    def __init__(self, plugins_dir: str = "plugins"):
        self._plugins: Dict[str, PluginBase] = {}
        self._plugin_info: Dict[str, PluginInfo] = {}
        self._plugins_dir = pathlib.Path(plugins_dir)

    def register(self, plugin: PluginBase) -> None:
        """Register a plugin instance."""
        info = plugin.get_info()
        self._plugins[info.name] = plugin
        self._plugin_info[info.name] = info
        logger.info("Registered plugin: %s v%s (%s)", info.name, info.version, info.plugin_type)

    def unregister(self, name: str) -> bool:
        """Unregister a plugin by name. Returns True if found and removed."""
        if name in self._plugins:
            plugin = self._plugins[name]
            try:
                plugin.deactivate()
            except Exception as e:
                logger.warning("Error deactivating plugin %s: %s", name, e)
            del self._plugins[name]
            del self._plugin_info[name]
            return True
        return False

    def discover(self) -> List[PluginInfo]:
        """Auto-discover plugins from the plugins directory.

        Each plugin subdirectory must contain a ``plugin.yaml`` manifest
        with at least ``name``, ``version``, and ``type`` fields.

        Returns:
            List of discovered PluginInfo (not yet registered).
        """
        discovered: List[PluginInfo] = []
        if not self._plugins_dir.exists():
            logger.info("Plugins directory %s does not exist", self._plugins_dir)
            return discovered

        for plugin_dir in self._plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            config_path = plugin_dir / "plugin.yaml"
            if not config_path.exists():
                continue
            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f) or {}
                info = PluginInfo(
                    name=config.get("name", plugin_dir.name),
                    version=config.get("version", "0.0.0"),
                    plugin_type=PluginType(config.get("type", "analysis")),
                    description=config.get("description", ""),
                    author=config.get("author", ""),
                    config=config.get("config", {}),
                )
                discovered.append(info)
            except Exception as e:
                logger.warning("Failed to load plugin from %s: %s", plugin_dir, e)

        return discovered

    def activate(self, name: str) -> bool:
        """Activate a registered plugin. Returns True on success."""
        if name in self._plugins:
            try:
                self._plugins[name].activate()
                self._plugin_info[name].enabled = True
                return True
            except Exception as e:
                logger.error("Failed to activate plugin %s: %s", name, e)
        return False

    def deactivate(self, name: str) -> bool:
        """Deactivate a registered plugin. Returns True on success."""
        if name in self._plugins:
            try:
                self._plugins[name].deactivate()
                self._plugin_info[name].enabled = False
                return True
            except Exception as e:
                logger.error("Failed to deactivate plugin %s: %s", name, e)
        return False

    def list_plugins(self, plugin_type: Optional[PluginType] = None) -> List[PluginInfo]:
        """List registered plugins, optionally filtered by type."""
        plugins = list(self._plugin_info.values())
        if plugin_type:
            plugins = [p for p in plugins if p.plugin_type == plugin_type]
        return plugins

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a plugin instance by name."""
        return self._plugins.get(name)
