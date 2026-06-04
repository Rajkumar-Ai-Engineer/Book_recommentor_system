# Docker Build & Deployment Guide

## Overview

This guide explains the optimized Dockerfile for the Book Recommendation System, build strategies, and deployment best practices.

---

## Dockerfile Architecture

### Multi-Stage Build Strategy

The Dockerfile uses a **two-stage build** approach to minimize the final image size:

#### Stage 1: Builder
```dockerfile
FROM python:3.12-slim as builder
```
- Installs build tools (gcc, g++, make)
- Compiles all Python dependencies into wheels
- Creates a virtual environment with all packages
- **Size**: ~850 MB (discarded after build)

**Why**: 
- Build tools are only needed to compile packages
- Wheels (compiled binaries) are reusable
- Significantly reduces final image size

#### Stage 2: Runtime
```dockerfile
FROM python:3.12-slim
```
- Starts fresh from minimal base image
- Copies only the compiled virtual environment from builder
- Copies application code
- Creates non-root user
- **Final Size**: ~480 MB uncompressed, ~150 MB compressed (in ECR)

**Why**:
- No build tools in final image
- Only runtime dependencies
- Minimal attack surface
- Faster container startup

---

## Image Specifications

### Base Image: `python:3.12-slim`

**Why This Image**:
- ✅ Official Python image (maintained by Docker)
- ✅ Debian-based, minimal (~160 MB)
- ✅ Slim variant excludes unneeded packages
- ✅ Python 3.12 is required by project (`pyproject.toml`)
- ✅ Security patches auto-applied

**Alternatives Considered**:
- `python:3.12` (full): 880 MB (100% larger)
- `python:3.12-alpine`: 50 MB smaller but no glibc (incompatible with some wheels)
- `ubuntu:24.04`: Would require manual Python installation

### Final Image Layers

```
Layer 1: Base OS (python:3.12-slim) - 160 MB
Layer 2: Runtime packages (curl, tzdata) - 10 MB
Layer 3: Virtual environment (/opt/venv) - 310 MB
Layer 4: Application code - 10 MB
Layer 5: User/permissions - <1 MB
────────────────────────────────
Total: ~490 MB uncompressed
Compressed (ECR): ~150 MB
```

---

## Build Commands

### Local Development Build

```bash
# Build image
docker build -t book-recommendation-system:dev .

# Run with MongoDB URI
docker run -it \
  -p 8000:8000 \
  -e MONGODB_URI="your-mongo-uri" \
  book-recommendation-system:dev

# Access at http://localhost:8000
```

### Production Build with Tags

```bash
# Build with specific version
docker build -t book-recommendation-system:1.0.0 .
docker build -t book-recommendation-system:latest .

# Tag for ECR
docker tag book-recommendation-system:1.0.0 \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/book-recommendation-system:1.0.0

docker tag book-recommendation-system:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/book-recommendation-system:latest

# Push to registry
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/book-recommendation-system:1.0.0
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/book-recommendation-system:latest
```

### Build with Custom Python Version (if needed)

```bash
# Build for Python 3.11 (requires Dockerfile modification)
# Change: FROM python:3.12-slim as builder → FROM python:3.11-slim as builder

docker build -t book-recommendation-system:py311 .
```

---

## Dockerfile Breakdown

### Stage 1: Builder

```dockerfile
FROM python:3.12-slim as builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
```

**Why `--no-install-recommends`**:
- Installs only essential packages
- Reduces image size (skip docs, man pages, etc.)
- Faster install, fewer vulnerabilities

**Why `rm -rf /var/lib/apt/lists/*`**:
- APT cache not needed in image
- Saves ~50 MB per layer
- Best practice for Docker images

**Build Tools Installed**:
- `gcc`: C compiler (needed for numpy, scipy)
- `g++`: C++ compiler (needed for sklearn)
- `make`: Build automation (needed for some packages)

```dockerfile
# Copy dependency files
COPY requirements.txt pyproject.toml uv.lock ./

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt
```

**Why Virtual Environment**:
- Isolates dependencies from system Python
- Easier to copy to next stage
- Clean separation of concerns

**Why `--no-cache-dir`**:
- pip cache not needed in image
- Saves disk space
- Faster builds after first run

---

### Stage 2: Runtime

```dockerfile
FROM python:3.12-slim
WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install minimal runtime packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*
```

**Non-Root User**:
- `appuser` runs with UID/GID 1000 (non-root)
- Limits damage if container is compromised
- Best practice for security
- **Verified**: Dockerfile uses `USER appuser` before `CMD`

