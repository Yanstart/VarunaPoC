"""
IHE APSR (Anatomic Pathology Structured Report) Builder.

Generates IHE PaLM APSR profile-compliant structured reports
for anatomic pathology cases, mapping VarunaPoC annotations
and ML results to standardized APSR sections.

Exports as CDA R2 XML structure (mock mode: deterministic
XML output from slide_id).

References:
    - IHE PaLM Technical Framework: https://www.ihe.net/
    - IHE APSR Profile: Anatomic Pathology Structured Report
    - HL7 CDA R2: Clinical Document Architecture Release 2
    - SNOMED CT pathology codes via services.terminology
"""

import hashlib
import logging
from datetime import UTC, datetime
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class APSRClinicalInfo(BaseModel):
    """Informations cliniques (section I du rapport APSR)."""

    clinical_history: str = ""
    clinical_diagnosis: str = ""
    procedure_type: str = ""
    specimen_type: str = ""


class APSRMacroscopic(BaseModel):
    """Description macroscopique (section II du rapport APSR)."""

    specimen_size: str = ""
    specimen_weight: str = ""
    gross_description: str = ""
    sections_count: int = 0


class APSRMicroscopic(BaseModel):
    """Description microscopique (section III du rapport APSR)."""

    histological_type: str = ""
    grade: str = ""
    margins: str = ""
    lymphovascular_invasion: str = ""
    annotations_summary: list[dict[str, Any]] = Field(default_factory=list)
    ml_results_summary: list[dict[str, Any]] = Field(default_factory=list)


class APSRDiagnosis(BaseModel):
    """Diagnostic (section IV du rapport APSR)."""

    primary_diagnosis: str = ""
    secondary_diagnoses: list[str] = Field(default_factory=list)
    snomed_codes: list[dict[str, str]] = Field(default_factory=list)
    staging: str = ""
    comment: str = ""


class APSRRequest(BaseModel):
    """Requete de generation d'un rapport APSR."""

    clinical_info: APSRClinicalInfo = Field(default_factory=APSRClinicalInfo)
    macroscopic: APSRMacroscopic = Field(default_factory=APSRMacroscopic)
    microscopic: APSRMicroscopic = Field(default_factory=APSRMicroscopic)
    diagnosis: APSRDiagnosis = Field(default_factory=APSRDiagnosis)
    patient_id: str | None = None
    patient_name: str | None = None
    performer_name: str | None = None
    performer_id: str | None = None


class APSRResult(BaseModel):
    """Resultat de la generation d'un rapport APSR."""

    slide_id: str
    document_id: str
    title: str = "Anatomic Pathology Structured Report"
    created_at: str
    xml: str
    sections: list[str] = Field(default_factory=list)
    status: str = "mock"


# ---------------------------------------------------------------------------
# APSR Builder
# ---------------------------------------------------------------------------


