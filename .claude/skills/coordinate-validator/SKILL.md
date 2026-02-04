---
name: coordinate-validator
description: Validate coordinate mapping accuracy between OpenSeadragon (normalized 0.0-1.0) and OpenSlide (absolute pixels). Ensures mathematical precision in the critical coordinate transformation.
allowed-tools: Read, Bash, Glob
---

# Coordinate Validator Skill

This skill validates the **most critical technical challenge** of VarunaPoC: ensuring mathematically precise and bidirectional coordinate mapping between OpenSeadragon (frontend) and OpenSlide (backend).

## Why This Is Critical

**Coordinate mapping is the heart of the viewer.** If coordinates are wrong:
- ❌ Tiles appear in wrong positions
- ❌ Zoom doesn't work correctly
- ❌ Mini-map shows incorrect viewport
- ❌ Navigation feels broken
- ❌ Clinical diagnosis becomes unreliable

**Target:** 100% pixel-perfect coordinate accuracy at all zoom levels.

## When to Use This Skill

Invoke this skill:

- ✅ After implementing/modifying coordinate mapping logic
- ✅ When tiles appear misaligned
- ✅ When zoom levels seem incorrect
- ✅ Before major releases (validation testing)
- ✅ When adding support for new slide format
- ✅ When mini-map viewport doesn't match actual view

## Coordinate Systems Involved

### 1. OpenSeadragon (Frontend)

**Normalized coordinates:** 0.0 to 1.0 range
- Origin: top-left (0, 0)
- Center of image: (0.5, 0.5)
- Bottom-right: (1.0, 1.0)
- **Independent of zoom level**
- **Independent of actual image dimensions**

**Example:**
```javascript
// Viewport bounds in OSD
const bounds = viewer.viewport.getBounds();
// bounds = {x: 0.25, y: 0.25, width: 0.5, height: 0.5}
// Means: viewing 50% of image, centered at (0.25, 0.25)
```

### 2. OpenSlide (Backend)

**Absolute pixel coordinates:** Level 0 (full resolution)
- Origin: top-left (0, 0)
- Center: (width/2, height/2)
- Bottom-right: (width, height)
- **Always specified at level 0** (OpenSlide requirement)
- **Independent of which pyramid level you're reading from**

**Example:**
```python
# For a 100,000 x 80,000 pixel slide
dimensions = (100000, 80000)  # Level 0

# Center of slide (level 0 coordinates)
center = (50000, 40000)

# Extract tile at center (using level 0 coords, but reading from level 2)
tile = slide.read_region((50000, 40000), level=2, size=(256, 256))
```

### 3. Pyramid Levels

**Multi-resolution pyramid:**
- **Level 0:** Full resolution (e.g., 100,000 x 80,000)
- **Level 1:** Downsampled ~2x (e.g., 50,000 x 40,000)
- **Level 2:** Downsampled ~4x (e.g., 25,000 x 20,000)
- **Level N:** Downsampled ~2^N

**Downsample factors:**
```python
slide.level_downsamples
# [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0]
```

## Conversion Formulas

### Frontend → Backend (OSD → OpenSlide)

```javascript
// Given: OSD normalized coordinates and slide dimensions
const osdX = 0.25;  // 25% from left
const osdY = 0.5;   // 50% from top

const slideWidth = 100000;   // Level 0 width
const slideHeight = 80000;   // Level 0 height

// Convert to level 0 pixel coordinates
const pixelX = Math.floor(osdX * slideWidth);   // 25000
const pixelY = Math.floor(osdY * slideHeight);  // 40000

// These coordinates are ALWAYS level 0, regardless of which level you're viewing
```

### Backend → Frontend (OpenSlide → OSD)

```python
# Given: Level 0 pixel coordinates
pixel_x = 25000
pixel_y = 40000

slide_width = 100000
slide_height = 80000

# Convert to OSD normalized coordinates
osd_x = pixel_x / slide_width   # 0.25
osd_y = pixel_y / slide_height  # 0.5
```

### Pyramid Level Selection

```javascript
function calculatePyramidLevel(zoom, maxLevel, containerWidth, slideWidth) {
    /**
     * Determine appropriate pyramid level based on zoom.
     *
     * Logic:
     * - Higher zoom → Lower pyramid level (more detail)
     * - Lower zoom → Higher pyramid level (less detail)
     *
     * Formula:
     * - pixelsPerViewport = containerWidth / zoom
     * - level = log2(slideWidth / pixelsPerViewport)
     */

    const pixelsPerViewport = containerWidth / zoom;
    const level = Math.floor(Math.log2(slideWidth / pixelsPerViewport));

    // Clamp to valid range [0, maxLevel]
    return Math.max(0, Math.min(level, maxLevel));
}

// Example:
// - Zoom 1.0 (fit to screen) → High level (low detail)
// - Zoom 4.0 (4x zoom) → Medium level
// - Zoom 16.0 (16x zoom) → Low level (high detail)
```

