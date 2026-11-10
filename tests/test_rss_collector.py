import logging
from datetime import datetime, timezone
from pathlib import Path

from collectors.rss_collector import fetch_rss

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample_feed.xml"


def test_entry_without_date_is_skipped_with_warning(caplog):
    with caplog.at_level(logging.WARNING):
        result = fetch_rss(url=str(FIXTURE), source_name="Sample", topic="Тема")

    assert [n.title for n in result] == ["Запись с pubDate", "Запись только с updated"]
    assert "Запись без даты" in caplog.text
    assert "Sample" in caplog.text


def test_published_date_preferred_then_updated():
    result = fetch_rss(url=str(FIXTURE), source_name="Sample", topic="Тема")

    assert result[0].published_at == datetime(2026, 11, 9, 10, 0, tzinfo=timezone.utc)
    assert result[1].published_at == datetime(2026, 11, 8, 12, 30, tzinfo=timezone.utc)
