"""
MCP Server for University of Osnabrück website interactions.

This module provides an MCP server that exposes tools for searching and
fetching content from the University of Osnabrück website.
"""

from fastmcp import FastMCP

from mcpuos import UOSWebsiteClient


# Create the FastMCP server instance
mcp = FastMCP(
    name="UOS MCP Server",
    instructions="""
    This server provides tools for interacting with the University of Osnabrück website.
    
    Use the uos_search tool to search for content on the university website.
    Use the uos_fetch tool to retrieve and convert page content to markdown.
    
    The server requires UOS_MCP_USERNAME and UOS_MCP_PASSWORD environment variables
    to be set for authentication with the university website.
    """,
)


# Initialize the UOSWebsiteClient
_client = UOSWebsiteClient()


@mcp.tool(
    name="uos_search",
    description="Search the University of Osnabrück website for content.",
)
def uos_search(
    search_term: str,
    results_per_page: int = 50,
) -> list[dict]:
    """
    Search the University of Osnabrück website for content.

    Args:
        search_term: The search term to look for.
        results_per_page: Number of results to return per page (default: 50).

    Returns:
        A list of search results, each containing:
        - title: The result title
        - url: The result URL (can be passed to uos_fetch)
        - breadcrumbs: List of breadcrumb items
        - teaser: A short preview text
    """
    return _client.search(search_term, results_per_page)


@mcp.tool(
    name="uos_fetch",
    description="Fetch page content from a URL and return it as markdown.",
)
def uos_fetch(url: str) -> str:
    """
    Fetch page content from a URL and return it as markdown.

    Args:
        url: The URL to fetch (can be relative or absolute).

    Returns:
        The main content of the page as a markdown string.
    """
    return _client.fetch(url)
