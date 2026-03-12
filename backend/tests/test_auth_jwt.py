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
        session = activate_break_glass(
            target_user="test-user",
            issued_by="admin-user",
            issued_by_username="admin",
            reason="Test emergency access",
            duration_minutes=30,
        )
        assert session is not None
        assert session.expires_at is not None

        # Check active
        assert is_break_glass_active("test-user") is True
        assert is_break_glass_active("other-user") is False

        # Deactivate
        assert deactivate_break_glass("test-user") is True
        assert is_break_glass_active("test-user") is False

    def test_expired_session(self):
        from datetime import UTC, datetime, timedelta

        from auth.break_glass import (
            BreakGlassSession,
            _sessions,
            _user_sessions,
            is_break_glass_active,
        )

        # Set an already-expired session
        expired_session = BreakGlassSession(
            id="expired-session-id",
            target_user="expired-user",
            issued_by="admin",
            issued_by_username="admin",
            reason="Test expired session",
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        _sessions["expired-session-id"] = expired_session
        _user_sessions["expired-user"] = ["expired-session-id"]
        assert is_break_glass_active("expired-user") is False

    def test_get_active_sessions(self):
        from auth.break_glass import (
            activate_break_glass,
            deactivate_break_glass,
            get_active_sessions,
        )

        activate_break_glass(
            target_user="session-test-user",
            issued_by="admin-user",
            issued_by_username="admin",
            reason="Test session listing",
            duration_minutes=30,
        )
        sessions = get_active_sessions()
        assert "session-test-user" in sessions

        # Cleanup
        deactivate_break_glass("session-test-user")

    def test_revoke_session(self):
        from auth.break_glass import activate_break_glass, is_break_glass_active, revoke_session

        session = activate_break_glass(
            target_user="revoke-test-user",
            issued_by="admin-user",
            issued_by_username="admin",
            reason="Test revocation workflow",
            duration_minutes=30,
        )
        assert is_break_glass_active("revoke-test-user") is True

        # Revoke by session ID
        revoked = revoke_session(session.id, revoked_by="admin-user")
        assert revoked is not None
        assert revoked.revoked is True
        assert is_break_glass_active("revoke-test-user") is False

    def test_review_session(self):
        from auth.break_glass import activate_break_glass, review_session, revoke_session

        session = activate_break_glass(
            target_user="review-test-user",
            issued_by="admin-user",
            issued_by_username="admin",
            reason="Test review workflow",
            duration_minutes=30,
        )

        # Revoke then review
        revoke_session(session.id, revoked_by="admin-user")
        reviewed = review_session(
            session.id,
            reviewed_by="admin-user",
            notes="Access was justified",
        )
        assert reviewed is not None
        assert reviewed.reviewed is True
        assert reviewed.review_notes == "Access was justified"

    def test_list_all_sessions(self):
        from auth.break_glass import activate_break_glass, list_all_sessions, review_session

        session = activate_break_glass(
            target_user="list-test-user",
            issued_by="admin-user",
            issued_by_username="admin",
            reason="Test listing workflow",
            duration_minutes=30,
        )

        # Should appear in all sessions
        all_sessions = list_all_sessions()
        session_ids = [s["id"] for s in all_sessions]
        assert session.id in session_ids

        # Should appear in pending review
        pending = list_all_sessions(pending_review=True)
        pending_ids = [s["id"] for s in pending]
        assert session.id in pending_ids

        # After review, should not appear in pending
        review_session(session.id, reviewed_by="admin-user")
        pending_after = list_all_sessions(pending_review=True)
        pending_ids_after = [s["id"] for s in pending_after]
        assert session.id not in pending_ids_after
