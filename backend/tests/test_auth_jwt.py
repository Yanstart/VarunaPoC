"""
Tests for JWT validation and OIDC discovery.

Tests with mock JWKS to verify token validation logic
without requiring a running Keycloak instance.
"""

from auth.config import OIDCConfig, get_oidc_config
from auth.oidc import clear_cache, find_key_by_kid


class TestOIDCConfig:
    """Test OIDC configuration."""

    def test_default_config(self):
        config = get_oidc_config()
        assert config.client_id == "varuna-viewer"
        assert "RS256" in config.algorithms
        assert "ES256" in config.algorithms

    def test_discovery_url(self):
        config = OIDCConfig(issuer_url="http://localhost:8180/realms/varuna")
        assert (
            config.discovery_url
            == "http://localhost:8180/realms/varuna/.well-known/openid-configuration"
        )

    def test_is_configured(self):
        config = OIDCConfig(issuer_url="http://localhost:8180/realms/varuna", client_id="test")
        assert config.is_configured is True

        empty = OIDCConfig(issuer_url="", client_id="")
        assert empty.is_configured is False


class TestFindKeyByKid:
    """Test JWKS key lookup."""

    def test_find_existing_key(self):
        jwks = {
            "keys": [
                {"kid": "key-1", "kty": "RSA", "n": "abc"},
                {"kid": "key-2", "kty": "RSA", "n": "def"},
            ]
        }
        key = find_key_by_kid(jwks, "key-2")
        assert key is not None
        assert key["n"] == "def"

    def test_key_not_found(self):
        jwks = {"keys": [{"kid": "key-1"}]}
        key = find_key_by_kid(jwks, "nonexistent")
        assert key is None

    def test_empty_jwks(self):
        key = find_key_by_kid({"keys": []}, "any-kid")
        assert key is None

    def test_no_keys_field(self):
        key = find_key_by_kid({}, "any-kid")
        assert key is None


class TestCacheManagement:
    """Test OIDC cache operations."""

    def test_clear_cache(self):
        """clear_cache should not raise."""
        clear_cache()


class TestBreakGlass:
    """Test break-glass in-memory sessions."""

    def test_activate_and_check(self):
        from auth.break_glass import (
            activate_break_glass,
            deactivate_break_glass,
            is_break_glass_active,
        )

        # Activate for user
        expires = activate_break_glass("test-user", duration_minutes=30)
        assert expires is not None

        # Check active
        assert is_break_glass_active("test-user") is True
        assert is_break_glass_active("other-user") is False

        # Deactivate
        assert deactivate_break_glass("test-user") is True
        assert is_break_glass_active("test-user") is False

    def test_expired_session(self):
        from datetime import UTC, datetime, timedelta

        from auth.break_glass import _active_sessions, is_break_glass_active

        # Set an already-expired session
        _active_sessions["expired-user"] = datetime.now(UTC) - timedelta(minutes=1)
        assert is_break_glass_active("expired-user") is False
        assert "expired-user" not in _active_sessions

    def test_get_active_sessions(self):
        from auth.break_glass import (
            activate_break_glass,
            deactivate_break_glass,
            get_active_sessions,
        )

        activate_break_glass("session-test-user", 30)
        sessions = get_active_sessions()
        assert "session-test-user" in sessions

        # Cleanup
        deactivate_break_glass("session-test-user")
