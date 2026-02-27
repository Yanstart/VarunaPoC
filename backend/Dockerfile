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
    libvips42t64 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

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
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start FastAPI server with Uvicorn
# --host 0.0.0.0: Listen on all interfaces (required for Docker)
# --port 8000: Standard backend port
# --workers 1: Single worker for Phase 1 (increase later if needed)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
