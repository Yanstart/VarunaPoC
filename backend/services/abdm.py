"""
Service ABDM HIP (Ayushman Bharat Digital Mission - Health Information Provider)

Interface pour le système de santé numérique indien ABDM.
Génère des bundles FHIR R4 conformes aux spécifications ABDM,
valide les identifiants ABHA et gère les artefacts de consentement.

Fonctionne en mode mock par défaut (pas de dépendance externe requise).

Références:
    - ABDM HIP: https://abdm.gov.in/hip
    - FHIR R4: https://hl7.org/fhir/R4/
    - ABHA: https://abha.abdm.gov.in/
"""

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ABDM FHIR server base URL
ABDM_FHIR_SERVER = "https://abdm.gov.in/fhir"

# ABHA number regex: exactly 14 digits
_ABHA_PATTERN = re.compile(r"^\d{14}$")


def validate_abha_number(abha_number: str) -> bool:
    """Valide un numéro ABHA (Ayushman Bharat Health Account).

    Le numéro ABHA est un identifiant de santé indien à 14 chiffres.

    Args:
        abha_number: Numéro ABHA à valider (format 14 chiffres).

    Returns:
        True si le format est valide, False sinon.
    """
    if not abha_number or not isinstance(abha_number, str):
        return False
    return bool(_ABHA_PATTERN.match(abha_number))


class ConsentArtifact:
    """Artefact de consentement ABDM.

    Structure de consentement définissant qui, quoi, pourquoi,
    quand et combien de temps les données de santé peuvent être partagées.

    Attributes:
        consent_id: Identifiant unique du consentement.
        patient_abha: Numéro ABHA du patient.
        hip_id: Identifiant du HIP (fournisseur d'informations de santé).
        hiu_id: Identifiant du HIU (utilisateur d'informations de santé).
        purpose: Motif du partage de données.
        date_range_from: Date de début de la période couverte.
        date_range_to: Date de fin de la période couverte.
        expiry: Date d'expiration du consentement.
        hi_types: Types d'informations de santé autorisés.
        status: Statut du consentement (REQUESTED, GRANTED, DENIED, REVOKED, EXPIRED).
    """

    def __init__(
        self,
        patient_abha: str,
        hip_id: str,
        hiu_id: str,
        purpose: str = "CAREMGT",
        hi_types: Optional[List[str]] = None,
        date_range_from: Optional[str] = None,
        date_range_to: Optional[str] = None,
        expiry_days: int = 30,
    ) -> None:
        now = datetime.now(tz=timezone.utc)
        self.consent_id = hashlib.sha256(
            f"{patient_abha}:{hip_id}:{now.isoformat()}".encode()
        ).hexdigest()[:24]
        self.patient_abha = patient_abha
        self.hip_id = hip_id
        self.hiu_id = hiu_id
        self.purpose = purpose
        self.date_range_from = date_range_from or (now - timedelta(days=365)).strftime("%Y-%m-%d")
        self.date_range_to = date_range_to or now.strftime("%Y-%m-%d")
        self.expiry = (now + timedelta(days=expiry_days)).isoformat()
        self.hi_types = hi_types or [
            "DiagnosticReport",
            "ImagingStudy",
            "Observation",
        ]
        self.status = "REQUESTED"

    def to_dict(self) -> Dict[str, Any]:
        """Sérialise l'artefact de consentement en dictionnaire."""
        return {
            "consentId": self.consent_id,
            "patientAbha": self.patient_abha,
            "hipId": self.hip_id,
            "hiuId": self.hiu_id,
            "purpose": self.purpose,
            "dateRange": {
                "from": self.date_range_from,
                "to": self.date_range_to,
            },
            "expiry": self.expiry,
            "hiTypes": self.hi_types,
            "status": self.status,
        }

    def grant(self) -> None:
        """Accorde le consentement."""
        self.status = "GRANTED"

    def deny(self) -> None:
        """Refuse le consentement."""
        self.status = "DENIED"

    def revoke(self) -> None:
        """Révoque le consentement."""
        self.status = "REVOKED"


