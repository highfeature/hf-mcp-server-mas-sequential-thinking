# Dockerfile for hf-mcp-sequential-thinking
# Based on Python 3.10 (required by pyproject.toml)
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=. \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs

# Copy project files
COPY pyproject.toml ./
COPY .env .env
COPY src/ ./src/

# Install uv (ultra-fast pip alternative)
RUN pip install --no-cache-dir uv

# Install project dependencies using uv
RUN uv sync

# Expose the port the app runs on
EXPOSE 8090

# Run the application
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--reload", "--env-file", ".env", "--port=8090", "--log-level", "debug"]
