import asyncio
import functools
from datetime import datetime, timedelta, timezone

import pytest

import pipeline
import storage
from models import News


def make_news(url, topic="Тема"):
    return News(
        title="Title",
        url=url,
        source="Test",
        published_at=datetime.now(timezone.utc) - timedelta(days=1),
        summary_raw="x" * 200,
        topic=topic,
    )


@pytest.fixture
def three_parts(monkeypatch, temp_db):
    """Девять новостей, которые при max_len=600 раскладываются минимум на три части."""
    news_list = [make_news(f"https://example.com/{i}") for i in range(9)]

    async def fake_collect_all():
        return news_list, []

    monkeypatch.setattr(pipeline, "collect_all", fake_collect_all)
    monkeypatch.setattr(pipeline, "build_parts", functools.partial(pipeline.build_parts, max_len=600))
    monkeypatch.setattr(pipeline, "OWNER_CHAT_ID", "42")
    return news_list


def test_marks_news_of_each_delivered_part(monkeypatch, three_parts):
    sent = []
    monkeypatch.setattr(pipeline, "send_message", lambda chat_id, text: sent.append(text))

    asyncio.run(pipeline.run_weekly_digest(dry_run=False))

    assert len(sent) >= 3
    assert all(storage.is_sent(news.url) for news in three_parts)


def test_failure_on_second_part_keeps_first_marked_and_reports_progress(monkeypatch, three_parts):
    sent = []

    def fake_send(chat_id, text):
        sent.append(text)
        if len(sent) == 2:
            raise RuntimeError("boom")

    monkeypatch.setattr(pipeline, "send_message", fake_send)
    parts = pipeline.build_parts(pipeline.rank(three_parts))
    assert len(parts) >= 3

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(pipeline.run_weekly_digest(dry_run=False))

    assert all(storage.is_sent(news.url) for news in parts[0].news)
    assert not any(storage.is_sent(news.url) for part in parts[1:] for news in part.news)

    error_message = sent[-1]
    assert f"Отправлено частей: 1 из {len(parts)}" in error_message


def test_dry_run_sends_and_marks_nothing(monkeypatch, three_parts, capsys):
    sent = []
    monkeypatch.setattr(pipeline, "send_message", lambda chat_id, text: sent.append(text))

    asyncio.run(pipeline.run_weekly_digest(dry_run=True))

    assert sent == []
    assert not any(storage.is_sent(news.url) for news in three_parts)
    assert "--- Часть 1/" in capsys.readouterr().out
