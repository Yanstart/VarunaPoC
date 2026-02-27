# ML Compatibility Matrix

Generated: 2026-02-27 09:51
OpenSlide: 3.4.1 | Slideflow: latest | Backend: OpenVINO (auto)

## Summary

| Metric | Count | % |
|--------|-------|---|
| Total slides scanned | 91 | 100% |
| OpenSlide opens | 73 | 80% |
| MPP metadata present | 70 | 76% |
| ML-compatible (Slideflow) | 69 | 75% |
| High load risk (>5000 tiles) | 67 | 73% |

## Failure Reasons

### Slideflow error at 10x

- `CMU-1.tiff`

### OpenSlide cannot open this file

- `Hamamatsu-1.ndpi`
- `Leica-3.scn`
- `Leica-Fluorescence-1.scn`
- `HE_BIF_1.bif`
- `Ventana-1.bif`
- `Zeiss-1-Merged.zvi`
- `Zeiss-1-Stacked.zvi`
- `Zeiss-2-Merged.zvi`
- `Zeiss-2-Stacked.zvi`
- `Zeiss-3-Mosaic.zvi`
- `Zeiss-4-Mosaic.zvi`
- `Zeiss-5-Cropped.czi`
- `Zeiss-5-Flat.czi`
- `Zeiss-5-JXR.czi`
- `Zeiss-5-SlidePreview-JXR.czi`
- `Zeiss-5-SlidePreview-Zstd0.czi`
- `Zeiss-5-SlidePreview-Zstd1-HiLo.czi`
- `Zeiss-5-Uncompressed.czi`

### No MPP metadata — Slideflow cannot determine tile scale

- `OS-1.vsi`
- `OS-2.vsi`
- `OS-3.vsi`

## Detailed Results by Format

### aperio (.svs)

> **ML: COMPATIBLE with server load risks on large slides**

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `CMU-1-JP2K-33005.svs` | 1513 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-1-Small-Region.svs` | 7 | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| `CMU-1.svs` | 1514 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-2.svs` | 2376 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-3.svs` | 2997 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `JP2K-33003-1.svs` | 269 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `JP2K-33003-2.svs` | 1538 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |

**`CMU-1-JP2K-33005.svs`**:
- **predict**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.

**`CMU-1.svs`**:
- **predict**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~29,930 tiles — may block server for 1-5 minutes on CPU.

**`CMU-2.svs`**:
- **predict**: Compatible but HIGH LOAD: ~46,980 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~46,980 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~46,980 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~46,980 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~46,980 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~46,980 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~46,980 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~46,980 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~46,980 tiles — may block server for 1-5 minutes on CPU.

**`CMU-3.svs`**:
- **predict**: Compatible but EXTREME LOAD: ~59,388 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~59,388 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~59,388 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~59,388 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~59,388 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~59,388 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~59,388 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~59,388 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~59,388 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`JP2K-33003-1.svs`**:
- **predict**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.

**`JP2K-33003-2.svs`**:
- **predict**: Compatible but HIGH LOAD: ~30,450 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~30,450 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~30,450 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~30,450 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~30,450 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~30,450 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~30,450 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~30,450 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~30,450 tiles — may block server for 1-5 minutes on CPU.

### dicom (.dcm)

> **ML: COMPATIBLE with server load risks on large slides**

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `000002.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000003.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000004.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000005.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000006.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000007.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000008.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000009.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000010.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000011.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000012.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000013.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `000014.dcm` | 3464 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.3.6.1.4.1.36533.1161292` | 516 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.3.6.1.4.1.36533.1881662` | 516 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.3.6.1.4.1.36533.2177323` | 516 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.3.6.1.4.1.36533.2391938` | 516 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.3.6.1.4.1.36533.2411761` | 516 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.3.6.1.4.1.36533.2642199` | 516 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `DCM_0.dcm` | 269 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `DCM_1.dcm` | 269 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `DCM_2.dcm` | 269 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `DCM_3.dcm` | 269 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `DCM_4.dcm` | 269 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `DCM_5.dcm` | 269 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |

