"""
Tests for integration standards: eHealth BE, Terminology, HL7 v2, APSR, Enhanced Audit.

Covers issues #106, #107, #108, #109, #113.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# #106 - Belgian eHealth Platform Integration
# ---------------------------------------------------------------------------


class TestSSINValidation:
    """Test Belgian SSIN (national number) validation."""

    def test_valid_ssin_pre2000(self):
        """A valid SSIN born before 2000."""
        from services.ehealth_be import validate_ssin

        # 85.07.30-033.xx : born 1985-07-30, male (033 odd)
        # Compute checksum: 850730033 mod 97 = ?
        base = 850730033
        check = 97 - (base % 97)
        ssin_str = f"850730033{check:02d}"
        result = validate_ssin(ssin_str)
        assert result.valid is True
        assert result.gender == "M"
        assert result.birth_date is not None
        assert result.birth_date.startswith("1985")

    def test_valid_ssin_with_separators(self):
        """SSIN with dots and dashes should be accepted."""
        from services.ehealth_be import validate_ssin

        base = 850730033
        check = 97 - (base % 97)
        ssin_str = f"85.07.30-033.{check:02d}"
        result = validate_ssin(ssin_str)
        assert result.valid is True
        assert result.formatted is not None

    def test_invalid_ssin_wrong_length(self):
        from services.ehealth_be import validate_ssin

        result = validate_ssin("123456")
        assert result.valid is False
        assert "11 chiffres" in result.error

    def test_invalid_ssin_bad_checksum(self):
        from services.ehealth_be import validate_ssin

        result = validate_ssin("85073003399")
        assert result.valid is False

    def test_invalid_ssin_non_numeric(self):
        from services.ehealth_be import validate_ssin

        result = validate_ssin("8507300AB99")
        assert result.valid is False
        assert "chiffres" in result.error


class TestRIZIVValidation:
    """Test RIZIV/INAMI practitioner number validation."""

    def test_valid_riziv(self):
        from services.ehealth_be import validate_riziv

        # Build a valid RIZIV: qualification=1, number=12345, check=(112345 % 97)
        base = 112345
        check = base % 97
        riziv = f"1{12345:05d}{check:02d}001"
        result = validate_riziv(riziv)
        assert result.valid is True
        assert result.qualification_code == "Medecin"
        assert result.formatted is not None

    def test_invalid_riziv_wrong_length(self):
        from services.ehealth_be import validate_riziv

        result = validate_riziv("12345")
        assert result.valid is False
        assert "11 chiffres" in result.error

    def test_invalid_riziv_bad_qualification(self):
        from services.ehealth_be import validate_riziv

        result = validate_riziv("01234567890")
        assert result.valid is False

    def test_invalid_riziv_bad_checksum(self):
        from services.ehealth_be import validate_riziv

        result = validate_riziv("11234599001")
        assert result.valid is False


class TestEHealthSTSClient:
    """Test eHealth STS client (mock mode)."""

    @pytest.mark.asyncio
    async def test_request_saml_token_mock(self):
        from services.ehealth_be import EHealthSTSClient

        client = EHealthSTSClient(mock_mode=True)
        result = await client.request_saml_token(ssin="85073003328")
        assert result.assertion_id.startswith("_saml_")
        assert result.issuer == "urn:be:fgov:ehealth:sts"
        assert result.subject == "85073003328"
        assert "ssin" in result.attributes
        assert len(result.xml) > 0
        assert "<saml:Assertion" in result.xml

    @pytest.mark.asyncio
    async def test_saml_token_deterministic(self):
        """Same inputs should produce same assertion_id."""
        from services.ehealth_be import EHealthSTSClient

        client = EHealthSTSClient(mock_mode=True)
        r1 = await client.request_saml_token(ssin="85073003328", purpose="test")
        r2 = await client.request_saml_token(ssin="85073003328", purpose="test")
        assert r1.assertion_id == r2.assertion_id

    @pytest.mark.asyncio
    async def test_send_ehbox_message_mock(self):
        from services.ehealth_be import EHealthSTSClient

        client = EHealthSTSClient(mock_mode=True)
        result = await client.send_ehbox_message(
            sender_ssin="85073003328",
            recipient_ssin="90010100144",
            subject="Test report",
            content="Pathology results attached",
        )
        assert result.status == "sent"
        assert result.sender == "85073003328"
        assert len(result.message_id) > 0

    def test_get_status(self):
        from services.ehealth_be import EHealthSTSClient

        client = EHealthSTSClient(mock_mode=True)
        status = client.get_status()
        assert status["mock_mode"] is True
        assert status["status"] == "available"

    @pytest.mark.asyncio
    async def test_real_mode_raises(self):
        from services.ehealth_be import EHealthSTSClient

        client = EHealthSTSClient(mock_mode=False)
        with pytest.raises(NotImplementedError):
            await client.request_saml_token(ssin="85073003328")


# ---------------------------------------------------------------------------
# #107 - SNOMED CT and LOINC Terminology Mapping
# ---------------------------------------------------------------------------


class TestTerminologyService:
    """Test terminology mapping service."""

    def test_lookup_snomed_tumeur(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        result = svc.lookup_snomed("108369006")
        assert result.found is True
        assert result.display == "Neoplasm"
        assert result.varuna_label == "Tumeur"
        assert result.system == "http://snomed.info/sct"

    def test_lookup_snomed_necrose(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        result = svc.lookup_snomed("6574001")
        assert result.found is True
        assert result.display == "Necrosis"
        assert result.varuna_label == "Nécrose"

    def test_lookup_snomed_all_labels(self):
        """All 6 required SNOMED mappings should exist."""
        from services.terminology import SNOMED_MAPPINGS, TerminologyService

        svc = TerminologyService()
        expected_labels = [
            "Tumeur",
            "Nécrose",
            "Inflammation",
            "Stroma",
            "Tissu sain",
            "Artefact",
        ]
        for label in expected_labels:
            assert label in SNOMED_MAPPINGS, f"Missing SNOMED mapping for {label}"
            info = SNOMED_MAPPINGS[label]
            result = svc.lookup_snomed(info["code"])
            assert result.found is True

    def test_lookup_snomed_not_found(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        result = svc.lookup_snomed("99999999")
        assert result.found is False

    def test_lookup_loinc_pathology_synoptic(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        result = svc.lookup_loinc("60568-3")
        assert result.found is True
        assert result.display == "Pathology synoptic report"

    def test_lookup_loinc_surgical_pathology(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        result = svc.lookup_loinc("22634-0")
        assert result.found is True
        assert result.procedure_key == "surgical_pathology"

    def test_lookup_loinc_not_found(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        result = svc.lookup_loinc("99999-9")
        assert result.found is False

    def test_map_label_tumeur(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        result = svc.map_label("Tumeur")
        assert result.mapped is True
        assert result.snomed is not None
        assert result.snomed.code == "108369006"

    def test_map_label_unknown(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        result = svc.map_label("UnknownLabel")
        assert result.mapped is False
        assert result.snomed is None

    def test_map_all_labels(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        mappings = svc.map_all_labels()
        assert len(mappings) == 6
        assert all(m.mapped for m in mappings)

    def test_build_snomed_codesystem(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        cs = svc.build_snomed_codesystem()
        assert cs["resourceType"] == "CodeSystem"
        assert cs["content"] == "fragment"
        assert cs["count"] == 6

    def test_build_loinc_codesystem(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        cs = svc.build_loinc_codesystem()
        assert cs["resourceType"] == "CodeSystem"
        assert len(cs["concept"]) > 0

    def test_build_snomed_valueset(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        vs = svc.build_snomed_valueset()
        assert vs["resourceType"] == "ValueSet"
        assert "compose" in vs
        concepts = vs["compose"]["include"][0]["concept"]
        assert len(concepts) == 6

    def test_build_loinc_valueset(self):
        from services.terminology import TerminologyService

        svc = TerminologyService()
        vs = svc.build_loinc_valueset()
        assert vs["resourceType"] == "ValueSet"
        assert "compose" in vs


# ---------------------------------------------------------------------------
# #108 - HL7 v2 ORM/ORU Message Parsing
# ---------------------------------------------------------------------------


class TestHL7v2Parser:
    """Test HL7 v2 message parser."""

    ORM_MESSAGE = (
        "MSH|^~\\&|HIS|CHU_UCL_NAMUR|VarunaPoC|PATH_LAB|"
        "20260218120000||ORM^O01|MSG00001|P|2.5\r"
        "PID|||PAT001^^^CHU||Dupont^Jean^^^Mr||19850730|M|||"
        "Rue de la Loi 1^^Bruxelles^^1000^BE|||||||850730033\r"
        "ORC|NW|ORD001|FIL001||SC|||||||Dr. Martin^Pierre\r"
        "OBR||ORD001|FIL001|22634-0^Surgical Pathology^LN|||"
        "20260218100000\r"
        "NTE|||Biopsie cutanee - lesion suspecte bras gauche"
    )

    ORU_MESSAGE = (
        "MSH|^~\\&|PATH_LAB|CHU_UCL_NAMUR|HIS|CHU_UCL_NAMUR|"
        "20260218140000||ORU^R01|MSG00002|P|2.5\r"
        "PID|||PAT001^^^CHU||Dupont^Jean^^^Mr||19850730|M\r"
        "OBR||ORD001|FIL001|22634-0^Surgical Pathology^LN|||"
        "20260218100000|||||||||||||||||F\r"
        "OBX|1|TX|22637-3^Pathology Diagnosis^LN||"
        "Carcinome basocellulaire nodulaire||||||F\r"
        "OBX|2|TX|22635-7^Microscopic Observation^LN||"
        "Proliferation basaloide nodulaire dermique||||||F\r"
        "NTE|||Marges de resection saines"
    )

    def test_parse_orm(self):
        from services.hl7v2_parser import HL7v2Parser

        parser = HL7v2Parser()
        result = parser.parse(self.ORM_MESSAGE)
        assert result.message_type == "ORM"
        assert result.trigger_event == "O01"
        assert result.version == "2.5"
        assert result.sending_application == "HIS"
        assert result.sending_facility == "CHU_UCL_NAMUR"

    def test_parse_patient_demographics(self):
        from services.hl7v2_parser import HL7v2Parser

        parser = HL7v2Parser()
        result = parser.parse(self.ORM_MESSAGE)
        assert result.patient is not None
        assert result.patient.patient_id == "PAT001"
        assert result.patient.family_name == "Dupont"
        assert result.patient.given_name == "Jean"
        assert result.patient.gender == "M"
        assert result.patient.date_of_birth == "19850730"

    def test_parse_order_info(self):
        from services.hl7v2_parser import HL7v2Parser

        parser = HL7v2Parser()
        result = parser.parse(self.ORM_MESSAGE)
        assert result.order is not None
        assert result.order.order_control == "NW"
        assert result.order.placer_order_number == "ORD001"
        assert result.order.filler_order_number == "FIL001"

    def test_parse_oru(self):
        from services.hl7v2_parser import HL7v2Parser

        parser = HL7v2Parser()
        result = parser.parse(self.ORU_MESSAGE)
        assert result.message_type == "ORU"
        assert result.trigger_event == "R01"

    def test_parse_observations(self):
        from services.hl7v2_parser import HL7v2Parser

        parser = HL7v2Parser()
        result = parser.parse(self.ORU_MESSAGE)
        assert len(result.observations) == 2
        assert "basocellulaire" in result.observations[0].observation_value
        assert result.observations[0].observation_status == "F"

    def test_parse_notes(self):
        from services.hl7v2_parser import HL7v2Parser

        parser = HL7v2Parser()
        result = parser.parse(self.ORU_MESSAGE)
        assert len(result.notes) == 1
        assert "Marges" in result.notes[0]

    def test_parse_segments(self):
        from services.hl7v2_parser import HL7v2Parser

        parser = HL7v2Parser()
        result = parser.parse(self.ORM_MESSAGE)
        seg_types = [s.segment_type for s in result.segments]
        assert "MSH" in seg_types
        assert "PID" in seg_types
        assert "ORC" in seg_types
        assert "OBR" in seg_types
        assert "NTE" in seg_types

    def test_parse_empty_message(self):
        from services.hl7v2_parser import HL7v2Parser

        parser = HL7v2Parser()
        result = parser.parse("")
        assert result.message_type == "UNKNOWN"
        assert len(result.parse_errors) > 0

    def test_mllp_framing(self):
        from services.hl7v2_parser import add_mllp, strip_mllp

        raw = "MSH|^~\\&|TEST|FAC|||20260218||ORM^O01|1|P|2.5"
        framed = add_mllp(raw)
        assert framed.startswith(b"\x0b")
        assert framed.endswith(b"\x1c\x0d")

        stripped = strip_mllp(framed)
        assert stripped == raw

    def test_parse_mllp_bytes(self):
        from services.hl7v2_parser import HL7v2Parser, add_mllp

        parser = HL7v2Parser()
        framed = add_mllp(self.ORM_MESSAGE)
        result = parser.parse(framed)
        assert result.message_type == "ORM"

    def test_build_ack(self):
        from services.hl7v2_parser import HL7v2Parser

        parser = HL7v2Parser()
        result = parser.parse(self.ORM_MESSAGE)
        ack = parser.build_ack(result, ack_code="AA")
        assert "MSH|" in ack
        assert "MSA|AA|MSG00001" in ack
        assert "ACK^O01" in ack


# ---------------------------------------------------------------------------
# #109 - Enhanced Audit Logging
# ---------------------------------------------------------------------------


class TestEnhancedAuditEvents:
    """Test new audit event types (#109)."""

    def test_fhir_event_types_exist(self):
        from auth.audit import AuditEvents

        assert AuditEvents.FHIR_READ == "FHIR_READ"
        assert AuditEvents.FHIR_SEARCH == "FHIR_SEARCH"
        assert AuditEvents.FHIR_EXPORT == "FHIR_EXPORT"

    def test_dicom_event_types_exist(self):
        from auth.audit import AuditEvents

        assert AuditEvents.DICOM_EXPORT == "DICOM_EXPORT"
        assert AuditEvents.DICOM_QUERY == "DICOM_QUERY"
        assert AuditEvents.DICOM_RETRIEVE == "DICOM_RETRIEVE"

    def test_data_event_types_exist(self):
        from auth.audit import AuditEvents

        assert AuditEvents.DATA_EXPORT == "DATA_EXPORT"
        assert AuditEvents.DATA_DOWNLOAD == "DATA_DOWNLOAD"
        assert AuditEvents.DATA_PRINT == "DATA_PRINT"

    def test_integration_event_types_exist(self):
        from auth.audit import AuditEvents

        assert AuditEvents.EHEALTH_TOKEN_REQUEST == "EHEALTH_TOKEN_REQUEST"
        assert AuditEvents.EHBOX_MESSAGE_SENT == "EHBOX_MESSAGE_SENT"
        assert AuditEvents.HL7_MESSAGE_PARSED == "HL7_MESSAGE_PARSED"
        assert AuditEvents.APSR_GENERATED == "APSR_GENERATED"
        assert AuditEvents.TERMINOLOGY_LOOKUP == "TERMINOLOGY_LOOKUP"

    def test_existing_events_preserved(self):
        """Existing event types must not be removed."""
        from auth.audit import AuditEvents

        assert AuditEvents.LOGIN == "LOGIN"
        assert AuditEvents.LOGOUT == "LOGOUT"
        assert AuditEvents.SLIDE_VIEWED == "SLIDE_VIEWED"
        assert AuditEvents.ANNOTATION_CREATED == "ANNOTATION_CREATED"
        assert AuditEvents.ML_PREDICTION == "ML_PREDICTION"
        assert AuditEvents.BREAK_GLASS_ACTIVATED == "BREAK_GLASS_ACTIVATED"
        assert AuditEvents.SESSION_SAVED == "SESSION_SAVED"

    @pytest.mark.asyncio
    async def test_compliance_fields(self, tmp_path):
        """Test new compliance-specific fields in log_audit_event."""
        from auth.audit import log_audit_event
        from auth.schemas import CurrentUser

        log_file = tmp_path / "audit.jsonl"
        user = CurrentUser(sub="dr-martin", username="dr.martin", roles=["MEDECIN"])

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
            patch("auth.audit._persist_to_db", new_callable=AsyncMock),
        ):
            await log_audit_event(
                event_type="FHIR_READ",
                action="READ",
                user=user,
                resource_type="DiagnosticReport",
                resource_id="slide-001",
                data_classification="confidential",
                legal_basis="legal_obligation",
                retention_years=30,
            )

        content = log_file.read_text().strip()
        parsed = json.loads(content)
        assert parsed["event_type"] == "FHIR_READ"
        assert parsed["data_classification"] == "confidential"
        assert parsed["legal_basis"] == "legal_obligation"
        assert parsed["retention_years"] == 30


