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


class PersonSearchResult(BaseModel):
    """Represents a single result from a people search (used internally while scraping)."""
    name: Annotated[str, Field(description="Full name with academic title, e.g. 'Kiesow, Lars, M. Sc.'")]
    details_url: Annotated[str, Field(description="URL of the person's full details page")]


class PersonDetails(BaseModel):
    """Full contact details for a single person."""
    name: Annotated[str, Field(description="Full name with academic title, e.g. 'Dr. rer. pol. Andreas Knaden'")]
    department: Annotated[str | None, Field(description="Department or organisational unit")] = None
    address: Annotated[str | None, Field(description="Street address and city, e.g. 'Heger-Tor-Wall 12, 49069 Osnabrück'")] = None
    room: Annotated[str | None, Field(description="Room number, e.g. '15/109'")] = None
    phone: Annotated[str | None, Field(description="Phone number, e.g. '+49 541 969-6500'")] = None
    fax: Annotated[str | None, Field(description="Fax number")] = None
    email: Annotated[str | None, Field(description="Email address")] = None
    website: Annotated[str | None, Field(description="Personal or group website URL")] = None
    source_url: Annotated[str | None, Field(description="URL of the page these details were retrieved from")] = None


class PersonDetailsResults(BaseModel):
    """Container for people search results with full contact details inline."""
    results: Annotated[list[PersonDetails], Field(description="List of matching people with full contact details")]
    query: Annotated[str, Field(description="The search query that was performed")] = ""
    total_count: Annotated[int, Field(description="Total number of results found")] = 0
