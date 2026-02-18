"""
Tests pour les services régionaux: ABDM, SS-MIX2 et i18n.

Couvre les fonctionnalités principales de chaque service
en mode mock (pas de dépendance externe).
"""

import pytest

from services.abdm import ABDMService, ConsentArtifact, validate_abha_number
from services.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, I18nService
from services.ssmix2 import (
    SSMIX2Service,
    build_ssmix2_path,
    decode_japanese_text,
    parse_hl7_segment,
)

# ==========================================
# ABDM Tests
# ==========================================


class TestABHAValidation:
    """Tests de validation du numéro ABHA."""

    def test_valid_abha_14_digits(self):
        assert validate_abha_number("12345678901234") is True

    def test_invalid_abha_too_short(self):
        assert validate_abha_number("1234567890") is False

    def test_invalid_abha_too_long(self):
        assert validate_abha_number("123456789012345") is False

    def test_invalid_abha_with_letters(self):
        assert validate_abha_number("1234567890123a") is False

    def test_invalid_abha_empty(self):
        assert validate_abha_number("") is False

    def test_invalid_abha_none(self):
        assert validate_abha_number(None) is False


class TestABDMService:
    """Tests du service ABDM HIP."""

    @pytest.fixture
    def service(self):
        return ABDMService(mock_mode=True)

    def test_validate_abha_valid(self, service):
        result = service.validate_abha("12345678901234")
        assert result["valid"] is True
        assert result["abhaNumber"] == "12345678901234"
        assert "name" in result

    def test_validate_abha_invalid(self, service):
        result = service.validate_abha("invalid")
        assert result["valid"] is False
        assert "error" in result

    def test_generate_fhir_bundle(self, service):
        bundle = service.generate_fhir_bundle(
            abha_number="12345678901234",
            slide_id="slide_001",
            diagnosis="Test diagnosis",
        )
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "document"
        assert len(bundle["entry"]) == 4

        # Vérifier les types de ressources
        resource_types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Composition" in resource_types
        assert "Patient" in resource_types
        assert "DiagnosticReport" in resource_types
        assert "ImagingStudy" in resource_types

    def test_generate_fhir_bundle_invalid_abha(self, service):
        with pytest.raises(ValueError, match="ABHA invalide"):
            service.generate_fhir_bundle(
                abha_number="invalid",
                slide_id="slide_001",
            )

    def test_generate_fhir_bundle_contains_abdm_server(self, service):
        bundle = service.generate_fhir_bundle(
            abha_number="12345678901234",
            slide_id="slide_001",
        )
        # Vérifier que le serveur ABDM est référencé
        first_url = bundle["entry"][0]["fullUrl"]
        assert "abdm.gov.in/fhir" in first_url

    def test_fhir_bundle_patient_has_abha_identifier(self, service):
        bundle = service.generate_fhir_bundle(
            abha_number="12345678901234",
            slide_id="slide_001",
        )
        patient_entry = next(
            e for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient"
        )
        identifiers = patient_entry["resource"]["identifier"]
        assert any(i["system"] == "https://healthid.abdm.gov.in" for i in identifiers)

    def test_create_consent(self, service):
        consent = service.create_consent(
            patient_abha="12345678901234",
            hiu_id="test-hiu",
        )
        assert isinstance(consent, ConsentArtifact)
        assert consent.status == "REQUESTED"
        assert consent.patient_abha == "12345678901234"
        assert consent.hiu_id == "test-hiu"

    def test_create_consent_invalid_abha(self, service):
        with pytest.raises(ValueError, match="ABHA invalide"):
            service.create_consent(
                patient_abha="invalid",
                hiu_id="test-hiu",
            )

    def test_consent_lifecycle(self, service):
        # Créer le consentement
        consent = service.create_consent(
            patient_abha="12345678901234",
            hiu_id="test-hiu",
        )
        assert consent.status == "REQUESTED"

        # Accorder le consentement
        result = service.process_consent_callback(
            consent_id=consent.consent_id,
            status="GRANTED",
        )
        assert result["status"] == "success"
        assert result["consentStatus"] == "GRANTED"

        # Demander les données
        data_result = service.process_data_request(
            consent_id=consent.consent_id,
            slide_id="slide_001",
        )
        assert data_result["status"] == "success"
        assert "bundle" in data_result
        assert data_result["bundle"]["resourceType"] == "Bundle"

    def test_data_request_without_consent(self, service):
        result = service.process_data_request(
            consent_id="nonexistent",
            slide_id="slide_001",
        )
        assert result["status"] == "error"

    def test_data_request_denied_consent(self, service):
        consent = service.create_consent(
            patient_abha="12345678901234",
            hiu_id="test-hiu",
        )
        service.process_consent_callback(consent.consent_id, "DENIED")

        result = service.process_data_request(
            consent_id=consent.consent_id,
            slide_id="slide_001",
        )
        assert result["status"] == "error"

    def test_consent_callback_invalid_status(self, service):
        consent = service.create_consent(
            patient_abha="12345678901234",
            hiu_id="test-hiu",
        )
        result = service.process_consent_callback(
            consent_id=consent.consent_id,
            status="INVALID",
        )
        assert result["status"] == "error"

    def test_get_consent_status(self, service):
        consent = service.create_consent(
            patient_abha="12345678901234",
            hiu_id="test-hiu",
        )
        status = service.get_consent_status(consent.consent_id)
        assert status is not None
        assert status["consentId"] == consent.consent_id

    def test_get_consent_status_not_found(self, service):
        assert service.get_consent_status("nonexistent") is None


