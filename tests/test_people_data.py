#!/usr/bin/env python3
"""Tests for the PeopleDataStore used by the MCP server's scrape mode.

Run with: pytest tests/test_people_data.py
"""

import json
import os
import signal

import pytest

from mcpuos.models import PersonDetails
from mcpuos.people_data import PeopleDataStore, install_reload_handler


def _write(path, people):
    path.write_text(
        json.dumps({"scraped_at": "2026-01-01T00:00:00+00:00", "count": len(people), "people": people}),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# load + search
# ---------------------------------------------------------------------------


def test_load_and_search_is_case_insensitive(tmp_path):
    path = tmp_path / "people.json"
    _write(path, [
        PersonDetails(name="Kiesow, Lars, M. Sc.", email="lkiesow@uos.de").model_dump(),
        PersonDetails(name="Anna Schmidt").model_dump(),
    ])

    store = PeopleDataStore(str(path))
    assert len(store) == 2

    matches = store.search("kiesow")
    assert len(matches) == 1
    assert matches[0].email == "lkiesow@uos.de"


def test_missing_file_raises_on_construction(tmp_path):
    with pytest.raises(OSError):
        PeopleDataStore(str(tmp_path / "does-not-exist.json"))


# ---------------------------------------------------------------------------
# reload
# ---------------------------------------------------------------------------


def test_reload_picks_up_new_data(tmp_path):
    path = tmp_path / "people.json"
    _write(path, [PersonDetails(name="Alice").model_dump()])
    store = PeopleDataStore(str(path))

    _write(path, [PersonDetails(name="Alice").model_dump(), PersonDetails(name="Bob").model_dump()])
    assert store.reload() is True
    assert len(store) == 2


def test_reload_keeps_last_known_good_on_corrupt_file(tmp_path):
    path = tmp_path / "people.json"
    _write(path, [PersonDetails(name="Alice").model_dump()])
    store = PeopleDataStore(str(path))

    path.write_text("{not valid json", encoding="utf-8")
    assert store.reload() is False
    assert len(store) == 1
    assert store.search("alice")[0].name == "Alice"


# ---------------------------------------------------------------------------
# SIGHUP wiring
# ---------------------------------------------------------------------------


def test_install_reload_handler_reloads_on_real_sighup(tmp_path):
    path = tmp_path / "people.json"
    _write(path, [PersonDetails(name="Alice").model_dump()])
    store = PeopleDataStore(str(path))

    previous_handler = signal.getsignal(signal.SIGHUP)
    install_reload_handler(store)
    try:
        _write(path, [PersonDetails(name="Alice").model_dump(), PersonDetails(name="Bob").model_dump()])
        os.kill(os.getpid(), signal.SIGHUP)

        assert len(store) == 2
    finally:
        signal.signal(signal.SIGHUP, previous_handler)
