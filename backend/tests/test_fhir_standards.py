"""
Tests for FHIR R4 Standards Implementation.

Covers:
- #103 DiagnosticReport API (CapabilityStatement, contained resources, search)
- #104 SMART on FHIR App Launch (launch handler, .well-known config)
- #112 US Core / CA Core Profile Conformance (patient profiles, validation)
- #114 mCODE FHIR IG for Oncology (CancerCondition, TNM, TumorMarker)
"""

# ---------------------------------------------------------------------------
# #103 — DiagnosticReport & CapabilityStatement
# ---------------------------------------------------------------------------


class TestCapabilityStatement:
    """Tests for the FHIR CapabilityStatement builder."""

    def test_build_capability_statement_structure(self):
        from fhir.capability import build_capability_statement

        cs = build_capability_statement()
        assert cs["resourceType"] == "CapabilityStatement"
        assert cs["fhirVersion"] == "4.0.1"
        assert cs["status"] == "active"
        assert cs["kind"] == "instance"

    def test_capability_statement_rest_resources(self):
        from fhir.capability import build_capability_statement

        cs = build_capability_statement()
        rest = cs["rest"]
        assert len(rest) == 1
        assert rest[0]["mode"] == "server"

        resource_types = [r["type"] for r in rest[0]["resource"]]
        assert "DiagnosticReport" in resource_types
        assert "Patient" in resource_types
        assert "Observation" in resource_types
        assert "Condition" in resource_types

    def test_capability_statement_search_params(self):
        from fhir.capability import build_capability_statement

        cs = build_capability_statement()
        dr_resource = next(
            r for r in cs["rest"][0]["resource"]
            if r["type"] == "DiagnosticReport"
        )
        search_names = [p["name"] for p in dr_resource["searchParam"]]
        assert "patient" in search_names
        assert "status" in search_names

    def test_capability_statement_smart_security(self):
        from fhir.capability import build_capability_statement

        cs = build_capability_statement()
        security = cs["rest"][0]["security"]
        assert security["cors"] is True
        service_codes = [
            c["code"]
            for svc in security["service"]
            for c in svc.get("coding", [])
        ]
        assert "SMART-on-FHIR" in service_codes

    def test_capability_statement_custom_base_url(self):
        from fhir.capability import build_capability_statement

        cs = build_capability_statement(base_url="https://hospital.example.org/fhir")
        assert cs["url"] == "https://hospital.example.org/fhir/metadata"
        assert cs["implementation"]["url"] == "https://hospital.example.org/fhir"


