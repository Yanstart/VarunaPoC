"""
DICOMweb Routes - API Endpoints pour services DICOMweb

Endpoints WADO-RS (Retrieve):
- GET  /api/dicomweb/studies/{study}/series/{series}/instances/{instance}
    Récupérer les métadonnées JSON d'une instance DICOM
- GET  /api/dicomweb/studies/{study}/series/{series}/instances/{instance}/frames/{frame}
    Récupérer un frame (tuile) en JPEG

Endpoints STOW-RS (Store):
- POST /api/dicomweb/studies
    Stocker des instances DICOM (multipart/related)

Endpoints QIDO-RS (Search):
- GET  /api/dicomweb/studies
    Rechercher des études DICOM
- GET  /api/dicomweb/studies/{study}/series
    Rechercher des séries dans une étude

Endpoints SR et Annotations:
- POST /api/dicomweb/sr/{slide_id}
    Créer un rapport structuré DICOM SR depuis résultats ML
- POST /api/dicomweb/annotations/{slide_id}
    Convertir annotations GeoJSON en DICOM Supplement 222/223

References:
    - DICOMweb: https://www.dicomstandard.org/using/dicomweb
    - WADO-RS: PS3.18 Section 10.4
    - STOW-RS: PS3.18 Section 10.5
    - QIDO-RS: PS3.18 Section 10.6
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from services.dicom_annotations import DICOMAnnotationService
from services.dicom_sr import DICOMSRService
from services.dicomweb import DICOMwebService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dicomweb", tags=["dicomweb"])

# Singleton service instances
_dicomweb_service: Optional[DICOMwebService] = None
_sr_service: Optional[DICOMSRService] = None
_annotation_service: Optional[DICOMAnnotationService] = None


def _get_dicomweb_service() -> DICOMwebService:
    """Obtenir l'instance singleton du service DICOMweb."""
    global _dicomweb_service
    if _dicomweb_service is None:
        _dicomweb_service = DICOMwebService()
    return _dicomweb_service


def _get_sr_service() -> DICOMSRService:
    """Obtenir l'instance singleton du service DICOM SR."""
    global _sr_service
    if _sr_service is None:
        _sr_service = DICOMSRService()
    return _sr_service


def _get_annotation_service() -> DICOMAnnotationService:
    """Obtenir l'instance singleton du service d'annotations DICOM."""
    global _annotation_service
    if _annotation_service is None:
        _annotation_service = DICOMAnnotationService()
    return _annotation_service


# =========================================================================
# Pydantic Models
# =========================================================================


class StowRequest(BaseModel):
    """Requête STOW-RS pour stocker des instances DICOM."""

    study_uid: Optional[str] = Field(
        None, description="Study Instance UID (auto-generated if absent)"
    )
    instances: Optional[List[Dict[str, Any]]] = Field(
        None, description="Liste de métadonnées d'instances à stocker"
    )


class SRRequest(BaseModel):
    """Requête de création de rapport structuré DICOM SR."""

    detections: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Résultats de détection ML (label, confidence, bbox)",
    )
    classifications: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Résultats de classification ML (diagnosis, probability)",
    )
    model_name: str = Field("VarunaPoC-ML", description="Nom du modèle ML")
    model_version: str = Field("1.0", description="Version du modèle ML")


class AnnotationRequest(BaseModel):
    """Requête de conversion GeoJSON vers DICOM annotations."""

    geojson: Dict[str, Any] = Field(
        ...,
        description="FeatureCollection GeoJSON avec annotations",
    )
    annotation_label: str = Field("annotation", description="Label par défaut pour les annotations")
    patient_name: str = Field("ANONYMOUS", description="Nom du patient DICOM")


# =========================================================================
# WADO-RS: Retrieve
# =========================================================================


