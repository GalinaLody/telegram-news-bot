import asyncio
import functools
import sqlite3
from contextlib import closing
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
def three_parts(monkeypatch):
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
    built = []
    real_build_parts = pipeline.build_parts

    def recording_build_parts(*args, **kwargs):
        built.append(real_build_parts(*args, **kwargs))
        return built[-1]

    def fake_send(chat_id, text):
        sent.append(text)
        if len(sent) == 2:
            raise RuntimeError("boom")

    monkeypatch.setattr(pipeline, "build_parts", recording_build_parts)
    monkeypatch.setattr(pipeline, "send_message", fake_send)

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(pipeline.run_weekly_digest(dry_run=False))

    total_parts = len(built[0])
    assert total_parts >= 3
    # Доставлена только первая отправленная часть (вторая упала); сверяем с её фактическим текстом.
    delivered_lines = set(sent[0].splitlines())
    delivered = [news for news in three_parts if news.url in delivered_lines]
    not_delivered = [news for news in three_parts if news.url not in delivered_lines]
    assert delivered and not_delivered
    assert all(storage.is_sent(news.url) for news in delivered)
    assert not any(storage.is_sent(news.url) for news in not_delivered)

    error_message = sent[-1]
    assert f"Отправлено частей: 1 из {total_parts}" in error_message


def test_first_part_starts_with_intro_then_failed_sources_warning(monkeypatch, three_parts):
    async def fake_collect_all():
        return three_parts, [("Сломанный источник", "boom")]

    sent = []
    monkeypatch.setattr(pipeline, "collect_all", fake_collect_all)
    monkeypatch.setattr(pipeline, "send_message", lambda chat_id, text: sent.append(text))

    asyncio.run(pipeline.run_weekly_digest(dry_run=False))

    first = sent[0]
    assert first.startswith("AI-дайджест за ")
    assert first.index("Новостей: 9") < first.index("⚠️ Без новостей") < first.index("=== Тема ===")
    assert all("AI-дайджест за" not in text for text in sent[1:])


def test_real_run_initializes_db_and_migrates_urls(monkeypatch, three_parts, temp_db):
    dirty = "https://habr.com/ru/articles/1/?utm_source=rss"
    with closing(sqlite3.connect(temp_db)) as conn:
        conn.execute("INSERT INTO sent_news (url, sent_at) VALUES (?, ?)", (dirty, "2026-11-02T04:00:00+00:00"))
        conn.commit()
    monkeypatch.setattr(pipeline, "send_message", lambda chat_id, text: None)

    asyncio.run(pipeline.run_weekly_digest(dry_run=False))

    assert storage.is_sent("https://habr.com/ru/articles/1")
    assert not storage.is_sent(dirty)


def test_dry_run_does_not_touch_db_file(monkeypatch, three_parts, isolated_db_path):
    monkeypatch.setattr(pipeline, "send_message", lambda chat_id, text: None)

    asyncio.run(pipeline.run_weekly_digest(dry_run=True))

    assert not isolated_db_path.exists()


def test_dry_run_leaves_existing_db_bytes_unchanged(monkeypatch, three_parts, temp_db):
    with closing(sqlite3.connect(temp_db)) as conn:
        conn.execute("INSERT INTO sent_news (url, sent_at) VALUES (?, ?)", ("https://habr.com/a/?utm_source=rss", "2026-11-02T04:00:00+00:00"))
        conn.commit()
    before = temp_db.read_bytes()

    asyncio.run(pipeline.run_weekly_digest(dry_run=True))

    assert temp_db.read_bytes() == before


def test_dry_run_sends_and_marks_nothing(monkeypatch, three_parts, capsys):
    sent = []
    monkeypatch.setattr(pipeline, "send_message", lambda chat_id, text: sent.append(text))

    asyncio.run(pipeline.run_weekly_digest(dry_run=True))

    assert sent == []
    assert not any(storage.is_sent(news.url) for news in three_parts)
    assert "--- Часть 1/" in capsys.readouterr().out