class TestAuditSearch:
    """Test audit event search functionality."""

    def test_search_by_user(self, tmp_path):
        from auth.audit import _persist_to_json, search_audit_events

        log_file = tmp_path / "audit.jsonl"

        events = [
            {
                "id": "1",
                "timestamp": "2026-02-18T10:00:00Z",
                "user_sub": "dr-martin",
                "event_type": "SLIDE_VIEWED",
            },
            {
                "id": "2",
                "timestamp": "2026-02-18T11:00:00Z",
                "user_sub": "dr-dupont",
                "event_type": "SLIDE_VIEWED",
            },
            {
                "id": "3",
                "timestamp": "2026-02-18T12:00:00Z",
                "user_sub": "dr-martin",
                "event_type": "FHIR_READ",
            },
        ]

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
        ):
            for event in events:
                _persist_to_json(event)

            results = search_audit_events(user_sub="dr-martin")

        assert len(results) == 2
        assert all(e["user_sub"] == "dr-martin" for e in results)

    def test_search_by_event_type(self, tmp_path):
        from auth.audit import _persist_to_json, search_audit_events

        log_file = tmp_path / "audit.jsonl"

        events = [
            {"id": "1", "timestamp": "2026-02-18T10:00:00Z", "event_type": "SLIDE_VIEWED"},
            {"id": "2", "timestamp": "2026-02-18T11:00:00Z", "event_type": "FHIR_READ"},
            {"id": "3", "timestamp": "2026-02-18T12:00:00Z", "event_type": "FHIR_READ"},
        ]

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
        ):
            for event in events:
                _persist_to_json(event)

            results = search_audit_events(event_type="FHIR_READ")

        assert len(results) == 2
        assert all(e["event_type"] == "FHIR_READ" for e in results)

    def test_search_by_date_range(self, tmp_path):
        from auth.audit import _persist_to_json, search_audit_events

        log_file = tmp_path / "audit.jsonl"

        events = [
            {"id": "1", "timestamp": "2026-02-17T10:00:00Z", "event_type": "SLIDE_VIEWED"},
            {"id": "2", "timestamp": "2026-02-18T11:00:00Z", "event_type": "SLIDE_VIEWED"},
            {"id": "3", "timestamp": "2026-02-19T12:00:00Z", "event_type": "SLIDE_VIEWED"},
        ]

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
        ):
            for event in events:
                _persist_to_json(event)

            results = search_audit_events(
                from_date="2026-02-18T00:00:00Z",
                to_date="2026-02-18T23:59:59Z",
            )

        assert len(results) == 1
        assert results[0]["id"] == "2"

    def test_search_pagination(self, tmp_path):
        from auth.audit import _persist_to_json, search_audit_events

        log_file = tmp_path / "audit.jsonl"

        events = [
            {"id": str(i), "timestamp": f"2026-02-18T{i:02d}:00:00Z", "event_type": "TEST"}
            for i in range(10)
        ]

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
        ):
            for event in events:
                _persist_to_json(event)

            results = search_audit_events(limit=3, offset=2)

        assert len(results) == 3

    def test_search_empty_log(self, tmp_path):
        from auth.audit import search_audit_events

        log_file = tmp_path / "nonexistent.jsonl"

        with patch("auth.audit._AUDIT_LOG_FILE", log_file):
            results = search_audit_events()

        assert results == []

    def test_search_sorted_descending(self, tmp_path):
        from auth.audit import _persist_to_json, search_audit_events

        log_file = tmp_path / "audit.jsonl"

        events = [
            {"id": "1", "timestamp": "2026-02-18T08:00:00Z", "event_type": "A"},
            {"id": "2", "timestamp": "2026-02-18T12:00:00Z", "event_type": "B"},
            {"id": "3", "timestamp": "2026-02-18T10:00:00Z", "event_type": "C"},
        ]

        with (
            patch("auth.audit._AUDIT_LOG_DIR", tmp_path),
            patch("auth.audit._AUDIT_LOG_FILE", log_file),
        ):
            for event in events:
                _persist_to_json(event)

            results = search_audit_events()

        assert results[0]["id"] == "2"  # 12:00 first
        assert results[1]["id"] == "3"  # 10:00 second
        assert results[2]["id"] == "1"  # 08:00 last


