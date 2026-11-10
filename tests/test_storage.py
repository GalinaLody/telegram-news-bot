import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

import storage


class TestIsSentMarkSent:
    def test_is_sent_false_then_true_after_mark(self, temp_db):
        url = "https://example.com/news-1"

        assert storage.is_sent(url) is False

        storage.mark_sent(url)

        assert storage.is_sent(url) is True

    def test_mark_sent_is_idempotent(self, temp_db):
        url = "https://example.com/news-2"

        storage.mark_sent(url)
        storage.mark_sent(url)

        assert storage.is_sent(url) is True


class TestNormalizeStoredUrls:
    def _insert(self, rows):
        with closing(sqlite3.connect(storage.DB_PATH)) as conn:
            conn.executemany("INSERT INTO sent_news (url, sent_at) VALUES (?, ?)", rows)
            conn.commit()

    def test_utm_record_found_by_clean_url_and_sent_at_kept(self, temp_db):
        dirty = "https://habr.com/ru/articles/1/?utm_source=habrahabr&utm_medium=rss"
        self._insert([(dirty, "2026-11-02T04:00:00+00:00")])

        storage.normalize_stored_urls()

        assert storage.is_sent("https://habr.com/ru/articles/1") is True
        assert storage.is_sent(dirty) is False
        with closing(sqlite3.connect(storage.DB_PATH)) as conn:
            row = conn.execute("SELECT sent_at FROM sent_news").fetchone()
        assert row == ("2026-11-02T04:00:00+00:00",)

    def test_collapses_records_that_match_after_normalization(self, temp_db):
        self._insert(
            [
                ("https://habr.com/ru/articles/1/?utm_source=a", "2026-11-02T04:00:00+00:00"),
                ("https://habr.com/ru/articles/1/?utm_source=b", "2026-11-03T04:00:00+00:00"),
            ]
        )

        storage.normalize_stored_urls()

        with closing(sqlite3.connect(storage.DB_PATH)) as conn:
            rows = conn.execute("SELECT url FROM sent_news").fetchall()
        assert rows == [("https://habr.com/ru/articles/1",)]

    def test_second_call_changes_nothing(self, temp_db):
        self._insert([("https://habr.com/ru/articles/1/?utm_source=a", "2026-11-02T04:00:00+00:00")])

        first = storage.normalize_stored_urls()
        second = storage.normalize_stored_urls()

        assert first == 1
        assert second == 0
        assert storage.is_sent("https://habr.com/ru/articles/1") is True


class TestCleanupOld:
    def test_removes_only_old_records(self, temp_db):
        old_url = "https://example.com/old"
        recent_url = "https://example.com/recent"

        old_date = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        recent_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

        with closing(sqlite3.connect(storage.DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO sent_news (url, sent_at) VALUES (?, ?)", (old_url, old_date)
            )
            conn.execute(
                "INSERT INTO sent_news (url, sent_at) VALUES (?, ?)", (recent_url, recent_date)
            )
            conn.commit()

        deleted_count = storage.cleanup_old(days=30)

        assert deleted_count == 1
        assert storage.is_sent(old_url) is False
        assert storage.is_sent(recent_url) is True