**`000002.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000003.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000004.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000005.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000006.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000007.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000008.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000009.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000010.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000011.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000012.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000013.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`000014.dcm`**:
- **predict**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~68,864 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`1.3.6.1.4.1.36533.116129230228107214763613716719238114924751.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.

**`1.3.6.1.4.1.36533.1881662823325113479691652532302192524914036.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.

**`1.3.6.1.4.1.36533.21773233891171386611617621819013191107166.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.

**`1.3.6.1.4.1.36533.2391938919943337319712912711949255392271.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.

**`1.3.6.1.4.1.36533.2411761230176195652241589819186191207215116.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.

**`1.3.6.1.4.1.36533.2642199142199497125516614013324167247234250.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~10,192 tiles — may block server for 1-5 minutes on CPU.

**`DCM_0.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.

**`DCM_1.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.

**`DCM_2.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.

**`DCM_3.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.

**`DCM_4.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.

**`DCM_5.dcm`**:
- **predict**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~5,304 tiles — may block server for 1-5 minutes on CPU.

### generic-tiff (.tiff)

> **ML: INCOMPATIBLE** — None of these slides work with ML

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `CMU-1.tiff` | 1514 | OK | OK | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | OK |

**`CMU-1.tiff`**:
- **slideflow_wsi**: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_
- **predict**: Slideflow prerequisite failed: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_
- **features**: Slideflow prerequisite failed: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_
- **heatmap**: Slideflow prerequisite failed: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_
- **detect**: Slideflow prerequisite failed: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_
- **focus**: Slideflow prerequisite failed: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_
- **measure**: Slideflow prerequisite failed: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_
- **quality**: Slideflow prerequisite failed: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_
- **count**: Slideflow prerequisite failed: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_
- **cluster**: Slideflow prerequisite failed: Slideflow error at 10x
  - _Could not detect microns-per-pixel for slide: /data/VarunaPoC/Slides/Generic-TIFF/CMU-1.tiff_

### hamamatsu (.ndpi)

> **ML: COMPATIBLE with server load risks on large slides**

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `CMU-1.ndpi` | 1953 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-2.ndpi` | 2699 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-3.ndpi` | 3633 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `OS-1.ndpi` | 13590 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `OS-2.ndpi` | 9362 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `OS-3.ndpi` | 9563 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |

**`CMU-1.ndpi`**:
- **predict**: Compatible but HIGH LOAD: ~38,760 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~38,760 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~38,760 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~38,760 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~38,760 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~38,760 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~38,760 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~38,760 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~38,760 tiles — may block server for 1-5 minutes on CPU.

**`CMU-2.ndpi`**:
- **predict**: Compatible but EXTREME LOAD: ~53,400 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~53,400 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~53,400 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~53,400 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~53,400 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~53,400 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~53,400 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~53,400 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~53,400 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`CMU-3.ndpi`**:
- **predict**: Compatible but EXTREME LOAD: ~72,320 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~72,320 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~72,320 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~72,320 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~72,320 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~72,320 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~72,320 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~72,320 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~72,320 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`OS-1.ndpi`**:
- **predict**: Compatible but EXTREME LOAD: ~270,164 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~270,164 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~270,164 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~270,164 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~270,164 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~270,164 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~270,164 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~270,164 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~270,164 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`OS-2.ndpi`**:
- **predict**: Compatible but EXTREME LOAD: ~186,214 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~186,214 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~186,214 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~186,214 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~186,214 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~186,214 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~186,214 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~186,214 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~186,214 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`OS-3.ndpi`**:
- **predict**: Compatible but EXTREME LOAD: ~190,156 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~190,156 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~190,156 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~190,156 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~190,156 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~190,156 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~190,156 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~190,156 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~190,156 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

### leica (.scn)

