#!/usr/bin/env python3
"""Integration tests for the UOS MCP server.

Launches the server as a subprocess via stdio transport and exercises all
three tools end-to-end, using a small fixture people-data JSON file so
uos_people_search needs no live network access. A single MCP connection and
event loop is shared across the entire test session.

Run with:  pytest tests/test_mcp.py
       or: pytest tests/test_mcp.py -s   (to see per-test detail output)
Requires:  UOS_MCP_USERNAME and UOS_MCP_PASSWORD (env vars or .env file)
           for the uos_search/uos_fetch tests.
"""

import asyncio
import json
import os
import sys

import pytest
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from mcpuos.models import PersonDetails

load_dotenv()

EXPECTED_TOOLS = {"uos_search", "uos_fetch", "uos_people_search"}


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
    skip_login = os.getenv("UOS_MCP_SKIP_LOGIN", "").lower() in ("1", "true", "yes")
    if not skip_login and (not os.getenv("UOS_MCP_USERNAME") or not os.getenv("UOS_MCP_PASSWORD")):
        pytest.skip("UOS_MCP_USERNAME and UOS_MCP_PASSWORD env vars required")


@pytest.fixture(scope="session")
def people_fixture_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("people-data") / "people.json"
    people = [
        PersonDetails(
            name="Kiesow, Lars, M. Sc.",
            department="virtUOS",
            email="lkiesow@uos.de",
        ).model_dump(),
        PersonDetails(name="Anna Schmidt", department="Physik").model_dump(),
    ]
    path.write_text(
        json.dumps({"scraped_at": "2026-01-01T00:00:00+00:00", "count": len(people), "people": people}),
        encoding="utf-8",
    )
    return path


@pytest.fixture(scope="session")
def mcp(people_fixture_path):
    loop = asyncio.new_event_loop()
    env = {**os.environ, "UOS_MCP_PEOPLE_DATA_PATH": str(people_fixture_path)}
    transport = StdioTransport(command=sys.executable, args=["-m", "mcpuos"], env=env)
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
    assert data["total_count"] == 1
    first = data["results"][0]
    assert "Kiesow" in first["name"]
    assert first["department"] == "virtUOS"
    assert first["email"] == "lkiesow@uos.de"
