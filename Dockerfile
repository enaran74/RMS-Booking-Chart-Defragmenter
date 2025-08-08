# BookingChartDefragmenter Dockerfile
# For Debian 12 Linux Server Deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    unzip \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r defrag && useradd -r -g defrag -s /bin/bash -m defrag

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /var/log/bookingchart-defragmenter && \
    mkdir -p /app/output && \
    chown -R defrag:defrag /app && \
    chown -R defrag:defrag /var/log/bookingchart-defragmenter

# Copy and set up entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER defrag

# Set volume for logs and output
VOLUME ["/var/log/bookingchart-defragmenter", "/app/output"]

# Expose port (if needed for health checks)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import os; exit(0 if os.path.exists('/var/log/bookingchart-defragmenter/defrag_analyzer.log') else 1)" || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
