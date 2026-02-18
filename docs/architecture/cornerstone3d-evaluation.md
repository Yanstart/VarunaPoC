# Cornerstone3D Architecture Evaluation

## Decision: NO-GO for current phase

### Summary
After evaluating Cornerstone3D + VTK.js for 3D medical viewer capabilities,
the recommendation is to **keep OpenSeadragon for 2D WSI** and defer Cornerstone3D
integration to a future phase when 3D features are actively needed.

### Evaluation Criteria

| Criterion | OpenSeadragon | Cornerstone3D | Notes |
|-----------|--------------|---------------|-------|
| 2D WSI viewing | Excellent | Overkill | OSD is purpose-built for tile-based 2D |
| WebGL performance | Good (OSD 4.x) | Excellent | CS3D has full GPU pipeline |
| Tile protocols | DZI, IIIF, custom | DICOM WADO | Different ecosystems |
| Bundle size | ~200KB | ~2MB+ | CS3D + VTK.js is heavy |
| Z-stack support | None | Native | Only needed for confocal/3D |
| Community | Large, active | Growing, medical | Both well-maintained |
| Integration effort | Already done | 2-4 weeks | Significant refactoring |

### Recommendation
1. **Keep OSD** as primary 2D WSI viewer — it's fast, lightweight, well-integrated
2. **Create ViewerInterface abstraction** — decouple viewer API from implementation
3. **Add Cornerstone3D later** — when Z-stack or 3D reconstruction features are requested
4. **OSDViewerAdapter** wraps current OSD usage behind the interface
5. **CornerstoneViewerAdapter** (stub) prepared for future implementation

### Resources
- Cornerstone3D: https://www.cornerstonejs.org/
- VTK.js: https://kitware.github.io/vtk-js/
