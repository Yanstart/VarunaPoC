"""
FHIR Profile Builders — US Core, CA Core, and mCODE.

Provides:
- US Core Patient profile (USCDI v3 required elements)
- CA Core Patient profile (pan-Canadian data elements)
- mCODE CancerCondition, TNMStageGroup, TumorMarkerTest
- Profile URL declarations in meta.profile
- Validation helper that checks required elements

References:
    US Core: https://hl7.org/fhir/us/core/STU6.1/
    CA Core: https://build.fhir.org/ig/HL7-Canada/ca-core/
    mCODE:   https://hl7.org/fhir/us/mcode/STU3/
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Profile URLs (canonical)
# ---------------------------------------------------------------------------

US_CORE_PATIENT_PROFILE = (
    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
)
CA_CORE_PATIENT_PROFILE = (
    "http://hl7.org/fhir/ca/core/StructureDefinition/profile-patient"
)
US_CORE_DIAGNOSTIC_REPORT_PROFILE = (
    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-note"
)
MCODE_CANCER_CONDITION_PROFILE = (
    "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-primary-cancer-condition"
)
MCODE_TNM_STAGE_GROUP_PROFILE = (
    "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-tnm-stage-group"
)
MCODE_TUMOR_MARKER_PROFILE = (
    "http://hl7.org/fhir/us/mcode/StructureDefinition/mcode-tumor-marker"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deterministic_id(seed: str) -> str:
    """Génère un identifiant déterministe à partir d'un seed."""
    return hashlib.sha256(seed.encode()).hexdigest()[:12]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# US Core Patient
# ---------------------------------------------------------------------------

def build_us_core_patient(
    patient_id: str,
    family_name: str = "Unknown",
    given_name: str = "Unknown",
    gender: str = "unknown",
    birth_date: str | None = None,
    identifier_value: str | None = None,
    identifier_system: str = "http://hospital.example.org/patients",
    race_code: str | None = None,
    race_display: str | None = None,
    ethnicity_code: str | None = None,
    ethnicity_display: str | None = None,
) -> dict[str, Any]:
    """
    Construit une ressource Patient conforme au profil US Core (USCDI v3).

    Éléments requis USCDI v3:
    - identifier, name, gender (Patient must-support)
    - Race/ethnicity extensions (US Core requirement)

    Args:
        patient_id: Identifiant du patient.
        family_name: Nom de famille.
        given_name: Prénom.
        gender: Genre administratif (male, female, other, unknown).
        birth_date: Date de naissance (YYYY-MM-DD).
        identifier_value: Valeur de l'identifiant (MRN, etc.).
        identifier_system: Système de l'identifiant.
        race_code: Code OMB de la race.
        race_display: Libellé de la race.
        ethnicity_code: Code OMB de l'ethnie.
        ethnicity_display: Libellé de l'ethnie.

    Returns:
        Ressource FHIR R4 Patient conforme US Core.
    """
    patient: dict[str, Any] = {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {
            "profile": [US_CORE_PATIENT_PROFILE],
            "lastUpdated": _now_iso(),
        },
        "identifier": [
            {
                "system": identifier_system,
                "value": identifier_value or patient_id,
            }
        ],
        "name": [
            {
                "use": "official",
                "family": family_name,
                "given": [given_name],
            }
        ],
        "gender": gender,
    }

    if birth_date:
        patient["birthDate"] = birth_date

    # US Core race extension (required if known)
    if race_code:
        patient.setdefault("extension", []).append({
            "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
            "extension": [
                {
                    "url": "ombCategory",
                    "valueCoding": {
                        "system": "urn:oid:2.16.840.1.113883.6.238",
                        "code": race_code,
                        "display": race_display or race_code,
                    },
                },
                {
                    "url": "text",
                    "valueString": race_display or race_code,
                },
            ],
        })

    # US Core ethnicity extension (required if known)
    if ethnicity_code:
        patient.setdefault("extension", []).append({
            "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
            "extension": [
                {
                    "url": "ombCategory",
                    "valueCoding": {
                        "system": "urn:oid:2.16.840.1.113883.6.238",
                        "code": ethnicity_code,
                        "display": ethnicity_display or ethnicity_code,
                    },
                },
                {
                    "url": "text",
                    "valueString": ethnicity_display or ethnicity_code,
                },
            ],
        })

    return patient


