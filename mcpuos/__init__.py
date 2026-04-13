"""
mcpuos - A package for interacting with the University of Osnabrück website.

This package provides functionality for logging in, searching, and fetching
content from the university's website, as well as running as an MCP server
for LLM integration.
"""

from mcpuos.website import UOSWebsiteClient
from mcpuos.mcp_server import mcp, uos_search, uos_fetch

__all__ = ['UOSWebsiteClient', 'mcp', 'uos_search', 'uos_fetch']
