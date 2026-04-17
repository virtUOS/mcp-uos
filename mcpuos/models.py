"""
Pydantic models for structured data exchange in the UOS MCP Server.

This module defines the data models used for search results and other
structured responses, providing type safety and automatic JSON Schema
generation for FastMCP tools.
"""

from typing import Annotated
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """
    Represents a single search result from the UOS website.

    Attributes:
        title: The title of the search result.
        url: The full URL to the result page (can be passed to uos_fetch).
        breadcrumbs: List of breadcrumb items describing the result's location.
        teaser: A short preview text for the result.
    """
    title: Annotated[str, Field(description="The title of the search result")]
    url: Annotated[str, Field(description="The full URL to the result page")]
    breadcrumbs: Annotated[list[str], Field(description="List of breadcrumb items")]
    teaser: Annotated[str | None, Field(description="A short preview text")]


class SearchResults(BaseModel):
    """
    Container for a collection of search results with metadata.

    Attributes:
        results: List of individual search results.
        query: The search query that produced these results.
        total_count: Total number of results found.
    """
    results: Annotated[list[SearchResult], Field(description="List of search results")]
    query: Annotated[str, Field(description="The search query that was performed")] = ""
    total_count: Annotated[int, Field(description="Total number of results found")] = 0