> **ML: COMPATIBLE with server load risks on large slides**

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `Leica-1.scn` | 8154 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Leica-2.scn` | 32615 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |

**`Leica-1.scn`**:
- **predict**: Compatible but EXTREME LOAD: ~162,345 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~162,345 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~162,345 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~162,345 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~162,345 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~162,345 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~162,345 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~162,345 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~162,345 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Leica-2.scn`**:
- **predict**: Compatible but EXTREME LOAD: ~649,380 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~649,380 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~649,380 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~649,380 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~649,380 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~649,380 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~649,380 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~649,380 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~649,380 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

### mirax (.mrxs)

> **ML: COMPATIBLE with server load risks on large slides**

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `CMU-1-Exported.mrxs` | 24122 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-1-Saved-1_16.mrxs` | 115 | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| `CMU-1-Saved-1_2.mrxs` | 6732 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-1.mrxs` | 24109 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-2.mrxs` | 24109 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-3.mrxs` | 24109 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Mirax2-Fluorescence-1.mrx` | 13048 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Mirax2-Fluorescence-2.mrx` | 11018 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Mirax2.2-1.mrxs` | 22401 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Mirax2.2-2.mrxs` | 22401 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Mirax2.2-3.mrxs` | 22401 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Mirax2.2-4-BMP.mrxs` | 21987 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Mirax2.2-4-PNG.mrxs` | 21987 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.2.826.0.1.3680043.10.46` | 16240 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.2.826.0.1.3680043.10.46` | 16240 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.2.826.0.1.3680043.10.46` | 16240 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `1.2.826.0.1.3680043.10.46` | 16240 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |

**`CMU-1-Exported.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~480,680 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~480,680 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~480,680 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~480,680 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~480,680 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~480,680 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~480,680 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~480,680 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~480,680 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`CMU-1-Saved-1_2.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~133,875 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~133,875 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~133,875 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~133,875 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~133,875 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~133,875 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~133,875 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~133,875 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~133,875 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`CMU-1.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`CMU-2.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`CMU-3.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~479,695 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Mirax2-Fluorescence-1.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~259,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~259,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~259,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~259,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~259,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~259,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~259,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~259,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~259,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Mirax2-Fluorescence-2.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~218,994 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~218,994 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~218,994 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~218,994 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~218,994 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~218,994 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~218,994 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~218,994 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~218,994 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Mirax2.2-1.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Mirax2.2-2.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Mirax2.2-3.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~445,828 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Mirax2.2-4-BMP.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Mirax2.2-4-PNG.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~437,326 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`1.2.826.0.1.3680043.10.460.0.0.6443.24123153658915.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`1.2.826.0.1.3680043.10.460.0.0.6452.24123153843571.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`1.2.826.0.1.3680043.10.460.0.0.6457.2412315413660.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`1.2.826.0.1.3680043.10.460.0.0.7729.241211143415210.mrxs`**:
- **predict**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~323,468 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

### philips (.tiff)

> **ML: COMPATIBLE with server load risks on large slides**

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `Philips-1.tiff` | 1615 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Philips-2.tiff` | 21168 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Philips-3.tiff` | 13153 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `Philips-4.tiff` | 6206 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |

**`Philips-1.tiff`**:
- **predict**: Compatible but HIGH LOAD: ~32,160 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~32,160 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~32,160 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~32,160 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~32,160 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~32,160 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~32,160 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~32,160 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~32,160 tiles — may block server for 1-5 minutes on CPU.

**`Philips-2.tiff`**:
- **predict**: Compatible but EXTREME LOAD: ~421,414 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~421,414 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~421,414 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~421,414 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~421,414 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~421,414 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~421,414 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~421,414 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~421,414 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Philips-3.tiff`**:
- **predict**: Compatible but EXTREME LOAD: ~262,080 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~262,080 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~262,080 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~262,080 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~262,080 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~262,080 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~262,080 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~262,080 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~262,080 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`Philips-4.tiff`**:
- **predict**: Compatible but EXTREME LOAD: ~123,424 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~123,424 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~123,424 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~123,424 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~123,424 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~123,424 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~123,424 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~123,424 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~123,424 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

### trestle (.tif)

> **ML: COMPATIBLE with server load risks on large slides**

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `CMU-1.tif` | 1108 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-2.tif` | 1563 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `CMU-3.tif` | 2167 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |

