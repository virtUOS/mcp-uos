# Use Python 3.14 slim image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install the package (this also installs all dependencies from pyproject.toml)
RUN --mount=type=bind,source=mcpuos,target=/app/mcpuos \
    --mount=type=bind,source=pyproject.toml,target=/app/pyproject.toml \
    pip install --no-cache-dir .

# Set default environment variables for MCP server
ENV UOS_MCP_SERVER_PORT=8000 \
    UOS_MCP_SERVER_HOST=0.0.0.0

# Expose port for HTTP transport (optional)
EXPOSE 8000

# Set the default command to run the MCP server
CMD ["mcp-uos"]
