"""
Unit Tests for Auth Interface

Tests verify the AuthProvider interface behavior with mock implementations.
These tests do NOT test actual LDAP/AD/SSO integration (see integration tests).

Markers:
- @pytest.mark.auth: Auth module tests
- @pytest.mark.unit: Unit tests (auto-added by conftest.py)
"""

import pytest

from core.interfaces.auth import User


@pytest.mark.auth
@pytest.mark.asyncio
async def test_authenticate_valid_credentials(mock_auth_provider):
    """
    Test authentication with valid credentials.
    """
    user = await mock_auth_provider.authenticate({
        "username": "test_pathologist",
        "password": "password123"  # pragma: allowlist secret
    })

    assert user is not None
    assert user.username == "test_pathologist"
    assert "pathologist" in user.roles


@pytest.mark.auth
@pytest.mark.asyncio
async def test_authenticate_invalid_credentials(mock_auth_provider):
    """
    Test authentication with invalid credentials.
    """
    user = await mock_auth_provider.authenticate({
        "username": "invalid_user",
        "password": "wrong_password"  # pragma: allowlist secret
    })

    assert user is None


@pytest.mark.auth
@pytest.mark.asyncio
async def test_authorize_user_with_permission(mock_auth_provider, mock_user):
    """
    Test authorization for user with permission.
    """
    authorized = await mock_auth_provider.authorize(
        user=mock_user,
        resource="slide:abc123",
        action="read"
    )

    assert authorized is True


@pytest.mark.auth
@pytest.mark.asyncio
async def test_validate_token_valid(mock_auth_provider):
    """
    Test token validation with valid token.
    """
    user = await mock_auth_provider.validate_token("valid_token")

    assert user is not None
    assert user.username == "test_pathologist"


@pytest.mark.auth
@pytest.mark.asyncio
async def test_validate_token_invalid(mock_auth_provider):
    """
    Test token validation with invalid token.
    """
    user = await mock_auth_provider.validate_token("invalid_token")

    assert user is None


@pytest.mark.auth
def test_user_creation():
    """
    Test User object creation with all fields.
    """
    user = User(
        user_id="user123",
        username="pathologist1",
        email="pathologist@chu-ucl.be",
        roles=["pathologist", "admin"],
        metadata={"department": "pathology"}
    )

    assert user.user_id == "user123"
    assert user.username == "pathologist1"
    assert "pathologist" in user.roles
    assert user.metadata["department"] == "pathology"


@pytest.mark.auth
def test_user_creation_minimal():
    """
    Test User object creation with minimal fields.
    """
    user = User(
        user_id="user123",
        username="pathologist1"
    )

    assert user.user_id == "user123"
    assert user.username == "pathologist1"
    assert user.roles == []  # Default empty list
    assert user.metadata == {}  # Default empty dict
