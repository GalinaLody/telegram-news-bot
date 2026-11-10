"""SQLite-хранилище отправленных новостей.

Защищает от повторов между выпусками: pipeline.py проверяет здесь URL перед
отбором и записывает их после доставки каждой части дайджеста.
"""

import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

from constants import STORAGE_CLEANUP_OLD_DAYS
from urls import normalize_url

DB_PATH = Path(__file__).resolve().parent / "digest.db"


def _get_connection() -> sqlite3.Connection:
    """Открыть соединение с базой digest.db."""
    return sqlite3.connect(DB_PATH)


def _get_readonly_connection() -> sqlite3.Connection:
    """Открыть digest.db только для чтения (файл не создаётся и не меняется)."""
    return sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)


def init_db() -> None:
    """Создать таблицу sent_news, если её нет, и нормализовать сохранённые URL.

    Вызывается явно при реальном запуске (не при импорте модуля), потому что
    меняет файл базы. В режиме --dry-run не вызывается.
    """
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

    normalize_stored_urls()


def normalize_stored_urls() -> int:
    """Привести URL в таблице sent_news к нормализованному виду (миграция).

    Если после нормализации ссылка совпала с уже имеющейся записью, остаётся
    одна запись (уже существующая), дата отправки сохраняется. Безопасно
    вызывать повторно: уже нормализованные записи не меняются.

    Returns:
        Количество изменённых или удалённых записей.
    """
    changed = 0
    with closing(_get_connection()) as conn:
        rows = conn.execute("SELECT url, sent_at FROM sent_news").fetchall()
        for url, sent_at in rows:
            normalized = normalize_url(url)
            if normalized == url:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO sent_news (url, sent_at) VALUES (?, ?)",
                (normalized, sent_at),
            )
            conn.execute("DELETE FROM sent_news WHERE url = ?", (url,))
            changed += 1
        conn.commit()
    return changed


def is_sent(url: str) -> bool:
    """Проверить, отправлялась ли новость с таким URL раньше.

    База открывается только для чтения, поэтому проверка не меняет файл
    digest.db (важно для --dry-run). Если файла или таблицы ещё нет, считается,
    что ничего не отправлялось.

    Args:
        url: Нормализованный URL новости.

    Returns:
        True, если URL есть в таблице sent_news.
    """
    try:
        with closing(_get_readonly_connection()) as conn:
            cursor = conn.execute("SELECT 1 FROM sent_news WHERE url = ?", (url,))
            return cursor.fetchone() is not None
    except sqlite3.OperationalError:
        return False


def mark_sent(url: str) -> None:
    """Записать URL как отправленный (повторный вызов ничего не меняет).

    Args:
        url: Нормализованный URL новости.
    """
    with closing(_get_connection()) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_news (url, sent_at) VALUES (?, ?)",
            (url, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def cleanup_old(days: int = STORAGE_CLEANUP_OLD_DAYS) -> int:
    """Удалить записи об отправленных новостях старше `days` дней.

    Args:
        days: Сколько дней хранить записи.

    Returns:
        Количество удалённых записей.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with closing(_get_connection()) as conn:
        cursor = conn.execute(
            "DELETE FROM sent_news WHERE sent_at < ?", (cutoff,)
        )
        conn.commit()
        return cursor.rowcount
