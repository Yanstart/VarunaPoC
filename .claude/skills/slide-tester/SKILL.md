---
name: slide-tester
description: Systematically test features across all supported slide formats (.mrxs, .bif, .tif) to ensure vendor-neutral functionality. Validates file structure, OpenSlide compatibility, and viewer integration.
allowed-tools: Read, Bash, Glob, Grep
---

# Slide Tester Skill

This skill automates comprehensive testing of slide-related features across all supported vendor formats to ensure vendor-neutral functionality.

## When to Use This Skill

Invoke this skill when:

- ✅ Implementing new slide handling feature
- ✅ Modifying OpenSlide integration
- ✅ Adding support for new format
- ✅ Debugging format-specific issues
- ✅ Validating coordinate mapping changes
- ✅ Before major releases (regression testing)

## What This Skill Does

1. **Scans `/Slides` directory** for test files
2. **Validates file structure** (companion files for .mrxs, etc.)
3. **Tests OpenSlide detection** for each format
4. **Extracts metadata** (dimensions, levels, vendor)
5. **Tests tile extraction** at multiple pyramid levels
6. **Validates coordinate accuracy** (if coordinate-validator skill available)
7. **Generates test report** with pass/fail status

## Supported Formats

### 3DHistech / MIRAX (.mrxs)
- **Vendor:** 3DHISTECH Ltd.
- **OpenSlide Format:** `mirax`
- **Test Directory:** `/Slides/3Dhistec/`
- **Critical Requirements:**
  - Companion directory must exist (`sample_name/` for `sample_name.mrxs`)
  - `Slidedat.ini` must be present
  - `Data*.dat` files contain image data

### Roche/Ventana (.bif)
- **Vendor:** Roche Diagnostics / Ventana Medical Systems
- **OpenSlide Format:** `ventana`
- **Test Directory:** `/Slides/ROCHE/`
- **Known Issues:**
  - `direction="LEFT"` attribute unsupported (see `/docs/ERROR_BIF_DIRECTION_LEFT.md`)

### Roche Generic TIFF (.tif, .tiff)
- **Vendor:** Generic pyramidal TIFF
- **OpenSlide Format:** `generic-tiff`
- **Test Directory:** `/Slides/ROCHE/`
- **Requirements:**
  - Must be pyramidal (multiple resolutions)
  - Standard TIFF with tiled layout

## Test Categories

### 1. File Structure Validation

```python
def test_file_structure(slide_path):
    """
    Validate file structure requirements.

    For .mrxs:
    - Check companion directory exists
    - Check Slidedat.ini present
    - Check Data*.dat files present

    For other formats:
    - Check file readable
    - Check file not corrupted
    """
    pass
```

### 2. OpenSlide Detection

```python
import openslide

def test_openslide_detection(slide_path):
    """
    Test if OpenSlide can detect and open the slide.

    Checks:
    - Format detection (detect_format)
    - File opening (OpenSlide constructor)
    - Basic properties accessible
    """
    try:
        format_name = openslide.detect_format(slide_path)
        if format_name is None:
            return {"status": "FAIL", "error": "Format not detected"}

        slide = openslide.OpenSlide(slide_path)
        slide.close()

        return {"status": "PASS", "format": format_name}

    except openslide.OpenSlideError as e:
        return {"status": "FAIL", "error": str(e)}
```

### 3. Metadata Extraction

```python
def test_metadata_extraction(slide_path):
    """
    Extract and validate metadata.

    Tests:
    - Dimensions (level 0)
    - Level count
    - Level dimensions
    - Downsamples
    - Vendor properties
    - Magnification (if available)
    """
    try:
        slide = openslide.OpenSlide(slide_path)

        metadata = {
            "dimensions": slide.dimensions,
            "level_count": slide.level_count,
            "level_dimensions": slide.level_dimensions,
            "level_downsamples": slide.level_downsamples,
            "vendor": slide.properties.get(openslide.PROPERTY_NAME_VENDOR, "Unknown"),
            "objective_power": slide.properties.get(openslide.PROPERTY_NAME_OBJECTIVE_POWER, "N/A"),
        }

        slide.close()

        # Validate metadata
        if metadata["dimensions"][0] < 1 or metadata["dimensions"][1] < 1:
            return {"status": "FAIL", "error": "Invalid dimensions"}

        if metadata["level_count"] < 1:
            return {"status": "FAIL", "error": "No pyramid levels"}

        return {"status": "PASS", "metadata": metadata}

    except Exception as e:
        return {"status": "FAIL", "error": str(e)}
```

### 4. Tile Extraction

```python
def test_tile_extraction(slide_path):
    """
    Test tile extraction at multiple levels.

    Extracts:
    - Top-left tile (0, 0) at level 0
    - Center tile at level 0
    - Top-left tile at highest level (lowest resolution)
    - Random tile at middle level

    Validates:
    - Tile size matches request
    - Tile is not blank/corrupted
    - Color channels present (RGB)
    """
    try:
        slide = openslide.OpenSlide(slide_path)

        # Test level 0 (full resolution)
        tile_0 = slide.read_region((0, 0), 0, (256, 256))
        if tile_0.size != (256, 256):
            return {"status": "FAIL", "error": "Tile size mismatch"}

        # Test highest level (lowest resolution)
        max_level = slide.level_count - 1
        tile_max = slide.read_region((0, 0), max_level, (256, 256))

        # Test center tile
        center_x = slide.dimensions[0] // 2
        center_y = slide.dimensions[1] // 2
        tile_center = slide.read_region((center_x, center_y), 0, (256, 256))

        slide.close()

        return {
            "status": "PASS",
            "tiles_extracted": 3,
            "levels_tested": [0, max_level]
        }

    except Exception as e:
        return {"status": "FAIL", "error": str(e)}
```

