"""Shared pytest configuration.

Importing mcpuos loads the people snapshot at import time, so pytest
collection would crash whenever ./data/people.json is absent (e.g. on CI or
a fresh checkout). conftest is imported before any test module, so pointing
UOS_MCP_PEOPLE_DATA_PATH at the committed fixture here keeps collection
working; setdefault preserves an explicitly configured path.
"""

import os

import pytest

PEOPLE_FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "people.json")

os.environ.setdefault("UOS_MCP_PEOPLE_DATA_PATH", PEOPLE_FIXTURE)


@pytest.fixture(scope="session")
def people_fixture_path():
    """Path to the committed people-directory snapshot used across tests."""
    return PEOPLE_FIXTURE