class TestDiagnosticReport:
    """Tests for the enhanced DiagnosticReport builder."""

    def test_basic_report(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(slide_id="abc123", slide_name="test.svs")
        assert report["resourceType"] == "DiagnosticReport"
        assert report["id"] == "slide-abc123"
        assert report["status"] == "preliminary"

    def test_report_contains_patient(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(
            slide_id="abc123",
            patient_id="P001",
            patient_name="Jane Doe",
        )
        contained = report.get("contained", [])
        patient_resources = [c for c in contained if c["resourceType"] == "Patient"]
        assert len(patient_resources) == 1
        assert patient_resources[0]["identifier"][0]["value"] == "P001"

    def test_report_contains_practitioner(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(
            slide_id="abc123",
            performer_name="Dr. Martin",
            performer_sub="dr-martin-uuid",
        )
        contained = report.get("contained", [])
        practitioner_resources = [
            c for c in contained if c["resourceType"] == "Practitioner"
        ]
        assert len(practitioner_resources) == 1
        assert practitioner_resources[0]["name"][0]["text"] == "Dr. Martin"

    def test_report_contains_specimen(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(
            slide_id="abc123",
            specimen_type="Biopsy specimen",
        )
        contained = report.get("contained", [])
        specimen_resources = [c for c in contained if c["resourceType"] == "Specimen"]
        assert len(specimen_resources) == 1
        assert specimen_resources[0]["type"]["text"] == "Biopsy specimen"

    def test_report_specimen_reference(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(slide_id="abc123")
        assert "specimen" in report
        assert len(report["specimen"]) == 1
        assert report["specimen"][0]["reference"].startswith("#specimen-")

    def test_report_result_observations(self):
        from fhir.resources import build_diagnostic_report

        obs = [
            {"id": "obs-1", "code": {"text": "Ki-67 marker"}},
            {"id": "obs-2", "code": {"text": "HER2 marker"}},
        ]
        report = build_diagnostic_report(
            slide_id="abc123",
            result_observations=obs,
        )
        assert "result" in report
        assert len(report["result"]) == 2
        refs = [r["reference"] for r in report["result"]]
        assert "Observation/obs-1" in refs
        assert "Observation/obs-2" in refs

    def test_report_presented_form_pdf(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(
            slide_id="abc123",
            slide_name="test.svs",
            pdf_url="https://hospital.example.org/reports/abc123.pdf",
        )
        assert "presentedForm" in report
        assert report["presentedForm"][0]["contentType"] == "application/pdf"
        assert report["presentedForm"][0]["url"].endswith("abc123.pdf")

    def test_report_us_core_profile(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(slide_id="abc123")
        profiles = report["meta"]["profile"]
        assert any("us-core-diagnosticreport" in p for p in profiles)

    def test_report_conclusion_default(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(slide_id="abc123", annotations_count=5)
        assert "5 annotation(s) recorded" in report["conclusion"]

    def test_report_conclusion_custom(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(
            slide_id="abc123",
            conclusion="Malignant neoplasm confirmed.",
        )
        assert report["conclusion"] == "Malignant neoplasm confirmed."

    def test_report_ml_tags_to_results(self):
        from fhir.resources import build_diagnostic_report

        report = build_diagnostic_report(
            slide_id="abc123",
            patient_id="P001",
            ml_tags={"ki67": 0.35, "her2": "positive"},
        )
        assert "result" in report
        assert len(report["result"]) == 2


class TestDiagnosticReportSearch:
    """Tests for DiagnosticReport search/filter."""

    def _make_reports(self):
        from fhir.resources import build_diagnostic_report

        return [
            build_diagnostic_report(
                slide_id="s1", patient_id="P001", status="preliminary"
            ),
            build_diagnostic_report(
                slide_id="s2", patient_id="P002", status="final"
            ),
            build_diagnostic_report(
                slide_id="s3", patient_id="P001", status="final"
            ),
        ]

    def test_search_by_patient(self):
        from fhir.resources import search_diagnostic_reports

        reports = self._make_reports()
        bundle = search_diagnostic_reports(reports, patient_id="P001")
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "searchset"
        assert bundle["total"] == 2

    def test_search_by_status(self):
        from fhir.resources import search_diagnostic_reports

        reports = self._make_reports()
        bundle = search_diagnostic_reports(reports, status="final")
        assert bundle["total"] == 2

    def test_search_by_patient_and_status(self):
        from fhir.resources import search_diagnostic_reports

        reports = self._make_reports()
        bundle = search_diagnostic_reports(
            reports, patient_id="P001", status="final"
        )
        assert bundle["total"] == 1

    def test_search_no_results(self):
        from fhir.resources import search_diagnostic_reports

        reports = self._make_reports()
        bundle = search_diagnostic_reports(reports, patient_id="P999")
        assert bundle["total"] == 0
        assert bundle["entry"] == []

    def test_search_no_filters(self):
        from fhir.resources import search_diagnostic_reports

        reports = self._make_reports()
        bundle = search_diagnostic_reports(reports)
        assert bundle["total"] == 3


# ---------------------------------------------------------------------------
# #104 — SMART on FHIR
# ---------------------------------------------------------------------------


class TestSMARTConfiguration:
    """Tests for SMART on FHIR configuration."""

    def test_smart_config_structure(self):
        from fhir.smart import get_smart_configuration

        config = get_smart_configuration()
        assert "authorization_endpoint" in config
        assert "token_endpoint" in config
        assert "scopes_supported" in config
        assert "capabilities" in config

    def test_smart_config_scopes(self):
        from fhir.smart import get_smart_configuration

        config = get_smart_configuration()
        scopes = config["scopes_supported"]
        assert "openid" in scopes
        assert "launch" in scopes
        assert "launch/patient" in scopes
        assert "patient/Patient.read" in scopes
        assert "patient/DiagnosticReport.read" in scopes

    def test_smart_config_capabilities(self):
        from fhir.smart import get_smart_configuration

        config = get_smart_configuration()
        caps = config["capabilities"]
        assert "launch-ehr" in caps
        assert "launch-standalone" in caps
        assert "context-ehr-patient" in caps

    def test_smart_config_pkce(self):
        from fhir.smart import get_smart_configuration

        config = get_smart_configuration()
        assert "S256" in config["code_challenge_methods_supported"]

    def test_smart_config_custom_base_url(self):
        from fhir.smart import get_smart_configuration

        config = get_smart_configuration(
            base_url="https://hospital.example.org/fhir"
        )
        assert config["authorization_endpoint"].startswith("https://hospital")
        assert config["token_endpoint"].startswith("https://hospital")


class TestSMARTLaunch:
    """Tests for SMART on FHIR EHR launch handler."""

    def test_ehr_launch_returns_context(self):
        from fhir.smart import handle_ehr_launch

        ctx = handle_ehr_launch(launch="abc123", iss="https://ehr.example.org/fhir")
        assert "launch_id" in ctx
        assert "patient_id" in ctx
        assert "encounter_id" in ctx
        assert ctx["iss"] == "https://ehr.example.org/fhir"
        assert ctx["mock_mode"] is True

    def test_ehr_launch_deterministic(self):
        from fhir.smart import handle_ehr_launch

        ctx1 = handle_ehr_launch(launch="abc123", iss="https://ehr.example.org/fhir")
        ctx2 = handle_ehr_launch(launch="abc123", iss="https://ehr.example.org/fhir")
        assert ctx1["patient_id"] == ctx2["patient_id"]
        assert ctx1["encounter_id"] == ctx2["encounter_id"]
        assert ctx1["launch_id"] == ctx2["launch_id"]

    def test_ehr_launch_different_params_different_ids(self):
        from fhir.smart import handle_ehr_launch

        ctx1 = handle_ehr_launch(launch="abc", iss="https://ehr1.example.org/fhir")
        ctx2 = handle_ehr_launch(launch="xyz", iss="https://ehr2.example.org/fhir")
        assert ctx1["patient_id"] != ctx2["patient_id"]

    def test_ehr_launch_intent(self):
        from fhir.smart import handle_ehr_launch

        ctx = handle_ehr_launch(launch="abc", iss="https://ehr.example.org/fhir")
        assert ctx["intent"] == "pathology-review"

    def test_ehr_launch_need_patient_banner(self):
        from fhir.smart import handle_ehr_launch

        ctx = handle_ehr_launch(launch="abc", iss="https://ehr.example.org/fhir")
        assert ctx["need_patient_banner"] is True


class TestPatientContextSMART:
    """Tests for patient context with SMART integration."""

    def test_url_params_source(self):
        from fhir.patient_context import get_patient_context

        ctx = get_patient_context(patient_id="P001", patient_name="Jane")
        assert ctx.patient_id == "P001"
        assert ctx.source == "url_params"

    def test_smart_launch_source(self):
        from fhir.patient_context import get_patient_context, store_smart_context

        store_smart_context("launch-test-1", {
            "patient_id": "smart-P001",
            "encounter_id": "enc-001",
        })
        ctx = get_patient_context(smart_launch_id="launch-test-1")
        assert ctx.patient_id == "smart-P001"
        assert ctx.encounter_id == "enc-001"
        assert ctx.source == "smart_launch"

    def test_smart_overrides_url_params(self):
        from fhir.patient_context import get_patient_context, store_smart_context

        store_smart_context("launch-test-2", {
            "patient_id": "smart-P002",
            "encounter_id": "enc-002",
        })
        ctx = get_patient_context(
            patient_id="url-P999",
            smart_launch_id="launch-test-2",
        )
        assert ctx.patient_id == "smart-P002"
        assert ctx.source == "smart_launch"

    def test_unknown_smart_launch_falls_back(self):
        from fhir.patient_context import get_patient_context

        ctx = get_patient_context(
            patient_id="url-P001",
            smart_launch_id="nonexistent-launch",
        )
        assert ctx.patient_id == "url-P001"
        assert ctx.source == "url_params"


# ---------------------------------------------------------------------------
# #112 — US Core / CA Core Profile Conformance
# ---------------------------------------------------------------------------


class TestUSCorePatient:
    """Tests for US Core Patient profile builder and validator."""

    def test_us_core_patient_structure(self):
        from fhir.profiles import build_us_core_patient

        p = build_us_core_patient(
            patient_id="P001",
            family_name="Doe",
            given_name="Jane",
            gender="female",
        )
        assert p["resourceType"] == "Patient"
        assert p["id"] == "P001"
        assert p["gender"] == "female"
        assert p["name"][0]["family"] == "Doe"
        assert "Jane" in p["name"][0]["given"]

    def test_us_core_patient_profile_url(self):
        from fhir.profiles import US_CORE_PATIENT_PROFILE, build_us_core_patient

        p = build_us_core_patient(patient_id="P001")
        assert US_CORE_PATIENT_PROFILE in p["meta"]["profile"]

    def test_us_core_patient_identifier(self):
        from fhir.profiles import build_us_core_patient

        p = build_us_core_patient(
            patient_id="P001",
            identifier_value="MRN-12345",
            identifier_system="http://hospital.example.org/mrn",
        )
        assert p["identifier"][0]["value"] == "MRN-12345"
        assert p["identifier"][0]["system"] == "http://hospital.example.org/mrn"

    def test_us_core_patient_race_extension(self):
        from fhir.profiles import build_us_core_patient

        p = build_us_core_patient(
            patient_id="P001",
            race_code="2106-3",
            race_display="White",
        )
        race_ext = [
            e for e in p.get("extension", [])
            if "us-core-race" in e["url"]
        ]
        assert len(race_ext) == 1
        omb = race_ext[0]["extension"][0]
        assert omb["valueCoding"]["code"] == "2106-3"

    def test_us_core_patient_ethnicity_extension(self):
        from fhir.profiles import build_us_core_patient

        p = build_us_core_patient(
            patient_id="P001",
            ethnicity_code="2186-5",
            ethnicity_display="Not Hispanic or Latino",
        )
        eth_ext = [
            e for e in p.get("extension", [])
            if "us-core-ethnicity" in e["url"]
        ]
        assert len(eth_ext) == 1

    def test_us_core_patient_birth_date(self):
        from fhir.profiles import build_us_core_patient

        p = build_us_core_patient(patient_id="P001", birth_date="1980-06-15")
        assert p["birthDate"] == "1980-06-15"

    def test_us_core_patient_validates(self):
        from fhir.profiles import build_us_core_patient, validate_us_core_patient

        p = build_us_core_patient(
            patient_id="P001",
            family_name="Doe",
            given_name="Jane",
            gender="female",
        )
        errors = validate_us_core_patient(p)
        assert errors == []

    def test_us_core_validation_missing_identifier(self):
        from fhir.profiles import US_CORE_PATIENT_PROFILE, validate_us_core_patient

        p = {
            "resourceType": "Patient",
            "meta": {"profile": [US_CORE_PATIENT_PROFILE]},
            "name": [{"family": "Doe"}],
            "gender": "female",
        }
        errors = validate_us_core_patient(p)
        assert any("identifier" in e for e in errors)

    def test_us_core_validation_missing_gender(self):
        from fhir.profiles import US_CORE_PATIENT_PROFILE, validate_us_core_patient

        p = {
            "resourceType": "Patient",
            "meta": {"profile": [US_CORE_PATIENT_PROFILE]},
            "identifier": [{"value": "P001"}],
            "name": [{"family": "Doe"}],
        }
        errors = validate_us_core_patient(p)
        assert any("gender" in e for e in errors)

    def test_us_core_validation_wrong_resource_type(self):
        from fhir.profiles import validate_us_core_patient

        errors = validate_us_core_patient({"resourceType": "Observation"})
        assert any("resourceType" in e for e in errors)


class TestCACorePatient:
    """Tests for CA Core Patient profile builder and validator."""

    def test_ca_core_patient_structure(self):
        from fhir.profiles import build_ca_core_patient

        p = build_ca_core_patient(
            patient_id="P001",
            family_name="Tremblay",
            given_name="Marie",
            gender="female",
        )
        assert p["resourceType"] == "Patient"
        assert p["name"][0]["family"] == "Tremblay"

    def test_ca_core_patient_profile_url(self):
        from fhir.profiles import CA_CORE_PATIENT_PROFILE, build_ca_core_patient

        p = build_ca_core_patient(patient_id="P001")
        assert CA_CORE_PATIENT_PROFILE in p["meta"]["profile"]

    def test_ca_core_patient_health_number_on(self):
        from fhir.profiles import build_ca_core_patient

        p = build_ca_core_patient(
            patient_id="P001",
            health_number="1234-567-890",
            health_number_jurisdiction="ON",
        )
        ident = p["identifier"][0]
        assert ident["value"] == "1234-567-890"
        assert "ca-on-patient-hcn" in ident["system"]
        assert ident["type"]["coding"][0]["code"] == "JHN"

    def test_ca_core_patient_health_number_qc(self):
        from fhir.profiles import build_ca_core_patient

        p = build_ca_core_patient(
            patient_id="P001",
            health_number="TREM 8006 1512",
            health_number_jurisdiction="QC",
        )
        assert "ca-qc-patient-hcn" in p["identifier"][0]["system"]

    def test_ca_core_patient_no_health_number(self):
        from fhir.profiles import build_ca_core_patient

        p = build_ca_core_patient(patient_id="P001")
        assert p["identifier"][0]["value"] == "P001"

    def test_ca_core_patient_validates(self):
        from fhir.profiles import build_ca_core_patient, validate_ca_core_patient

        p = build_ca_core_patient(
            patient_id="P001",
            family_name="Tremblay",
            gender="female",
        )
        errors = validate_ca_core_patient(p)
        assert errors == []

    def test_ca_core_validation_missing_profile(self):
        from fhir.profiles import validate_ca_core_patient

        p = {
            "resourceType": "Patient",
            "meta": {"profile": []},
            "identifier": [{"value": "P001"}],
            "name": [{"family": "Doe"}],
            "gender": "female",
        }
        errors = validate_ca_core_patient(p)
        assert any("profile" in e for e in errors)


# ---------------------------------------------------------------------------
# #114 — mCODE FHIR IG for Oncology
# ---------------------------------------------------------------------------


class TestMCODECancerCondition:
    """Tests for mCODE PrimaryCancerCondition builder and validator."""

    def test_cancer_condition_structure(self):
        from fhir.profiles import build_cancer_condition

        c = build_cancer_condition(
            condition_id="cond-001",
            patient_id="P001",
        )
        assert c["resourceType"] == "Condition"
        assert c["id"] == "cond-001"
        assert c["subject"]["reference"] == "Patient/P001"
        assert c["clinicalStatus"]["coding"][0]["code"] == "active"

    def test_cancer_condition_profile_url(self):
        from fhir.profiles import (
            MCODE_CANCER_CONDITION_PROFILE,
            build_cancer_condition,
        )

        c = build_cancer_condition(condition_id="cond-001", patient_id="P001")
        assert MCODE_CANCER_CONDITION_PROFILE in c["meta"]["profile"]

    def test_cancer_condition_histology(self):
        from fhir.profiles import build_cancer_condition

        c = build_cancer_condition(
            condition_id="cond-001",
            patient_id="P001",
            histology_code="8500/3",
            histology_display="Infiltrating duct carcinoma",
        )
        coding = c["code"]["coding"][0]
        assert coding["code"] == "8500/3"
        assert "duct carcinoma" in coding["display"]

    def test_cancer_condition_body_site(self):
        from fhir.profiles import build_cancer_condition

        c = build_cancer_condition(
            condition_id="cond-001",
            patient_id="P001",
            body_site_code="76752008",
            body_site_display="Breast structure",
        )
        site = c["bodySite"][0]["coding"][0]
        assert site["system"] == "http://snomed.info/sct"
        assert site["code"] == "76752008"

    def test_cancer_condition_tnm_stage_reference(self):
        from fhir.profiles import build_cancer_condition

        c = build_cancer_condition(
            condition_id="cond-001",
            patient_id="P001",
            tnm_stage_group_id="tnm-obs-001",
        )
        assert "stage" in c
        ref = c["stage"][0]["assessment"][0]["reference"]
        assert ref == "Observation/tnm-obs-001"

    def test_cancer_condition_no_tnm(self):
        from fhir.profiles import build_cancer_condition

        c = build_cancer_condition(
            condition_id="cond-001",
            patient_id="P001",
        )
        assert "stage" not in c

    def test_cancer_condition_validates(self):
        from fhir.profiles import build_cancer_condition, validate_mcode_cancer_condition

        c = build_cancer_condition(condition_id="cond-001", patient_id="P001")
        errors = validate_mcode_cancer_condition(c)
        assert errors == []

    def test_cancer_condition_validation_missing_code(self):
        from fhir.profiles import (
            MCODE_CANCER_CONDITION_PROFILE,
            validate_mcode_cancer_condition,
        )

        c = {
            "resourceType": "Condition",
            "meta": {"profile": [MCODE_CANCER_CONDITION_PROFILE]},
            "subject": {"reference": "Patient/P001"},
            "clinicalStatus": {"coding": [{"code": "active"}]},
        }
        errors = validate_mcode_cancer_condition(c)
        assert any("code" in e for e in errors)


class TestMCODETNMStageGroup:
    """Tests for mCODE TNMStageGroup observation builder."""

    def test_tnm_stage_group_structure(self):
        from fhir.profiles import build_tnm_stage_group

        obs = build_tnm_stage_group(
            observation_id="tnm-001",
            patient_id="P001",
        )
        assert obs["resourceType"] == "Observation"
        assert obs["status"] == "final"
        assert obs["subject"]["reference"] == "Patient/P001"

    def test_tnm_stage_group_profile_url(self):
        from fhir.profiles import MCODE_TNM_STAGE_GROUP_PROFILE, build_tnm_stage_group

        obs = build_tnm_stage_group(observation_id="tnm-001", patient_id="P001")
        assert MCODE_TNM_STAGE_GROUP_PROFILE in obs["meta"]["profile"]

    def test_tnm_stage_group_value(self):
        from fhir.profiles import build_tnm_stage_group

        obs = build_tnm_stage_group(
            observation_id="tnm-001",
            patient_id="P001",
            stage_group_code="261638004",
            stage_group_display="Stage II",
        )
        value = obs["valueCodeableConcept"]["coding"][0]
        assert value["code"] == "261638004"
        assert value["display"] == "Stage II"

    def test_tnm_stage_group_loinc_code(self):
        from fhir.profiles import build_tnm_stage_group

        obs = build_tnm_stage_group(observation_id="tnm-001", patient_id="P001")
        loinc = obs["code"]["coding"][0]
        assert loinc["system"] == "http://loinc.org"
        assert loinc["code"] == "21908-9"

    def test_tnm_components(self):
        from fhir.profiles import build_tnm_stage_group

        obs = build_tnm_stage_group(
            observation_id="tnm-001",
            patient_id="P001",
            t_display="T3",
            n_display="N1",
            m_display="M0",
        )
        components = obs["component"]
        assert len(components) == 3

        # T component
        t_comp = components[0]
        assert t_comp["code"]["coding"][0]["code"] == "21905-5"
        assert t_comp["valueCodeableConcept"]["coding"][0]["display"] == "T3"

        # N component
        n_comp = components[1]
        assert n_comp["code"]["coding"][0]["code"] == "21906-3"
        assert n_comp["valueCodeableConcept"]["coding"][0]["display"] == "N1"

        # M component
        m_comp = components[2]
        assert m_comp["code"]["coding"][0]["code"] == "21907-1"
        assert m_comp["valueCodeableConcept"]["coding"][0]["display"] == "M0"


class TestMCODETumorMarkerTest:
    """Tests for mCODE TumorMarkerTest observation builder."""

    def test_tumor_marker_structure(self):
        from fhir.profiles import build_tumor_marker_test

        obs = build_tumor_marker_test(
            observation_id="marker-001",
            patient_id="P001",
            marker_name="ki67",
            value=35.0,
        )
        assert obs["resourceType"] == "Observation"
        assert obs["status"] == "final"
        assert obs["subject"]["reference"] == "Patient/P001"

    def test_tumor_marker_profile_url(self):
        from fhir.profiles import MCODE_TUMOR_MARKER_PROFILE, build_tumor_marker_test

        obs = build_tumor_marker_test(
            observation_id="marker-001",
            patient_id="P001",
            marker_name="ki67",
        )
        assert MCODE_TUMOR_MARKER_PROFILE in obs["meta"]["profile"]

    def test_ki67_marker_loinc(self):
        from fhir.profiles import build_tumor_marker_test

        obs = build_tumor_marker_test(
            observation_id="marker-001",
            patient_id="P001",
            marker_name="ki67",
            value=35.0,
        )
        loinc = obs["code"]["coding"][0]
        assert loinc["code"] == "85319-2"
        assert obs["valueQuantity"]["value"] == 35.0
        assert obs["valueQuantity"]["unit"] == "%"

    def test_her2_marker_loinc(self):
        from fhir.profiles import build_tumor_marker_test

        obs = build_tumor_marker_test(
            observation_id="marker-002",
            patient_id="P001",
            marker_name="her2",
            value="3+",
        )
        loinc = obs["code"]["coding"][0]
        assert loinc["code"] == "85318-4"
        assert obs["valueString"] == "3+"

    def test_er_marker_loinc(self):
        from fhir.profiles import build_tumor_marker_test

        obs = build_tumor_marker_test(
            observation_id="marker-003",
            patient_id="P001",
            marker_name="er",
            value=95.0,
        )
        assert obs["code"]["coding"][0]["code"] == "85337-4"

    def test_pr_marker_loinc(self):
        from fhir.profiles import build_tumor_marker_test

        obs = build_tumor_marker_test(
            observation_id="marker-004",
            patient_id="P001",
            marker_name="pr",
            value=80.0,
        )
        assert obs["code"]["coding"][0]["code"] == "85339-0"

    def test_tumor_marker_interpretation(self):
        from fhir.profiles import build_tumor_marker_test

        obs = build_tumor_marker_test(
            observation_id="marker-001",
            patient_id="P001",
            marker_name="ki67",
            value=35.0,
            interpretation_code="H",
            interpretation_display="High",
        )
        interp = obs["interpretation"][0]["coding"][0]
        assert interp["code"] == "H"
        assert interp["display"] == "High"

    def test_tumor_marker_no_value(self):
        from fhir.profiles import build_tumor_marker_test

        obs = build_tumor_marker_test(
            observation_id="marker-001",
            patient_id="P001",
            marker_name="ki67",
        )
        assert "valueQuantity" not in obs
        assert "valueString" not in obs

    def test_tumor_marker_validates(self):
        from fhir.profiles import build_tumor_marker_test, validate_mcode_tumor_marker

        obs = build_tumor_marker_test(
            observation_id="marker-001",
            patient_id="P001",
            marker_name="ki67",
            value=35.0,
        )
        errors = validate_mcode_tumor_marker(obs)
        assert errors == []

    def test_tumor_marker_validation_missing_code(self):
        from fhir.profiles import MCODE_TUMOR_MARKER_PROFILE, validate_mcode_tumor_marker

        obs = {
            "resourceType": "Observation",
            "meta": {"profile": [MCODE_TUMOR_MARKER_PROFILE]},
            "status": "final",
            "subject": {"reference": "Patient/P001"},
        }
        errors = validate_mcode_tumor_marker(obs)
        assert any("code" in e for e in errors)


class TestMLTagsToTumorMarkers:
    """Tests for mapping VarunaPoC ML auto-tags to mCODE concepts."""

    def test_map_numeric_tags(self):
        from fhir.profiles import map_ml_tags_to_tumor_markers

        tags = {"ki67": 0.35, "her2": 2.0}
        markers = map_ml_tags_to_tumor_markers(
            tags=tags, patient_id="P001", slide_id="slide-abc"
        )
        assert len(markers) == 2
        marker_codes = [
            m["code"]["coding"][0]["code"] for m in markers
        ]
        assert "85319-2" in marker_codes  # ki67
        assert "85318-4" in marker_codes  # her2

    def test_map_string_tags(self):
        from fhir.profiles import map_ml_tags_to_tumor_markers

        tags = {"er": "positive", "pr": "negative"}
        markers = map_ml_tags_to_tumor_markers(
            tags=tags, patient_id="P001", slide_id="slide-abc"
        )
        assert len(markers) == 2

        # Check interpretation codes
        er_marker = next(
            m for m in markers if m["code"]["coding"][0]["code"] == "85337-4"
        )
        assert er_marker["interpretation"][0]["coding"][0]["code"] == "POS"

        pr_marker = next(
            m for m in markers if m["code"]["coding"][0]["code"] == "85339-0"
        )
        assert pr_marker["interpretation"][0]["coding"][0]["code"] == "NEG"

    def test_map_ki67_high_interpretation(self):
        from fhir.profiles import map_ml_tags_to_tumor_markers

        markers = map_ml_tags_to_tumor_markers(
            tags={"ki67": 0.25}, patient_id="P001", slide_id="slide-abc"
        )
        assert len(markers) == 1
        interp = markers[0]["interpretation"][0]["coding"][0]
        assert interp["code"] == "H"
        assert interp["display"] == "High"

    def test_map_ki67_low_interpretation(self):
        from fhir.profiles import map_ml_tags_to_tumor_markers

        markers = map_ml_tags_to_tumor_markers(
            tags={"ki67": 0.10}, patient_id="P001", slide_id="slide-abc"
        )
        assert len(markers) == 1
        interp = markers[0]["interpretation"][0]["coding"][0]
        assert interp["code"] == "L"
        assert interp["display"] == "Low"

    def test_map_ignores_unknown_tags(self):
        from fhir.profiles import map_ml_tags_to_tumor_markers

        tags = {"ki67": 0.35, "unknown_tag": 1.0, "cell_count": 500}
        markers = map_ml_tags_to_tumor_markers(
            tags=tags, patient_id="P001", slide_id="slide-abc"
        )
        assert len(markers) == 1  # Only ki67

    def test_map_deterministic_ids(self):
        from fhir.profiles import map_ml_tags_to_tumor_markers

        markers1 = map_ml_tags_to_tumor_markers(
            tags={"ki67": 0.35}, patient_id="P001", slide_id="slide-abc"
        )
        markers2 = map_ml_tags_to_tumor_markers(
            tags={"ki67": 0.35}, patient_id="P001", slide_id="slide-abc"
        )
        assert markers1[0]["id"] == markers2[0]["id"]

    def test_map_empty_tags(self):
        from fhir.profiles import map_ml_tags_to_tumor_markers

        markers = map_ml_tags_to_tumor_markers(
            tags={}, patient_id="P001", slide_id="slide-abc"
        )
        assert markers == []