@router.get(
    "/studies/{study_uid}/series/{series_uid}/instances/{instance_uid}",
)
async def retrieve_instance_metadata(
    study_uid: str,
    series_uid: str,
    instance_uid: str,
):
    """Récupérer les métadonnées DICOM JSON d'une instance (WADO-RS).

    Retourne les métadonnées au format DICOM JSON Model (PS3.18 F.2)
    pour l'instance demandée.

    Args:
        study_uid: Study Instance UID.
        series_uid: Series Instance UID.
        instance_uid: SOP Instance UID.

    Returns:
        Métadonnées DICOM JSON (application/dicom+json).
    """
    service = _get_dicomweb_service()

    try:
        metadata = service.retrieve_instance_metadata(study_uid, series_uid, instance_uid)
        return JSONResponse(
            content=metadata,
            media_type="application/dicom+json",
        )
    except Exception as e:
        logger.error("WADO-RS metadata retrieval failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de récupération des métadonnées: {e!s}",
        )


@router.get(
    "/studies/{study_uid}/series/{series_uid}" "/instances/{instance_uid}/frames/{frame_number}",
)
async def retrieve_frame(
    study_uid: str,
    series_uid: str,
    instance_uid: str,
    frame_number: int,
):
    """Récupérer un frame (tuile) en JPEG (WADO-RS).

    Retourne les données pixel d'un frame au format JPEG.
    Le content type est multipart/related conformément à WADO-RS.

    Args:
        study_uid: Study Instance UID.
        series_uid: Series Instance UID.
        instance_uid: SOP Instance UID.
        frame_number: Numéro de frame (base 1).

    Returns:
        Données JPEG du frame (image/jpeg).
    """
    if frame_number < 1:
        raise HTTPException(
            status_code=400,
            detail="Le numéro de frame doit être >= 1",
        )

    service = _get_dicomweb_service()

    try:
        frame_data = service.retrieve_frame(study_uid, series_uid, instance_uid, frame_number)
        # Return as multipart/related with single JPEG part
        # For simplicity in mock mode, return as image/jpeg
        boundary = "dicom-frame-boundary"
        body = (
            (f"--{boundary}\r\n" f"Content-Type: image/jpeg\r\n" f"\r\n").encode()
            + frame_data
            + f"\r\n--{boundary}--\r\n".encode()
        )

        return Response(
            content=body,
            media_type=f"multipart/related; boundary={boundary}",
        )
    except Exception as e:
        logger.error("WADO-RS frame retrieval failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de récupération du frame: {e!s}",
        )


# =========================================================================
# STOW-RS: Store
# =========================================================================


@router.post("/studies")
async def store_instances(request: StowRequest):
    """Stocker des instances DICOM (STOW-RS).

    Accepte des instances DICOM et les enregistre dans le registre
    en mémoire. En mode mock, les données ne sont pas persistées
    sur disque.

    Args:
        request: Corps de la requête avec study_uid optionnel et instances.

    Returns:
        Réponse STOW-RS avec références des instances stockées.
    """
    service = _get_dicomweb_service()

    try:
        result = service.store_instances(
            study_uid=request.study_uid,
            instances_data=request.instances,
        )
        return JSONResponse(
            content=result,
            status_code=200,
        )
    except Exception as e:
        logger.error("STOW-RS store failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de stockage STOW-RS: {e!s}",
        )


# =========================================================================
# QIDO-RS: Search
# =========================================================================


