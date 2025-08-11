# NexusController v2.0 - Production Container
# Multi-stage build for optimal size and security

# Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    nmap \
    openssh-client \
    curl \
    tar \
    openssl \
    ca-certificates \
    xvfb \
    x11vnc \
    fluxbox \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r nexus && useradd -r -g nexus -u 1000 nexus

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy application files
COPY --chown=nexus:nexus . .

# Create necessary directories
RUN mkdir -p /app/.nexus/{config,logs,keys,backups} && \
    chown -R nexus:nexus /app/.nexus && \
    chmod -R 700 /app/.nexus

# Create VNC directory for GUI access
RUN mkdir -p /tmp/.X11-unix && \
    chmod 1777 /tmp/.X11-unix && \
    chown nexus:nexus /tmp/.X11-unix

# Switch to non-root user
USER nexus

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    NEXUS_CONFIG_DIR=/app/.nexus \
    DISPLAY=:99

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import nexus_controller_v2; print('OK')" || exit 1

# Expose ports
EXPOSE 8080 5901

# Create startup script
COPY --chown=nexus:nexus docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Start command
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gui"]