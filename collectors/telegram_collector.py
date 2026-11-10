"""Сборщик новостей из публичных Telegram-каналов через Telethon.

Первый шаг цепочки для источников типа telegram; работает от имени личного
аккаунта по строке сессии TG_SESSION.
"""

import re
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient
from telethon.sessions import StringSession

from config import TG_API_HASH, TG_API_ID, TG_SESSION
from constants import (
    COLLECTORS_TELEGRAM_COLLECTOR_TITLE_MAX_CHARS,
    DIGEST_FILTER_RECENT_DAYS,
)
from models import News


def strip_markdown(text: str) -> str:
    """Убрать Markdown-разметку Telegram, оставив обычный текст.

    Args:
        text: Текст поста с разметкой (ссылки, **жирный**, __подчёркнутый__,
            *курсив*, _курсив_).

    Returns:
        Текст без разметки; у ссылок остаётся только подпись.
    """
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"\1", text, flags=re.DOTALL)
    return text


async def fetch_telegram_channel(
    channel_username: str,
    topic: str,
    since_days: int = DIGEST_FILTER_RECENT_DAYS,
) -> list[News]:
    """Прочитать свежие посты канала и преобразовать их в новости.

    Args:
        channel_username: Имя канала, с @ или без.
        topic: Тема, которую получат все новости канала.
        since_days: Сколько дней назад от текущего момента брать посты.

    Returns:
        Новости из текстовых постов канала, от новых к старым.

    Raises:
        RuntimeError: Не задана переменная окружения TG_SESSION.
    """
    if not TG_SESSION:
        raise RuntimeError(
            "Переменная окружения TG_SESSION не найдена. Сгенерируйте строку сессии "
            "через generate_session_string.py и добавьте её в .env."
        )

    channel = channel_username.lstrip("@")
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    news_list = []

    async with TelegramClient(StringSession(TG_SESSION), int(TG_API_ID), TG_API_HASH) as client:
        async for message in client.iter_messages(channel):
            if not message.date:
                continue
            if message.date < cutoff:
                break

            text = message.text or ""
            if not text:
                continue

            text = strip_markdown(text)

            news_list.append(
                News(
                    title=text[:COLLECTORS_TELEGRAM_COLLECTOR_TITLE_MAX_CHARS],
                    url=f"https://t.me/{channel}/{message.id}",
                    source=f"Telegram @{channel}",
                    published_at=message.date,
                    summary_raw=text,
                    topic=topic,
                )
            )

    return news_list
