# Dockerfile for hf-mcp-sequential-thinking
# Build all
# docker build --target build .
# Build just base 
# docker build --target base build .

# Stage 1: Build dependencies
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
COPY pyproject.toml uv.lock .env ./
COPY src/ ./src/

# Install uv (ultra-fast pip alternative)
RUN pip install --no-cache-dir uv

# Install project dependencies using uv
RUN uv sync --no-group dev --python 3.13

# Stage 2: Runtime (minimal image)
FROM python:3.13-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=. \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# Install system dependencies (minimal for runtime)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs

# Copy only necessary files from build stage
COPY --from=base /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=base /app/pyproject.toml /app/uv.lock /app/.env /app/
COPY --from=base /app/src /app/src

# Install standalone uv binary in runtime stage
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8090

# Run the application
CMD ["uv", "run", "--no-dev", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--reload", "--env-file", ".env", "--port=8090", "--log-level", "debug"]
