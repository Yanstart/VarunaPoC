# ADR-0004: Serve slides in native format, no DICOM conversion

**Status:** Accepted
**Date:** 2025-10-15
**Decision makers:** Project lead

## Context

Hospital scanners produce slides in vendor-specific formats (MRXS, BIF, SVS, NDPI). DICOM WSI is the standard for interoperability. Converting to DICOM would enable PACS integration but adds complexity and storage.

## Decision

Serve slides directly from their native format using OpenSlide. Provide DICOMweb-compatible API endpoints for metadata queries but stream tiles from original files.

## Consequences

**Positive:**
- Zero ingest time: slides are viewable immediately after scanning
- No storage duplication: a 60 GB slide collection stays 60 GB
- OpenSlide supports all major scanner formats out of the box
- DICOMweb endpoints provide interoperability without conversion

**Negative:**
- Cannot store slides in PACS directly (no DICOM SM objects)
- Vendor-specific quirks (e.g., BIF DIRECTION_LEFT bug) must be handled per-format
- No DICOM Structured Report embedding in the slide file itself

**Alternatives rejected:**
- Full DICOM conversion on ingest: doubles storage, hours of CPU per slide
- Hybrid (convert on first access): unpredictable latency, complex cache management
- DICOM-only (require scanners to output DICOM): not supported by all scanner vendors
