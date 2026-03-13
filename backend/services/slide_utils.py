"""Shared slide utilities for MPP resolution across routes and ML providers."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


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
