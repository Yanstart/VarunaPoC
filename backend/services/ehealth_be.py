"""
Belgian eHealth Platform Integration - STS Client & ehBox Stub.

Provides integration with the Belgian eHealth platform:
- SAML token exchange via Security Token Service (STS)
- SSIN (Social Security Identification Number) validation
- RIZIV/INAMI practitioner number validation
- ehBox secure messaging stub

Mock mode by default: all operations return deterministic results
derived from input hashes (no network calls).

References:
    - Belgian eHealth Platform: https://www.ehealth.fgov.be/
    - SSIN format: 11-digit Belgian national number (YY.MM.DD-XXX.CC)
    - RIZIV/INAMI: Belgian healthcare provider identification number
"""

import hashlib
import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SSINValidation(BaseModel):
    """Resultat de la validation d'un numero NISS/SSIN belge."""

    ssin: str
    valid: bool
    formatted: str | None = None
    birth_date: str | None = None
    gender: str | None = None
    error: str | None = None


class RIZIVValidation(BaseModel):
    """Resultat de la validation d'un numero RIZIV/INAMI."""

    number: str
    valid: bool
    formatted: str | None = None
    qualification_code: str | None = None
    error: str | None = None


class SAMLAssertion(BaseModel):
    """SAML assertion retournee par le STS eHealth."""

    assertion_id: str
    issuer: str = "urn:be:fgov:ehealth:sts"
    subject: str
    not_before: str
    not_on_or_after: str
    audience: str = "urn:be:fgov:ehealth:varuna"
    attributes: dict[str, str] = Field(default_factory=dict)
    xml: str = ""


class EhBoxMessage(BaseModel):
    """Message ehBox (messagerie securisee eHealth)."""

    message_id: str
    sender: str
    recipient: str
    subject: str
    content_type: str = "text/plain"
    timestamp: str
    status: str = "sent"


# ---------------------------------------------------------------------------
# SSIN validation
# ---------------------------------------------------------------------------


def validate_ssin(ssin: str) -> SSINValidation:
    """
    Valide un numero NISS/SSIN belge (11 chiffres).

    Format: YY.MM.DD-XXX.CC
    - YY.MM.DD = date de naissance
    - XXX = numero de serie (impair = homme, pair = femme)
    - CC = checksum (97 - (YYMMDDXXX mod 97))

    Pour les personnes nees apres 2000, le calcul du checksum
    utilise le prefixe '2' devant les 9 premiers chiffres.

    Args:
        ssin: Numero SSIN (avec ou sans separateurs)

    Returns:
        SSINValidation avec resultat de validation
    """
    # Strip separators
    cleaned = re.sub(r"[.\-\s]", "", ssin)

    if len(cleaned) != 11:
        return SSINValidation(
            ssin=ssin,
            valid=False,
            error="Le SSIN doit contenir exactement 11 chiffres",
        )

    if not cleaned.isdigit():
        return SSINValidation(
            ssin=ssin,
            valid=False,
            error="Le SSIN ne doit contenir que des chiffres",
        )

    # Extract components
    yy = int(cleaned[0:2])
    mm = int(cleaned[2:4])
    dd = int(cleaned[4:6])
    seq = int(cleaned[6:9])
    checksum = int(cleaned[9:11])

    # Validate date components (basic)
    if mm < 1 or mm > 12 or dd < 1 or dd > 31:
        return SSINValidation(
            ssin=ssin,
            valid=False,
            error="Date de naissance invalide dans le SSIN",
        )

    # Try both centuries: born before 2000 and after 2000
    base_9 = int(cleaned[0:9])
    expected_pre2000 = 97 - (base_9 % 97)
    expected_post2000 = 97 - (int("2" + cleaned[0:9]) % 97)

    if checksum == expected_pre2000:
        birth_year = 1900 + yy
    elif checksum == expected_post2000:
        birth_year = 2000 + yy
    else:
        return SSINValidation(
            ssin=ssin,
            valid=False,
            error="Checksum SSIN invalide",
        )

    birth_date = f"{birth_year:04d}-{mm:02d}-{dd:02d}"
    gender = "M" if seq % 2 == 1 else "F"
    formatted = f"{cleaned[0:2]}.{cleaned[2:4]}.{cleaned[4:6]}-{cleaned[6:9]}.{cleaned[9:11]}"

    return SSINValidation(
        ssin=ssin,
        valid=True,
        formatted=formatted,
        birth_date=birth_date,
        gender=gender,
    )


# ---------------------------------------------------------------------------
# RIZIV/INAMI validation
# ---------------------------------------------------------------------------