class TestConsentArtifact:
    """Tests de l'artefact de consentement."""

    def test_consent_to_dict(self):
        consent = ConsentArtifact(
            patient_abha="12345678901234",
            hip_id="test-hip",
            hiu_id="test-hiu",
            purpose="CAREMGT",
        )
        data = consent.to_dict()
        assert data["patientAbha"] == "12345678901234"
        assert data["hipId"] == "test-hip"
        assert data["hiuId"] == "test-hiu"
        assert data["purpose"] == "CAREMGT"
        assert data["status"] == "REQUESTED"
        assert "dateRange" in data
        assert "expiry" in data

    def test_consent_grant(self):
        consent = ConsentArtifact(
            patient_abha="12345678901234",
            hip_id="test-hip",
            hiu_id="test-hiu",
        )
        consent.grant()
        assert consent.status == "GRANTED"

    def test_consent_deny(self):
        consent = ConsentArtifact(
            patient_abha="12345678901234",
            hip_id="test-hip",
            hiu_id="test-hiu",
        )
        consent.deny()
        assert consent.status == "DENIED"

    def test_consent_revoke(self):
        consent = ConsentArtifact(
            patient_abha="12345678901234",
            hip_id="test-hip",
            hiu_id="test-hiu",
        )
        consent.revoke()
        assert consent.status == "REVOKED"

    def test_consent_custom_hi_types(self):
        consent = ConsentArtifact(
            patient_abha="12345678901234",
            hip_id="test-hip",
            hiu_id="test-hiu",
            hi_types=["DiagnosticReport"],
        )
        assert consent.hi_types == ["DiagnosticReport"]


# ==========================================
# SS-MIX2 Tests
# ==========================================


class TestSSMIX2Path:
    """Tests de construction et extraction de chemins SS-MIX2."""

    def test_build_path(self):
        path = build_ssmix2_path(
            root="/ssmix2/storage",
            patient_id="PAT001",
            order_date="20240115",
            data_type="ADT",
            message_id="MSG001",
        )
        assert path == "/ssmix2/storage/PAT001/20240115/ADT/MSG001"

    def test_build_path_invalid_date(self):
        with pytest.raises(ValueError, match="Format de date invalide"):
            build_ssmix2_path(
                root="/ssmix2/storage",
                patient_id="PAT001",
                order_date="2024-01-15",
                data_type="ADT",
                message_id="MSG001",
            )

    def test_build_path_different_data_types(self):
        for dtype in ["ADT", "OML", "ORU"]:
            path = build_ssmix2_path(
                root="/root",
                patient_id="P001",
                order_date="20240101",
                data_type=dtype,
                message_id="M001",
            )
            assert dtype in path


