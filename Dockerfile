# ==============================================================================
# RMS Booking Chart Defragmenter - Production Docker Image
# ==============================================================================
# Multi-stage build for optimized deployment with both CLI and Web interface
# Supports multiple architectures: linux/amd64, linux/arm64

# Stage 1: Build environment
FROM python:3.11-slim-bookworm as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create wheel directory
WORKDIR /wheels

# Copy requirements and build wheels to avoid recompilation
COPY requirements.txt ./
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels \
    -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim-bookworm

LABEL maintainer="DHP Operations Systems"
LABEL description="RMS Booking Chart Defragmenter - Complete System"
LABEL version="2.0.0"

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client for database connectivity
    postgresql-client \
    # Network utilities
    curl \
    # Process management
    procps \
    # Cron for scheduled tasks
    cron \
    # System monitoring
    htop \
    # Text editor for debugging
    nano \
    # Timezone data
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create application directories
RUN mkdir -p /app/logs /app/output /app/backups /app/config \
    && mkdir -p /app/app/original /app/app/web /app/app/shared \
    && mkdir -p /app/scripts \
    && chown -R appuser:appuser /app

# Copy wheels from builder stage and install Python dependencies
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --find-links /wheels \
    pandas numpy openpyxl python-dateutil pytz \
    fastapi uvicorn sqlalchemy psycopg2-binary alembic \
    PyJWT cryptography passlib bcrypt \
    requests httpx aiohttp \
    pydantic pydantic-settings python-dotenv \
    jinja2 python-multipart aiofiles \
    xlsxwriter python-docx click \
    websockets schedule croniter \
    pytest pytest-asyncio pytest-cov structlog \
    email-validator \
    && rm -rf /wheels

# Copy application files
COPY start.py defrag_analyzer.py rms_client.py excel_generator.py \
     email_sender.py holiday_client.py school_holiday_client.py \
     utils.py school_holidays.json ./app/original/

COPY web_app/main.py ./app/web/
COPY web_app/app/ ./app/web/app/

COPY env.example ./app/shared/env.example

# Copy scripts
COPY scripts/entrypoint.sh scripts/health_check.sh scripts/cron_runner.py scripts/crontab ./scripts/
RUN chmod +x ./scripts/entrypoint.sh ./scripts/health_check.sh

# Set up cron
COPY scripts/crontab /etc/cron.d/defrag-cron
RUN chmod 0644 /etc/cron.d/defrag-cron && crontab /etc/cron.d/defrag-cron

# Set proper ownership
RUN chown -R appuser:appuser /app

# Switch to application user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD ./scripts/health_check.sh

# Set entrypoint to handle arguments properly
ENTRYPOINT ["./scripts/entrypoint.sh"]