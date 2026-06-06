#!/usr/bin/env python3
"""Integration tests for the UOS MCP server.

Launches the server as a subprocess via stdio transport and exercises all
four tools end-to-end. A single MCP connection and event loop is shared
across the entire test session.

Run with:  pytest tests/test_mcp.py
       or: pytest tests/test_mcp.py -s   (to see per-test detail output)
Requires:  UOS_MCP_USERNAME and UOS_MCP_PASSWORD (env vars or .env file)
"""

import asyncio
import sys

import pytest
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

load_dotenv()

EXPECTED_TOOLS = {"uos_search", "uos_fetch", "uos_people_search", "uos_person_details"}


class _MCP:
    """Thin synchronous wrapper around an async fastmcp Client."""

    def __init__(self, client: Client, loop: asyncio.AbstractEventLoop) -> None:
        self._client = client
        self._loop = loop

    def run(self, coro):
        return self._loop.run_until_complete(coro)

    def list_tools(self):
        return self.run(self._client.list_tools())

    def call_tool(self, name, arguments=None):
        return self.run(self._client.call_tool(name, arguments))


@pytest.fixture(scope="session")
def requires_auth():
    import os

    if not os.getenv("UOS_MCP_USERNAME") or not os.getenv("UOS_MCP_PASSWORD"):
        pytest.skip("UOS_MCP_USERNAME and UOS_MCP_PASSWORD env vars required")


@pytest.fixture(scope="session")
def mcp():
    loop = asyncio.new_event_loop()
    transport = StdioTransport(command=sys.executable, args=["-m", "mcpuos"])
    client = Client(transport)

    loop.run_until_complete(client.__aenter__())
    yield _MCP(client, loop)
    loop.run_until_complete(client.__aexit__(None, None, None))
    loop.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_tools_are_listed(mcp):
    tools = mcp.list_tools()
    names = {t.name for t in tools}
    print(f"\n  Tools: {', '.join(sorted(names))}")
    assert names == EXPECTED_TOOLS


def test_uos_search(mcp, requires_auth):
    result = mcp.call_tool("uos_search", {"search_term": "Dienstreise"})
    data = result.structured_content
    print(f"\n  {data['total_count']} results for 'Dienstreise'")
    print(f"  First: {data['results'][0]['title']}")
    assert data["total_count"] > 0
    first = data["results"][0]
    assert first["title"]
    assert first["url"].startswith("https://")


def test_uos_fetch(mcp, requires_auth):
    url = "https://www.uni-osnabrueck.de/virtuos/vorstand"
    result = mcp.call_tool("uos_fetch", {"url": url})
    text = result.content[0].text
    print(f"\n  Fetched {url!r}: {len(text)} chars")
    assert len(text) > 200


def test_uos_people_search(mcp):
    result = mcp.call_tool("uos_people_search", {"query": "Kiesow"})
    data = result.structured_content
    print(f"\n  {data['total_count']} people matching 'Kiesow'")
    for r in data["results"]:
        print(f"  - {r['name']}")
    assert data["total_count"] > 0
    first = data["results"][0]
    assert "Kiesow" in first["name"]
    assert first["details_url"].startswith("https://")


def test_uos_person_details(mcp):
    search = mcp.call_tool("uos_people_search", {"query": "Kiesow"})
    url = search.structured_content["results"][0]["details_url"]

    result = mcp.call_tool("uos_person_details", {"url": url})
    details = result.structured_content
    print(f"\n  Name:    {details.get('name')}")
    print(f"  Dept:    {details.get('department')}")
    print(f"  Email:   {details.get('email')}")
    print(f"  Phone:   {details.get('phone')}")
    assert "Kiesow" in details["name"]
