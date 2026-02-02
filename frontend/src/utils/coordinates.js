/**
 * Coordinate Utilities - Coordinate transformation and mapping
 *
 * Provides utilities for coordinate transformations between:
 * - OpenSeadragon normalized coordinates (0-1)
 * - OpenSlide absolute pixel coordinates
 * - Different pyramid levels
 *
 * CRITICAL: Coordinate mapping accuracy is essential for:
 * - Synchronized viewing between viewers with different slide sizes
 * - Accurate tile requests
 * - Annotation positioning
 *
 * @module utils/coordinates
 *
 * @see docs/Manuel/ for coordinate system documentation
 * @see CLAUDE.md for technical specifications
 */

/**
 * Convert OpenSeadragon normalized coordinates to absolute pixels
 *
 * OpenSeadragon uses normalized coordinates where:
 * - x: 0.0 = left edge, 1.0 = right edge
 * - y: 0.0 = top edge, y_max = bottom edge (aspect ratio dependent)
 *
 * @param {Object} normalizedCoords - Normalized coordinates
 * @param {number} normalizedCoords.x - X position (0-1)
 * @param {number} normalizedCoords.y - Y position (0-aspect)
 * @param {number} normalizedCoords.width - Width (0-1)
 * @param {number} normalizedCoords.height - Height (0-aspect)
 * @param {Object} slideDimensions - Slide dimensions at level 0
 * @param {number} slideDimensions.width - Slide width in pixels
 * @param {number} slideDimensions.height - Slide height in pixels
 * @returns {Object} Absolute pixel coordinates { x, y, width, height }
 *
 * @example
 * const absolute = normalizedToAbsolute(
 *     { x: 0.25, y: 0.25, width: 0.5, height: 0.5 },
 *     { width: 100000, height: 80000 }
 * );
 * // Result: { x: 25000, y: 20000, width: 50000, height: 40000 }
 */
export function normalizedToAbsolute(normalizedCoords, slideDimensions) {
    const { width: slideWidth, height: slideHeight } = slideDimensions;

    return {
        x: Math.round(normalizedCoords.x * slideWidth),
        y: Math.round(normalizedCoords.y * slideWidth), // Note: OSD uses width for both
        width: Math.round(normalizedCoords.width * slideWidth),
        height: Math.round(normalizedCoords.height * slideWidth)
    };
}

/**
 * Convert absolute pixel coordinates to OpenSeadragon normalized
 *
 * @param {Object} absoluteCoords - Absolute pixel coordinates
 * @param {number} absoluteCoords.x - X position in pixels
 * @param {number} absoluteCoords.y - Y position in pixels
 * @param {number} absoluteCoords.width - Width in pixels
 * @param {number} absoluteCoords.height - Height in pixels
 * @param {Object} slideDimensions - Slide dimensions at level 0
 * @param {number} slideDimensions.width - Slide width in pixels
 * @param {number} slideDimensions.height - Slide height in pixels
 * @returns {Object} Normalized coordinates { x, y, width, height }
 */
export function absoluteToNormalized(absoluteCoords, slideDimensions) {
    const { width: slideWidth } = slideDimensions;

    return {
        x: absoluteCoords.x / slideWidth,
        y: absoluteCoords.y / slideWidth,
        width: absoluteCoords.width / slideWidth,
        height: absoluteCoords.height / slideWidth
    };
}

/**
 * Convert coordinates between pyramid levels
 *
 * OpenSlide uses downsampling factors for each level.
 * Level 0 is full resolution; higher levels are downsampled.
 *
 * @param {Object} coords - Coordinates at source level
 * @param {number} coords.x - X position
 * @param {number} coords.y - Y position
 * @param {number} [coords.width] - Width (optional)
 * @param {number} [coords.height] - Height (optional)
 * @param {number} sourceDownsample - Downsample factor of source level
 * @param {number} targetDownsample - Downsample factor of target level
 * @returns {Object} Coordinates at target level
 *
 * @example
 * // Convert from level 0 (downsample 1) to level 2 (downsample 4)
 * const level2Coords = convertBetweenLevels(
 *     { x: 1000, y: 2000 },
 *     1.0,
 *     4.0
 * );
 * // Result: { x: 250, y: 500 }
 */
export function convertBetweenLevels(coords, sourceDownsample, targetDownsample) {
    const factor = sourceDownsample / targetDownsample;

    const result = {
        x: Math.round(coords.x * factor),
        y: Math.round(coords.y * factor)
    };

    if (coords.width !== undefined) {
        result.width = Math.round(coords.width * factor);
    }

    if (coords.height !== undefined) {
        result.height = Math.round(coords.height * factor);
    }

    return result;
}

/**
 * Convert level 0 coordinates to a specific pyramid level
 *
 * @param {Object} level0Coords - Coordinates at level 0
 * @param {number} level0Coords.x - X position at level 0
 * @param {number} level0Coords.y - Y position at level 0
 * @param {number} downsample - Downsample factor of target level
 * @returns {Object} Coordinates at target level { x, y }
 */
export function level0ToLevel(level0Coords, downsample) {
    return convertBetweenLevels(level0Coords, 1.0, downsample);
}

/**
 * Convert coordinates from a pyramid level to level 0
 *
 * @param {Object} levelCoords - Coordinates at source level
 * @param {number} levelCoords.x - X position at source level
 * @param {number} levelCoords.y - Y position at source level
 * @param {number} downsample - Downsample factor of source level
 * @returns {Object} Coordinates at level 0 { x, y }
 */
export function levelToLevel0(levelCoords, downsample) {
    return convertBetweenLevels(levelCoords, downsample, 1.0);
}