**`CMU-1.tif`**:
- **predict**: Compatible but HIGH LOAD: ~21,894 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~21,894 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~21,894 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~21,894 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~21,894 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~21,894 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~21,894 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~21,894 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~21,894 tiles — may block server for 1-5 minutes on CPU.

**`CMU-2.tif`**:
- **predict**: Compatible but HIGH LOAD: ~30,962 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~30,962 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~30,962 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~30,962 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~30,962 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~30,962 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~30,962 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~30,962 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~30,962 tiles — may block server for 1-5 minutes on CPU.

**`CMU-3.tif`**:
- **predict**: Compatible but HIGH LOAD: ~43,180 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~43,180 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~43,180 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~43,180 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~43,180 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~43,180 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~43,180 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~43,180 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~43,180 tiles — may block server for 1-5 minutes on CPU.

### unknown (.bif)

> **ML: INCOMPATIBLE** — None of these slides work with ML

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `HE_BIF_1.bif` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Ventana-1.bif` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |

**`HE_BIF_1.bif`**:
- **openslide_open**: OpenSlide cannot open this format
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **predict**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **features**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **heatmap**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **detect**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **focus**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **measure**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **quality**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **count**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **cluster**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **tags**: Cannot read slide metadata
  - _OpenSlideError: Bad direction attribute "LEFT"_

**`Ventana-1.bif`**:
- **openslide_open**: OpenSlide cannot open this format
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **predict**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **features**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **heatmap**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **detect**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **focus**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **measure**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **quality**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **count**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **cluster**: OpenSlide cannot open this slide
  - _OpenSlideError: Bad direction attribute "LEFT"_
- **tags**: Cannot read slide metadata
  - _OpenSlideError: Bad direction attribute "LEFT"_

### unknown (.czi)

> **ML: INCOMPATIBLE** — None of these slides work with ML

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `Zeiss-5-Cropped.czi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-5-Flat.czi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-5-JXR.czi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-5-SlidePreview-JXR.` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-5-SlidePreview-Zstd` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-5-SlidePreview-Zstd` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-5-Uncompressed.czi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |

**`Zeiss-5-Cropped.czi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Cropped.czi'_

**`Zeiss-5-Flat.czi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Flat.czi'_

**`Zeiss-5-JXR.czi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-JXR.czi'_

**`Zeiss-5-SlidePreview-JXR.czi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-JXR.czi'_

**`Zeiss-5-SlidePreview-Zstd0.czi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd0.czi'_

**`Zeiss-5-SlidePreview-Zstd1-HiLo.czi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-SlidePreview-Zstd1-HiLo.czi'_

**`Zeiss-5-Uncompressed.czi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-5-Uncompressed.czi'_

### unknown (.ndpi)

> **ML: INCOMPATIBLE** — None of these slides work with ML

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `Hamamatsu-1.ndpi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |

**`Hamamatsu-1.ndpi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **predict**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **features**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **heatmap**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **detect**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **focus**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **measure**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **quality**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **count**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **cluster**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_
- **tags**: Cannot read slide metadata
  - _OpenSlideError: Can't validate JPEG for directory 0: Expected marker at 4294969977, found none_

### unknown (.scn)

