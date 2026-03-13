"""Shared slide utilities for MPP resolution across routes and ML providers."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Objective power to MPP lookup table (common scanner defaults)
OBJECTIVE_TO_MPP: dict[int, float] = {
    100: 0.10,
    80: 0.125,
    60: 0.167,
    40: 0.25,
    20: 0.50,
    10: 1.0,
    5: 2.0,
    4: 2.5,
    2: 5.0,
    1: 10.0,
}


@dataclass
class MPPData:
    """Resolved microns-per-pixel data."""

    mpp_x: float
    mpp_y: float
    objective: int | None = None
    source: str = "openslide"


def resolve_slide_mpp(slide_path: str) -> MPPData | None:
    """Open a slide and resolve its MPP using all available sources.

    Resolution order:
    1. openslide.mpp-x / openslide.mpp-y (canonical)
    2. Vendor-specific keys (Aperio, Hamamatsu, TIFF)
    3. Estimated from openslide.objective-power via lookup table

    Returns:
        MPPData if resolved, None if no MPP data available.
    """
    import openslide

    slide = openslide.OpenSlide(slide_path)
    try:
        props = slide.properties

        # Read objective power (may be None)
        obj_str = props.get("openslide.objective-power")
        objective = int(float(obj_str)) if obj_str else None

        # 1. Direct MPP from metadata
        mpp_x_str = props.get("openslide.mpp-x")
        mpp_y_str = props.get("openslide.mpp-y")
        if mpp_x_str and mpp_y_str:
            return MPPData(
                mpp_x=float(mpp_x_str),
                mpp_y=float(mpp_y_str),
                objective=objective,
                source="openslide",
            )

        # 2. Vendor-specific fallbacks
        vendor_result = resolve_mpp_from_properties(dict(props))
        if vendor_result:
            mpp_x, mpp_y, source = vendor_result
            return MPPData(mpp_x=mpp_x, mpp_y=mpp_y, objective=objective, source=source)

        # 3. Estimate from objective power
        if objective and objective in OBJECTIVE_TO_MPP:
            estimated = OBJECTIVE_TO_MPP[objective]
            return MPPData(
                mpp_x=estimated,
                mpp_y=estimated,
                objective=objective,
                source="estimated_from_objective",
            )

        return None
    finally:
        slide.close()


def resolve_mpp_from_properties(
    props: dict,
) -> tuple[float, float, str] | None:
    """Try to resolve MPP from slide properties using vendor-specific keys.

    Checks Aperio, Hamamatsu, and TIFF resolution tags in order.

    Returns:
        (mpp_x, mpp_y, source) tuple if resolved, None otherwise.
    """
    # Aperio
    aperio_mpp = props.get("aperio.MPP")
    if aperio_mpp:
        try:
            v = float(aperio_mpp)
            if v > 0:
                return (v, v, "aperio")
        except (ValueError, TypeError):
            pass

    # Hamamatsu: derive MPP from objective lens magnification
    hama_lens = props.get("hamamatsu.SourceLens")
    if hama_lens:
        try:
            mag = float(hama_lens)
            if mag > 0:
                v = 10.0 / mag
                return (v, v, "hamamatsu")
        except (ValueError, ZeroDivisionError):
            pass

    # TIFF resolution tags
    tiff_xres = props.get("tiff.XResolution")
    tiff_unit = props.get("tiff.ResolutionUnit")
    if tiff_xres:
        try:
            xres = float(tiff_xres)
            if xres > 0:
                if tiff_unit in {"centimeter", "3"}:
                    return (10000.0 / xres, 10000.0 / xres, "tiff")
                if tiff_unit in {"inch", "2"}:
                    return (25400.0 / xres, 25400.0 / xres, "tiff")
        except (ValueError, ZeroDivisionError):
            pass

    return None