/**
 * Calculate tile coordinates for a given viewport
 *
 * @param {Object} viewport - Viewport bounds (normalized or absolute)
 * @param {number} viewport.x - X position
 * @param {number} viewport.y - Y position
 * @param {number} viewport.width - Viewport width
 * @param {number} viewport.height - Viewport height
 * @param {number} tileSize - Tile size in pixels
 * @param {Object} levelDimensions - Dimensions at target level
 * @param {number} levelDimensions.width - Level width
 * @param {number} levelDimensions.height - Level height
 * @returns {Object} Tile range { startCol, startRow, endCol, endRow }
 */
export function calculateTileRange(viewport, tileSize, levelDimensions) {
    const startCol = Math.max(0, Math.floor(viewport.x / tileSize));
    const startRow = Math.max(0, Math.floor(viewport.y / tileSize));

    const endCol = Math.min(
        Math.ceil(levelDimensions.width / tileSize) - 1,
        Math.ceil((viewport.x + viewport.width) / tileSize)
    );

    const endRow = Math.min(
        Math.ceil(levelDimensions.height / tileSize) - 1,
        Math.ceil((viewport.y + viewport.height) / tileSize)
    );

    return {
        startCol,
        startRow,
        endCol,
        endRow,
        tileCount: (endCol - startCol + 1) * (endRow - startRow + 1)
    };
}

/**
 * Find best pyramid level for a given zoom
 *
 * Selects the level that provides adequate resolution without
 * loading unnecessarily high-resolution tiles.
 *
 * @param {number} zoom - Current OpenSeadragon zoom level
 * @param {number[]} downsamples - Array of downsample factors for each level
 * @param {number} [threshold=1.5] - Quality threshold (higher = prefer higher resolution)
 * @returns {number} Best level index (0 = highest resolution)
 *
 * @example
 * const level = findBestLevel(4.0, [1.0, 4.0, 16.0, 64.0]);
 * // Returns 1 (downsample 4.0 is best for zoom 4.0)
 */
export function findBestLevel(zoom, downsamples, threshold = 1.5) {
    // OpenSeadragon zoom 1.0 = full image fits in viewport
    // We want level where: zoom * downsample >= threshold

    for (let i = downsamples.length - 1; i >= 0; i--) {
        if (zoom * downsamples[i] >= threshold) {
            return i;
        }
    }

    // Default to highest resolution
    return 0;
}

/**
 * Normalize viewport for synchronization between different slide sizes
 *
 * Converts viewport to a slide-independent representation
 * based on relative position and coverage.
 *
 * @param {Object} viewport - Viewport bounds from OpenSeadragon
 * @param {Object} slideDimensions - Slide dimensions
 * @returns {Object} Normalized sync data
 */
export function normalizeForSync(viewport, slideDimensions) {
    const aspectRatio = slideDimensions.height / slideDimensions.width;

    return {
        // Center point (relative to slide)
        centerX: viewport.x + viewport.width / 2,
        centerY: (viewport.y + viewport.height / 2) / aspectRatio,

        // Coverage (how much of slide is visible)
        coverage: viewport.width,

        // Original aspect ratio for denormalization
        aspectRatio
    };
}

/**
 * Denormalize viewport for a target slide
 *
 * Converts normalized sync data to viewport for a specific slide.
 *
 * @param {Object} syncData - Normalized sync data
 * @param {Object} targetDimensions - Target slide dimensions
 * @returns {Object} Viewport bounds for target slide
 */
export function denormalizeForSync(syncData, targetDimensions) {
    const targetAspect = targetDimensions.height / targetDimensions.width;

    // Calculate viewport dimensions
    const width = syncData.coverage;
    const height = width * targetAspect;

    // Calculate position from center point
    const x = syncData.centerX - width / 2;
    const y = (syncData.centerY * targetAspect) - height / 2;

    return {
        x,
        y,
        width,
        height
    };
}

/**
 * Clamp viewport to valid bounds
 *
 * Ensures viewport stays within slide boundaries.
 *
 * @param {Object} viewport - Viewport to clamp
 * @param {Object} slideDimensions - Slide dimensions
 * @returns {Object} Clamped viewport
 */
export function clampViewport(viewport, slideDimensions) {
    const aspectRatio = slideDimensions.height / slideDimensions.width;
    const maxY = aspectRatio;

    return {
        x: Math.max(0, Math.min(1 - viewport.width, viewport.x)),
        y: Math.max(0, Math.min(maxY - viewport.height, viewport.y)),
        width: Math.min(1, viewport.width),
        height: Math.min(maxY, viewport.height)
    };
}

/**
 * Calculate distance between two points
 *
 * @param {Object} p1 - First point { x, y }
 * @param {Object} p2 - Second point { x, y }
 * @returns {number} Euclidean distance
 */
export function distance(p1, p2) {
    const dx = p2.x - p1.x;
    const dy = p2.y - p1.y;
    return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Convert microns to pixels
 *
 * Uses slide's MPP (Microns Per Pixel) metadata.
 *
 * @param {number} microns - Distance in microns
 * @param {number} mpp - Microns per pixel (from slide metadata)
 * @returns {number} Distance in pixels
 */
export function micronsToPixels(microns, mpp) {
    return microns / mpp;
}

/**
 * Convert pixels to microns
 *
 * @param {number} pixels - Distance in pixels
 * @param {number} mpp - Microns per pixel
 * @returns {number} Distance in microns
 */
export function pixelsToMicrons(pixels, mpp) {
    return pixels * mpp;
}

// Default export with all functions
export default {
    normalizedToAbsolute,
    absoluteToNormalized,
    convertBetweenLevels,
    level0ToLevel,
    levelToLevel0,
    calculateTileRange,
    findBestLevel,
    normalizeForSync,
    denormalizeForSync,
    clampViewport,
    distance,
    micronsToPixels,
    pixelsToMicrons
};
