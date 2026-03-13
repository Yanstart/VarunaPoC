"""
Slideflow ML Provider

Implémentation de MLProvider interface avec Slideflow framework.
Supporte 3 modes progressifs:

Phase 1-2 (extractor): Feature extraction avec modèles pré-entraînés
  - CTransPath, RetCCL, Virchow, UNI, Phikon, GigaPath, ResNet50
  - extract_features() fonctionne immédiatement
  - predict() utilise analyse basée sur features (tissue/background)
  - generate_heatmap() utilise feature norms comme attention proxy

Phase 3 (classifier): Classification avec modèle entraîné
  - predict() fait de la vraie classification ML
  - generate_heatmap() utilise Grad-CAM
  - Feedback pathologiste pour amélioration continue

Configuration via variables d'environnement:
  ML_PROVIDER=slideflow
  ML_MODE=extractor          # "extractor" ou "classifier"
  ML_EXTRACTOR=ctranspath    # Nom du feature extractor
  ML_MODEL_PATH=             # Chemin modèle entraîné (Phase 3)

Slideflow: https://github.com/slideflow/slideflow
References:
- Dolezal et al. (2024): "Slideflow: Deep Learning for Digital Histopathology"
  https://bmcbioinformatics.biomedcentral.com/articles/10.1186/s12859-024-05758-x
"""

import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np

if TYPE_CHECKING:
    import slideflow as sf

from core.exceptions import (
    FeatureExtractionError,
    HeatmapGenerationError,
    MLModelNotLoadedError,
    ModelLoadError,
    PredictionError,
)
from core.interfaces import FeatureExtractionResult, HeatmapResult, PredictionResult

logger = logging.getLogger(__name__)


# ============================================================================
# KNOWN FEATURE EXTRACTORS
# ============================================================================

KNOWN_EXTRACTORS = {
    # Core slideflow (Apache-2.0) - inclus dans pip install slideflow
    "resnet50_imagenet": {"dim": 2048, "tile_px": 224, "package": "slideflow"},
    "virchow": {"dim": 2560, "tile_px": 224, "package": "slideflow"},
    # slideflow-gpl (GPL-3.0) - pip install slideflow-gpl
    "ctranspath": {"dim": 768, "tile_px": 224, "package": "slideflow-gpl"},
    "retccl": {"dim": 2048, "tile_px": 224, "package": "slideflow-gpl"},
    # slideflow-noncommercial (CC BY-NC 4.0) - pip install slideflow-noncommercial
    "uni": {"dim": 1024, "tile_px": 224, "package": "slideflow-noncommercial"},
    "phikon": {"dim": 768, "tile_px": 224, "package": "slideflow-noncommercial"},
    "gigapath": {"dim": 1536, "tile_px": 256, "package": "slideflow-noncommercial"},
    "plip": {"dim": 512, "tile_px": 224, "package": "slideflow-noncommercial"},
    "histossl": {"dim": 2048, "tile_px": 224, "package": "slideflow-noncommercial"},
    # Direct HuggingFace (no slideflow plugin needed) - loaded via transformers
    "phikon-v2": {
        "dim": 1024,
        "tile_px": 224,
        "package": "transformers",
        "hf_id": "owkin/phikon-v2",
    },
}

# Extractors loaded directly via transformers (bypass slideflow's sf.build_feature_extractor)
CUSTOM_EXTRACTORS = {"phikon-v2"}


def _resolve_ml_backend(requested: str) -> str:
    """Resolve ML_BACKEND=auto to the best available backend."""
    if requested != "auto":
        return requested

    # Try openvino first (best Intel optimization), then onnx, then pytorch
    try:
        import openvino

        if _find_onnx_model():
            return "openvino"
    except ImportError:
        pass

    try:
        import onnxruntime

        if _find_onnx_model():
            return "onnx"
    except ImportError:
        pass

    return "pytorch"


