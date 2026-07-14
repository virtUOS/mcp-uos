"""
Standalone script for scraping the full Personensuche directory.

Walks the alphabetical listing at /kontakt/personensuche (A-Z), fetches full
contact details for every person found, and writes the result to a JSON
file. Intended to be run on a schedule via an external cron/systemd timer:

    mcp-uos-scrape-people

This module has no dependency on the MCP server itself; it only reuses
UOSWebsiteClient's HTTP/parsing logic.
"""

import json
import os
import sys
import time

from datetime import datetime, timezone

from mcpuos.website import UOSWebsiteClient

DEFAULT_DATA_PATH = "./data/people.json"
DEFAULT_DELAY_SECONDS = 0.3


def _log(message):
    print(message, flush=True)


def scrape_all_people(client, delay):
    """
    Walk the A-Z listing, then fetch full details for every person found.

    Returns a list of dicts (PersonDetails.model_dump()); a failure on any
    single person's detail page is logged and skipped rather than aborting
    the whole run. Progress within each letter is logged after every
    person as "<letter>: i/N people details fetched" (i advances on a
    skipped/failed fetch too, so the counter always reaches N by the end
    of the letter; skipped people are additionally logged on their own
    line).
    """
    people = []

    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        stubs = client.list_people_by_letter(letter, delay=delay)
        total = len(stubs)
        width = len(str(total))
        _log(f"{letter}: {total} people found")

        for i, stub in enumerate(stubs, start=1):
            fetched = True
            try:
                details = client.people_details(stub.details_url)
            except Exception as exc:
                fetched = False
                _log(f"  skipped {stub.details_url}: {exc}")
            else:
                people.append(details.model_dump())

            _log(f"{letter}: {i:>{width}}/{total} people details fetched")

            if fetched and delay:
                time.sleep(delay)

    return people


def write_people_data(people, path):
    """Atomically write the scraped people list to a JSON file."""
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    data = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "count": len(people),
        "people": people,
    }

    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(tmp_path, path)


def main():
    path = os.getenv("UOS_MCP_PEOPLE_DATA_PATH", DEFAULT_DATA_PATH)
    delay = float(os.getenv("UOS_MCP_SCRAPE_DELAY_SECONDS", DEFAULT_DELAY_SECONDS))

    client = UOSWebsiteClient(skip_login=True)

    _log(f"Scraping Personensuche directory (delay={delay}s) ...")
    people = scrape_all_people(client, delay)

    write_people_data(people, path)
    _log(f"Wrote {len(people)} people to {path}")


if __name__ == "__main__":
    sys.exit(main())
