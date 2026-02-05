"""
VarunaPoC Backend Tests

Test suite pour le backend FastAPI.

Structure:
- test_health.py: Health checks et endpoints basiques
- test_slides.py: API de détection et navigation de lames
- test_openslide.py: Intégration OpenSlide (requires .mrxs test files)

Exécution:
    pytest                          # Tous les tests
    pytest -m unit                  # Tests unitaires rapides
    pytest -m integration           # Tests d'intégration (require OpenSlide)
    pytest --cov=. --cov-report=html  # Avec coverage

Documentation:
    - pytest: https://docs.pytest.org/
    - pytest-asyncio: https://pytest-asyncio.readthedocs.io/
"""
