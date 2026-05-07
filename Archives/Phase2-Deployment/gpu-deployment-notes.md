VarunaPoC - Deployment on GPU Host
====================================

Prerequisites:
  - Docker + Docker Compose
  - Python 3.11+
  - Node.js 20+
  - NVIDIA GPU with CUDA drivers
  - 16+ GB RAM recommended

Files not in git (must be copied from current VM):
  - backend/ml_models/phikon-v2.quant.onnx  (292 MB - ML model)
  - Slides/                                   (60 GB - test slide data)

Steps:
------

1. Clone
   git clone https://github.com/Yanstart/VarunaPoC.git
   cd VarunaPoC

2. Config backend
   cp backend/.env.example backend/.env

   Edit backend/.env and set:
     ML_ADAPTIVE_STRIDE=false       # GPU does not need tile limiting
     ML_MAX_TILES=                  # remove the limit (empty = unlimited)
     ML_EXTRACTOR=phikon-v2         # or resnet50_imagenet if no ONNX model
     AUTH_ENABLED=false             # for testing without Keycloak
     ML_TIMEOUT_SECONDS=120         # GPU is fast, no need for 600s

3. Copy ML model (292 MB)
   scp user@current-vm:/data/VarunaPoC/backend/ml_models/phikon-v2.quant.onnx \
       backend/ml_models/

4. Copy or symlink slides (60 GB)
   ln -s /path/to/your/slides Slides

5. Start services (PostgreSQL + Keycloak)
   docker compose -f docker-compose.dev.yml up -d

6. Backend setup
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install onnxruntime-gpu      # GPU acceleration for ONNX model
   # or: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   alembic upgrade heads
   uvicorn main:app --host 0.0.0.0 --port 8000

7. Frontend setup
   cd ../frontend
   npm ci
   npm run dev

8. Open browser
   http://localhost:5173

GPU-specific .env settings:
---------------------------
ML_ADAPTIVE_STRIDE=false    # CPU uses adaptive stride to limit tiles; GPU processes all
ML_MAX_TILES=               # empty = no limit (GPU can handle full resolution)
ML_TIMEOUT_SECONDS=120      # GPU inference is 10-50x faster than CPU

GPU detection:
  The slideflow provider auto-detects CUDA via torch.cuda.is_available().
  ONNX model uses onnxruntime-gpu (CUDAExecutionProvider) if installed.
  Check backend logs for: "Using GPU" or "Using CPU (no GPU detected)".

Performance expectations (vs CPU on current VM):
  - Heatmap generation: ~30s (vs 5-10 min on CPU)
  - Cell counting: ~5s (vs 60s on CPU)
  - Detection: ~10s (vs 10-30 min on CPU)
  - Feature extraction: ~2s per tile (vs 20s on CPU)

Troubleshooting:
  - "No GPU detected": install onnxruntime-gpu or torch with CUDA
  - "CUDA out of memory": reduce ML_MAX_TILES or use smaller batch size
  - ONNX model not found: ensure backend/ml_models/phikon-v2.quant.onnx exists
  - Slides not loading: verify SLIDES_REPOSITORY_PATH in .env points to Slides/
