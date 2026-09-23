import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from telethon import TelegramClient

from models import News

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

logger = logging.getLogger(__name__)

TG_API_ID = os.getenv("TG_API_ID")
TG_API_HASH = os.getenv("TG_API_HASH")
SESSION_NAME = "telegram_news_bot"


async def fetch_telegram_channel(channel_username: str, topic: str, since_days: int = 7) -> list[News]:
    channel = channel_username.lstrip("@")
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    news_list = []

    try:
        async with TelegramClient(SESSION_NAME, int(TG_API_ID), TG_API_HASH) as client:
            async for message in client.iter_messages(channel):
                if not message.date:
                    continue
                if message.date < cutoff:
                    break

                text = message.text or ""
                if not text:
                    continue

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
