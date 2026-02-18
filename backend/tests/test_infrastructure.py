"""
Tests for infrastructure services: PluginManager, EmbeddingService, DICOMExportService.

Covers:
  - PluginManager: register, unregister, discover, activate/deactivate, filter
  - EmbeddingService: extract, invalid model, list models, determinism
  - DICOMExportService: mock export, UID generation
"""

import pytest
import yaml

from services.dicom_export import DICOMExportResult, DICOMExportService
from services.embeddings import EmbeddingResult, EmbeddingService
from services.plugin_manager import (
    PluginBase,
    PluginInfo,
    PluginManager,
    PluginType,
)

# ============================================================================
# HELPERS
# ============================================================================


class DummyPlugin(PluginBase):
    """A minimal plugin for testing."""

    def __init__(self, name: str = "test-plugin", plugin_type: PluginType = PluginType.ANALYSIS):
        self._name = name
        self._type = plugin_type
        self.activated = False
        self.deactivated = False

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name=self._name,
            version="1.0.0",
            plugin_type=self._type,
            description="A test plugin",
            author="Test Author",
        )

    def activate(self) -> None:
        self.activated = True

    def deactivate(self) -> None:
        self.deactivated = True


class FailingPlugin(PluginBase):
    """A plugin that raises on activate/deactivate."""

    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="failing-plugin",
            version="0.1.0",
            plugin_type=PluginType.ANALYSIS,
        )

    def activate(self) -> None:
        msg = "Activation failed"
        raise RuntimeError(msg)

    def deactivate(self) -> None:
        msg = "Deactivation failed"
        raise RuntimeError(msg)


# ============================================================================
# PLUGIN MANAGER TESTS
# ============================================================================


class TestPluginManager:
    """PluginManager unit tests."""

    def test_register_and_list(self):
        """Register a plugin and verify it appears in list."""
        manager = PluginManager()
        plugin = DummyPlugin()
        manager.register(plugin)

        plugins = manager.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].name == "test-plugin"
        assert plugins[0].version == "1.0.0"
        assert plugins[0].plugin_type == PluginType.ANALYSIS

    def test_unregister_removes_plugin(self):
        """Unregister removes the plugin and calls deactivate."""
        manager = PluginManager()
        plugin = DummyPlugin()
        manager.register(plugin)

        result = manager.unregister("test-plugin")
        assert result is True
        assert manager.list_plugins() == []
        assert plugin.deactivated is True

    def test_unregister_nonexistent_returns_false(self):
        """Unregistering a non-existent plugin returns False."""
        manager = PluginManager()
        assert manager.unregister("does-not-exist") is False

    def test_discover_empty_directory(self, tmp_path):
        """Discover from empty directory returns empty list."""
        manager = PluginManager(plugins_dir=str(tmp_path))
        discovered = manager.discover()
        assert discovered == []

    def test_discover_nonexistent_directory(self):
        """Discover from non-existent directory returns empty list."""
        manager = PluginManager(plugins_dir="/nonexistent/path/plugins")
        discovered = manager.discover()
        assert discovered == []

    def test_discover_finds_plugin_yaml(self, tmp_path):
        """Discover finds plugins with valid plugin.yaml manifests."""
        # Create a plugin directory with plugin.yaml
        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()
        config = {
            "name": "my-awesome-plugin",
            "version": "2.1.0",
            "type": "reader",
            "description": "Reads custom format",
            "author": "Jane Doe",
            "config": {"max_threads": 4},
        }
        with (plugin_dir / "plugin.yaml").open("w") as f:
            yaml.dump(config, f)

        # Create another directory without plugin.yaml (should be skipped)
        (tmp_path / "not_a_plugin").mkdir()

        manager = PluginManager(plugins_dir=str(tmp_path))
        discovered = manager.discover()

        assert len(discovered) == 1
        info = discovered[0]
        assert info.name == "my-awesome-plugin"
        assert info.version == "2.1.0"
        assert info.plugin_type == PluginType.READER
        assert info.description == "Reads custom format"
        assert info.author == "Jane Doe"
        assert info.config == {"max_threads": 4}

    def test_activate_deactivate_lifecycle(self):
        """Activate and deactivate a registered plugin."""
        manager = PluginManager()
        plugin = DummyPlugin()
        manager.register(plugin)

        # Activate
        assert manager.activate("test-plugin") is True
        assert plugin.activated is True
        info = manager.list_plugins()[0]
        assert info.enabled is True

        # Deactivate
        assert manager.deactivate("test-plugin") is True
        assert plugin.deactivated is True
        info = manager.list_plugins()[0]
        assert info.enabled is False

    def test_activate_nonexistent_returns_false(self):
        """Activating a non-existent plugin returns False."""
        manager = PluginManager()
        assert manager.activate("ghost") is False

    def test_deactivate_nonexistent_returns_false(self):
        """Deactivating a non-existent plugin returns False."""
        manager = PluginManager()
        assert manager.deactivate("ghost") is False

    def test_activate_failing_plugin_returns_false(self):
        """Activating a plugin that raises returns False."""
        manager = PluginManager()
        plugin = FailingPlugin()
        manager.register(plugin)
        assert manager.activate("failing-plugin") is False

    def test_deactivate_failing_plugin_returns_false(self):
        """Deactivating a plugin that raises returns False."""
        manager = PluginManager()
        plugin = FailingPlugin()
        manager.register(plugin)
        assert manager.deactivate("failing-plugin") is False

    def test_filter_by_plugin_type(self):
        """list_plugins filters correctly by plugin_type."""
        manager = PluginManager()
        manager.register(DummyPlugin("reader-1", PluginType.READER))
        manager.register(DummyPlugin("analysis-1", PluginType.ANALYSIS))
        manager.register(DummyPlugin("export-1", PluginType.EXPORT))

        readers = manager.list_plugins(plugin_type=PluginType.READER)
        assert len(readers) == 1
        assert readers[0].name == "reader-1"

        exports = manager.list_plugins(plugin_type=PluginType.EXPORT)
        assert len(exports) == 1
        assert exports[0].name == "export-1"

        all_plugins = manager.list_plugins()
        assert len(all_plugins) == 3

    def test_get_plugin(self):
        """get_plugin returns the registered plugin instance."""
        manager = PluginManager()
        plugin = DummyPlugin()
        manager.register(plugin)

        assert manager.get_plugin("test-plugin") is plugin
        assert manager.get_plugin("nonexistent") is None


