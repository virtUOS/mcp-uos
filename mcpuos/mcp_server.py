"""
MCP Server for Osnabrück University website interactions.

This module provides an MCP server that exposes tools for searching and
fetching content from the Osnabrück University website.
"""

from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP

from mcpuos import UOSWebsiteClient
from mcpuos.models import SearchResults, PersonDetailsResults
from mcpuos.people_data import PeopleDataStore, install_reload_handler


# Create the FastMCP server instance
mcp = FastMCP(
    name="UOS MCP Server",
    instructions="""
    This server provides tools for interacting with the University of Osnabrück website.

    Use the uos_search tool to search for content on the university website.
    Use the uos_fetch tool to retrieve and convert page content to markdown.

    The server requires UOS_MCP_USERNAME and UOS_MCP_PASSWORD environment variables
    to be set for authentication with the university website.

    Set UOS_MCP_SKIP_LOGIN=true to skip authentication and access only public content.

    Use the uos_people_search tool to search for people employed at the university.
    It answers from a local pre-scraped snapshot (UOS_MCP_PEOPLE_DATA_PATH) and
    returns full contact details inline for every match; there is no separate
    "person details" tool.
    """,
)


# Initialize the UOSWebsiteClient
_client = UOSWebsiteClient()

_people_store = PeopleDataStore()
install_reload_handler(_people_store)


@mcp.tool(
    name="uos_search",
    description="Search the Osnabrück University (UOS) website for content.",
)
def uos_search(
    search_term: Annotated[str, Field(description="The search term to look for on the Osnabrück University website.")],
    results_per_page: Annotated[int, Field(description="Number of results to return per page. Valid values are 10, 25, or 50. Defaults to 50.", ge=1, le=50)] = 50,
) -> SearchResults:
    """
    Search the Osnabrück University website for content.

    Args:
        search_term: The search term to look for.
        results_per_page: Number of results to return per page (default: 50).

    Returns:
        A SearchResults object containing:
        - results: List of SearchResult objects with title, url, breadcrumbs, teaser
        - query: The search query that was performed
        - total_count: Total number of results found
    """
    return _client.search(search_term, results_per_page)


@mcp.tool(
    name="uos_fetch",
    description="Fetch page content from a URL and return it as markdown.",
)
def uos_fetch(
    url: Annotated[str, Field(description="The URL to fetch (can be relative or absolute).")],
) -> Annotated[str, Field(description="The main content of the page as a markdown string.")]:
    """
    Fetch page content from a URL and return it as markdown.

    Args:
        url: The URL to fetch (can be relative or absolute).

    Returns:
        The main content of the page as a markdown string.
    """
    return _client.fetch(url)


@mcp.tool(
    name="uos_people_search",
    description=(
        "Search for people employed at the Osnabrück University using a locally "
        "cached directory snapshot. Returns full contact details directly for "
        "every match."
    ),
)
def uos_people_search(
    query: Annotated[str, Field(description="Name or partial name to search for.")],
) -> PersonDetailsResults:
    """
    Search the locally cached people directory.

    Args:
        query: Name or partial name to search for.

    Returns:
        A PersonDetailsResults object containing:
        - results: List of PersonDetails objects with full contact details
        - query: The search query that was performed
        - total_count: Total number of people found
    """
    matches = _people_store.search(query)
    return PersonDetailsResults(results=matches, query=query, total_count=len(matches))
