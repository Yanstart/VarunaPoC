"""
Slides API Tests

Tests pour les endpoints de détection et navigation de lames.

Note: Ces tests nécessitent OpenSlide installé sur le système.
Les tests utilisent des mocks pour éviter de dépendre de vraies lames.
"""

import pytest


@pytest.mark.unit
def test_browse_endpoint_requires_path(client):
    """
    Test GET /api/slides/browse sans paramètre path.

    Devrait retourner une erreur 400 ou la racine.
    """
    response = client.get("/api/slides/browse")

    # Endpoint should handle missing path gracefully
    assert response.status_code in [200, 400, 422]


@pytest.mark.unit
def test_slides_list_endpoint(client):
    """
    Test GET /api/slides/ - Liste complète des lames.

    Note: Retourne liste vide si /Slides n'existe pas (normal en CI).
    """
    response = client.get("/api/slides/")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    # Liste peut être vide si /Slides n'existe pas


@pytest.mark.integration
@pytest.mark.skip(reason="Requires /Slides directory with test slides")
def test_browse_endpoint_with_valid_path(client):
    """
    Test GET /api/slides/browse avec un chemin valide.

    Ce test est skippé par défaut car il nécessite /Slides.
    Pour l'exécuter: pytest -m integration
    """
    response = client.get("/api/slides/browse", params={"path": "/Slides"})

    assert response.status_code == 200

    data = response.json()
    assert "folders" in data
    assert "slides" in data
    assert isinstance(data["folders"], list)
    assert isinstance(data["slides"], list)


@pytest.mark.integration
@pytest.mark.skip(reason="Requires test slide file")
def test_slide_info_endpoint(client):
    """
    Test GET /api/slides/{id}/info.

    Ce test nécessite une vraie lame dans /Slides.
    """
    # Replace with actual slide ID from test fixtures
    slide_id = "test_slide_001"

    response = client.get(f"/api/slides/{slide_id}/info")

    assert response.status_code == 200

    data = response.json()
    assert "slide_id" in data
    assert "format" in data
    assert "dimensions" in data


@pytest.mark.integration
@pytest.mark.skip(reason="Requires test slide file")
def test_slide_overview_endpoint(client):
    """
    Test GET /api/slides/{id}/overview.

    Retourne une image JPEG de l'aperçu.
    """
    slide_id = "test_slide_001"

    response = client.get(f"/api/slides/{slide_id}/overview")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


@pytest.mark.unit
def test_invalid_slide_id(client):
    """
    Test avec un slide_id inexistant.

    Devrait retourner 404.
    """
    response = client.get("/api/slides/nonexistent_slide_12345/info")

    assert response.status_code == 404


@pytest.mark.unit
def test_api_version_consistency(client):
    """
    Test que la version API est cohérente partout.

    Vérifie main.py, OpenAPI schema, et root endpoint.
    """
    # Root endpoint
    root_response = client.get("/")
    assert root_response.json()["version"] == "1.7.0"

    # OpenAPI schema
    openapi_response = client.get("/openapi.json")
    assert openapi_response.json()["info"]["version"] == "1.7.0"
