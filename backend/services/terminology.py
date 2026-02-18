"""
Terminology Mapping Service - SNOMED CT & LOINC.

Provides mapping between VarunaPoC pathology labels and standard
medical terminologies:
- SNOMED CT codes for pathology findings
- LOINC codes for laboratory procedures
- FHIR CodeSystem and ValueSet resource builders

References:
    - SNOMED CT: http://snomed.info/sct
    - LOINC: http://loinc.org
    - FHIR CodeSystem: https://www.hl7.org/fhir/R4/codesystem.html
    - FHIR ValueSet: https://www.hl7.org/fhir/R4/valueset.html
"""

import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System URIs
# ---------------------------------------------------------------------------

SNOMED_SYSTEM = "http://snomed.info/sct"
LOINC_SYSTEM = "http://loinc.org"

# ---------------------------------------------------------------------------
# SNOMED CT mappings: VarunaPoC label -> SNOMED CT concept
# ---------------------------------------------------------------------------

SNOMED_MAPPINGS: dict[str, dict[str, str]] = {
    "Tumeur": {
        "code": "108369006",
        "display": "Neoplasm",
        "display_fr": "Tumeur / Neoplasme",
    },
    "Nécrose": {
        "code": "6574001",
        "display": "Necrosis",
        "display_fr": "Necrose",
    },
    "Inflammation": {
        "code": "23583003",
        "display": "Inflammation",
        "display_fr": "Inflammation",
    },
    "Stroma": {
        "code": "37652006",
        "display": "Stroma",
        "display_fr": "Stroma",
    },
    "Tissu sain": {
        "code": "21390004",
        "display": "Normal tissue",
        "display_fr": "Tissu sain / normal",
    },
    "Artefact": {
        "code": "47973001",
        "display": "Artifact",
        "display_fr": "Artefact",
    },
}

# Reverse lookup: SNOMED code -> label info
_SNOMED_BY_CODE: dict[str, dict[str, str]] = {}
for _label, _info in SNOMED_MAPPINGS.items():
    _SNOMED_BY_CODE[_info["code"]] = {
        "code": _info["code"],
        "display": _info["display"],
        "display_fr": _info["display_fr"],
        "varuna_label": _label,
        "system": SNOMED_SYSTEM,
    }

# ---------------------------------------------------------------------------
# LOINC mappings: procedure type -> LOINC code
# ---------------------------------------------------------------------------

LOINC_MAPPINGS: dict[str, dict[str, str]] = {
    "pathology_synoptic": {
        "code": "60568-3",
        "display": "Pathology synoptic report",
        "display_fr": "Rapport synoptique de pathologie",
    },
    "surgical_pathology": {
        "code": "22634-0",
        "display": "Pathology report gross and microscopic observation",
        "display_fr": "Rapport de pathologie chirurgicale",
    },
    "cytology": {
        "code": "47528-5",
        "display": "Cytology report",
        "display_fr": "Rapport de cytologie",
    },
    "autopsy": {
        "code": "18743-5",
        "display": "Autopsy report",
        "display_fr": "Rapport d'autopsie",
    },
    "immunohistochemistry": {
        "code": "40556-3",
        "display": "Immunohistochemistry stain report",
        "display_fr": "Rapport de coloration immunohistochimique",
    },
    "flow_cytometry": {
        "code": "49584-5",
        "display": "Flow cytometry report",
        "display_fr": "Rapport de cytometrie en flux",
    },
    "molecular_pathology": {
        "code": "55232-3",
        "display": "Genetic analysis summary report",
        "display_fr": "Rapport d'analyse de pathologie moleculaire",
    },
    "electron_microscopy": {
        "code": "50007-4",
        "display": "Electron microscopy study",
        "display_fr": "Etude en microscopie electronique",
    },
}

