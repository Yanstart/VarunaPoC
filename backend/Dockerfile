# VarunaPoC Backend Dockerfile (Phase 1)
# Base: Python 3.11 slim with OpenSlide dependencies

FROM python:3.11-slim

LABEL maintainer="VarunaPoC Team"
LABEL description="VarunaPoC Backend - FastAPI + OpenSlide tile server"
LABEL version="1.7.0"

# Set working directory
WORKDIR /app

# Install system dependencies
# OpenSlide 4.0 C library is provided by openslide-bin pip wheel (no apt needed)
# Build tools: build-essential, python3-dev (needed for native Python extensions)
# Additional deps: curl (healthcheck), libvips (pyvips image processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    python3-dev \
    swig \
    libvips42t64 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
# Note: slideflow pulls smac->pyrfr which fails to compile with modern GCC.
# Install slideflow without deps first, then install requirements normally
# (pyrfr/smac are only used for hyperparameter tuning, not needed here).
# After requirements, install Slideflow's *minimal* runtime deps explicitly —
# previously they were missing, so `import slideflow` blew up with
# ModuleNotFoundError on pandas/torch and every ML endpoint returned 503.
# Using PyTorch CPU wheels (~600 MB) instead of the default CUDA build (~2 GB).
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir slideflow==3.0.2 --no-deps && \
    grep -v '^slideflow' requirements.txt | pip install --no-cache-dir -r /dev/stdin && \
    pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/cpu \
        pandas 'Pillow>=10' tqdm scikit-image scikit-learn opencv-python-headless \
        torch torchvision \
        matplotlib 'seaborn<0.14' umap-learn zarr tabulate tensorboard \
        triangle rasterio saliency fpdf2 pyopengl pyperclip

# Remove build dependencies to reduce image size
RUN apt-get purge -y --auto-remove \
    build-essential \
    python3-dev

# Prepare OpenSlide 4.0 for libvips: create .so.0 symlink
# libvips expects libopenslide.so.0 (3.x soname), but openslide-bin ships .so.1 (4.x)
# The symlink is created at build time (before switching to non-root user).
# LD_LIBRARY_PATH is set by config_openslide.py at startup via os.execv re-exec.
RUN OSBIN_DIR=$(python -c "from pathlib import Path; import openslide_bin; print(Path(openslide_bin.__file__).parent)") && \
    ln -sf libopenslide.so.1 "$OSBIN_DIR/libopenslide.so.0" && \
    echo "$OSBIN_DIR" > /tmp/openslide_bin_path && \
    echo "OpenSlide 4.0 symlink created in $OSBIN_DIR"

# Copy application code
COPY . .

# Set environment variable to indicate Docker environment
ENV DOCKER_CONTAINER=true

# Create non-root user for security
RUN useradd -m -u 1000 varuna && \
    chown -R varuna:varuna /app

USER varuna

# Expose FastAPI port
EXPOSE 8000

# Health check (uses curl installed earlier)
HEALTHCHECK --interval=30s --timeout=60s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start FastAPI server with Uvicorn
# --host 0.0.0.0: Listen on all interfaces (required for Docker)
# --port 8000: Standard backend port
# UVICORN_WORKERS: number of worker processes (default 1; recommended 2*CPU+1 for prod)
# LOG_LEVEL: uvicorn log level (default info; options: debug, info, warning, error, critical)
CMD uvicorn main:app --host 0.0.0.0 --port 8000 \
    --workers ${UVICORN_WORKERS:-1} \
    --log-level ${LOG_LEVEL:-info}
