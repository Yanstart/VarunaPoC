"""Integration tests for the ml_models CRUD API (issue #370).

Auth is mocked via `app.dependency_overrides[get_current_user]` so the real
`require_role` logic is exercised end-to-end. The HTTP client is an async
`httpx.AsyncClient` over an `ASGITransport` to avoid the asyncpg event-loop
mismatch that breaks the sync TestClient on multi-request tests.

The whole module is skipped when DATABASE_URL is missing (CI without DB).

NOTE: The current `tests/conftest.py` has a session-scoped autouse fixture
that tries to connect to localhost:5433 — inside the backend container this
hangs because PostgreSQL is exposed only as `db:5432` on the docker network.
Tracked by #371 (chore(tests): fix conftest.py session-scoped fixture for
docker-internal DB). Smoke tests via curl in the dev stack and the 22 unit
tests in tests/unit/test_ml_model_schemas.py (100% coverage of the schema
layer) cover the same surface in the meantime.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

import httpx
import pytest

if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL not set — integration tests require the running stack",
        allow_module_level=True,
    )

from auth.dependencies import get_current_user
from auth.schemas import CurrentUser
from core.tenant import get_current_tenant
from main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _user(roles: list[str], username: str = "tester") -> CurrentUser:
    return CurrentUser(
        sub=f"{username}-sub",
        username=username,
        email=f"{username}@test.local",
        roles=roles,
    )


@asynccontextmanager
async def client_as(user: CurrentUser, tenant: str = "default"):
    """Yield an httpx.AsyncClient with the given user / tenant overrides."""
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_tenant] = lambda: tenant
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_current_tenant, None)


def _minimal_extractor() -> dict:
    return {
        "name": f"test-ext-{uuid4().hex[:8]}",
        "version": "1.0.0",
        "task_type": "feature_extractor",
        "embedding_dim": 512,
    }


def _minimal_classifier() -> dict:
    return {
        "name": f"test-clf-{uuid4().hex[:8]}",
        "version": "1.0.0",
        "task_type": "classifier",
    }


def _admin() -> CurrentUser:
    return _user(["ADMIN_TECHNIQUE"], username="admin")


def _viewer() -> CurrentUser:
    return _user(["LECTURE_SEULE"], username="viewer")


def _medecin() -> CurrentUser:
    return _user(["MEDECIN"], username="medecin")


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_authenticated_viewer_returns_200():
    async with client_as(_viewer()) as client:
        r = await client.get("/api/v1/ml-models")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_create_as_viewer_forbidden():
    async with client_as(_viewer()) as client:
        r = await client.post("/api/v1/ml-models", json=_minimal_classifier())
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_as_medecin_forbidden():
    async with client_as(_medecin()) as client:
        r = await client.post("/api/v1/ml-models", json=_minimal_classifier())
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Create — happy paths + validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_minimal_classifier_201():
    async with client_as(_admin()) as client:
        r = await client.post("/api/v1/ml-models", json=_minimal_classifier())
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["task_type"] == "classifier"
        assert body["tenant_id"] == "default"
        assert body["is_active"] is True
        assert body["is_deployed"] is False
        UUID(body["id"])


@pytest.mark.asyncio
async def test_create_invalid_task_type_422():
    async with client_as(_admin()) as client:
        bad = _minimal_classifier() | {"task_type": "not_a_real_task"}
        r = await client.post("/api/v1/ml-models", json=bad)
        assert r.status_code == 422


@pytest.mark.asyncio
async def test_create_extractor_without_embedding_dim_422():
    async with client_as(_admin()) as client:
        payload = {
            "name": f"bad-ext-{uuid4().hex[:8]}",
            "version": "1",
            "task_type": "feature_extractor",
        }
        r = await client.post("/api/v1/ml-models", json=payload)
        assert r.status_code == 422
        assert "embedding_dim" in r.text.lower()


@pytest.mark.asyncio
async def test_create_license_other_without_description_422():
    async with client_as(_admin()) as client:
        payload = _minimal_classifier() | {"license": "other"}
        r = await client.post("/api/v1/ml-models", json=payload)
        assert r.status_code == 422
        assert "other" in r.text.lower()


@pytest.mark.asyncio
async def test_create_duplicate_returns_409():
    async with client_as(_admin()) as client:
        payload = _minimal_classifier()
        first = await client.post("/api/v1/ml-models", json=payload)
        assert first.status_code == 201, first.text
        second = await client.post("/api/v1/ml-models", json=payload)
        assert second.status_code == 409


# ---------------------------------------------------------------------------
# Tenant guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_global_endpoint_admin_ok():
    """ADMIN_TECHNIQUE can register a model in the global tenant."""
    async with client_as(_admin()) as client:
        r = await client.post("/api/v1/ml-models/global", json=_minimal_classifier())
        assert r.status_code == 201, r.text
        assert r.json()["tenant_id"] == "global"


@pytest.mark.asyncio
async def test_global_endpoint_medecin_forbidden():
    """MEDECIN cannot register a global model."""
    async with client_as(_medecin()) as client:
        r = await client.post("/api/v1/ml-models/global", json=_minimal_classifier())
        assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_payload_tenant_silently_ignored():
    """Even if the payload tries to set tenant_id, it's never honored —
    the schema drops the field at validation time."""
    async with client_as(_admin(), tenant="foo") as client:
        payload = _minimal_classifier() | {"tenant_id": "bar"}
        r = await client.post("/api/v1/ml-models", json=payload)
        assert r.status_code == 201, r.text
        # The caller's tenant wins — the payload's "bar" is ignored
        assert r.json()["tenant_id"] == "foo"


# ---------------------------------------------------------------------------
# Retrieve / list filters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_id_found():
    async with client_as(_admin()) as client:
        created = (await client.post("/api/v1/ml-models", json=_minimal_classifier())).json()
        r = await client.get(f"/api/v1/ml-models/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]


@pytest.mark.asyncio
async def test_get_by_id_not_found_404():
    async with client_as(_admin()) as client:
        r = await client.get(f"/api/v1/ml-models/{uuid4()}")
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_filter_by_task_type():
    async with client_as(_admin()) as client:
        await client.post("/api/v1/ml-models", json=_minimal_extractor())
        await client.post("/api/v1/ml-models", json=_minimal_classifier())
        r = await client.get("/api/v1/ml-models?task_type=feature_extractor")
        assert r.status_code == 200
        assert all(m["task_type"] == "feature_extractor" for m in r.json())


# ---------------------------------------------------------------------------
# PATCH — identity immutable
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_updates_description():
    async with client_as(_admin()) as client:
        created = (await client.post("/api/v1/ml-models", json=_minimal_classifier())).json()
        r = await client.patch(
            f"/api/v1/ml-models/{created['id']}",
            json={"description": "Updated"},
        )
        assert r.status_code == 200
        assert r.json()["description"] == "Updated"


@pytest.mark.asyncio
async def test_patch_silently_ignores_identity_fields():
    """`name` is absent from MLModelUpdate; Pydantic default extras='ignore'."""
    async with client_as(_admin()) as client:
        payload = _minimal_classifier()
        created = (await client.post("/api/v1/ml-models", json=payload)).json()
        r = await client.patch(
            f"/api/v1/ml-models/{created['id']}",
            json={"name": "hacker", "description": "ok"},
        )
        assert r.status_code == 200
        assert r.json()["name"] == payload["name"]


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deploy_sets_deployed_at():
    async with client_as(_admin()) as client:
        created = (await client.post("/api/v1/ml-models", json=_minimal_classifier())).json()
        r = await client.post(f"/api/v1/ml-models/{created['id']}/deploy")
        assert r.status_code == 200
        body = r.json()
        assert body["deployed_at"] is not None
        assert body["is_deployed"] is True


@pytest.mark.asyncio
async def test_deploy_idempotent():
    async with client_as(_admin()) as client:
        created = (await client.post("/api/v1/ml-models", json=_minimal_classifier())).json()
        first = (await client.post(f"/api/v1/ml-models/{created['id']}/deploy")).json()
        second = (await client.post(f"/api/v1/ml-models/{created['id']}/deploy")).json()
        assert first["deployed_at"] == second["deployed_at"]


@pytest.mark.asyncio
async def test_deploy_retired_returns_409():
    async with client_as(_admin()) as client:
        created = (await client.post("/api/v1/ml-models", json=_minimal_classifier())).json()
        assert (await client.post(f"/api/v1/ml-models/{created['id']}/retire")).status_code == 200
        r = await client.post(f"/api/v1/ml-models/{created['id']}/deploy")
        assert r.status_code == 409


@pytest.mark.asyncio
async def test_retire_sets_retired_at():
    async with client_as(_admin()) as client:
        created = (await client.post("/api/v1/ml-models", json=_minimal_classifier())).json()
        r = await client.post(f"/api/v1/ml-models/{created['id']}/retire")
        assert r.status_code == 200
        body = r.json()
        assert body["retired_at"] is not None
        assert body["is_active"] is False


@pytest.mark.asyncio
async def test_delete_alias_of_retire():
    async with client_as(_admin()) as client:
        created = (await client.post("/api/v1/ml-models", json=_minimal_classifier())).json()
        r = await client.delete(f"/api/v1/ml-models/{created['id']}")
        assert r.status_code == 200
        assert r.json()["retired_at"] is not None


@pytest.mark.asyncio
async def test_list_excludes_retired_by_default():
    async with client_as(_admin()) as client:
        created = (await client.post("/api/v1/ml-models", json=_minimal_classifier())).json()
        await client.delete(f"/api/v1/ml-models/{created['id']}")
        r = await client.get("/api/v1/ml-models")
        ids = [m["id"] for m in r.json()]
        assert created["id"] not in ids


@pytest.mark.asyncio
async def test_list_include_retired_flag():
    async with client_as(_admin()) as client:
        created = (await client.post("/api/v1/ml-models", json=_minimal_classifier())).json()
        await client.delete(f"/api/v1/ml-models/{created['id']}")
        r = await client.get("/api/v1/ml-models?include_retired=true")
        ids = [m["id"] for m in r.json()]
        assert created["id"] in ids