### 5. Performance Testing

```python
import time

def test_tile_performance(slide_path, num_tiles=10):
    """
    Measure tile extraction performance.

    Extracts multiple tiles and measures:
    - Average extraction time
    - Min/max extraction time
    - Throughput (tiles per second)

    Target: < 100ms per tile for local files
    """
    try:
        slide = openslide.OpenSlide(slide_path)

        times = []
        for i in range(num_tiles):
            x = (i * 1000) % slide.dimensions[0]
            y = (i * 1000) % slide.dimensions[1]

            start = time.time()
            tile = slide.read_region((x, y), 0, (256, 256))
            elapsed = time.time() - start

            times.append(elapsed * 1000)  # Convert to ms

        slide.close()

        return {
            "status": "PASS",
            "avg_time_ms": sum(times) / len(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "tiles_per_second": 1000 / (sum(times) / len(times))
        }

    except Exception as e:
        return {"status": "FAIL", "error": str(e)}
```

## Test Report Format

```json
{
  "test_date": "2025-12-03T10:30:00Z",
  "total_slides": 15,
  "formats_tested": ["mirax", "ventana", "generic-tiff"],
  "results": [
    {
      "slide_path": "/Slides/3Dhistec/sample1.mrxs",
      "format": "mirax",
      "vendor": "3DHISTECH",
      "tests": {
        "file_structure": "PASS",
        "openslide_detection": "PASS",
        "metadata_extraction": "PASS",
        "tile_extraction": "PASS",
        "performance": "PASS (avg: 45ms/tile)"
      },
      "overall_status": "PASS"
    },
    {
      "slide_path": "/Slides/ROCHE/sample_left.bif",
      "format": "ventana",
      "vendor": "Ventana",
      "tests": {
        "file_structure": "PASS",
        "openslide_detection": "FAIL",
        "error": "Bad direction attribute: LEFT"
      },
      "overall_status": "FAIL",
      "notes": "Known issue, see docs/ERROR_BIF_DIRECTION_LEFT.md"
    }
  ],
  "summary": {
    "total_passed": 14,
    "total_failed": 1,
    "pass_rate": 93.3,
    "known_issues": 1
  }
}
```

## Regression Testing

Run this skill before major releases to catch regressions:

```bash
# Test all slides in /Slides directory
python backend/tests/test_all_slides.py

# Test specific format
python backend/tests/test_all_slides.py --format mirax

# Test with performance benchmarking
python backend/tests/test_all_slides.py --benchmark

# Generate HTML report
python backend/tests/test_all_slides.py --report html
```

## Integration Testing with Frontend

Test complete workflow (backend + frontend):

```javascript
// Test slide loading in viewer
async function testSlideInViewer(slideId) {
    // 1. Fetch slide info
    const info = await fetch(`/api/slides/${slideId}/info`).then(r => r.json());
    console.log(`Slide dimensions: ${info.dimensions}`);

    // 2. Initialize OpenSeadragon
    const viewer = OpenSeadragon({
        id: "viewer",
        tileSources: {
            height: info.dimensions[1],
            width: info.dimensions[0],
            tileSize: 256,
            maxLevel: info.level_count - 1,
            getTileUrl: (level, x, y) =>
                `/api/slides/${slideId}/tile/${level}/${x}/${y}/256/256`
        }
    });

    // 3. Wait for tiles to load
    viewer.addHandler('tile-loaded', () => {
        console.log('Tile loaded successfully');
    });

    // 4. Zoom to center
    viewer.viewport.zoomTo(2.0);

    // 5. Validate tiles displayed
    setTimeout(() => {
        console.log('Integration test complete');
    }, 5000);
}
```

## Known Issues Reference

Always check `/docs/ERROR_*.md` for documented format-specific issues:

- `/docs/ERROR_BIF_DIRECTION_LEFT.md` - Ventana BIF with direction="LEFT"
- `/docs/ERROR_OPENSLIDE_JPEG_CORRUPTION.md` - JPEG tile corruption (future)
- `/docs/ERROR_MRXS_MISSING_COMPANION.md` - Missing companion directory (future)

## Test Automation (Phase 2+)

```yaml
# .github/workflows/test-slides.yml (future CI/CD)
name: Slide Format Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install openslide-python pytest
      - name: Run slide tests
        run: pytest backend/tests/test_all_slides.py
```

## Integration with Other Skills

This skill works well with:
- **error-documenter** - Document format-specific issues discovered during testing
- **coordinate-validator** - Validate coordinate mapping for each format
- **api-documenter** - Validate API endpoints work with all formats

## References

- **OpenSlide Formats:** https://openslide.org/formats/
- **Test Data:** `/Slides/` directory
- **Error Documentation:** `/docs/ERROR_*.md`
- **CLAUDE.md:** Testing requirements and standards

## Official Resources

- **OpenSlide Python API:** https://openslide.org/api/python/
- **pytest Documentation:** https://docs.pytest.org/
- **Python unittest:** https://docs.python.org/3/library/unittest.html

---

**Remember:** Vendor neutrality is a core principle. Every feature must work identically across all supported formats. Test comprehensively, document exceptions.
