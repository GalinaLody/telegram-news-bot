import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from constants import STORAGE_CLEANUP_OLD_DAYS

DB_PATH = Path(__file__).resolve().parent / "digest.db"


def _get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def _init_db() -> None:
    with closing(_get_connection()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_news (
                url TEXT PRIMARY KEY,
                sent_at TIMESTAMP
            )
            """
        )
        conn.commit()


_init_db()


def is_sent(url: str) -> bool:
    with closing(_get_connection()) as conn:
        cursor = conn.execute("SELECT 1 FROM sent_news WHERE url = ?", (url,))
        return cursor.fetchone() is not None


def mark_sent(url: str) -> None:
    with closing(_get_connection()) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_news (url, sent_at) VALUES (?, ?)",
            (url, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def cleanup_old(days: int = STORAGE_CLEANUP_OLD_DAYS) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with closing(_get_connection()) as conn:
        cursor = conn.execute(
            "DELETE FROM sent_news WHERE sent_at < ?", (cutoff,)
        )
        conn.commit()
        return cursor.rowcount
