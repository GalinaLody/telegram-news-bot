import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

import storage
from bot import bot, send_message
from collectors.rss_collector import fetch_rss
from collectors.telegram_collector import fetch_telegram_channel
from digest import build_digest, dedupe, filter_recent, rank, split_for_telegram
from models import News

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

SOURCES_PATH = Path(__file__).resolve().parent / "sources.yaml"
OWNER_CHAT_ID = os.getenv("OWNER_CHAT_ID")


async def collect_all() -> list[News]:
    with open(SOURCES_PATH, encoding="utf-8") as f:
        sources = yaml.safe_load(f)

    all_news: list[News] = []

    for source in sources:
        if not source.get("enabled"):
            continue

        topics = source.get("topics", [])
        source_type = source.get("type")

        if source_type == "rss":
            news_items = fetch_rss(
                url=source["url"],
                source_name=source["name"],
                topic=topics[0],
                keywords=source.get("keywords"),
            )
        elif source_type == "telegram":
            channel = source["url"].rstrip("/").split("/")[-1]
            news_items = await fetch_telegram_channel(
                channel_username=channel,
                topic=topics[0],
            )
        else:
            continue

        if len(topics) > 1:
            for i, news in enumerate(news_items):
                news.topic = topics[i % len(topics)]

        all_news.extend(news_items)

    return all_news


async def run_weekly_digest(dry_run: bool = True) -> None:
    news_items = await collect_all()
    recent_news = filter_recent(news_items)
    deduped_news = dedupe(recent_news)
    ranked_news = rank(deduped_news)
    digest_text = build_digest(ranked_news)
    parts = split_for_telegram(digest_text)

    if dry_run:
        for i, part in enumerate(parts, start=1):
            print(f"--- Часть {i}/{len(parts)} ---")
            print(part)
    else:
        for part in parts:
            await send_message(OWNER_CHAT_ID, part)

        for news in ranked_news:
            storage.mark_sent(news.url)

        await bot.session.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_weekly_digest(dry_run=False))
