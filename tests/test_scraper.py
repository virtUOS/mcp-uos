#!/usr/bin/env python3
"""Tests for the Personensuche directory scraper.

Run with: pytest tests/test_scraper.py
"""

import json

from mcpuos.models import PersonDetails, PersonSearchResult
from mcpuos.scrape_people import write_people_data
from mcpuos.website import UOSWebsiteClient


# ---------------------------------------------------------------------------
# list_people_by_letter — live integration test
# ---------------------------------------------------------------------------


def test_list_people_by_letter_paginates():
    client = UOSWebsiteClient(skip_login=True)

    # A rare initial letter keeps this test fast while still exercising
    # pagination (the "»" next-link) across at least one page boundary.
    results = client.list_people_by_letter("Q")

    assert len(results) > 0
    assert all(isinstance(r, PersonSearchResult) for r in results)
    assert all(r.name.upper().startswith("Q") for r in results)

    urls = [r.details_url for r in results]
    assert len(urls) == len(set(urls))
    assert all(url.startswith(UOSWebsiteClient.PEOPLE_DETAILS_PREFIX) for url in urls)


# ---------------------------------------------------------------------------
# write_people_data — atomic JSON write
# ---------------------------------------------------------------------------


def test_write_people_data_is_atomic(tmp_path):
    path = tmp_path / "nested" / "people.json"

    people = [
        PersonDetails(name="Kiesow, Lars, M. Sc.", email="lkiesow@uos.de").model_dump(),
    ]

    write_people_data(people, str(path))

    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["count"] == 1
    assert data["people"][0]["name"] == "Kiesow, Lars, M. Sc."
    assert "scraped_at" in data
