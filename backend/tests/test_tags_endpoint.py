"""Tests for auto-tag endpoint logic."""
import pytest
from services.ml.tag_extractor import TagExtractor


class TestTagExtractor:
    def test_prostate_he_from_filename(self):
        extractor = TagExtractor()
        # _extract_from_filename only, not full pipeline
        tags = extractor._extract_from_filename("prostate_HE_sample.svs")
        assert tags is not None
        assert tags["organ"] == "prostate"
        assert tags["stain"] == "H&E"

    def test_breast_ki67_from_filename(self):
        extractor = TagExtractor()
        tags = extractor._extract_from_filename("breast_Ki67_case45.svs")
        assert tags is not None
        assert tags["organ"] == "sein"
        assert tags["marker"] == "Ki-67"

    def test_unknown_filename(self):
        extractor = TagExtractor()
        tags = extractor._extract_from_filename("12345_unknown_sample.svs")
        # Should return None since no organ/stain/marker found
        assert tags is None

    def test_lung_pdl1_from_filename(self):
        extractor = TagExtractor()
        tags = extractor._extract_from_filename("lung_PDL1_patient789.bif")
        assert tags is not None
        assert tags["organ"] == "poumon"
        assert tags["marker"] == "PD-L1"