## Validation Tests

### Test 1: Center Point

```javascript
/**
 * Test that viewer starts at center of slide.
 */
function testCenterPoint(viewer, slideWidth, slideHeight) {
    const center = viewer.viewport.getCenter();

    // Center should be (0.5, 0.5) in OSD coords
    const tolerance = 0.01;  // 1% tolerance

    console.assert(
        Math.abs(center.x - 0.5) < tolerance &&
        Math.abs(center.y - 0.5) < tolerance,
        'Viewer should start at center (0.5, 0.5)'
    );

    // Convert to pixel coords
    const pixelX = Math.floor(center.x * slideWidth);
    const pixelY = Math.floor(center.y * slideHeight);

    console.log(`Center: OSD (${center.x}, ${center.y}) → Pixels (${pixelX}, ${pixelY})`);
    console.log(`Expected: Pixels (~${slideWidth/2}, ~${slideHeight/2})`);
}
```

### Test 2: Corner Points

```javascript
/**
 * Test all four corners of the slide.
 */
function testCorners(slideWidth, slideHeight) {
    const corners = [
        { name: "Top-Left", osd: {x: 0, y: 0}, pixel: {x: 0, y: 0} },
        { name: "Top-Right", osd: {x: 1, y: 0}, pixel: {x: slideWidth, y: 0} },
        { name: "Bottom-Left", osd: {x: 0, y: 1}, pixel: {x: 0, y: slideHeight} },
        { name: "Bottom-Right", osd: {x: 1, y: 1}, pixel: {x: slideWidth, y: slideHeight} }
    ];

    corners.forEach(corner => {
        const pixelX = Math.floor(corner.osd.x * slideWidth);
        const pixelY = Math.floor(corner.osd.y * slideHeight);

        console.assert(
            pixelX === corner.pixel.x && pixelY === corner.pixel.y,
            `${corner.name}: Expected (${corner.pixel.x}, ${corner.pixel.y}), got (${pixelX}, ${pixelY})`
        );
    });

    console.log('✓ All corners validated');
}
```

### Test 3: Zoom Level Mapping

```javascript
/**
 * Test that zoom levels map to correct pyramid levels.
 */
function testZoomLevelMapping(viewer, slideWidth, maxLevel) {
    const zoomLevels = [1.0, 2.0, 4.0, 8.0, 16.0];

    zoomLevels.forEach(zoom => {
        viewer.viewport.zoomTo(zoom);

        const containerWidth = viewer.viewport.getContainerSize().x;
        const level = calculatePyramidLevel(zoom, maxLevel, containerWidth, slideWidth);

        console.log(`Zoom ${zoom}x → Pyramid Level ${level}`);

        // Verify level is in valid range
        console.assert(
            level >= 0 && level <= maxLevel,
            `Level ${level} out of range [0, ${maxLevel}]`
        );
    });
}
```

### Test 4: Tile URL Correctness

```javascript
/**
 * Test that tile URLs are generated correctly.
 */
function testTileUrls(viewer, slideId) {
    // Listen to tile requests
    viewer.addHandler('tile-drawing', function(event) {
        const tile = event.tile;
        const url = tile.url;

        console.log(`Tile URL: ${url}`);

        // Validate URL format
        const pattern = /\/api\/slides\/(.+)\/tile\/(\d+)\/(\d+)\/(\d+)\/(\d+)\/(\d+)/;
        const match = url.match(pattern);

        console.assert(match !== null, 'Tile URL format invalid');

        const [, id, level, x, y, width, height] = match;

        // Validate parameters
        console.assert(id === slideId, 'Slide ID mismatch');
        console.assert(parseInt(level) >= 0, 'Invalid level');
        console.assert(parseInt(x) >= 0 && parseInt(y) >= 0, 'Invalid tile position');
        console.assert(parseInt(width) === 256 && parseInt(height) === 256, 'Invalid tile size');
    });

    // Trigger tile loading
    viewer.viewport.zoomTo(2.0);
}
```

### Test 5: Bidirectional Conversion

```javascript
/**
 * Test that conversions are bidirectional (reversible).
 */
function testBidirectionalConversion(slideWidth, slideHeight) {
    // Test random points
    const testPoints = [
        {x: 0.1, y: 0.2},
        {x: 0.5, y: 0.5},
        {x: 0.75, y: 0.9},
        {x: 0.01, y: 0.99}
    ];

    testPoints.forEach(osd => {
        // OSD → Pixel
        const pixelX = Math.floor(osd.x * slideWidth);
        const pixelY = Math.floor(osd.y * slideHeight);

        // Pixel → OSD
        const osdX2 = pixelX / slideWidth;
        const osdY2 = pixelY / slideHeight;

        // Should be close to original (within rounding error)
        const tolerance = 1 / Math.max(slideWidth, slideHeight);  // 1 pixel tolerance

        console.assert(
            Math.abs(osdX2 - osd.x) < tolerance &&
            Math.abs(osdY2 - osd.y) < tolerance,
            `Bidirectional conversion failed: (${osd.x}, ${osd.y}) → (${pixelX}, ${pixelY}) → (${osdX2}, ${osdY2})`
        );
    });

    console.log('✓ Bidirectional conversion validated');
}
```

