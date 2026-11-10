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