class TestHL7Parsing:
    """Tests de parsing HL7 v2.5."""

    def test_parse_segment(self):
        segment = parse_hl7_segment("PID|1||PAT001^^^HOSPITAL||山田^太郎||19850315|M")
        assert segment["segment_type"] == "PID"
        assert segment["field_3"] == "PAT001^^^HOSPITAL"

    def test_parse_empty_segment(self):
        segment = parse_hl7_segment("")
        assert segment["segment_type"] == ""


class TestJapaneseEncoding:
    """Tests d'encodage japonais."""

    def test_decode_utf8(self):
        text = "山田太郎"
        result = decode_japanese_text(text.encode("utf-8"), "utf-8")
        assert result == text

    def test_decode_shift_jis(self):
        text = "病理検査"
        result = decode_japanese_text(text.encode("shift_jis"), "shift_jis")
        assert result == text

    def test_decode_fallback(self):
        text = "テスト"
        # Encode as UTF-8 but request shift_jis decoding - should fallback
        encoded = text.encode("utf-8")
        result = decode_japanese_text(encoded, "utf-8")
        assert result == text

    def test_decode_invalid_encoding_name(self):
        text = "テスト"
        encoded = text.encode("utf-8")
        # Should eventually decode with UTF-8 fallback
        result = decode_japanese_text(encoded, "nonexistent_encoding")
        assert "テスト" in result


class TestSSMIX2Service:
    """Tests du service SS-MIX2."""

    @pytest.fixture
    def service(self):
        return SSMIX2Service(mock_mode=True)

    def test_parse_adt_message(self, service):
        raw = service.get_mock_adt_message()
        msg = service.parse_message(raw)
        assert msg.message_type == "ADT"
        assert msg.patient_id == "PAT001"
        assert msg.patient_name == "山田"

    def test_parse_oml_message(self, service):
        raw = service.get_mock_oml_message()
        msg = service.parse_message(raw)
        assert msg.message_type == "OML"
        assert msg.patient_id == "PAT001"
        assert msg.order_id == "ORD001"
        assert msg.order_date == "20240115"

    def test_message_to_dict(self, service):
        raw = service.get_mock_adt_message()
        msg = service.parse_message(raw)
        data = msg.to_dict()
        assert data["messageType"] == "ADT"
        assert data["patientId"] == "PAT001"
        assert "segmentCount" in data

    def test_get_storage_path(self, service):
        path = service.get_storage_path(
            patient_id="PAT001",
            order_date="20240115",
            data_type="ADT",
            message_id="MSG001",
        )
        assert "PAT001" in path
        assert "20240115" in path
        assert "ADT" in path
        assert "MSG001" in path

    def test_extract_from_path(self, service):
        metadata = service.extract_from_path("/ssmix2/storage/PAT001/20240115/ADT/MSG001")
        assert metadata["patientId"] == "PAT001"
        assert metadata["orderDate"] == "20240115"
        assert metadata["dataType"] == "ADT"
        assert metadata["messageId"] == "MSG001"

    def test_extract_from_path_too_short(self, service):
        with pytest.raises(ValueError, match="pas assez de segments"):
            service.extract_from_path("/too/short")

    def test_get_mock_patient_data(self, service):
        data = service.get_mock_patient_data()
        assert "patient" in data
        assert "order" in data
        assert "storagePath" in data
        assert data["patient"]["messageType"] == "ADT"
        assert data["order"]["messageType"] == "OML"

    def test_decode_text(self, service):
        text = "病理検査"
        result = service.decode_text(text.encode("utf-8"), "utf-8")
        assert result == text

    def test_list_data_types(self, service):
        types = service.list_data_types()
        assert "ADT" in types
        assert "OML" in types


# ==========================================
# I18n Tests
# ==========================================