**Runtime Packages**:
- `curl`: Health checks in Docker/ECS
- `tzdata`: Timezone support (if needed)

```dockerfile
# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

**Environment Variables**:
| Variable | Value | Purpose |
|----------|-------|---------|
| `PATH` | `/opt/venv/bin:$PATH` | Use virtual environment Python/pip |
| `PYTHONUNBUFFERED` | `1` | No stdout buffering (real-time logs) |
| `PYTHONDONTWRITEBYTECODE` | `1` | No .pyc files (saves space) |
| `PYTHONHASHSEED` | `random` | Prevents hash randomization attacks |
| `PIP_*` | Disabled | Prevents pip from caching |

```dockerfile
# Copy application code
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser templates ./templates
COPY --chown=appuser:appuser static ./static
COPY --chown=appuser:appuser main.py train.py ./

# Create directories with correct ownership
RUN mkdir -p /app/logs /app/Artifacts && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser
```

**Ownership Management**:
- `COPY --chown=appuser:appuser`: Sets ownership during copy (atomic)
- Directories created before `USER` switch (needs root)
- Application runs as unprivileged user

```dockerfile
# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start application
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--access-log"]
```

**Health Check**:
- `interval=30s`: Check every 30 seconds
- `timeout=5s`: Fail if response >5 seconds
- `start-period=10s`: Grace period before first check
- `retries=3`: Mark unhealthy after 3 failures

**Startup Command**:
- `uvicorn main:app`: Run FastAPI app from main.py
- `--host 0.0.0.0`: Listen on all interfaces (required for containers)
- `--port 8000`: Listen on 8000
- `--workers 4`: 4 worker processes (handles concurrency)
- `--access-log`: Log HTTP requests to stdout (for CloudWatch)

---

## .dockerignore Details

The `.dockerignore` file prevents unnecessary files from being copied into the image.

**Key Exclusions**:

```
# Development
.venv/              # Virtual environment (large, not needed)
.git/               # Git repo (for deployment, not app)
tests/              # Unit tests (not needed in prod)
Notebooks/          # Jupyter notebooks (not needed)
.pytest_cache/      # Test artifacts

# Configuration
.env                # Secrets (use Secrets Manager instead)
.github/            # CI/CD workflows (not needed in image)
Dockerfile          # Dockerfile not needed in build context
.dockerignore       # This file

# Documentation
README.md           # Docs not needed in image
*.md                # Markdown files

# Data
logs/               # Log files (build-time only)
data_schema/        # Data schemas (not needed)
```

**Benefits**:
- Faster `docker build` (smaller context)
- Smaller image size
- Security (no sensitive files)

---

## Local Testing

### 1. Build and Run Locally

```bash
# Build
docker build -t book-recommendation-system:test .

# Run (interactive)
docker run -it \
  -p 8000:8000 \
  -e MONGODB_URI="mongodb+srv://user:pass@cluster.mongodb.net/db" \
  -v $(pwd)/Artifacts:/app/Artifacts \
  book-recommendation-system:test

# In another terminal, test
curl http://localhost:8000/
curl -X GET "http://localhost:8000/suggestions?q=Harry"
curl -X POST "http://localhost:8000/recommend" -F "book_name=Harry Potter"
```

### 2. Container Health Check

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' <container-id>

# View health logs
docker inspect --format='{{json .State.Health.Log}}' <container-id> | jq
```

### 3. View Container Logs

```bash
# Real-time logs
docker logs -f <container-id>

# Last 100 lines
docker logs --tail 100 <container-id>

# With timestamps
docker logs -t <container-id>
```

### 4. Test Volume Mounts

```bash
# Create local Artifacts directory
mkdir -p ./Artifacts

# Run with volume mount
docker run -it \
  -p 8000:8000 \
  -v $(pwd)/Artifacts:/app/Artifacts:rw \
  -e MONGODB_URI="mongodb+srv://..." \
  book-recommendation-system:test

# Verify artifacts are accessible
ls -la ./Artifacts
```

---

## Container Resource Management

### Memory Limits

```bash
# Run with memory limit (for testing)
docker run \
  -m 2g \
  -p 8000:8000 \
  -e MONGODB_URI="mongodb+srv://..." \
  book-recommendation-system:test
```

### CPU Limits

```bash
# Run with CPU limit (1 vCPU)
docker run \
  --cpus="1.0" \
  -p 8000:8000 \
  -e MONGODB_URI="mongodb+srv://..." \
  book-recommendation-system:test
```

### Monitoring Resource Usage

```bash
# View real-time stats
docker stats <container-id>

# One-time snapshot
docker stats --no-stream <container-id>
```

