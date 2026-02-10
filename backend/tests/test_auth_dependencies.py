"""
Tests for auth dependencies - get_current_user(), require_role().

Tests that AUTH_ENABLED=false (default) returns anonymous admin user,
ensuring all existing tests pass without modification.
"""

from unittest.mock import MagicMock, patch

import pytest

from auth.schemas import CurrentUser


class TestCurrentUser:
    """Test CurrentUser schema."""

    def test_anonymous_user(self):
        user = CurrentUser(
            sub="anonymous",
            username="anonymous",
            roles=["ADMIN_TECHNIQUE"],
            is_anonymous=True,
        )
        assert user.sub == "anonymous"
        assert user.primary_role == "ADMIN_TECHNIQUE"
        assert user.is_anonymous is True
        assert user.has_role("ADMIN_TECHNIQUE") is True
        assert user.has_role("MEDECIN") is False

    def test_medecin_user(self):
        user = CurrentUser(
            sub="dr-martin-uuid",
            username="dr.martin",
            email="dr.martin@hospital.local",
            roles=["MEDECIN"],
        )
        assert user.primary_role == "MEDECIN"
        assert user.has_role("MEDECIN") is True
        assert user.has_role("ADMIN_TECHNIQUE") is False
        assert user.has_role("MEDECIN", "ADMIN_TECHNIQUE") is True

    def test_multi_role_user(self):
        user = CurrentUser(
            sub="admin-uuid",
            username="admin",
            roles=["MEDECIN", "ADMIN_TECHNIQUE"],
        )
        assert user.primary_role == "ADMIN_TECHNIQUE"

    def test_no_roles(self):
        user = CurrentUser(sub="empty", username="empty", roles=[])
        assert user.primary_role == "LECTURE_SEULE"


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_anonymous_mode(self):
        """AUTH_ENABLED=false should return anonymous admin."""
        with patch("auth.dependencies.AUTH_ENABLED", False):
            from auth.dependencies import get_current_user

            request = MagicMock()
            user = await get_current_user(request)

            assert user.sub == "anonymous"
            assert user.username == "anonymous"
            assert user.is_anonymous is True
            assert "ADMIN_TECHNIQUE" in user.roles

    @pytest.mark.asyncio
    async def test_auth_enabled_no_token(self):
        """AUTH_ENABLED=true without token should raise 401."""
        with patch("auth.dependencies.AUTH_ENABLED", True):
            from fastapi import HTTPException

            from auth.dependencies import get_current_user

            request = MagicMock()
            request.headers = {}

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request)

            assert exc_info.value.status_code == 401


class TestRequireRole:
    """Test require_role dependency factory."""

    @pytest.mark.asyncio
    async def test_anonymous_mode_always_passes(self):
        """AUTH_ENABLED=false should always pass role check."""
        with patch("auth.dependencies.AUTH_ENABLED", False):
            from auth.dependencies import require_role

            checker = require_role("MEDECIN", "ADMIN_TECHNIQUE")

            # Anonymous user (has ADMIN_TECHNIQUE)
            user = CurrentUser(
                sub="anonymous",
                username="anonymous",
                roles=["ADMIN_TECHNIQUE"],
                is_anonymous=True,
            )

            result = await checker(current_user=user)
            assert result.sub == "anonymous"

    @pytest.mark.asyncio
    async def test_auth_enabled_correct_role(self):
        """User with correct role should pass."""
        with patch("auth.dependencies.AUTH_ENABLED", True):
            from auth.dependencies import require_role

            checker = require_role("MEDECIN", "ADMIN_TECHNIQUE")

            user = CurrentUser(
                sub="dr-martin",
                username="dr.martin",
                roles=["MEDECIN"],
            )

            result = await checker(current_user=user)
            assert result.sub == "dr-martin"

    @pytest.mark.asyncio
    async def test_auth_enabled_wrong_role(self):
        """User without required role should get 403."""
        with patch("auth.dependencies.AUTH_ENABLED", True):
            from fastapi import HTTPException

            from auth.dependencies import require_role

            checker = require_role("MEDECIN", "ADMIN_TECHNIQUE")

            user = CurrentUser(
                sub="viewer",
                username="viewer",
                roles=["LECTURE_SEULE"],
            )

            with pytest.raises(HTTPException) as exc_info:
                await checker(current_user=user)

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_break_glass_bypasses_role(self):
        """Break-glass should bypass role requirements."""
        with patch("auth.dependencies.AUTH_ENABLED", True):
            from auth.dependencies import require_role

            checker = require_role("ADMIN_TECHNIQUE")

            user = CurrentUser(
                sub="dr-martin",
                username="dr.martin",
                roles=["MEDECIN"],
                break_glass_active=True,
            )

            result = await checker(current_user=user)
            assert result.sub == "dr-martin"


class TestExtractRoles:
    """Test role extraction from JWT claims."""

    def test_keycloak_format(self):
        from auth.dependencies import _extract_roles

        claims = {"realm_access": {"roles": ["MEDECIN", "offline_access", "uma_authorization"]}}
        roles = _extract_roles(claims, "realm_access.roles")
        assert roles == ["MEDECIN"]

    def test_azure_ad_format(self):
        from auth.dependencies import _extract_roles

        claims = {"roles": ["ADMIN_TECHNIQUE", "MEDECIN"]}
        roles = _extract_roles(claims, "roles")
        assert set(roles) == {"ADMIN_TECHNIQUE", "MEDECIN"}

    def test_missing_claim(self):
        from auth.dependencies import _extract_roles

        claims = {}
        roles = _extract_roles(claims, "realm_access.roles")
        assert roles == []

    def test_filters_invalid_roles(self):
        from auth.dependencies import _extract_roles

        claims = {"realm_access": {"roles": ["MEDECIN", "INVALID_ROLE", "default-roles-varuna"]}}
        roles = _extract_roles(claims, "realm_access.roles")
        assert roles == ["MEDECIN"]
