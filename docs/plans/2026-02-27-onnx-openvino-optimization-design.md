# ONNX/OpenVINO Inference Optimization

**Date**: 2026-02-27
**Status**: Approved
**Scope**: Optimize Phikon-v2 CPU inference via ONNX Runtime and OpenVINO

## Problem

Phikon-v2 inference on CPU (i7-9700T) takes ~30-100ms per tile. A large slide
(100K+ px) has thousands of tiles, blocking the single-worker uvicorn server
for minutes. ML features are unusable in practice.

## Solution

Add configurable inference backend (`ML_BACKEND=auto|pytorch|onnx|openvino`)
to `_PhikonExtractor` in `slideflow_provider.py`. Export Phikon-v2 to ONNX
format once, then use ONNX Runtime or OpenVINO for optimized CPU inference.

Expected speedup: 3-8x on Intel CPUs.

## Configuration

```
ML_BACKEND=auto    # auto tries openvino -> onnx -> pytorch
```

## Architecture

```
_PhikonExtractor.__init__(backend="auto")
    |
    +--> "openvino" -> openvino.Core().compile_model("phikon-v2.onnx")
    +--> "onnx"     -> onnxruntime.InferenceSession("phikon-v2.onnx")
    +--> "pytorch"  -> AutoModel.from_pretrained("owkin/phikon-v2")

_PhikonExtractor.__call__(batch)
    |
    +--> Same preprocessing (float32, normalize)
    +--> Dispatch to backend-specific inference
    +--> Same output: (B, 1024) float32 embeddings
```

## Files

| File | Change |
|------|--------|
| `services/ml/providers/slideflow_provider.py` | Multi-backend _PhikonExtractor |
| `scripts/export_phikon_onnx.py` | New: one-time ONNX export script |
| `requirements.txt` | Add onnxruntime, openvino |
| `models/` | New: directory for exported ONNX models |

## Unchanged

- REST API (same endpoints, same responses)
- SlideflowProvider public interface
- Tile processing pipeline (OpenSlide/Slideflow WSI)