def validate_riziv(number: str) -> RIZIVValidation:
    """
    Valide un numero RIZIV/INAMI (identification praticien belge).

    Format: X-XXXXX-XX-XXX (11 chiffres)
    - Premier chiffre: code de qualification (1=medecin, 5=pharmacien, etc.)
    - Chiffres 2-6: numero de praticien
    - Chiffres 7-8: checksum
    - Chiffres 9-11: sous-numero

    Args:
        number: Numero RIZIV/INAMI (avec ou sans separateurs)

    Returns:
        RIZIVValidation avec resultat de validation
    """
    cleaned = re.sub(r"[.\-\s/]", "", number)

    if len(cleaned) != 11:
        return RIZIVValidation(
            number=number,
            valid=False,
            error="Le numero RIZIV/INAMI doit contenir 11 chiffres",
        )

    if not cleaned.isdigit():
        return RIZIVValidation(
            number=number,
            valid=False,
            error="Le numero RIZIV/INAMI ne doit contenir que des chiffres",
        )

    # Qualification code (first digit)
    qualification_codes = {
        "1": "Medecin",
        "2": "Pharmacien",
        "3": "Kinesitherapeute",
        "4": "Infirmier",
        "5": "Pharmacien",
        "6": "Dentiste",
        "7": "Logopede",
        "8": "Auxiliaire paramedical",
        "9": "Opticien",
    }

    qual_code = cleaned[0]
    if qual_code not in qualification_codes:
        return RIZIVValidation(
            number=number,
            valid=False,
            error=f"Code de qualification inconnu: {qual_code}",
        )

    # Basic checksum validation: digits 7-8 = (digits 1-6) mod 97
    base = int(cleaned[0:6])
    check = int(cleaned[6:8])
    expected = base % 97

    if check != expected:
        return RIZIVValidation(
            number=number,
            valid=False,
            error="Checksum RIZIV/INAMI invalide",
        )

    formatted = f"{cleaned[0]}-{cleaned[1:6]}-{cleaned[6:8]}-{cleaned[8:11]}"

    return RIZIVValidation(
        number=number,
        valid=True,
        formatted=formatted,
        qualification_code=qualification_codes[qual_code],
    )


# ---------------------------------------------------------------------------
# eHealth STS Client (mock mode)
# ---------------------------------------------------------------------------


class EHealthSTSClient:
    """
    Client pour le Security Token Service (STS) de la plateforme eHealth belge.

    En mode mock (defaut), toutes les operations retournent des resultats
    deterministes derives du hash des parametres d'entree.

    Args:
        mock_mode: Utiliser le mode mock (defaut: True)
        sts_url: URL du STS eHealth (ignore en mode mock)
    """

    def __init__(
        self,
        mock_mode: bool = True,
        sts_url: str = "https://services.ehealth.fgov.be/IAM/Saml11TokenService/Legacy/v1",
    ) -> None:
        self.mock_mode = mock_mode
        self.sts_url = sts_url
        logger.info("eHealth STS client initialized (mock_mode=%s)", mock_mode)

    def _deterministic_id(self, seed: str) -> str:
        """Generate a deterministic ID from a seed string."""
        return hashlib.sha256(seed.encode()).hexdigest()[:32]

    async def request_saml_token(
        self,
        ssin: str,
        purpose: str = "clinical-use",
        audience: str = "urn:be:fgov:ehealth:varuna",
    ) -> SAMLAssertion:
        """
        Demande un token SAML aupres du STS eHealth.

        En mode mock, retourne une assertion SAML deterministe.

        Args:
            ssin: Numero SSIN du praticien
            purpose: Usage prevu du token
            audience: Audience cible

        Returns:
            SAMLAssertion avec les attributs du praticien
        """
        if not self.mock_mode:
            msg = "Real eHealth STS integration requires production certificates"
            raise NotImplementedError(msg)

        # Mock: deterministic SAML assertion
        now = datetime.now(UTC)
        assertion_id = f"_saml_{self._deterministic_id(ssin + purpose)}"

        xml_assertion = f"""<saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{assertion_id}"
    IssueInstant="{now.isoformat()}"
    Version="2.0">
  <saml:Issuer>urn:be:fgov:ehealth:sts</saml:Issuer>
  <saml:Subject>
    <saml:NameID Format="urn:be:fgov:person:ssin">{ssin}</saml:NameID>
  </saml:Subject>
  <saml:Conditions NotBefore="{now.isoformat()}"
                   NotOnOrAfter="{(now + timedelta(hours=1)).isoformat()}">
    <saml:AudienceRestriction>
      <saml:Audience>{audience}</saml:Audience>
    </saml:AudienceRestriction>
  </saml:Conditions>
  <saml:AttributeStatement>
    <saml:Attribute Name="urn:be:fgov:ehealth:1.0:certificateholder:person:ssin">
      <saml:AttributeValue>{ssin}</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="urn:be:fgov:ehealth:1.0:purpose">
      <saml:AttributeValue>{purpose}</saml:AttributeValue>
    </saml:Attribute>
  </saml:AttributeStatement>
</saml:Assertion>"""

        return SAMLAssertion(
            assertion_id=assertion_id,
            subject=ssin,
            not_before=now.isoformat(),
            not_on_or_after=(now + timedelta(hours=1)).isoformat(),
            audience=audience,
            attributes={
                "ssin": ssin,
                "purpose": purpose,
            },
            xml=xml_assertion,
        )

    async def send_ehbox_message(
        self,
        sender_ssin: str,
        recipient_ssin: str,
        subject: str,
        content: str,
    ) -> EhBoxMessage:
        """
        Envoie un message via ehBox (messagerie securisee eHealth).

        En mode mock, retourne un message deterministe.

        Args:
            sender_ssin: SSIN de l'expediteur
            recipient_ssin: SSIN du destinataire
            subject: Sujet du message
            content: Contenu du message

        Returns:
            EhBoxMessage avec le statut d'envoi
        """
        if not self.mock_mode:
            msg = "Real ehBox integration requires production certificates"
            raise NotImplementedError(msg)

        now = datetime.now(UTC)
        message_id = self._deterministic_id(f"{sender_ssin}{recipient_ssin}{subject}")

        return EhBoxMessage(
            message_id=message_id,
            sender=sender_ssin,
            recipient=recipient_ssin,
            subject=subject,
            timestamp=now.isoformat(),
            status="sent",
        )

    def get_status(self) -> dict[str, Any]:
        """Retourne le statut du client eHealth."""
        return {
            "service": "eHealth STS",
            "mock_mode": self.mock_mode,
            "sts_url": self.sts_url,
            "status": "available" if self.mock_mode else "requires_configuration",
        }
