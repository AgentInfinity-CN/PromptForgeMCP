# PromptForge MCP Server Dockerfile
# Multi-stage build for Python MCP service

# Build stage
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy pyproject.toml and uv.lock for dependency installation
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv .venv
RUN uv pip install --no-cache-dir -r pyproject.toml

# Copy source code
COPY promptforge_mcp/ ./promptforge_mcp/
COPY test_mcp_client.py ./
COPY env.template ./

# Runtime stage
FROM python:3.11-slim AS runtime

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r mcp && useradd -r -g mcp mcp

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy virtual environment and application from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/promptforge_mcp /app/promptforge_mcp
COPY --from=builder /app/pyproject.toml /app/
COPY --from=builder /app/test_mcp_client.py /app/
COPY --from=builder /app/env.template /app/

# Create directory for database and ensure permissions
RUN mkdir -p /data && chown -R mcp:mcp /data /app

# Activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV DATABASE_PATH=/data/promptforge.db
ENV MCP_SERVER_PORT=9099
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 9099

# Switch to non-root user
USER mcp

# Health check - Simple process check since MCP uses non-HTTP protocols
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pgrep -f "promptforge_mcp.main" || exit 1

# Run the application
CMD ["python", "-m", "promptforge_mcp.main", "--http", "--host", "0.0.0.0", "--port", "9099"]