class ABDMService:
    """Service d'interface ABDM Health Information Provider (HIP).

    Gère la génération de bundles FHIR R4 pour ABDM,
    la validation des identifiants ABHA et le flux de consentement.

    Fonctionne en mode mock par défaut pour le développement.

    Attributes:
        mock_mode: Si True, retourne des données déterministes de test.
        hip_id: Identifiant du Health Information Provider.
    """

    def __init__(
        self,
        hip_id: str = "varuna-pathology-hip",
        mock_mode: bool = True,
    ) -> None:
        self.hip_id = hip_id
        self.mock_mode = mock_mode
        self._consents: Dict[str, ConsentArtifact] = {}
        logger.info(
            "ABDMService initialisé (mock_mode=%s, hip_id=%s)",
            mock_mode,
            hip_id,
        )

    def validate_abha(self, abha_number: str) -> Dict[str, Any]:
        """Valide un numéro ABHA et retourne les informations du patient.

        Args:
            abha_number: Numéro ABHA à 14 chiffres.

        Returns:
            Dictionnaire avec le statut de validation et les informations patient.
        """
        is_valid = validate_abha_number(abha_number)
        if not is_valid:
            return {
                "valid": False,
                "abhaNumber": abha_number,
                "error": "Format ABHA invalide. 14 chiffres requis.",
            }

        if self.mock_mode:
            return {
                "valid": True,
                "abhaNumber": abha_number,
                "name": "Patient Mock ABDM",
                "gender": "M",
                "yearOfBirth": "1985",
                "address": {
                    "state": "Maharashtra",
                    "district": "Mumbai",
                },
            }

        # En mode réel, appeler l'API ABDM pour vérification
        return {
            "valid": True,
            "abhaNumber": abha_number,
            "note": "Validation réelle non implémentée",
        }

    def generate_fhir_bundle(
        self,
        abha_number: str,
        slide_id: str,
        diagnosis: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Génère un bundle FHIR R4 conforme ABDM pour un rapport de pathologie.

        Args:
            abha_number: Numéro ABHA du patient.
            slide_id: Identifiant de la lame histologique.
            diagnosis: Diagnostic textuel (optionnel).

        Returns:
            Bundle FHIR R4 avec DiagnosticReport et observations.
        """
        if not validate_abha_number(abha_number):
            msg = f"Numéro ABHA invalide: {abha_number}"
            raise ValueError(msg)

        now = datetime.now(tz=timezone.utc).isoformat()
        bundle_id = hashlib.sha256(f"{abha_number}:{slide_id}:{now}".encode()).hexdigest()[:16]

        patient_ref = f"Patient/{abha_number}"
        report_id = f"DiagnosticReport/{bundle_id}"

        bundle: Dict[str, Any] = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "meta": {
                "lastUpdated": now,
                "profile": [f"{ABDM_FHIR_SERVER}/StructureDefinition/DiagnosticReportBundle"],
            },
            "type": "document",
            "timestamp": now,
            "entry": [
                # Composition (document header)
                {
                    "fullUrl": f"{ABDM_FHIR_SERVER}/Composition/{bundle_id}-comp",
                    "resource": {
                        "resourceType": "Composition",
                        "id": f"{bundle_id}-comp",
                        "status": "final",
                        "type": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "721981007",
                                    "display": "Diagnostic studies report",
                                }
                            ]
                        },
                        "subject": {"reference": patient_ref},
                        "date": now,
                        "title": "Rapport de pathologie numérique",
                        "section": [
                            {
                                "title": "Diagnostic Report",
                                "entry": [{"reference": report_id}],
                            }
                        ],
                    },
                },
                # Patient
                {
                    "fullUrl": f"{ABDM_FHIR_SERVER}/{patient_ref}",
                    "resource": {
                        "resourceType": "Patient",
                        "id": abha_number,
                        "identifier": [
                            {
                                "system": "https://healthid.abdm.gov.in",
                                "value": abha_number,
                                "type": {
                                    "coding": [
                                        {
                                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                            "code": "MR",
                                            "display": "Medical record number",
                                        }
                                    ]
                                },
                            }
                        ],
                    },
                },
                # DiagnosticReport
                {
                    "fullUrl": f"{ABDM_FHIR_SERVER}/{report_id}",
                    "resource": {
                        "resourceType": "DiagnosticReport",
                        "id": bundle_id,
                        "status": "final",
                        "category": [
                            {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                                        "code": "PAT",
                                        "display": "Pathology",
                                    }
                                ]
                            }
                        ],
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "60568-3",
                                    "display": "Pathology Synoptic report",
                                }
                            ]
                        },
                        "subject": {"reference": patient_ref},
                        "effectiveDateTime": now,
                        "issued": now,
                        "conclusion": diagnosis or "Rapport en attente de conclusion",
                        "presentedForm": [
                            {
                                "contentType": "application/dicom",
                                "title": f"Lame numérique: {slide_id}",
                            }
                        ],
                    },
                },
                # ImagingStudy reference
                {
                    "fullUrl": f"{ABDM_FHIR_SERVER}/ImagingStudy/{bundle_id}-img",
                    "resource": {
                        "resourceType": "ImagingStudy",
                        "id": f"{bundle_id}-img",
                        "status": "available",
                        "subject": {"reference": patient_ref},
                        "description": f"Whole Slide Image - {slide_id}",
                        "numberOfSeries": 1,
                        "numberOfInstances": 1,
                    },
                },
            ],
        }

        return bundle

    def create_consent(
        self,
        patient_abha: str,
        hiu_id: str,
        purpose: str = "CAREMGT",
        hi_types: Optional[List[str]] = None,
    ) -> ConsentArtifact:
        """Crée un artefact de consentement pour le partage de données.

        Args:
            patient_abha: Numéro ABHA du patient.
            hiu_id: Identifiant du Health Information User.
            purpose: Code de motif (CAREMGT, BTG, PUBHLTH, etc.).
            hi_types: Types d'informations de santé demandés.

        Returns:
            Artefact de consentement créé.
        """
        if not validate_abha_number(patient_abha):
            msg = f"Numéro ABHA invalide: {patient_abha}"
            raise ValueError(msg)

        consent = ConsentArtifact(
            patient_abha=patient_abha,
            hip_id=self.hip_id,
            hiu_id=hiu_id,
            purpose=purpose,
            hi_types=hi_types,
        )
        self._consents[consent.consent_id] = consent
        logger.info(
            "Consentement créé: %s pour patient %s",
            consent.consent_id,
            patient_abha,
        )
        return consent

    def process_consent_callback(
        self,
        consent_id: str,
        status: str,
    ) -> Dict[str, Any]:
        """Traite le callback de consentement ABDM.

        Appelé par le gateway ABDM quand le patient accorde ou refuse le consentement.

        Args:
            consent_id: Identifiant du consentement.
            status: Nouveau statut (GRANTED, DENIED).

        Returns:
            Résultat du traitement avec le statut mis à jour.
        """
        consent = self._consents.get(consent_id)
        if not consent:
            return {
                "status": "error",
                "message": f"Consentement non trouvé: {consent_id}",
            }

        if status == "GRANTED":
            consent.grant()
        elif status == "DENIED":
            consent.deny()
        else:
            return {
                "status": "error",
                "message": f"Statut invalide: {status}",
            }

        logger.info("Consentement %s mis à jour: %s", consent_id, status)
        return {
            "status": "success",
            "consentId": consent_id,
            "consentStatus": consent.status,
        }

    def process_data_request(
        self,
        consent_id: str,
        slide_id: str,
    ) -> Dict[str, Any]:
        """Traite une demande de données de santé via ABDM.

        Vérifie que le consentement est accordé avant de fournir les données.

        Args:
            consent_id: Identifiant du consentement.
            slide_id: Identifiant de la lame à partager.

        Returns:
            Bundle FHIR si le consentement est accordé, erreur sinon.
        """
        consent = self._consents.get(consent_id)
        if not consent:
            return {
                "status": "error",
                "message": f"Consentement non trouvé: {consent_id}",
            }

        if consent.status != "GRANTED":
            return {
                "status": "error",
                "message": f"Consentement non accordé (statut: {consent.status})",
            }

        # Générer le bundle FHIR pour la lame demandée
        bundle = self.generate_fhir_bundle(
            abha_number=consent.patient_abha,
            slide_id=slide_id,
            diagnosis="Rapport de pathologie numérique (mode mock)",
        )

        return {
            "status": "success",
            "consentId": consent_id,
            "bundle": bundle,
        }

    def get_consent_status(self, consent_id: str) -> Optional[Dict[str, Any]]:
        """Récupère le statut d'un consentement.

        Args:
            consent_id: Identifiant du consentement.

        Returns:
            Dictionnaire du consentement ou None si non trouvé.
        """
        consent = self._consents.get(consent_id)
        if not consent:
            return None
        return consent.to_dict()