> **ML: INCOMPATIBLE** — None of these slides work with ML

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `Leica-3.scn` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Leica-Fluorescence-1.scn` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |

**`Leica-3.scn`**:
- **openslide_open**: OpenSlide cannot open this format
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **predict**: OpenSlide cannot open this slide
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **features**: OpenSlide cannot open this slide
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **heatmap**: OpenSlide cannot open this slide
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **detect**: OpenSlide cannot open this slide
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **focus**: OpenSlide cannot open this slide
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **measure**: OpenSlide cannot open this slide
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **quality**: OpenSlide cannot open this slide
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **count**: OpenSlide cannot open this slide
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **cluster**: OpenSlide cannot open this slide
  - _OpenSlideError: Slides with dissimilar main images are not supported_
- **tags**: Cannot read slide metadata
  - _OpenSlideError: Slides with dissimilar main images are not supported_

**`Leica-Fluorescence-1.scn`**:
- **openslide_open**: OpenSlide cannot open this format
  - _OpenSlideError: Can't find main image_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _OpenSlideError: Can't find main image_
- **predict**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't find main image_
- **features**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't find main image_
- **heatmap**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't find main image_
- **detect**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't find main image_
- **focus**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't find main image_
- **measure**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't find main image_
- **quality**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't find main image_
- **count**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't find main image_
- **cluster**: OpenSlide cannot open this slide
  - _OpenSlideError: Can't find main image_
- **tags**: Cannot read slide metadata
  - _OpenSlideError: Can't find main image_

### unknown (.vsi)

> **ML: INCOMPATIBLE** — None of these slides work with ML

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `OS-1.vsi` | 0 | OK | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | OK |
| `OS-2.vsi` | 0 | OK | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | OK |
| `OS-3.vsi` | 0 | OK | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | OK |

**`OS-1.vsi`**:
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **predict**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **features**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **heatmap**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **detect**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **focus**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **measure**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **quality**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **count**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **cluster**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._

**`OS-2.vsi`**:
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **predict**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **features**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **heatmap**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **detect**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **focus**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **measure**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **quality**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **count**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **cluster**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._

**`OS-3.vsi`**:
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **predict**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **features**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **heatmap**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **detect**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **focus**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **measure**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **quality**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **count**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._
- **cluster**: Slideflow prerequisite failed: No MPP metadata — Slideflow cannot determine tile scale
  - _openslide.mpp-x property is missing. Generic TIFF files lack scanner resolution metadata._

### unknown (.zvi)

> **ML: INCOMPATIBLE** — None of these slides work with ML

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `Zeiss-1-Merged.zvi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-1-Stacked.zvi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-2-Merged.zvi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-2-Stacked.zvi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-3-Mosaic.zvi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| `Zeiss-4-Mosaic.zvi` | 0 | FAIL | FAIL | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |

**`Zeiss-1-Merged.zvi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Merged.zvi'_

**`Zeiss-1-Stacked.zvi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-1-Stacked.zvi'_

**`Zeiss-2-Merged.zvi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Merged.zvi'_

**`Zeiss-2-Stacked.zvi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-2-Stacked.zvi'_

