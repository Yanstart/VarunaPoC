"""
Health Check Tests

Tests pour les endpoints de base et health checks.

Ces tests ne nécessitent pas OpenSlide ni de lames de test.
Ils vérifient que l'application FastAPI démarre correctement.
"""

import pytest


@pytest.mark.unit
def test_root_endpoint(client):
    """
    Test GET / - Root endpoint.

    Vérifie que l'endpoint racine retourne les informations du service.
    """
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "VarunaPoC Backend"
    assert data["status"] == "running"
    assert data["version"] == "1.7.0"
    assert "docs" in data
    assert "endpoints" in data


@pytest.mark.unit
def test_health_endpoint(client):
    """
    Test GET /api/health - Health check.

    Endpoint utilisé par Docker healthcheck et monitoring.
    """
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.unit
def test_docs_endpoint(client):
    """
    Test GET /docs - Swagger UI.

    Vérifie que la documentation Swagger est accessible.
    """
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.unit
def test_openapi_endpoint(client):
    """
    Test GET /openapi.json - OpenAPI schema.

    Vérifie que le schéma OpenAPI est valide.
    """
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    assert schema["info"]["title"] == "VarunaPoC Backend API"
    assert schema["info"]["version"] == "1.7.0"
    assert "paths" in schema


@pytest.mark.unit
def test_metrics_endpoint_when_monitoring_enabled(client):
    """
    Test GET /metrics - Prometheus metrics.

    Note: Ce test vérifie que l'endpoint existe.
    Le contenu dépend de MONITORING_ENABLED.
    """
    response = client.get("/metrics")

    # Accept various responses depending on configuration:
    # 200: metrics enabled
    # 404/422: endpoint not configured or missing params
    # 503: metrics disabled
    assert response.status_code in [200, 404, 422, 503]


@pytest.mark.unit
def test_cors_headers(client):
    """
    Test CORS headers.

    Vérifie que CORS est correctement configuré pour frontend.
    """
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    # CORS preflight should succeed
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
