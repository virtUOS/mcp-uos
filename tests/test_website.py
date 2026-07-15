#!/usr/bin/env python3
"""Tests for UOSWebsiteClient URL handling.

Run with: pytest tests/test_website.py
"""

import pytest

from mcpuos.website import UOSWebsiteClient


class _FakeResponse:
    headers = {'content-type': 'text/html'}
    text = '<html></html>'
    content = b''

    def raise_for_status(self):
        pass


@pytest.fixture
def client(monkeypatch):
    client = UOSWebsiteClient(skip_login=True)
    monkeypatch.setattr(client.session, "get", lambda url: _FakeResponse())
    return client


@pytest.mark.parametrize("url", [
    "/impressum",
    "https://www.uni-osnabrueck.de/impressum",
    "https://uni-osnabrueck.de/impressum",
    "https://virtuos.uni-osnabrueck.de/some/page",
])
def test_fetch_allows_university_urls(client, url):
    content, content_type = client._fetch_page_content(url)
    assert content_type == 'text/html'


@pytest.mark.parametrize("url", [
    "https://example.com/",
    "https://evil-uni-osnabrueck.de/phish",
    "https://uni-osnabrueck.de.evil.com/phish",
    "http://localhost:8000/internal",
])
def test_fetch_rejects_external_urls(client, url):
    with pytest.raises(ValueError, match="not on the university website"):
        client._fetch_page_content(url)


def test_fetch_rejects_non_absolute_urls(client):
    with pytest.raises(ValueError, match="must be absolute"):
        client._fetch_page_content("ftp://www.uni-osnabrueck.de/x")
