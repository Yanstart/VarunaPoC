"""
Routes de terminologie - API pour SNOMED CT et LOINC.

Endpoints:
- GET /api/terminology/snomed/{code}    - Rechercher un code SNOMED CT
- GET /api/terminology/loinc/{code}     - Rechercher un code LOINC
- GET /api/terminology/mappings         - Tous les mappings VarunaPoC
- GET /api/terminology/codesystem/snomed - CodeSystem FHIR SNOMED
- GET /api/terminology/codesystem/loinc  - CodeSystem FHIR LOINC
- GET /api/terminology/valueset/snomed   - ValueSet FHIR SNOMED
- GET /api/terminology/valueset/loinc    - ValueSet FHIR LOINC

References:
    - SNOMED CT: http://snomed.info/sct
    - LOINC: http://loinc.org
    - FHIR Terminology: https://www.hl7.org/fhir/R4/terminology-module.html
"""

import logging

from fastapi import APIRouter, HTTPException

from services.terminology import (
    LabelMapping,
    LOINCLookupResult,
    SNOMEDLookupResult,
    TerminologyService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/terminology", tags=["Terminology"])

# Singleton service
_service: TerminologyService | None = None


def _get_service() -> TerminologyService:
    global _service
    if _service is None:
        _service = TerminologyService()
    return _service


# ---------------------------------------------------------------------------
# Lookup endpoints
# ---------------------------------------------------------------------------


@router.get("/snomed/{code}", response_model=SNOMEDLookupResult)
async def lookup_snomed(code: str):
    """Rechercher un code SNOMED CT dans le referentiel VarunaPoC.

    Retourne le concept SNOMED CT et le label VarunaPoC correspondant.
    """
    svc = _get_service()
    result = svc.lookup_snomed(code)
    if not result.found:
        raise HTTPException(
            status_code=404,
            detail=f"Code SNOMED CT {code} non trouve dans le referentiel VarunaPoC",
        )
    return result


@router.get("/loinc/{code}", response_model=LOINCLookupResult)
async def lookup_loinc(code: str):
    """Rechercher un code LOINC dans le referentiel VarunaPoC.

    Retourne la procedure LOINC et ses details.
    """
    svc = _get_service()
    result = svc.lookup_loinc(code)
    if not result.found:
        raise HTTPException(
            status_code=404,
            detail=f"Code LOINC {code} non trouve dans le referentiel VarunaPoC",
        )
    return result


@router.get("/mappings", response_model=list[LabelMapping])
async def get_all_mappings():
    """Retourner tous les mappings VarunaPoC label -> SNOMED CT.

    Liste la correspondance entre les labels internes (francais)
    et les codes SNOMED CT standards.
    """
    svc = _get_service()
    return svc.map_all_labels()


# ---------------------------------------------------------------------------
# FHIR resource endpoints
# ---------------------------------------------------------------------------


@router.get("/codesystem/snomed")
async def get_snomed_codesystem():
    """Retourner la ressource FHIR CodeSystem pour les codes SNOMED CT.

    Fragment du CodeSystem SNOMED CT utilise par VarunaPoC.
    """
    svc = _get_service()
    return svc.build_snomed_codesystem()


@router.get("/codesystem/loinc")
async def get_loinc_codesystem():
    """Retourner la ressource FHIR CodeSystem pour les codes LOINC.

    Fragment du CodeSystem LOINC utilise par VarunaPoC.
    """
    svc = _get_service()
    return svc.build_loinc_codesystem()


@router.get("/valueset/snomed")
async def get_snomed_valueset():
    """Retourner la ressource FHIR ValueSet pour les codes SNOMED CT.

    ValueSet des codes SNOMED CT de pathologie utilises par VarunaPoC.
    """
    svc = _get_service()
    return svc.build_snomed_valueset()


@router.get("/valueset/loinc")
async def get_loinc_valueset():
    """Retourner la ressource FHIR ValueSet pour les codes LOINC.

    ValueSet des codes LOINC de pathologie utilises par VarunaPoC.
    """
    svc = _get_service()
    return svc.build_loinc_valueset()
