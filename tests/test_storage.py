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