# ============================================================================
# EMBEDDING SERVICE TESTS
# ============================================================================


class TestEmbeddingService:
    """EmbeddingService unit tests."""

    def test_extract_valid_model(self):
        """Extract with a valid model returns a proper result."""
        service = EmbeddingService()
        result = service.extract_embeddings(slide_id="slide_001", model="uni")

        assert isinstance(result, EmbeddingResult)
        assert result.slide_id == "slide_001"
        assert result.model == "uni"
        assert result.dimensions == 1024
        assert 50 <= result.embeddings_count <= 249
        assert result.processing_time_ms >= 0

    def test_extract_invalid_model_raises(self):
        """Extract with an invalid model raises ValueError."""
        service = EmbeddingService()
        with pytest.raises(ValueError, match="Unknown model"):
            service.extract_embeddings(slide_id="slide_001", model="nonexistent_model")

    def test_list_models_returns_all(self):
        """list_models returns all supported models."""
        service = EmbeddingService()
        models = service.list_models()

        assert "uni" in models
        assert "phikon" in models
        assert "virchow" in models
        assert "ctranspath" in models
        assert len(models) == 4

        # Verify each model has required keys
        for _name, info in models.items():
            assert "dim" in info
            assert "tile_px" in info
            assert "description" in info

    def test_mock_mode_is_deterministic(self):
        """Same slide_id and model produce same embeddings_count."""
        service = EmbeddingService()

        result1 = service.extract_embeddings(slide_id="slide_abc", model="uni")
        result2 = service.extract_embeddings(slide_id="slide_abc", model="uni")

        assert result1.embeddings_count == result2.embeddings_count
        assert result1.dimensions == result2.dimensions

    def test_different_slides_may_differ(self):
        """Different slide_ids produce (likely) different counts."""
        service = EmbeddingService()

        result1 = service.extract_embeddings(slide_id="slide_aaa", model="uni")
        result2 = service.extract_embeddings(slide_id="slide_zzz", model="uni")

        # They are deterministic but based on different hashes,
        # so very likely different (not guaranteed but extremely likely)
        # We just verify both are valid
        assert 50 <= result1.embeddings_count <= 249
        assert 50 <= result2.embeddings_count <= 249

    def test_extract_all_models(self):
        """Extraction works for every supported model."""
        service = EmbeddingService()
        for model_name, model_info in service.SUPPORTED_MODELS.items():
            result = service.extract_embeddings(slide_id="test_slide", model=model_name)
            assert result.dimensions == model_info["dim"]
            assert result.model == model_name


# ============================================================================
# DICOM EXPORT SERVICE TESTS
# ============================================================================


class TestDICOMExportService:
    """DICOMExportService unit tests."""

    def test_export_mock_mode(self):
        """Export in mock mode returns status='mock'."""
        service = DICOMExportService()
        result = service.export(slide_id="slide_001")

        assert isinstance(result, DICOMExportResult)
        assert result.slide_id == "slide_001"
        assert result.status == "mock"
        assert result.processing_time_ms >= 0

    def test_export_generates_valid_uid(self):
        """Export generates a UID with valid DICOM format (2.25. prefix)."""
        service = DICOMExportService()
        result = service.export(slide_id="test_slide_123")

        assert result.dicom_uid.startswith("2.25.")
        assert len(result.dicom_uid) <= 64  # DICOM UID max length

    def test_export_uid_is_deterministic(self):
        """Same slide_id produces same DICOM UID."""
        service = DICOMExportService()
        result1 = service.export(slide_id="deterministic_test")
        result2 = service.export(slide_id="deterministic_test")

        assert result1.dicom_uid == result2.dicom_uid

    def test_export_different_slides_different_uids(self):
        """Different slide_ids produce different DICOM UIDs."""
        service = DICOMExportService()
        result1 = service.export(slide_id="slide_aaa")
        result2 = service.export(slide_id="slide_bbb")

        assert result1.dicom_uid != result2.dicom_uid

    def test_get_export_status(self):
        """get_export_status returns a status dict."""
        service = DICOMExportService()
        status = service.get_export_status("slide_001")

        assert status["slide_id"] == "slide_001"
        assert "status" in status