**`Zeiss-3-Mosaic.zvi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-3-Mosaic.zvi'_

**`Zeiss-4-Mosaic.zvi`**:
- **openslide_open**: OpenSlide cannot open this format
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **mpp_available**: No microns-per-pixel metadata in slide properties
  - _This format does not embed scanner resolution. All ML features requiring tiling will fail._
- **slideflow_wsi**: OpenSlide cannot open this file
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **predict**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **features**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **heatmap**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **detect**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **focus**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **measure**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **quality**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **count**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **cluster**: OpenSlide cannot open this slide
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_
- **tags**: Cannot read slide metadata
  - _UnidentifiedImageError: cannot identify image file '/data/VarunaPoC/Slides/Zeiss CZI and ZVI/Zeiss-4-Mosaic.zvi'_

### ventana (.bif)

> **ML: COMPATIBLE with server load risks on large slides**

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `OS-1.bif` | 9941 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `OS-2.bif` | 8776 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |

**`OS-1.bif`**:
- **predict**: Compatible but EXTREME LOAD: ~197,768 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~197,768 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~197,768 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~197,768 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~197,768 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~197,768 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~197,768 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~197,768 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~197,768 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`OS-2.bif`**:
- **predict**: Compatible but EXTREME LOAD: ~174,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~174,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~174,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~174,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~174,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~174,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~174,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~174,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~174,420 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

### ventana (.tif)

> **ML: COMPATIBLE with server load risks on large slides**

| Slide | MP | openslid | mpp_avai | slideflo | predict | features | heatmap | detect | focus | measure | quality | count | cluster | tags |
|-------|-----|------|------|------|------|------|------|------|------|------|------|------|------|------|
| `24P14876.tif` | 5168 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `AO.25C16090.1.1.1.tif` | 4063 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |
| `HE_TIF_1.tif` | 973 | OK | OK | OK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | RISK | OK |

**`24P14876.tif`**:
- **predict**: Compatible but EXTREME LOAD: ~102,858 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~102,858 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~102,858 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~102,858 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~102,858 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~102,858 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~102,858 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~102,858 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~102,858 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`AO.25C16090.1.1.1.tif`**:
- **predict**: Compatible but EXTREME LOAD: ~80,712 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **features**: Compatible but EXTREME LOAD: ~80,712 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **heatmap**: Compatible but EXTREME LOAD: ~80,712 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **detect**: Compatible but EXTREME LOAD: ~80,712 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **focus**: Compatible but EXTREME LOAD: ~80,712 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **measure**: Compatible but EXTREME LOAD: ~80,712 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **quality**: Compatible but EXTREME LOAD: ~80,712 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **count**: Compatible but EXTREME LOAD: ~80,712 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.
- **cluster**: Compatible but EXTREME LOAD: ~80,712 tiles — will block single-worker server for 10+ minutes on CPU. Use batch endpoint or region-based inference.

**`HE_TIF_1.tif`**:
- **predict**: Compatible but HIGH LOAD: ~19,250 tiles — may block server for 1-5 minutes on CPU.
- **features**: Compatible but HIGH LOAD: ~19,250 tiles — may block server for 1-5 minutes on CPU.
- **heatmap**: Compatible but HIGH LOAD: ~19,250 tiles — may block server for 1-5 minutes on CPU.
- **detect**: Compatible but HIGH LOAD: ~19,250 tiles — may block server for 1-5 minutes on CPU.
- **focus**: Compatible but HIGH LOAD: ~19,250 tiles — may block server for 1-5 minutes on CPU.
- **measure**: Compatible but HIGH LOAD: ~19,250 tiles — may block server for 1-5 minutes on CPU.
- **quality**: Compatible but HIGH LOAD: ~19,250 tiles — may block server for 1-5 minutes on CPU.
- **count**: Compatible but HIGH LOAD: ~19,250 tiles — may block server for 1-5 minutes on CPU.
- **cluster**: Compatible but HIGH LOAD: ~19,250 tiles — may block server for 1-5 minutes on CPU.

## Recommendations

### For missing MPP (Generic TIFF)
- These files have no scanner resolution metadata embedded
- **Workaround**: Convert to SVS format with a tool like `bioformats2raw` + `raw2ometiff`, or set MPP manually via a TIFF tag editor
- **Alternative**: Add a `--mpp-override` option to the ML pipeline that accepts user-provided MPP

### For unsupported formats (DICOM, CZI, ZVI, VSI)
- **DICOM/CZI**: Require OpenSlide >= 4.0.0 (current: 3.4.1)
- **ZVI/VSI**: Not supported by OpenSlide at any version — convert to SVS/TIFF with vendor tools

### For server blocking (large slides)
- **Short term**: Use region-based inference (`region` param in predict/features)
- **Medium term**: Add multi-worker uvicorn or background task queue (Celery/RQ)
- **Long term**: Implement tile-level streaming inference with progress reporting

### For BIF direction errors
- Known OpenSlide bug with some Ventana BIF files
- **Workaround**: Convert affected BIF files to SVS with `vips tiffsave input.bif output.svs --pyramid`
