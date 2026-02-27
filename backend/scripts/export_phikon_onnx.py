"""
Export Phikon-v2 model from PyTorch to ONNX format.

Usage:
    python scripts/export_phikon_onnx.py
    python scripts/export_phikon_onnx.py --quantize
    python scripts/export_phikon_onnx.py --output ml_models/phikon-v2.onnx
"""

import argparse
import time
from pathlib import Path

import numpy as np
import torch
from transformers import AutoImageProcessor, AutoModel


def export_onnx(output_path: Path, opset_version: int = 17) -> Path:
    """Export Phikon-v2 to ONNX format."""
    print("Loading Phikon-v2 from HuggingFace...")
    model = AutoModel.from_pretrained("owkin/phikon-v2")
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224)

    print(f"Exporting to ONNX (opset {opset_version})...")
    torch.onnx.export(
        model,
        (dummy_input,),
        str(output_path),
        input_names=["pixel_values"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "pixel_values": {0: "batch_size"},
            "last_hidden_state": {0: "batch_size"},
        },
        opset_version=opset_version,
    )

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Exported: {output_path} ({size_mb:.1f} MB)")
    return output_path


def quantize_onnx(input_path: Path) -> Path:
    """Apply dynamic INT8 quantization to ONNX model."""
    from onnxruntime.quantization import QuantType, quantize_dynamic

    output_path = input_path.with_suffix(".quant.onnx")
    print("Applying INT8 dynamic quantization...")

    quantize_dynamic(
        str(input_path),
        str(output_path),
        weight_type=QuantType.QInt8,
    )

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Quantized: {output_path} ({size_mb:.1f} MB)")
    return output_path


def validate(onnx_path: Path):
    """Validate ONNX model produces same output as PyTorch."""
    import onnxruntime as ort

    print("Validating ONNX output vs PyTorch...")

    # PyTorch reference
    model = AutoModel.from_pretrained("owkin/phikon-v2")
    processor = AutoImageProcessor.from_pretrained("owkin/phikon-v2")
    model.eval()

    dummy = torch.randn(1, 3, 224, 224)
    normalized = (dummy.float() - torch.tensor(processor.image_mean).view(1, 3, 1, 1)) / torch.tensor(
        processor.image_std
    ).view(1, 3, 1, 1)

    with torch.no_grad():
        pt_out = model(pixel_values=normalized).last_hidden_state[:, 0, :].numpy()

    # ONNX inference
    session = ort.InferenceSession(str(onnx_path))
    onnx_full = session.run(None, {"pixel_values": normalized.numpy()})[0]
    onnx_out = onnx_full[:, 0, :]  # CLS token

    # Compare
    max_diff = np.max(np.abs(pt_out - onnx_out))
    print(f"Max absolute difference: {max_diff:.8f}")
    if max_diff < 1e-4:
        print("PASS: ONNX output matches PyTorch")
    else:
        print(f"WARNING: Difference {max_diff} exceeds 1e-4 threshold")


def benchmark(onnx_path: Path, quantized_path: Path | None, n_iterations: int = 50):
    """Benchmark PyTorch vs ONNX vs quantized ONNX vs OpenVINO."""
    import onnxruntime as ort

    processor = AutoImageProcessor.from_pretrained("owkin/phikon-v2")
    dummy = torch.randn(1, 3, 224, 224)
    normalized = (dummy.float() - torch.tensor(processor.image_mean).view(1, 3, 1, 1)) / torch.tensor(
        processor.image_std
    ).view(1, 3, 1, 1)
    np_input = normalized.numpy()

    results = {}

    # PyTorch
    model = AutoModel.from_pretrained("owkin/phikon-v2")
    model.eval()
    for _ in range(3):
        with torch.no_grad():
            model(pixel_values=normalized)
    start = time.perf_counter()
    for _ in range(n_iterations):
        with torch.no_grad():
            model(pixel_values=normalized)
    pt_time = (time.perf_counter() - start) / n_iterations * 1000
    results["pytorch"] = pt_time
    del model

    # ONNX Runtime
    session = ort.InferenceSession(str(onnx_path))
    for _ in range(3):
        session.run(None, {"pixel_values": np_input})
    start = time.perf_counter()
    for _ in range(n_iterations):
        session.run(None, {"pixel_values": np_input})
    onnx_time = (time.perf_counter() - start) / n_iterations * 1000
    results["onnx"] = onnx_time
    del session

    # Quantized ONNX
    if quantized_path and quantized_path.exists():
        session = ort.InferenceSession(str(quantized_path))
        for _ in range(3):
            session.run(None, {"pixel_values": np_input})
        start = time.perf_counter()
        for _ in range(n_iterations):
            session.run(None, {"pixel_values": np_input})
        quant_time = (time.perf_counter() - start) / n_iterations * 1000
        results["onnx_quantized"] = quant_time
        del session

    # OpenVINO
    try:
        import openvino as ov

        core = ov.Core()
        ov_model = core.compile_model(str(onnx_path), "CPU")
        infer_request = ov_model.create_infer_request()
        for _ in range(3):
            infer_request.infer({"pixel_values": np_input})
        start = time.perf_counter()
        for _ in range(n_iterations):
            infer_request.infer({"pixel_values": np_input})
        ov_time = (time.perf_counter() - start) / n_iterations * 1000
        results["openvino"] = ov_time
    except ImportError:
        print("OpenVINO not installed, skipping benchmark")

    # Report
    print(f"\n{'Backend':<20} {'ms/inference':<15} {'Speedup vs PyTorch'}")
    print("-" * 55)
    for name, ms in results.items():
        speedup = results["pytorch"] / ms
        print(f"{name:<20} {ms:>8.1f} ms     {speedup:>5.1f}x")


def main():
    parser = argparse.ArgumentParser(description="Export Phikon-v2 to ONNX")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "ml_models" / "phikon-v2.onnx",
    )
    parser.add_argument("--quantize", action="store_true", help="Apply INT8 quantization")
    parser.add_argument("--validate", action="store_true", help="Validate output matches PyTorch")
    parser.add_argument("--benchmark", action="store_true", help="Benchmark all backends")
    parser.add_argument("--all", action="store_true", help="Export + quantize + validate + benchmark")
    args = parser.parse_args()

    if args.all:
        args.quantize = args.validate = args.benchmark = True

    args.output.parent.mkdir(parents=True, exist_ok=True)

    onnx_path = export_onnx(args.output)

    quantized_path = None
    if args.quantize:
        quantized_path = quantize_onnx(onnx_path)

    if args.validate:
        validate(onnx_path)

    if args.benchmark:
        benchmark(onnx_path, quantized_path)

    print("\nDone.")


if __name__ == "__main__":
    main()
