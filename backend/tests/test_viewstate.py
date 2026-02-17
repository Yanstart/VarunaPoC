"""
ViewState Tests

Tests for N-dimensional view state model and API endpoint.
"""

import pytest


@pytest.mark.unit
def test_ndviewstate_defaults():
    """NDViewState has correct default values."""
    from services.nd_viewstate import NDViewState

    state = NDViewState()
    assert state.x == 0
    assert state.y == 0
    assert state.z == 0
    assert state.c == 0
    assert state.t == 0
    assert state.level == 0
    assert state.zoom == 1.0
    assert state.z_max == 1
    assert state.c_max == 1
    assert state.t_max == 1
    assert state.level_max == 1


@pytest.mark.unit
def test_ndviewstate_set_z_clamped():
    """set_z clamps values to valid range [0, z_max-1]."""
    from services.nd_viewstate import NDViewState

    state = NDViewState(z_max=5)
    state.set_z(3)
    assert state.z == 3

    state.set_z(10)
    assert state.z == 4  # clamped to z_max - 1

    state.set_z(-1)
    assert state.z == 0  # clamped to 0


@pytest.mark.unit
def test_ndviewstate_set_channel_clamped():
    """set_channel clamps values to valid range [0, c_max-1]."""
    from services.nd_viewstate import NDViewState

    state = NDViewState(c_max=3)
    state.set_channel(2)
    assert state.c == 2

    state.set_channel(5)
    assert state.c == 2  # clamped to c_max - 1

    state.set_channel(-1)
    assert state.c == 0  # clamped to 0


@pytest.mark.unit
def test_ndviewstate_set_timepoint_clamped():
    """set_timepoint clamps values to valid range [0, t_max-1]."""
    from services.nd_viewstate import NDViewState

    state = NDViewState(t_max=10)
    state.set_timepoint(5)
    assert state.t == 5

    state.set_timepoint(100)
    assert state.t == 9  # clamped to t_max - 1

    state.set_timepoint(-3)
    assert state.t == 0  # clamped to 0


@pytest.mark.unit
def test_ndviewstate_to_dict():
    """to_dict returns all fields as a dictionary."""
    from services.nd_viewstate import NDViewState

    state = NDViewState(x=10, y=20, z=1, c=2, t=3, level=4, zoom=2.5)
    d = state.to_dict()
    assert d["x"] == 10
    assert d["y"] == 20
    assert d["z"] == 1
    assert d["c"] == 2
    assert d["t"] == 3
    assert d["level"] == 4
    assert d["zoom"] == 2.5
    assert d["z_max"] == 1
    assert d["c_max"] == 1
    assert d["t_max"] == 1
    assert d["level_max"] == 1


@pytest.mark.unit
def test_ndviewstate_from_dict():
    """from_dict reconstructs an NDViewState from a dictionary."""
    from services.nd_viewstate import NDViewState

    data = {
        "x": 5,
        "y": 10,
        "z": 2,
        "c": 1,
        "t": 0,
        "level": 3,
        "zoom": 4.0,
        "z_max": 8,
        "c_max": 4,
        "t_max": 1,
        "level_max": 10,
    }
    state = NDViewState.from_dict(data)
    assert state.x == 5
    assert state.y == 10
    assert state.z == 2
    assert state.c == 1
    assert state.t == 0
    assert state.level == 3
    assert state.zoom == 4.0
    assert state.z_max == 8
    assert state.c_max == 4
    assert state.t_max == 1
    assert state.level_max == 10


@pytest.mark.unit
def test_ndviewstate_from_dict_ignores_extra_keys():
    """from_dict ignores keys not in the dataclass."""
    from services.nd_viewstate import NDViewState

    data = {"x": 1, "y": 2, "unknown_field": "ignored"}
    state = NDViewState.from_dict(data)
    assert state.x == 1
    assert state.y == 2


@pytest.mark.unit
def test_ndviewstate_from_slide_metadata():
    """from_slide_metadata creates state from slide metadata dict."""
    from services.nd_viewstate import NDViewState

    metadata = {
        "z_levels": 20,
        "channels": 4,
        "timepoints": 5,
        "level_count": 9,
    }
    state = NDViewState.from_slide_metadata(metadata)
    assert state.z_max == 20
    assert state.c_max == 4
    assert state.t_max == 5
    assert state.level_max == 9
    # Positional defaults
    assert state.x == 0
    assert state.z == 0


@pytest.mark.unit
def test_ndviewstate_from_slide_metadata_defaults():
    """from_slide_metadata uses defaults for missing metadata keys."""
    from services.nd_viewstate import NDViewState

    state = NDViewState.from_slide_metadata({})
    assert state.z_max == 1
    assert state.c_max == 1
    assert state.t_max == 1
    assert state.level_max == 1


@pytest.mark.unit
def test_viewstate_endpoint(client):
    """GET /api/viewstate/{slide_id} returns default view state."""
    response = client.get("/api/viewstate/test-slide-123")
    assert response.status_code == 200

    data = response.json()
    assert data["x"] == 0
    assert data["y"] == 0
    assert data["z"] == 0
    assert data["c"] == 0
    assert data["t"] == 0
    assert data["level"] == 0
    assert data["zoom"] == 1.0
    assert data["z_max"] == 1
    assert data["c_max"] == 1
    assert data["t_max"] == 1
    assert data["level_max"] == 1
