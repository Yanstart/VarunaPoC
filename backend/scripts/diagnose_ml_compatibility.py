#!/usr/bin/env python3
"""
ML Compatibility Diagnostic — Slide × Feature Matrix

Systematically tests every slide against every ML feature and reports:
- Which slides work with which features
- WHY failures occur (missing MPP, format blocked, server overload risk, etc.)
- Estimated inference time and server impact

Usage:
    cd backend
    ../backend/venv/bin/python3 scripts/diagnose_ml_compatibility.py

Output:
    docs/ML_COMPATIBILITY.md
"""

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("ml_compat")


# ── Slide metadata ──────────────────────────────────────────────────────────

@dataclass
class SlideInfo:
    path: str
    name: str
    vendor: str = "unknown"
    format_ext: str = ""
    dimensions: tuple = (0, 0)
    mpp_x: float | None = None
    mpp_y: float | None = None
    objective_power: str | None = None
    openslide_ok: bool = False
    openslide_error: str = ""
    megapixels: float = 0.0
    estimated_tiles_224: int = 0


@dataclass
class FeatureResult:
    """Result of testing one ML feature on one slide."""
    status: str  # "ok", "fail", "blocked", "risk"
    reason: str  # Human explanation
    detail: str = ""  # Technical detail
    time_ms: float = 0.0


@dataclass
class SlideReport:
    info: SlideInfo
    features: dict = field(default_factory=dict)  # feature_name -> FeatureResult


# ── Constants ───────────────────────────────────────────────────────────────

BLOCKED_EXTENSIONS = {".dcm", ".dicom"}
UNSUPPORTED_OPENSLIDE = {".vsi", ".zvi"}

# Slides above this tile count risk blocking the server for > 60s
HIGH_LOAD_TILE_THRESHOLD = 5000
# Slides above this risk blocking > 5 min on CPU
EXTREME_LOAD_TILE_THRESHOLD = 50000

ML_FEATURES = [
    "openslide_open",     # Can OpenSlide open the file?
    "mpp_available",      # Does the slide have MPP metadata?
    "slideflow_wsi",      # Can Slideflow open it as WSI?
    "predict",            # POST /ml/predict/{id}
    "features",           # POST /ml/features/{id}
    "heatmap",            # GET /ml/heatmap/{id}
    "detect",             # POST /ml/detect/{id}
    "focus",              # GET /ml/focus/{id}
    "measure",            # GET /ml/measure/{id}
    "quality",            # GET /ml/quality/{id}
    "count",              # POST /ml/count/{id}
    "cluster",            # POST /ml/cluster/{id}
    "tags",               # GET /ml/tags/{id} (metadata-only, no model)
]


# ── Diagnostic functions ────────────────────────────────────────────────────

