"""
Routes régionales - Endpoints pour les intégrations régionales

Endpoints pour l'intégration ABDM (Inde), SS-MIX2 (Japon)
et l'internationalisation (i18n).

API Design:
    - POST /api/regional/abdm/validate      → Valider un numéro ABHA
    - POST /api/regional/abdm/fhir-bundle    → Générer un bundle FHIR ABDM
    - POST /api/regional/abdm/consent        → Créer un artefact de consentement
    - POST /api/regional/abdm/consent/callback → Callback de consentement
    - POST /api/regional/abdm/data-request   → Demande de données via consentement
    - POST /api/regional/ssmix2/parse        → Parser un message HL7 SS-MIX2
    - GET  /api/regional/ssmix2/storage-path → Calculer un chemin SS-MIX2
    - POST /api/regional/ssmix2/extract-path → Extraire les métadonnées d'un chemin
    - GET  /api/regional/ssmix2/mock-data    → Données mock SS-MIX2
    - GET  /api/regional/ssmix2/data-types   → Types de données SS-MIX2
    - GET  /api/regional/i18n/{locale}       → Traductions pour une locale
    - GET  /api/regional/i18n/locales        → Liste des locales supportées
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth.dependencies import get_current_user, require_role
from auth.schemas import CurrentUser
from services.abdm import ABDMService
from services.i18n import I18nService
from services.ssmix2 import SSMIX2Service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/regional", tags=["regional"])

# ==========================================
# Singleton service instances
# ==========================================

_abdm_service: Optional[ABDMService] = None
_ssmix2_service: Optional[SSMIX2Service] = None
_i18n_service: Optional[I18nService] = None


def get_abdm_service() -> ABDMService:
    """Obtient ou crée l'instance singleton ABDMService."""
    global _abdm_service
    if _abdm_service is None:
        _abdm_service = ABDMService(mock_mode=True)
    return _abdm_service


def get_ssmix2_service() -> SSMIX2Service:
    """Obtient ou crée l'instance singleton SSMIX2Service."""
    global _ssmix2_service
    if _ssmix2_service is None:
        _ssmix2_service = SSMIX2Service(mock_mode=True)
    return _ssmix2_service


def get_i18n_service() -> I18nService:
    """Obtient ou crée l'instance singleton I18nService."""
    global _i18n_service
    if _i18n_service is None:
        _i18n_service = I18nService()
    return _i18n_service


# ==========================================
# ABDM Request/Response Schemas
# ==========================================


class ABHAValidationRequest(BaseModel):
    """Requête de validation d'un numéro ABHA."""

    abha_number: str = Field(..., description="Numéro ABHA à 14 chiffres")


class FHIRBundleRequest(BaseModel):
    """Requête de génération de bundle FHIR ABDM."""

    abha_number: str = Field(..., description="Numéro ABHA du patient")
    slide_id: str = Field(..., description="Identifiant de la lame")
    diagnosis: Optional[str] = Field(None, description="Diagnostic textuel")


class ConsentRequest(BaseModel):
    """Requête de création de consentement ABDM."""

    patient_abha: str = Field(..., description="Numéro ABHA du patient")
    hiu_id: str = Field(..., description="Identifiant du HIU")
    purpose: str = Field("CAREMGT", description="Motif du consentement")
    hi_types: Optional[List[str]] = Field(None, description="Types d'informations de santé")


class ConsentCallbackRequest(BaseModel):
    """Requête de callback de consentement."""

    consent_id: str = Field(..., description="Identifiant du consentement")
    status: str = Field(..., description="Statut (GRANTED ou DENIED)")


class DataRequestBody(BaseModel):
    """Requête de données via consentement ABDM."""

    consent_id: str = Field(..., description="Identifiant du consentement")
    slide_id: str = Field(..., description="Identifiant de la lame")


# ==========================================
# SS-MIX2 Request/Response Schemas
# ==========================================


class SSMIX2ParseRequest(BaseModel):
    """Requête de parsing d'un message HL7 SS-MIX2."""

    raw_message: str = Field(..., description="Message HL7 v2.5 brut")


class SSMIX2ExtractPathRequest(BaseModel):
    """Requête d'extraction de métadonnées depuis un chemin SS-MIX2."""

    path: str = Field(..., description="Chemin SS-MIX2 complet")


# ==========================================
# ABDM Endpoints
# ==========================================