# ---------------------------------------------------------------------------
# CA Core Patient
# ---------------------------------------------------------------------------

def build_ca_core_patient(
    patient_id: str,
    family_name: str = "Unknown",
    given_name: str = "Unknown",
    gender: str = "unknown",
    birth_date: str | None = None,
    health_number: str | None = None,
    health_number_jurisdiction: str = "ON",
) -> dict[str, Any]:
    """
    Construit une ressource Patient conforme au profil CA Core.

    Éléments pan-canadiens:
    - Provincial health number (JHN) as identifier
    - Official name with family and given

    Args:
        patient_id: Identifiant du patient.
        family_name: Nom de famille.
        given_name: Prénom.
        gender: Genre administratif.
        birth_date: Date de naissance (YYYY-MM-DD).
        health_number: Numéro d'assurance maladie provincial.
        health_number_jurisdiction: Code province (ON, QC, BC, etc.).

    Returns:
        Ressource FHIR R4 Patient conforme CA Core.
    """
    # Provincial health number system URIs
    jhn_systems = {
        "ON": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-on-patient-hcn",
        "QC": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-qc-patient-hcn",
        "BC": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-bc-patient-hcn",
        "AB": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-ab-patient-hcn",
    }

    identifiers = []
    if health_number:
        system = jhn_systems.get(
            health_number_jurisdiction,
            f"https://fhir.infoway-inforoute.ca/NamingSystem/ca-{health_number_jurisdiction.lower()}-patient-hcn",
        )
        identifiers.append({
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                        "code": "JHN",
                        "display": "Jurisdictional health number",
                    }
                ]
            },
            "system": system,
            "value": health_number,
        })
    else:
        identifiers.append({
            "system": "http://hospital.example.ca/patients",
            "value": patient_id,
        })

    patient: dict[str, Any] = {
        "resourceType": "Patient",
        "id": patient_id,
        "meta": {
            "profile": [CA_CORE_PATIENT_PROFILE],
            "lastUpdated": _now_iso(),
        },
        "identifier": identifiers,
        "name": [
            {
                "use": "official",
                "family": family_name,
                "given": [given_name],
            }
        ],
        "gender": gender,
    }

    if birth_date:
        patient["birthDate"] = birth_date

    return patient


# ---------------------------------------------------------------------------
# mCODE CancerCondition (#114)
# ---------------------------------------------------------------------------

def build_cancer_condition(
    condition_id: str,
    patient_id: str,
    histology_code: str = "8140/3",
    histology_display: str = "Adenocarcinoma, NOS",
    body_site_code: str = "80248005",
    body_site_display: str = "Left breast structure",
    clinical_status: str = "active",
    tnm_stage_group_id: str | None = None,
) -> dict[str, Any]:
    """
    Construit une ressource Condition conforme au profil mCODE PrimaryCancerCondition.

    Args:
        condition_id: Identifiant de la condition.
        patient_id: Référence patient.
        histology_code: Code ICD-O-3 de l'histologie.
        histology_display: Libellé histologique.
        body_site_code: Code SNOMED CT du site anatomique.
        body_site_display: Libellé du site anatomique.
        clinical_status: Statut clinique (active, remission, etc.).
        tnm_stage_group_id: Référence à l'Observation TNMStageGroup.

    Returns:
        Ressource FHIR R4 Condition conforme mCODE.
    """
    condition: dict[str, Any] = {
        "resourceType": "Condition",
        "id": condition_id,
        "meta": {
            "profile": [MCODE_CANCER_CONDITION_PROFILE],
            "lastUpdated": _now_iso(),
        },
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": clinical_status,
                    "display": clinical_status.capitalize(),
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": (
                        "http://terminology.hl7.org/CodeSystem"
                        "/condition-ver-status"
                    ),
                    "code": "confirmed",
                    "display": "Confirmed",
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": (
                            "http://terminology.hl7.org/CodeSystem"
                            "/condition-category"
                        ),
                        "code": "encounter-diagnosis",
                        "display": "Encounter Diagnosis",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/icd-o-3",
                    "code": histology_code,
                    "display": histology_display,
                }
            ],
            "text": histology_display,
        },
        "bodySite": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": body_site_code,
                        "display": body_site_display,
                    }
                ]
            }
        ],
        "subject": {
            "reference": f"Patient/{patient_id}",
        },
        "onsetDateTime": _now_iso(),
    }

    # Stage information with TNM reference
    if tnm_stage_group_id:
        condition["stage"] = [
            {
                "assessment": [
                    {
                        "reference": f"Observation/{tnm_stage_group_id}",
                    }
                ],
            }
        ]

    return condition