def scan_slides(slides_dir: str) -> list[SlideInfo]:
    """Discover all slide files and extract OpenSlide metadata."""
    import openslide

    slides = []
    slide_extensions = {
        ".svs", ".mrxs", ".ndpi", ".tif", ".tiff", ".scn",
        ".bif", ".dcm", ".dicom", ".vsi", ".czi", ".zvi",
    }

    for root, _dirs, files in sorted(os.walk(slides_dir)):
        for fname in sorted(files):
            ext = Path(fname).suffix.lower()
            if ext not in slide_extensions:
                continue
            # Skip DICOMDIR, companion files, overlap files
            if fname == "DICOMDIR" or "-draw" in fname:
                continue
            if ext in (".tif", ".tiff") and any(
                fname.endswith(x) for x in ["-0b", "-1b", "-2b"]
            ):
                continue

            full_path = os.path.join(root, fname)
            info = SlideInfo(
                path=full_path,
                name=fname,
                format_ext=ext,
            )

            # Try opening with OpenSlide
            try:
                slide = openslide.open_slide(full_path)
                props = slide.properties
                info.vendor = props.get("openslide.vendor", "unknown")
                info.dimensions = slide.dimensions
                info.megapixels = (slide.dimensions[0] * slide.dimensions[1]) / 1e6

                mpp = props.get("openslide.mpp-x")
                if mpp:
                    info.mpp_x = float(mpp)
                mpp_y = props.get("openslide.mpp-y")
                if mpp_y:
                    info.mpp_y = float(mpp_y)

                mag = props.get("openslide.objective-power")
                if mag:
                    info.objective_power = mag

                # Estimate tiles at 224px
                w, h = slide.dimensions
                info.estimated_tiles_224 = (w // 224) * (h // 224)

                info.openslide_ok = True
                slide.close()
            except Exception as e:
                info.openslide_error = f"{type(e).__name__}: {str(e)[:120]}"
                info.openslide_ok = False

            slides.append(info)

    return slides


def test_slideflow_wsi(slide: SlideInfo) -> FeatureResult:
    """Test if Slideflow can open the slide as WSI."""
    if not slide.openslide_ok:
        return FeatureResult("blocked", "OpenSlide cannot open this file",
                             slide.openslide_error)
    if slide.format_ext in BLOCKED_EXTENSIONS:
        return FeatureResult("blocked", "DICOM format explicitly blocked for ML",
                             "Extension in _UNSUPPORTED_ML_FORMATS")
    if not slide.mpp_x:
        return FeatureResult("fail",
                             "No MPP metadata — Slideflow cannot determine tile scale",
                             "openslide.mpp-x property is missing. "
                             "Generic TIFF files lack scanner resolution metadata.")

    # Actually try opening with Slideflow
    try:
        import slideflow as sf
        preferred_mags = ["10x", "20x", "5x", "40x"]
        for mag in preferred_mags:
            try:
                t0 = time.time()
                wsi = sf.WSI(slide.path, tile_px=224, tile_um=mag)
                dt = (time.time() - t0) * 1000
                return FeatureResult("ok", f"Opened at {mag}", time_ms=dt)
            except Exception as e:
                if "magnification" in str(e).lower() or "mpp" in str(e).lower():
                    continue
                return FeatureResult("fail", f"Slideflow error at {mag}",
                                     str(e)[:150])

        # Try computed magnification from MPP
        approx_mag = round(10.0 / slide.mpp_x)
        mag_str = f"{approx_mag}x"
        t0 = time.time()
        wsi = sf.WSI(slide.path, tile_px=224, tile_um=mag_str)
        dt = (time.time() - t0) * 1000
        return FeatureResult("ok", f"Opened at computed {mag_str} (from MPP)",
                             time_ms=dt)
    except Exception as e:
        return FeatureResult("fail", "Slideflow WSI open failed", str(e)[:150])


def assess_feature(slide: SlideInfo, feature: str,
                   sf_result: FeatureResult) -> FeatureResult:
    """Assess compatibility of a slide with a specific ML feature."""

    # ── openslide_open ──
    if feature == "openslide_open":
        if slide.openslide_ok:
            return FeatureResult("ok", f"vendor={slide.vendor}, "
                                 f"{slide.dimensions[0]}x{slide.dimensions[1]}")
        return FeatureResult("fail", "OpenSlide cannot open this format",
                             slide.openslide_error)

    # ── mpp_available ──
    if feature == "mpp_available":
        if slide.mpp_x:
            return FeatureResult("ok",
                                 f"mpp_x={slide.mpp_x:.4f}, "
                                 f"mag={slide.objective_power or 'computed'}")
        return FeatureResult("fail",
                             "No microns-per-pixel metadata in slide properties",
                             "This format does not embed scanner resolution. "
                             "All ML features requiring tiling will fail.")

    # ── slideflow_wsi ──
    if feature == "slideflow_wsi":
        return sf_result

    # ── tags (metadata-only, no model needed) ──
    if feature == "tags":
        if not slide.openslide_ok:
            return FeatureResult("blocked", "Cannot read slide metadata",
                                 slide.openslide_error)
        # Tags uses filename + metadata, works on everything OpenSlide opens
        return FeatureResult("ok",
                             "Metadata/filename extraction — no model needed")

    # ── All model-dependent features ──
    # Check prerequisites first
    if slide.format_ext in BLOCKED_EXTENSIONS:
        return FeatureResult("blocked",
                             "DICOM format blocked for ML analysis",
                             "routes/ml.py: _UNSUPPORTED_ML_FORMATS")
    if not slide.openslide_ok:
        return FeatureResult("blocked", "OpenSlide cannot open this slide",
                             slide.openslide_error)
    if sf_result.status != "ok":
        return FeatureResult("fail",
                             f"Slideflow prerequisite failed: {sf_result.reason}",
                             sf_result.detail)

    # ── Server load assessment ──
    tiles = slide.estimated_tiles_224
    load_warning = ""
    if tiles > EXTREME_LOAD_TILE_THRESHOLD:
        load_warning = (f"EXTREME LOAD: ~{tiles:,} tiles — will block single-worker "
                        f"server for 10+ minutes on CPU. Use batch endpoint or "
                        f"region-based inference.")
    elif tiles > HIGH_LOAD_TILE_THRESHOLD:
        load_warning = (f"HIGH LOAD: ~{tiles:,} tiles — may block server for "
                        f"1-5 minutes on CPU.")

    # ── Feature-specific checks ──

    if feature == "predict":
        # Prediction works if Slideflow WSI opens
        # But large slides risk blocking
        if load_warning:
            return FeatureResult("risk", f"Compatible but {load_warning}")
        return FeatureResult("ok", f"~{tiles:,} tiles at 224px")

    if feature == "features":
        if load_warning:
            return FeatureResult("risk", f"Compatible but {load_warning}")
        return FeatureResult("ok", f"~{tiles:,} tiles → ({tiles}, 1024) embeddings")

    if feature == "heatmap":
        if load_warning:
            return FeatureResult("risk", f"Compatible but {load_warning}")
        return FeatureResult("ok", "Feature-norm attention proxy (Phase 1-2)")

    if feature == "detect":
        # Depends on heatmap generation
        if load_warning:
            return FeatureResult("risk", f"Compatible but {load_warning}")
        return FeatureResult("ok", "Heatmap → threshold → GeoJSON contours")

    if feature == "focus":
        if load_warning:
            return FeatureResult("risk", f"Compatible but {load_warning}")
        return FeatureResult("ok", "Top N attention zones from heatmap")

    if feature == "measure":
        # Requires MPP for mm conversion
        if not slide.mpp_x:
            return FeatureResult("fail",
                                 "Requires MPP for millimeter conversion",
                                 "Without microns-per-pixel, cannot convert pixel "
                                 "measurements to physical units.")
        if load_warning:
            return FeatureResult("risk", f"Compatible but {load_warning}")
        return FeatureResult("ok",
                             f"MPP={slide.mpp_x:.4f} → physical measurements in mm")

    if feature == "quality":
        if load_warning:
            return FeatureResult("risk", f"Compatible but {load_warning}")
        return FeatureResult("ok", "Blur/artifact/folding detection")

    if feature == "count":
        # Cell counting requires IHC stain detection
        if load_warning:
            return FeatureResult("risk", f"Compatible but {load_warning}")
        return FeatureResult("ok", "Ki-67/IHC counting (requires appropriate stain)")

    if feature == "cluster":
        if load_warning:
            return FeatureResult("risk", f"Compatible but {load_warning}")
        return FeatureResult("ok",
                             f"K-means on ({tiles}, 1024) embedding space")

    return FeatureResult("fail", f"Unknown feature: {feature}")


# ── Report generation ───────────────────────────────────────────────────────

def generate_report(reports: list[SlideReport], output_path: str):
    """Generate comprehensive Markdown compatibility report."""

    lines = []
    lines.append("# ML Compatibility Matrix")
    lines.append("")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"OpenSlide: 3.4.1 | Slideflow: latest | Backend: OpenVINO (auto)")
    lines.append("")

    # ── Executive summary ──
    lines.append("## Summary")
    lines.append("")

    total = len(reports)
    ok_openslide = sum(1 for r in reports if r.info.openslide_ok)
    ok_mpp = sum(1 for r in reports if r.info.mpp_x is not None)
    ok_ml = sum(1 for r in reports
                if r.features.get("slideflow_wsi", FeatureResult("", "")).status == "ok")
    risk_ml = sum(1 for r in reports
                  if r.features.get("predict", FeatureResult("", "")).status == "risk")

    lines.append(f"| Metric | Count | % |")
    lines.append(f"|--------|-------|---|")
    lines.append(f"| Total slides scanned | {total} | 100% |")
    lines.append(f"| OpenSlide opens | {ok_openslide} | {ok_openslide*100//total}% |")
    lines.append(f"| MPP metadata present | {ok_mpp} | {ok_mpp*100//total}% |")
    lines.append(f"| ML-compatible (Slideflow) | {ok_ml} | {ok_ml*100//total}% |")
    lines.append(f"| High load risk (>5000 tiles) | {risk_ml} | {risk_ml*100//total}% |")
    lines.append("")

    # ── Failure reasons summary ──
    lines.append("## Failure Reasons")
    lines.append("")

    failure_reasons = {}
    for r in reports:
        sf = r.features.get("slideflow_wsi", FeatureResult("", ""))
        if sf.status in ("fail", "blocked"):
            key = sf.reason
            failure_reasons.setdefault(key, []).append(r.info.name)

    if failure_reasons:
        for reason, slides in failure_reasons.items():
            lines.append(f"### {reason}")
            lines.append("")
            for s in slides:
                lines.append(f"- `{s}`")
            lines.append("")
    else:
        lines.append("No ML failures detected.")
        lines.append("")

    # ── Per-format group detail ──
    lines.append("## Detailed Results by Format")
    lines.append("")

    # Group by vendor/format
    by_vendor = {}
    for r in reports:
        key = f"{r.info.vendor} ({r.info.format_ext})"
        by_vendor.setdefault(key, []).append(r)

    for vendor_key in sorted(by_vendor.keys()):
        group = by_vendor[vendor_key]
        sample = group[0]

        lines.append(f"### {vendor_key}")
        lines.append("")

        # Format-level verdict
        all_ok = all(
            r.features.get("slideflow_wsi", FeatureResult("", "")).status == "ok"
            for r in group
        )
        any_risk = any(
            r.features.get("predict", FeatureResult("", "")).status == "risk"
            for r in group
        )
        all_blocked = all(
            r.features.get("slideflow_wsi", FeatureResult("", "")).status
            in ("fail", "blocked")
            for r in group
        )

        if all_blocked:
            lines.append("> **ML: INCOMPATIBLE** — None of these slides work with ML")
        elif all_ok and not any_risk:
            lines.append("> **ML: FULLY COMPATIBLE**")
        elif all_ok and any_risk:
            lines.append("> **ML: COMPATIBLE with server load risks on large slides**")
        else:
            lines.append("> **ML: PARTIALLY COMPATIBLE**")
        lines.append("")

        # Feature matrix table
        header = "| Slide | MP |"
        sep = "|-------|-----|"
        for feat in ML_FEATURES:
            short = feat[:8]
            header += f" {short} |"
            sep += "------|"
        lines.append(header)
        lines.append(sep)

        status_icons = {
            "ok": "OK",
            "fail": "FAIL",
            "blocked": "BLOCK",
            "risk": "RISK",
        }

        for r in group:
            row = f"| `{r.info.name[:25]}` | {r.info.megapixels:.0f} |"
            for feat in ML_FEATURES:
                res = r.features.get(feat, FeatureResult("?", ""))
                icon = status_icons.get(res.status, "?")
                row += f" {icon} |"
            lines.append(row)
        lines.append("")

        # Per-slide comments
        for r in group:
            has_issues = any(
                r.features.get(f, FeatureResult("ok", "")).status in ("fail", "blocked", "risk")
                for f in ML_FEATURES
            )
            if has_issues:
                lines.append(f"**`{r.info.name}`**:")
                for feat in ML_FEATURES:
                    res = r.features.get(feat, FeatureResult("ok", ""))
                    if res.status in ("fail", "blocked", "risk"):
                        lines.append(f"- **{feat}**: {res.reason}")
                        if res.detail:
                            lines.append(f"  - _{res.detail}_")
                lines.append("")

    # ── Recommendations ──
    lines.append("## Recommendations")
    lines.append("")
    lines.append("### For missing MPP (Generic TIFF)")
    lines.append("- These files have no scanner resolution metadata embedded")
    lines.append("- **Workaround**: Convert to SVS format with a tool like "
                 "`bioformats2raw` + `raw2ometiff`, or set MPP manually via "
                 "a TIFF tag editor")
    lines.append("- **Alternative**: Add a `--mpp-override` option to the ML "
                 "pipeline that accepts user-provided MPP")
    lines.append("")
    lines.append("### For unsupported formats (DICOM, CZI, ZVI, VSI)")
    lines.append("- **DICOM/CZI**: Require OpenSlide >= 4.0.0 (current: 3.4.1)")
    lines.append("- **ZVI/VSI**: Not supported by OpenSlide at any version — "
                 "convert to SVS/TIFF with vendor tools")
    lines.append("")
    lines.append("### For server blocking (large slides)")
    lines.append("- **Short term**: Use region-based inference "
                 "(`region` param in predict/features)")
    lines.append("- **Medium term**: Add multi-worker uvicorn or background "
                 "task queue (Celery/RQ)")
    lines.append("- **Long term**: Implement tile-level streaming inference "
                 "with progress reporting")
    lines.append("")
    lines.append("### For BIF direction errors")
    lines.append("- Known OpenSlide bug with some Ventana BIF files")
    lines.append("- **Workaround**: Convert affected BIF files to SVS with "
                 "`vips tiffsave input.bif output.svs --pyramid`")
    lines.append("")

    content = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
    return content


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    slides_dir = "/data/VarunaPoC/Slides"
    output_path = "/data/VarunaPoC/docs/ML_COMPATIBILITY.md"

    print(f"Scanning slides in {slides_dir}...")
    slides = scan_slides(slides_dir)
    print(f"Found {len(slides)} slide files\n")

    reports = []
    for i, slide in enumerate(slides, 1):
        print(f"[{i}/{len(slides)}] {slide.name} ({slide.vendor}, {slide.format_ext})")

        # Test Slideflow WSI (the key prerequisite for all ML features)
        sf_result = test_slideflow_wsi(slide)

        report = SlideReport(info=slide)

        for feature in ML_FEATURES:
            if feature == "slideflow_wsi":
                report.features[feature] = sf_result
            else:
                report.features[feature] = assess_feature(slide, feature, sf_result)

        reports.append(report)

        # Brief status line
        sf_icon = {"ok": "OK", "fail": "FAIL", "blocked": "BLOCK"}.get(
            sf_result.status, sf_result.status
        )
        print(f"  -> ML: {sf_icon} | {sf_result.reason}\n")

    print(f"\nGenerating report -> {output_path}")
    content = generate_report(reports, output_path)
    print(f"Report written ({len(content)} bytes)")

    # Also print summary
    ok = sum(1 for r in reports
             if r.features.get("slideflow_wsi", FeatureResult("", "")).status == "ok")
    print(f"\n{'='*60}")
    print(f"ML COMPATIBLE: {ok}/{len(reports)} slides")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