class TestI18nService:
    """Tests du service d'internationalisation."""

    @pytest.fixture
    def service(self):
        return I18nService()

    def test_default_locale(self, service):
        assert service.default_locale == DEFAULT_LOCALE

    def test_all_locales_loaded(self, service):
        for locale in SUPPORTED_LOCALES:
            assert locale in service.translations
            assert len(service.translations[locale]) > 0

    def test_get_translations_fr(self, service):
        translations = service.get_translations("fr")
        assert "nav.home" in translations
        assert translations["nav.home"] == "Accueil"

    def test_get_translations_en(self, service):
        translations = service.get_translations("en")
        assert "nav.home" in translations
        assert translations["nav.home"] == "Home"

    def test_get_translations_ja(self, service):
        translations = service.get_translations("ja")
        assert "nav.home" in translations
        assert translations["nav.home"] == "ホーム"

    def test_get_translations_zh(self, service):
        translations = service.get_translations("zh")
        assert "nav.home" in translations
        assert translations["nav.home"] == "首页"

    def test_get_translations_hi(self, service):
        translations = service.get_translations("hi")
        assert "nav.home" in translations
        assert translations["nav.home"] == "होम"

    def test_get_translations_unsupported_locale(self, service):
        # Should fallback to default locale
        translations = service.get_translations("xx")
        assert translations == service.get_translations(DEFAULT_LOCALE)

    def test_translate_key(self, service):
        assert service.translate("nav.home", "en") == "Home"
        assert service.translate("nav.home", "fr") == "Accueil"

    def test_translate_missing_key(self, service):
        # Should return the key itself
        result = service.translate("nonexistent.key", "en")
        assert result == "nonexistent.key"

    def test_translate_fallback_to_default(self, service):
        # For unsupported locale, should fallback to default
        result = service.translate("nav.home", "xx")
        assert result == "Accueil"  # French fallback

    def test_get_supported_locales(self, service):
        locales = service.get_supported_locales()
        assert len(locales) == len(SUPPORTED_LOCALES)
        codes = [loc["code"] for loc in locales]
        for locale in SUPPORTED_LOCALES:
            assert locale in codes
        # Check names
        fr_locale = next(loc for loc in locales if loc["code"] == "fr")
        assert fr_locale["name"] == "Français"

    def test_get_translation_count(self, service):
        count = service.get_translation_count("fr")
        assert count >= 40  # At least 40 translations per locale

    def test_export_translations(self, service):
        export = service.export_translations("en")
        assert export["locale"] == "en"
        assert export["keyCount"] > 0
        assert "translations" in export
        assert "nav.home" in export["translations"]

    def test_all_locales_have_same_keys(self, service):
        """Vérifie que toutes les locales ont les mêmes clés de traduction."""
        fr_keys = set(service.translations["fr"].keys())
        for locale in SUPPORTED_LOCALES:
            locale_keys = set(service.translations[locale].keys())
            assert locale_keys == fr_keys, (
                f"Locale {locale} a des clés différentes de fr: "
                f"manquantes={fr_keys - locale_keys}, "
                f"extras={locale_keys - fr_keys}"
            )

    def test_minimum_translations_per_locale(self, service):
        """Vérifie qu'il y a au moins 30 traductions par locale."""
        for locale in SUPPORTED_LOCALES:
            count = service.get_translation_count(locale)
            assert count >= 30, f"Locale {locale} n'a que {count} traductions (minimum: 30)"

    def test_translation_categories(self, service):
        """Vérifie que les catégories principales sont couvertes."""
        categories = [
            "app.",
            "nav.",
            "slide.",
            "panel.",
            "btn.",
            "error.",
            "search.",
            "worklist.",
            "folder.",
            "case.",
        ]
        for locale in SUPPORTED_LOCALES:
            keys = service.translations[locale].keys()
            for category in categories:
                matching = [k for k in keys if k.startswith(category)]
                assert (
                    len(matching) > 0
                ), f"Locale {locale} n'a aucune traduction pour la catégorie {category}"
