"""
Routes d'integration - API pour les standards d'interoperabilite.

Endpoints:
- POST /api/integration/hl7v2/parse         - Parser un message HL7 v2
- POST /api/integration/ehealth/token        - Demander un token SAML eHealth
- POST /api/integration/ehealth/ehbox        - Envoyer un message ehBox
- GET  /api/integration/ehealth/status       - Statut du client eHealth
- POST /api/integration/ehealth/validate/ssin    - Valider un SSIN belge
- POST /api/integration/ehealth/validate/riziv   - Valider un numero RIZIV
- POST /api/integration/apsr/{slide_id}      - Generer un rapport APSR

References:
    - HL7 v2.5: https://www.hl7.org/implement/standards/
    - Belgian eHealth: https://www.ehealth.fgov.be/
    - IHE PaLM APSR: https://www.ihe.net/
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.apsr import APSRBuilder, APSRRequest, APSRResult
from services.ehealth_be import (
    EhBoxMessage,
    EHealthSTSClient,
    RIZIVValidation,
    SAMLAssertion,
    SSINValidation,
    validate_riziv,
    validate_ssin,
)
from services.hl7v2_parser import HL7v2Parser, HL7v2ParseResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integration", tags=["Integration"])

# ---------------------------------------------------------------------------
# Singleton service instances
# ---------------------------------------------------------------------------

_ehealth_client: EHealthSTSClient | None = None
_hl7_parser: HL7v2Parser | None = None
_apsr_builder: APSRBuilder | None = None


def _get_ehealth_client() -> EHealthSTSClient:
    global _ehealth_client
    if _ehealth_client is None:
        _ehealth_client = EHealthSTSClient(mock_mode=True)
    return _ehealth_client


def _get_hl7_parser() -> HL7v2Parser:
    global _hl7_parser
    if _hl7_parser is None:
        _hl7_parser = HL7v2Parser()
    return _hl7_parser


def _get_apsr_builder() -> APSRBuilder:
    global _apsr_builder
    if _apsr_builder is None:
        _apsr_builder = APSRBuilder(mock_mode=True)
    return _apsr_builder


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class HL7v2ParseRequest(BaseModel):
    """Requete de parsing HL7 v2."""

    message: str = Field(description="Message HL7 v2 brut")


class EHealthTokenRequest(BaseModel):
    """Requete de token SAML eHealth."""

    ssin: str = Field(description="Numero SSIN du praticien")
    purpose: str = Field(default="clinical-use", description="Usage prevu du token")


class EhBoxSendRequest(BaseModel):
    """Requete d'envoi de message ehBox."""

    sender_ssin: str = Field(description="SSIN de l'expediteur")
    recipient_ssin: str = Field(description="SSIN du destinataire")
    subject: str = Field(description="Sujet du message")
    content: str = Field(description="Contenu du message")


class SSINRequest(BaseModel):
    """Requete de validation SSIN."""

    ssin: str = Field(description="Numero SSIN a valider")


class RIZIVRequest(BaseModel):
    """Requete de validation RIZIV."""

    number: str = Field(description="Numero RIZIV/INAMI a valider")


# ---------------------------------------------------------------------------
# HL7 v2 endpoints
# ---------------------------------------------------------------------------


@router.post("/hl7v2/parse", response_model=HL7v2ParseResult)
async def parse_hl7v2(request: HL7v2ParseRequest):
    """Parser un message HL7 v2.5 (ORM/ORU).

    Analyse les segments MSH, PID, ORC, OBR, OBX, NTE et extrait
    les donnees structurees (patient, commande, observations).
    """
    parser = _get_hl7_parser()
    try:
        result = parser.parse(request.message)
    except Exception as e:
        logger.error("HL7 v2 parse error: %s", e)
        raise HTTPException(status_code=400, detail=f"HL7 v2 parse error: {e!s}")
    return result


# ---------------------------------------------------------------------------
# eHealth endpoints
# ---------------------------------------------------------------------------


@router.post("/ehealth/token", response_model=SAMLAssertion)
async def request_ehealth_token(request: EHealthTokenRequest):
    """Demander un token SAML aupres du STS eHealth belge.

    En mode mock, retourne une assertion SAML deterministe.
    """
    client = _get_ehealth_client()
    try:
        result = await client.request_saml_token(
            ssin=request.ssin,
            purpose=request.purpose,
        )
    except Exception as e:
        logger.error("eHealth STS error: %s", e)
        raise HTTPException(status_code=500, detail=f"eHealth STS error: {e!s}")
    return result


@router.post("/ehealth/ehbox", response_model=EhBoxMessage)
async def send_ehbox_message(request: EhBoxSendRequest):
    """Envoyer un message via ehBox (messagerie securisee eHealth).

    En mode mock, retourne un message deterministe sans envoi reel.
    """
    client = _get_ehealth_client()
    try:
        result = await client.send_ehbox_message(
            sender_ssin=request.sender_ssin,
            recipient_ssin=request.recipient_ssin,
            subject=request.subject,
            content=request.content,
        )
    except Exception as e:
        logger.error("ehBox error: %s", e)
        raise HTTPException(status_code=500, detail=f"ehBox error: {e!s}")
    return result


@router.get("/ehealth/status")
async def ehealth_status():
    """Statut du client eHealth STS."""
    client = _get_ehealth_client()
    return client.get_status()


@router.post("/ehealth/validate/ssin", response_model=SSINValidation)
async def validate_ssin_endpoint(request: SSINRequest):
    """Valider un numero NISS/SSIN belge (11 chiffres).

    Verifie le format, la date de naissance et le checksum.
    """
    return validate_ssin(request.ssin)


@router.post("/ehealth/validate/riziv", response_model=RIZIVValidation)
async def validate_riziv_endpoint(request: RIZIVRequest):
    """Valider un numero RIZIV/INAMI (identification praticien belge).

    Verifie le format, le code de qualification et le checksum.
    """
    return validate_riziv(request.number)


# ---------------------------------------------------------------------------
# APSR endpoints
# ---------------------------------------------------------------------------


@router.post("/apsr/{slide_id}", response_model=APSRResult)
async def generate_apsr(slide_id: str, request: APSRRequest | None = None):
    """Generer un rapport APSR (Anatomic Pathology Structured Report).

    Produit un document CDA R2 XML conforme au profil IHE PaLM APSR.
    En mode mock, le XML est deterministe a partir du slide_id.
    """
    builder = _get_apsr_builder()
    try:
        result = builder.build(slide_id=slide_id, request=request)
    except Exception as e:
        logger.error("APSR build error for %s: %s", slide_id, e)
        raise HTTPException(status_code=500, detail=f"APSR build error: {e!s}")
    return result
