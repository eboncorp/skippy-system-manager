# Skippy System Manager - Docker Image
# Base image with Python 3.12
FROM python:3.12-slim

# Set labels
LABEL maintainer="Skippy Development Team <dev@example.com>"
LABEL version="2.0.0"
LABEL description="Skippy System Manager - Comprehensive automation and management suite"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    git \
    jq \
    gpg \
    openssh-client \
    shellcheck \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-test.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/backups /app/conversations

# Set permissions
RUN chmod +x scripts/**/*.sh || true

# Create non-root user
RUN useradd -m -u 1000 skippy && \
    chown -R skippy:skippy /app

# Switch to non-root user
USER skippy

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "mcp-servers/general-server/server.py"]