@router.get("/studies")
async def search_studies(
    patient_name: Optional[str] = Query(
        None, alias="PatientName", description="Filtrer par nom de patient"
    ),
    patient_id: Optional[str] = Query(
        None, alias="PatientID", description="Filtrer par ID patient"
    ),
    study_date: Optional[str] = Query(
        None, alias="StudyDate", description="Filtrer par date (YYYYMMDD)"
    ),
    modality: Optional[str] = Query(
        None,
        alias="ModalitiesInStudy",
        description="Filtrer par modalité",
    ),
    limit: int = Query(50, description="Nombre maximum de résultats"),
    offset: int = Query(0, description="Décalage pour pagination"),
):
    """Rechercher des études DICOM (QIDO-RS).

    Retourne les résultats au format DICOM JSON avec filtres optionnels.

    Args:
        patient_name: Filtre par nom de patient (correspondance partielle).
        patient_id: Filtre par ID patient (correspondance exacte).
        study_date: Filtre par date d'étude (YYYYMMDD).
        modality: Filtre par modalité (ex: SM).
        limit: Nombre maximum de résultats.
        offset: Décalage de pagination.

    Returns:
        Liste de résultats d'études au format DICOM JSON.
    """
    service = _get_dicomweb_service()

    try:
        results = service.search_studies(
            patient_name=patient_name,
            patient_id=patient_id,
            study_date=study_date,
            modality=modality,
            limit=limit,
            offset=offset,
        )
        return JSONResponse(
            content=results,
            media_type="application/dicom+json",
        )
    except Exception as e:
        logger.error("QIDO-RS study search failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de recherche QIDO-RS: {e!s}",
        )


@router.get("/studies/{study_uid}/series")
async def search_series(
    study_uid: str,
    modality: Optional[str] = Query(None, alias="Modality", description="Filtrer par modalité"),
    limit: int = Query(50, description="Nombre maximum de résultats"),
    offset: int = Query(0, description="Décalage pour pagination"),
):
    """Rechercher des séries dans une étude DICOM (QIDO-RS).

    Args:
        study_uid: Study Instance UID de l'étude parente.
        modality: Filtre par modalité.
        limit: Nombre maximum de résultats.
        offset: Décalage de pagination.

    Returns:
        Liste de résultats de séries au format DICOM JSON.
    """
    service = _get_dicomweb_service()

    try:
        results = service.search_series(
            study_uid=study_uid,
            modality=modality,
            limit=limit,
            offset=offset,
        )
        return JSONResponse(
            content=results,
            media_type="application/dicom+json",
        )
    except Exception as e:
        logger.error("QIDO-RS series search failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de recherche de séries QIDO-RS: {e!s}",
        )


# =========================================================================
# DICOM SR (Structured Reporting)
# =========================================================================


@router.post("/sr/{slide_id}")
async def create_structured_report(slide_id: str, request: SRRequest):
    """Créer un rapport structuré DICOM SR depuis résultats ML.

    Encode les résultats de détection et classification ML dans
    un document DICOM SR suivant le template TID 1500
    (Measurement Report).

    Args:
        slide_id: Identifiant de la lame source.
        request: Détections et classifications ML à encoder.

    Returns:
        Document SR avec structure TID 1500 et métadonnées.
    """
    service = _get_sr_service()

    try:
        result = service.create_measurement_report(
            slide_id=slide_id,
            detections=request.detections,
            classifications=request.classifications,
            model_name=request.model_name,
            model_version=request.model_version,
        )
        return result
    except Exception as e:
        logger.error("DICOM SR creation failed for %s: %s", slide_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de création du SR: {e!s}",
        )


# =========================================================================
# DICOM Annotations (Supplement 222/223)
# =========================================================================


@router.post("/annotations/{slide_id}")
async def convert_annotations(slide_id: str, request: AnnotationRequest):
    """Convertir des annotations GeoJSON en format DICOM Supplement 222/223.

    Prend une FeatureCollection GeoJSON et la convertit en structure
    DICOM Microscopy Bulk Simple Annotations avec groupes d'annotations
    par label.

    Args:
        slide_id: Identifiant de la lame source.
        request: GeoJSON FeatureCollection et paramètres de conversion.

    Returns:
        Résultat de conversion avec groupes d'annotations DICOM.
    """
    service = _get_annotation_service()

    try:
        result = service.convert_geojson_to_dicom(
            slide_id=slide_id,
            geojson=request.geojson,
            annotation_label=request.annotation_label,
            patient_name=request.patient_name,
        )
        return result
    except Exception as e:
        logger.error(
            "DICOM annotation conversion failed for %s: %s",
            slide_id,
            e,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de conversion des annotations: {e!s}",
        )
