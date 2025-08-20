# Use Python 3.11 slim image based on stable Debian bookworm
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies - split into separate steps for better debugging
# Update package lists with retry logic
RUN apt-get update --fix-missing || (sleep 10 && apt-get update --fix-missing) || apt-get update

# Install packages with retry logic
RUN apt-get install -y --no-install-recommends \
        gcc \
        postgresql-client \
        curl \
    || (apt-get update && apt-get install -y --no-install-recommends gcc postgresql-client curl)

# Clean up package cache
RUN rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Install pandas and numpy first with pre-compiled wheels to avoid compilation issues
RUN pip install --no-cache-dir --only-binary=all pandas>=1.5.0 numpy>=1.21.0 || \
    pip install --no-cache-dir pandas>=1.5.0 numpy>=1.21.0

# Install remaining Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