@router.post("/abdm/validate")
async def validate_abha(
    request: ABHAValidationRequest,
    _current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Valide un numéro ABHA (Ayushman Bharat Health Account).

    Vérifie le format à 14 chiffres et retourne les informations
    du patient en mode mock.
    """
    service = get_abdm_service()
    return service.validate_abha(request.abha_number)


@router.post("/abdm/fhir-bundle")
async def generate_fhir_bundle(
    request: FHIRBundleRequest,
    _current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Génère un bundle FHIR R4 conforme ABDM.

    Crée un document FHIR avec DiagnosticReport, Patient et ImagingStudy
    pour le rapport de pathologie numérique.
    """
    service = get_abdm_service()
    try:
        bundle = service.generate_fhir_bundle(
            abha_number=request.abha_number,
            slide_id=request.slide_id,
            diagnosis=request.diagnosis,
        )
        return bundle
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/abdm/consent")
async def create_consent(
    request: ConsentRequest,
    _current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Crée un artefact de consentement ABDM.

    Définit qui, quoi, pourquoi, quand et combien de temps
    les données de santé peuvent être partagées.
    """
    service = get_abdm_service()
    try:
        consent = service.create_consent(
            patient_abha=request.patient_abha,
            hiu_id=request.hiu_id,
            purpose=request.purpose,
            hi_types=request.hi_types,
        )
        return consent.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/abdm/consent/callback")
async def consent_callback(
    request: ConsentCallbackRequest,
    _current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Traite le callback de consentement ABDM.

    Appelé par le gateway ABDM quand le patient accorde ou refuse
    le consentement. Met à jour le statut du consentement.
    """
    service = get_abdm_service()
    result = service.process_consent_callback(
        consent_id=request.consent_id,
        status=request.status,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@router.post("/abdm/data-request")
async def data_request(
    request: DataRequestBody,
    _current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Traite une demande de données de santé via ABDM.

    Vérifie que le consentement est accordé et retourne
    le bundle FHIR correspondant.
    """
    service = get_abdm_service()
    result = service.process_data_request(
        consent_id=request.consent_id,
        slide_id=request.slide_id,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


# ==========================================
# SS-MIX2 Endpoints
# ==========================================


@router.post("/ssmix2/parse")
async def parse_ssmix2_message(
    request: SSMIX2ParseRequest,
    _current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Parse un message HL7 v2.5 au format SS-MIX2.

    Extrait les données démographiques du patient et les informations
    de commande depuis un message HL7 brut.
    """
    service = get_ssmix2_service()
    message = service.parse_message(request.raw_message)
    return message.to_dict()


@router.get("/ssmix2/storage-path")
async def get_storage_path(
    patient_id: str = Query(..., description="Identifiant du patient"),
    order_date: str = Query(..., description="Date de commande (YYYYMMDD)"),
    data_type: str = Query(..., description="Type de données SS-MIX2"),
    message_id: str = Query(..., description="Identifiant du message"),
    _current_user: CurrentUser = Depends(get_current_user),
):
    """Calcule le chemin de stockage SS-MIX2 standardisé.

    Format: {root}/{PatientID}/{OrderDate}/{DataType}/{MessageID}
    """
    service = get_ssmix2_service()
    try:
        path = service.get_storage_path(
            patient_id=patient_id,
            order_date=order_date,
            data_type=data_type,
            message_id=message_id,
        )
        return {"path": path}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ssmix2/extract-path")
async def extract_path_metadata(
    request: SSMIX2ExtractPathRequest,
    _current_user: CurrentUser = Depends(require_role("MEDECIN", "ADMIN_TECHNIQUE")),
):
    """Extrait les métadonnées depuis un chemin de stockage SS-MIX2.

    Décompose le chemin pour récupérer PatientID, OrderDate,
    DataType et MessageID.
    """
    service = get_ssmix2_service()
    try:
        metadata = service.extract_from_path(request.path)
        return metadata
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ssmix2/mock-data")
async def get_mock_data(
    _current_user: CurrentUser = Depends(get_current_user),
):
    """Retourne des données patient SS-MIX2 de test.

    Génère des messages ADT et OML mock avec des données
    démographiques et de commande déterministes.
    """
    service = get_ssmix2_service()
    return service.get_mock_patient_data()


@router.get("/ssmix2/data-types")
async def get_data_types(
    _current_user: CurrentUser = Depends(get_current_user),
):
    """Retourne les types de données SS-MIX2 supportés.

    Liste les codes de type de données HL7 v2.5 reconnus
    par le service SS-MIX2.
    """
    service = get_ssmix2_service()
    return {"dataTypes": service.list_data_types()}


# ==========================================
# I18n Endpoints
# ==========================================


@router.get("/i18n/locales")
async def get_supported_locales(
    _current_user: CurrentUser = Depends(get_current_user),
):
    """Retourne la liste des locales supportées.

    Chaque locale inclut son code ISO et son nom dans sa propre langue.
    """
    service = get_i18n_service()
    return {"locales": service.get_supported_locales()}


@router.get("/i18n/{locale}")
async def get_translations(
    locale: str,
    _current_user: CurrentUser = Depends(get_current_user),
):
    """Retourne toutes les traductions pour une locale.

    Fallback vers le français si la locale n'est pas supportée.

    Args:
        locale: Code de locale (fr, en, ja, zh, hi).
    """
    service = get_i18n_service()
    return service.export_translations(locale)
