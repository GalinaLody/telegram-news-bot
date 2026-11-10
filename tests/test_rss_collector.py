import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

from collectors import rss_collector
from collectors.rss_collector import fetch_rss
from constants import COLLECTORS_RSS_TIMEOUT_SECONDS

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_feed.xml"


class FakeResponse:
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


@pytest.fixture
def sample_feed(monkeypatch):
    """Подменяет requests.get: вместо сети отдаёт sample_feed.xml и запоминает вызовы."""
    calls = []

    def fake_get(url, timeout, headers):
        calls.append({"url": url, "timeout": timeout, "headers": headers})
        return FakeResponse(FIXTURE.read_bytes())

    monkeypatch.setattr(rss_collector.requests, "get", fake_get)
    return calls


def test_entry_without_date_is_skipped_with_warning(sample_feed, caplog):
    with caplog.at_level(logging.WARNING):
        result = fetch_rss(url="https://example.com/feed", source_name="Sample", topic="Тема")

    assert [n.title for n in result] == ["Запись с pubDate", "Запись только с updated"]
    assert "Запись без даты" in caplog.text
    assert "Sample" in caplog.text


def test_published_date_preferred_then_updated(sample_feed):
    result = fetch_rss(url="https://example.com/feed", source_name="Sample", topic="Тема")

    assert result[0].published_at == datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc)
    assert result[1].published_at == datetime(2026, 11, 8, 12, 30, tzinfo=timezone.utc)


def test_request_uses_timeout_and_user_agent(sample_feed):
    fetch_rss(url="https://example.com/feed", source_name="Sample", topic="Тема")

    assert sample_feed[0]["url"] == "https://example.com/feed"
    assert sample_feed[0]["timeout"] == COLLECTORS_RSS_TIMEOUT_SECONDS
    assert sample_feed[0]["headers"]["User-Agent"]


def test_http_error_is_raised(monkeypatch):
    monkeypatch.setattr(
        rss_collector.requests,
        "get",
        lambda url, timeout, headers: FakeResponse(b"", status_code=503),
    )

    with pytest.raises(requests.HTTPError):
        fetch_rss(url="https://example.com/feed", source_name="Sample", topic="Тема")


def test_unparseable_empty_feed_raises_runtime_error(monkeypatch):
    monkeypatch.setattr(
        rss_collector.requests,
        "get",
        lambda url, timeout, headers: FakeResponse(b"not a feed"),
    )

    with pytest.raises(RuntimeError):
        fetch_rss(url="https://example.com/feed", source_name="Sample", topic="Тема")
