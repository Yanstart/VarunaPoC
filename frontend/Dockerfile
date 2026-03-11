# VarunaPoC Frontend Dockerfile (Phase 1)
# Multi-stage build: Build with Node, Serve with Nginx

# ============================================
# Stage 1: Build Vite application
# ============================================
FROM node:20-alpine AS builder

LABEL stage="builder"

WORKDIR /app

# Copy package files for reproducible installs
COPY package.json package-lock.json ./

# Install exact dependency versions from lockfile
RUN npm ci

# Copy source code
COPY . .

# Build argument for API URL (can be overridden at build time)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}

# Build Vite application for production
# Limit Node heap to avoid OOM in memory-constrained CI environments
RUN NODE_OPTIONS="--max-old-space-size=512" npm run build

# ============================================
# Stage 2: Serve with Nginx
# ============================================
FROM nginx:alpine

LABEL maintainer="VarunaPoC Team"
LABEL description="VarunaPoC Frontend - Vite + OpenSeadragon viewer"
LABEL version="0.1.0"

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Install curl for healthcheck
RUN apk add --no-cache curl

# Expose HTTP port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=60s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Start Nginx (daemon off for Docker)
CMD ["nginx", "-g", "daemon off;"]
