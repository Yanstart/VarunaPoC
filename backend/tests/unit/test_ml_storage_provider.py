"""Sprint 3 — verifies that routes/ml.py resolves slide paths through the
injected StorageProvider, falling back to the legacy slide_scanner only
when no provider is attached.

The actual ML worker / OpenSlide pipeline is heavy; we test the
`_resolve_slide_path` helper directly with the injected provider.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from core.exceptions.storage import SlideNotFoundError
from routes.ml import _resolve_slide_path


@pytest.mark.asyncio
async def test_resolve_uses_storage_provider_when_attached():
    storage = AsyncMock()
    expected = Path("/slides/sample.mrxs")
    storage.get_slide_path = AsyncMock(return_value=expected)
    path = await _resolve_slide_path(storage, "abc123")
    # Path stringification is OS-specific (\ on Windows, / on POSIX);
    # compare via Path equality rather than literal string match.
    assert Path(path) == expected
    storage.get_slide_path.assert_awaited_once_with("abc123")


@pytest.mark.asyncio
async def test_resolve_translates_slide_not_found_to_http_404():
    from fastapi import HTTPException

    storage = AsyncMock()
    storage.get_slide_path = AsyncMock(side_effect=SlideNotFoundError("ghost"))
    with pytest.raises(HTTPException) as exc:
        await _resolve_slide_path(storage, "ghost")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_resolve_falls_back_to_legacy_when_no_provider():
    """When startup wiring failed (storage_provider=None), the legacy
    slide_scanner is used. This keeps the route operational on a degraded
    backend instead of returning 503.
    """
    with patch(
        "routes.ml.get_slide_path_by_id",
        return_value="/slides/legacy.svs",
    ):
        path = await _resolve_slide_path(None, "abc123")
    assert path == "/slides/legacy.svs"


@pytest.mark.asyncio
async def test_resolve_legacy_404_when_scanner_returns_none():
    from fastapi import HTTPException

    with patch("routes.ml.get_slide_path_by_id", return_value=None), pytest.raises(
        HTTPException
    ) as exc:
        await _resolve_slide_path(None, "missing")
    assert exc.value.status_code == 404