---

## Image Security Scanning

### Local Security Scanning with Docker Scout

```bash
# Requires Docker Desktop with Scout enabled
docker scout cves book-recommendation-system:latest

# Generate vulnerability report
docker scout cves book-recommendation-system:latest --format sarif > vulnerabilities.sarif
```

### ECR Image Scanning

```bash
# ECR automatically scans images on push
aws ecr describe-image-scan-findings \
  --repository-name book-recommendation-system \
  --image-id imageTag=latest \
  --region us-east-1
```

---

## Build Optimization Tips

### 1. Layer Caching

Docker caches layers to speed up rebuilds. Order matters:

```dockerfile
# Good: Changes infrequently first
COPY requirements.txt .
RUN pip install -r requirements.txt

# Bad: Changes frequently first (invalidates cache)
COPY . .
RUN pip install -r requirements.txt
```

Current Dockerfile optimizes this by:
1. Copying only `requirements.txt` → cached
2. Installing dependencies → cached if requirements unchanged
3. Copying application code → rebuilt only if app changed

### 2. Parallel Multi-Stage Builds

```bash
# Build uses parallel stages automatically
# Builder stage and runtime collection happen separately
docker build -t image:tag --progress=plain .
```

### 3. BuildKit for Advanced Optimization

```bash
# Enable BuildKit (faster, more features)
DOCKER_BUILDKIT=1 docker build -t image:tag .

# Or set in Docker daemon config (~/.docker/config.json)
{
  "features": {
    "buildkit": true
  }
}
```

---

## Common Issues & Solutions

### Issue: Container exits immediately

**Cause**: Application crashes during startup

**Solution**:
```bash
# Check logs
docker logs <container-id>

# Check if MongoDB URI is set
docker run -e MONGODB_URI="mongodb+srv://..." ...

# Test locally with hardcoded connection
```

### Issue: "ModuleNotFoundError: No module named 'X'"

**Cause**: Dependency not in requirements.txt

**Solution**:
```bash
# Update requirements.txt
pip freeze > requirements.txt

# Rebuild Dockerfile
docker build -t image:tag . --no-cache
```

### Issue: Slow container startup

**Cause**: Uvicorn or model loading slow

**Solution**:
```bash
# Monitor startup
docker logs -f <container-id>

# Check if model file exists/is accessible
docker exec <container-id> ls -la /app/Artifacts/

# Increase health check start-period in Dockerfile
HEALTHCHECK --start-period=30s ...
```

### Issue: Out of memory (OOM)

**Cause**: Task memory insufficient for ML models

**Solution**:
```bash
# Test with higher memory locally
docker run -m 4g ...

# Increase ECS task memory in task definition
"memory": "4096"  # 4 GB
```

---

## Production Checklist

Before deploying to production:

- [ ] Build passes locally without errors
- [ ] Docker Scout/ECR scanning shows no critical vulnerabilities
- [ ] Health check endpoint responds correctly
- [ ] MongoDB connection string tested
- [ ] Image pushed to ECR with proper tags
- [ ] Task definition references correct image URI
- [ ] IAM roles have required permissions
- [ ] CloudWatch log group exists
- [ ] Load balancer health checks configured
- [ ] Auto-scaling policies set up
- [ ] Monitoring alarms configured

---

## Monitoring Image Size Over Time

```bash
# Track image size
docker images book-recommendation-system

# Output: Shows SIZE column (uncompressed)
REPOSITORY                  TAG         SIZE
book-recommendation-system  latest      489MB
book-recommendation-system  v1.0.0      489MB

# Check compressed size in ECR
aws ecr describe-images \
  --repository-name book-recommendation-system \
  --query 'imageDetails[].imageSizeBytes' \
  | jq '.[]/1024/1024' # Convert to MB
```

---

## Upgrading Dependencies

### Safe Dependency Updates

```bash
# Update requirements
pip install --upgrade pip
pip install -r requirements.txt --upgrade

# Rebuild Dockerfile
docker build -t book-recommendation-system:updated .

# Test locally
docker run -it -p 8000:8000 -e MONGODB_URI="..." book-recommendation-system:updated

# If tests pass, tag and push
docker tag book-recommendation-system:updated book-recommendation-system:v1.1.0
docker push <registry>/book-recommendation-system:v1.1.0
```

### Breaking Changes

If updating major versions:
1. Test thoroughly in staging
2. Use feature flags or env variables for backwards compatibility
3. Gradual rollout (canary deployment)

---

## References

- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Python Docker Images](https://hub.docker.com/_/python)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
