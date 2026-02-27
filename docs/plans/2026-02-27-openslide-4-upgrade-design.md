# OpenSlide 4.0 Upgrade

**Date**: 2026-02-27
**Status**: Approved
**Issue**: #144

## Problem

OpenSlide 3.4.1 (2015) cannot open DICOM WSI or Zeiss CZI files.
25 DICOM + 7 CZI slides in the test dataset are inaccessible.

## Solution

Install `openslide-bin` PyPI wheel which bundles OpenSlide 4.0 C library
with libdicom and all codecs. Zero compilation required.

Note: CZI support was NOT added in OpenSlide 4.0 (only DICOM).
CZI remains unsupported — conversion to TIFF is the only option.

## Changes

| File | Change |
|------|--------|
| `requirements.txt` | `openslide-python>=1.4.0` + `openslide-bin>=4.0.0` |
| `Dockerfile` | Remove `openslide-tools libopenslide0` from apt |
| `routes/ml.py` | Remove `.dcm`/`.dicom` from `_UNSUPPORTED_ML_FORMATS` |
| `format_detector.py` | Update DICOM support notes |

## Phase 2 (if needed)

If Ventana BIF direction patch is required, compile OpenSlide from
`openslide-patch/` fork with `ventana-left-direction.patch`.

## Validation

1. `openslide.__library_version__` == "4.0.0"
2. DICOM slides open in viewer
3. Re-run `diagnose_ml_compatibility.py`
4. Test BIF problematic slides
