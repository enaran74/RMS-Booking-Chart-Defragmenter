# ==============================================================================
# RMS Booking Chart Defragmenter - Docker Image
# ==============================================================================
# This Dockerfile creates a container running both:
# 1. Original CLI defragmentation analyzer with cron scheduling
# 2. FastAPI web interface for move management
# 3. PostgreSQL client for database connectivity

FROM python:3.11-slim-bookworm

# Metadata
LABEL maintainer="DHP Operations Systems"
LABEL description="RMS Booking Chart Defragmenter with CLI and Web Interface"
LABEL version="2.0.0"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    # Build tools
    gcc \
    g++ \
    # PostgreSQL client
    postgresql-client \
    # Network tools
    curl \
    wget \
    # Process management
    supervisor \
    # Cron scheduling
    cron \
    # System utilities
    procps \
    htop \
    nano \
    # Timezone data
    tzdata \
    # Clean up
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application user and directories
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /app/logs /app/output /app/backups /app/config \
    && mkdir -p /app/app/original /app/app/web /app/app/shared \
    && mkdir -p /app/scripts \
    && chown -R appuser:appuser /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --only-binary=all pandas>=1.5.0 numpy>=1.21.0 \
    && pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt

# Copy original application files
COPY start.py defrag_analyzer.py rms_client.py excel_generator.py \
     email_sender.py holiday_client.py school_holiday_client.py \
     utils.py school_holidays.json ./app/original/

# Copy web application files
COPY web_app/main.py ./app/web/
COPY web_app/app/ ./app/web/app/

# Copy shared configuration and utilities
COPY env.example ./app/shared/env.example

# Copy management scripts
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/*.sh

# Create supervisor configuration
RUN mkdir -p /etc/supervisor/conf.d

# Create entrypoint script
COPY scripts/entrypoint.sh ./
RUN chmod +x ./entrypoint.sh

# Create cron configuration
COPY scripts/crontab /etc/cron.d/defrag-cron
RUN chmod 0644 /etc/cron.d/defrag-cron && crontab /etc/cron.d/defrag-cron

# Create health check script
COPY scripts/health_check.sh ./
RUN chmod +x ./health_check.sh

# Set proper ownership
RUN chown -R appuser:appuser /app

# Switch to application user
USER appuser

# Expose ports
EXPOSE 8000

# Volume mounts for persistent data
VOLUME ["/app/logs", "/app/output", "/app/backups", "/app/config"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ./health_check.sh

# Set entrypoint to handle arguments properly
ENTRYPOINT ["./entrypoint.sh"]
