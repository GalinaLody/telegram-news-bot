import asyncio
import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

from models import News

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

logger = logging.getLogger(__name__)

TG_API_ID = os.getenv("TG_API_ID")
TG_API_HASH = os.getenv("TG_API_HASH")
TG_SESSION = os.getenv("TG_SESSION")


def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"__(.+?)__", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"\1", text, flags=re.DOTALL)
    return text


async def fetch_telegram_channel(channel_username: str, topic: str, since_days: int = 7) -> list[News]:
    if not TG_SESSION:
        raise RuntimeError(
            "Переменная окружения TG_SESSION не найдена. Сгенерируйте строку сессии "
            "через generate_session_string.py и добавьте её в .env."
        )

    channel = channel_username.lstrip("@")
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    news_list = []

    try:
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
                        title=text[:80],
                        url=f"https://t.me/{channel}/{message.id}",
                        source=f"Telegram @{channel}",
                        published_at=message.date,
                        summary_raw=text,
                        topic=topic,
                    )
                )
    except Exception as exc:
        logger.error(f"Ошибка получения Telegram-канала @{channel}: {exc}")
        return []

    return news_list


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    vibecoding_news = asyncio.run(
        fetch_telegram_channel(channel_username="vibecoding_tg", topic="Вайбкодинг", since_days=7)
    )

    print(f"Получено новостей: {len(vibecoding_news)}")
    for news in vibecoding_news[:5]:
        print(f"{news.published_at} — {news.title}")

    veryvibecoding_news = asyncio.run(
        fetch_telegram_channel(channel_username="veryvibecoding", topic="Вайбкодинг, AI-агенты", since_days=7)
    )

    print(f"\nvery vibecoding — получено новостей: {len(veryvibecoding_news)}")
    for news in veryvibecoding_news[:3]:
        print(f"{news.published_at} — {news.title}")