class APSRBuilder:
    """
    Constructeur de rapports APSR conformes au profil IHE PaLM.

    En mode mock (defaut), genere des documents CDA R2 XML deterministes
    a partir du slide_id.

    Args:
        mock_mode: Utiliser le mode mock (defaut: True)
    """

    def __init__(self, mock_mode: bool = True) -> None:
        self.mock_mode = mock_mode

    def _deterministic_id(self, seed: str) -> str:
        """Generate a deterministic OID-like identifier from a seed."""
        h = hashlib.sha256(seed.encode()).hexdigest()
        # Create a deterministic OID-like identifier
        return f"2.16.56.10.1.{int(h[:8], 16)}.{int(h[8:16], 16)}"

    def build(
        self,
        slide_id: str,
        request: APSRRequest | None = None,
    ) -> APSRResult:
        """
        Construit un rapport APSR pour une lame donnee.

        En mode mock, genere un document CDA R2 XML deterministe
        a partir du slide_id.

        Args:
            slide_id: Identifiant de la lame
            request: Parametres optionnels du rapport

        Returns:
            APSRResult avec le document XML CDA R2
        """
        if request is None:
            request = APSRRequest()

        now = datetime.now(UTC)
        doc_id = self._deterministic_id(slide_id)
        created_at = now.isoformat()

        sections = [
            "Clinical Information",
            "Macroscopic Description",
            "Microscopic Description",
            "Diagnosis",
        ]

        return APSRResult(
            slide_id=slide_id,
            document_id=doc_id,
            title="Anatomic Pathology Structured Report",
            created_at=created_at,
            xml=self._build_cda_xml(slide_id, doc_id, request, now),
            sections=sections,
            status="mock" if self.mock_mode else "generated",
        )

    def _build_cda_xml(
        self,
        slide_id: str,
        doc_id: str,
        request: APSRRequest,
        timestamp: datetime,
    ) -> str:
        """Build CDA R2 XML document."""
        ts = timestamp.strftime("%Y%m%d%H%M%S")
        patient_id = request.patient_id or f"PAT-{slide_id}"
        patient_name = request.patient_name or "Unknown Patient"
        performer_name = request.performer_name or "Unknown Pathologist"
        performer_id = request.performer_id or "PRACT-001"

        # Build section bodies
        clinical_body = self._section_clinical(request.clinical_info)
        macro_body = self._section_macroscopic(request.macroscopic)
        micro_body = self._section_microscopic(request.microscopic)
        diag_body = self._section_diagnosis(request.diagnosis)

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xsi:schemaLocation="urn:hl7-org:v3 CDA.xsd">
  <!-- IHE PaLM APSR Profile -->
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="1.3.6.1.4.1.19376.1.8.1.1.1"/>
  <id root="{doc_id}"/>
  <code code="11526-1" codeSystem="2.16.840.1.113883.6.1"
        codeSystemName="LOINC" displayName="Pathology study"/>
  <title>Anatomic Pathology Structured Report</title>
  <effectiveTime value="{ts}"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="fr-BE"/>
  <recordTarget>
    <patientRole>
      <id root="2.16.56.10.1" extension="{xml_escape(patient_id)}"/>
      <patient>
        <name>{xml_escape(patient_name)}</name>
      </patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="{ts}"/>
    <assignedAuthor>
      <id root="2.16.56.10.2" extension="{xml_escape(performer_id)}"/>
      <assignedPerson>
        <name>{xml_escape(performer_name)}</name>
      </assignedPerson>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.56.10.3"/>
        <name>CHU UCL Namur - Service d'Anatomie Pathologique</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <component>
    <structuredBody>
      <!-- Section I: Clinical Information -->
      <component>
        <section>
          <templateId root="1.3.6.1.4.1.19376.1.8.1.2.1"/>
          <code code="22636-5" codeSystem="2.16.840.1.113883.6.1"
                displayName="Pathology report relevant history"/>
          <title>Clinical Information</title>
          <text>{clinical_body}</text>
        </section>
      </component>
      <!-- Section II: Macroscopic Description -->
      <component>
        <section>
          <templateId root="1.3.6.1.4.1.19376.1.8.1.2.2"/>
          <code code="22634-0" codeSystem="2.16.840.1.113883.6.1"
                displayName="Pathology report gross observation"/>
          <title>Macroscopic Description</title>
          <text>{macro_body}</text>
        </section>
      </component>
      <!-- Section III: Microscopic Description -->
      <component>
        <section>
          <templateId root="1.3.6.1.4.1.19376.1.8.1.2.3"/>
          <code code="22635-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Pathology report microscopic observation"/>
          <title>Microscopic Description</title>
          <text>{micro_body}</text>
        </section>
      </component>
      <!-- Section IV: Diagnosis -->
      <component>
        <section>
          <templateId root="1.3.6.1.4.1.19376.1.8.1.2.4"/>
          <code code="22637-3" codeSystem="2.16.840.1.113883.6.1"
                displayName="Pathology report diagnosis"/>
          <title>Diagnosis</title>
          <text>{diag_body}</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

    def _section_clinical(self, info: APSRClinicalInfo) -> str:
        """Build clinical information section body."""
        parts = []
        if info.clinical_history:
            parts.append(
                f"<paragraph>Clinical History: {xml_escape(info.clinical_history)}</paragraph>"
            )
        if info.clinical_diagnosis:
            parts.append(
                f"<paragraph>Clinical Diagnosis: {xml_escape(info.clinical_diagnosis)}</paragraph>"
            )
        if info.procedure_type:
            parts.append(f"<paragraph>Procedure: {xml_escape(info.procedure_type)}</paragraph>")
        if info.specimen_type:
            parts.append(f"<paragraph>Specimen: {xml_escape(info.specimen_type)}</paragraph>")
        if not parts:
            parts.append("<paragraph>No clinical information provided.</paragraph>")
        return "\n          ".join(parts)

    def _section_macroscopic(self, macro: APSRMacroscopic) -> str:
        """Build macroscopic description section body."""
        parts = []
        if macro.specimen_size:
            parts.append(f"<paragraph>Size: {xml_escape(macro.specimen_size)}</paragraph>")
        if macro.specimen_weight:
            parts.append(f"<paragraph>Weight: {xml_escape(macro.specimen_weight)}</paragraph>")
        if macro.gross_description:
            parts.append(
                f"<paragraph>Description: {xml_escape(macro.gross_description)}</paragraph>"
            )
        if macro.sections_count > 0:
            parts.append(f"<paragraph>Sections: {macro.sections_count}</paragraph>")
        if not parts:
            parts.append("<paragraph>No macroscopic description provided.</paragraph>")
        return "\n          ".join(parts)

    def _section_microscopic(self, micro: APSRMicroscopic) -> str:
        """Build microscopic description section body."""
        parts = []
        if micro.histological_type:
            parts.append(
                f"<paragraph>Histological Type: {xml_escape(micro.histological_type)}</paragraph>"
            )
        if micro.grade:
            parts.append(f"<paragraph>Grade: {xml_escape(micro.grade)}</paragraph>")
        if micro.margins:
            parts.append(f"<paragraph>Margins: {xml_escape(micro.margins)}</paragraph>")
        if micro.lymphovascular_invasion:
            parts.append(
                "<paragraph>Lymphovascular Invasion: "
                f"{xml_escape(micro.lymphovascular_invasion)}</paragraph>"
            )
        if micro.annotations_summary:
            parts.append("<paragraph>Annotations:</paragraph>")
            parts.append("<list>")
            for ann in micro.annotations_summary:
                label = ann.get("label", "Unknown")
                count = ann.get("count", 0)
                parts.append(f"  <item>{xml_escape(label)}: {count}</item>")
            parts.append("</list>")
        if micro.ml_results_summary:
            parts.append("<paragraph>ML Analysis:</paragraph>")
            parts.append("<list>")
            for ml_res in micro.ml_results_summary:
                model = ml_res.get("model", "Unknown")
                result = ml_res.get("result", "N/A")
                parts.append(f"  <item>{xml_escape(model)}: {xml_escape(str(result))}</item>")
            parts.append("</list>")
        if not parts:
            parts.append("<paragraph>No microscopic description provided.</paragraph>")
        return "\n          ".join(parts)

    def _section_diagnosis(self, diag: APSRDiagnosis) -> str:
        """Build diagnosis section body."""
        parts = []
        if diag.primary_diagnosis:
            parts.append(
                f"<paragraph>Primary Diagnosis: {xml_escape(diag.primary_diagnosis)}</paragraph>"
            )
        if diag.secondary_diagnoses:
            parts.append("<paragraph>Secondary Diagnoses:</paragraph>")
            parts.append("<list>")
            for dx in diag.secondary_diagnoses:
                parts.append(f"  <item>{xml_escape(dx)}</item>")
            parts.append("</list>")
        if diag.snomed_codes:
            parts.append("<paragraph>SNOMED CT Codes:</paragraph>")
            parts.append("<list>")
            for sc in diag.snomed_codes:
                code = sc.get("code", "")
                display = sc.get("display", "")
                parts.append(f"  <item>{xml_escape(code)} - {xml_escape(display)}</item>")
            parts.append("</list>")
        if diag.staging:
            parts.append(f"<paragraph>Staging: {xml_escape(diag.staging)}</paragraph>")
        if diag.comment:
            parts.append(f"<paragraph>Comment: {xml_escape(diag.comment)}</paragraph>")
        if not parts:
            parts.append("<paragraph>No diagnosis provided.</paragraph>")
        return "\n          ".join(parts)