# Reverse lookup: LOINC code -> procedure info
_LOINC_BY_CODE: dict[str, dict[str, str]] = {}
for _proc, _info in LOINC_MAPPINGS.items():
    _LOINC_BY_CODE[_info["code"]] = {
        "code": _info["code"],
        "display": _info["display"],
        "display_fr": _info["display_fr"],
        "procedure_key": _proc,
        "system": LOINC_SYSTEM,
    }


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TerminologyCoding(BaseModel):
    """Un code dans un systeme de terminologie."""

    system: str
    code: str
    display: str
    display_fr: str | None = None


class SNOMEDLookupResult(BaseModel):
    """Resultat de recherche SNOMED CT."""

    code: str
    system: str = SNOMED_SYSTEM
    display: str
    display_fr: str | None = None
    varuna_label: str | None = None
    found: bool = True


class LOINCLookupResult(BaseModel):
    """Resultat de recherche LOINC."""

    code: str
    system: str = LOINC_SYSTEM
    display: str
    display_fr: str | None = None
    procedure_key: str | None = None
    found: bool = True


class LabelMapping(BaseModel):
    """Mapping d'un label VarunaPoC vers SNOMED CT."""

    varuna_label: str
    snomed: TerminologyCoding | None = None
    mapped: bool = False


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class TerminologyService:
    """
    Service de mapping terminologique pour la pathologie numerique.

    Fournit les correspondances entre les labels internes VarunaPoC
    et les codes SNOMED CT / LOINC standards.
    """

    def lookup_snomed(self, code: str) -> SNOMEDLookupResult:
        """
        Recherche un code SNOMED CT.

        Args:
            code: Code SNOMED CT (ex: '108369006')

        Returns:
            SNOMEDLookupResult avec les details du concept
        """
        info = _SNOMED_BY_CODE.get(code)
        if info:
            return SNOMEDLookupResult(
                code=info["code"],
                display=info["display"],
                display_fr=info["display_fr"],
                varuna_label=info["varuna_label"],
                found=True,
            )
        return SNOMEDLookupResult(
            code=code,
            display="Unknown",
            found=False,
        )

    def lookup_loinc(self, code: str) -> LOINCLookupResult:
        """
        Recherche un code LOINC.

        Args:
            code: Code LOINC (ex: '60568-3')

        Returns:
            LOINCLookupResult avec les details de la procedure
        """
        info = _LOINC_BY_CODE.get(code)
        if info:
            return LOINCLookupResult(
                code=info["code"],
                display=info["display"],
                display_fr=info["display_fr"],
                procedure_key=info["procedure_key"],
                found=True,
            )
        return LOINCLookupResult(
            code=code,
            display="Unknown",
            found=False,
        )

    def map_label(self, varuna_label: str) -> LabelMapping:
        """
        Mappe un label VarunaPoC vers un code SNOMED CT.

        Args:
            varuna_label: Label interne (ex: 'Tumeur', 'Necrose')

        Returns:
            LabelMapping avec le code SNOMED CT correspondant
        """
        info = SNOMED_MAPPINGS.get(varuna_label)
        if info:
            return LabelMapping(
                varuna_label=varuna_label,
                snomed=TerminologyCoding(
                    system=SNOMED_SYSTEM,
                    code=info["code"],
                    display=info["display"],
                    display_fr=info["display_fr"],
                ),
                mapped=True,
            )
        return LabelMapping(varuna_label=varuna_label, mapped=False)

    def map_all_labels(self) -> list[LabelMapping]:
        """Retourne le mapping de tous les labels VarunaPoC connus."""
        return [self.map_label(label) for label in SNOMED_MAPPINGS]

    def build_snomed_codesystem(self) -> dict[str, Any]:
        """
        Construit une ressource FHIR CodeSystem pour les codes SNOMED CT
        utilises dans VarunaPoC.

        Returns:
            FHIR R4 CodeSystem resource (dict)
        """
        concepts = []
        for label, info in SNOMED_MAPPINGS.items():
            concepts.append(
                {
                    "code": info["code"],
                    "display": info["display"],
                    "designation": [
                        {
                            "language": "fr-BE",
                            "value": info["display_fr"],
                        }
                    ],
                    "property": [
                        {
                            "code": "varuna-label",
                            "valueString": label,
                        }
                    ],
                }
            )

        return {
            "resourceType": "CodeSystem",
            "id": "varuna-snomed-pathology",
            "url": "http://varuna.local/fhir/CodeSystem/snomed-pathology",
            "version": "1.0.0",
            "name": "VarunaSNOMEDPathology",
            "title": "VarunaPoC SNOMED CT Pathology Codes",
            "status": "active",
            "content": "fragment",
            "description": (
                "Subset of SNOMED CT codes used by VarunaPoC for "
                "digital pathology annotations."
            ),
            "valueSet": "http://varuna.local/fhir/ValueSet/snomed-pathology",
            "count": len(concepts),
            "concept": concepts,
        }

    def build_loinc_codesystem(self) -> dict[str, Any]:
        """
        Construit une ressource FHIR CodeSystem pour les codes LOINC
        utilises dans VarunaPoC.

        Returns:
            FHIR R4 CodeSystem resource (dict)
        """
        concepts = []
        for proc_key, info in LOINC_MAPPINGS.items():
            concepts.append(
                {
                    "code": info["code"],
                    "display": info["display"],
                    "designation": [
                        {
                            "language": "fr-BE",
                            "value": info["display_fr"],
                        }
                    ],
                    "property": [
                        {
                            "code": "procedure-key",
                            "valueString": proc_key,
                        }
                    ],
                }
            )

        return {
            "resourceType": "CodeSystem",
            "id": "varuna-loinc-pathology",
            "url": "http://varuna.local/fhir/CodeSystem/loinc-pathology",
            "version": "1.0.0",
            "name": "VarunaLOINCPathology",
            "title": "VarunaPoC LOINC Pathology Procedure Codes",
            "status": "active",
            "content": "fragment",
            "description": (
                "Subset of LOINC codes used by VarunaPoC for "
                "pathology laboratory procedures."
            ),
            "count": len(concepts),
            "concept": concepts,
        }

    def build_snomed_valueset(self) -> dict[str, Any]:
        """
        Construit une ressource FHIR ValueSet pour les codes SNOMED CT
        utilises dans VarunaPoC.

        Returns:
            FHIR R4 ValueSet resource (dict)
        """
        includes = []
        for info in SNOMED_MAPPINGS.values():
            includes.append(
                {
                    "code": info["code"],
                    "display": info["display"],
                }
            )

        return {
            "resourceType": "ValueSet",
            "id": "varuna-snomed-pathology",
            "url": "http://varuna.local/fhir/ValueSet/snomed-pathology",
            "version": "1.0.0",
            "name": "VarunaSNOMEDPathologyValueSet",
            "title": "VarunaPoC SNOMED CT Pathology Value Set",
            "status": "active",
            "description": "Value set of SNOMED CT pathology codes used in VarunaPoC.",
            "compose": {
                "include": [
                    {
                        "system": SNOMED_SYSTEM,
                        "concept": includes,
                    }
                ]
            },
        }

    def build_loinc_valueset(self) -> dict[str, Any]:
        """
        Construit une ressource FHIR ValueSet pour les codes LOINC
        utilises dans VarunaPoC.

        Returns:
            FHIR R4 ValueSet resource (dict)
        """
        includes = []
        for info in LOINC_MAPPINGS.values():
            includes.append(
                {
                    "code": info["code"],
                    "display": info["display"],
                }
            )

        return {
            "resourceType": "ValueSet",
            "id": "varuna-loinc-pathology",
            "url": "http://varuna.local/fhir/ValueSet/loinc-pathology",
            "version": "1.0.0",
            "name": "VarunaLOINCPathologyValueSet",
            "title": "VarunaPoC LOINC Pathology Value Set",
            "status": "active",
            "description": "Value set of LOINC pathology codes used in VarunaPoC.",
            "compose": {
                "include": [
                    {
                        "system": LOINC_SYSTEM,
                        "concept": includes,
                    }
                ]
            },
        }
