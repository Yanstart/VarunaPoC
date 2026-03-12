"""
Routes d'audit - API de recherche et compliance.

Endpoints:
- GET  /api/audit/events          - Rechercher les evenements d'audit
- GET  /api/audit/gdpr/register   - Registre RGPD Article 30

References:
    - GDPR Article 30: https://gdpr-info.eu/art-30-gdpr/
    - Belgian Privacy Commission: https://www.dataprotectionauthority.be/
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from auth.audit import GDPR_PROCESSING_REGISTER, search_audit_events
from auth.dependencies import require_role
from auth.schemas import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit"])


# ---------------------------------------------------------------------------
# Audit search endpoint
# ---------------------------------------------------------------------------


@router.get("/events")
async def get_audit_events(
    user: str | None = Query(None, description="Filtrer par identifiant utilisateur (sub)"),
    event_type: str | None = Query(None, alias="type", description="Filtrer par type d'evenement"),
    from_date: str | None = Query(None, alias="from", description="Date de debut ISO (inclusive)"),
    to_date: str | None = Query(None, alias="to", description="Date de fin ISO (inclusive)"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre max de resultats"),
    offset: int = Query(0, ge=0, description="Nombre de resultats a sauter"),
    _current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
) -> dict[str, Any]:
    """Rechercher les evenements d'audit.

    Permet de filtrer les evenements par utilisateur, type, et plage
    de dates. Les resultats sont tries par date decroissante.

    Parametres de requete:
    - user: identifiant subject de l'utilisateur
    - type: type d'evenement (LOGIN, SLIDE_VIEWED, FHIR_READ, etc.)
    - from: date ISO de debut (inclusive)
    - to: date ISO de fin (inclusive)
    - limit: nombre max de resultats (1-1000, defaut: 100)
    - offset: pagination (defaut: 0)
    """
    events = search_audit_events(
        user_sub=user,
        event_type=event_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )

    return {
        "total": len(events),
        "limit": limit,
        "offset": offset,
        "events": events,
    }


# ---------------------------------------------------------------------------
# GDPR Article 30 Register
# ---------------------------------------------------------------------------


@router.get("/gdpr/register")
async def get_gdpr_register(
    _current_user: CurrentUser = Depends(require_role("ADMIN_TECHNIQUE")),
) -> dict[str, Any]:
    """Registre des activites de traitement (RGPD Article 30).

    Retourne la liste des activites de traitement de donnees
    personnelles effectuees par VarunaPoC, avec les bases legales,
    categories de donnees et mesures de securite associees.
    """
    return {
        "register_name": "VarunaPoC - Registre des activites de traitement",
        "controller": "CHU UCL Namur - Service d'Anatomie Pathologique",
        "dpo_contact": "dpo@chuuclnamur.be",
        "last_updated": "2026-02-18",
        "activities": GDPR_PROCESSING_REGISTER,
    }
