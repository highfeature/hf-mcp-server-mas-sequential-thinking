# Generated by https://smithery.ai. See: https://smithery.ai/docs/config#dockerfile
FROM python:3.10-alpine

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY main.py ./
COPY README.md ./

# Upgrade pip and install hatchling build tool
RUN pip install --upgrade pip && \
    pip install hatchling

# Build and install the project
RUN pip install .

# Command to run the MCP server
CMD ["hf-mcp-server-mas-sequential-thinking"]
