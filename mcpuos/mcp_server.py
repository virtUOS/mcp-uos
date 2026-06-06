"""
MCP Server for Osnabrück University website interactions.

This module provides an MCP server that exposes tools for searching and
fetching content from the Osnabrück University website.
"""

from typing import Annotated
from pydantic import Field

from fastmcp import FastMCP

from mcpuos import UOSWebsiteClient
from mcpuos.models import SearchResults, PersonSearchResults, PersonDetails


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
    Use the uos_person_details tool to retrieve full contact details for a person.
    """,
)


# Initialize the UOSWebsiteClient
_client = UOSWebsiteClient()


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
        "Search for people employed at the Osnabrück University. "
        "Returns a list of matches with names and detail URLs. "
        "Pass a details_url to uos_person_details to get full contact information."
    ),
)
def uos_people_search(
    query: Annotated[str, Field(description="Name or partial name to search for.")],
) -> PersonSearchResults:
    """
    Search for people employed at the Osnabrück University.

    Args:
        query: Name or partial name to search for.

    Returns:
        A PersonSearchResults object containing:
        - results: List of PersonSearchResult objects with name and details_url
        - query: The search query that was performed
        - total_count: Total number of people found
    """
    return _client.people_search(query)


@mcp.tool(
    name="uos_person_details",
    description=(
        "Fetch full contact details for a person at the Osnabrück University. "
        "Pass the details_url returned by uos_people_search."
    ),
)
def uos_person_details(
    url: Annotated[str, Field(
        description=(
            "The details_url from a uos_people_search result. "
            "Must start with https://www.uni-osnabrueck.de/kontakt/personensuche/personendetails"
        )
    )],
) -> PersonDetails:
    """
    Fetch full contact details for a person at the Osnabrück University.

    Args:
        url: The details_url from a uos_people_search result.

    Returns:
        A PersonDetails object with all available contact fields including
        name, department, address, room, phone, fax, email, and website.

    Raises:
        ValueError: If the URL does not point to the person details endpoint.
    """
    return _client.people_details(url)
