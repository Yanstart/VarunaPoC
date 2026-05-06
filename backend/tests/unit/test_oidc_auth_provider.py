"""
Unit tests for OIDCAuthProvider — verifies it satisfies the AuthProvider
Protocol and that the JWT-claims-to-User mapping + RBAC matrix behave.

External dependencies (jwt_validator) are patched at the module boundary;
no live Keycloak required.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest

from auth.auth_provider import OIDCAuthProvider, _user_from_claims, get_auth_provider
from core.exceptions.auth import AuthenticationError
from core.interfaces import AuthProvider
from core.interfaces.auth import User

# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_provider_satisfies_authprovider_protocol():
    """isinstance via @runtime_checkable Protocol (duck typing on methods)."""
    provider = OIDCAuthProvider()
    assert isinstance(provider, AuthProvider)


def test_singleton_returns_same_instance():
    a = get_auth_provider()
    b = get_auth_provider()
    assert a is b


# ---------------------------------------------------------------------------
# JWT claims → User mapping
# ---------------------------------------------------------------------------


def _claims(role_path: str = "realm_access.roles", roles: list | None = None, **extra) -> Dict[str, Any]:
    """Build a Keycloak-shaped claims dict with given roles."""
    base: Dict[str, Any] = {
        "sub": "user-123",
        "preferred_username": "dr.martin",
        "email": "dr.martin@chu-ucl.be",
        "iss": "https://keycloak/realms/varuna",
        "aud": "varuna-backend",
        "exp": 9999999999,
    }
    base.update(extra)
    if role_path == "realm_access.roles":
        base["realm_access"] = {"roles": roles or []}
    else:
        # dotted path support
        parts = role_path.split(".")
        cursor: Any = base
        for p in parts[:-1]:
            cursor.setdefault(p, {})
            cursor = cursor[p]
        cursor[parts[-1]] = roles or []
    return base


def test_user_from_claims_maps_keycloak_shape():
    claims = _claims(roles=["MEDECIN", "ADMIN_TECHNIQUE"])
    user = _user_from_claims(claims)
    assert user.user_id == "user-123"
    assert user.username == "dr.martin"
    assert user.email == "dr.martin@chu-ucl.be"
    assert sorted(user.roles) == ["ADMIN_TECHNIQUE", "MEDECIN"]
    assert user.metadata["issuer"] == "https://keycloak/realms/varuna"


def test_user_from_claims_filters_unknown_roles():
    """Roles outside the project's RBAC vocabulary are dropped."""
    claims = _claims(roles=["MEDECIN", "RANDOM_ROLE", "INFIRMIER"])
    user = _user_from_claims(claims)
    assert sorted(user.roles) == ["INFIRMIER", "MEDECIN"]


def test_user_from_claims_handles_missing_role_path():
    """When the role claim path is absent, the user has no roles."""
    claims = {"sub": "u1", "preferred_username": "u1"}
    user = _user_from_claims(claims)
    assert user.roles == []


# ---------------------------------------------------------------------------
# validate_token + authenticate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_token_returns_user_on_valid_token():
    provider = OIDCAuthProvider()
    fake_claims = _claims(roles=["MEDECIN"])
    with patch(
        "auth.auth_provider._jwt_validate_token",
        new=AsyncMock(return_value=fake_claims),
    ):
        user = await provider.validate_token("any.jwt.string")
    assert isinstance(user, User)
    assert user.username == "dr.martin"
    assert user.roles == ["MEDECIN"]


@pytest.mark.asyncio
async def test_validate_token_raises_authentication_error_on_invalid():
    provider = OIDCAuthProvider()
    with patch(
        "auth.auth_provider._jwt_validate_token",
        new=AsyncMock(side_effect=ValueError("expired signature")),
    ), pytest.raises(AuthenticationError) as exc_info:
        await provider.validate_token("bad.jwt")
    assert "expired signature" in str(exc_info.value)