# ---------------------------------------------------------------------------
# mCODE TNMStageGroup (#114)
# ---------------------------------------------------------------------------

def build_tnm_stage_group(
    observation_id: str,
    patient_id: str,
    stage_group_code: str = "261638004",
    stage_group_display: str = "Stage II",
    t_code: str = "261650005",
    t_display: str = "T2",
    n_code: str = "261651009",
    n_display: str = "N0",
    m_code: str = "261652002",
    m_display: str = "M0",
) -> dict[str, Any]:
    """
    Construit une Observation conforme au profil mCODE TNMStageGroup.

    Args:
        observation_id: Identifiant de l'observation.
        patient_id: Référence patient.
        stage_group_code: Code SNOMED du groupe de stade.
        stage_group_display: Libellé du groupe de stade.
        t_code: Code SNOMED de la catégorie T.
        t_display: Libellé T.
        n_code: Code SNOMED de la catégorie N.
        n_display: Libellé N.
        m_code: Code SNOMED de la catégorie M.
        m_display: Libellé M.

    Returns:
        Ressource FHIR R4 Observation conforme mCODE TNMStageGroup.
    """
    return {
        "resourceType": "Observation",
        "id": observation_id,
        "meta": {
            "profile": [MCODE_TNM_STAGE_GROUP_PROFILE],
            "lastUpdated": _now_iso(),
        },
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": (
                            "http://terminology.hl7.org/CodeSystem"
                            "/observation-category"
                        ),
                        "code": "laboratory",
                        "display": "Laboratory",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "21908-9",
                    "display": "Stage group.clinical Cancer",
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
        },
        "effectiveDateTime": _now_iso(),
        "valueCodeableConcept": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": stage_group_code,
                    "display": stage_group_display,
                }
            ]
        },
        "component": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "21905-5",
                            "display": "Primary tumor.clinical [Class] Cancer",
                        }
                    ]
                },
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": t_code,
                            "display": t_display,
                        }
                    ]
                },
            },
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "21906-3",
                            "display": (
                                "Regional lymph nodes.clinical [Class] Cancer"
                            ),
                        }
                    ]
                },
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": n_code,
                            "display": n_display,
                        }
                    ]
                },
            },
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "21907-1",
                            "display": "Distant metastases.clinical [Class] Cancer",
                        }
                    ]
                },
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": m_code,
                            "display": m_display,
                        }
                    ]
                },
            },
        ],
    }


# ---------------------------------------------------------------------------
# mCODE TumorMarkerTest (#114)
# ---------------------------------------------------------------------------

# Mapping VarunaPoC ML auto-tags to mCODE tumor marker LOINC codes
TUMOR_MARKER_LOINC_MAP: dict[str, dict[str, str]] = {
    "ki67": {
        "code": "85319-2",
        "display": "Ki-67 [Percentile] in Specimen",
        "unit": "%",
    },
    "her2": {
        "code": "85318-4",
        "display": "HER2 [Presence] in Breast cancer specimen",
        "unit": "score",
    },
    "er": {
        "code": "85337-4",
        "display": "Estrogen receptor Ag [Presence] in Breast cancer specimen",
        "unit": "%",
    },
    "pr": {
        "code": "85339-0",
        "display": "Progesterone receptor Ag [Presence] in Breast cancer specimen",
        "unit": "%",
    },
}


