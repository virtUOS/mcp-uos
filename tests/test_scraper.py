#!/usr/bin/env python3
"""Tests for the Personensuche directory scraper.

Run with: pytest tests/test_scraper.py
"""

import json

from mcpuos.models import PersonDetails, PersonSearchResult
from mcpuos.scrape_people import scrape_all_people, write_people_data
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
# scrape_all_people — per-letter progress logging
# ---------------------------------------------------------------------------


class _FakeClient:
    """Minimal stand-in for UOSWebsiteClient covering only the two methods
    scrape_all_people calls, so this test needs no network access."""

    def __init__(self, people_by_letter, failing_urls=()):
        self._people_by_letter = people_by_letter
        self._failing_urls = set(failing_urls)

    def list_people_by_letter(self, letter, delay=0.0):
        return self._people_by_letter.get(letter, [])

    def people_details(self, url):
        if url in self._failing_urls:
            raise RuntimeError("boom")
        return PersonDetails(name=url, source_url=url)


def test_scrape_all_people_logs_per_letter_progress(capsys):
    stubs_a = [PersonSearchResult(name="Person A1", details_url="https://x/a1")]
    stubs_b = [
        PersonSearchResult(name=f"Person B{i}", details_url=f"https://x/b{i}")
        for i in range(1, 13)
    ]
    failing_url = "https://x/b5"

    client = _FakeClient(
        people_by_letter={"A": stubs_a, "B": stubs_b},
        failing_urls={failing_url},
    )

    people = scrape_all_people(client, delay=0)

    assert len(people) == 12  # 1 (A) + 12 (B) minus 1 failure

    out_lines = capsys.readouterr().out.splitlines()

    assert "A: 1 people found" in out_lines
    assert "A: 1/1 people details fetched" in out_lines

    assert "B: 12 people found" in out_lines
    assert "B:  1/12 people details fetched" in out_lines
    assert "B: 12/12 people details fetched" in out_lines

    assert any(f"skipped {failing_url}" in line for line in out_lines)
    assert not any("people fetched so far" in line for line in out_lines)

    assert "C: 0 people found" in out_lines
    assert not any(line.startswith("C: ") and "/" in line for line in out_lines)


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
