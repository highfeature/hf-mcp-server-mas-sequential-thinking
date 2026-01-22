# Dockerfile for hf-mcp-sequential-thinking
# Build all
# docker build --target build .
# Build just base 
# docker build --target base build .

# Stage 1: Build dependencies
# Based on Python 3.10 (required by pyproject.toml)
FROM python:3.13-slim AS base

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
#COPY pyproject.toml uv.lock .env /app/
#COPY src/ /app/src/
COPY pyproject.toml uv.lock .env ./
COPY src/ ./src/

# Install uv (ultra-fast pip alternative)
RUN pip install --no-cache-dir uv

# Install project dependencies using uv
RUN uv sync --no-group dev --python 3.13



# # Stage 2: Runtime (minimal image)
# FROM python:3.13-slim AS runtime

# WORKDIR /app
# # COPY --from=base /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.11/site-packages
# COPY --from=base /app/.venv/ /app/.venv/
# COPY --from=base /usr/local/bin/uv /usr/local/bin/
# # Copy project files
# COPY pyproject.toml .env src ./
# # COPY .env .env
# # COPY src/ ./src/

# # Expose the port the app runs on
# EXPOSE 8090

# Run the application
CMD ["uv", "run", "--no-dev", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--reload", "--env-file", ".env", "--port=8090", "--log-level", "debug"]