def build_tumor_marker_test(
    observation_id: str,
    patient_id: str,
    marker_name: str,
    value: float | str | None = None,
    interpretation_code: str | None = None,
    interpretation_display: str | None = None,
) -> dict[str, Any]:
    """
    Construit une Observation conforme au profil mCODE TumorMarkerTest.

    Mappe les auto-tags ML VarunaPoC (ki67, her2, er, pr) vers les codes LOINC mCODE.

    Args:
        observation_id: Identifiant de l'observation.
        patient_id: Référence patient.
        marker_name: Nom du marqueur (ki67, her2, er, pr).
        value: Valeur numérique ou textuelle du résultat.
        interpretation_code: Code d'interprétation (POS, NEG, H, L).
        interpretation_display: Libellé d'interprétation.

    Returns:
        Ressource FHIR R4 Observation conforme mCODE TumorMarkerTest.
    """
    marker_key = marker_name.lower()
    loinc_info = TUMOR_MARKER_LOINC_MAP.get(marker_key, {
        "code": "85319-2",
        "display": f"Tumor marker: {marker_name}",
        "unit": "",
    })

    obs: dict[str, Any] = {
        "resourceType": "Observation",
        "id": observation_id,
        "meta": {
            "profile": [MCODE_TUMOR_MARKER_PROFILE],
            "lastUpdated": _now_iso(),
        },
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": (
                            "http://terminology.hl7.org/CodeSystem"
                            "/observation-category"
                        ),
                        "code": "laboratory",
                        "display": "Laboratory",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": loinc_info["code"],
                    "display": loinc_info["display"],
                }
            ],
            "text": f"{marker_name.upper()} tumor marker test",
        },
        "subject": {
            "reference": f"Patient/{patient_id}",
        },
        "effectiveDateTime": _now_iso(),
    }

    # Set value as Quantity (numeric) or string
    if isinstance(value, (int, float)):
        obs["valueQuantity"] = {
            "value": value,
            "unit": loinc_info.get("unit", ""),
            "system": "http://unitsofmeasure.org",
            "code": loinc_info.get("unit", ""),
        }
    elif value is not None:
        obs["valueString"] = str(value)

    # Interpretation
    if interpretation_code:
        obs["interpretation"] = [
            {
                "coding": [
                    {
                        "system": (
                            "http://terminology.hl7.org/CodeSystem"
                            "/v3-ObservationInterpretation"
                        ),
                        "code": interpretation_code,
                        "display": interpretation_display or interpretation_code,
                    }
                ]
            }
        ]

    return obs


def map_ml_tags_to_tumor_markers(
    tags: dict[str, Any],
    patient_id: str,
    slide_id: str,
) -> list[dict[str, Any]]:
    """
    Mappe les auto-tags ML VarunaPoC vers des ressources mCODE TumorMarkerTest.

    Les tags ML ont la forme: {"ki67": 0.35, "her2": "positive", ...}
    Chaque tag reconnu est converti en Observation FHIR mCODE.

    Args:
        tags: Dictionnaire de tags ML VarunaPoC.
        patient_id: Référence patient.
        slide_id: ID de la lame (utilisé pour générer des IDs déterministes).

    Returns:
        Liste de ressources Observation FHIR mCODE.
    """
    markers = []
    for tag_name, tag_value in tags.items():
        tag_lower = tag_name.lower()
        if tag_lower not in TUMOR_MARKER_LOINC_MAP:
            continue

        obs_id = f"marker-{_deterministic_id(f'{slide_id}:{tag_lower}')}"

        # Determine interpretation
        interp_code = None
        interp_display = None
        if isinstance(tag_value, str):
            val_lower = tag_value.lower()
            if val_lower in ("positive", "pos", "+"):
                interp_code = "POS"
                interp_display = "Positive"
            elif val_lower in ("negative", "neg", "-"):
                interp_code = "NEG"
                interp_display = "Negative"
            numeric_value = None
        else:
            numeric_value = tag_value
            # Threshold-based interpretation for ki67
            if tag_lower == "ki67" and isinstance(tag_value, (int, float)):
                if tag_value >= 0.20:
                    interp_code = "H"
                    interp_display = "High"
                else:
                    interp_code = "L"
                    interp_display = "Low"

        marker = build_tumor_marker_test(
            observation_id=obs_id,
            patient_id=patient_id,
            marker_name=tag_lower,
            value=numeric_value if numeric_value is not None else tag_value,
            interpretation_code=interp_code,
            interpretation_display=interp_display,
        )
        markers.append(marker)

    return markers


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_us_core_patient(patient: dict[str, Any]) -> list[str]:
    """
    Valide qu'une ressource Patient contient les éléments requis US Core.

    Vérifie les must-support elements USCDI v3:
    - identifier (au moins un)
    - name (au moins un avec family)
    - gender

    Args:
        patient: Ressource Patient FHIR.

    Returns:
        Liste d'erreurs (vide si conforme).
    """
    errors = []

    if patient.get("resourceType") != "Patient":
        errors.append("resourceType must be 'Patient'")
        return errors

    # Check profile declaration
    profiles = patient.get("meta", {}).get("profile", [])
    if US_CORE_PATIENT_PROFILE not in profiles:
        errors.append(f"meta.profile must include {US_CORE_PATIENT_PROFILE}")

    # Required: at least one identifier
    identifiers = patient.get("identifier", [])
    if not identifiers:
        errors.append("identifier is required (at least one)")

    # Required: name with family
    names = patient.get("name", [])
    if not names:
        errors.append("name is required (at least one)")
    elif not any(n.get("family") for n in names):
        errors.append("name.family is required")

    # Gender is mandatory
    if not patient.get("gender"):
        errors.append("gender is required")

    return errors