class TestGDPRRegister:
    """Test GDPR Article 30 processing register."""

    def test_register_exists(self):
        from auth.audit import GDPR_PROCESSING_REGISTER

        assert len(GDPR_PROCESSING_REGISTER) >= 4

    def test_register_has_required_fields(self):
        from auth.audit import GDPR_PROCESSING_REGISTER

        required_fields = [
            "activity",
            "purpose",
            "legal_basis",
            "data_categories",
            "data_subjects",
            "recipients",
            "retention_years",
            "security_measures",
        ]
        for activity in GDPR_PROCESSING_REGISTER:
            for field in required_fields:
                assert field in activity, f"Missing {field} in activity {activity.get('activity')}"

    def test_register_has_slide_viewing(self):
        from auth.audit import GDPR_PROCESSING_REGISTER

        activities = [a["activity"] for a in GDPR_PROCESSING_REGISTER]
        assert any("Slide" in a for a in activities)


# ---------------------------------------------------------------------------
# #113 - IHE APSR (Anatomic Pathology Structured Report)
# ---------------------------------------------------------------------------


class TestAPSRBuilder:
    """Test APSR (Anatomic Pathology Structured Report) builder."""

    def test_build_basic(self):
        from services.apsr import APSRBuilder

        builder = APSRBuilder(mock_mode=True)
        result = builder.build(slide_id="slide-001")
        assert result.slide_id == "slide-001"
        assert result.status == "mock"
        assert len(result.xml) > 0
        assert "ClinicalDocument" in result.xml

    def test_build_deterministic(self):
        """Same slide_id should produce same document_id."""
        from services.apsr import APSRBuilder

        builder = APSRBuilder(mock_mode=True)
        r1 = builder.build(slide_id="slide-001")
        r2 = builder.build(slide_id="slide-001")
        assert r1.document_id == r2.document_id

    def test_build_different_slides(self):
        """Different slide_ids should produce different document_ids."""
        from services.apsr import APSRBuilder

        builder = APSRBuilder(mock_mode=True)
        r1 = builder.build(slide_id="slide-001")
        r2 = builder.build(slide_id="slide-002")
        assert r1.document_id != r2.document_id

    def test_sections_present(self):
        from services.apsr import APSRBuilder

        builder = APSRBuilder(mock_mode=True)
        result = builder.build(slide_id="slide-001")
        assert "Clinical Information" in result.sections
        assert "Macroscopic Description" in result.sections
        assert "Microscopic Description" in result.sections
        assert "Diagnosis" in result.sections

    def test_cda_xml_structure(self):
        from services.apsr import APSRBuilder

        builder = APSRBuilder(mock_mode=True)
        result = builder.build(slide_id="slide-001")
        xml = result.xml
        assert '<?xml version="1.0"' in xml
        assert "ClinicalDocument" in xml
        assert "templateId" in xml
        assert "IHE PaLM APSR Profile" in xml
        assert "structuredBody" in xml

    def test_build_with_request(self):
        from services.apsr import (
            APSRBuilder,
            APSRClinicalInfo,
            APSRDiagnosis,
            APSRMicroscopic,
            APSRRequest,
        )

        builder = APSRBuilder(mock_mode=True)
        request = APSRRequest(
            clinical_info=APSRClinicalInfo(
                clinical_history="Lesion suspecte bras gauche",
                specimen_type="Biopsie cutanee",
            ),
            microscopic=APSRMicroscopic(
                histological_type="Carcinome basocellulaire",
                grade="Grade II",
                annotations_summary=[
                    {"label": "Tumeur", "count": 5},
                    {"label": "Stroma", "count": 3},
                ],
            ),
            diagnosis=APSRDiagnosis(
                primary_diagnosis="Carcinome basocellulaire nodulaire",
                snomed_codes=[
                    {"code": "108369006", "display": "Neoplasm"},
                ],
            ),
            patient_name="Jean Dupont",
            performer_name="Dr. Martin",
        )
        result = builder.build(slide_id="slide-001", request=request)
        assert "Lesion suspecte" in result.xml
        assert "basocellulaire" in result.xml
        assert "Jean Dupont" in result.xml
        assert "Dr. Martin" in result.xml

    def test_xml_escaping(self):
        """Special characters in input should be XML-escaped."""
        from services.apsr import APSRBuilder, APSRClinicalInfo, APSRRequest

        builder = APSRBuilder(mock_mode=True)
        request = APSRRequest(
            clinical_info=APSRClinicalInfo(
                clinical_history="Test <script>alert('xss')</script> & more",
            ),
        )
        result = builder.build(slide_id="slide-001", request=request)
        assert "<script>" not in result.xml
        assert "&lt;script&gt;" in result.xml

    def test_cda_loinc_codes(self):
        """CDA document should reference LOINC codes for sections."""
        from services.apsr import APSRBuilder

        builder = APSRBuilder(mock_mode=True)
        result = builder.build(slide_id="slide-001")
        xml = result.xml
        # Section codes from IHE PaLM
        assert "22636-5" in xml  # Clinical history
        assert "22634-0" in xml  # Gross observation
        assert "22635-7" in xml  # Microscopic observation
        assert "22637-3" in xml  # Diagnosis
