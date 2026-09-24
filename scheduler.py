import sys
from collections import Counter
from pathlib import Path

import yaml

from collectors.rss_collector import fetch_rss
from collectors.telegram_collector import fetch_telegram_channel
from models import News

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

SOURCES_PATH = Path(__file__).resolve().parent / "sources.yaml"


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


if __name__ == "__main__":
    import asyncio

    news_items = asyncio.run(collect_all())

    print(f"Всего собрано новостей: {len(news_items)}\n")

    counts = Counter(news.source for news in news_items)
    for source_name, count in counts.items():
        print(f"{source_name}: {count}")
