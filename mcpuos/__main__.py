"""
Main entry point for running the MCP server.

This module enables running the MCP server via:
    python -m mcpuos
"""

from mcpuos.mcp_server import mcp

if __name__ == "__main__":
    mcp.run()