def validate_ca_core_patient(patient: dict[str, Any]) -> list[str]:
    """
    Valide qu'une ressource Patient contient les éléments requis CA Core.

    Args:
        patient: Ressource Patient FHIR.

    Returns:
        Liste d'erreurs (vide si conforme).
    """
    errors = []

    if patient.get("resourceType") != "Patient":
        errors.append("resourceType must be 'Patient'")
        return errors

    profiles = patient.get("meta", {}).get("profile", [])
    if CA_CORE_PATIENT_PROFILE not in profiles:
        errors.append(f"meta.profile must include {CA_CORE_PATIENT_PROFILE}")

    identifiers = patient.get("identifier", [])
    if not identifiers:
        errors.append("identifier is required (at least one)")

    names = patient.get("name", [])
    if not names:
        errors.append("name is required (at least one)")
    elif not any(n.get("family") for n in names):
        errors.append("name.family is required")

    if not patient.get("gender"):
        errors.append("gender is required")

    return errors


def validate_mcode_cancer_condition(condition: dict[str, Any]) -> list[str]:
    """
    Valide qu'une ressource Condition contient les éléments requis mCODE.

    Args:
        condition: Ressource Condition FHIR.

    Returns:
        Liste d'erreurs (vide si conforme).
    """
    errors = []

    if condition.get("resourceType") != "Condition":
        errors.append("resourceType must be 'Condition'")
        return errors

    profiles = condition.get("meta", {}).get("profile", [])
    if MCODE_CANCER_CONDITION_PROFILE not in profiles:
        errors.append(f"meta.profile must include {MCODE_CANCER_CONDITION_PROFILE}")

    if not condition.get("code"):
        errors.append("code is required")

    if not condition.get("subject"):
        errors.append("subject is required")

    if not condition.get("clinicalStatus"):
        errors.append("clinicalStatus is required")

    return errors


def validate_mcode_tumor_marker(observation: dict[str, Any]) -> list[str]:
    """
    Valide qu'une Observation contient les éléments requis mCODE TumorMarkerTest.

    Args:
        observation: Ressource Observation FHIR.

    Returns:
        Liste d'erreurs (vide si conforme).
    """
    errors = []

    if observation.get("resourceType") != "Observation":
        errors.append("resourceType must be 'Observation'")
        return errors

    profiles = observation.get("meta", {}).get("profile", [])
    if MCODE_TUMOR_MARKER_PROFILE not in profiles:
        errors.append(f"meta.profile must include {MCODE_TUMOR_MARKER_PROFILE}")

    if not observation.get("code"):
        errors.append("code is required")

    if not observation.get("subject"):
        errors.append("subject is required")

    if not observation.get("status"):
        errors.append("status is required")

    return errors
