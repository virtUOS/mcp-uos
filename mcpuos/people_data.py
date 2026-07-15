"""
In-memory store for the pre-scraped Personensuche directory.

Used by the MCP server to answer uos_people_search locally, without hitting
the live website, using the JSON file produced by `mcp-uos-scrape-people`
(see scrape_people.py).
"""

import json
import os
import signal

from fastmcp.utilities.logging import get_logger

from mcpuos.models import PersonDetails
from mcpuos.scrape_people import DEFAULT_DATA_PATH

logger = get_logger(__name__)


class PeopleDataStore:
    """Holds the people directory loaded from a scrape_people.py JSON file."""

    def __init__(self, path: str | None = None):
        if path is None:
            path = os.getenv("UOS_MCP_PEOPLE_DATA_PATH", DEFAULT_DATA_PATH)
        self.path = path
        self._people: list[PersonDetails] = self._read(path)

    @staticmethod
    def _read(path: str) -> list[PersonDetails]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [PersonDetails(**p) for p in data["people"]]

    def reload(self) -> bool:
        """
        Reload the JSON file from disk. On failure, keeps serving the
        last-known-good in-memory data and logs the error; never raises.

        Returns:
            True if the reload succeeded, False otherwise.
        """
        try:
            people = self._read(self.path)
        except Exception as exc:
            logger.error(
                "people_data: reload of %s failed (%s); keeping %d previously loaded records",
                self.path, exc, len(self._people),
            )
            return False
        self._people = people
        logger.info("people_data: reloaded %d people from %s", len(self._people), self.path)
        return True

    def search(self, query: str) -> list[PersonDetails]:
        """Case-insensitive substring match against `name`."""
        q = query.lower()
        return [p for p in self._people if q in p.name.lower()]

    def __len__(self) -> int:
        return len(self._people)


def install_reload_handler(store: PeopleDataStore):
    """
    Register a SIGHUP handler that reloads `store`. Returns the handler
    function (mainly so it can be exercised directly in unit tests without
    needing a real signal delivery).
    """
    def _handler(signum, frame):
        store.reload()

    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, _handler)
    return _handler