## Validation Report Format

```json
{
  "validation_date": "2025-12-03T10:30:00Z",
  "slide_tested": {
    "id": "abc123...",
    "path": "/Slides/3Dhistec/sample.mrxs",
    "dimensions": [100000, 80000],
    "level_count": 9
  },
  "tests": {
    "center_point": {
      "status": "PASS",
      "osd_coords": [0.5, 0.5],
      "pixel_coords": [50000, 40000],
      "error_pixels": 0
    },
    "corners": {
      "status": "PASS",
      "tested": 4,
      "passed": 4
    },
    "zoom_levels": {
      "status": "PASS",
      "tested": [1.0, 2.0, 4.0, 8.0, 16.0],
      "pyramid_levels": [8, 7, 6, 5, 4]
    },
    "tile_urls": {
      "status": "PASS",
      "tiles_tested": 50,
      "format_errors": 0
    },
    "bidirectional": {
      "status": "PASS",
      "points_tested": 10,
      "max_error_pixels": 1
    }
  },
  "overall_status": "PASS",
  "accuracy": "100% pixel-perfect"
}
```

## Common Issues and Fixes

### Issue 1: Tiles Misaligned

**Symptom:** Tiles appear in wrong positions, gaps between tiles
**Cause:** Incorrect level 0 coordinate conversion
**Fix:** Always use level 0 coordinates with OpenSlide, regardless of which level you're reading

```javascript
// BAD: Using level N coordinates
const badX = levelNTileX * 256;  // WRONG

// GOOD: Using level 0 coordinates
const level0X = Math.floor(osdX * slideWidth);  // CORRECT
```

### Issue 2: Wrong Pyramid Level

**Symptom:** Blurry when zoomed in, or too detailed when zoomed out
**Cause:** Incorrect zoom → level mapping
**Fix:** Use logarithmic calculation based on viewport size

```javascript
// Correct level calculation
const level = Math.floor(Math.log2(slideWidth / pixelsPerViewport));
```

### Issue 3: Mini-map Viewport Wrong

**Symptom:** Mini-map rectangle doesn't match actual viewport
**Cause:** Mini-map not synced with main viewport
**Fix:** Update mini-map on every viewport-change event

```javascript
viewer.addHandler('viewport-change', function() {
    const bounds = viewer.viewport.getBounds();
    updateMinimapViewport(bounds);  // Sync mini-map
});
```

## Automated Testing (Phase 2+)

```python
# backend/tests/test_coordinates.py
import pytest
from backend.utils.coordinate_mapper import osd_to_pixel, pixel_to_osd

def test_center_point():
    slide_width, slide_height = 100000, 80000

    # OSD center (0.5, 0.5) should map to pixel center
    pixel_x, pixel_y = osd_to_pixel(0.5, 0.5, slide_width, slide_height)

    assert pixel_x == 50000
    assert pixel_y == 40000

def test_bidirectional_conversion():
    slide_width, slide_height = 100000, 80000

    test_points = [(0.1, 0.2), (0.5, 0.5), (0.75, 0.9)]

    for osd_x, osd_y in test_points:
        # OSD → Pixel → OSD
        pixel_x, pixel_y = osd_to_pixel(osd_x, osd_y, slide_width, slide_height)
        osd_x2, osd_y2 = pixel_to_osd(pixel_x, pixel_y, slide_width, slide_height)

        # Should be equal within rounding error
        assert abs(osd_x2 - osd_x) < 1e-5
        assert abs(osd_y2 - osd_y) < 1e-5
```

## Integration with Other Skills

This skill works well with:
- **performance-engineer agent** - Coordinate mapping is their core responsibility
- **slide-tester** - Validate coordinates for each slide format
- **error-documenter** - Document coordinate-related bugs

## References

- **OpenSeadragon Coordinates:** https://openseadragon.github.io/examples/viewport-coordinates/
- **OpenSlide Coordinates:** https://openslide.org/api/python/#reading-image-data
- **CLAUDE.md:** Coordinate mapping section
- **Performance Engineer Agent:** Core coordinate mapping expertise

## Official Resources

- **OpenSeadragon API:** https://openseadragon.github.io/docs/OpenSeadragon.Viewport.html
- **OpenSlide Python API:** https://openslide.org/api/python/

---

**Remember:** Coordinate accuracy is non-negotiable in medical imaging. One pixel off can affect clinical diagnosis. Test exhaustively, validate continuously.
