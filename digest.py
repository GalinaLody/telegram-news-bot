import sys
from datetime import datetime, timedelta, timezone

import storage
from models import News

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def filter_recent(news_list: list[News], days: int = 7) -> list[News]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [news for news in news_list if news.published_at >= cutoff]


def dedupe(news_list: list[News]) -> list[News]:
    return [news for news in news_list if not storage.is_sent(news.url)]


if __name__ == "__main__":
    from collectors.rss_collector import fetch_rss

    news_items = fetch_rss(
        url="https://habr.com/ru/rss/hub/artificial_intelligence/all/",
        source_name="Habr (хаб AI)",
        topic="AI-агенты",
    )
    print(f"Собрано с Habr: {len(news_items)}")

    recent_news = filter_recent(news_items, days=7)
    print(f"После filter_recent: {len(recent_news)}")

    deduped_news = dedupe(recent_news)
    print(f"После dedupe: {len(deduped_news)}")
