"""
Tests for the feature flag registry and /api/capabilities endpoint.

Covers:
- FeatureRegistry singleton behaviour
- register / is_enabled / get_all contract
- GET /api/capabilities returns the registry contents
"""

from core.feature_flags import FeatureRegistry, feature_registry

# ── Unit tests for FeatureRegistry ─────────────────────────────────────


class TestFeatureRegistry:
    """Unit tests for the FeatureRegistry class."""

    def _make_registry(self):
        """Create a fresh registry instance for isolation."""
        reg = FeatureRegistry.__new__(FeatureRegistry)
        reg._features = {}
        return reg

    def test_register_and_get(self):
        reg = self._make_registry()
        reg.register("foo", True)
        reg.register("bar", False)
        assert reg.get_all() == {"foo": True, "bar": False}

    def test_is_enabled_registered(self):
        reg = self._make_registry()
        reg.register("on", True)
        reg.register("off", False)
        assert reg.is_enabled("on") is True
        assert reg.is_enabled("off") is False

    def test_is_enabled_unknown_returns_false(self):
        reg = self._make_registry()
        assert reg.is_enabled("nonexistent") is False

    def test_get_all_returns_copy(self):
        reg = self._make_registry()
        reg.register("x", True)
        result = reg.get_all()
        result["x"] = False  # mutate the copy
        assert reg.is_enabled("x") is True  # original unchanged

    def test_reset_clears_features(self):
        reg = self._make_registry()
        reg.register("a", True)
        reg.reset()
        assert reg.get_all() == {}

    def test_singleton_identity(self):
        a = FeatureRegistry()
        b = FeatureRegistry()
        assert a is b

    def test_module_level_instance_is_singleton(self):
        assert feature_registry is FeatureRegistry()


# ── Integration test for /api/capabilities ─────────────────────────────


def test_capabilities_endpoint(client):
    """GET /api/capabilities returns feature flags as JSON dict."""
    response = client.get("/api/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    # At minimum, the core flags should be present
    for key in ("annotations", "auth", "fhir", "quality", "monitoring", "ml"):
        assert key in data
        assert isinstance(data[key], bool)
