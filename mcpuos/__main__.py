"""
Main entry point for running the MCP server.

This module enables running the MCP server via:
    python -m mcpuos
"""

import os

from mcpuos.mcp_server import mcp

def main():
    port = os.getenv("UOS_MCP_SERVER_PORT")
    host = os.getenv("UOS_MCP_SERVER_HOST", "127.0.0.1")
    if port:
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()

if __name__ == "__main__":
    main()