@pytest.mark.asyncio
async def test_authenticate_with_token_credential_returns_user():
    provider = OIDCAuthProvider()
    fake_claims = _claims(roles=["INFIRMIER"])
    with patch(
        "auth.auth_provider._jwt_validate_token",
        new=AsyncMock(return_value=fake_claims),
    ):
        user = await provider.authenticate({"token": "good.jwt"})
    assert user is not None
    assert user.roles == ["INFIRMIER"]


@pytest.mark.asyncio
async def test_authenticate_returns_none_on_invalid_token():
    provider = OIDCAuthProvider()
    with patch(
        "auth.auth_provider._jwt_validate_token",
        new=AsyncMock(side_effect=ValueError("nope")),
    ):
        result = await provider.authenticate({"token": "bad"})
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_returns_none_when_no_token_in_credentials():
    provider = OIDCAuthProvider()
    assert await provider.authenticate({}) is None
    assert await provider.authenticate({"username": "x", "password": "y"}) is None


# ---------------------------------------------------------------------------
# authorize — RBAC matrix
# ---------------------------------------------------------------------------


def _user(*roles: str) -> User:
    return User(user_id="u1", username="u1", roles=list(roles))


@pytest.mark.asyncio
async def test_authorize_medecin_can_annotate_slide():
    provider = OIDCAuthProvider()
    assert await provider.authorize(_user("MEDECIN"), "slide", "annotate") is True


@pytest.mark.asyncio
async def test_authorize_lecture_seule_cannot_annotate():
    provider = OIDCAuthProvider()
    assert await provider.authorize(_user("LECTURE_SEULE"), "slide", "annotate") is False


@pytest.mark.asyncio
async def test_authorize_lecture_seule_can_read_slide():
    provider = OIDCAuthProvider()
    assert await provider.authorize(_user("LECTURE_SEULE"), "slide", "read") is True


@pytest.mark.asyncio
async def test_authorize_admin_can_train_ml():
    provider = OIDCAuthProvider()
    assert await provider.authorize(_user("ADMIN_TECHNIQUE"), "ml", "train") is True


@pytest.mark.asyncio
async def test_authorize_medecin_cannot_train_ml():
    provider = OIDCAuthProvider()
    assert await provider.authorize(_user("MEDECIN"), "ml", "train") is False


@pytest.mark.asyncio
async def test_authorize_strips_resource_id_suffix():
    """authorize("slide:abc123", "read") evaluates against the "slide" rules."""
    provider = OIDCAuthProvider()
    assert await provider.authorize(_user("MEDECIN"), "slide:abc123", "read") is True


@pytest.mark.asyncio
async def test_authorize_no_roles_denied():
    provider = OIDCAuthProvider()
    assert await provider.authorize(_user(), "slide", "read") is False


@pytest.mark.asyncio
async def test_authorize_unknown_resource_denied():
    provider = OIDCAuthProvider()
    assert await provider.authorize(_user("ADMIN_TECHNIQUE"), "unknown_kind", "read") is False


@pytest.mark.asyncio
async def test_authorize_unknown_action_denied():
    provider = OIDCAuthProvider()
    assert await provider.authorize(_user("ADMIN_TECHNIQUE"), "slide", "unknown_action") is False


# ---------------------------------------------------------------------------
# Stub methods explicitly raise so callers don't get silent failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_token_not_implemented():
    provider = OIDCAuthProvider()
    with pytest.raises(NotImplementedError):
        await provider.refresh_token("refresh.token")


@pytest.mark.asyncio
async def test_logout_not_implemented():
    provider = OIDCAuthProvider()
    with pytest.raises(NotImplementedError):
        await provider.logout(_user("MEDECIN"))


@pytest.mark.asyncio
async def test_get_user_by_id_not_implemented():
    provider = OIDCAuthProvider()
    with pytest.raises(NotImplementedError):
        await provider.get_user_by_id("user-123")