def _find_onnx_model() -> Optional[Path]:
    """Locate the exported ONNX model file."""
    env_path = os.getenv("ML_ONNX_MODEL", "")
    candidates = [
        Path(env_path) if env_path else Path("/dev/null"),
        Path(__file__).parent.parent.parent.parent / "ml_models" / "phikon-v2.quant.onnx",
        Path(__file__).parent.parent.parent.parent / "ml_models" / "phikon-v2.onnx",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


class _PhikonExtractor:
    """
    Wrapper Phikon-v2 compatible with Slideflow's extractor API.

    Supports multiple inference backends via ML_BACKEND env var:
    - pytorch:  Original PyTorch (transformers AutoModel)
    - onnx:     ONNX Runtime (requires exported .onnx model)
    - openvino: OpenVINO Runtime (requires exported .onnx model)
    - auto:     Best available (openvino > onnx > pytorch)

    Paper: Filiot et al. (2024) "Phikon-v2"
    HuggingFace: owkin/phikon-v2
    """

    # ImageNet/DINOv2 normalization constants
    MEAN = [0.485, 0.456, 0.406]
    STD = [0.229, 0.224, 0.225]

    def __init__(self, device="cpu"):
        requested_backend = os.getenv("ML_BACKEND", "auto")
        self._inference_backend = _resolve_ml_backend(requested_backend)

        # Slideflow-compatible attributes
        self.num_features = 1024
        self.num_classes = 0
        self.num_uncertainty = 0
        self.backend = "torch"
        self._device = device
        self.tag = "phikon-v2"
        self.include_preds = False
        self.img_format = "numpy"
        self.wsi_normalizer = None
        self.preprocess_kwargs = {}

        # Backend-specific model references
        self._pt_model = None
        self._onnx_session = None
        self._ov_infer = None
        self._ov_output_key = None

        if self._inference_backend == "openvino":
            self._load_openvino()
        elif self._inference_backend == "onnx":
            self._load_onnx()
        else:
            self._load_pytorch()

        # Cache normalization arrays for onnx/openvino (numpy)
        self._np_mean = np.array(self.MEAN, dtype=np.float32).reshape(1, 3, 1, 1)
        self._np_std = np.array(self.STD, dtype=np.float32).reshape(1, 3, 1, 1)

        logger.info(
            f"Phikon-v2 loaded (1024-dim, backend: {self._inference_backend}, " f"device: {device})"
        )

    def _load_pytorch(self):
        import torch
        from transformers import AutoModel

        logger.info("Loading Phikon-v2 via PyTorch...")
        self._pt_model = AutoModel.from_pretrained("owkin/phikon-v2")
        self._pt_model.eval()
        if self._device == "cuda":
            self._pt_model = self._pt_model.cuda()

        # Cache torch normalization tensors
        self._torch_mean = torch.tensor(self.MEAN).view(1, 3, 1, 1)
        self._torch_std = torch.tensor(self.STD).view(1, 3, 1, 1)

    def _load_onnx(self):
        import onnxruntime as ort

        onnx_path = _find_onnx_model()
        if not onnx_path:
            logger.warning("ONNX model not found, falling back to PyTorch")
            self._inference_backend = "pytorch"
            self._load_pytorch()
            return

        logger.info(f"Loading Phikon-v2 via ONNX Runtime: {onnx_path}")
        self._onnx_session = ort.InferenceSession(
            str(onnx_path),
            providers=["CPUExecutionProvider"],
        )

    def _load_openvino(self):
        import openvino as ov

        onnx_path = _find_onnx_model()
        if not onnx_path:
            logger.warning("ONNX model not found, falling back to PyTorch")
            self._inference_backend = "pytorch"
            self._load_pytorch()
            return

        logger.info(f"Loading Phikon-v2 via OpenVINO: {onnx_path}")
        core = ov.Core()
        compiled = core.compile_model(str(onnx_path), "CPU")
        self._ov_infer = compiled.create_infer_request()
        self._ov_output_key = compiled.output(0)

    @property
    def device(self):
        return self._device

    def is_torch(self):
        return True

    def is_tensorflow(self):
        return False

    def _preprocess_numpy(self, tensor) -> np.ndarray:
        """Convert torch uint8 tensor (B,3,H,W) to normalized float32 numpy."""
        import torch

        arr = tensor.cpu().numpy() if isinstance(tensor, torch.Tensor) else np.asarray(tensor)
        arr = arr.astype(np.float32) / 255.0
        return (arr - self._np_mean) / self._np_std

    def _infer_pytorch(self, images_tensor):
        """Run inference via PyTorch."""
        import torch

        images = images_tensor.float() / 255.0
        mean = self._torch_mean.to(images.device)
        std = self._torch_std.to(images.device)
        images = (images - mean) / std

        with torch.no_grad():
            outputs = self._pt_model(pixel_values=images)
            return outputs.last_hidden_state[:, 0, :]

    def _infer_onnx(self, images_tensor):
        """Run inference via ONNX Runtime."""
        import torch

        np_input = self._preprocess_numpy(images_tensor)
        result = self._onnx_session.run(None, {"pixel_values": np_input})
        features = result[0][:, 0, :]
        return torch.tensor(features, device=images_tensor.device)

    def _infer_openvino(self, images_tensor):
        """Run inference via OpenVINO."""
        import torch

        np_input = self._preprocess_numpy(images_tensor)
        self._ov_infer.infer({"pixel_values": np_input})
        result = self._ov_infer.get_output_tensor(0).data
        features = result[:, 0, :]
        return torch.tensor(features.copy(), device=images_tensor.device)

    def __call__(self, obj, **kwargs):
        import slideflow as sf

        if isinstance(obj, sf.WSI):
            from slideflow.model.extractors._slide import features_from_slide

            return features_from_slide(self, obj, **kwargs)

        if self._inference_backend == "openvino":
            return self._infer_openvino(obj)
        elif self._inference_backend == "onnx":
            return self._infer_onnx(obj)
        else:
            return self._infer_pytorch(obj)


def _patch_slideflow_dicom_support():
    """Add DICOM (.dcm) to Slideflow's supported formats.

    Slideflow's format whitelist predates OpenSlide 4.0 DICOM support.
    We patch both the global list and the vips backend list so that
    Slideflow delegates .dcm files to libvips/OpenSlide as usual.
    """
    try:
        import slideflow.util

        for ext in ("dcm", "dicom"):
            if ext not in slideflow.util.SUPPORTED_FORMATS:
                slideflow.util.SUPPORTED_FORMATS.append(ext)
        from slideflow.slide.backends import vips as _vips_backend

        for ext in ("dcm", "dicom"):
            if ext not in _vips_backend.SUPPORTED_BACKEND_FORMATS:
                _vips_backend.SUPPORTED_BACKEND_FORMATS.append(ext)
    except Exception:
        pass


class SlideflowProvider:
    """
    ML Provider basé sur Slideflow - mode progressif.

    Modes:
    - "extractor": Feature extractors pré-entraînés (Phase 1-2)
    - "classifier": Modèle de classification entraîné (Phase 3)

    Le mode est déterminé par model_config["mode"] ou auto-détecté:
    - Si model_path est un nom d'extracteur connu → mode extractor
    - Si model_path est un chemin fichier → mode classifier
    - Si model_path commence par "extractor://" → mode extractor

    Usage Phase 1-2 (Feature Extraction):
        >>> provider = SlideflowProvider()
        >>> provider.load_model("extractor://ctranspath", {
        ...     "model_id": "ctranspath_features",
        ...     "mode": "extractor"
        ... })
        >>> features = provider.extract_features("slide.mrxs")

    Usage Phase 3 (Classification):
        >>> provider = SlideflowProvider()
        >>> provider.load_model("models/gleason_v1.pt", {
        ...     "model_id": "gleason_grading_v1",
        ...     "mode": "classifier",
        ...     "classes": ["gleason_3", "gleason_4", "gleason_5"]
        ... })
        >>> result = provider.predict("slide.mrxs")
    """

    def __init__(self, device: str = "auto"):
        self.device = self._detect_device(device)
        self.model = None
        self.extractor = None
        self.model_config: Dict = {}
        self.model_loaded = False
        self.mode = "extractor"  # "extractor" or "classifier"

        self._slideflow_available = self._check_slideflow()

        if not self._slideflow_available:
            logger.warning("Slideflow not installed. Install with: pip install slideflow[torch]")
        else:
            logger.info(
                f"SlideflowProvider initialized (device: {self.device}, "
                f"slideflow v{self.sf.__version__})"
            )

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def _check_slideflow(self) -> bool:
        try:
            import slideflow as sf

            self.sf = sf
            _patch_slideflow_dicom_support()
            logger.debug(f"Slideflow version: {sf.__version__}")
            return True
        except ImportError:
            logger.debug("Slideflow not installed")
            return False

    def _detect_device(self, device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch

            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"GPU detected: {gpu_name}")
                return "cuda"
        except ImportError:
            pass
        logger.info("Using CPU (no GPU detected)")
        return "cpu"

    # ========================================================================
    # WSI HELPERS
    # ========================================================================

    def _estimate_tiles(self, slide_path: str, target_mag: float, tile_size: int = 224) -> int:
        """
        Estimate tile count at a given magnification without opening a full WSI.

        Uses OpenSlide to read dimensions and MPP, then calculates the grid.
        Returns -1 if MPP is unavailable.
        """
        try:
            import openslide

            slide = openslide.open_slide(slide_path)
            w, h = slide.dimensions
            mpp = slide.properties.get("openslide.mpp-x")
            slide.close()

            mpp_val = 0.5 if not mpp else float(mpp)

            # Unreliable MPP — assume ~20x native (mpp=0.5)
            if mpp_val <= 0 or mpp_val > 10:
                mpp_val = 0.5
                logger.debug(
                    f"Unreliable MPP for {Path(slide_path).name}, "
                    f"assuming mpp={mpp_val} for tile estimation"
                )

            native_mag = 10.0 / mpp_val
            downsample = native_mag / target_mag
            extract_px = downsample * tile_size

            if extract_px <= 0:
                return -1

            return int((w / extract_px) * (h / extract_px))

        except Exception as e:
            logger.debug(f"Tile estimation failed: {e}")
            return -1

    def _select_magnification(self, slide_path: str, tile_size: int = 224) -> list:
        """
        Select magnification adaptively based on estimated tile count.

        Reads ML_MAX_TILES (default 500) and ML_ADAPTIVE_STRIDE (default true).
        Iterates from highest to lowest magnification, returning the first
        where estimated tiles <= max_tiles.
        """
        adaptive = os.getenv("ML_ADAPTIVE_STRIDE", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        if not adaptive:
            return ["10x", "20x", "5x", "40x"]

        max_tiles = int(os.getenv("ML_MAX_TILES", "500"))
        candidates = [
            ("10x", 10.0),
            ("5x", 5.0),
            ("2.5x", 2.5),
            ("1.25x", 1.25),
        ]

        best_mag = candidates[-1][0]
        best_tiles = float("inf")

        for mag_str, mag_val in candidates:
            estimated = self._estimate_tiles(slide_path, mag_val, tile_size)
            if estimated < 0:
                # No MPP — fall back to original behavior
                logger.debug("No MPP available, using default magnification order")
                return ["10x", "20x", "5x", "40x"]
            if estimated <= max_tiles:
                logger.info(f"Adaptive mag: {mag_str} (~{estimated} tiles, max={max_tiles})")
                return [mag_str]
            if estimated < best_tiles:
                best_tiles = estimated
                best_mag = mag_str

        logger.info(
            f"Adaptive mag: {best_mag} (~{int(best_tiles)} tiles, max={max_tiles}) "
            f"— all exceed limit, using lowest"
        )
        return [best_mag]

    def _open_wsi(self, slide_path: str, tile_size: int = 224) -> "sf.WSI":  # noqa: PLR0915
        """
        Open a WSI with automatic magnification detection.

        Tries 10x first (good coverage/resolution tradeoff), then falls back
        to the closest available magnification if 10x is not available.
        """
        preferred_mags = self._select_magnification(slide_path, tile_size)

        # Try to import slideflow's typed MPP exception (may not exist in all versions)
        try:
            from slideflow.errors import SlideMissingMPPError
        except ImportError:
            SlideMissingMPPError = None  # noqa: N806

        last_error = None
        for mag in preferred_mags:
            try:
                wsi = self.sf.WSI(slide_path, tile_px=tile_size, tile_um=mag)
                num_tiles = getattr(wsi, "estimated_num_tiles", "?")
                logger.info(
                    f"Opened WSI at {mag} (~{num_tiles} tiles): " f"{Path(slide_path).name}"
                )
                return wsi
            except Exception as e:
                last_error = e
                logger.debug(f"Failed to open WSI at {mag}: {e}")
                continue

        # Last resort: force MPP and try adaptive magnification
        default_mpp = 0.5  # ~20x, safe default for histology
        slide_name = Path(slide_path).name

        try:
            import openslide

            slide = openslide.open_slide(slide_path)
            props = slide.properties
            mpp = props.get("openslide.mpp-x")

            # Fallback: vendor-specific MPP keys
            if not mpp:
                mpp = props.get("aperio.MPP")
            if not mpp:
                # Hamamatsu: derive MPP from objective lens magnification
                source_lens = props.get("hamamatsu.SourceLens")
                if source_lens:
                    try:
                        lens_mag = float(source_lens)
                        if lens_mag > 0:
                            # Standard relation: 10/mpp ~ magnification
                            mpp = str(10.0 / lens_mag)
                    except (ValueError, ZeroDivisionError):
                        pass
            if not mpp:
                # TIFF: XResolution in pixels per cm → convert to microns per pixel
                x_res = props.get("tiff.XResolution")
                res_unit = props.get("tiff.ResolutionUnit")
                if x_res:
                    try:
                        x_res_val = float(x_res)
                        if x_res_val > 0:
                            if res_unit in {"centimeter", "3"}:
                                mpp = str(10000.0 / x_res_val)
                            elif res_unit in {"inch", "2"}:
                                mpp = str(25400.0 / x_res_val)
                    except (ValueError, ZeroDivisionError):
                        pass

            slide.close()
            if mpp:
                mpp_val = float(mpp)
                if 0.1 <= mpp_val <= 5.0:
                    approx_mag = round(10.0 / mpp_val)
                    mag_str = f"{approx_mag}x"
                    logger.info(f"Using calculated magnification {mag_str} (mpp={mpp_val})")
                    return self.sf.WSI(slide_path, tile_px=tile_size, tile_um=mag_str)
        except Exception:  # nosec B110
            pass

        # Force MPP — try adaptive mags first, then fixed tile_um fallback
        logger.warning(
            f"Bad/missing MPP for {slide_name}, forcing mpp={default_mpp} "
            f"with adaptive magnification"
        )
        for mag in preferred_mags:
            try:
                wsi = self.sf.WSI(slide_path, tile_px=tile_size, tile_um=mag, mpp=default_mpp)
                num_tiles = getattr(wsi, "estimated_num_tiles", "?")
                logger.info(
                    f"Opened WSI at {mag} (~{num_tiles} tiles, forced mpp): " f"{slide_name}"
                )
                return wsi
            except Exception:
                continue

        # Ultimate fallback: fixed tile_um
        try:
            return self.sf.WSI(slide_path, tile_px=tile_size, tile_um=256, mpp=default_mpp)
        except Exception as e:
            raise HeatmapGenerationError(
                f"Cannot open slide '{slide_name}' for ML analysis: {e}",
                slide_path=slide_path,
                prediction_class="",
                method="open_wsi",
                provider="slideflow",
                details={"reason": "missing_mpp", "slide": slide_name},
            )

    # ========================================================================
    # MODEL MANAGEMENT
    # ========================================================================

    def load_model(self, model_path: str, model_config: Dict) -> None:
        """
        Charge modèle ou feature extractor.

        Détection automatique du mode:
        - "extractor://ctranspath" → feature extractor CTransPath
        - "extractor://resnet50_imagenet" → ResNet50 ImageNet
        - "models/trained_model.pt" → classification model (Phase 3)

        Args:
            model_path: Chemin ou identifiant
                - "extractor://<name>" pour feature extractors
                - Chemin fichier pour modèles entraînés
            model_config: Configuration
                {
                    "model_id": str,
                    "mode": "extractor" | "classifier",  # auto-détecté si absent
                    "classes": [...],          # pour classifier
                    "tile_size": 224,
                    "batch_size": 32,
                    "num_mc_samples": 10,      # Monte Carlo pour classifier
                }
        """
        if not self._slideflow_available:
            raise ModelLoadError(
                "Slideflow not installed. Install: pip install slideflow[torch]",
                model_path=model_path,
                provider="slideflow",
            )

        try:
            # Determine mode
            explicit_mode = model_config.get("mode", "")
            extractor_name = self._parse_extractor_name(model_path)

            if explicit_mode == "extractor" or extractor_name:
                self._load_extractor(extractor_name or model_path, model_config)
            elif explicit_mode == "classifier" or Path(model_path).exists():
                self._load_classifier(model_path, model_config)
            # Default: try extractor first
            elif model_path.lower() in KNOWN_EXTRACTORS:
                self._load_extractor(model_path.lower(), model_config)
            else:
                self._load_classifier(model_path, model_config)

        except ModelLoadError:
            raise
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise ModelLoadError(
                f"Failed to load: {e!s}",
                model_path=model_path,
                model_id=model_config.get("model_id", ""),
                provider="slideflow",
                details={"error": str(e)},
            )

    def _parse_extractor_name(self, model_path: str) -> Optional[str]:
        """Parse extractor name from path like 'extractor://ctranspath'."""
        if model_path.startswith("extractor://"):
            return model_path.replace("extractor://", "").strip().lower()
        if model_path.lower() in KNOWN_EXTRACTORS:
            return model_path.lower()
        return None

    def _load_extractor(self, extractor_name: str, model_config: Dict) -> None:
        """
        Charge un feature extractor pré-entraîné.

        Les poids sont téléchargés automatiquement depuis Hugging Face
        lors de la première utilisation.

        Supports:
        - Slideflow built-in extractors (via sf.build_feature_extractor)
        - Custom extractors loaded directly via transformers (phikon-v2, etc.)
        """
        if extractor_name not in KNOWN_EXTRACTORS:
            available = ", ".join(sorted(KNOWN_EXTRACTORS.keys()))
            raise ModelLoadError(
                f"Unknown extractor '{extractor_name}'. Available: {available}",
                model_path=f"extractor://{extractor_name}",
                provider="slideflow",
            )

        info = KNOWN_EXTRACTORS[extractor_name]
        logger.info(
            f"Loading feature extractor: {extractor_name} "
            f"(dim={info['dim']}, tile_px={info['tile_px']}, "
            f"package={info['package']})"
        )

        if extractor_name in CUSTOM_EXTRACTORS:
            # Custom extractor loaded via transformers (bypass slideflow)
            self.extractor = _PhikonExtractor(device=self.device)
        else:
            try:
                self.extractor = self.sf.build_feature_extractor(
                    extractor_name,
                    tile_px=info["tile_px"],
                    device=self.device,
                )
            except TypeError:
                # Fallback: some extractors don't accept device param
                self.extractor = self.sf.build_feature_extractor(
                    extractor_name, tile_px=info["tile_px"]
                )
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower() or "import" in error_msg.lower():
                    raise ModelLoadError(
                        f"Extractor '{extractor_name}' requires package: {info['package']}. "
                        f"Install with: pip install {info['package']}",
                        model_path=f"extractor://{extractor_name}",
                        provider="slideflow",
                        details={"required_package": info["package"]},
                    )
                raise

        self.mode = "extractor"
        self.model_config = {
            "model_id": model_config.get("model_id", f"{extractor_name}_features"),
            "extractor_name": extractor_name,
            "embedding_dim": info["dim"],
            "tile_size": info["tile_px"],
            "mode": "extractor",
            **{k: v for k, v in model_config.items() if k not in ("mode",)},
        }
        self.model_loaded = True

        logger.info(
            f"Feature extractor loaded: {extractor_name} "
            f"({info['dim']}-dim, device: {self.device})"
        )

    def _load_classifier(self, model_path: str, model_config: Dict) -> None:
        """
        Charge un modèle de classification entraîné (Phase 3).

        Supports:
        - Local files (.pt, .h5, .zip)
        - MLflow URIs (models:/model_name/version)
        - Hugging Face Hub (hf://namespace/model)
        """
        logger.info(f"Loading classification model: {model_path}")

        if model_path.startswith("models:/"):
            model = self._load_from_mlflow(model_path)
        elif model_path.startswith("hf://"):
            model = self._load_from_huggingface(model_path)
        else:
            path = Path(model_path)
            if not path.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            model = self.sf.model.load(str(path))

        if self.device == "cuda" and hasattr(model, "cuda"):
            model = model.cuda()

        self.model = model
        self.mode = "classifier"
        self.model_config = {
            "mode": "classifier",
            "tile_size": model_config.get("tile_size", 224),
            **model_config,
        }
        self.model_loaded = True

        logger.info(
            f"Classification model loaded: {model_config.get('model_id', 'unknown')} "
            f"(device: {self.device})"
        )

    def _load_from_mlflow(self, model_uri: str):
        """Charge modèle depuis MLflow Model Registry."""
        try:
            import mlflow

            model_path = mlflow.artifacts.download_artifacts(model_uri)
            return self.sf.model.load(model_path)
        except ImportError:
            raise ModelLoadError(
                "MLflow not installed. Install: pip install mlflow",
                model_path=model_uri,
                provider="slideflow",
            )

    def _load_from_huggingface(self, model_uri: str):
        """Charge modèle depuis Hugging Face Hub."""
        try:
            from huggingface_hub import hf_hub_download

            namespace, model_name = model_uri.replace("hf://", "").split("/", 1)
            model_path = hf_hub_download(  # nosec B615
                repo_id=f"{namespace}/{model_name}", filename="model.pt"
            )
            return self.sf.model.load(model_path)
        except ImportError:
            raise ModelLoadError(
                "huggingface_hub not installed. Install: pip install huggingface_hub",
                model_path=model_uri,
                provider="slideflow",
            )

    def unload_model(self) -> None:
        """Décharge modèle/extractor de la mémoire."""
        if self.model is not None:
            del self.model
            self.model = None

        if self.extractor is not None:
            del self.extractor
            self.extractor = None

        self.model_loaded = False

        if self.device == "cuda":
            try:
                import torch

                torch.cuda.empty_cache()
            except ImportError:
                pass

        logger.info(f"Model unloaded (was mode: {self.mode})")

    # ========================================================================
    # PREDICT
    # ========================================================================

    def predict(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Prédiction sur slide.

        Mode extractor (Phase 1-2):
            Analyse basée sur features extraites. Classifie tissue/background
            en utilisant les statistiques des embeddings. Pas de vrai modèle ML
            mais utilise les features d'un foundation model pré-entraîné.

        Mode classifier (Phase 3):
            Vraie classification ML avec uncertainty quantification
            (Monte Carlo Dropout).
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        if self.mode == "extractor":
            return self._predict_from_features(slide_path, region)
        else:
            return self._predict_from_classifier(slide_path, region)

    def _predict_from_features(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Prédiction basée sur feature extraction (Phase 1-2).

        Process:
        1. Extraire embeddings via foundation model
        2. Calculer statistiques des features (norms, variance)
        3. Classifier tissue/background via heuristique sur feature norms

        Note:
            Cette méthode ne remplace PAS un modèle entraîné (Phase 3).
            Elle fournit une analyse de base en attendant l'entraînement.
        """
        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "unknown")
        start_time = time.time()

        try:
            tile_size = self.model_config.get("tile_size", 224)
            wsi = self._open_wsi(slide_path, tile_size)

            # Region filtering: mask tiles outside viewport
            if region and hasattr(wsi, "coord") and len(wsi.coord) > 0:
                x, y, w, h = region
                in_region = (
                    (wsi.coord[:, 0] >= x)
                    & (wsi.coord[:, 0] < x + w)
                    & (wsi.coord[:, 1] >= y)
                    & (wsi.coord[:, 1] < y + h)
                )
                for i in range(len(wsi.coord)):
                    if not in_region[i]:
                        gx, gy = int(wsi.coord[i, 2]), int(wsi.coord[i, 3])
                        if 0 <= gx < wsi.grid.shape[0] and 0 <= gy < wsi.grid.shape[1]:
                            wsi.grid[gx, gy] = 0
                active = int(wsi.grid.sum())
                logger.info(f"Region filter: ~{active} tiles in viewport")

            # Extract features using foundation model
            features = self.extractor(wsi)

            # features shape: (num_tiles, embedding_dim) or (h, w, dim)
            if features.ndim == 3:
                _h, _w, d = features.shape
                features = features.reshape(-1, d)

            # Feature-based analysis - cast to float32 (GPU features may be float16)
            features = features.astype(np.float32) if features.dtype != np.float32 else features
            feature_norms = np.linalg.norm(features, axis=1)
            mean_norm = float(np.mean(feature_norms))
            std_norm = float(np.std(feature_norms))

            # Simple tissue/background classification based on feature activity
            # Higher feature norms = more "interesting" regions
            classes = self.model_config.get("classes", ["tissue", "background"])
            tissue_ratio = float(np.mean(feature_norms > np.median(feature_norms)))

            if tissue_ratio > 0.3:
                pred_class = classes[0] if classes else "tissue"
                confidence = min(0.95, 0.5 + tissue_ratio * 0.4)
            else:
                pred_class = classes[-1] if len(classes) > 1 else "background"
                confidence = min(0.95, 0.5 + (1 - tissue_ratio) * 0.4)

            probabilities = {}
            for cls in classes:
                if cls == pred_class:
                    probabilities[cls] = confidence
                else:
                    probabilities[cls] = (1 - confidence) / max(1, len(classes) - 1)

            execution_time_ms = (time.time() - start_time) * 1000

            result = PredictionResult(
                prediction_class=pred_class,
                confidence=confidence,
                probabilities=probabilities,
                uncertainty=1.0 - confidence,
                execution_time_ms=execution_time_ms,
                model_id=model_id,
                slide_id=slide_id,
                metadata={
                    "provider": "slideflow",
                    "mode": "extractor",
                    "extractor": self.model_config.get("extractor_name", ""),
                    "device": self.device,
                    "num_tiles": features.shape[0],
                    "embedding_dim": features.shape[1],
                    "mean_feature_norm": mean_norm,
                    "std_feature_norm": std_norm,
                    "region": region,
                    "note": "Feature-based analysis. Train a classifier (Phase 3) for real ML predictions.",
                },
            )

            logger.info(
                f"[EXTRACTOR] Prediction: {pred_class} (conf: {confidence:.2%}, "
                f"tiles: {features.shape[0]}, time: {execution_time_ms:.0f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"Feature-based prediction failed: {e}", exc_info=True)
            raise PredictionError(
                f"Feature-based prediction failed: {e!s}",
                slide_path=slide_path,
                slide_id=slide_id,
                model_id=model_id,
                region=region,
                provider="slideflow",
                details={"mode": "extractor", "error": str(e)},
            )

    def _predict_from_classifier(
        self, slide_path: str, region: Optional[Tuple[int, int, int, int]] = None
    ) -> PredictionResult:
        """
        Vraie classification ML avec Monte Carlo Dropout (Phase 3).

        Process:
        1. Load WSI et tiling
        2. Multiple forward passes avec dropout (MC)
        3. Aggregation + uncertainty quantification
        """
        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "unknown")
        start_time = time.time()

        try:
            tile_size = self.model_config.get("tile_size", 224)
            wsi = self.sf.WSI(slide_path, tile_px=tile_size)

            if region:
                x, y, w, h = region
                tiles = wsi.build_generator(region=(x, y, w, h))
            else:
                tiles = wsi.build_generator()

            # Monte Carlo Dropout
            num_mc_samples = self.model_config.get("num_mc_samples", 10)
            predictions_mc = []

            for _ in range(num_mc_samples):
                pred = self.model.predict(tiles, training=True)
                predictions_mc.append(pred)

            predictions_mc = np.array(predictions_mc)
            mean_pred = predictions_mc.mean(axis=0)
            uncertainty = float(predictions_mc.var(axis=0).mean())

            classes = self.model_config.get("classes", [])
            pred_class_idx = np.argmax(mean_pred)
            pred_class = classes[pred_class_idx] if classes else f"class_{pred_class_idx}"
            confidence = float(mean_pred[pred_class_idx])

            if classes:
                probabilities = {cls: float(mean_pred[i]) for i, cls in enumerate(classes)}
            else:
                probabilities = {f"class_{i}": float(p) for i, p in enumerate(mean_pred)}

            execution_time_ms = (time.time() - start_time) * 1000

            result = PredictionResult(
                prediction_class=pred_class,
                confidence=confidence,
                probabilities=probabilities,
                uncertainty=uncertainty,
                execution_time_ms=execution_time_ms,
                model_id=model_id,
                slide_id=slide_id,
                metadata={
                    "provider": "slideflow",
                    "mode": "classifier",
                    "device": self.device,
                    "num_mc_samples": num_mc_samples,
                    "region": region,
                },
            )

            logger.info(
                f"[CLASSIFIER] Prediction: {pred_class} (conf: {confidence:.2%}, "
                f"unc: {uncertainty:.3f}, time: {execution_time_ms:.0f}ms)"
            )

            return result

        except Exception as e:
            logger.error(f"Classification failed: {e}", exc_info=True)
            raise PredictionError(
                f"Classification failed: {e!s}",
                slide_path=slide_path,
                slide_id=slide_id,
                model_id=model_id,
                region=region,
                provider="slideflow",
                details={"mode": "classifier", "error": str(e)},
            )

    # ========================================================================
    # FEATURE EXTRACTION
    # ========================================================================

    def extract_features(
        self, slide_path: str, tile_size: int = 224, overlap: int = 0
    ) -> FeatureExtractionResult:
        """
        Extraction de features (embeddings).

        Mode extractor: Utilise le foundation model directement.
        Mode classifier: Utilise le backbone du modèle (sans classification head).
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        slide_id = Path(slide_path).stem
        model_id = self.model_config.get("model_id", "unknown")

        try:
            logger.info(f"Extracting features: {slide_id} (mode: {self.mode})")

            tile_px = self.model_config.get("tile_size", tile_size)
            wsi = self._open_wsi(slide_path, tile_px)

            if self.mode == "extractor":
                # Feature extractor mode - direct extraction
                raw_features = self.extractor(wsi)

                if raw_features.ndim == 3:
                    h, w, d = raw_features.shape
                    embeddings = raw_features.reshape(-1, d)
                    # Generate grid coordinates
                    coords = []
                    for yi in range(h):
                        for xi in range(w):
                            coords.append((xi * tile_px, yi * tile_px))
                    coordinates = coords
                else:
                    embeddings = raw_features
                    coordinates = [(i * tile_px, 0) for i in range(len(embeddings))]

            else:
                # Classifier mode - use backbone
                feature_extractor = self.model.get_feature_extractor()
                embeddings_list = []
                coordinates = []

                for tile, (x, y) in wsi.build_generator(return_coords=True):
                    feats = feature_extractor(tile)
                    if hasattr(feats, "cpu"):
                        feats = feats.cpu().numpy()
                    elif hasattr(feats, "numpy"):
                        feats = feats.numpy()
                    embeddings_list.append(feats)
                    coordinates.append((int(x), int(y)))

                embeddings = np.vstack(embeddings_list)

            # Ensure float32
            embeddings = embeddings.astype(np.float32)

            result = FeatureExtractionResult(
                embeddings=embeddings,
                coordinates=coordinates,
                slide_id=slide_id,
                model_id=model_id,
                tile_size=tile_px,
                metadata={
                    "provider": "slideflow",
                    "mode": self.mode,
                    "device": self.device,
                    "extractor": self.model_config.get("extractor_name", ""),
                    "overlap": overlap,
                },
            )

            logger.info(
                f"Extracted {result.num_patches} patches, "
                f"{result.embedding_dim}-dim features (mode: {self.mode})"
            )

            return result

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}", exc_info=True)
            raise FeatureExtractionError(
                f"Feature extraction failed: {e!s}",
                slide_path=slide_path,
                tile_size=tile_size,
                provider="slideflow",
                details={"mode": self.mode, "error": str(e)},
            )

    # ========================================================================
    # HEATMAP
    # ========================================================================

    def generate_heatmap(
        self, slide_path: str, prediction_class: str, resolution_level: int = 2
    ) -> HeatmapResult:
        """
        Génère heatmap d'explainability.

        Mode extractor: Attention map basée sur feature norms.
            Les régions avec des activations fortes sont mises en évidence.
        Mode classifier: Grad-CAM (gradient-based class activation).
        """
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        if self.mode == "extractor":
            return self._heatmap_from_features(slide_path, prediction_class, resolution_level)
        else:
            return self._heatmap_from_gradcam(slide_path, prediction_class, resolution_level)

    def _heatmap_from_features(  # noqa: PLR0915
        self, slide_path: str, prediction_class: str, resolution_level: int
    ) -> HeatmapResult:
        """
        Heatmap basée sur feature norms (Phase 1-2).

        Les feature norms du foundation model servent de proxy pour
        l'attention: les régions avec des features plus "actives"
        sont plus susceptibles de contenir du tissu intéressant.
        """
        slide_id = Path(slide_path).stem

        try:
            logger.info(f"[EXTRACTOR] Generating attention heatmap: {slide_id}")

            tile_size = self.model_config.get("tile_size", 224)
            wsi = self._open_wsi(slide_path, tile_size)

            raw_features = self.extractor(wsi)

            if raw_features.ndim == 3:
                # Shape (h, w, dim) → compute norm per spatial position
                # float64 to prevent overflow when features have large magnitudes
                feature_norms = np.linalg.norm(raw_features.astype(np.float64), axis=2).astype(
                    np.float32
                )
            else:
                # Shape (n, dim) → need to reshape to 2D grid
                norms = np.linalg.norm(raw_features.astype(np.float64), axis=1).astype(np.float32)
                n = len(norms)

                # Try to use the WSI grid shape if available (Slideflow provides it)
                grid_shape = None
                if hasattr(wsi, "grid") and wsi.grid is not None:
                    try:
                        grid_shape = wsi.grid.shape[:2]  # (rows, cols)
                        if grid_shape[0] * grid_shape[1] >= n:
                            logger.debug(f"Using WSI grid shape: {grid_shape}")
                        else:
                            grid_shape = None
                    except (AttributeError, IndexError):
                        grid_shape = None

                if grid_shape is None:
                    # Calculate aspect-ratio-aware grid from slide dimensions
                    slide_dims = wsi.dimensions if hasattr(wsi, "dimensions") else None
                    if slide_dims and slide_dims[0] > 0 and slide_dims[1] > 0:
                        aspect = slide_dims[0] / slide_dims[1]  # width / height
                        grid_h = max(1, int(np.ceil(np.sqrt(n / aspect))))
                        grid_w = max(1, int(np.ceil(n / grid_h)))
                    else:
                        grid_w = int(np.ceil(np.sqrt(n)))
                        grid_h = grid_w
                    grid_shape = (grid_h, grid_w)

                padded = np.zeros(grid_shape[0] * grid_shape[1])
                padded[:n] = norms
                feature_norms = padded.reshape(grid_shape[0], grid_shape[1])

            # Sanitize any residual NaN/inf from extreme magnitudes
            feature_norms = np.nan_to_num(feature_norms, nan=0.0, posinf=0.0, neginf=0.0).astype(
                np.float32
            )

            # Normalize [0, 1]
            heatmap = (feature_norms - feature_norms.min()) / (
                feature_norms.max() - feature_norms.min() + 1e-8
            )

            # Resize to target resolution
            target_size = max(64, 256 // (2**resolution_level))
            if heatmap.shape[0] != target_size or heatmap.shape[1] != target_size:
                try:
                    from scipy.ndimage import zoom

                    scale_h = target_size / heatmap.shape[0]
                    scale_w = target_size / heatmap.shape[1]
                    heatmap = zoom(heatmap, (scale_h, scale_w), order=1)
                except ImportError:
                    # Fallback: simple resize with numpy
                    from PIL import Image

                    img = Image.fromarray((heatmap * 255).astype(np.uint8))
                    img = img.resize((target_size, target_size), Image.BILINEAR)
                    heatmap = np.array(img).astype(np.float32) / 255.0

            # Re-normalize after resize and clamp to valid range
            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)
            heatmap = np.clip(heatmap, 0.0, 1.0).astype(np.float32)

            slide_dimensions = wsi.dimensions if hasattr(wsi, "dimensions") else (20000, 15000)

            result = HeatmapResult(
                heatmap=heatmap,
                slide_dimensions=slide_dimensions,
                resolution_level=resolution_level,
                slide_id=slide_id,
                method="feature_attention",
                target_class=prediction_class,
                metadata={
                    "provider": "slideflow",
                    "mode": "extractor",
                    "extractor": self.model_config.get("extractor_name", ""),
                    "note": "Attention proxy from feature norms. Use trained model (Phase 3) for Grad-CAM.",
                },
            )

            logger.info(f"[EXTRACTOR] Attention heatmap generated: {heatmap.shape}")
            return result

        except Exception as e:
            logger.error(f"Feature heatmap failed: {e}", exc_info=True)
            raise HeatmapGenerationError(
                f"Feature-based heatmap failed: {e!s}",
                slide_path=slide_path,
                prediction_class=prediction_class,
                method="feature_attention",
                provider="slideflow",
                details={"mode": "extractor", "error": str(e)},
            )

    def _heatmap_from_gradcam(
        self, slide_path: str, prediction_class: str, resolution_level: int
    ) -> HeatmapResult:
        """Grad-CAM heatmap avec modèle de classification (Phase 3)."""
        slide_id = Path(slide_path).stem

        try:
            logger.info(f"[CLASSIFIER] Generating Grad-CAM heatmap: {slide_id}")

            classes = self.model_config.get("classes", [])
            if classes and prediction_class not in classes:
                raise ValueError(f"Class '{prediction_class}' not in model classes: {classes}")

            wsi = self.sf.WSI(slide_path, tile_px=224)

            heatmap_generator = self.sf.grad.GradientHeatmap(
                model=self.model,
                target_class=prediction_class,
                method="gradcam",
            )

            heatmap = heatmap_generator.generate(
                wsi,
                level=resolution_level,
                batch_size=self.model_config.get("batch_size", 32),
            )

            heatmap = (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min() + 1e-8)

            result = HeatmapResult(
                heatmap=heatmap,
                slide_dimensions=wsi.dimensions,
                resolution_level=resolution_level,
                slide_id=slide_id,
                method="gradcam",
                target_class=prediction_class,
                metadata={
                    "provider": "slideflow",
                    "mode": "classifier",
                    "device": self.device,
                },
            )

            logger.info(f"[CLASSIFIER] Grad-CAM heatmap: {heatmap.shape}")
            return result

        except Exception as e:
            logger.error(f"Grad-CAM heatmap failed: {e}", exc_info=True)
            raise HeatmapGenerationError(
                f"Grad-CAM heatmap failed: {e!s}",
                slide_path=slide_path,
                prediction_class=prediction_class,
                method="gradcam",
                provider="slideflow",
                details={"mode": "classifier", "error": str(e)},
            )

    # ========================================================================
    # MODEL INFO
    # ========================================================================

    def get_model_info(self) -> Dict:
        """Retourne metadata du modèle/extractor chargé."""
        if not self.model_loaded:
            raise MLModelNotLoadedError(provider="slideflow")

        base_info = {
            "model_id": self.model_config.get("model_id", "unknown"),
            "model_name": self.model_config.get("model_name", ""),
            "version": self.model_config.get("version", ""),
            "task_type": self.model_config.get("task_type", "classification"),
            "classes": self.model_config.get("classes", []),
            "input_size": (
                self.model_config.get("tile_size", 224),
                self.model_config.get("tile_size", 224),
            ),
            "device": self.device,
            "provider": "slideflow",
            "mode": self.mode,
            "slideflow_version": self.sf.__version__ if self._slideflow_available else "N/A",
        }

        if self.mode == "extractor":
            extractor_name = self.model_config.get("extractor_name", "")
            base_info.update(
                {
                    "extractor_name": extractor_name,
                    "embedding_dim": self.model_config.get("embedding_dim", 0),
                    "task_type": "feature_extraction",
                    "reference_metrics": {},
                    "capabilities": [
                        "extract_features",
                        "predict (feature-based, approximate)",
                        "generate_heatmap (attention proxy)",
                    ],
                    "upgrade_path": "Train a classifier on extracted features for Phase 3",
                }
            )
        else:
            base_info.update(
                {
                    "reference_metrics": self.model_config.get("reference_metrics", {}),
                    "capabilities": [
                        "predict (ML classification)",
                        "extract_features",
                        "generate_heatmap (Grad-CAM)",
                    ],
                }
            )

        return base_info
