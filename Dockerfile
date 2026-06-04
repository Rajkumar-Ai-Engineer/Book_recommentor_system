# Stage 1: Builder - compile dependencies and prepare environment
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies only in builder stage
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (for better layer caching)
COPY requirements.txt pyproject.toml uv.lock ./

# Create a virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies using pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - minimal production image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Create non-root user for security (principle of least privilege)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install only runtime dependencies (curl for health checks, timezone data)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy application code
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser templates ./templates
COPY --chown=appuser:appuser static ./static
COPY --chown=appuser:appuser main.py train.py ./

# Create directories for logs and artifacts with proper permissions
RUN mkdir -p /app/logs /app/Artifacts && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (FastAPI default)
EXPOSE 8000

# Health check configuration (every 30 seconds, 3 failures = unhealthy, timeout 5s)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start application with uvicorn
# - Host 0.0.0.0 allows external connections (required for ECS)
# - Production workers (4 = 2 x CPU cores for typical ECS task)
# - Disable reload in production (changes won't be detected in container anyway)
# - Access logs sent to stdout for CloudWatch
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--access-log"]
